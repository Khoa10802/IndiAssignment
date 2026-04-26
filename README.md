# COSC2790 (PIoT) - Assignment 3
## Task list:

- Task A:
	 - [x] Create [config.json](https://github.com/Khoa10802/IndiAssignment/blob/master/TaskA/config.json) that stores the **temperature, humidity category ranges, and data sampling interval**.
	 - [x] Read and **validate** temperature, humidity category ranges, and data sampling interval.
	 - [x] (**Live Mode**) Obtain temperature and humidity data using sensors repeatedly with the **predetermined interval**.
	 - [x] (**Live Mode**)Sensor calibration (temperature)
	 - [x] (**Live Mode**)Define the temperature and humidity category using the ranges from [config.json](https://github.com/Khoa10802/IndiAssignment/blob/master/TaskA/config.json).
	 - [x] (**Live Mode**)Log the obtained **sensor data and respective categories** into SQLite database (datalog.db)
	 - [x] (**Live Mode**)Correctly display the data recorded on the Sense Hat LED matrix.
	 - [x] (**Live Mode**) The display must be **alternate** between temperature and humidity every **5 seconds**.
	 - [x] (**Live Mode**)The display must also have **different colors** dependent on the **categories**.
	 - [x] (**Live Mode**) Pressing on the **UP joystick** will pause and unpause the displaying and logging process.
	 - [x] (**Live Mode**) The LED matrix must **retain while pausing**.
	 - [x] (**Live Mode**) While paused, pressing the **MIDDLE joystick** will switch to **History Mode**.
	 - [x] (**History Mode**) Display the last 5 records.
	 - [x] (**History Mode**) Pressing the **MIDDLE joystick** will switch to **Live Mode**.
	 - [x] Mode indication (**Live** & **History**)
- Task B:
	 - [x] Read data from database.
	 - [x] Generate 2 different visualizations (scatter & pie) with 2 libraries (Matplotlib & Plotly)
	 - [ ] Save visualizations as images.
- Task C:
	 - [x] Create [animated_emoji.json](https://github.com/Khoa10802/IndiAssignment/blob/master/TaskC/animated_emoji.py) for list of emoji matrixes (at least 3 color and 2 animation frames per emoji)
	 - [x] Each emoji must be displayed **once at a time**.
	 - [x] Pressing **LEFT** and **RIGHT joystick** to change emoji accordingly.
	 - [x] **Shaking** will also change the emoji.
	 - [x] Have a cooldown period for shaking action.
- Task D:
	 - [x] Have the starting value **x = 4**.
	 - [x] The current value of **x** must always be displayed on the Sense HAT LED matrix.
	 - [x] Having different joystick directions perform the correct operations.
	 - [x] Store the last **3** values in **history**.
	 - [x] **Shaking** will **revert** the last operation (does nothing if there is no history)
	 - [x]  Have a cooldown period for shaking action.

## Prerequisites:

 - Clone the repository:
``` BASH
git clone https://github.com/Khoa10802/IndiAssignment
cd IndiAssignment
```
 - Install dependencies:
 ``` BASH
sudo apt update && sudo apt upgrade
```
``` BASH
sudo apt install python3-matplotlib python3-plotly
```
``` BASH
sudo pip install numpy pandas
```

## Task A:
### Methodology

 1. The first step is to create file named [config.json](https://github.com/Khoa10802/IndiAssignment/blob/master/TaskC/animated_emoji.py) that must follow these rules:
	- Each configuration file must have the same structure and keywords as provided.
	- Each threshold must a **str** to indicate:
		- a double closed range (i.e., "30/60" or "40/25")
		- a single closed range (i.e., "<35" or ">55")
	- Values can be integers or float (both positive & negative) (i.e., "<10.5", "-20/-10", ...)
	- The real categorizing thresholds will only be between the entered values (i.e., "10/20" does not include 10 and 20)
	- "interval" value must be a multiple of 10 (i.e., 10, 20, 30, ...)

 2. In this step, we need to read config.json, store the data, then validate the structure and values
	 - 
	``` python
	class ConfigReader:
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
				# open config
				self._config_file = open(JSON_FILE_NAME, "r")
				# store config
				self._cdata = json.load(self._config_file)
				# close config
				self.close_file()
				self.__class__._initialized = True
	```
 4. Obtain sensor data + calibration:
 5. Categorize temperature & humidity:
 6. Log sensor data to database:
 7. Display data:
 8. Joystick controller:

### Example


