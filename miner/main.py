import requests
import json
import time
from AverCoin.blockchain import transaction, mine, chain, block
from AverCoin.blockchain.chain import get_update_diff
from AverCoin.blockchain.constants import *
from Cryptodome.PublicKey import RSA
import AverCoin.blockchain.block as chain_helper
import datetime

host_ip = "127.0.0.1"
host_port = "3006"

# private1 = RSA.generate(2048)
# address = private1.publickey().exportKey('DER').hex()
private_key = input("Введите свой ключ\n")
private1 = RSA.importKey(bytes.fromhex(private_key))
address = input("Введите свой адресс\n")

print(f"Подключена нода {host_ip}:{host_port} ")


# address = input("Введите свой адрес")
# private1 = input("Введите свой приватный ключ (создаст транзакцию если нет транзакций)")


def day_time():
    return f"[{datetime.datetime.now().hour}:{datetime.datetime.now().minute}]"


def get_pending_transactions(ip, port):
    try:
        r = requests.get(f"http://{ip}:{port}/get_pending_transactions")
        data = r.text
        j = json.loads(data)
        pending_data = {}
        for objects in j["result"]:
            test_transaction = {
                "inputs": json.loads(json.dumps(objects))["inputs"],
                "outputs": json.loads(json.dumps(objects))["outputs"],
                "timestamp": json.loads(json.dumps(objects))["timestamp"],
                "hash": json.loads(json.dumps(objects))["hash"]
            }
            test_transaction = chain_helper.createFromDictionary(test_transaction)
            return test_transaction
    except Exception as err:
        print(err)
        time.sleep(1)
        return []


def get_blocks(ip, port):
    try:
        full_blocks = []
        r2 = requests.get(f"http://{ip}:{port}/get_blocks?limit=1&offset=1")
        data2 = r2.text
        j2 = json.loads(data2)

        for element in j2["result"]:
            full_blocks.append(j2["result"][f"{element}"])
        return json.dumps(full_blocks, indent=2)
    except Exception as err:
        print(err)


def get_json_blocks(ip, port):
    try:
        r = requests.get(f"http://{ip}:{port}/get_json_blocks")
        data = r.text
        j = json.loads(data)
        return j
    except Exception as err:
        print(err)
        time.sleep(1)


def get_last_hash(ip, port):
    try:
        r2 = requests.get(f"http://{ip}:{port}/get_last_hash")
        data2 = r2.text
        j2 = json.loads(data2)
        return str(j2)

    except Exception as err:
        print(err)


def get_last_index(ip, port) -> int:
    try:
        r2 = requests.get(f"http://{ip}:{port}/get_last_index")
        data2 = r2.text
        j2 = json.loads(data2)
        try:
            return int(j2)
        except:
            time.sleep(10)
    except Exception as err:
        print(err)


def get_diff(ip, port, block_hash: str):
    try:
        last_index = get_last_index(ip, port)
        json_blocks = get_json_blocks(ip, port)
        previousDiff = int(mine.checkProofOfWork(block_hash))
        if last_index + 1 % CHANGING_DIFF_TIME != 0:
            return previousDiff
        elif last_index + 1 % CHANGING_DIFF_TIME == 0:
            currentDiff = (chain.get_update_diff(previousDiff, json_blocks))
            return currentDiff
    except Exception as err:
        print(err)


def add_block(ip, port, new_block):
    try:
        r2 = requests.get(f"http://{ip}:{port}/add_block?new_block={new_block}")
        data2 = r2.text
        j = json.loads(data2)
        return j['ok'], j
    except Exception as err:
        print(err)


def correctSingleQuoteJSON(s):
    rstr = ""
    escaped = False

    for c in s:

        if c == "'" and not escaped:
            c = '"'  # replace single with double quote

        elif c == "'" and escaped:
            rstr = rstr[:-1]  # remove escape character before single quotes

        elif c == '"':
            c = '\\' + c  # escape existing double quotes

        escaped = (c == "\\")  # check for an escape character
        rstr += c  # append the correct json

    return rstr


if __name__ == '__main__':
    pending_transaction_verify = True
    while True:
        # create coinbase transaction
        tx1 = transaction.createTransaction([address], [250], time.time())
        tx2 = transaction.createTransaction(
            outputAddresses=[address],
            outputAmounts=[250],
            timestamp=time.time(),
            previousTransactionHashes=[tx1.hash],
            previousOutputIndices=[0],
            privateKeys=[private1]
        )

        all_transactions = []

        last_hash = get_last_hash(host_ip, host_port)
        diff = get_diff(host_ip, host_port, last_hash)
        pending_transactions = get_pending_transactions(host_ip, host_port)
        index = get_last_index(host_ip, host_port)
        previous_hash = last_hash

        # pending_transactions = correctSingleQuoteJSON(pending_transactions)

        all_transactions.append(tx1)
        if len(str(pending_transactions)) == 0 or pending_transaction_verify is False:
            all_transactions.append(tx2)
        if pending_transaction_verify:
            all_transactions.append(pending_transactions)
            '''
            correctJson = correctSingleQuoteJSON(pending_transactions)
            correctJson = correctJson.replace("[", "")
            correctJson = correctJson.replace("]", "")
            all_transactions = f"{str(all_transactions)},[{correctJson}]"
            '''

        # for objects in pending_transactions:
        #    all_transactions.append(objects)

        print(f"{day_time()} \033[35mНовая задача, \033[0m Сложность {diff}, Блок {index + 1}")

        previous_time = time.time()
        nextBlock = mine.SimpleGenerateNextBlock(index + 1, previous_hash, all_transactions, diff)
        now_time = time.time()
        if now_time - previous_time != 0:
            print(f"{day_time()} Хешрейт: {nextBlock.noonce / (now_time - previous_time)} H/s")
        else:
            print(f"Хешрейт не рассчитан")
        add_result = add_block(host_ip, host_port, nextBlock)

        if add_result[0]:
            print(
                f"{day_time()} \033[32mДобыт блок\033[0m {index} при сложности {diff} за {now_time - previous_time} секунд")
        elif not add_result[0]:
            print(f"{day_time()} \033[31m Не удалось добыть блок :(")
            print(f"\033[31m Потрачено {time.time() - previous_time} секунд")
            print(f"\033[31m Нода вернула {add_result[1]}\033[0m")
            print("Пытаемся удалить ненужные транзакции")
            pending_transaction_verify = False

    # print(f"diff {diff}")
    # print(f"pending transactions {pending_transactions}")
    # print(f"index {index}")
