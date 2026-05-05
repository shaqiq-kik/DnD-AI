import os
import hashlib
import chromadb
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

class EmbeddingStore:
    def __init__(self, collection_name="dnd_lore"):
        """
        Initializes the ChromaDB persistent client and sets up the Ollama embedding function.
        """
        # Create a persistent client storing data in a folder called "chroma_db"
        self.client = chromadb.PersistentClient(path="chroma_db")
        
        # Use Ollama for generating embeddings with the required model
        self.embedding_function = OllamaEmbeddingFunction(
            model_name="nomic-embed-text",
            url="http://localhost:11434/api/embeddings"
        )
        
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
        
    def add_documents(self, documents: list[str], ids: list[str]):
        """
        Adds text chunks to the collection.
        Uses upsert so that duplicates with the same ID simply overwrite safely.
        """
        if not documents:
            return
            
        self.collection.upsert(documents=documents, ids=ids)

    def query(self, query_text: str, n_results: int = 3) -> list[str]:
        """
        Retrieves the most relevant chunks based on similarity to the query.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        if results and "documents" in results and results["documents"]:
            return results["documents"][0]
        return []

def load_lore(store: EmbeddingStore):
    """
    Checks if the data/ folder exists and reads .txt files to split into ~300-word chunks.
    If no files exist, loads a hardcoded list of foundational D&D lore.
    Handles existing chunks by filtering them out based on stable hashes.
    """
    def chunk_text(text: str, chunk_size=300) -> list[str]:
        """Helper to split text into chunks of specified word count."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i + chunk_size]))
        return chunks

    def generate_id(text: str) -> str:
        """Generates a stable MD5 hash ID based on content to prevent duplicates."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    documents = []
    
    # 1. Attempt to load from data/ directory
    if os.path.exists("data") and os.path.isdir("data"):
        files = [f for f in os.listdir("data") if f.endswith(".txt")]
        for file_name in files:
            file_path = os.path.join("data", file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    documents.extend(chunk_text(content, chunk_size=300))
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                
    # 2. If no documents found, use the hardcoded fallback list
    if not documents:
        documents = [
            "Fighter Class: Masters of martial combat, proficient with all armor and weapons. They excel in melee and ranged physical attacks. Action Surge gives them an extra action.",
            "Wizard Class: Supreme magic users defined by their study. They cast spells from a spellbook, use Intelligence for magic, and have the largest spell list.",
            "Rogue Class: Stealthy skirmishers who use sneak attack to deal massive extra damage to distracted foes. They are experts in skills and thieves' tools.",
            "Goblin Monster Stats: Small humanoids with 7 HP, AC 15, and a scimitar attack. They can disengage or hide as a bonus action, making them slippery combatants.",
            "Dragon Monster Stats: Massive winged reptiles. Red dragons breathe fire, blue breathe lightning. High AC, huge HP pools, legendary actions, and terrifying presence.",
            "Fireball Spell: A 3rd-level evocation spell that creates an explosive burst of flame, dealing 8d6 fire damage in a 20-foot radius. Dex save for half.",
            "Healing Spell: Cure Wounds is a 1st-level abjuration spell that restores 1d8 + spellcasting modifier hit points to a creature you touch.",
            "Stealth Rules: To hide, you must be obscured from view. Roll a Dexterity (Stealth) check contested by the opponent's Wisdom (Perception). You gain surprise if successful.",
            "Combat Rules: Combat runs in rounds representing 6 seconds. Each participant gets a turn with an action, bonus action, and movement. Initiative determines the turn order.",
            "Tavern Setting: The Yawning Portal is a famous tavern in Waterdeep. It serves as a gathering place for adventurers seeking rumors, ale, and access to the Undermountain dungeon."
        ]

    # Generate IDs for each document chunk
    ids = [generate_id(doc) for doc in documents]
    
    # Check what is already present in the collection to prevent re-adding duplicates
    existing = store.collection.get(ids=ids)
    existing_ids = set(existing["ids"]) if existing and "ids" in existing else set()
    
    # Filter out duplicates
    new_docs = []
    new_ids = []
    for doc, doc_id in zip(documents, ids):
        if doc_id not in existing_ids:
            new_docs.append(doc)
            new_ids.append(doc_id)
            
    # Add new chunks to the store
    if new_docs:
        store.add_documents(new_docs, new_ids)
        print(f"Successfully loaded {len(new_docs)} new lore chunks into ChromaDB.")
    else:
        print(f"Checked {len(documents)} chunks. All are already present in the database (0 new).")

def get_rag_context(store: EmbeddingStore, query: str) -> str:
    """
    Queries the store for the top 3 most relevant chunks based on the query,
    and joins them with newlines into a single string for prompt injection.
    """
    results = store.query(query, n_results=3)
    return "\n\n".join(results)
