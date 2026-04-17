import os
import asyncio
import aiohttp
import logging
from datetime import datetime
from telegram import Bot, Update
from telegram.constants import ParseMode

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 🔐 Variables de entorno
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # Para broadcasts automáticos
WEATHER_CITY = "Havana" # Ciudad por defecto

# 🌍 Códigos WMO para clima
WMO_CODES = {
    0: "☀️ Despejado", 1: "🌤 Mayormente despejado", 2: "⛅ Parcialmente nublado",
    3: "☁️ Nublado", 45: "🌫 Niebla", 51: "🌧 Llovizna", 61: "🌧 Lluvia",
    71: "🌨 Nieve", 80: "🌦 Chubascos", 95: "⛈ Tormenta", 96: "⛈ Tormenta + granizo"
}

# ========== 📡 APIs GRATIS SIN REGISTRO ==========

async def get_weather(city: str, session: aiohttp.ClientSession) -> str:
    """Clima actual vía Open-Meteo (geocoding + forecast)"""
    try:
        # 1. Geocodificación
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=es"
        async with session.get(geo_url, timeout=aiohttp.ClientTimeout(total=5)) as r:
            geo = await r.json()
        if not geo.get("results"):
            return f"❌ Ciudad '{city}' no encontrada."
        
        loc = geo["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]
        
        # 2. Clima actual
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
        async with session.get(weather_url, timeout=aiohttp.ClientTimeout(total=5)) as r:
            data = await r.json()
        
        w = data["current_weather"]
        temp = w["temperature"]
        desc = WMO_CODES.get(w["weathercode"], "🌍 Variable")
        return f"📍 *{loc['name']}, {loc.get('country', '')}*\n🌡 {temp}°C → {desc}"
    except Exception as e:
        logger.error(f"Clima: {e}")
        return "⚠️ Error obteniendo el clima."

async def get_advice(session: aiohttp.ClientSession) -> str:
    """Consejo aleatorio vía api.adviceslip.com"""
    try:
        url = "https://api.adviceslip.com/advice"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as r:
            data = await r.json()
        return f"💡 {data['slip']['advice']}"
    except Exception as e:
        logger.error(f"Consejo: {e}")
        return "💡 La paciencia es amarga, pero su fruto es dulce. — Rousseau"

async def get_age(name: str, session: aiohttp.ClientSession) -> str:
    """Edad promedio estadística vía api.agify.io"""
    try:
        url = f"https://api.agify.io/?name={name}"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as r:
            data = await r.json()
        if not data.get("count") or data["count"] < 10:
            return f"❌ '{name}' tiene pocos registros públicos."
        return f"👤 '{name}' → ~{data['age']} años en promedio\n📊 Basado en {data['count']} registros."
    except Exception as e:
        logger.error(f"Edad: {e}")
        return "⚠️ Error consultando edad."

# ========== 🔄 PROCESAR COMANDOS (PULL) ==========

async def process_commands(bot: Bot, session: aiohttp.ClientSession):
    """Revisa updates pendientes y responde comandos"""
    try:
        updates = await bot.get_updates(timeout=10, limit=10)
        for update in updates:
            if not update.message or not update.message.text:
                continue
            
            msg = update.message
            text = msg.text.strip().lower()
            chat_id = msg.chat_id
            
            if text.startswith("/clima"):
                city = text.replace("/clima", "").strip() or WEATHER_CITY
                response = await get_weather(city, session)
            elif text.startswith("/consejo"):
                response = await get_advice(session)
            elif text.startswith("/edad"):
                name = text.replace("/edad", "").strip()                if not name:
                    response = "Uso: /edad [nombre]"
                else:
                    response = await get_age(name, session)
            elif text in ["/start", "/help"]:
                response = (
                    "🤖 *Bot Híbrido (Cron + Comandos)*\n\n"
                    "🌤 `/clima [ciudad]` → Clima actual\n"
                    "💡 `/consejo` → Consejo aleatorio\n"
                    "🎂 `/edad [nombre]` → Edad promedio\n\n"
                    "✨ También recibes broadcasts automáticos 2x/día."
                )
            else:
                continue  # Ignorar mensajes no reconocidos
            
            await bot.send_message(chat_id=chat_id, text=response, parse_mode=ParseMode.MARKDOWN)
            await bot.delete_message(chat_id=chat_id, message_id=update.update_id + 1) if update.update_id else None
            logger.info(f"Comando procesado: {text} → chat {chat_id}")
            
    except Exception as e:
        logger.error(f"Error procesando comandos: {e}")

# ========== 📢 BROADCAST AUTOMÁTICO (PUSH) ==========

async def send_broadcast(bot: Bot, session: aiohttp.ClientSession):
    """Envía mensaje automático al CHAT_ID configurado"""
    if not CHAT_ID:
        logger.warning("CHAT_ID no configurado → omitiendo broadcast")
        return
    
    # Alternar entre clima y consejo
    choice = "weather" if datetime.now().hour < 14 else "advice"
    
    if choice == "weather":
        content = await get_weather(WEATHER_CITY, session)
        prefix = f"🌅 *Reporte matutino*" if datetime.now().hour < 14 else f"🌙 *Reporte nocturno*"
    else:
        content = await get_advice(session)
        prefix = "💫 *Consejo del día*"
    
    full_msg = f"{prefix}\n\n{content}\n\n_{datetime.now().strftime('%d/%m %H:%M UTC')}_"
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text=full_msg, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"Broadcast enviado: {choice}")
    except Exception as e:
        logger.error(f"Error en broadcast: {e}")

# ========== 🎯 MAIN ==========
async def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN no configurado en variables de entorno")
        return
    
    bot = Bot(token=BOT_TOKEN)
    
    async with aiohttp.ClientSession() as session:
        # 1. Primero procesar comandos pendientes (respuesta a usuarios)
        await process_commands(bot, session)
        
        # 2. Luego enviar broadcast si corresponde (automático)
        # Solo en ejecuciones programadas (no en workflow_dispatch manual)
        if os.getenv("GITHUB_EVENT_NAME") == "schedule":
            await send_broadcast(bot, session)

if __name__ == "__main__":
    asyncio.run(main())
