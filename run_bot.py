import sys
import os
from flask import Flask
from threading import Thread

# Flask Sunucusu (Render Port Hatası İçin)
app = Flask('')

@app.route('/')
def home():
    return "Irvus Bot is Alive!"

def run_flask():
    # Render varsayılan olarak 10000 portunu bekler
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# Proje kök dizinini yola ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.main import run

if __name__ == "__main__":
    # Önce web sunucusunu başlat
    keep_alive()
    # Sonra botu başlat
    run()
    
