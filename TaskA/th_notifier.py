import json, re, time, threading, sys
import sqlite3 as lite
from collections import deque
import datetime as dt
from sense_hat import SenseHat, ACTION_PRESSED, ACTION_RELEASED
from enum import Enum
from signal import pause

sys.path.insert(0, "../Helper")

import SenseHatCharacter as character

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
RETRIEVE_LAST_5_QUERY = f"""SELECT * FROM {TABLE_NAME} ORDER_BY timestamp DESC LIMIT 5"""

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
    VIVID_PURPLE = [204, 102, 255]
    DIM_GRAY = [80, 80, 80]

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
    """
    A singleton class responsible for reading and validating the configuration from a JSON file (config.json).
    """

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
        """
        Initializes the ConfigReader instance by reading the configuration from a JSON file 
        and validating its structure and values.
        """
        with self.__class__._lock:
            if not self.__class__._initialized:
                self._config_file = open(JSON_FILE_NAME, "r")
                self._cdata = json.load(self._config_file)

                self.close_file()

                self.__values_setter()
                self.__class__._initialized = True

    def get_raw_data(self):
        """
        Returns the raw and non-validated configuration data loaded from the JSON file.
        """
        return self._cdata

    def __validate_structure(self):
        """
        Validate the structure of the configuration data.
        """
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
        """
        Validate the values, requirements, and formats of the configuration data.
        """
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
        """
        Set the validated configuration values into the _config_data attribute.
        """
        self.__validate_structure()
        self.__validate_values()

        for mtype in ("temperature", "humidity"):
            threshholds = self._cdata[mtype]['thresholds'].values()
            self._config_data[mtype] = tuple(threshholds)

        self._config_data['interval'] = self._cdata['interval']

    def get_config_values(self):
        """
        Returns the validated configuration data loaded from the JSON file.

        Returns:
            dict: A dictionary containing temperature, humidity thresholds, and the logging interval. (see above)
        """
        return self._config_data

    def get_config_interval(self):
        """
        Returns the logging interval value from the configuration data.

        Returns:
            int: The logging interval value.
        """
        return self._config_data['interval']

    def close_file(self):
        """
        Closes the configuration file if it is open.
        """
        if hasattr(self, "_config_file") and not self._config_file.closed:
            self._config_file.close()

