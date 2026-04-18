import json, re, time, threading
import sqlite3 as lite
from queue import Queue
import datetime as dt
from sense_hat import SenseHat, ACTION_PRESSED, ACTION_RELEASED
from enum import Enum
from signal import pause

JSON_FILE_NAME = "config.json"
DB_NAME = "datalog.db"
TABLE_NAME = "datalog"
CHARACTERS_JSON = "lowres_characters.json"

CREATE_TABLE_QUERY = f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME}(
    timestamp TEXT,
    temperature REAL,
    temperatureCate TINYTEXT,
    humidity REAL,
    humidityCate TINYTEXT
)"""

INSERT_DATA_QUERY = f"""INSERT INTO {TABLE_NAME} VALUES(?, ?, ?, ?, ?)"""
DROP_TABLE_QUERY = f"""DROP TABLE IF EXISTS {TABLE_NAME}"""

SELECT_QUERY = f"""SELECT * FROM {TABLE_NAME}"""

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

TEMP_COLOR = {
    "Cold": COLOR.ICE_BLUE,
    "Comfortable": COLOR.BALANCED_GREEN,
    "Hot": COLOR.RED_ORANGE
}

HUMID_COLOR = {
    "Dry": COLOR.YELLOW_BROWN,
    "Comfortable": COLOR.GENTLE_BLUE,
    "Wet": COLOR.DEEP_TEAL
}


class ConfigReader:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    _config_data = {
        "temperature": None,
        "humidity": None,
        "interval": None
    }

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        with self.__class__._lock:
            if not self.__class__._initialized:
                self._config_file = open(JSON_FILE_NAME, "r")
                self._cdata = json.load(self._config_file)

                self.close_file()

                self.__values_setter()
                self.__class__._initialized = True

    def get_raw_data(self):
        return self._cdata

    def __validate_structure(self) -> bool:
        if not isinstance(self._cdata, dict):
            raise ValueError("Incorrect config file format.")
        if len(self._cdata) != 3:
            raise ValueError("Config file must contain exactly three keys: 'temperature', 'humidity', and 'interval'.")
        if 'temperature' not in self._cdata or 'humidity' not in self._cdata or 'interval' not in self._cdata:
            raise ValueError("Config file must contain keys 'temperature', 'humidity', and 'interval'.")

        thresholds = {
            "temperature": ("cold", "comfortable", "hot"),
            "humidity": ("dry", "comfortable", "wet")
        }

        for mtype in ("temperature", "humidity"):
            if not isinstance(self._cdata[mtype], dict):
                raise ValueError(f"Incorrect format for key '{mtype}'.")
            if len(self._cdata[mtype]) != 1:
                raise ValueError(f"Key '{mtype}' must contain exactly one sub-key: 'thresholds'.")
            if "thresholds" not in self._cdata[mtype]:
                raise ValueError(f"Key '{mtype}' must contain the 'thresholds' sub-key.")

            if not isinstance(self._cdata[mtype]['thresholds'], dict):
                raise ValueError(f"Incorrect format for sub-key 'thresholds' in key '{mtype}'.")
            if len(self._cdata[mtype]['thresholds']) != 3:
                raise ValueError(f"Sub-key 'thresholds' in key '{mtype}' must contain exactly three categories: {thresholds[mtype]}.")

            if thresholds[mtype][0] not in self._cdata[mtype]['thresholds'] or thresholds[mtype][1] not in self._cdata[mtype]['thresholds'] or thresholds[mtype][2] not in self._cdata[mtype]['thresholds']:
                raise ValueError(f"Sub-key 'thresholds' in key '{mtype}' must contain the categories: {thresholds[mtype]}")

    def __validate_values(self):
        value_validation_regex = r'^([<>][+-]?\d+(?:\.\d+)?|[+-]?\d+(?:\.\d+)?/[+-]?\d+(?:\.\d+)?)$'

        interval_value = self._cdata['interval']
        if not isinstance(interval_value, int):
            raise ValueError("Invalid data type for 'interval'. Must be an integer.")
        if interval_value <= 0:
            raise ValueError("'interval' value must be a positive integer")
        if (interval_value % 10) != 0:
            raise ValueError("'interval' value must be a multiple of 10")

        for mtype in ("temperature", "humidity"):
            threshold_values = self._cdata[mtype]['thresholds'].values()
            for value in threshold_values:
                if not isinstance(value, str):
                    raise ValueError(f"Invalid data type in key '{mtype}'. Must be a string. i.e., '<5' or '5/10'")
                if not re.match(value_validation_regex, value):
                    raise ValueError(f"Invalid threshold value '{value}' in key '{mtype}'. i.e., '<5' or '5/10'.")

    def __values_setter(self):
        self.__validate_structure()
        self.__validate_values()

        for mtype in ("temperature", "humidity"):
            threshholds = self._cdata[mtype]['thresholds'].values()
            self._config_data[mtype] = tuple(threshholds)

        self._config_data['interval'] = self._cdata['interval']

    def get_config_values(self):
        return self._config_data

    def get_config_interval(self):
        return self._config_data['interval']

    def close_file(self):
        if hasattr(self, "_config_file") and not self._config_file.closed:
            self._config_file.close()

class DBLogger:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    _debug = False
    _paused = False

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        with self.__class__._lock:
            if not self.__class__._initialized:
                self._conn = lite.connect(DB_NAME)
                self._cursor = self._conn.cursor()
                self._cursor.execute(DROP_TABLE_QUERY)
                self._cursor.execute(CREATE_TABLE_QUERY)

                self._config_reader = ConfigReader()
                self._configuration = self._config_reader.get_config_values()
                self._config_reader.close_file()

                self._sense = SenseHat()
                self._sense.stick.direction_up = self.__pause_and_resume_log

                self._data_display = DataDisplay()
                self._history = Queue(maxsize=5)

                self.__class__._initialized = True

    def __categorizer(self, value, mtype='temperature'):
        thresholds = self._configuration[mtype]
        temp_designation = ('Cold', 'Comfortable', 'Hot')
        humid_designation = ('Dry', 'Comfortable', 'Wet')

        designation = temp_designation if mtype == 'temperature' else humid_designation

        for threshold in thresholds:
            if '/' in threshold:
                a, b = threshold.split('/')
                if (value >= float(a) and value <= float(b)) or (value <= float(a) and value >= float(b)):
                    return designation[thresholds.index(threshold)]
                continue
            elif threshold.startswith('<'):
                c = threshold[1:]
                if value < float(c):
                    return designation[thresholds.index(threshold)]
                continue
            elif threshold.startswith('>'):
                d = threshold[1:]
                if value > float(d):
                    return designation[thresholds.index(threshold)]
                continue
        
        return None

    def log_data(self, temp, humid):
        if self._history.full(): self._history.get()

        temp_cate = self.__categorizer(temp)
        humid_cate = self.__categorizer(humid, "humidity")
        curr_time = dt.datetime.now().strftime("%H:%M:%S")
        
        data = (curr_time, temp, temp_cate, humid, humid_cate)
        self._history.put(data)
        self._cursor.execute(INSERT_DATA_QUERY, data)
        self._conn.commit()

        self._data_display.display_data(int(temp), temp_cate, int(humid), humid_cate)
        print(f"Logged data: {data}") if self._debug else None

    def __get_data(self):
        sense = SenseHat()
        calibrated_temp = (sense.get_temperature_from_pressure() + sense.get_temperature_from_humidity()) / 2
        curr_humid = sense.get_humidity()
        return round(calibrated_temp - 5, 2), round(curr_humid - 10, 2)

    def start_log(self, limit=None):
        if limit is not None:
            i = 0
            while i < limit and not self._paused:
                temp, humid = self.__get_data()
                self.log_data(temp, humid)
                i += 1
        else:
            while not self._paused:
                temp, humid = self.__get_data()
                self.log_data(temp, humid)

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = bool(value)

    def __pause_and_resume_log(self, event):
        if event.action == ACTION_PRESSED:
            self._data_display.toggle_pause()
            # self._paused = not self._paused

    def get_history(self):
        return list(self._history.queue)

    def close_db(self):
        if hasattr(self, "_conn") and self._conn:
            self._conn.close()

class SenseHatCharacter:
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

    def get_character_matrix(self, char: str, color=COLOR.WHITE, bgcolor=COLOR.BLACK) -> list:
        if len(char) != 1:
            raise ValueError("Input must be a single character.")
        if char not in self._characters:
            raise ValueError(f"Character '{char}' not found in character set.")

        pixel_char = self._characters[char]
        for index, p in enumerate(pixel_char):
            if p == 0:
                pixel_char[index] = bgcolor.value
            if p == 1:
                pixel_char[index] = color.value

        return pixel_char

class DataDisplay:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    _paused = False

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        with self.__class__._lock:
            if not self.__class__._initialized:
                self._config_reader = ConfigReader()
                self._config_interval = self._config_reader.get_config_interval()
                self._config_reader.close_file()

                self._screen = [COLOR.BLACK.value] * 64

                self.__class__._initialized = True

    def display_data(self, temp, temp_cate, humid, humid_cate):
        sense = SenseHat()
        DISPLAY_INTERVAL = 5
        display_count = self._config_interval / DISPLAY_INTERVAL

        LETTER_START_INDEX = 2
        FIRST_NUMBER_START_INDEX = 24
        SECOND_NUMBER_START_INDEX = 28

        i = 0
        while i != display_count:
            if not self._paused:
                self.__write_letter("T", startAt=LETTER_START_INDEX)
                first_digit = int(temp / 10)
                self.__write_number(first_digit, startAt=FIRST_NUMBER_START_INDEX, color=TEMP_COLOR[temp_cate])
                second_digit = temp % 10
                self.__write_number(second_digit, startAt=SECOND_NUMBER_START_INDEX, color=TEMP_COLOR[temp_cate])
                sense.set_pixels(self._screen)

                time.sleep(DISPLAY_INTERVAL)
                sense.clear()

                self.__write_letter("H", startAt=LETTER_START_INDEX)
                first_digit = int(humid / 10)
                self.__write_number(first_digit, startAt=FIRST_NUMBER_START_INDEX, color=HUMID_COLOR[humid_cate])
                second_digit = humid % 10
                self.__write_number(second_digit, startAt=SECOND_NUMBER_START_INDEX, color=HUMID_COLOR[humid_cate])
                sense.set_pixels(self._screen)

                time.sleep(DISPLAY_INTERVAL)
                sense.clear()
                i += 2

    def __write_letter(self, letter: str, startAt: int, color=COLOR.WHITE, bgcolor=COLOR.BLACK):
        shd = SenseHatCharacter()
        letter_matrix = shd.get_character_matrix(letter, color, bgcolor)

        for i in range(0, 12 - 4 + 1, 4):
            self._screen[startAt:startAt+4] = letter_matrix[i:i+4]
            startAt += 8

    def __write_number(self, number: int, startAt: int, color=COLOR.WHITE, bgcolor=COLOR.BLACK):
        shd = SenseHatCharacter()
        number_matrix = shd.get_character_matrix(str(number), color, bgcolor)

        for i in range(0, 20 - 4 + 1, 4):
            self._screen[startAt:startAt+4] = number_matrix[i:i+4]
            startAt += 8

    def toggle_pause(self):
        self._paused = not self._paused

# class SensorInterface:
#     _run = True
#     _live_mode = True

#     def __init__(self, Debug=False):
#         self._sense = SenseHat()
#         self.dbLogger = DBLogger()
#         self.dbLogger.debug = Debug
#         self._debug = Debug

#         self._sense.stick.direction_up = self.__pause_and_resume_log


#     def start(self):
#         while self._run:
#             self.dbLogger.start_log()

#     def __pause_and_resume_log(self, event):
#         if event.action == ACTION_PRESSED:
#             self._run = not self._run

#             print(self._run)


if __name__ == "__main__":
    # sensor_interface = SensorInterface(Debug=True)
    # sensor_interface.start()
    db_logger = DBLogger()
    db_logger.debug = True
    db_logger.start_log()