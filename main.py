import asyncio
from dotenv import load_dotenv
load_dotenv()

from bot import main

if __name__ == "__main__":
    try:
        # Mevcut bir döngü varsa onu alıp main'i çalıştırır
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Eğer döngü zaten çalışıyorsa (Render/Spyder gibi ortamlarda olabilir)
            task = loop.create_task(main())
        else:
            loop.run_until_complete(main())
    except RuntimeError:
        # Eğer hiç döngü yoksa yeni bir tane başlatır
        asyncio.run(main())
        
