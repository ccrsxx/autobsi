import json
import os


def get_from_config(key):
    with open('config.json') as raw:
        data = json.load(raw)
    return data[key]


def get_from_dotenv(key):
    with open(os.getenv('bsi')) as raw:
        data = json.load(raw)
    return data[key]
