from sense_hat import SenseHat, ACTION_PRESSED
import sys, math, json
from collections import deque
from enum import Enum

sys.path.insert(0, "../Helper")

import SenseHatCharacter as character

CHARACTERS_JSON = "lowres_characters.json"

class COLOR(Enum):
    BLACK = [0, 0, 0]
    WHITE = [255, 255, 255]

class MyCalculator:
    def __init__(self, Debug=False):
        self._sense = SenseHat()
        self.x = 4

        self._sense.stick.direction_up = self.__add_up
        self._sense.stick.direction_down = self.__sub_down
        self._sense.stick.direction_left = self.__squared_left
        self._sense.stick.direction_right = self.__sqrt_right
        self._sense.stick.direction_middle = self.__reset_middle

        self._shc = character.SenseHatCharacter()
        self._screen = [COLOR.BLACK.value] * 64

        self._history = deque(maxlen=3)

        self._debug = Debug

    def start(self):
        SINGLE_DIGIT_POSTION = 17
        DOUBLE_DIGIT_1ST_POSITION = 16
        DOUBLE_DIGIT_2ND_POSITION = 20

        while True:
            if self.x < 10:
                self.__write_number(self.x, startAt=SINGLE_DIGIT_POSTION)
                self._sense.set_pixels(self._screen)
            else:
                first_digit = self.x // 10
                second_digit = self.x % 10
                self.__write_number(first_digit, startAt=DOUBLE_DIGIT_1ST_POSITION)
                self.__write_number(second_digit, startAt=DOUBLE_DIGIT_2ND_POSITION)
                self._sense.set_pixels(self._screen)   

    def __add_up(self, event):
        if event.action == ACTION_PRESSED: 
            self._history.append(self.x)
            self.x = min(self.x + 1, 99)

            self._screen = [COLOR.BLACK.value] * 64
            self._sense.clear()

            print(f"Added 1 ({self.x})") if self._debug else None

    def __sub_down(self, event):
        if event.action == ACTION_PRESSED: 
            self._history.append(self.x)
            self.x = max(self.x - 1, 0)

            self._screen = [COLOR.BLACK.value] * 64
            self._sense.clear()

            print(f"Subtracted 1 ({self.x})") if self._debug else None

    def __squared_left(self, event):
        if event.action == ACTION_PRESSED:
            self._history.append(self.x)
            self.x = min(self.x ** 2, 99)

            self._screen = [COLOR.BLACK.value] * 64
            self._sense.clear()

            print(f"Squared ({self.x})") if self._debug else None

    def __sqrt_right(self, event):
        if event.action == ACTION_PRESSED:
            self._history.append(self.x)
            self.x = int(math.sqrt(self.x))

            self._screen = [COLOR.BLACK.value] * 64
            self._sense.clear()

            print(f"Square-rooted ({self.x})") if self._debug else None

    def __reset_middle(self, event):
        if event.action == ACTION_PRESSED:
            self._history.append(self.x)
            self.x = 4
            
            self._screen = [COLOR.BLACK.value] * 64
            self._sense.clear()

            print("Reset") if self._debug else None

    def __write_number(self, number: int, startAt: int):
        number_matrix = self._shc.get_character_matrix(str(number))
        for i in range(0, 20 - 4 + 1, 4):
            self._screen[startAt:startAt+4] = number_matrix[i:i+4]
            startAt += 8

if __name__ == "__main__":
    calculator = MyCalculator(Debug=True)
    calculator.start()


    

        