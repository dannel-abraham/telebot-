#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import os
from telegram import Bot
from telegram.ext import Application

# Configuración de logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Configuración
# TOKEN = os.environ.get("TELEGRAM_TOKEN")
# Constantes y configuración
TOKEN = "8703222853:AAHBgU_2izFJyd3QV6O7QFSi6P8p7tMQtZY"
if not TOKEN:
    raise ValueError("No se encontró la variable de entorno TELEGRAM_TOKEN")

CHAT_ID = os.environ.get("CHAT_ID")
if not CHAT_ID:
    raise ValueError("No se encontró la variable de entorno CHAT_ID")

# ----------------------------------------------------------------------
# Saludos genéricos
SALUDOS = [
    "¡Hola! 👋 Espero que tengas un excelente día.",
    "🌟 ¡Buenas! ¿Cómo estás?",
    "¡Saludos! 😊 Que tengas un momento genial.",
    "👋 ¡Hola de nuevo! Todo bien por aquí.",
    "✨ ¡Hey! Pasaba a saludarte.",
    "🌞 ¡Hola! Espero que estés teniendo un gran día.",
    "💬 ¡Saludos! ¿Qué tal todo?",
    "🎉 ¡Hola! Aquí seguimos.",
]

async def enviar_saludo(bot: Bot) -> None:
    """Envía un saludo genérico al chat configurado."""
    saludo = SALUDOS[hash(str(asyncio.get_event_loop().time())) % len(SALUDOS)]
    try:
        await bot.send_message(chat_id=CHAT_ID, text=saludo)
        logger.info(f"Saludo enviado: {saludo}")
    except Exception as e:
        logger.error(f"Error al enviar saludo: {e}")

async def main() -> None:
    """Función principal del bot."""
    logger.info("Iniciando bot de saludos...")
    
    # Crear la aplicación
    app = Application.builder().token(TOKEN).build()
    
    # Enviar primer saludo al iniciar
    await enviar_saludo(app.bot)
    
    # Programar envío cada 5 minutos (300 segundos)
    app.job_queue.run_repeating(
        lambda context: asyncio.create_task(enviar_saludo(context.bot)),
        interval=300,
        first=300,
    )
    
    logger.info("Bot configurado. Enviando saludos cada 5 minutos.")
    
    # Determinar modo de ejecución
    webhook_url = os.environ.get("WEBHOOK_URL")
    port = int(os.environ.get("PORT", "8443"))
    
    if webhook_url:
        # Modo Webhook (recomendado para Render)
        logger.info(f"Iniciando con webhook en {webhook_url}")
        await app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=TOKEN,
            webhook_url=f"{webhook_url}/{TOKEN}",
            drop_pending_updates=True,
        )
    else:
        # Modo Polling
        logger.info("Iniciando con polling")
        await app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
