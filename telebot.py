#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import nest_asyncio  # <-- NUEVO: Para solucionar conflictos de event loop en Render
import logging
import os
import random
import re
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Aplicar el parche de nest_asyncio para entornos con event loop ya corriendo
nest_asyncio.apply()

# ----------------------------------------------------------------------
# Configuración de logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Constantes y configuración
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("No se encontró la variable de entorno TELEGRAM_TOKEN")

# IDs de administradores (pueden ser varios separados por coma)
ADMIN_IDS_STR = os.environ.get("ADMIN_IDS", "")
ADMIN_IDS = set()
if ADMIN_IDS_STR:
    for admin_id in ADMIN_IDS_STR.split(","):
        try:
            ADMIN_IDS.add(int(admin_id.strip()))
        except ValueError:
            logger.warning(f"ID de admin inválido: {admin_id}")

# Canal donde se enviarán los mensajes programados
CHANNEL_ID = os.environ.get("CHANNEL_ID")
if CHANNEL_ID:
    try:
        CHANNEL_ID = int(CHANNEL_ID)
    except ValueError:
        logger.warning(f"CHANNEL_ID inválido: {CHANNEL_ID}")
        CHANNEL_ID = None

# ----------------------------------------------------------------------
# Estructuras de datos en memoria (para almacenar recordatorios)
# Formato: { chat_id: {"message": str, "interval": int(minutos), "last_sent": datetime} }
reminders: Dict[int, Dict] = {}

# ----------------------------------------------------------------------
# Funciones de utilidad
def is_admin(user_id: int) -> bool:
    """Verifica si un usuario es administrador."""
    return user_id in ADMIN_IDS

def parse_interval(text: str) -> int:
    """Convierte una cadena como '30m', '2h', '1d' a minutos."""
    match = re.match(r"^(\d+)([mhd])$", text.lower().strip())
    if not match:
        raise ValueError("Formato inválido. Usa por ejemplo: 30m, 2h, 1d")
    value = int(match.group(1))
    unit = match.group(2)
    if unit == "m":
        return value
    elif unit == "h":
        return value * 60
    elif unit == "d":
        return value * 60 * 24
    else:
        raise ValueError("Unidad no soportada")

# ----------------------------------------------------------------------
# Comandos del bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"¡Hola {user.first_name}! Soy un bot para programar mensajes periódicos.\n"
        f"Usa /help para ver los comandos disponibles."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /help"""
    help_text = (
        "📋 *Comandos disponibles:*\n\n"
        "/start - Inicia el bot\n"
        "/help - Muestra esta ayuda\n"
        "/set `<mensaje>` `<intervalo>` - Programa un mensaje periódico (solo admins)\n"
        "   Ejemplo: `/set Hola mundo! 30m`\n"
        "   Intervalos: `m` (minutos), `h` (horas), `d` (días)\n"
        "/unset - Elimina el recordatorio programado para este chat (solo admins)\n"
        "/trigger - Envía el mensaje programado ahora mismo (para pruebas)\n"
        "/status - Muestra el estado actual del recordatorio en este chat\n"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /set <mensaje> <intervalo>"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not is_admin(user_id):
        await update.message.reply_text("⛔ No tienes permisos para usar este comando.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Uso: /set <mensaje> <intervalo>\n"
            "Ejemplo: /set Hola mundo! 30m"
        )
        return

    # El intervalo es el último argumento
    interval_str = context.args[-1]
    # El mensaje es todo lo anterior
    message = " ".join(context.args[:-1])

    try:
        interval_minutes = parse_interval(interval_str)
    except ValueError as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return

    reminders[chat_id] = {
        "message": message,
        "interval": interval_minutes,
        "last_sent": datetime.now(),  # Se inicia ahora, primer envío tras intervalo
    }

    await update.message.reply_text(
        f"✅ Recordatorio programado cada {interval_minutes} minutos.\n"
        f"Mensaje: {message}"
    )
    logger.info(f"Recordatorio establecido en chat {chat_id} por usuario {user_id}")

async def unset_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /unset"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not is_admin(user_id):
        await update.message.reply_text("⛔ No tienes permisos para usar este comando.")
        return

    if chat_id in reminders:
        del reminders[chat_id]
        await update.message.reply_text("✅ Recordatorio eliminado.")
        logger.info(f"Recordatorio eliminado en chat {chat_id} por usuario {user_id}")
    else:
        await update.message.reply_text("ℹ️ No hay ningún recordatorio activo en este chat.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /status"""
    chat_id = update.effective_chat.id

    if chat_id in reminders:
        rem = reminders[chat_id]
        last = rem["last_sent"].strftime("%Y-%m-%d %H:%M:%S")
        next_time = rem["last_sent"] + timedelta(minutes=rem["interval"])
        next_str = next_time.strftime("%Y-%m-%d %H:%M:%S")
        await update.message.reply_text(
            f"📌 Recordatorio activo:\n"
            f"Mensaje: {rem['message']}\n"
            f"Intervalo: {rem['interval']} minutos\n"
            f"Último envío: {last}\n"
            f"Próximo envío: {next_str}"
        )
    else:
        await update.message.reply_text("ℹ️ No hay recordatorio activo en este chat.")

