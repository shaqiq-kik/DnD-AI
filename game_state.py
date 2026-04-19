class GameState:
    def __init__(self, name, char_class, max_hp=20):
        self.name = name
        self.char_class = char_class
        self.max_hp = max_hp
        self.hp = max_hp
        self.inventory = []
        self.location = "Starting Area"
        self.quest_log = []

    def update_hp(self, amount):
        """Adds to HP (positive to heal, negative to damage)."""
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        elif self.hp < 0:
            self.hp = 0

    def update_location(self, new_location):
        """Updates the player's current location."""
        self.location = new_location

    def add_item(self, item):
        """Adds an item to the inventory."""
        self.inventory.append(item)

    def remove_item(self, item):
        """Removes an item from the inventory if it exists."""
        if item in self.inventory:
            self.inventory.remove(item)

    def add_quest(self, quest):
        """Adds a new quest to the quest log."""
        self.quest_log.append(quest)

    def display_state(self):
        """Prints the current game state out to the terminal."""
        print("\n--- Current Game State ---")
        print(f"Name: {self.name} | Class: {self.char_class}")
        print(f"HP: {self.hp}/{self.max_hp} | Location: {self.location}")
        
        inv_str = ", ".join(self.inventory) if self.inventory else "Empty"
        print(f"Inventory: {inv_str}")
        
        quest_str = ", ".join(self.quest_log) if self.quest_log else "None"
        print(f"Quests: {quest_str}")
        print("--------------------------\n")
