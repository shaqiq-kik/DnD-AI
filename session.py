import os
import json
import datetime
from game_state import GameState

def save_session(game_state: GameState, conversation_history: list, filepath: str = "session.json"):
    """
    Saves the current game state and the GM agent's conversation history to a JSON file.
    """
    data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "game_state": {
            "name": game_state.name,
            "char_class": game_state.char_class,
            "max_hp": game_state.max_hp,
            "hp": game_state.hp,
            "inventory": game_state.inventory,
            "location": game_state.location,
            "quest_log": game_state.quest_log
        },
        "conversation_history": conversation_history
    }
    
    # Save to file
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        
    print(f"\n[System] Game session successfully saved to '{filepath}'.")

def load_session(filepath: str = "session.json") -> tuple:
    """
    Loads a saved game session from a JSON file.
    Returns a tuple containing the rebuilt GameState and the conversation history list.
    Returns (None, []) if the file does not exist.
    """
    if not os.path.exists(filepath):
        return None, []
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        gs_data = data.get("game_state", {})
        
        # Rebuild the GameState object from saved data
        game_state = GameState(
            name=gs_data.get("name", "Unknown"),
            char_class=gs_data.get("char_class", "Adventurer"),
            max_hp=gs_data.get("max_hp", 20)
        )
        game_state.hp = gs_data.get("hp", 20)
        game_state.inventory = gs_data.get("inventory", [])
        game_state.location = gs_data.get("location", "Starting Area")
        game_state.quest_log = gs_data.get("quest_log", [])
        
        conversation_history = data.get("conversation_history", [])
        
        return game_state, conversation_history
        
    except Exception as e:
        print(f"\n[System Error] Failed to load session from '{filepath}': {e}")
        return None, []

def session_exists(filepath: str = "session.json") -> bool:
    """
    Checks whether a saved session file exists at the given filepath.
    """
    return os.path.exists(filepath)
