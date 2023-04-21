import requests
import pandas as pd
import numpy as np
import talib
from datetime import datetime
import time
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
import nest_asyncio
import ssl
nest_asyncio.apply()


API_TOKEN = "your_bots_token"
CHAT_ID = "group_or_channel_id"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

async def send_message(text):
    await bot.send_message(chat_id=CHAT_ID, text=text)

async def main():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        while True:
            async with session.get("https://api.binance.com/api/v3/klines", params={"symbol": "BTCUSDT", "interval": "5m"}) as response:
                data = await response.json()
            df = pd.DataFrame(data, columns=["Open time", "Open", "High", "Low", "Close", "Volume", "Close time", "Quote asset volume", "Number of trades", "Taker buy base asset volume", "Taker buy quote asset volume", "Ignore"])
            df["Close"] = df["Close"].astype(float)
            df["High"] = df["High"].astype(float)
            df["Low"] = df["Low"].astype(float)
            short_ema_periods = [3, 5, 8, 10, 12, 15]
            long_ema_periods = [30, 35, 40, 45, 50, 60]
            for period in short_ema_periods + long_ema_periods:
                df[f"EMA{period}"] = talib.EMA(df["Close"], timeperiod=period)
            for period in short_ema_periods + long_ema_periods:
                df[f"EMA{period}_prev"] = df[f"EMA{period}"].shift(1)
            upper, middle, lower = talib.BBANDS(df["Close"], timeperiod=20)
            row = df.iloc[-1]
            buy_signals = sum([row[f"EMA{period}"] > row[f"EMA{period}_prev"] for period in short_ema_periods]) + sum([row["Close"] <= middle.iloc[-1]] * (row["Close"] > lower.iloc[-1])) + (row["Close"] > upper.iloc[-1])
            sell_signals = sum([row[f"EMA{period}"] < row[f"EMA{period}_prev"] for period in short_ema_periods]) + sum([row["Close"] >= middle.iloc[-1]] * (row["Close"] < upper.iloc[-1])) + (row["Close"] < lower.iloc[-1])

            if buy_signals >= 2:
                await send_message(f"Buy signal at {row['Close']} USDT on {datetime.fromtimestamp(row['Open time'] / 1000)}")
            elif sell_signals >= 2:
                await send_message(f"Sell signal at {row['Close']} USDT on {datetime.fromtimestamp(row['Open time'] / 1000)}")
            else:
                await send_message(f"No signal at {row['Close']} USDT on {datetime.fromtimestamp(row['Open time'] / 1000)}")
            await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(main())
    
    
