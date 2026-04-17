import os
import asyncio
import aiohttp
import random
import logging
from telegram import Bot

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ---------- CLIMA (funciona) ----------
async def get_weather_havana():
    url = "https://api.open-meteo.com/v1/forecast?latitude=23.1330&longitude=-82.3830&current_weather=true"
    try:
        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as r:
                data = await r.json()
                w = data.get("current_weather")
                if w and w.get("temperature") is not None:
                    return (f"🌤️ La Habana\n"
                            f"🌡️ Temp: {w['temperature']}°C\n"
                            f"💨 Viento: {w['windspeed']} km/h")
                else:
                    return "⚠️ Sin datos del clima."
    except Exception as e:
        logging.error(f"Clima: {e}")
        return "⚠️ Error clima."

# ---------- FRASE MOTIVACIONAL (corregida) ----------
async def get_motivation_quote():
    # Quotable migró a quotable.kro.kr
    url = "https://api.quotable.kro.kr/random"
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as r:
                if r.status != 200:
                    # Fallback a ZenQuotes
                    async with session.get("https://zenquotes.io/api/random") as r2:
                        data = await r2.json()
                        if data and isinstance(data, list):
                            return f"💬 {data[0]['q']} — {data[0]['a']}"
                else:
                    data = await r.json()
                    return f"💬 {data['content']} — {data['author']}"
    except Exception as e:
        logging.error(f"Frase: {e}")
        return "💬 La persistencia es el camino al éxito. — Anónimo"

# ---------- NOTICIAS (con verificación de API key) ----------
async def get_top_news():
    if not NEWS_API_KEY:
        logging.warning("NEWS_API_KEY no configurada")
        return "📰 No hay clave de noticias configurada."
    url = f"https://newsapi.org/v2/top-headlines?country=cu&apiKey={NEWS_API_KEY}"
    try:
        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as r:
                if r.status == 401:
                    return "📰 Error: API key inválida."
                if r.status == 429:
                    return "📰 Límite de peticiones excedido."
                data = await r.json()
                if data.get("status") == "ok" and data.get("articles"):
                    article = data["articles"][0]
                    return f"📰 {article['title']}\n{article['url']}"
                else:
                    return "📰 Sin noticias disponibles."
    except Exception as e:
        logging.error(f"Noticias: {e}")
        return "📰 Error al obtener noticias."

# ---------- LÓGICA PRINCIPAL (sin cambios) ----------
async def main():
    bot = Bot(token=BOT_TOKEN)
    choice = random.choice(["weather", "quote", "news"])
    try:
        if choice == "weather":
            msg = await get_weather_havana()
        elif choice == "quote":
            msg = await get_motivation_quote()
        else:
            msg = await get_top_news()
        await bot.send_message(chat_id=CHAT_ID, text=msg)
        logging.info(f"Mensaje enviado: {choice}")
    except Exception as e:
        logging.error(f"Error enviando mensaje: {e}")

if __name__ == "__main__":
    asyncio.run(main())
