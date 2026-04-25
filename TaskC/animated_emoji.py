import json, threading, time
from sense_hat import SenseHat, ACTION_PRESSED
from enum import Enum

EMOJI_JSON = "emoji.json"

class COLOR(Enum):
    BLACK = [0, 0, 0]
    WHITE = [255, 255, 255]
    RED = [255, 0, 0]
    BLUE = [0, 0, 255]
    LIGHT_YELLOW = [255, 255, 70]
    LIGHT_BLUE = [135, 206, 235]

color_index = {
    0: COLOR.BLACK,
    1: COLOR.WHITE,
    2: COLOR.RED,
    3: COLOR.BLUE,
    4: COLOR.LIGHT_YELLOW,
    5: COLOR.LIGHT_BLUE
}

class AnimatedEmoji:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    _debug = False
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

                self._allow_shaking = True

                self.__class__._initialized = True

    def start(self):
        i = 0
        while True:
            if not self._allow_shaking:
                i += 1
                if i == 3:
                    self._allow_shaking = True
                    i = 0
                
            acceleration = self._sense.get_accelerometer_raw()
            x = abs(acceleration['x'])
            y = abs(acceleration['y'])
            z = abs(acceleration['z'])

            if self._allow_shaking:
                if x > 1.5 or y > 1.5 or z > 1.3:
                    if self._current_emoji_index == 4:
                        self._current_emoji_index = 0
                    else: 
                        self._current_emoji_index += 1
                    print("Move to next Emoji") if self._debug else None
                    self._allow_shaking = False
                    continue

            self.__switch_frame()

    def get_emoji_names(self):
        return tuple(self._emoji.keys())

    def __switch_frame(self):
        self._sense.clear()
        self._sense.set_pixels(self._emoji.get(self._emoji_names[self._current_emoji_index])[int(self._frame_one)])

        time.sleep(1)

        print("Switching frame") if self._debug else None
        self._frame_one = not self._frame_one

    def __set_color(self):
        emoji = self._emoji
        for i, name in enumerate(self._emoji_names):
            for frame in emoji[name]:
                for index, pixel in enumerate(frame):
                    frame[index] = color_index[pixel].value

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

    def close_file(self):
        if hasattr(self, "_emoji_file") and not self._emoji_file.closed:
            self._emoji_file.close()

if __name__ == "__main__":
    ae = AnimatedEmoji()
    ae.debug = True
    ae.start()
            