import itertools
import json
import os, os.path

import json_helper
import sys

# Add the path to the parent directory of 'blockchain'
sys.path.append(os.path.abspath('../blockchain'))
sys.path.append(os.path.abspath('../node'))
from blockchain import chain, transaction, mine
import blockchain.block as chain_helper
from blockchain.constants import *
from Cryptodome.PublicKey import RSA
import time
import ast
# import AverCoin
import asyncio
from settings import pending_transaction_file


class Database:
    Chain: dict = None

    @staticmethod
    def init():
        try:
            print("Database loading...")
            Chain = chain.Chain()
            manager = chain.UTXOManager()
            chain_data = []
            DIR = os.curdir + '/blocks'
            files_count = len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])
            if files_count > 0:
                for i in range(files_count):
                    chain_data.append(json_helper.read_json(os.getcwd() + f"/blocks/block{i}"))
                for objects in chain_data:
                    if objects["index"] != 0:
                        Chain.addBlock(chain_helper.createFromJSON(chain_helper.toJSON(objects)))
                print("Database loaded")
            else:
                blocks_count = 0
                for block in Chain.blocks:
                    f = open(f'{DIR}/block{blocks_count}.json', 'x')
                    f.write(str(Chain.blocks[block]))
                    f.close()
                    blocks_count += 1

        except Exception as err:
            print(err)

    @staticmethod
    def import_blocks():
        try:
            Chain = chain.Chain()
            manager = chain.UTXOManager()
            chain_data = []
            DIR = os.curdir + '/blocks'
            files_count = len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])
            if files_count > 0:
                for i in range(files_count):
                    chain_data.append(json_helper.read_json(os.getcwd() + f"/blocks/block{i}"))
                for objects in chain_data:
                    if objects["index"] != 0:
                        Chain.addBlock(chain_helper.createFromJSON(chain_helper.toJSON(objects)))
                return Chain
            else:
                blocks_count = 0
                for block in Chain.blocks:
                    f = open(f'{DIR}/block{blocks_count}.json', 'x')
                    f.write(str(Chain.blocks[block]))
                    f.close()
                    blocks_count += 1

        except Exception as err:
            print(err)
            return None

    @staticmethod
    def import_pending_transactions(file):
        json_data = json.dumps(list(json_helper.read_json(file)["Pending_transactions"]))
        return json.loads(json_data)

    @staticmethod
    def get_difficulty(block_hash: str):
        try:
            Chain = Database.import_blocks()
            previousDiff = int(mine.checkProofOfWork(str(Chain.blocks[block_hash].hash)))
            if len(Chain.blocks)+1 % CHANGING_DIFF_TIME != 0:
                return previousDiff
            elif len(Chain.blocks)+1 % CHANGING_DIFF_TIME == 0:
                currentDiff = (chain.get_update_diff(previousDiff, Chain.blocks))
                return currentDiff
        except Exception as err:
            print(err)


    @staticmethod
    def add_block(block: chain_helper.Block):
        remove_pending = False
        try:
            pending_transactions = Database.import_pending_transactions(pending_transaction_file)
            for objects in pending_transactions:
                d = objects["hash"]
                for block_transactions in block.transactions:
                    b_hash = json.loads(chain_helper.toJSON(block_transactions))["hash"]
                    if str(d) == str(b_hash):
                        remove_pending = True
                        # print(remove_pending)
                    # else:
                    # print("transactions != pending_transactions")
                    # print("d", d)
                    # print("b_hash", b_hash)
            if remove_pending:
                Database.clear_pending_transactions(pending_transaction_file)

            Chain = Database.import_blocks()
            Chain.addBlock(block)
            DIR = os.curdir + '/blocks'
            f = open(f'{DIR}/block{block.index}.json', 'x')
            f.write(str(Chain.blocks[block.hash]))
            f.close()
            return True
        except Exception as err:
            print(err)
            return False

    @staticmethod
    def add_pending_transactions(file, pending_transaction: str):
        pending_transactions = json.load(open(f'{file}.json'))
        pending_transaction = json.loads(pending_transaction)
        if not pending_transaction["inputs"]:
            return False, "Coinbase transaction don't needed in pending"
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
        json_data = json.dumps(list(json_helper.read_json(file)["Pending_transactions"]))
        if len(json.loads(json_data)) + 1 > MAX_TRANSACTIONS_PER_BLOCK:
            return False, "Transactions are full"
        for objects in json.loads(json_data):
            pending_data["Pending_transactions"].append({
                "inputs": json.loads(json.dumps(objects))["inputs"],
                "outputs": json.loads(json.dumps(objects))["outputs"],
                "timestamp": json.loads(json.dumps(objects))["timestamp"],
                "hash": json.loads(json.dumps(objects))["hash"]
            })
            if json.loads(json.dumps(objects))["hash"] == pending_transaction["hash"]:
                return False, "Transaction already in the block"

        verify_data = transaction.createFromDictionary(pending_transaction)
        pending_transactions.update(pending_data)
        print(chain.verifyTransactionSyntax([verify_data]))
        if chain.verifyTransactionSyntax([verify_data]):
            json.dump(pending_transactions, open(f'{file}.json', 'w'), indent=2)
        else:
            return False, "Transaction is bad"
        return True, "Transaction added"

    @staticmethod
    def clear_pending_transactions(file):
        with open(f"{file}.json", encoding="utf8") as f:
            dict_ = json.load(f)

        pop_count = 0
        for objects in dict_["Pending_transactions"]:
            pop_count += 1
        for i in range(pop_count):
            dict_["Pending_transactions"].pop()

        with open(f"{file}.json", "w", encoding="utf8") as f:
            json.dump(dict_, f, ensure_ascii=False)

    # this is not useful btw
    '''
    @staticmethod
    def import_pending_transactions():
        try:
            try:
                json_data = json_helper.read_json("pending_transactions")
                print(json_data)
                return json_data
            except:
                json_helper.save_new_json("", "pending_transactions")

        except Exception as err:
            print(err)
            return None
    '''

    @staticmethod
    async def get_transaction(transaction_hash: str):
        try:
            Chain = Database.import_blocks()
            return Chain.getTransaction(transaction_hash)

        except Exception as err:
            print(err)
            return None

    @staticmethod
    async def get_block(block_hash: str):
        try:
            Chain = Database.import_blocks()
            return Chain.blocks[block_hash]

        except Exception as err:
            print(err)
            return None

    @staticmethod
    async def get_blocks(offset, limit):
        try:
            Chain = Database.import_blocks()
            # print(Chain.getAncestors(child=Chain.head, n=limit))
            return Chain.blocks

        except Exception as err:
            print(err)
            return None

    @staticmethod
    async def get_pending_transactions():
        try:
            transactions = Database.import_pending_transactions(pending_transaction_file)
            return transactions

        except Exception as err:
            print(err)
            return None

