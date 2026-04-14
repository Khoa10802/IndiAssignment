import json, re
import threading
from enum import Enum
import sqlite3 as lite

JSON_FILE_NAME = "config.json"
DB_NAME = "datalog.db"
TABLE_NAME = "datalog"

CREATE_TABLE_QUERY = f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME}(
    timestamp TEXT,
    temperature REAL,
    temperatureCate TINYTEXT,
    humidity REAL,
    humidityCate TINYTEXT
)"""

class MTYPE(Enum):
    TEMP = "temperature"
    HUMIDITY = "humidity"

class ConfigReader:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    _temp_threshholds = None
    _temp_interval = None

    _temp_threshholds = None
    _humid_interval = None

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
                self.__validate_structure()
                self.__validate_values()
                self.__class__._initialized = True

    def get_raw_data(self):
        return self._cdata

    def __validate_structure(self) -> bool:
        if not isinstance(self._cdata, dict):
            raise ValueError("Incorrect config file format.")
        if len(self._cdata) != 2:
            raise ValueError("Config file must contain exactly two keys: 'temperature' and 'humidity'.")
        if 'temperature' not in self._cdata or 'humidity' not in self._cdata:
            raise ValueError("Config file must contain keys 'temperature' and 'humidity'.")

        thresholds = {
            "temperature": ("cold", "comfortable", "hot"),
            "humidity": ("dry", "comfortable", "humid")
        }

        for mtype in ("temperature", "humidity"):
            if not isinstance(self._cdata[mtype], dict):
                raise ValueError(f"Invalid data type for key '{mtype}'.")
            if len(self._cdata[mtype]) != 2:
                raise ValueError(f"Key '{mtype}' must contain exactly two sub-keys: 'thresholds' and 'interval'.")
            if "thresholds" not in self._cdata[mtype] or "interval" not in self._cdata[mtype]:
                raise ValueError(f"Key '{mtype}' must contain both 'thresholds' and 'interval' sub-keys.")

            if not isinstance(self._cdata[mtype]['thresholds'], dict):
                raise ValueError(f"Invalid data type for sub-key 'thresholds' in key '{mtype}'.")
            if len(self._cdata[mtype]['thresholds']) != 3:
                raise ValueError(f"Sub-key 'thresholds' in key '{mtype}' must contain exactly three categories: {thresholds[mtype]}.")

            if thresholds[mtype][0] not in self._cdata[mtype]['thresholds'] or thresholds[mtype][1] not in self._cdata[mtype]['thresholds'] or thresholds[mtype][2] not in self._cdata[mtype]['thresholds']:
                raise ValueError(f"Sub-key 'thresholds' in key '{mtype}' must contain the categories: {thresholds[mtype]}")

    def __validate_values(self):
        value_validation_regex = r'^([<>][+-]?\d+(?:\.\d+)?|[+-]?\d+(?:\.\d+)?/[+-]?\d+(?:\.\d+)?)$'

        for mtype in ("temperature", "humidity"):
            threshold_values = self._cdata[mtype]['thresholds'].values()
            interval_value = self._cdata[mtype]['interval']
            if not isinstance(interval_value, (int, float)):
                raise ValueError(f"Invalid data type for 'interval' in key '{mtype}'. Must be numeric.")
            for value in threshold_values:
                if not isinstance(value, str):
                    raise ValueError(f"Invalid data type in key '{mtype}'. Must be a string. i.e., '<5' or '5/10'")
                if not re.match(value_validation_regex, value):
                    raise ValueError(f"Invalid threshold value '{value}' in key '{mtype}'. i.e., '<5' or '5/10'.")
        
    def get_config_values(self, mtype=MTYPE.TEMP):
        if mtype == MTYPE.TEMP: return self._temp_threshholds, self._temp_interval
        if mtype == MTYPE.HUMIDITY: return self._humid_threshholds, self._humid_interval

    def close_file(self):
        if hasattr(self, "_config_file") and not self._config_file.closed:
            print("Closing the config file.")
            self._config_file.close()

class Logger:
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
                self._conn = lite.connect(DB_NAME)
                self._cursor = self._conn.cursor()
                self._cursor.execute(CREATE_TABLE_QUERY)
                self.__class__._initialized = True

    def __temp_categorize(self, configtemp):
        pass

if __name__ == "__main__":
    config_reader = ConfigReader()
    temp_data = config_reader.get_config_values(MTYPE.TEMP)
    print(temp_data)
    
    config_reader.close_file()