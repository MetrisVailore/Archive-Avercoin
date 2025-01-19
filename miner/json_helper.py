import json
import os
import time
from AverCoin.blockchain.transaction import *
from AverCoin.blockchain.block import createFromJSON


def save_new_json(data, file):
    try:
        with open(f"{file}.json", mode="x", encoding="utf-8") as write_file:
            json.dump(data, write_file)
    except:
        print("File exists.")


# this is not working as I saw
'''
def update_json(data, file):
    try:
        with open(f"{file}.json", mode="w", encoding="utf-8") as write_file:
            json.dump(data, write_file)
    except:
        print("File exists.")
'''

# just change add_json to add_to_json


def add_json(data, file):
    with open(f"{file}.json", mode="a", encoding="utf-8") as write_file:
        try:
            write_file.write("\n")
            json.dump(data, write_file)
        except:
            write_file.close()


def read_json(file):
    with open(f"{file}.json", mode="r", encoding="utf-8") as read_file:
        json_data = json.load(read_file)
        return json_data


# I did this for a very long time, but it turned out to be very simple
'''
def get_pending_transactions(data, file):
    json_data = json.dumps(list(read_json(file)["Pending_transactions"]))
    count = 0
    for objects in json.loads(json_data):
        print(f"Transaction {count}")
        print(json.loads(json.dumps(objects))["inputs"])
        print(json.loads(json.dumps(objects))["outputs"])
        print(json.loads(json.dumps(objects))["timestamp"])
        print(json.loads(json.dumps(objects))["hash"])
        print("\n")
        count += 1
    return json.loads(json_data)
    # print(json.loads(objects)["inputs"])
    # print(createFromDictionary(dict(json_data)))


nodes_data = {
  "Nodes": [
    {
      "name": "AverCoin Node",
      "active": True,
      "url": "127.0.0.1",
      "version": "1",
    },
    {
      "name": "AverCoin Node2",
      "active": False,
      "url": "127.0.0.1",
      "version": 1,
    },
  ],
  "lastMessages": [
    {
      "url": "127.0.0.1",
      "message": "test",
      "timestamp": time.time(),
    },
  ],
}

add_json(nodes_data, "nodes")

private1 = RSA.generate(2048)
public1 = private1.publickey().exportKey('DER').hex()
pending_data = createTransaction([public1], [1000], time.time()).asDict()

add_json(pending_data, "pending_transactions")

'''