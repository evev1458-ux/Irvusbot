import json
import os

DB_FILE = "data.json"

class Database:
    def __init__(self):
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, "w") as f:
                json.dump({}, f)

    def _load(self):
        with open(DB_FILE, "r") as f:
            return json.load(f)

    def _save(self, data):
        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def get_group_config(self, chat_id: int) -> dict:
        data = self._load()
        key = str(chat_id)
        if key not in data:
            data[key] = {
                "tg_link": None,
                "web_link": None,
                "x_link": None,
                "emoji": "🟢",
                "min_buy": 0,
                "media_file_id": None,
                "media_type": None,
                "tokens": []
            }
            self._save(data)
        return data[key]

    def set_group_config(self, chat_id: int, key: str, value):
        data = self._load()
        k = str(chat_id)
        if k not in data:
            self.get_group_config(chat_id)
            data = self._load()
        data[k][key] = value
        self._save(data)

    def get_tokens(self, chat_id: int) -> list:
        cfg = self.get_group_config(chat_id)
        return cfg.get("tokens", [])

    def add_token(self, chat_id: int, ca: str, chain: str):
        data = self._load()
        k = str(chat_id)
        if k not in data:
            self.get_group_config(chat_id)
            data = self._load()
        tokens = data[k].get("tokens", [])
        # Aynı CA varsa ekleme
        for t in tokens:
            if t["ca"].lower() == ca.lower():
                return False
        tokens.append({"ca": ca, "chain": chain})
        data[k]["tokens"] = tokens
        self._save(data)
        return True

    def remove_token(self, chat_id: int, ca: str):
        data = self._load()
        k = str(chat_id)
        if k not in data:
            return False
        tokens = data[k].get("tokens", [])
        new_tokens = [t for t in tokens if t["ca"].lower() != ca.lower()]
        data[k]["tokens"] = new_tokens
        self._save(data)
        return True

    def get_all_groups_with_tokens(self) -> list:
        data = self._load()
        result = []
        for chat_id, cfg in data.items():
            if cfg.get("tokens"):
                result.append({"chat_id": int(chat_id), "config": cfg})
        return result
        
