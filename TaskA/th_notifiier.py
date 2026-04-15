import json, re, time
import threading
from enum import Enum
import sqlite3 as lite
from queue import Queue
import datetime as dt
from sense_hat import SenseHat

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

INSERT_DATA_QUERY = f"""INSERT INTO {TABLE_NAME} VALUES(?, ?, ?, ?, ?)"""
DROP_TABLE_QUERY = f"""DROP TABLE IF EXISTS {TABLE_NAME}"""

SELECT_QUERY = f"""SELECT * FROM {TABLE_NAME}"""

class MTYPE(Enum):
    TEMP = "temperature"
    HUMIDITY = "humidity"

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
            "humidity": ("dry", "comfortable", "humid")
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

    def close_file(self):
        if hasattr(self, "_config_file") and not self._config_file.closed:
            self._config_file.close()

class DBLogger:
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
                self._cursor.execute(DROP_TABLE_QUERY)
                self._cursor.execute(CREATE_TABLE_QUERY)

                self._config_reader = ConfigReader()
                self._configuration = self._config_reader.get_config_values()
                self._config_reader.close_file()

                self._history = Queue(maxsize=5)

                self.__class__._initialized = True

    def __categorizer(self, value, mtype='temperature'):
        thresholds = self._configuration[mtype]
        temp_designation = ('Cold', 'Comfortable', 'Hot')
        humid_designation = ('Dry', 'Comfortable', 'Humid')

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
        humid_cate = self.__categorizer(temp, "humidity")
        curr_time = dt.datetime.now().strftime("%H:%M:%S")
        
        data = (curr_time, temp, temp_cate, humid, humid_cate)
        self._history.put(data)
        self._cursor.execute(INSERT_DATA_QUERY, data)
        self._conn.commit()

    def __get_data(self):
        sense = SenseHat()
        calibrated_temp = (sense.get_temperature_from_pressure() + sense.get_temperature_from_humidity()) / 2
        curr_humid = sense.get_humidity()
        return round(calibrated_temp, 2), round(curr_humid, 2)

    def start_log(self, limit=None):
        interval = self._configuration['interval']
        if limit is not None:
            for _ in range(limit):
                temp, humid = self.__get_data()
                self.log_data(temp, humid)
                time.sleep(interval)
        else:
            while True:
                temp, humid = self.__get_data()
                self.log_data(temp, humid)
                time.sleep(interval)

    def get_history(self):
        return list(self._history.queue)

    def close_db(self):
        if hasattr(self, "_conn") and self._conn:
            self._conn.close()


class RecordDisplay():
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

                self._data = self._cursor.execute(SELECT_QUERY)
                self.close_db()

                self.__class__._initialized = True

    def close_db(self):
        if hasattr(self, "_conn") and self._conn:
            self._conn.close()

if __name__ == "__main__":
    db_logger = DBLogger()
    db_logger.start_log(limit=6)
    print(db_logger.get_history())
    db_logger.close_db()