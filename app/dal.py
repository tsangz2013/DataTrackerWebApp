import builtins
import os
import collections
import time
import math
from sortedcontainers import SortedList

class DAL:
	UPDATE_INTERVAL_SECONDS = 30
	WINDOW_INTERVAL_SECONDS = 60 * 60 * 24
	# in-memory: sorted-list as ranking helper
	latest_metrics_rank = None	

	def __init__(self, db):
		self.db = db
		self.latest_metrics_rank = self.db.getAllMetricsRank()
		pass

	def get_metrics_list(self):
		return list(self.db.getAllMetricsRank().keys())

	# if the latest data is older than UPDATE_INTERVAL_SECONDS, 
	# read the rank from db, and read the history from db
	# and return
	def get_metrics_data_with_rank(self, name):
		if name not in self.latest_metrics_rank:
			raise BaseException("name: " + name + " not supported")
		
		tsNow = int(time.time())
		ts24HoursAgo = tsNow - self.WINDOW_INTERVAL_SECONDS

		# get 24 hour history
		priceHistory = self.db.getMetricsPriceHistory(name, ts24HoursAgo, tsNow)
		self.latest_metrics_rank = self.db.getAllMetricsRank()

		return {
			"name": name,
			"price_history": priceHistory,
			"rank": self.latest_metrics_rank[name]
		}

