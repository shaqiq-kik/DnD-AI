import sys
from game_state import GameState
from gm_agent import GMAgent

def main():
    print("Welcome to the AI Dungeon Master!")
    print("---------------------------------")
    
    # 1. Start New Game - Character Setup
    name = input("Enter your character's name: ").strip()
    if not name:
        name = "Adventurer"
        
    char_class = input("Enter your character's class (e.g., Wizard, Fighter, Rogue): ").strip()
    if not char_class:
        char_class = "Fighter"
    
    # Initialize components
    state = GameState(name, char_class)
    gm = GMAgent()
    
    print("\n--- Game Starts ---")
    print("Type 'quit' to exit the game.")
    print("Type 'state' to view your current character sheet.")
    print("Type 'combat' to switch to combat scenario, and 'explore' to switch back.")
    print("You awake in a dimly lit tavern...\n")
    
    scenario = "exploration"
    
    # Core Game Loop
    while True:
        # Display HP and Location before the prompt
        print(f"\n[HP: {state.hp}/{state.max_hp} | Location: {state.location} | Mode: {scenario.title()}]")
        
        action = input("What do you do? > ").strip()
        
        # Meta-commands handler
        if action.lower() == 'quit':
            print("The adventure ends here. Goodbye!")
            sys.exit(0)
            
        elif action.lower() == 'state':
            state.display_state()
            continue
            
        elif action.lower() == 'combat':
            scenario = "combat"
            print("\n*** Switched to Combat Mode. The GM is now stricter and follows combat rules. ***")
            continue
            
        elif action.lower() == 'explore':
            scenario = "exploration"
            print("\n*** Switched to Exploration Mode. The GM will focus on narration. ***")
            continue
            
        if not action:
            continue
            
        # 2. Process exploration or combat action
        print("\nThe GM is thinking...")
        try:
            response = gm.respond_to_action(state, action, scenario=scenario)
            print(f"\n[DM] {response}")
        except Exception as e:
            print(f"\n[Error interfacing with Ollama Setup: {e}]")
            print("Ensure you have Ollama running locally and the 'llama3.2' model is pulled.")

if __name__ == "__main__":
    main()
