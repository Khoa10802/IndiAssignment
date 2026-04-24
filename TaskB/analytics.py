import matplotlib.pyplot as plt
import plotly.express as px
import plotly.subplots as ps
import plotly.io as pio
import threading
import sqlite3 as lite
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from pandas import DataFrame

class ReadDB:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    _db_name = 'datalog.db'
    _table_name = 'datalog'
    _sql = f"SELECT * FROM {_table_name}"

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        with self.__class__._lock:
            self._conn = lite.connect(self._db_name)

            self._df = pd.read_sql(sql=self._sql, con=self._conn)
            self._df = self._df.drop(index=0)

            self.__class__._initialized = True

    def get_data(self) -> DataFrame:
        return self._df

class Plotter(ABC):
    _temp_labels = ('Cold', 'Comfortable', 'Hot')
    _humid_labels = ('Dry', 'Comfortable', 'Wet')

    def __init__(self, png_save=False, randomize_data=False):
        self._rdb = ReadDB()
        self._data = self._rdb.get_data()
        self._data_size = len(self._data)
        self._data['timestamp'].astype('datetime64[ns]')

        self._png_save = png_save
        self._randomize_data = randomize_data

    @abstractmethod
    def scatter_plot(self):
        pass

    @abstractmethod
    def pie_plot(self):
        pass

    def __randomize_cate(self):
        self._data['temperatureCate'] = np.random.choice(self._temp_labels, size=self._data_size)
        self._data['humidityCate'] = np.random.choice(self._humid_labels, size=self._data_size)

    def __randomize_value(self):
        self._data['temperature'] = np.random.randint(20, 45, size=self._data_size)
        self._data['humidity'] = np.random.randint(50, 70, size=self._data_size)

class PlotlyPlotter(Plotter):
    def scatter_plot(self):
        fig = ps.make_subplots(shared_yaxes=True, x_title='Time')

        self._Plotter__randomize_value() if self._randomize_data else None
        fig.add_scatter(x=self._data['timestamp'], y=self._data['temperature'], name='Temperature')
        fig.add_scatter(x=self._data['timestamp'], y=self._data['humidity'], name='Humidity')

        fig.show()
        fig.write_image("scatter-data-plotly.png") if self._png_save else None
        
    def pie_plot(self):
        fig = ps.make_subplots(shared_yaxes=True, rows=1, cols=2, column_titles=['Temperature', 'Humidity'], specs=[[{'type': 'domain'}, {'type': 'domain'}]])

        self._Plotter__randomize_cate() if self._randomize_data else None
        temp_vc = self._data['temperatureCate'].value_counts().to_dict()
        temp_values = tuple(temp_vc[label] for label in self._temp_labels)
        fig.add_pie(values=temp_values, labels=self._temp_labels, row=1, col=1)

        humid_vc = self._data['humidityCate'].value_counts().to_dict()
        humid_values = tuple(humid_vc[label] for label in self._humid_labels)
        fig.add_pie(values=humid_values, labels=self._humid_labels, row=1, col=2)

        fig.show()
        fig.write_image("pie-data-plotly.png") if self._png_save else None

class MPLPlotter(Plotter):
    def scatter_plot(self):
        fig, ax = plt.subplots(figsize=(12, 6))

        self._Plotter__randomize_value() if self._randomize_data else None
        ax.scatter(self._data['timestamp'], self._data['temperature'], color='r')
        ax.scatter(self._data['timestamp'], self._data['humidity'], color='b')

        plt.xlabel('Time')
        plt.ylabel('Temperature (℃) / Humidity (%)')
        plt.title('Temperature and Humidity over Time')
        plt.show()
        fig.savefig("scatter-data-mpl.png") if self._png_save else None

    def pie_plot(self):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

        self._Plotter__randomize_cate() if self._randomize_data else None
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

class PlotterFactory:
    def create_graph(self, plotter_name, plot_type, save_png=False, randomize=False):
        plotter = self.__get_plotter(plotter_name)(save_png, randomize)
        if plot_type == "scatter":
            plotter.scatter_plot()
        if plot_type == "pie":
            plotter.pie_plot()

    @staticmethod
    def __get_plotter(plotter_name):
        if plotter_name == "Matplotlib":
            return MPLPlotter
        elif plotter_name == "Plotly":
            return PlotlyPlotter
        return None

if __name__ == '__main__':
    plot = PlotterFactory()
    plot.create_graph("Matplotlib", "pie", save_png=True, randomize=True)