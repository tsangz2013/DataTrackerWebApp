# DataTrackerWebApp
Init git commit from Zhi.

# Environment requirements:
Python version >= 3.6.9
linux environment recommanded

# Currencies to be tracked
Currencies to be track should be defined in /resources/metrics_rank.json

-- I assume all the markets are of no significant difference, so I randomly choose one of the markets
-- you can add any of currencies from https://api.cryptowat.ch/markets/coinbase-pro

# Runing the server:

## repare the vir env
python3 -m venv ./env
source ./env/bin/activate

## install packages
pip install -r requirements.txt

## start the server program
python3 app/server.py

---
# TODOs:
## 1. Imporve storage solution: 
Current code writes a db_table module that mimic a storage component using file operations, 
due to lack of time to config and set up real-life DB / middleware for storage, 
which will offer better durability, throughtput, consistency and concurrency-control.

Should consider use kafka or other timeseries-friendly storage solution like MongoDB and such.
So as it could boost the performance of adding new price point, and do windowing of the 24 hours data points:
somehow having 2 pointers for a window between 24-hour ago and now, 
and this will make standard-deviation calculation much easier.

## 2. Scale-out and Separate functionlities:
This website should be build into parts:

### (1) storage - db (replicated preferred) with cache: 
should be a layer of cache (redis), plus a timeseries-friendly db;
the cache stores the states: [rank, standard-deviation, price-sum, square-price-sum] for all currency,
where they can all be derived from the data in db, and is for performance boost

### (2) the front-end - a pool of scalable replica processes: 
should be stateless, only read and serve latest time-series and rank from the storage layer

### (3) the data-fetcher - a pool of scalable replica processes: 
should be stateless, periodically fetch metrics from external API, and update the storage:
update both the cache and the db, in ONE transaction if XA-TX is supported

## 3. Improvement:
### (1) ranking
Now the ranking of the currencies are done by data-fetcher, who gather all the std-dev info in one place and do a ranking, which is very good, as number of fetcher scales up, adds computation duplication 

To improve, when a data-fetcher fetch the data, it only updates [standard-deviation, price-sum, square-price-sum] the cache and db, and have another party to do this centralized [rank] calculation periodically in the cache.

### (2) mimic cache in the current code
current code is not organized well, to mimic storage with cache, I can move many veriables from metrics-fetcher to db_tables

---
# Challenge to address:
## Scalability: 
1. What would you change if you needed to track many metrics?: *Change the REST API to serve multiple metrics, and use batch db query*

2. What if you needed to sample them more frequently? *Add more data-fetcher process, and each process fetch a set of currencies*

3. What if you had many users accessing your dashboard to view metrics? *Add more front-end process replica and add more read-replica for storage*

## Testing: 
1. unit test for code method snippets

2. component by component tests, front-end / data-fetcher / rank-updater / storage-cache, each part need to be tested by mocking the other components
3. test together, by mocking the external remove API: failure of each part, see if they can recover quickly, with correct state.

## Alert feature
1. Add below logic into the data-fetch processes: maintains the 1-hour average price in the cache-layer of storage,
and check if the latest price is 3X the 1-hour average, if so, send the alert to a message queue (e.g. kafka).

2. Add another pool of processes consuming from the alert queue, whenever consumes a message, fire the alert message to user (also pool should also be scalable).
