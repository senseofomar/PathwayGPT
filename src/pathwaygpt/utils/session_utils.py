import json
from pathlib import Path


def save_session(data:dict, path:str)->None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent = 2)


def load_session(path:str)->dict:

    if not Path(path).exists():
        return{}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def reset_session(path:str)->None:
    Path(path).unlink(missing_ok=True)