#!flask/bin/python

import os
import time
from dal import DAL
from metrics_fetcher import metricsFetcher
from flask import Flask, jsonify, request
from flask_api import status
from db_tables import db_handler

# global veriables
app = Flask(__name__)

@app.route('/api/metrics/listall', methods=['GET'])
def list_all():
    return jsonify({"metrics_list": my_dal.get_metrics_list()})


@app.route('/api/metrics/get', methods=['GET', 'POST'])
def get():
    data = request.get_json()
    print(data)
    if "metrics_name" not in data:
        return "Metrics name not provided in body", status.HTTP_400_BAD_REQUEST
    
    name = data["metrics_name"]
    try:
        result = my_dal.get_metrics_data_with_rank(name)
        return jsonify(result)
    except BaseException as err:
        print(err)
        return "Fail to get metrics data, err: {0}, call /api/metrics/listall for full list".format(err), status.HTTP_400_BAD_REQUEST

if __name__ == '__main__':
    # points the path to resources files and initial the db
    path = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__),  "resources"))
    db = db_handler(path)
    
    # create a dal object, for reading the rank and history of currencies from db
    my_dal = DAL(db)
    
    # create a fetcher thread that will periodically fetch the price of the currencies and writes to db
    ft = metricsFetcher(db)
    ft.start()

    app.run(debug=False)