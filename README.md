# Bot de Telegram para Render

Este bot envía datos aleatorios (clima, chistes, frases, Bitcoin, datos de gatos) cada 5 minutos.

## Configuración en Render

### Opción A: Web Service (Recomendado)

1. **Crea un nuevo Web Service** en [render.com](https://render.com)
2. Conecta tu repositorio de GitHub
3. Configura las siguientes variables de entorno:
   - `BOT_TOKEN`: Tu token de bot de Telegram (obtenido de @BotFather)

4. **Configuración**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python telebot.py`
   - Región: Elige la más cercana a ti
   - Instancia: Free (gratis)

### Opción B: Background Worker (Mejor para bots polling)

1. **Crea un nuevo Background Worker** en render.com
2. Conecta tu repositorio de GitHub
3. Variables de entorno:
   - `BOT_TOKEN`: Tu token de bot de Telegram

4. **Configuración**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python telebot.py`

> **Nota**: Los Background Workers son ideales para bots que usan polling, ya que están diseñados para procesos de larga duración.


## Uso

Envía `/start` al bot en Telegram para activarlo. El bot te enviará mensajes aleatorios cada 5 minutos.

## Notas de seguridad

⚠️ **Nunca commits tu BOT_TOKEN en el código**. Usa siempre variables de entorno.

## APIs utilizadas

- Open-Meteo (clima)
- JokeAPI (chistes)
- ZenQuotes (frases)
- CoinGecko (Bitcoin)
- CatFact (datos de gatos)
