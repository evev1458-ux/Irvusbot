import json, os
DB_FILE = "data.json"

class Database:
    def __init__(self):
        if not os.path.exists(DB_FILE): self._save({})
    def _load(self):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    def _save(self, d):
        with open(DB_FILE, "w") as f: json.dump(d, f, indent=2)
    def get_group_config(self, chat_id):
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
        data[k]["tokens"].append({"ca": ca, "chain": chain})
        self._save(data)
    def get_tokens(self, chat_id): return self.get_group_config(chat_id).get("tokens", [])
    def get_all_groups_with_tokens(self):
        d = self._load()
        return [{"chat_id": int(k), "config": v} for k, v in d.items() if v.get("tokens")]

db = Database()
