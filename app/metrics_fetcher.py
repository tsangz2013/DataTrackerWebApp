import collections
import time
import math
import requests
import threading
import json
from sortedcontainers import SortedList

class metricsFetcher(threading.Thread):
	FETCH_INTERVAL_SECONDS = 10

	# TODO: should move these to storage
	# in-memory: sorted-list as ranking helper
	# a list sorted by the std-dev value, for the ease of getting ranking 
	metrics_sorted = SortedList(key = lambda x: -x[1])	
	metrics_to_std_dev = collections.defaultdict(float)	
	metrics_history_cache = collections.defaultdict(collections.deque)
	metrics_24hour_price_sum = collections.defaultdict(float)
	metrics_24hour_square_price_sum = collections.defaultdict(float)

	# Initial the fetcher with an db connection
	# for each currency, load 24 hours price history from db into memory
	# and calculate the 24 hours price-sum, square-price-sum, and standard-deviation 
	def __init__(self, db):
		threading.Thread.__init__(self)
		self.db = db

		tsNow = int(time.time())
		ts24HourAgo = tsNow - 3600 * 24
		
		# pre-load the 24 hour price history into memory cache
		for name in self.db.getAllMetricsRank().keys():
			# get 24 hour price history
			self.metrics_history_cache[name] = \
				collections.deque(self.db.getMetricsPriceHistory(name, int(time.time()) - ts24HourAgo))

			# calculate 24h sum of price, 24h sum of price^2, and std-dev
			if len(self.metrics_history_cache[name]) > 0:
				self.metrics_24hour_price_sum[name] = \
					sum([price for _, price in self.metrics_history_cache[name]])
				self.metrics_24hour_square_price_sum[name] = \
					sum([price ** 2 for _, price in self.metrics_history_cache[name]])

				a = self.metrics_24hour_square_price_sum[name]
				b = (self.metrics_24hour_price_sum[name] / float(len(self.metrics_history_cache[name]))) ** 2 
				self.metrics_to_std_dev[name] = math.sqrt(a - b)

			# add (name, std-dev) to sorted list
			self.metrics_sorted.add((name, self.metrics_to_std_dev[name]))

		# update the rank using latest data in db
		self.update_std_dev_rank()	
		pass

	# periodically fetch all currencies' latest price, update history and update all their rank
	def run(self):
		while True:
			for name in self.metrics_to_std_dev.keys():
				timestamp, price = self.get_latest_price(name)
				self.add_new_price_change(name, timestamp, price)
			self.update_std_dev_rank()	
			print("sleeping")
			time.sleep(self.FETCH_INTERVAL_SECONDS)
	
	# write into db the newest price with timestamp, and update the in-memory variables
	def add_new_price_change(self, name, timestamp, price):
		# append new price into db
		self.db.insertNewMetricsPrice(name, timestamp, price)
		
		# update in the in-memory variables
		tsNow = int(time.time())
		ts24HourAgo = tsNow - 3600 * 24
		
		# clean up stale prices > 24 hours
		while len(self.metrics_history_cache[name]) > 0 :
			# get left most, if stale, pop
			ts, oldPrice = self.metrics_history_cache[name][0]
			if ts >= ts24HourAgo:
				break

			self.metrics_history_cache[name].popleft()
			self.metrics_24hour_price_sum[name] -= oldPrice 
			self.metrics_24hour_square_price_sum[name] -= oldPrice ** 2

		# add the new price 
		self.metrics_history_cache[name].append((timestamp, price))
		self.metrics_24hour_price_sum[name] += price 
		self.metrics_24hour_square_price_sum[name] += price ** 2
		
	# re-calculate the standard-deviation and the rank for all, write into db
	def update_std_dev_rank(self):
		for name in self.metrics_to_std_dev:
			if len(self.metrics_history_cache[name]) == 0:
				continue

			# re-calculate and insert new std-dev to sorted_list and dict
			a = self.metrics_24hour_square_price_sum[name]
			b = (self.metrics_24hour_price_sum[name] / float(len(self.metrics_history_cache[name]))) ** 2 
			if b == 0:
				print("ERROR: have 24 hour average price == 0 for metrics: " + name)
			
			newStdDev = math.sqrt(a - b)

			# update if change
			if self.metrics_to_std_dev[name] != newStdDev:
				self.metrics_sorted.remove((name, self.metrics_to_std_dev[name]))
				self.metrics_to_std_dev[name] = newStdDev
				self.metrics_sorted.add((name, self.metrics_to_std_dev[name]))

		# re-rank all the metrics
		newRanking = {name: 1 + self.metrics_sorted.index((name, self.metrics_to_std_dev[name])) \
			for name in self.metrics_history_cache}
			
		# update db
		self.db.updateMetricsRank(newRanking)
		pass

	# make http call to the API to get the latest price of a currency
	def get_latest_price(self, name):
		nowTS = int(time.time())
		r = requests.get("https://api.cryptowat.ch/markets/coinbase-pro/{0}/price".format(name))
		content = dict(json.loads(r.text))
		if "result" not in content or "price" not in content["result"]:
			print("ERROR: http call doesn't return correct price")
		print("get latest price for " + name, nowTS, content["result"]["price"])
		return nowTS, content["result"]["price"]