# testing full blockchain
'''
def maint():
    Chain = Database.import_blocks()
    DIR = os.curdir + '/blocks'
    private1 = RSA.generate(2048)
    public1 = private1.publickey().exportKey('DER').hex()
    for i in range(1000):
        tx1 = transaction.createTransaction([public1], [250], time.time())
        tx2 = transaction.createTransaction(
            outputAddresses=[public1],
            outputAmounts=[250],
            timestamp=time.time(),
            previousTransactionHashes=[tx1.hash],
            previousOutputIndices=[0],
            privateKeys=[private1]
        )
        # Database.add_pending_transactions(pending_transaction_file, str(tx1))

        # 1 has 1000 SPC
        b1 = mine.generateNextBlock(Chain.head, [tx1, tx2], 5)
        Database.add_block(b1)
        Chain.addBlock(b1)
        print(Database.get_difficulty(b1.hash))
        print(f"blocks mined {i}")
    old_blocks_count = len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])
    blocks_count = len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])
    for block in Chain.blocks:
        if Chain.blocks[block].index > (old_blocks_count-1):
            f = open(f'{DIR}/block{blocks_count}.json', 'x')
            f.write(str(Chain.blocks[block]))
            f.close()
            blocks_count += 1
    # else:
    # print("block:", Chain.blocks[block].index)
    # print("old_block", old_blocks_count)


maint()

'''
