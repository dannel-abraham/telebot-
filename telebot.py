import asyncio
import random
import logging
import aiohttp
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

# Token para pruebas (REEMPLAZA con tu token real)
BOT_TOKEN = "8703222853:AAHBgU_2izFJyd3QV6O7QFSi6P8p7tMQtZY"

# Para producción en Render, usa variables de entorno:
# BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# HTTP HELPER (async real)
# ------------------------------------------------------------

async def fetch_json(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()
    except Exception as e:
        logger.error(f"HTTP error: {e}")
        return None

# ------------------------------------------------------------
# APIs
# ------------------------------------------------------------

async def get_open_meteo_weather():
    data = await fetch_json(
        "https://api.open-meteo.com/v1/forecast?latitude=40.4168&longitude=-3.7038&current_weather=true"
    )
    try:
        current = data["current_weather"]
        return f"🌤️ Clima en Madrid: {current['temperature']}°C | viento {current['windspeed']} km/h"
    except:
        return None


async def get_spanish_joke():
    data = await fetch_json("https://v2.jokeapi.dev/joke/Any?lang=es")
    try:
        if data["type"] == "single":
            return f"😄 {data['joke']}"
        else:
            return f"😄 {data['setup']}\n{data['delivery']}"
    except:
        return None


async def get_quote():
    data = await fetch_json("https://zenquotes.io/api/random")
    try:
        return f"📜 {data[0]['q']} — {data[0]['a']}"
    except:
        return None


async def get_bitcoin():
    data = await fetch_json(
        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    )
    try:
        return f"💰 Bitcoin: ${data['bitcoin']['usd']} USD"
    except:
        return None


async def get_cat_fact():
    data = await fetch_json("https://catfact.ninja/fact")
    try:
        return f"🐱 {data['fact']}"
    except:
        return None


# ------------------------------------------------------------
# LÓGICA CENTRAL
# ------------------------------------------------------------

async def get_random_message():
    funcs = [
        get_open_meteo_weather,
        get_spanish_joke,
        get_quote,
        get_bitcoin,
        get_cat_fact,
    ]

    func = random.choice(funcs)
    logger.info(f"Ejecutando: {func.__name__}")

    return await func()


# ------------------------------------------------------------
# JOB (envío automático)
# ------------------------------------------------------------

async def job_send(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id

    message = await get_random_message()

    if message:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            logger.error(f"Telegram error: {e}")
    else:
        logger.warning("No se obtuvo mensaje")


# ------------------------------------------------------------
# /start
# ------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    await update.message.reply_text(
        "🤖 Bot activo. Te enviaré datos aleatorios cada 5 minutos."
    )

    # Enviar uno inmediato
    message = await get_random_message()
    if message:
        await update.message.reply_text(message)

    # Programar job
    job_name = f"job_{chat_id}"

    if not context.job_queue.get_jobs_by_name(job_name):
        context.job_queue.run_repeating(
            job_send,
            interval=300,
            first=10,
            chat_id=chat_id,
            name=job_name
        )

        logger.info(f"Job creado para {chat_id}")


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():
    app = Application.builder() \
        .token(BOT_TOKEN) \
        .build()

    app.add_handler(CommandHandler("start", start))

    logger.info("Bot corriendo...")
    
    # Modo polling (funciona en Render con workers gratuitos)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
