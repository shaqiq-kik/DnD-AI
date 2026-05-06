import os
import ollama
from dotenv import load_dotenv

# Import the tool schema and implementation from tools.py
from tools import TOOLS_DEFINITION, roll_for

# Load environment variables
load_dotenv()
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2")


class GMAgent:
    def __init__(self):
        self.model = MODEL_NAME
        self.base_system_prompt = (
            "You are an expert Dungeon Master for a Dungeons & Dragons game. "
            "You are creative, engaging, and strictly adhere to the rules of D&D 5e. "
            "Keep your responses concise but descriptive. "
            "Address the player directly and resolve their actions based on your judgment. "
            "You have access to exactly TWO tools:\n"
            "1. roll_for(skill, dc, player) — use for ALL dice rolls and skill checks\n"
            "2. apply_damage(amount) — use ONLY when an enemy successfully hits the "
            "player and deals damage. Call this immediately after narrating the hit."
        )

        # Maintain conversation history across turns
        self.messages = [
            {"role": "system", "content": self.base_system_prompt}
        ]

    def _build_context(self, game_state):
        """
        Formats the game state into a string to be injected into the prompt.
        """
        inv_str = ", ".join(game_state.inventory) if game_state.inventory else "Empty"
        quest_str = ", ".join(game_state.quest_log) if game_state.quest_log else "None"

        return (
            f"Here is the player's current status:\n"
            f"- Name: {game_state.name}\n"
            f"- Class: {game_state.char_class}\n"
            f"- HP: {game_state.hp}/{game_state.max_hp}\n"
            f"- Location: {game_state.location}\n"
            f"- Inventory: {inv_str}\n"
            f"- Active Quests: {quest_str}\n"
        )

    def _plan(self, player_message: str, game_state) -> str:
        """
        Chain-of-thought planning:
        Makes a separate LLM call to reason step-by-step before responding.
        Returns the reasoning as a plain string.
        
        This is called BEFORE the main response so the AI thinks
        through the situation before committing to a narrative direction.
        """
        context = self._build_context(game_state)

        planning_prompt = (
            f"You are the Dungeon Master planning your next move.\n\n"
            f"{context}\n"
            f"The player just said/did: '{player_message}'\n\n"
            f"Reason step-by-step:\n"
            f"1. What is the player trying to do?\n"
            f"2. Is a skill check needed? If so, what skill and what is the DC?\n"
            f"3. What are the story stakes?\n\n"
            f"Provide your internal reasoning in 3-5 sentences. No narration."
        )

        try:
            # Separate planning call with NO tools — pure reasoning only
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": planning_prompt}]
            )
            # FIX: use attribute access, not dict .get()
            return response.message.content
        except Exception as e:
            print(f"\n[System Warning] Planning step failed: {e}")
            return "No plan generated."

    def process_tool_call(self, tool_call) -> str:
        """
        Handles the tool call returned by the LLM.
        Extracts arguments and calls the corresponding Python function.
        """
        # Handle both object and dict formats defensively
        if isinstance(tool_call, dict):
            func = tool_call.get('function', {})
            name = func.get('name', '')
            args = func.get('arguments', {})
        else:
            name = tool_call.function.name
            args = tool_call.function.arguments

        # If args came in as a string, parse it
        if isinstance(args, str):
            import json
            try:
                args = json.loads(args)
            except Exception:
                args = {}

        # Ensure args is a dict
        if not isinstance(args, dict):
            args = {}

        if name == "roll_for":
            skill = args.get('skill', 'Unknown Skill')
            if isinstance(skill, dict):
                skill = skill.get('value', 'Unknown Skill')
                
            player = args.get('player', 'Player')
            if isinstance(player, dict):
                player = player.get('value', 'Player')

            # FIX: defensively handle dc — it can arrive as None, dict, or string
            dc = args.get('dc', 10)
            if isinstance(dc, dict):
                dc = dc.get('value') or dc.get('dc') or 10
            try:
                dc = int(dc)
            except (TypeError, ValueError):
                dc = 10  # safe default DC

            print(f"\n  🎲 Skill Check: {skill} (DC {dc})")
            result = roll_for(skill=skill, dc=dc, player=player)
            print(f"  {result}")
            return result
            
        elif name == "apply_damage":
            amount = args.get('amount', 0)
            if isinstance(amount, dict):
                amount = amount.get('value') or amount.get('amount') or 0
            try:
                amount = int(amount)
            except (TypeError, ValueError):
                amount = 0
            # Accumulate damage so respond_to_action can signal main.py
            self._pending_damage = getattr(self, '_pending_damage', 0) + amount
            return f"DAMAGE:{amount}"

        return f"[Tool '{name}' not found.]"

    def respond_to_action(self, game_state, player_action, scenario="exploration"):
        """
        Main method to process a player's action.

        Order of operations:
        1. _plan()  — chain-of-thought reasoning (hidden from player)
        2. Build enriched prompt with context + plan + action
        3. Call LLM WITH tools — may trigger roll_for
        4. Handle tool calls in a loop until final response
        5. Return final response string (with DAMAGE:N appended if damage occurred)
        """
        # Track damage from apply_damage tool calls so we can signal main.py
        self._pending_damage = 0

        # Step 1 — Chain-of-thought planning (separate LLM call, player doesn't see this)
        plan = self._plan(player_action, game_state)

        # Step 2 — Build enriched prompt
        context = self._build_context(game_state)
        enriched_prompt = (
            f"{context}\n"
            f"[DM Internal Plan]:\n{plan}\n\n"
            f"[Player Action]:\n{player_action}"
        )

        # Add to conversation history
        self.messages.append({"role": "user", "content": enriched_prompt})

        # Temperature: 0.8 for creative exploration, 0.4 for strict combat rules
        temperature = 0.8 if scenario == "exploration" else 0.4

        # Step 3 — Main LLM call WITH tools
        try:
            response = ollama.chat(
                model=self.model,
                messages=self.messages,
                tools=TOOLS_DEFINITION,
                options={"temperature": temperature}
            )
        except Exception as e:
            return f"[System Error] Main LLM call failed: {e}"

        # FIX: use attribute access on response object, not dict .get()
        # Step 4 — Tool call loop
        while response.message.tool_calls:
            # Append assistant's tool call intent to history
            self.messages.append({
                "role": "assistant",
                "content": response.message.content or ""
            })

            # Execute each tool and append results
            for tool_call in response.message.tool_calls:
                tool_result = self.process_tool_call(tool_call)
                self.messages.append({
                    "role": "tool",
                    "content": tool_result
                })

            # Call LLM again so it can narrate the tool result
            try:
                response = ollama.chat(
                    model=self.model,
                    messages=self.messages,
                    tools=TOOLS_DEFINITION,
                    options={"temperature": temperature}
                )
            except Exception as e:
                return f"[System Error] Tool follow-up call failed: {e}"

        # Step 5 — Append final response to history and return
        final_content = response.message.content or ""

        # FIX: AI sometimes returns raw JSON instead of calling tools properly
        final_content_stripped = final_content.strip()
        if final_content_stripped.startswith('{'):
            import json
            try:
                parsed = json.loads(final_content_stripped)
                if isinstance(parsed, dict) and "name" in parsed:
                    mock_tool_call = {
                        "function": {
                            "name": parsed.get("name", ""),
                            "arguments": parsed.get("parameters", {})
                        }
                    }
                    tool_result = self.process_tool_call(mock_tool_call)

                    # Narrate the result
                    self.messages.append({"role": "assistant", "content": final_content})
                    self.messages.append({"role": "tool", "content": tool_result})

                    try:
                        response = ollama.chat(
                            model=self.model,
                            messages=self.messages,
                            tools=TOOLS_DEFINITION,
                            options={"temperature": temperature}
                        )
                        final_content = response.message.content or ""
                    except Exception as e:
                        return f"[System Error] Tool follow-up call failed: {e}"
                else:
                    return "The Dungeon Master seems confused. Please try again."
            except Exception:
                return "The Dungeon Master seems to be speaking in tongues. Please try again."

        self.messages.append({
            "role": "assistant",
            "content": final_content
        })

        # Append DAMAGE signal so main.py can update game_state.hp
        pending = getattr(self, '_pending_damage', 0)
        if pending > 0:
            final_content += f" DAMAGE:{pending}"
            self._pending_damage = 0

        return final_content