import random
import aiohttp
import os
import asyncio
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

FREENEWS_API_KEY = os.getenv("FREENEWS_API_KEY")
CURRENTS_API_KEY = os.getenv("CURRENTS_API_KEY")

bot = Bot(token=BOT_TOKEN)

# ---------------------------
# APIs
# ---------------------------

async def get_freenews():
    countries = ["us", "mx"]
    country = random.choice(countries)

    url = f"https://freenewsapi.io/api/v1/news?apikey={FREENEWS_API_KEY}&country={country}&lang=es,en"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            news = data.get("data", [])

            if news:
                n = random.choice(news)
                return f"📰 FreeNews ({country.upper()})\n{n.get('title')}\n{n.get('url')}"

async def get_currents():
    url = f"https://api.currentsapi.services/v1/latest-news?apiKey={CURRENTS_API_KEY}&language=es,en"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            news = data.get("news", [])

            if news:
                n = random.choice(news)
                return f"🌎 Currents\n{n.get('title')}\n{n.get('url')}"

async def get_pynews():
    url = "https://pynews.pythonanywhere.com/api/news"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            news = data.get("news", [])

            if news:
                n = random.choice(news)
                return f"⚡ PyNews\n{n.get('title')}"

async def get_weather():
    url = "https://api.open-meteo.com/v1/forecast?latitude=23.11&longitude=-82.36&current_weather=true"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            w = data.get("current_weather")

            if w:
                return f"🌦️ La Habana\nTemp: {w.get('temperature')}°C\nViento: {w.get('windspeed')} km/h"

# ---------------------------
# MAIN
# ---------------------------

async def main():
    funcs = [get_freenews, get_currents, get_pynews, get_weather]
    func = random.choice(funcs)

    try:
        msg = await func()
        if not msg:
            msg = "⚠️ Sin datos ahora mismo"
    except Exception as e:
        print("ERROR:", e)
        msg = "⚠️ Error obteniendo datos"

    await bot.send_message(chat_id=CHAT_ID, text=msg)

if __name__ == "__main__":
    asyncio.run(main())
