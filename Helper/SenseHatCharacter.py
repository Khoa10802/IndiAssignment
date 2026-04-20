import threading, json
from enum import Enum

CHARACTERS_JSON = "lowres_characters.json"

class COLOR(Enum):
    BLACK = [0, 0, 0]
    WHITE = [255, 255, 255]
    RED = [255, 0, 0]
    RED_ORANGE = [255, 51, 51]
    BALANCED_GREEN = [102, 204, 102]
    ICE_BLUE = [51, 153, 255]
    YELLOW_BROWN = [204, 153, 51]
    GENTLE_BLUE = [102, 153, 204]
    DEEP_TEAL = [0, 102, 153]

class SenseHatCharacter:
    """
    A singleton class responsible for loading character pixel data from a JSON file (lowres_characters.json) 
    and providing methods to retrieve the pixel matrix for a given character with specified colors.
    """
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initializes the SenseHatCharacter instance by loading the character pixel data from JSON file and storing it in memory.
        """
        with self.__class__._lock:
            if not self.__class__._initialized:
                self._characters_file = open(CHARACTERS_JSON, "r")
                self._characters = json.load(self._characters_file)
                self._characters_file.close()

                self.__class__._initialized = True

    def get_character_matrix(self, char: str, color=COLOR.WHITE, bgcolor=COLOR.BLACK) -> list:
        """
        Retrieves the pixel matrix for a given character.

        Parameters:
            char (str): The character to retrieve the pixel matrix for (H, T, or digits 0-9).
            color (COLOR): The color to use for the character pixels.
            bgcolor (COLOR): The background color to use for the character pixels.

        Returns:
            list: A list of pixel values representing the input character.
        """
        if len(char) != 1:
            raise ValueError("Input must be a single character.")
        if char not in self._characters:
            raise ValueError(f"Character '{char}' not found in character set.")

        pixel_char = self._characters[char].copy()
        for index, p in enumerate(pixel_char):
            if p == 0:
                pixel_char[index] = bgcolor.value
            if p == 1:
                pixel_char[index] = color.value

        return pixel_char