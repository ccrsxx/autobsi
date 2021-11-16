import json
import os

def get_from_dotenv(what):
    with open(os.getenv('bsi')) as f:
        data = json.load(f)
    return data[what]

def get_from_config(what):
    with open('config.json') as f:
        data = json.load(f)
    return data[what]
