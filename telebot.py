import asyncio
import random
import aiohttp
import os
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

FREENEWS_API_KEY = os.getenv("FREENEWS_API_KEY")
CURRENTS_API_KEY = os.getenv("CURRENTS_API_KEY")

bot = Bot(token=BOT_TOKEN)

# ---------------------------
# FUNCIONES DE APIs
# ---------------------------

async def get_freenews():
    url = f"https://freenewsapi.io/api/v1/news?apikey={FREENEWS_API_KEY}&country=us,cu,mx&lang=es,en"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            if "data" in data and data["data"]:
                n = random.choice(data["data"])
                return f"📰 FreeNews\n{n.get('title','Sin título')}\n{n.get('url','')}"
    return None


async def get_currents():
    url = f"https://api.currentsapi.services/v1/latest-news?apiKey={CURRENTS_API_KEY}&language=es,en"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            if "news" in data and data["news"]:
                n = random.choice(data["news"])
                return f"🌎 Currents\n{n.get('title','Sin título')}\n{n.get('url','')}"
    return None


async def get_pynews():
    url = "https://pynews.pythonanywhere.com/api/news"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            if "news" in data and data["news"]:
                n = random.choice(data["news"])
                return f"⚡ PyNews\n{n.get('title','Sin título')}"
    return None


async def get_weather():
    # Habana, Cuba
    url = "https://api.open-meteo.com/v1/forecast?latitude=23.11&longitude=-82.36&current_weather=true"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            if "current_weather" in data:
                w = data["current_weather"]
                return (
                    "🌦️ Clima en La Habana\n"
                    f"Temperatura: {w.get('temperature')}°C\n"
                    f"Viento: {w.get('windspeed')} km/h"
                )
    return None


# ---------------------------
# ROTADOR DE APIs
# ---------------------------

API_FUNCTIONS = [
    get_freenews,
    get_currents,
    get_pynews,
    get_weather
]

last_index = -1


async def get_next_data():
    global last_index
    last_index = (last_index + 1) % len(API_FUNCTIONS)
    func = API_FUNCTIONS[last_index]

    try:
        result = await func()
        if result:
            return result
    except Exception as e:
        print("Error:", e)

    return "⚠️ No se pudo obtener información en este ciclo."


# ---------------------------
# LOOP PRINCIPAL
# ---------------------------

async def main():
    print("Bot corriendo...")
    while True:
        try:
            msg = await get_next_data()
            await bot.send_message(chat_id=CHAT_ID, text=msg)
        except Exception as e:
            print("Error enviando mensaje:", e)

        await asyncio.sleep(300)  # 5 minutos


if __name__ == "__main__":
    asyncio.run(main())
