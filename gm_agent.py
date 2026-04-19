import os
import ollama
from dotenv import load_dotenv

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

    def _get_context_prompt(self, game_state):
        """
        Uses the GameState object to inject the current character status 
        into the system prompt context.
        """
        inv_str = ", ".join(game_state.inventory) if game_state.inventory else "Empty"
        quest_str = ", ".join(game_state.quest_log) if game_state.quest_log else "None"
        
        return (
            f"{self.base_system_prompt}\n\n"
            f"Here is the player's current status:\n"
            f"- Name: {game_state.name}\n"
            f"- Class: {game_state.char_class}\n"
            f"- HP: {game_state.hp}/{game_state.max_hp}\n"
            f"- Location: {game_state.location}\n"
            f"- Inventory: {inv_str}\n"
            f"- Active Quests: {quest_str}\n\n"
        )

    def respond_to_action(self, game_state, player_action, scenario="exploration"):
        """
        Takes the current game state and the player's action, packages them
        into a dynamic prompt, and communicates with the local LLM.
        """
        system_context = self._get_context_prompt(game_state)
        
        # Adjust behavior and temperature based on whether we are in combat or exploration
        if scenario == "combat":
            mode_prompt = (
                "The current scenario is COMBAT. "
                "Rely heavily on game logic, strict D&D combat mechanics (AC, HP, rolls). "
                "Keep descriptions brief and action-oriented."
            )
            temperature = 0.4
        else:
            mode_prompt = (
                "The current scenario is EXPLORATION. "
                "Focus on atmospheric description, storytelling, world-building, and NPC interactions."
            )
            temperature = 0.8
            
        full_system_prompt = f"{system_context}{mode_prompt}\n\n"

        # Make the API call to the local Ollama instance
        response = ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": f"The player takes the following action: {player_action}"}
            ],
            options={
                "temperature": temperature
            }
        )

        return response['message']['content']
