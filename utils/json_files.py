import json

def load_json(file:str) -> list:
    with open(file, 'r') as json_file:
        key = json.load(json_file)
        return key