class DBLogger:
    """
    A singleton class responsible for logging temperature and humidity data from the Sense HAT to a SQLite database, 
    and displaying the data on the Sense HAT's LED matrix. 
    It also allows pausing/resuming logging 
    and switching between live and history display modes using the joystick.
    """
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    _debug = False
    _paused = False
    _live = True

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initializes the DBLogger instance by setting up the database connection, reading the configuration,
        and setting up the joystick event handlers.
        """
        with self.__class__._lock:
            if not self.__class__._initialized:
                self._conn = lite.connect(DB_NAME)
                self._cursor = self._conn.cursor()
                self._cursor.execute(DROP_TABLE_QUERY) if DATABASE_RESET else None
                self._cursor.execute(CREATE_TABLE_QUERY)

                self._config_reader = ConfigReader()
                self._configuration = self._config_reader.get_config_values()
                self._config_reader.close_file()

                self._sense = SenseHat()
                self._sense.stick.direction_up = self.__pause_and_resume_log
                self._sense.stick.direction_middle = self.__mode_switch

                self._screen = [COLOR.BLACK.value] * 64

                self._shc = character.SenseHatCharacter()

                self._history = deque(maxlen=5)

                self.__class__._initialized = True

    def __categorizer(self, value, mtype='temperature'):
        """
        Categorizing the temperature or humidity value based on the thresholds defined in the configuration.

        Parameters:
            value (float): The temperature or humidity value to categorize.
            mtype (str): The type of measurement, either 'temperature' or 'humidity'.

        Returns:
            str: Cold / Comfortable / Hot for temperature, 
                 Dry / Comfortable / Wet for humidity, 
                 or None.
        """
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

    def log_data(self):
        """
        Logs the current temperature and humidity data to the database and updates the history of last 5 recorded data.

        Returns:
            tuple: Comprised of timestamp, temperature, temperature category, humidity, and humidity category.
        """
        temp, humid = self.__get_data()

        temp_cate = self.__categorizer(temp)
        humid_cate = self.__categorizer(humid, "humidity")
        curr_time = dt.datetime.now().strftime("%H:%M:%S")
        
        data = (curr_time, temp, temp_cate, humid, humid_cate)
        self._history.append(data)
        self._cursor.execute(INSERT_DATA_QUERY, data)
        self._conn.commit()

        print(f"Logged data: {data}") if self._debug else None
        return data

    def start(self):
        """
        Starts the data logging and display loop.
        """
        DISPLAY_INTERVAL = 5
        HISTORY_DISPLAY_INTERVAL = 2
        display_count = (self._configuration['interval'] / DISPLAY_INTERVAL) / 2

        while True:
            if self._live:
                if not self._paused:
                    _, temp, temp_cate, humid, humid_cate = self.log_data()
                    i = 0
                    while i != display_count:
                        self.__mode_indicator()

                        first_digit = int(temp / 10)
                        second_digit = int(temp % 10)
                        self.__write_screen("T", first_digit, second_digit, color=TEMP_COLOR[temp_cate])

                        time.sleep(DISPLAY_INTERVAL)
                        if self._paused: break

                        self._sense.clear()

                        first_digit = int(humid / 10)
                        second_digit = int(humid % 10)
                        self.__write_screen("H", first_digit, second_digit, color=HUMID_COLOR[humid_cate])

                        time.sleep(DISPLAY_INTERVAL)
                        if self._paused: break

                        self._sense.clear()
                        i += 1
            
            if not self._live:
                if len(self._history) == 0: 
                    self.__draw_cross(color=COLOR.RED)
                    self._sense.set_pixels(self._screen)
                    self._screen = [COLOR.BLACK.value] * 64
                index = 0
                while index != len(self._history):
                    self.__mode_indicator()
                    _, temp, temp_cate, humid, humid_cate = self._history[index]
                    print(temp, temp_cate, humid, humid_cate) if self._debug else None
                    first_digit = int(temp / 10)
                    second_digit = int(temp % 10)
                    self.__write_screen("T", first_digit, second_digit, color=TEMP_COLOR[temp_cate])

                    time.sleep(HISTORY_DISPLAY_INTERVAL)

                    self._sense.clear()
                    if self._live: break

                    first_digit = int(humid / 10)
                    second_digit = int(humid % 10)
                    self.__write_screen("H", first_digit, second_digit, color=HUMID_COLOR[humid_cate])

                    time.sleep(HISTORY_DISPLAY_INTERVAL)

                    self._sense.clear()
                    if self._live: break
                    index += 1

    def __get_data(self):
        """
        Retrieves the current temperature and humidity from the Sense Hat, applies calibration, 
        and returns the calibrated values.

        Returns:
            tuple: Calibrated temperature and humidity values.
        """
        calibrated_temp = (self._sense.get_temperature_from_pressure() + self._sense.get_temperature_from_humidity()) / 2
        curr_humid = self._sense.get_humidity()
        return round(calibrated_temp - 5, 2), round(curr_humid, 2)

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = bool(value)

    def __pause_and_resume_log(self, event):
        """
        Callback function for the joystick's up direction to pause or resume logging when pressed.
        """
        if event.action == ACTION_PRESSED:
            self._paused = not self._paused
            print("Logging paused." if self._paused else "Logging resumed.") if self._debug else None

    def __mode_switch(self, event):
        """
        Callback function for the joystick's middle direction to switch between live and history display modes when pressed.
        """
        if event.action == ACTION_PRESSED and self._paused:
            self._live = not self._live
            print("Switching to live mode." if self._live else "Switching to history mode") if self._debug else None

    def __mode_indicator(self):
        self._screen[10] = COLOR.VIVID_PURPLE.value if self._live else COLOR.DIM_GRAY.value

    def __draw_cross(self, color=COLOR.WHITE, bgcolor=COLOR.BLACK):
        X = color.value
        O = bgcolor.value

        cross = [
            O, O, O, O, O, O, O, O,
            O, X, O, O, O, X, O, O,
            O, O, X, O, X, O, O, O,
            O, O, O, X, O, O, O, O,
            O, O, X, O, X, O, O, O,
            O, X, O, O, O, X, O, O,
            O, O, O, O, O, O, O, O,
            O, O, O, O, O, O, O, O
        ]

        self._screen = cross

    def __write_letter(self, letter: str, startAt: int, color=COLOR.WHITE, bgcolor=COLOR.BLACK):
        """
        Inserts the pixel matrix of a letter into the _screen.

        Parameters:
            letter (str): The letter to write (H or T).
            startAt (int): The starting position on the screen.
            color (COLOR): The color of the letter.
            bgcolor (COLOR): The background color.
        """
        letter_matrix = self._shc.get_character_matrix(letter, color, bgcolor)
        for i in range(0, 12 - 4 + 1, 4):
            self._screen[startAt:startAt+4] = letter_matrix[i:i+4]
            startAt += 8

    def __write_number(self, number: int, startAt: int, color=COLOR.WHITE, bgcolor=COLOR.BLACK):
        """
        Inserts the pixel matrix of a number into the _screen.

        Parameters:
            number (int): The number to write (0-9).
            startAt (int): The starting position on the screen.
            color (COLOR): The color of the number.
            bgcolor (COLOR): The background color.
        """
        number_matrix = self._shc.get_character_matrix(str(number), color, bgcolor)
        for i in range(0, 20 - 4 + 1, 4):
            self._screen[startAt:startAt+4] = number_matrix[i:i+4]
            startAt += 8

    def __write_screen(self, letter: str, fdigit: int, sdigit: int, color, bcolor=COLOR.BLACK):
        """
        Writes a letter and two numbers to the screen.

        Parameters:
            letter (str): The letter to write (H or T).
            fdigit (int): The first digit to write (0-9).
            sdigit (int): The second digit to write (0-9).
            color (COLOR): The color of the text.
            bcolor (COLOR): The background color.
        """
        LETTER_START_INDEX = 4
        FIRST_NUMBER_START_INDEX = 24
        SECOND_NUMBER_START_INDEX = 28

        self.__write_letter(letter, startAt=LETTER_START_INDEX)
        self.__write_number(fdigit, startAt=FIRST_NUMBER_START_INDEX, color=color)
        self.__write_number(sdigit, startAt=SECOND_NUMBER_START_INDEX, color=color)
        self._sense.set_pixels(self._screen)

    def close_db(self):
        """
        Closed the database connection if it is open.
        """
        if hasattr(self, "_conn") and self._conn:
            self._conn.close()

if __name__ == "__main__":
    DATABASE_RESET = True
    db_logger = DBLogger()
    db_logger.debug = True
    db_logger.start()