"""
Mimic the database APIs
"""
import os
import sys
import json
import collections
from pkg_resources import resource_string
from readerwriterlock import rwlock

class db_handler:
	# to add concurrent-control
	MetricsTankTable = None
	stdTableLock = rwlock.RWLockWrite()
	MetricsHistoryTable = None
	historyTableLock = rwlock.RWLockWrite()


	def __init__(self, db_file_path):
		# mimic initialize the DB using files: view the files like the db tables

		# of DB table: all metrics supported, and the standard deviation
		self.MetricsTankTable = os.path.join(db_file_path, 'metrics_rank.json')
		file = open(self.MetricsTankTable, "r")
		MetricsStdDevCache = collections.defaultdict(float, json.loads(file.read()))

		# of DB table: time series of all metrics
		self.MetricsHistoryTable = {}

		for name in MetricsStdDevCache.keys():
			file_path = os.path.join(db_file_path, "metrics_history_" + name + ".txt")
			self.MetricsHistoryTable[name] = file_path


	def getAllMetricsRank(self):
		with self.stdTableLock.gen_rlock():
			file = open(self.MetricsTankTable, "r")
			return collections.defaultdict(int, json.loads(file.read()))

	def getMetricsRank(self, metrice_name: str):
		with self.stdTableLock.gen_rlock():
			file = open(self.MetricsTankTable, "r")
			MetricsStdDevCache = collections.defaultdict(int, json.loads(file.read()))

			if metrice_name not in MetricsStdDevCache:
				raise BaseException("metrics_name not defined: " + metrics_name)
			return MetricsStdDevCache[metrice_name]

	def updateMetricsRank(self, ranking):
		with self.stdTableLock.gen_wlock():
			# update and write
			file = open(self.MetricsTankTable, "w")
			json.dump(ranking, file)
			file.close()

	def getMetricsPriceHistory(self, metrice_name: str, start_time: int = 0, end_time: int = sys.maxsize):
		with self.historyTableLock.gen_rlock():
			if metrice_name not in self.MetricsHistoryTable:
				raise BaseException("metrics_name not defined: " + metrics_name)

			history = []
			try:
				file = open(self.MetricsHistoryTable[metrice_name], "r")
				for line in file:
					ts, price = line.split(",")
					if start_time <= int(ts) <= end_time:
						history.append((int(ts), float(price)))
				file.close()
			except FileNotFoundError:
				open(self.MetricsHistoryTable[metrice_name], "w+").close()
			return history	

	def insertNewMetricsPrice(self, metrice_name: str, timestamp: int, price: float):
		with self.historyTableLock.gen_wlock():
			file = open(self.MetricsHistoryTable[metrice_name], "a+")
			file.write(str(timestamp) + ',' + str(price) + "\n")
			file.close()
		pass
