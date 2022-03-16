import os
import json


def get_from_config(key: str):
    with open('config.json') as raw:
        data = json.load(raw)
    return data[key]


def get_from_dotenv(key: str):
    with open(os.getenv('bsi')) as raw:  # type: ignore
        data = json.load(raw)
    return data[key]
