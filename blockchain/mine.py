import time
from typing import List

import sys, os

# Add the path to the parent directory of 'blockchain'
sys.path.append(os.path.abspath('../blockchain'))
sys.path.append(os.path.abspath('../node'))
from block import Block, hashBlock
from transaction import Transaction
from constants import MIN_MINING_DIFFICULTY, CHANGING_DIFF_TIME


def checkProofOfWork(hash: str) -> int:
    difficulty = int(MIN_MINING_DIFFICULTY)
    while True:
        if int(hash[:difficulty], 16) == 0:
            difficulty += 1
            continue
        elif int(hash[:difficulty], 16) != 0:
            if int(difficulty) - 1 != 0:
                return int(difficulty) - 1
            else:
                return int(MIN_MINING_DIFFICULTY)


def hasProofOfWork(hash: str, diff: int) -> bool:
    """
    Checks if the first n half-bytes in the hash are zero, where n
    is the difficulty.
    """
    difficulty = diff  # Number of most significant bytes that are zero.
    return int(hash[:difficulty], 16) == 0


def SimpleGenerateNextBlock(nextIndex, previous_hash, transactions: List[Transaction], currentDiff: int) -> Block:
    nextTimestamp = time.time()
    noonce = 0
    if nextIndex % CHANGING_DIFF_TIME != 0:
        while True:
            hash = hashBlock(
                nextIndex,
                nextTimestamp,
                transactions,
                noonce,
                previous_hash)
            if hasProofOfWork(hash, currentDiff):
                return Block(
                    index=nextIndex,
                    timestamp=nextTimestamp,
                    transactions=transactions,
                    noonce=noonce,
                    previousHash=previous_hash)
            noonce += 1
        return None
    elif nextIndex % CHANGING_DIFF_TIME == 0:
        while True:
            hash = hashBlock(
                nextIndex,
                nextTimestamp,
                transactions,
                noonce,
                previous_hash)
            if hasProofOfWork(hash, currentDiff):
                return Block(
                    index=nextIndex,
                    timestamp=nextTimestamp,
                    transactions=transactions,
                    noonce=noonce,
                    previousHash=previous_hash)
            noonce += 1
        return None


def generateNextBlock(
        previousBlock: Block,
        transactions: List[Transaction],
        currentDiff: int) -> Block:
    """
    Attempts to generate the next block in given new data
    """
    previousDiff = checkProofOfWork(previousBlock.hash)
    nextIndex = previousBlock.index + 1
    nextTimestamp = time.time()
    noonce = 0

    if nextIndex % CHANGING_DIFF_TIME != 0:
        while True:
            hash = hashBlock(
                nextIndex,
                nextTimestamp,
                transactions,
                noonce,
                previousBlock.hash)
            if hasProofOfWork(hash, previousDiff):
                return Block(
                    index=nextIndex,
                    timestamp=nextTimestamp,
                    transactions=transactions,
                    noonce=noonce,
                    previousHash=previousBlock.hash)
            noonce += 1
        return None

    elif nextIndex % CHANGING_DIFF_TIME == 0:
        while True:
            hash = hashBlock(
                nextIndex,
                nextTimestamp,
                transactions,
                noonce,
                previousBlock.hash)
            if hasProofOfWork(hash, currentDiff):
                return Block(
                    index=nextIndex,
                    timestamp=nextTimestamp,
                    transactions=transactions,
                    noonce=noonce,
                    previousHash=previousBlock.hash)
            noonce += 1

        return None
