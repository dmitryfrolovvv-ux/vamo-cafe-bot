from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()


@dp.message(F.text == "/start")
async def start_handler(message: Message):
    await message.answer(
        "👋 Welcome to VAMO Cafe!\n\n"
        "Choose language:\n"
        "🇷🇺 Русский\n"
        "🇹🇷 Türkçe\n"
        "🇬🇧 English\n"
        "🇩🇪 Deutsch"
    )


async def main():
    print("VAMO Cafe Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())