from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiohttp import web
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# =========================
# LANGUAGE KEYBOARD
# =========================

language_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
        ],
        [
            InlineKeyboardButton(text="🇹🇷 Türkçe", callback_data="lang_tr")
        ],
        [
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")
        ],
        [
            InlineKeyboardButton(text="🇩🇪 Deutsch", callback_data="lang_de")
        ],
    ]
)

# =========================
# MAIN MENU
# =========================

main_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🌭 Hot Dogs", callback_data="hotdogs")
        ],
        [
            InlineKeyboardButton(text="🌯 Shawarma", callback_data="shawarma")
        ],
        [
            InlineKeyboardButton(text="🥟 Chebureki", callback_data="chebureki")
        ],
        [
            InlineKeyboardButton(text="🥤 Drinks", callback_data="drinks")
        ],
        [
            InlineKeyboardButton(text="🛒 Cart", callback_data="cart")
        ],
    ]
)

# =========================
# START
# =========================

@dp.message(F.text == "/start")
async def start_handler(message: Message):
    await message.answer(
        "👋 Welcome to VAMO Cafe!\n\nChoose language:",
        reply_markup=language_keyboard
    )

# =========================
# LANGUAGE SELECT
# =========================

@dp.callback_query(F.data.startswith("lang_"))
async def language_selected(callback: CallbackQuery):

    await callback.message.edit_text(
        "✅ Language selected!\n\nChoose category:",
        reply_markup=main_menu
    )

# =========================
# CATEGORIES
# =========================

@dp.callback_query(F.data == "hotdogs")
async def hotdogs(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "🌭 Hot Dogs Menu\n\n"
        "Classic Hot Dog — 150 TL\n"
        "Cheese Hot Dog — 180 TL\n"
        "Double Hot Dog — 220 TL"
    )

@dp.callback_query(F.data == "shawarma")
async def shawarma(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "🌯 Shawarma Menu\n\n"
        "Chicken Shawarma — 200 TL\n"
        "Beef Shawarma — 250 TL\n"
        "Mega Shawarma — 320 TL"
    )

@dp.callback_query(F.data == "chebureki")
async def chebureki(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "🥟 Chebureki Menu\n\n"
        "Cheese Cheburek — 120 TL\n"
        "Meat Cheburek — 160 TL"
    )

@dp.callback_query(F.data == "drinks")
async def drinks(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "🥤 Drinks\n\n"
        "Coca-Cola — 60 TL\n"
        "Fanta — 60 TL\n"
        "Ayran — 50 TL"
    )

@dp.callback_query(F.data == "cart")
async def cart(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "🛒 Your cart is empty."
    )

# =========================
# HEALTHCHECK
# =========================

async def healthcheck(request):
    return web.Response(text="VAMO Cafe Bot is running")

# =========================
# MAIN
# =========================

async def main():

    print("VAMO Cafe Bot started")

    app = web.Application()
    app.router.add_get("/", healthcheck)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 10000))

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())