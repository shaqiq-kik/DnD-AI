import os
import sys
import re
from dotenv import load_dotenv

# Import our custom modules
from game_state import GameState
from gm_agent import GMAgent
from tools import roll_dice
from rag import EmbeddingStore, load_lore, get_rag_context
from tts import narrate
from session import save_session, load_session

# Load environment variables (e.g. MODEL_NAME)
load_dotenv()

def print_separator():
    """Helper to print a clean visual separator."""
    print("\n" + "="*70 + "\n")

def print_help():
    """Displays all available player commands."""
    print("\n--- Available Commands ---")
    print("  quit     : Exits the game")
    print("  state    : Shows full character sheet")
    print("  combat   : Switches to combat mode (precise logic)")
    print("  explore  : Switches to exploration mode (creative logic)")
    print("  roll [n] : Manually rolls a die (e.g. 'roll 20')")
    print("  quests   : Shows your quest log")
    print("  help     : Shows this list of commands")
    print("--------------------------")

def main():
    # 1. Startup: Print ASCII Title
    print(r"""
  _____         _____          _____   _____                    __  __           _            
 |  __ \       |  __ \   /\   |_   _| / ____|                  |  \/  |         | |           
 | |  | |______| |  | | /  \    | |  | |  __  __ _ _ __ ___  ___| \  / | __ _ ___| |_ ___ _ __ 
 | |  | |______| |  | |/ /\ \   | |  | | |_ |/ _` | '_ ` _ \/ _ \ |\/| |/ _` / __| __/ _ \ '__|
 | |__| |      | |__| / ____ \ _| |_ | |__| | (_| | | | | | |  __/ |  | | (_| \__ \ ||  __/ |   
 |_____/       |_____/_/    \_\_____| \_____|\__,_|_| |_| |_|\___|_|  |_|\__,_|___/\__\___|_|   
    """)
    
    print("[System] Initializing Dungeon Master systems and RAG lore database...")
    
    # Initialize RAG Store
    try:
        store = EmbeddingStore()
        load_lore(store)
    except Exception as e:
        print(f"[System Error] Failed to initialize RAG database: {e}")
        print("Please ensure Ollama is running and 'nomic-embed-text' is pulled.")
        sys.exit(1)
        
    print_separator()
    
    # Check for saved session
    loaded_state, history = load_session()
    loaded = False
    if loaded_state:
        load_choice = input("A saved session was found. Would you like to resume? (y/n) > ").strip().lower()
        if load_choice == 'y':
            game_state = loaded_state
            name = game_state.name
            loaded = True

    if not loaded:
        # Character setup
        print("Welcome, adventurer. Before we begin, tell me about yourself.")
        name = input("What is your character's name? > ").strip()
        char_class = input("What is your character's class? > ").strip()

        # Fallbacks if user leaves input empty
        if not name:
            name = "Hero"
        if not char_class:
            char_class = "Fighter"

        game_state = GameState(name=name, char_class=char_class)

    # TTS prompt (asked regardless of new/loaded session)
    tts_input = input("Would you like to enable Text-to-Speech narration? (y/n) > ").strip().lower()
    tts_enabled = tts_input == 'y'
    
    # Instantiate DM Agent
    gm_agent = GMAgent()
    if loaded:
        gm_agent.messages = history
    else:
        # Welcome narration
        welcome_msg = f"Greetings, {name} the {game_state.char_class}. Your journey begins in the {game_state.location}."
        print(f"\n[DM]: {welcome_msg}")
        narrate(welcome_msg, enabled=tts_enabled)
        
    mode = "exploration" # Default scenario mode
    
    print_separator()
    print("Type 'help' at any time for a list of system commands.")
    
    # 2. Main Game Loop
    while True:
        # Display heads-up status
        print(f"\n[HP: {game_state.hp}/{game_state.max_hp} | Loc: {game_state.location} | Mode: {mode.capitalize()}]")
        player_input = input(f"{name} > ").strip()
        
        # Error handling: Empty input
        if not player_input:
            print("[System] Please describe an action or enter a command.")
            continue
            
        cmd = player_input.lower()
        
        # Command Handling
        if cmd == "quit":
            save_session(game_state, gm_agent.messages)
            print("\n[System] Exiting the game. Farewell, adventurer!")
            break
            
        elif cmd == "state":
            # Display character sheet gracefully
            if hasattr(game_state, 'display_state'):
                game_state.display_state()
            else:
                print(f"\n--- {game_state.name}'s Character Sheet ---")
                print(f"Class: {game_state.char_class}")
                print(f"HP: {game_state.hp} / {game_state.max_hp}")
                print(f"Location: {game_state.location}")
                print(f"Inventory: {', '.join(game_state.inventory) if game_state.inventory else 'Empty'}")
                print("-----------------------------------")
            continue
            
        elif cmd == "combat":
            mode = "combat"
            print("\n[System] Switched to Combat Mode. (DM logic shifted to tactical)")
            continue
            
        elif cmd == "explore":
            mode = "exploration"
            print("\n[System] Switched to Exploration Mode. (DM logic shifted to creative)")
            continue
            
        elif cmd.startswith("roll "):
            try:
                sides = int(cmd.split(" ")[1])
                result = roll_dice(sides)
                print(f"\n[System] You rolled a d{sides} and got a {result}!")
            except (ValueError, IndexError):
                print("\n[System] Invalid roll format. Please use 'roll 20'.")
            continue
            
        elif cmd == "quests":
            if game_state.quest_log:
                print("\n--- Quest Log ---")
                for q in game_state.quest_log:
                    print(f"- {q}")
                print("-----------------")
            else:
                print("\n[System] Your quest log is empty.")
            continue
            
        elif cmd == "help":
            print_help()
            continue
            
        # LLM Interaction
        print("\n[System] The Dungeon Master is thinking...")
        
        try:
            # Retrieve lore/rules context using RAG
            rag_context = get_rag_context(store, player_input)
            
            # Enrich the player's action with relevant context (invisible to player output)
            enriched_action = player_input
            if rag_context:
                enriched_action += f"\n\n[Relevant D&D 5e Rules/Lore]:\n{rag_context}"
                
            # Process the action through the agent
            response = gm_agent.respond_to_action(game_state, enriched_action, scenario=mode)
            
            # Check for DAMAGE signal
            damage_match = re.search(r'DAMAGE:(\d+)', response)
            if damage_match:
                damage_amount = int(damage_match.group(1))
                if hasattr(game_state, 'update_hp'):
                    game_state.update_hp(-damage_amount)
                else:
                    game_state.hp = max(0, game_state.hp - damage_amount)
                print(f"\n[System] {name} takes {damage_amount} damage! HP: {game_state.hp}/{game_state.max_hp}")
                # Remove the signal from the response string before narrating/printing
                response = response.replace(f"DAMAGE:{damage_amount}", "").strip()
            
            # Format and output the final response
            print_separator()
            print(f"[DM]: {response}")
            print_separator()
            
            # Speak the response if TTS is toggled on
            narrate(response, enabled=tts_enabled)
            
        except Exception as e:
            # Gracefully catch connection errors if Ollama crashes or isn't running
            print("\n[System Error] Failed to generate DM response. Is the Ollama server running locally?")
            print(f"Error Details: {e}")

if __name__ == "__main__":
    main()
