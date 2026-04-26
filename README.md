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
	 - [x] Create [animated_emoji.json](https://github.com/Khoa10802/IndiAssignment/blob/master/TaskC/animated_emoji.py) for list of emoji matrices (at least 3 color and 2 animation frames per emoji)
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
	- "interval" value must be an integer and a multiple of 10 (i.e., 10, 20, 30, ...)

 2. In this step, we need to read config.json, store the data, then validate both the structure and values
	 - When class **ConfigReader** is initialized, data from the configuration file will be read and store in **_cdata**. Additionally, class **ConfigReader** is a Singleton class, so the json file will only need to be opened once to mitigate any potential of file corruption.
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
				# assign thresholds to dictionary attribute
				self.__values_setter()
				self.__class__._initialized = True
	```
	- Next, 2 methods will check and validate the **structure** and **values** within **_cdata**. To ensure the integrity of the structure, we must check for: is the structure type a dictionary, how many elements in that dictionary, and are all the keywords presented.
	``` python
	def __validate_structure(self):
		# type check
		if not isinstance(self._cdata, dict):
			raise ValueError("Incorrect config file format.")
		# check numbers of keywords
		if len(self._cdata) != 3:
			raise ValueError("Config file must contain exactly three keys: 'temperature', 'humidity', and 'interval'.")
		# check presents of keywords
		if 'temperature' not in self._cdata or 'humidity' not in self._cdata or 'interval' not in self._cdata:
			raise ValueError("Config file must contain keys 'temperature', 'humidity', and 'interval'.")
	```

	- On the other hand, for value validation, we employed a mixture of type checking, conditional, and regex matching.

	``` python
	 def __validate_values(self):
        value_validation_regex = r'^([<>][+-]?\d+(?:\.\d+)?|[+-]?\d+(?:\.\d+)?/[+-]?\d+(?:\.\d+)?)$'

        interval_value = self._cdata['interval']
        # type check
        if not isinstance(interval_value, int):
            raise ValueError("Invalid data type for 'interval'. Must be an integer.")
        # conditional check
        if interval_value <= 0:
            raise ValueError("'interval' value must be a positive integer")
        # conditional check
        if (interval_value % 10) != 0:
            raise ValueError("'interval' value must be a multiple of 10")

		for mtype in ("temperature", "humidity"):
			threshold_values = self._cdata[mtype]['thresholds'].values()
			for value in threshold_values:
				# type check
				if not isinstance(value, str):
					raise ValueError(f"Invalid data type in key '{mtype}'. Must be a string. i.e., '<5' or '5/10'")
				# regex matching
				if not re.match(value_validation_regex, value):
					raise ValueError(f"Invalid threshold value '{value}' in key '{mtype}'. i.e., '<5' or '5/10'.")
	```

	- Lastly, after validation, we assigned the thresholds to a dictionary attribute for return.

	``` python
	def __values_setter(self):
		# call validation methods
		self.__validate_structure()
		self.__validate_values()

		# assign thresholds to dictionary attribute
		for mtype in ("temperature", "humidity"):
			threshholds = self._cdata[mtype]['thresholds'].values()
			self._config_data[mtype] = tuple(threshholds)

		self._config_data['interval'] = self._cdata['interval']
	```
 3. For step 3, we have class **DBLogger** to handle: database logging, reading sensor data, categorizing, displaying data, and controlling joystick behavior. Below are the methods to sensor reading, categorizing, and data logging.
	``` python
	class DBLogger:
		_debug = False
		_paused = False
		_live = True
		def __init__(self):
			# accessing database
			self._conn = lite.connect(DB_NAME)
			self._cursor = self._conn.cursor()

			self._cursor.execute(DROP_TABLE_QUERY) if DATABASE_RESET else None
			# create table
			self._cursor.execute(CREATE_TABLE_QUERY)

			# get config values
			self._config_reader = ConfigReader()
			self._configuration = self._config_reader.get_config_values()
			self._config_reader.close_file()
			
			# history queue
			self._history = deque(maxlen=5)
	```

	- A small calibration to temperature is applied after its recording. We took the average of temperature obtained from the surrounding pressure and humidity, then subtracted 5 (differences when compared to weather forecast data) to obtain the final values.

	``` python
	def __get_data(self):
		# apply calibration
		calibrated_temp = (self._sense.get_temperature_from_pressure() + self._sense.get_temperature_from_humidity()) / 2
		curr_humid = self._sense.get_humidity()
		return round(calibrated_temp - 5, 2), round(curr_humid, 2)
	```

	- After detecting '/' or '<' or '>', we then assign the temperature or humidity to one of theirs category based on the surrounding numerical values.

	``` python
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
	```

	- For data logging, we get the sensor data, categorize it, and insert it to the table (and the history queue)

	``` python
		def log_data(self):
			# get sensor data
			temp, humid = self.__get_data()

			# categorize temperature and humidity
			temp_cate = self.__categorizer(temp)
			humid_cate = self.__categorizer(humid, "humidity")
			curr_time = dt.datetime.now().strftime("%H:%M:%S")

			# insert data into table and history queue
			data = (curr_time, temp, temp_cate, humid, humid_cate)
			self._history.append(data)
			self._cursor.execute(INSERT_DATA_QUERY, data)
			self._conn.commit()
			return data
	```
 4. To display data on the LED matrix, we use the approach of adding the measurement type letter (T or H) along with the numerical value of temperature and humidity on to an array of 64 (**_screen**). Then we used sense hat method **.set_pixels(_screen)** to change the LED display.
	 - First we made a separate json file containing the matrices of all the digit (0 to 9) and the letters (T and H) called **lowres_character.json**. Of course, because the matrices in the file only contains 1 and 0, we need to convert them into RGB arrays (i.e., [255, 0, 0] for red)
	``` python
		def get_character_matrix(self, char: str, color=COLOR.WHITE, bgcolor=COLOR.BLACK) -> list:
			if len(char) != 1:
				raise ValueError("Input must be a single character.")
			if char not in self._characters:
				raise ValueError(f"Character '{char}' not found in character set.")

			# get character matrix from the json file
			pixel_char = self._characters[char].copy()
			for index, p in enumerate(pixel_char):
				# set 0 to background color
				if p == 0:
					pixel_char[index] = bgcolor.value
				# set 1 to background color
				if p == 1:
					pixel_char[index] = color.value

		return pixel_char
	```

	- We then add the character matrix to **_screen** at the desired index.

	``` python
	def __write_number(self, number: int, startAt: int, color=COLOR.WHITE, bgcolor=COLOR.BLACK):
		number_matrix = self._shc.get_character_matrix(str(number), color, bgcolor)
		for i in range(0, 20 - 4 + 1, 4):
		self._screen[startAt:startAt+4] = number_matrix[i:i+4]
		startAt += 8
	```
	``` python
	def __write_letter(self, letter: str, startAt: int, color=COLOR.WHITE, bgcolor=COLOR.BLACK):
		letter_matrix = self._shc.get_character_matrix(letter, color, bgcolor)
		for i in range(0, 12 - 4 + 1, 4):
		self._screen[startAt:startAt+4] = letter_matrix[i:i+4]
		startAt += 8
	```

	- Then set the LED matrix pixel to _screen
	
	``` python
	def __write_2digit_screen(self, letter: str, fdigit: int, sdigit: int, color, bcolor=COLOR.BLACK):
		LETTER_START_INDEX = 4
		FIRST_DIGIT_START_INDEX = 24
		SECOND_DIGIT_START_INDEX = 28
		# clear _screen
		self._screen = [COLOR.BLACK.value] * 64

		self.__write_letter(letter, startAt=LETTER_START_INDEX)
		self.__write_number(fdigit, startAt=FIRST_DIGIT_START_INDEX, color=color)
		self.__write_number(sdigit, startAt=SECOND_DIGIT_START_INDEX, color=color)
		# set pixel to _screen
		self._sense.set_pixels(self._screen)
	```

	- To repeatedly obtaining new sensor data every the configured interval, we ran an infinite loop. Inside these loop will be our displaying loop cycle. For instance, if we set the sampling interval to 10 seconds, we will first display T15 for 5 seconds, then switch to display H50 for 5 seconds. If the interval is 20 seconds, we need to repeat the displaying again, meaning T15 for 5, H50 for 5, T15 for 5, and H50 for 5.

	``` python
	while True:
 		# get data
		_, temp, temp_cate, humid, humid_cate = self.log_data()
		i = 0
		while i != display_count:
			self.__mode_indicator()

			first_digit = int(temp / 10)
			second_digit = int(temp % 10)
			self.__write_2digit_screen("T", first_digit, second_digit, color=TEMP_COLOR[temp_cate])

			time.sleep(DISPLAY_INTERVAL)

			self._sense.clear()
 
			# write data to screen
			first_digit = int(humid / 10)
			second_digit = int(humid % 10)
			self.__write_2digit_screen("H", first_digit, second_digit, color=HUMID_COLOR[humid_cate])

			time.sleep(DISPLAY_INTERVAL)

			self._sense.clear()
			i += 1
	```

 6. To control the joystick behaviors, we set flags to indicate the state of the operation (**_live** for LIVE or HISTORY mode, **_paused** for PAUSED or UNPAUSED state). Then let the event of the joystick action to toggle these flags.

	``` python
	def __pause_and_resume_log(self, event):
	if event.action == ACTION_PRESSED and self._live:
		self._paused = not self._paused
 	```
 	``` python
	def __mode_switch(self, event):
		if event.action == ACTION_PRESSED and self._paused:
			self._live = not self._live
			if self._live: self._paused = False
  	```

  - Then assign these callback function to the direction of the joystick.

	``` python
  	def __init__(self):
		...
			
        self._sense = SenseHat()
        # assign sense hat behaviors
        self._sense.stick.direction_up = self.__pause_and_resume_log
        self._sense.stick.direction_middle = self.__mode_switch
  	```

  - Then add check for the flag inside our infinite loop, we can change the state of our programm. Additionally, if any flag changes in the middle of the infinite loop, we would only able to view any change until the next interation of the loop. Therefore, we added 'checkpoints' to break out the current loop cycle.

	``` python
  	while True:
            # LIVE MODE
            if self._live:
                # PAUSED/UNPAUSED
                if not self._paused:
                    # get data
                    _, temp, temp_cate, humid, humid_cate = self.log_data()
  					i = 0
  					while i != display_count:
						# Display logic here
  						...
  						
                        # checkpoint for paused
                        if self._paused: break

 						# Display logic here
  						...

                        # checkpoint for paused
                        if self._paused: break

  						i += 1
            
            # HISTORY MODE
            if not self._live:
                index = 0
                while index != len(self._history):
                    _, temp, temp_cate, humid, humid_cate = self._history[index]
  					# Display logic here
					...

                    # checkpoint for live
                    if self._live: break

  					# Display logic here
					...

                    # checkpoint for live
                    if self._live: break
                    index += 1
  	```

7. To display the history, we ustilize a queue to track the last 5 entries.

	``` python
 	def __init__(self):
		...
 
        self._history = deque(maxlen=5)

 	def log_data(self):
		...
 		
        data = (curr_time, temp, temp_cate, humid, humid_cate)
        self._history.append(data)

 		...
        return data
 	```

 	- Another way to get these data is through the database. However, during development, we encountered an error when trying to query the data upon clicking MIDDLE joystick to switch mode. It seems that SQLite Python library does not allow SELECT query if this action is not on the same thread, and the callback function of switching mode of the Sense_hat library run entirely on a different thread.

### Example:

- To run the logger, we just need to:

``` python
db_logger = DBLogger(Debug=False, DBReset=False)
db_logger.start()
```

- If you want to run on debug mode, just set the **Debug** to **True**
- If you want to reset the database every run, set **DBReset** to **True**

## Task B:
### Methodology
1. Gather data from database
   - First, we need to obtain data from the database by SELCT query them. The ReadDB class below gather all data from the database the return via a method as a Panda DataFrame.

	``` python
 	class ReadDB:
	...

    _db_name = 'datalog.db'
    _table_name = 'datalog'
    _sql = f"SELECT * FROM {_table_name}"

	...

    def __init__(self):
		# connect to database
		self._conn = lite.connect(self._db_name)
		# SELCT query all data
		self._df = pd.read_sql(sql=self._sql, con=self._conn)
		self._df = self._df.drop(index=0)
 
    def get_data(self) -> DataFrame:
        return self._df
 	```
2. Scatter and Pie plot with Plotly
   - The process of plotting temperature and humidity over time with Plotly:
     	- Create a subplots with shared x-axis
     	- Add a scatter trace with 'temperature' column as x, and 'time' as y
     	- Add another scatter trace with 'humidity' column as x, and 'time' as y
     	- Show graph

   ``` python
   def scatter_plot(self):
   		# create subplots for temperature and humidity
        fig = ps.make_subplots(shared_xaxes=True, x_title='Time')

        fig.add_scatter(x=self._data['timestamp'], y=self._data['temperature'], name='Temperature')
        fig.add_scatter(x=self._data['timestamp'], y=self._data['humidity'], name='Humidity')

		# show graph
        fig.show()
   ```

   - The process of plotting 2 side-by-side pie charts for temperature and humidity categories" with Plotly:
     	- Create subplots for 2 pie charts
     	- Set the subplots **specs** to type **domain**
     	- Get the numbers of each category of temperature
     	- Add a pie plot with values as the category count, and on column 1 (**col**)
     	- Repeat with humidity
     	- Show graph
  
   	``` python
	def pie_plot(self):
		fig = ps.make_subplots(shared_yaxes=True, rows=1, cols=2, column_titles=['Temperature', 'Humidity'], specs=[[{'type': 'domain'}, {'type': 'domain'}]])
		
		temp_vc = self._data['temperatureCate'].value_counts().to_dict()
		temp_values = tuple(temp_vc[label] for label in self._temp_labels)
		fig.add_pie(values=temp_values, labels=self._temp_labels, row=1, col=1)
		
		humid_vc = self._data['humidityCate'].value_counts().to_dict()
		humid_values = tuple(humid_vc[label] for label in self._humid_labels)
		fig.add_pie(values=humid_values, labels=self._humid_labels, row=1, col=2)
		
		fig.show()
   	```
	
2. Scatter and Pie plot with Matplotlib
   - The process of plotting temperature and humidity over time with Matplotlib:
     	- Create subplots
     	- Plot a scatter with y for time column, and x for temperature coloumn
     	- Plot a scatter with y for time column, and x for humidity column
     	- Set x and y label, plot title
     	- Show graph
     	- Save figure as image if needed

   ``` python
   def scatter_plot(self):
		fig, ax = plt.subplots(figsize=(12, 6))

		ax.scatter(self._data['timestamp'], self._data['temperature'], color='r')
		ax.scatter(self._data['timestamp'], self._data['humidity'], color='b')

		plt.xlabel('Time')
		plt.ylabel('Temperature (℃) / Humidity (%)')
		plt.title('Temperature and Humidity over Time')
		plt.show()
		fig.savefig("scatter-data-mpl.png") if self._png_save else None
   ```

   - The process of plotting 2 side-by-side pie charts for temperature and humidity categories" with Plotly:
     	- Create subplots
     	- Get the numbers of each category of temperature and humidity
     	- Plot pie charts for temperature and humidity with category count
     	- Set titles for 2 pie charts
     	- Show graph
     	- Save figure as image if needed
   ``` python
   def pie_plot(self):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

        temp_vc = self._data['temperatureCate'].value_counts().to_dict()
        temp_values = tuple(temp_vc[label] for label in self._temp_labels)

        humid_vc = self._data['humidityCate'].value_counts().to_dict()
        humid_values = tuple(humid_vc[label] for label in self._humid_labels)

        ax1.pie(temp_values, labels=self._temp_labels)
        ax2.pie(humid_values, labels=self._humid_labels)

        ax1.set_title('Temperature')
        ax2.set_title('Humidity')
        plt.show()
        fig.savefig("pie-data-mpl.png") if self._png_save else None
   ```

### Example:
- To plot a scatter graph with Plotly, we first create an object of **PlotterFactory** class, then pass in 'Plotly' and 'scaater' as the first and second arguement:

``` python
plot = PlotterFactory()
plot.create_graph("Plotly", "scatter", save_png=True, randomize=True)
```

- Additionally, if you want to save the figure as image, **save_png** to **True**
- Also, if your data of category is unifrom in one type or value, you can randomize the data by setting **randomize** to **True**

## Task C:
### Methodology:
1. Create a json (emoji.json) file to store all emoji matrices. Within this file we will have 5 names of emoji, and each one will contain an array (64) of the first and second frame of the emoji.
``` json
{
    "smile": [
        [
            4, 4, 4, 4, 4, 4, 4, 4, 
            4, 1, 1, 4, 4, 1, 1, 4, 
            4, 1, 3, 4, 4, 3, 1, 4, 
            4, 4, 4, 4, 4, 4, 4, 4, 
            4, 4, 4, 4, 4, 4, 4, 4, 
            4, 2, 4, 4, 4, 4, 2, 4, 
            4, 4, 2, 2, 2, 2, 4, 4, 
            4, 4, 4, 4, 4, 4, 4, 4
        ],
        [
            4, 4, 4, 4, 4, 4, 4, 4, 
            4, 1, 1, 4, 4, 1, 1, 4, 
            4, 1, 3, 4, 4, 3, 1, 4,
            4, 4, 4, 4, 4, 4, 4, 4,
            4, 2, 2, 2, 2, 2, 2, 4,
            4, 2, 4, 4, 4, 4, 2, 4,
            4, 4, 2, 2, 2, 2, 4, 4,
            4, 4, 4, 4, 4, 4, 4, 4
        ]
    ]
}
```
2. Read and store the matrices. Using the same principle of singleton of Task A, we only need to open the json file once, then store the data within it as an attribute.
``` python
class AnimatedEmoji:
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
				# open json file
                self._emoji_file = open(EMOJI_JSON, 'r')
				# store emoji matrices
                self._emoji = json.load(self._emoji_file)
				# close json file
                self.close_file()

                self.__class__._initialized = True
```
3. To keep track of the current emoji, we assign an attribute **_current_emoji_index** acting a the emoji index. In order to switch between frames of the emoji, we implement it by toggling. To explain it, we created a flag called **_frame_one** and set it to **True**. To display the first frame the just set the **_screen** attribute to the emoji matrix at index **int(True)**, which would equal to 1. Then wait 1 second and toggle **_frame_one** to False.

``` python
def __switch_frame(self):
        self._sense.clear()
        self._sense.set_pixels(self._emoji.get(self._emoji_names[self._current_emoji_index])[int(self._frame_one)])

        time.sleep(1)

        self._frame_one = not self._frame_one
```

### Example:
 

	

