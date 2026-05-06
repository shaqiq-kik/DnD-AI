# D&D AI Game Master

An AI-powered Dungeon Master for Dungeons & Dragons 5e, built with Python and Ollama. The system uses a local LLM (llama3.2) to generate narrative responses, perform skill checks via tool calling, and retrieve relevant D&D lore using RAG (Retrieval-Augmented Generation) with ChromaDB.

## Features

- **AI Dungeon Master** — Creative narrative responses powered by llama3.2
- **Tool Calling** — Automatic dice rolls and skill checks (d20 system)
- **Chain-of-Thought Planning** — The DM reasons step-by-step before responding
- **RAG Lore System** — ChromaDB stores D&D rules, spells, monsters, and locations for context-aware responses
- **Session Save/Load** — Game state and conversation history persist between sessions
- **Text-to-Speech** — Optional TTS narration of DM responses
- **Dynamic Temperature** — 0.8 for creative exploration, 0.4 for precise combat logic

## Prerequisites

1. **Python 3.10+**
2. **Ollama** installed and running locally — [Install Ollama](https://ollama.com)
3. Pull the required models:
   ```bash
   ollama pull llama3.2
   ollama pull nomic-embed-text
   ```

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd DnD-AI

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## How to Run

Make sure Ollama is running (`ollama serve`), then:

```bash
python main.py
```

You will be prompted to create a character (name and class) and optionally enable Text-to-Speech narration.

## In-Game Commands

| Command | Description |
|---------|-------------|
| `help` | Show all available commands |
| `quit` | Save the session and exit the game |
| `state` | Display your full character sheet (HP, class, inventory, quests) |
| `combat` | Switch to combat mode (tactical DM logic, temperature 0.4) |
| `explore` | Switch to exploration mode (creative DM logic, temperature 0.8) |
| `roll <n>` | Manually roll a die (e.g., `roll 20` for a d20) |
| `quests` | View your quest log |

Any other input is treated as a player action and sent to the AI Dungeon Master.

## Project Structure

```
DnD-AI/
├── main.py          # Game loop, command handling, input/output
├── gm_agent.py      # LLM agent with planning, tool calling, and response generation
├── tools.py         # Dice rolling functions and tool schema definitions
├── game_state.py    # Player state management (HP, inventory, location, quests)
├── rag.py           # ChromaDB embedding store, lore loading, and context retrieval
├── session.py       # Session save/load to JSON
├── tts.py           # Text-to-Speech narration using pyttsx3
├── data/            # D&D lore text files (rules, spells, monsters, classes, locations)
├── requirements.txt # Python dependencies
└── .gitignore       # Excludes venv, chroma_db, session.json, etc.
```

## Example Gameplay

```
[HP: 20/20 | Loc: Starting Area | Mode: Exploration]
Hero > I look around the tavern

[System] The Dungeon Master is thinking...

[DM]: The Yawning Portal is alive with activity tonight. Flickering torchlight
dances across weathered wooden beams...

Hero > I attack the goblin

  🎲 Skill Check: Attack (DC 15)
  Hero rolled a 17 for Attack against DC 15. Success!

[DM]: Your blade finds its mark, slicing through the goblin's leather armor...
```
