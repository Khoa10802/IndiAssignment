import json, threading
from enum import Enum

CHARACTERS_JSON = "lowres_characters.json"

class COLOR(Enum):
    BLACK = [0, 0, 0]
    WHITE = [255, 255, 255]

class SenseHatDisplay:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        with self.__class__._lock:
            if not self.__class__._initialized:
                self._characters_file = open(CHARACTERS_JSON, "r")
                self._characters = json.load(self._characters_file)
                self._characters_file.close()

                self.__class__._initialized = True

    def get_character(self, char: str, color=COLOR.BLACK) -> list:
        if len(char) != 1:
            raise ValueError("Input must be a single character.")
        if char not in self._characters:
            raise ValueError(f"Character '{char}' not found in character set.")

        pixel_char = self._characters[char]
        for index, p in enumerate(pixel_char):
            if p == 0:
                pixel_char[index] = COLOR.WHITE.value
            if p == 1:
                pixel_char[index] = COLOR.BLACK.value

        return pixel_char

if __name__ == "__main__":
    sensehatdisplay = SenseHatDisplay()
    print(sensehatdisplay.get_character("T"))


         