import requests, json
import sys, os

# Add the path to the parent directory of 'blockchain'
sys.path.append(os.path.abspath('../blockchain'))
sys.path.append(os.path.abspath('../node'))

import transaction
import time

wallet_commands = ["keys",
                   "import_keys",
                   "create_new",
                   "change_wallet",
                   "/exit"]

wallet_use_cmd = [
    "Показывает ключи кошелька (не показывайте ни кому другому, они используются для доступа к кошельку.)",
    "Импорт кошелька по приватному ключу",
    "Создать новый кошелек с ключами",
    "Поменять кошелек",
    "выйти из кошелька"]

node_commands = ["sync",
                 "get_difficulty",
                 "download_blocks",
                 "get_block blockHash",
                 "get_last_index",
                 "get_last_hash",
                 "get_last_block"
                 "get_blocks",
                 "add_block",
                 "get_json_blocks",
                 "get_transaction transactionHash",
                 "add_transaction amount address",
                 "get_pending_transactions",

                 ]
node_use_cmd = ["Проверка синхронизации (путем сравнивая количество блоков у клиента и ноды",
                "возвращает текущую сложность",
                "скачивает блокчейн",
                "возвращает блок по хешу",
                "возвращается число последнего блока",
                "возвращается хеш последнего блока",
                "возвращает последний блок",
                "возвращает все блоки",
                "добавляет блок в формате блока",
                "возвращает блоки в json формате",
                "возвращает транзакцию по хешу транзакции",
                "добавляется транзакция при передачи в формате транзакции",
                "возвращаются pending транзакции",
                ]


async def cmd_help():
    print("\nКоманды кошелька\n")
    for a, w_cmd in enumerate(wallet_commands):
        print(f"{w_cmd} - {wallet_use_cmd[a]}")
    print("\nКоманды нод\n")
    for i, cmd in enumerate(node_commands):
        print(f"{cmd} - {node_use_cmd[i]}")


async def get_pending_transactions(ip, port):
    try:
        r = requests.get(f"http://{ip}:{port}/get_pending_transactions")
        data = r.text
        j = json.loads(data)
        pending_data = []
        for objects in j["result"]:
            pending_data.append({
                "inputs": json.loads(json.dumps(objects))["inputs"],
                "outputs": json.loads(json.dumps(objects))["outputs"],
                "timestamp": json.loads(json.dumps(objects))["timestamp"],
                "hash": json.loads(json.dumps(objects))["hash"]
            })
        return json.dumps(pending_data, indent=2)
    except:
        return []


async def get_blocks(ip, port):
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


async def get_block(ip, port, block_hash):
    try:
        r2 = requests.get(f"http://{ip}:{port}/get_block?block_hash={block_hash}")
        data2 = r2.text
        j2 = json.loads(data2)
        return json.dumps(j2["result"], indent=2)
    except Exception as err:
        print(err)


async def get_transaction(ip, port, tx_hash):
    try:
        r2 = requests.get(f"http://{ip}:{port}/get_transaction?tx_hash={tx_hash}")
        data2 = r2.text
        j2 = json.loads(data2)
        return j2["result"]
    except Exception as err:
        print(err)


async def add_transaction(ip, port, private1, amount, address):
    try:
        pending_data = await get_pending_transactions(ip, port)
        tx2 = transaction.createTransaction(
            outputAddresses=[address],
            outputAmounts=[int(amount)],
            timestamp=time.time(),
            previousTransactionHashes=["2780823b189d25158c83cd83dc4a8931a8c7b4b1a64a68f64f8710a88ea92207"],
            previousOutputIndices=[0],
            privateKeys=[private1]
        )
        print(tx2)
        r2 = requests.get(f"http://{ip}:{port}/add_transaction?pending_transaction={tx2}")
        data2 = r2.text
        j2 = json.loads(data2)
        return bool(j2["ok"])

    except Exception as err:
        print(err)


async def get_json_blocks(ip, port):
    try:
        r = requests.get(f"http://{ip}:{port}/get_json_blocks")
        data = r.text
        j = json.loads(data)
        return j
    except Exception as err:
        print(err)


async def get_last_hash(ip, port):
    try:
        r2 = requests.get(f"http://{ip}:{port}/get_last_hash")
        data2 = r2.text
        j2 = json.loads(data2)
        return str(j2)

    except Exception as err:
        print(err)


async def get_last_index(ip, port):
    try:
        r2 = requests.get(f"http://{ip}:{port}/get_last_index")
        data2 = r2.text
        j2 = json.loads(data2)
        return int(j2)
    except Exception as err:
        print(err)


async def get_diff(ip, port, block_hash: str):
    try:
        r2 = requests.get(f"http://{ip}:{port}/get_difficulty?block_hash={block_hash}")
        data2 = r2.text
        j = json.loads(data2)
        return j['result']
    except Exception as err:
        print(err)


async def add_block(ip, port, new_block):
    try:
        r2 = requests.get(f"http://{ip}:{port}/add_block?new_block={new_block}")
        data2 = r2.text
        j = json.loads(data2)
        return j['ok'], j
    except Exception as err:
        print(err)
