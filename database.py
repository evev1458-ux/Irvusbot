import json
import os
import logging

logger = logging.getLogger(__name__)
DB_FILE = "data.json"

class Database:
    def __init__(self):
        if not os.path.exists(DB_FILE):
            self._save({})

    def _load(self):
        try:
            if not os.path.exists(DB_FILE): return {}
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except: return {}

    def _save(self, data):
        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def get_group_config(self, chat_id: int) -> dict:
        data = self._load()
        k = str(chat_id)
        if k not in data:
            data[k] = {"emoji": "🟢", "min_buy": 0, "tokens": []}
            self._save(data)
        return data[k]

    def set_group_config(self, chat_id: int, key: str, value):
        data = self._load()
        if str(chat_id) in data:
            data[str(chat_id)][key] = value
            self._save(data)

    def get_tokens(self, chat_id: int) -> list:
        return self.get_group_config(chat_id).get("tokens", [])

    def add_token(self, chat_id, ca, chain):
        data = self._load()
        k = str(chat_id)
        if k not in data: self.get_group_config(chat_id); data = self._load()
        tokens = data[k].get("tokens", [])
        if any(t['ca'] == ca for t in tokens): return False
        tokens.append({"ca": ca, "chain": chain})
        data[k]["tokens"] = tokens
        self._save(data)
        return True

    def remove_token(self, chat_id, ca):
        data = self._load()
        k = str(chat_id)
        if k in data:
            data[k]["tokens"] = [t for t in data[k]["tokens"] if t["ca"] != ca]
            self._save(data)
            return True
        return False

    def get_all_groups_with_tokens(self):
        data = self._load()
        return [{"chat_id": int(k), "config": v} for k, v in data.items() if v.get("tokens")]

db = Database()
