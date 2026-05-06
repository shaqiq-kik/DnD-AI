"""
tts.py

Innovation Feature: Text-to-Speech Narration
This module provides a Text-to-Speech (TTS) narrator to read out the Dungeon Master's 
descriptions, enhancing the immersion of the D&D game.

Requirements:
- pip package needed: pyttsx3
- To install: pip install pyttsx3

This script is designed to gracefully handle environments where pyttsx3 is not installed,
falling back to standard print statements. On macOS, pyttsx3 utilizes the built-in 
'say' command, meaning no additional system dependencies are required.
"""

import sys

# Attempt to import pyttsx3, gracefully handling the case where it's missing
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("Warning: 'pyttsx3' is not installed. Text-to-Speech narration is disabled.", file=sys.stderr)
    print("To enable TTS, run: pip install pyttsx3", file=sys.stderr)


class Narrator:
    """
    Handles text-to-speech functionality to narrate the Dungeon Master's lines.
    """
    def __init__(self):
        self.engine = None
        if TTS_AVAILABLE:
            try:
                # Initialize the pyttsx3 engine
                self.engine = pyttsx3.init()
                
                # Set voice rate to 150 (slightly slower for dramatic DM effect)
                self.engine.setProperty('rate', 150)
                
                # Set volume to maximum (1.0)
                self.engine.setProperty('volume', 1.0)
            except Exception as e:
                print(f"Warning: Failed to initialize the TTS engine: {e}", file=sys.stderr)
                self.engine = None

    def speak(self, text: str):
        """
        Speaks the given text if TTS is available and initialized.
        Otherwise, it falls back to printing the text.
        """
        if TTS_AVAILABLE and self.engine:
            self.engine.say(text)
            self.engine.runAndWait()
        else:
            # Fallback behavior when TTS fails or is missing
            print(f"[Narrator fallback]: {text}")

    def set_rate(self, rate: int):
        """
        Adjusts the speaking speed of the TTS engine.
        """
        if TTS_AVAILABLE and self.engine:
            self.engine.setProperty('rate', rate)

    def stop(self):
        """
        Stops the speech engine.
        """
        if TTS_AVAILABLE and self.engine:
            self.engine.stop()


def narrate(text: str, enabled: bool = True):
    """
    Standalone helper function to speak text out loud.
    Creates a Narrator instance and speaks the text if enabled and available.
    Safe to call even if pyttsx3 is not installed.
    """
    if enabled:
        narrator = Narrator()
        narrator.speak(text)


# Simple test block that executes when the script is run directly
if __name__ == "__main__":
    print("Testing Text-to-Speech Narration...")
    narrate("Welcome, brave adventurer, to the world of Dungeons and Dragons!")
