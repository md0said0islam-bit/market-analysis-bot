import asyncio
import os
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler
from pyquotex.client import Client
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

# 🔐 আপনার তথ্য
QUOTEX_EMAIL = "ineedjobnigga@gmail.com"
QUOTEX_PASS = "asdfghjkl0999+"
TELEGRAM_TOKEN = "8567250923:AAG-ZfnTGSUC_nP7ah-_hnt7evJ5aSKQ4pM"
CHAT_ID = "8048776600"

bot = Bot(TELEGRAM_TOKEN)
client = Client()

class MarketAnalysisBot:
    def __init__(self):
        self.latest_analysis = None
        self.is_running = True

    async def update_market(self):
        await client.connect()
        await client.login(QUOTEX_EMAIL, QUOTEX_PASS)
        logging.info("✅ Quotex এ লগইন সফল!")

        while self.is_running:
            try:
                candles = await client.get_candels("EURUSD", 60, 100)
                df = pd.DataFrame(candles, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
                df['time'] = pd.to_datetime(df['time'], unit='s')

                df['rsi'] = ta.rsi(df['close'], length=14)
                macd = ta.macd(df['close'])
                df = pd.concat([df, macd], axis=1)

                latest = df.iloc[-1]
                support = df['low'].rolling(20).min().iloc[-1]
                resistance = df['high'].rolling(20).max().iloc[-1]

                rsi = latest['rsi']
                macd_line = latest['MACD_12_26_9']
                signal_line = latest['MACDs_12_26_9']

                if rsi < 30 and macd_line > signal_line:
                    decision = "🟢 BUY"
                    reason = "RSI ওভারসল্ড + MACD বুলিশ ক্রস"
                elif rsi > 70 and macd_line < signal_line:
                    decision = "🔴 SELL"
                    reason = "RSI ওভারবট + MACD বিয়ারিশ ক্রস"
                else:
                    decision = "⚪ HOLD"
                    reason = "কোন ক্লিয়ার সিগন্যাল নেই"

                self.latest_analysis = {
                    'time': latest['time'],
                    'price': round(latest['close'], 5),
                    'rsi': round(rsi, 2),
                    'support': round(support, 5),
                    'resistance': round(resistance, 5),
                    'decision': decision,
                    'reason': reason
                }

                await asyncio.sleep(60)

            except Exception as e:
                logging.error(f"Error: {e}")
                await asyncio.sleep(10)

    async def get_signal(self):
        return self.latest_analysis

bot_instance = MarketAnalysisBot()

async def signal_handler(update, context):
    analysis = bot_instance.latest_analysis
    if not analysis:
        await update.message.reply_text("⏳ ডেটা লোড হচ্ছে...")
        return

    msg = f"""
📊 **EURUSD মার্কেট অ্যানালাইসিস**
🕐 {analysis['time']}
💰 প্রাইস: {analysis['price']}
📈 RSI: {analysis['rsi']}
📊 সাপোর্ট: {analysis['support']}
📈 রেসিস্ট্যান্স: {analysis['resistance']}
🎯 **সিগন্যাল: {analysis['decision']}**
📝 কারণ: {analysis['reason']}
    """
    await update.message.reply_text(msg)

async def main():
    asyncio.create_task(bot_instance.update_market())
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("signal", signal_handler))
    logging.info("🤖 মার্কেট অ্যানালাইসিস বট চালু! Telegram-এ /signal দিন")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
