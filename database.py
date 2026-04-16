import json
import os
import threading
from typing import List, Dict, Any

DB_FILE = "data/bot_data.json"

class Database:
    def __init__(self):
        self.lock = threading.Lock()
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(DB_FILE):
            self._write({})

    def _read(self) -> dict:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _get_group(self, chat_id: int) -> dict:
        data = self._read()
        key = str(chat_id)
        if key not in data:
            data[key] = {"config": {}, "tokens": []}
            self._write(data)
        return data[key]

    def get_group_config(self, chat_id: int) -> dict:
        with self.lock:
            return self._get_group(chat_id).get("config", {})

    def save_group_config(self, chat_id: int, config: dict):
        with self.lock:
            data = self._read()
            key = str(chat_id)
            if key not in data:
                data[key] = {"config": {}, "tokens": []}
            data[key]["config"] = config
            self._write(data)

    def get_tokens(self, chat_id: int) -> List[Dict]:
        with self.lock:
            return self._get_group(chat_id).get("tokens", [])

    def add_token(self, chat_id: int, ca: str, chain: str):
        with self.lock:
            data = self._read()
            key = str(chat_id)
            if key not in data:
                data[key] = {"config": {}, "tokens": []}
            tokens = data[key]["tokens"]
            # Duplicate kontrolü
            if not any(t["ca"].lower() == ca.lower() for t in tokens):
                tokens.append({"ca": ca, "chain": chain})
                self._write(data)

    def remove_token(self, chat_id: int, ca: str):
        with self.lock:
            data = self._read()
            key = str(chat_id)
            if key in data:
                data[key]["tokens"] = [
                    t for t in data[key]["tokens"]
                    if t["ca"].lower() != ca.lower()
                ]
                self._write(data)

    def get_all_groups_with_tokens(self) -> List[Dict]:
        """Tüm grupları ve tokenlerini döndür (monitoring için)"""
        with self.lock:
            data = self._read()
            result = []
            for chat_id, group_data in data.items():
                tokens = group_data.get("tokens", [])
                if tokens:
                    result.append({
                        "chat_id": int(chat_id),
                        "tokens": tokens,
                        "config": group_data.get("config", {})
                    })
            return result

    def get_last_tx(self, chat_id: int, ca: str) -> str:
        """Son işlenen tx hash'ini döndür"""
        with self.lock:
            data = self._read()
            key = str(chat_id)
            if key in data:
                txs = data[key].get("last_txs", {})
                return txs.get(ca.lower(), "")
            return ""

    def set_last_tx(self, chat_id: int, ca: str, tx_hash: str):
        """Son işlenen tx hash'ini kaydet"""
        with self.lock:
            data = self._read()
            key = str(chat_id)
            if key not in data:
                data[key] = {"config": {}, "tokens": [], "last_txs": {}}
            if "last_txs" not in data[key]:
                data[key]["last_txs"] = {}
            data[key]["last_txs"][ca.lower()] = tx_hash
            self._write(data)
