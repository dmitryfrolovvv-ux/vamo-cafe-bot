from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils import executor
import asyncio
import os
from aiohttp import web

# =========================
# CONFIG
# =========================

TOKEN = "8729557900:AAGQceOGd-V5erYJpSXV5M95wrFU_JeMd4Q"
OWNER_ID = 1472777680

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# =========================
# STORAGE
# =========================

carts = {}
waiting_phone = set()

# =========================
# KEYBOARDS
# =========================

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🌭 Hot Dogs")
    kb.add("🌯 Shawarma")
    kb.add("🥟 Chebureki")
    kb.add("🥤 Drinks")
    kb.add("🛒 Cart")

    return kb

def back_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("⬅️ Back")

    return kb

def cart_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("✅ Checkout")
    kb.add("🗑 Clear Cart")
    kb.add("⬅️ Back")

    return kb

# =========================
# START
# =========================

@dp.message_handler(commands=['start'])
async def start(message: types.Message):

    user_id = message.from_user.id

    if user_id not in carts:
        carts[user_id] = []

    text = """
👋 Welcome to VAMO Cafe!

Choose category:
"""

    await message.answer(
        text,
        reply_markup=main_menu()
    )

# =========================
# HOT DOGS
# =========================

@dp.message_handler(lambda message: message.text == "🌭 Hot Dogs")
async def hotdogs(message: types.Message):

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🌭 Classic Hot Dog")
    kb.add("🧀 Cheese Hot Dog")
    kb.add("🌭🌭 Double Hot Dog")
    kb.add("⬅️ Back")

    text = """
🌭 Hot Dogs Menu

Classic Hot Dog — 150 TL
Cheese Hot Dog — 180 TL
Double Hot Dog — 220 TL
"""

    await message.answer(text, reply_markup=kb)

# =========================
# SHAWARMA
# =========================

@dp.message_handler(lambda message: message.text == "🌯 Shawarma")
async def shawarma(message: types.Message):

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🌯 Chicken Shawarma")
    kb.add("🥩 Beef Shawarma")
    kb.add("🔥 Mega Shawarma")
    kb.add("⬅️ Back")

    text = """
🌯 Shawarma Menu

Chicken Shawarma — 200 TL
Beef Shawarma — 250 TL
Mega Shawarma — 320 TL
"""

    await message.answer(text, reply_markup=kb)

# =========================
# CHEBUREKI
# =========================

@dp.message_handler(lambda message: message.text == "🥟 Chebureki")
async def chebureki(message: types.Message):

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🥟 Beef Chebureki")
    kb.add("🧀 Cheese Chebureki")
    kb.add("⬅️ Back")

    text = """
🥟 Chebureki Menu

Beef Chebureki — 180 TL
Cheese Chebureki — 160 TL
"""

    await message.answer(text, reply_markup=kb)

# =========================
# DRINKS
# =========================

@dp.message_handler(lambda message: message.text == "🥤 Drinks")
async def drinks(message: types.Message):

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🥤 Cola")
    kb.add("🥛 Ayran")
    kb.add("💧 Water")
    kb.add("⬅️ Back")

    text = """
🥤 Drinks Menu

Cola — 60 TL
Ayran — 50 TL
Water — 30 TL
"""

    await message.answer(text, reply_markup=kb)

# =========================
# ADD TO CART
# =========================

@dp.message_handler(lambda message: message.text in [
    "🌭 Classic Hot Dog",
    "🧀 Cheese Hot Dog",
    "🌭🌭 Double Hot Dog",
    "🌯 Chicken Shawarma",
    "🥩 Beef Shawarma",
    "🔥 Mega Shawarma",
    "🥟 Beef Chebureki",
    "🧀 Cheese Chebureki",
    "🥤 Cola",
    "🥛 Ayran",
    "💧 Water"
])
async def add_to_cart(message: types.Message):

    user_id = message.from_user.id

    if user_id not in carts:
        carts[user_id] = []

    item_map = {
        "🌭 Classic Hot Dog": {"name": "Classic Hot Dog", "price": 150},
        "🧀 Cheese Hot Dog": {"name": "Cheese Hot Dog", "price": 180},
        "🌭🌭 Double Hot Dog": {"name": "Double Hot Dog", "price": 220},

        "🌯 Chicken Shawarma": {"name": "Chicken Shawarma", "price": 200},
        "🥩 Beef Shawarma": {"name": "Beef Shawarma", "price": 250},
        "🔥 Mega Shawarma": {"name": "Mega Shawarma", "price": 320},

        "🥟 Beef Chebureki": {"name": "Beef Chebureki", "price": 180},
        "🧀 Cheese Chebureki": {"name": "Cheese Chebureki", "price": 160},

        "🥤 Cola": {"name": "Cola", "price": 60},
        "🥛 Ayran": {"name": "Ayran", "price": 50},
        "💧 Water": {"name": "Water", "price": 30},
    }

    item = item_map[message.text]

    carts[user_id].append(item)

    await message.answer(
        f"✅ Added: {item['name']}",
        reply_markup=main_menu()
    )