async def trigger_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /trigger: envía el mensaje inmediatamente (solo admins)."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not is_admin(user_id):
        await update.message.reply_text("⛔ No tienes permisos para usar este comando.")
        return

    if chat_id not in reminders:
        await update.message.reply_text("ℹ️ No hay recordatorio activo que disparar.")
        return

    rem = reminders[chat_id]
    message = rem["message"]
    # Enviar al canal si está definido, sino al mismo chat
    target_id = CHANNEL_ID if CHANNEL_ID else chat_id
    try:
        await context.bot.send_message(target_id, message)
        # Actualizar last_sent
        reminders[chat_id]["last_sent"] = datetime.now()
        await update.message.reply_text("✅ Mensaje enviado manualmente.")
    except Exception as e:
        logger.error(f"Error al enviar mensaje trigger: {e}")
        await update.message.reply_text(f"❌ Error al enviar: {e}")

# ----------------------------------------------------------------------
# Tarea periódica para enviar los recordatorios automáticamente
async def reminder_checker(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Se ejecuta cada minuto para verificar si toca enviar algún recordatorio."""
    now = datetime.now()
    for chat_id, rem in list(reminders.items()):
        last_sent = rem["last_sent"]
        interval = rem["interval"]
        next_send = last_sent + timedelta(minutes=interval)

        if now >= next_send:
            # Determinar destino
            target_id = CHANNEL_ID if CHANNEL_ID else chat_id
            try:
                await context.bot.send_message(target_id, rem["message"])
                reminders[chat_id]["last_sent"] = now
                logger.info(f"Recordatorio enviado a {target_id}")
            except Exception as e:
                logger.error(f"Error enviando recordatorio a {target_id}: {e}")

# ----------------------------------------------------------------------
# Manejo de señales para cierre limpio (útil en Render)
def signal_handler(sig, frame):
    logger.info("Señal de terminación recibida. Cerrando...")
    # asyncio.get_event_loop().stop()
    # En vez de parar bruscamente, dejamos que el proceso termine solo
    raise SystemExit(0)

# ----------------------------------------------------------------------
# Función principal asíncrona
async def main() -> None:
    """Inicia el bot."""
    # Configurar señales para un cierre más limpio (opcional)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Iniciando bot de Telegram...")

    # Crear la aplicación
    app = Application.builder().token(TOKEN).build()

    # Registrar handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("set", set_reminder))
    app.add_handler(CommandHandler("unset", unset_reminder))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("trigger", trigger_now))

    # JobQueue para la tarea periódica (cada 60 segundos)
    job_queue = app.job_queue
    if job_queue:
        job_queue.run_repeating(reminder_checker, interval=60, first=10)
    else:
        logger.warning("JobQueue no disponible. La verificación periódica no funcionará.")

    # Determinar si usar webhook o polling
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
        # Modo Polling (desarrollo o si no hay WEBHOOK_URL)
        logger.info("Iniciando con polling (no se detectó WEBHOOK_URL)")
        await app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    # Esta es la parte clave para evitar problemas de event loop en Render
    try:
        # Intentamos obtener el loop actual (si ya está corriendo)
        loop = asyncio.get_running_loop()
        # Si existe, creamos una tarea y la dejamos correr (el loop ya está en marcha)
        logger.info("Event loop ya en ejecución, creando tarea para main()")
        loop.create_task(main())
        # Importante: no bloqueamos aquí, dejamos que el proceso siga vivo.
        # Render mantendrá el worker activo.
    except RuntimeError:
        # No hay loop corriendo, podemos usar asyncio.run() normalmente
        logger.info("No hay event loop, iniciando con asyncio.run()")
        asyncio.run(main())
