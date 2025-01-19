import json


def save_new_json(data, file):
    try:
        with open(f"{file}.json", mode="x", encoding="utf-8") as write_file:
            json.dump(data, write_file, indent=2)
    except:
        print("File exists.")


def read_json(file):
    with open(f"{file}.json", mode="r", encoding="utf-8") as read_file:
        json_data = json.load(read_file)
        return json_data
