"""
for objects in pending_transactions:
    pending_inputs = json.loads(block.toJSON(objects))['inputs']
    pending_outputs = json.loads(block.toJSON(objects))['outputs']
    for tx_data in pending_outputs:
        pending_amount = tx_data['amount']
    print(objects)
"""


'''
pending_transactions = json.load(open(f'transactions.json'))
pending_transaction = json.loads(str(tx1))
pending_data = {
    "Pending_transactions": [
        {
            "inputs": pending_transaction["inputs"],
            "outputs": pending_transaction["outputs"],
            "timestamp": pending_transaction["timestamp"],
            "hash": pending_transaction["hash"]
        },
    ],
}
json_data = json.dumps(list(json.load(open('transactions.json'))["Pending_transactions"]))
for objects in json.loads(json_data):
    pending_data["Pending_transactions"].append({
        "inputs": json.loads(json.dumps(objects))["inputs"],
        "outputs": json.loads(json.dumps(objects))["outputs"],
        "timestamp": json.loads(json.dumps(objects))["timestamp"],
        "hash": json.loads(json.dumps(objects))["hash"]
    })

verify_data = transaction.createFromDictionary(pending_transaction)
pending_transactions.update(pending_data)
json.dump(str(tx1), open(f'transactions.json', 'a'), indent=2)
'''


'''
for element in j["result"]:
    if element["inputs"]:
        for input_objects in element["inputs"]:
            pending_data.append({"referencedHash": input_objects["referencedHash"]})
            pending_data.append({"referencedOutputIndex": input_objects["referencedOutputIndex"]})
            pending_data.append({"signature": input_objects["signature"]})
    for objects in element["outputs"]:
        pending_data.append({"address": objects["address"]})
        pending_data.append({"amount": objects["amount"]})
        pending_data.append({"timestamp": element["timestamp"]})
        
'''

