import json, threading, time
from sense_hat import SenseHat, ACTION_PRESSED
from enum import Enum

EMOJI_JSON = "emoji.json"

class COLOR(Enum):
    BLACK = [0, 0, 0]
    WHITE = [255, 255, 255]
    RED = [255, 0, 0]

class AnimatedEmoji:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    _debug = False
    _emoji_name = ("smile", "wink", "suprise", "death", "crying")
    _emoji_colors = (COLOR.WHITE, COLOR.WHITE, COLOR.WHITE, COLOR.WHITE, COLOR.WHITE)
    _current_emoji_index = 0
    _frame_one = True

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        with self.__class__._lock:
            if not self.__class__._initialized:
                self._emoji_file = open(EMOJI_JSON, 'r')
                self._emoji = json.load(self._emoji_file)
                self.close_file()

                self._sense = SenseHat()

                self._emoji_names = self.get_emoji_names()
                self.__set_color()

                self._sense.stick.direction_left = self.__switch_left
                self._sense.stick.direction_right = self.__switch_right

                self.__class__._initialized = True

    def start(self):
        while True:
            self.__switch_frame()

    def get_emoji_names(self):
        return tuple(self._emoji.keys())

    def __switch_frame(self):
        self._sense.clear()
        # print(self._emoji.get(self._emoji_names[self._current_emoji_index])[int(self._frame_one)])
        self._sense.set_pixels(self._emoji.get(self._emoji_names[self._current_emoji_index])[int(self._frame_one)])

        time.sleep(1)

        print("Switching frame") if self._debug else None
        self._frame_one = not self._frame_one

    def __set_color(self):
        emoji = self._emoji
        for i, name in enumerate(self._emoji_names):
            for frame in emoji[name]:
                for index, pixel in enumerate(frame):
                    if pixel == 1:
                        frame[index] = self._emoji_colors[i].value
                    elif pixel == 0:
                        frame[index] = COLOR.BLACK.value
                    elif pixel != COLOR.BLACK.value:
                        frame[index] = self._emoji_colors[i].value

    def __switch_left(self, event):
        if event.action == ACTION_PRESSED:
            print("Switch to Left") if self._debug else None
            if self._current_emoji_index == 0:
                self._current_emoji_index = 4
            else: self._current_emoji_index -= 1

    def __switch_right(self, event):
        if event.action == ACTION_PRESSED:
            print("Switch to Right") if self._debug else None
            if self._current_emoji_index == 4:
                self._current_emoji_index = 0
            else: self._current_emoji_index += 1
                    
    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = bool(value)

    @property
    def emoji_colors(self):
        return self._emoji_colors

    @emoji_colors.setter
    def emoji_colors(self, colors):
        if len(colors) != 5:
            raise ValueError("Colors must be set for all 5 emojis")
        if not isinstance(colors, (list, tuple)):
            raise ValueError("Colors must be a list or tuple")
        self._emoji_colors = colors
        self.__set_color()

    def close_file(self):
        if hasattr(self, "_emoji_file") and not self._emoji_file.closed:
            self._emoji_file.close()

if __name__ == "__main__":
    ae = AnimatedEmoji()
    ae.debug = True
    ae.emoji_colors = (COLOR.RED, COLOR.RED, COLOR.WHITE, COLOR.RED, COLOR.WHITE)
    ae.start()
            