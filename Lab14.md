# Lab 14: AI Game Master Implementation

## Use Case Diagram
*The system provides the following functionality (Use Cases text description):*

- **Start new game**: The player initializes a session by providing character details like their name and class.
- **Explore dungeon room**: The player describes an action investigating their environment. The AI Game Master uses a high temperature setting to narrate rich environmental details and respond creatively.
- **Engage in combat**: The player declares an attack or tactical maneuver. The AI GM switches to a lower temperature setting to prioritize strict D&D mechanics and rules over creative flourishing.
- **Talk to NPC**: The player initiates dialogue with characters in the game world, prompting the GM to roleplay.
- **Bargain with merchant**: A specialized social interaction where the player negotiates over shop items and services.
- **Track quest progress**: The system stores the player's active objectives and history via GameState, allowing the GM to reference them.
- **Roll dice**: The player explicitly performs a check, or the AI requests one to adjudicate an action.
- **Retrieve D&D lore**: The player investigates magical artifacts or monsters out of game or in character, utilizing the LLM's vast knowledge base.
- **Plan combat strategy**: The player assesses the battlefield, asking the GM for positioning details or checking tactical advantages.
- **Manage game state**: The user requests a summary of their HP, inventory, and location via console commands.
- **Generate voice narration**: Textual outputs from the GM could potentially be hooked up to a Text-to-Speech library API in future versions.

## Completed Feature

Currently, two major use cases from the diagram have been successfully implemented:
1. **Start New Game**: This feature is handled in `main.py`. The script starts up and prompts the user for a name and class. This establishes the initial `GameState` and successfully completes the initialization cycle.
2. **Explore Dungeon Room**: Players can type unstructured exploration choices into the prompt within the game loop. These are processed dynamically by `gm_agent.py` in exploration mode. The current player context (Location, HP, Inventory) is sent alongside the prompt, allowing continuous contextual exploration until the player exits the script.

## Prompt Engineering Choices

To effectively adapt the LLM's responses as a Game Master, two distinct `temperature` parameters have been engineered for our scenarios:

1. **Temperature = 0.8 (Exploration/Narration Mode):**
   - *Reasoning*: Exploration requires a high degree of creativity, atmospheric description, and spontaneous world-building. A higher temperature makes the `llama3.2` model generate more varied and colorful prose, keeping exploration feeling vivid, alive, and unscripted.

2. **Temperature = 0.4 (Combat Mode):**
   - *Reasoning*: Combat in Dungeons & Dragons is mechanically strict. The GM must adhere closely to rules, track exact stats like HP/AC, and maintain a grounded logic. A lower temperature decreases hallucination and forces the model into a more deterministic response pattern suited for tactical decisions and rule adjudication.
