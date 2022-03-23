import json

from .autobsi import os


def get_from_config(key: str):
    with open(os.path.join('src', 'config.json')) as raw:
        data = json.load(raw)
    return data[key]


def get_from_dotenv(key: str):
    with open(os.getenv('bsi')) as raw:  # type: ignore
        data = json.load(raw)
    return data[key]


def get_from_heroku(key: str):
    data = json.loads(os.getenv('config'))  # type: ignore
    return data[key]
