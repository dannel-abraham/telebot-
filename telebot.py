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
    countries = ["us", "mx"]  # evitar múltiples países
    country = random.choice(countries)

    url = f"https://freenewsapi.io/api/v1/news?apikey={FREENEWS_API_KEY}&country={country}&lang=es,en"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()

            news_list = data.get("data", [])
            if news_list:
                n = random.choice(news_list)
                return f"📰 FreeNews ({country.upper()})\n{n.get('title','Sin título')}\n{n.get('url','')}"
    return None


async def get_currents():
    url = f"https://api.currentsapi.services/v1/latest-news?apiKey={CURRENTS_API_KEY}&language=es,en"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()

            news_list = data.get("news", [])
            if news_list:
                n = random.choice(news_list)
                return f"🌎 Currents\n{n.get('title','Sin título')}\n{n.get('url','')}"
    return None


async def get_pynews():
    url = "https://pynews.pythonanywhere.com/api/news"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()

            news_list = data.get("news", [])
            if news_list:
                n = random.choice(news_list)
                return f"⚡ PyNews\n{n.get('title','Sin título')}"
    return None


async def get_weather():
    url = "https://api.open-meteo.com/v1/forecast?latitude=23.11&longitude=-82.36&current_weather=true"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()

            w = data.get("current_weather")
            if w:
                return (
                    "🌦️ Clima en La Habana\n"
                    f"Temperatura: {w.get('temperature')}°C\n"
                    f"Viento: {w.get('windspeed')} km/h"
                )
    return None


# ---------------------------
# ROTACIÓN
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
        print(f"🔄 Usando API: {func.__name__}")
        result = await func()

        if result:
            return result

        print(f"⚠️ {func.__name__} devolvió None")

    except Exception as e:
        print(f"❌ Error en {func.__name__}: {e}")

    return None


# ---------------------------
# LOOP PRINCIPAL
# ---------------------------

async def main():
    print("🚀 Bot iniciado...")

    while True:
        msg = await get_next_data()

        # fallback si todo falla
        if not msg:
            msg = "⚠️ No hay datos disponibles ahora mismo. Intentando en breve..."

        try:
            await bot.send_message(chat_id=CHAT_ID, text=msg)
            print("✅ Mensaje enviado")
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")

        await asyncio.sleep(300)  # 5 minutos


if __name__ == "__main__":
    asyncio.run(main())
