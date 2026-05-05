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
            "Address the player directly and resolve their actions based on your judgment."
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
            f"Provide your internal reasoning."
        )
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": planning_prompt}]
            )
            return response.get('message', {}).get('content', '')
        except Exception as e:
            print(f"\n[System Error] Planning LLM call failed: {e}")
            return "Plan generation failed."

    def process_tool_call(self, tool_call) -> str:
        """
        Handles the tool call returned by the LLM. 
        Extracts arguments and calls the corresponding python function.
        """
        # Accommodate both dict and object access depending on the ollama python client version
        if isinstance(tool_call, dict):
            func = tool_call.get('function', {})
            name = func.get('name')
            args = func.get('arguments', {})
        else:
            name = getattr(tool_call.function, 'name', '')
            args = getattr(tool_call.function, 'arguments', {})

        if name == "roll_for":
            skill = args.get('skill', 'Unknown Skill')
            dc = args.get('dc', 10)
            player = args.get('player', 'Player')
            
            # Use the imported roll_for function from tools.py
            result = roll_for(skill=skill, dc=dc, player=player)
            return result
        
        return f"Tool {name} not found or not implemented."

    def respond_to_action(self, game_state, player_action, scenario="exploration"):
        """
        Main method to process a player's action. Uses chain-of-thought planning,
        builds an enriched prompt, handles tool calls, and returns the final response string.
        """
        # 1. Chain-of-thought planning (called before the main response)
        plan = self._plan(player_action, game_state)
        
        # 2. Build enriched prompt with game state context, plan, and player action
        context = self._build_context(game_state)
        enriched_prompt = (
            f"{context}\n"
            f"[DM Internal Plan]:\n{plan}\n\n"
            f"[Player Action]:\n{player_action}"
        )
        
        # Add the enriched prompt to the conversation history
        self.messages.append({"role": "user", "content": enriched_prompt})
        
        # Set temperature based on scenario as requested
        temperature = 0.8 if scenario == "exploration" else 0.4
        
        # 3. Call LLM WITH tools (roll_for tool from tools.py)
        try:
            response = ollama.chat(
                model=self.model,
                messages=self.messages,
                tools=TOOLS_DEFINITION,
                options={"temperature": temperature}
            )
        except Exception as e:
            return f"[System Error] Main LLM call failed: {e}"
            
        message = response.get('message', {})
        self.messages.append(message)
        
        # 4. Handle any tool calls in a loop
        while message.get('tool_calls'):
            for tool_call in message['tool_calls']:
                tool_result = self.process_tool_call(tool_call)
                
                # Append the tool's result to the conversation history
                self.messages.append({
                    "role": "tool",
                    "content": tool_result
                })
                
            # Request LLM to continue its response based on the tool result(s)
            try:
                response = ollama.chat(
                    model=self.model,
                    messages=self.messages,
                    tools=TOOLS_DEFINITION,
                    options={"temperature": temperature}
                )
                message = response.get('message', {})
                self.messages.append(message)
            except Exception as e:
                return f"[System Error] Tool follow-up LLM call failed: {e}"
            
        return message.get('content', '')
