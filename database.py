import json
import os

DB_FILE = "data.json"

class Database:
    def __init__(self):
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, "w") as f: json.dump({}, f)

    def _load(self):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}

    def _save(self, data):
        with open(DB_FILE, "w") as f: json.dump(data, f, indent=2)

    def get_group_config(self, chat_id: int):
        data = self._load()
        k = str(chat_id)
        if k not in data:
            data[k] = {"emoji": "🟢", "min_buy": 0, "tokens": []}
            self._save(data)
        return data[k]

    def add_token(self, chat_id, ca, chain):
        data = self._load()
        k = str(chat_id)
        if k not in data: data[k] = {"emoji": "🟢", "min_buy": 0, "tokens": []}
        tokens = data[k].get("tokens", [])
        if any(t['ca'] == ca for t in tokens): return False
        tokens.append({"ca": ca, "chain": chain})
        data[k]["tokens"] = tokens
        self._save(data)
        return True

    def get_tokens(self, chat_id: int):
        return self.get_group_config(chat_id).get("tokens", [])

    def get_all_groups_with_tokens(self):
        data = self._load()
        return [{"chat_id": int(k), "config": v} for k, v in data.items() if v.get("tokens")]

db = Database()
