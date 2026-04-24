import matplotlib.pyplot as plt
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
    @abstractmethod
    def scatter_plot(self):
        pass

    @abstractmethod
    def pie_plot(self):
        pass

class PlotlyPlotter(Plotter):
    def __init__(self, png_save=False, randomize_data=False):
        pass
    def scatter_plot(self):
        pass
    def pie_plot(self):
        pass

class MPLPlotter(Plotter):
    _temp_labels = ('Cold', 'Comfortable', 'Hot')
    _humid_labels = ('Dry', 'Comfortable', 'Wet')

    def __init__(self, png_save=False, randomize_data=False):
        self._rdb = ReadDB()
        self._data = self._rdb.get_data()
        self._data_size = len(self._data)
        self._data['timestamp'].astype('datetime64[ns]')

        self._png_save = png_save
        self._randomize_data = randomize_data

    def scatter_plot(self):
        fig, ax = plt.subplots()

        self.__randomize_value() if self._randomize_data else None
        ax.scatter(self._data['timestamp'], self._data['temperature'], color='r')
        ax.scatter(self._data['timestamp'], self._data['humidity'], color='b')

        plt.show()
        fig.savefig("scatter-data.png") if self._png_save else None

    def pie_plot(self):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

        self.__randomize_cate() if self._randomize_data else None
        temp_vc = self._data['temperatureCate'].value_counts().to_dict()
        temp_values = tuple(temp_vc[label] for label in self._temp_labels)

        humid_vc = self._data['humidityCate'].value_counts().to_dict()
        humid_values = tuple(humid_vc[label] for label in self._humid_labels)

        ax1.pie(temp_values, labels=self._temp_labels)
        ax2.pie(humid_values, labels=self._humid_labels)

        plt.show()
        fig.savefig("pie-data.png") if self._png_save else None

    def __randomize_cate(self):
        self._data['temperatureCate'] = np.random.choice(self._temp_labels, size=self._data_size)
        self._data['humidityCate'] = np.random.choice(self._humid_labels, size=self._data_size)

    def __randomize_value(self):
        self._data['temperature'] = np.random.randint(20, 45, size=self._data_size)
        self._data['humidity'] = np.random.randint(50, 70, size=self._data_size)

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
    plot.create_graph("Matplotlib", "scatter", save_png=True, randomize=True)