# =========================
# CART
# =========================

@dp.message_handler(lambda message: message.text == "🛒 Cart")
async def cart(message: types.Message):

    user_id = message.from_user.id

    if user_id not in carts or not carts[user_id]:

        await message.answer(
            "🛒 Your cart is empty!",
            reply_markup=main_menu()
        )

        return

    text = "🛒 Your Cart\n\n"

    total = 0

    for item in carts[user_id]:

        text += f"• {item['name']} — {item['price']} TL\n"

        total += item['price']

    text += f"\n💰 Total: {total} TL"

    await message.answer(
        text,
        reply_markup=cart_keyboard()
    )

# =========================
# CLEAR CART
# =========================

@dp.message_handler(lambda message: message.text == "🗑 Clear Cart")
async def clear_cart(message: types.Message):

    carts[message.from_user.id] = []

    await message.answer(
        "🗑 Cart cleared.",
        reply_markup=main_menu()
    )

# =========================
# BACK
# =========================

@dp.message_handler(lambda message: message.text == "⬅️ Back")
async def back(message: types.Message):

    await message.answer(
        "⬅️ Returned to main menu",
        reply_markup=main_menu()
    )

# =========================
# CHECKOUT
# =========================

@dp.message_handler(lambda message: message.text == "✅ Checkout")
async def checkout(message: types.Message):

    waiting_phone.add(message.from_user.id)

    await message.answer(
        "📞 Send your phone number:\n\nExample:\n+905551112233",
        reply_markup=types.ReplyKeyboardRemove()
    )

# =========================
# RECEIVE PHONE NUMBER
# =========================

@dp.message_handler(lambda message: message.from_user.id in waiting_phone)
async def process_phone(message: types.Message):

    user_id = message.from_user.id

    phone = message.text.strip()

    if user_id not in carts or not carts[user_id]:

        await message.answer(
            "🛒 Your cart is empty!",
            reply_markup=main_menu()
        )

        return

    cart_items = carts[user_id]

    total = 0
    cart_text = ""

    for item in cart_items:

        cart_text += f"• {item['name']} — {item['price']} TL\n"

        total += item['price']

    full_name = message.from_user.full_name
    username = message.from_user.username
    telegram_id = message.from_user.id

    if username:
        username_text = f"@{username}"
    else:
        username_text = "No username"

    order_text = f"""
📦 NEW ORDER

{cart_text}

💰 Total: {total} TL
📞 Phone: {phone}

👤 Client: {full_name}
🆔 ID: {telegram_id}
🔗 Username: {username_text}
"""

    # SEND ORDER TO OWNER
    await bot.send_message(OWNER_ID, order_text)

    await message.answer(
        "✅ Order sent successfully!\n\nVAMO Cafe will contact you soon.",
        reply_markup=main_menu()
    )

    carts[user_id] = []

    waiting_phone.remove(user_id)

# =========================
# WEB SERVER FOR RENDER
# =========================

async def handle(request):
    return web.Response(text="VAMO Cafe Bot is running!")

async def start_webserver():

    app = web.Application()

    app.router.add_get('/', handle)

    runner = web.AppRunner(app)

    await runner.setup()

    port = int(os.environ.get("PORT", 10000))

    site = web.TCPSite(
        runner,
        host="0.0.0.0",
        port=port
    )

    await site.start()

# =========================
# STARTUP
# =========================

async def on_startup(dp):

    asyncio.create_task(start_webserver())

    print("VAMO Cafe Bot started")

# =========================
# RUN
# =========================

if __name__ == "__main__":

    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup
    )