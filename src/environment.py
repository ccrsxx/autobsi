import os
import json

from typing import Any


def get_from_config(key: str) -> Any:
    env_path = os.path.join('src', 'config.json')

    with open(env_path) as raw:
        data = json.load(raw)

    return data[key]


def get_from_env(key: str) -> Any:
    env_data = os.getenv('BSI_CONFIG')

    if not env_data:
        raise ValueError('BSI_CONFIG is not set')

    with open(env_data) as raw:
        data = json.load(raw)

    return data[key]


def get_from_heroku(key: str) -> Any:
    env_data = os.getenv('BSI_CONFIG')

    if not env_data:
        raise ValueError('BSI_CONFIG is not set')

    data = json.loads(env_data)

    return data[key]
