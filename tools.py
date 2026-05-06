import random

def roll_dice(sides: int) -> int:
    """
    Rolls a single dice with the specified number of sides.
    
    Args:
        sides (int): The number of sides on the dice.
        
    Returns:
        int: The result of the roll (a random number between 1 and sides).
    """
    return random.randint(1, sides)

def roll_for(skill: str, dc: int, player: str) -> str:
    """
    Rolls a d20 for a skill check and determines if it is a success or failure against a Difficulty Class (DC).
    
    Args:
        skill (str): The name of the skill being rolled for.
        dc (int): The difficulty class that the roll needs to meet or exceed.
        player (str): The name of the player character making the roll.
        
    Returns:
        str: A message indicating the result of the roll (critical success, success, failure, or critical failure).
    """
    roll = roll_dice(20)
    
    if roll == 20:
        return f"{player} rolled a 20 for {skill} against DC {dc}. Critical success!"
    elif roll == 1:
        return f"{player} rolled a 1 for {skill} against DC {dc}. Critical failure!"
    elif roll >= dc:
        return f"{player} rolled a {roll} for {skill} against DC {dc}. Success!"
    else:
        return f"{player} rolled a {roll} for {skill} against DC {dc}. Failure."

def calculate_damage(dice_count: int, dice_sides: int, bonus: int = 0) -> dict:
    """
    Rolls a specified number of dice to calculate damage, optionally adding a flat bonus.
    
    Args:
        dice_count (int): The number of dice to roll.
        dice_sides (int): The number of sides on each dice.
        bonus (int): An optional flat bonus to add to the total damage. Defaults to 0.
        
    Returns:
        dict: A dictionary containing the individual rolls, the total of the rolls, the bonus, and the final total.
    """
    rolls = [roll_dice(dice_sides) for _ in range(dice_count)]
    total = sum(rolls)
    final = total + bonus
    
    return {
        "rolls": rolls,
        "total": total,
        "bonus": bonus,
        "final": final
    }

# Tool schema definition for OpenAI/Ollama tool calling format
TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "roll_for",
            "description": "Roll a d20 for a skill check and determine success or failure",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill": {
                        "type": "string",
                        "description": "The name of the skill being checked"
                    },
                    "dc": {
                        "type": "integer",
                        "description": "The difficulty class (DC) the roll needs to beat"
                    },
                    "player": {
                        "type": "string",
                        "description": "The name of the player making the check"
                    }
                },
                "required": ["skill", "dc", "player"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_damage",
            "description": "Apply damage to the player character after an enemy attack",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "integer",
                        "description": "Amount of damage dealt"
                    }
                },
                "required": ["amount"]
            }
        }
    }
]
