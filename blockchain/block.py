import time
import json
from typing import List, cast
from AverCoin.blockchain.transaction import Transaction, createTransaction, createFromDictionary

from Cryptodome.Hash import SHA256


class BlockException(Exception):
    pass


class Block:
    def __init__(self, index: int, timestamp: float, transactions: List[Transaction], noonce: int, previousHash: str) -> None:
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.noonce = noonce
        self.previousHash = previousHash
        self.hash = hashBlock(
            index=index,
            timestamp=timestamp,
            transactions=transactions,
            noonce=noonce,
            previousHash=previousHash)

    def asJSON(self) -> str:
        d = {
            "hash": self.hash,
            "index": self.index,
            "timestamp": self.timestamp,
            "noonce": self.noonce,
            "previousHash": self.previousHash,
            "transactions": [],
        }

        for transaction in self.transactions:
            dTransactions = cast(List[Transaction], d["transactions"])
            dTransactions.append(transaction.asDict())

        return json.dumps(d, indent=4)

    def __repr__(self) -> str:
        return self.asJSON()

    def __eq__(self, other: object):
        if isinstance(self, other.__class__):
            lhs = hashBlock(
                self.index,
                self.timestamp,
                self.transactions,
                self.noonce,
                self.previousHash
            )

            other = cast(Block, other)
            rhs = hashBlock(
                other.index,
                other.timestamp,
                other.transactions,
                other.noonce,
                other.previousHash
            )
            return lhs == rhs
        return NotImplemented


def hashBlock(
        index: int,
        timestamp: float,
        transactions: List[Transaction],
        noonce: int,
        previousHash: str) -> str:
    """
    Generates a SHA256 hash for the given data inside a block.
    """
    # Serialize the block's data by encoding it using utf8.
    combinedTransaction = \
        "".join([transaction.hash for transaction in transactions])

    serialized = \
        "{}{}{}{}".format(
            index,
            timestamp,
            combinedTransaction,
            noonce,
            previousHash) \
        .encode('utf-8')
    return SHA256.new(serialized).hexdigest()


def genesisBlock() -> Block:
    """
    Returns the hard-coded genesis block, which is the first Block in
    everybody's chain.
    """
    genesisTime = 1725615747.2513995
    genesisAddress = "30820122300d06092a864886f70d01010105000382010f003082010a0282010100b0bb73e00ebdc83794c8b926253e6f72a45b8ef487ffe565941fcd74384884a95939fc0e1213db0dfbab83dcd3902af5b6c7391a453324b956aa5be8d58cf2d5b9e9667429ee40abe8a0d0ad831939454b61db63281f2d42665dccc0088f67291926dfdb321efd7b77ad5e571b16acc931aa31046423ba16ae5c1d3d613dcf2331041d90d0f39e0fd85f30238925d00198a765e0f6c721aa7372bc5cb648156dbaf98bfe16aab9eba12545e05253fb9aab932da75067dc432ac9228b42252c1fb4d5851a5108afa063c4b4f1d1795074e66a2c92261a3d976314134bbd3ba7ae0eb1938a936381239d6f6127b846fc42c99a9fcf36984a83a924ed0522ea24830203010001"
    genesisTimestamp = genesisTime
    genesisTransaction = createTransaction(
        outputAddresses=[genesisAddress],
        outputAmounts=[100],
        timestamp=genesisTimestamp
    )

    return Block(
        index=0,
        timestamp=genesisTime,
        transactions=[genesisTransaction],
        noonce=0,
        previousHash="AverCoin is a future, and i want to be in it."
    )


def toJSON(self):
    """
    Serialize the object custom object
    """
    return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


def createFromJSON(jsonBlock: str) -> Block:
    deserialized = json.loads(jsonBlock)

    transactions: List[Transaction] = []
    for transactionDict in deserialized["transactions"]:
        transactions.append(createFromDictionary(transactionDict))

    obj = Block(
        index=deserialized["index"],
        transactions=transactions,
        timestamp=deserialized["timestamp"],
        noonce=deserialized["noonce"],
        previousHash=deserialized["previousHash"])

    if deserialized["hash"] != obj.hash:
        raise BlockException("Serialized block hash is invalid.")

    return obj

'''
def createTransactionsFromJson(transactions: str) -> List:
    deserialized = json.dumps(list(json.loads(transactions)["Pending_transactions"]))
    print(deserialized)
    d = {
        "hash": tx_hash,
        "index": index,
        "timestamp": timestamp,
        "noonce": noonce,
        "previousHash": previousHash,
        "transactions": [],
    }
    for transaction in deserialized:
        dTransactions = cast(List[Transaction], d["transactions"])
        dTransactions.append(transaction.asDict())

    return json.dumps(d, indent=4)
'''
