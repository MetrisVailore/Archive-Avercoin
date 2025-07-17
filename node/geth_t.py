from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import time

app = Flask(__name__)
CORS(app)

# Simulated blockchain state
accounts = {
    "0xb6C548bEBe86F4D1D4EA5e3FEa2C292aD051CFe6": 1000000000000000000,  # 1 Ether in Wei
}

# Simulated blockchain data
chain_id = 3007  # Example chain ID for a local test network
blocks = []
current_block_number = 0

def create_block():
    global current_block_number
    current_block_number += 1
    block = {
        "number": hex(current_block_number),
        "hash": f"0x{current_block_number:064x}",
        "transactions": [],
        "timestamp": hex(int(time.time())),
    }
    blocks.append(block)
    return block

# Create the genesis block
create_block()

@app.route('/', methods=['POST'])  # Change to root path
def rpc():
    data = request.get_json()
    method = data.get('method')
    params = data.get('params', [])
    response = {}

    if method == 'eth_blockNumber':
        response = {
            "jsonrpc": "2.0",
            "id": data.get('id'),
            "result": hex(current_block_number)
        }
    elif method == 'eth_getBlockByNumber':
        block_number = int(params[0], 16)
        if block_number <= current_block_number:
            block = blocks[block_number - 1]
            response = {
                "jsonrpc": "2.0",
                "id": data.get('id'),
                "result": block
            }
        else:
            response = {
                "jsonrpc": "2.0",
                "id": data.get('id'),
                "error": {
                    "code": -32000,
                    "message": "Block not found"
                }
            }
    elif method == 'eth_getBalance':
        address = params[0]
        balance = accounts.get(address, 0)
        response = {
            "jsonrpc": "2.0",
            "id": data.get('id'),
            "result": hex(balance)
        }
    elif method == 'eth_sendTransaction':
        # Simulate sending a transaction
        from_address = params[0]['from']
        to_address = params[0]['to']
        value = params[0]['value']

        if from_address in accounts and accounts[from_address] >= value:
            accounts[from_address] -= value
            accounts[to_address] = accounts.get(to_address, 0) + value
            # Add transaction to the latest block
            blocks[-1]['transactions'].append({
                "from": from_address,
                "to": to_address,
                "value": hex(value)
            })
            response = {
                "jsonrpc": "2.0",
                "id": data.get('id'),
                "result": "0xTransactionHash"  # Simulated transaction hash
            }
        else:
            response = {
                "jsonrpc": "2.0",
                "id": data.get('id'),
                "error": {
                    "code": -32000,
                    "message": "Insufficient funds"
                }
            }
    elif method == 'eth_estimateGas':
        # Simulate gas estimation
        # Here we assume a fixed gas limit for simplicity
        response = {
            "jsonrpc": "2.0",
            "id": data.get('id'),
            "result": hex(21000)  # Standard gas limit for a simple transaction
        }
    elif method == 'eth_gasPrice':
        # Simulate gas price
        # Here we assume a fixed gas price for simplicity
        response = {
            "jsonrpc": "2.0",
            "id": data.get('id'),
            "result": hex(20000000000)  # 20 Gwei in Wei
        }
    elif method == 'eth_chainId':
        # Define the chain ID for your simulated blockchain
        response = {
            "jsonrpc": "2.0",
            "id": data.get('id'),
            "result": hex(chain_id)  # Return the chain ID in hex format
        }
    else:
        response = {
            "jsonrpc": "2.0",
            "id": data.get('id'),
            "error": {
                "code": -32601,
                "message": "Method not found"
            }
        }

    return jsonify(response)

if __name__ == '__main__':
    app.run(port=8545)  # Default port for Ethereum JSON-RPC
