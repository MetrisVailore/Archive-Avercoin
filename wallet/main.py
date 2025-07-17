import requests
import json
import time
import os
from json_helper import *
from Cryptodome.PublicKey import RSA
import asyncio
import sys
from all_comands import *
from settings import *
import ctypes

if os.name == 'nt':
    kernel32 = ctypes.windll.kernel32
    
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


def commands(file):
    while True:
        msg = input(f': ')
        if msg == "help":
            asyncio.run(cmd_help())
        elif msg == "keys":
            wallet_keys = read_json(f"wallets/{file}")
            private_key = wallet_keys["private_key"]
            public_key = wallet_keys["public_key"]
            print(f"Кошелек {file}")
            print(f"private_key: {private_key}\n"
                  f"public_key: {public_key}")
        elif msg == "create_new":
            create_new_wallet()
            break
        elif msg == "change_wallet":
            change_wallet()
            break
        elif msg.startswith("get_diff"):
            last_hash = str(asyncio.run(get_last_hash(STANDART_IP, STANDART_PORT)))
            print("diff:", asyncio.run(get_diff(STANDART_IP, STANDART_PORT, last_hash)))
        elif msg.startswith("get_block"):
            full_message = msg.split()
            try:
                print("\n" + str(asyncio.run(get_block(STANDART_IP, STANDART_PORT, full_message[1]))) + "\n")
            except:
                print("Не удалось найти блок")
        elif msg == "get_blocks":
            print("\n" + asyncio.run(get_blocks(STANDART_IP, STANDART_PORT)) + "\n")
        elif msg == "get_json_blocks":
            print(f"\n{asyncio.run(get_json_blocks(STANDART_IP, STANDART_PORT))}\n")
        elif msg.startswith("get_transaction"):
            full_message = msg.split()
            try:
                print("\n" + str(asyncio.run(get_transaction(STANDART_IP, STANDART_PORT, full_message[1]))) + "\n")
            except Exception as err:
                print(err)
                print("Не удалось найти транзакцию")
        elif msg.startswith("add_transaction"):
            wallet_keys = read_json(f"wallets/{file}")
            private_key = wallet_keys["private_key"]
            private1 = RSA.importKey(bytes.fromhex(private_key))
            try:
                full_message = msg.split()
                amount = full_message[1]
                address = full_message[2]
            except:
                print("Неправильные данные транзакции")
                continue
            try:
                result = asyncio.run(add_transaction(STANDART_IP, STANDART_PORT, private1, amount, address))
                if result is False:
                    print("\nНе удалось сделать транзакцию\n")
                elif result is True:
                    print("\nТранзакция добавилась в pending транзакции")
            except Exception as err:
                print(err)
                print("Не удалось сделать транзакцию")
        elif msg == "get_pending_transactions":
            print(asyncio.run(get_pending_transactions(STANDART_IP, STANDART_PORT)))
        elif msg == "get_last_index":
            print(asyncio.run(get_last_index(STANDART_IP, STANDART_PORT)))
        elif msg == "get_last_hash":
            print(asyncio.run(get_last_hash(STANDART_IP, STANDART_PORT)))
        elif msg == "/exit":
            sys.exit()


def create_new_wallet():
    new_private_wallet = RSA.generate(1024)
    new_public_wallet = new_private_wallet.publickey().exportKey('DER').hex()
    private_key = new_private_wallet.exportKey('DER').hex()
    json_wallet = {
        f"private_key": private_key,
        f"public_key": new_public_wallet
    }
    new_wallet_name = input("Введите имя кошелька\n")
    save_new_json(json_wallet, f"wallets/{new_wallet_name}")
    print("Введите /help для всех доступных команд")
    commands(new_wallet_name)


def change_wallet():
    change_DIR = os.curdir + '/wallets'
    wallets = []
    for name in os.listdir(change_DIR):
        wallets.append(name.replace(".json", ""))
    print("Кошельки", ', '.join(wallets))
    change_wallet_answer = input("Кошельки найдены, введите нужный:\n")
    change_without_name_json = change_wallet_answer.replace(".json", "")
    commands(change_without_name_json)


if __name__ == '__main__':
    DIR = os.curdir + '/wallets'
    files_count = len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])
    if files_count > 1:
        main_wallets = []
        for name in os.listdir(DIR):
            main_wallets.append(name.replace(".json", ""))
        print("Кошельки", ', '.join(main_wallets))
        wallet_answer = input("Кошельки найдены, введите нужный:\n")
        without_name_json = wallet_answer.replace(".json", "")
        wallet_json = read_json(f"wallets/{without_name_json}")
        commands(without_name_json)
    elif files_count == 1:
        for name in os.listdir(DIR):
            without_name = name.replace(".json", "")
            print(f"Найден кошелек {without_name}")
            wallet_json = read_json(without_name)
            commands(str(without_name))
    elif files_count == 0:
        wallet_name = input("У вас нет кошелька, введите имя кошелька\n")
        new_private = RSA.generate(1024)
        new_public = new_private.publickey().exportKey('DER').hex()
        new_private_key = new_private.exportKey('DER').hex()
        new_json = {
            f"private_key": new_private_key,
            f"public_key": new_public
        }
        save_new_json(new_json, f"wallets/{wallet_name}")
        print("Введите /help для всех доступных команд")
        commands(wallet_name)
