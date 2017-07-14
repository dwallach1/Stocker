import os
import json

def run():
    f = "start.json"
    ticker = "ua"
    addition = ["link3", "link4"]
    with open(f) as f_:
        data = json.load(f_)
    if ticker in data.keys():
        starter = data[ticker]
        updated = starter + addition
        data.update({ticker : updated })
    else:
        data.update(addition)
    with open(f, 'w') as f_:
        json.dump(data, f_)

run()
