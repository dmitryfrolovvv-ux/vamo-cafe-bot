from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
import asyncio
import os
from aiohttp import web

TOKEN = "YOUR_BOT_TOKEN"
OWNER_ID = 1472777680

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# =========================
# CART STORAGE
# =========================

carts = {}
user_language = {}
waiting_phone = set()

# =========================
# MENU DATA
# =========================

MENU = {
    "hotdogs": [
        {"name": "Classic Hot Dog", "price": 150},
        {"name": "Cheese Hot Dog", "price": 180},
        {"name": "Double Hot Dog", "price": 220},
    ],
    "shawarma": [
        {"name": "Chicken Shawarma", "price": 200},
        {"name": "Beef Shawarma", "price": 250},
        {"name": "Mega Shawarma", "price": 320},
    ],
    "chebureki": [
        {"name": "Chebureki Beef", "price": 180},
        {"name": "Chebureki Cheese", "price": 160},
    ],
    "drinks": [
        {"name": "Cola", "price": 60},
        {"name": "Ayran", "price": 50},
        {"name": "Water", "price": 30},
    ]
}

# =========================
# KEYBOARDS
# =========================

def language_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🇷🇺 Русский")
    kb.add("🇹🇷 Türkçe")
    kb.add("🇬🇧 English")
    kb.add("🇩🇪 Deutsch")

    return kb

def get_main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🌭 Hot Dogs")
    kb.add("🌯 Shawarma")
    kb.add("🥟 Chebureki")
    kb.add("🥤 Drinks")
    kb.add("🛒 Cart")
    kb.add("🌐 Change Language")

    return kb

def get_back_keyboard():
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

    await message.answer(
        "👋 Welcome to VAMO Cafe!\n\nChoose language:",
        reply_markup=language_keyboard()
    )

# =========================
# LANGUAGE
# =========================

@dp.message_handler(lambda message: message.text in [
    "🇷🇺 Русский",
    "🇹🇷 Türkçe",
    "🇬🇧 English",
    "🇩🇪 Deutsch"
])
async def set_language(message: types.Message):

    user_language[message.from_user.id] = message.text

    await message.answer(
        "✅ Language selected!\n\nChoose category:",
        reply_markup=get_main_menu()
    )

# =========================
# CHANGE LANGUAGE
# =========================

@dp.message_handler(lambda message: message.text == "🌐 Change Language")
async def change_language(message: types.Message):

    await message.answer(
        "🌐 Choose new language:",
        reply_markup=language_keyboard()
    )

# =========================
# HOT DOGS
# =========================

@dp.message_handler(lambda message: message.text == "🌭 Hot Dogs")
async def hotdogs(message: types.Message):

    text = "🌭 Hot Dogs Menu\n\n"

    for item in MENU["hotdogs"]:
        text += f"{item['name']} — {item['price']} TL\n"

    text += "\nSend number:\n1 / 2 / 3"

    await message.answer(text, reply_markup=get_back_keyboard())

# =========================
# SHAWARMA
# =========================

@dp.message_handler(lambda message: message.text == "🌯 Shawarma")
async def shawarma(message: types.Message):

    text = "🌯 Shawarma Menu\n\n"

    for item in MENU["shawarma"]:
        text += f"{item['name']} — {item['price']} TL\n"

    text += "\nSend number:\n1 / 2 / 3"

    await message.answer(text, reply_markup=get_back_keyboard())

# =========================
# CHEBUREKI
# =========================

@dp.message_handler(lambda message: message.text == "🥟 Chebureki")
async def chebureki(message: types.Message):

    text = "🥟 Chebureki Menu\n\n"

    for item in MENU["chebureki"]:
        text += f"{item['name']} — {item['price']} TL\n"

    text += "\nSend number:\n1 / 2"

    await message.answer(text, reply_markup=get_back_keyboard())

# =========================
# DRINKS
# =========================

@dp.message_handler(lambda message: message.text == "🥤 Drinks")
async def drinks(message: types.Message):

    text = "🥤 Drinks Menu\n\n"

    for item in MENU["drinks"]:
        text += f"{item['name']} — {item['price']} TL\n"

    text += "\nSend number:\n1 / 2 / 3"

    await message.answer(text, reply_markup=get_back_keyboard())

# =========================
# ADD ITEMS
# =========================

@dp.message_handler(lambda message: message.text.isdigit())
async def add_item(message: types.Message):

    user_id = message.from_user.id
    number = int(message.text)

    item = None

    if number == 1:
        item = MENU["hotdogs"][0]
    elif number == 2:
        item = MENU["hotdogs"][1]
    elif number == 3:
        item = MENU["hotdogs"][2]

    if item:
        carts[user_id].append(item)

        await message.answer(
            f"✅ Added: {item['name']}",
            reply_markup=get_main_menu()
        )

# =========================
# CART
# =========================

@dp.message_handler(lambda message: message.text == "🛒 Cart")
async def show_cart(message: types.Message):

    user_id = message.from_user.id

    if not carts[user_id]:
        await message.answer(
            "🛒 Your cart is empty!",
            reply_markup=get_main_menu()
        )
        return

    text = "🛒 Your Cart\n\n"

    total = 0

    for item in carts[user_id]:
        text += f"🌭 {item['name']} — {item['price']} TL\n"
        total += item['price']

    text += f"\n💰 Total: {total} TL"

    await message.answer(text, reply_markup=cart_keyboard())

# =========================
# CLEAR CART
# =========================

@dp.message_handler(lambda message: message.text == "🗑 Clear Cart")
async def clear_cart(message: types.Message):

    carts[message.from_user.id] = []

    await message.answer(
        "🗑 Cart cleared.",
        reply_markup=get_main_menu()
    )

# =========================
# BACK
# =========================

@dp.message_handler(lambda message: message.text == "⬅️ Back")
async def back(message: types.Message):

    await message.answer(
        "⬅️ Returned to main menu",
        reply_markup=get_main_menu()
    )

# =========================
# CHECKOUT
# =========================

@dp.message_handler(lambda message: message.text == "✅ Checkout")
async def checkout(message: types.Message):

    waiting_phone.add(message.from_user.id)

    await message.answer(
        "📞 Send your phone number manually:\n\nExample:\n+905551112233"
    )

# =========================
# RECEIVE PHONE
# =========================

@dp.message_handler(lambda message: message.from_user.id in waiting_phone)
async def process_phone(message: types.Message):

    user_id = message.from_user.id

    phone = message.text.strip()

    if user_id not in carts or not carts[user_id]:
        await message.answer("🛒 Your cart is empty!")
        return

    cart_items = carts[user_id]

    total = 0
    cart_text = ""

    for item in cart_items:
        name = item["name"]
        price = item["price"]

        cart_text += f"• {name} — {price} TL\n"
        total += price

    full_name = message.from_user.full_name
    telegram_id = message.from_user.id
    username = message.from_user.username

    if username:
        username_text = f"@{username}"
        user_link = f"https://t.me/{username}"
    else:
        username_text = "No username"
        user_link = "No link"

    order_text = f"""
📦 NEW ORDER

{cart_text}

💰 Total: {total} TL
📞 Phone: {phone}

👤 Client: {full_name}
🆔 ID: {telegram_id}
🔗 Username: {username_text}
🌐 Link: {user_link}
"""

    # SEND TO OWNER
    await bot.send_message(OWNER_ID, order_text)

    await message.answer(
        "✅ Order sent successfully!\n\nVAMO Cafe will contact you soon.",
        reply_markup=get_main_menu()
    )

    carts[user_id] = []

    waiting_phone.remove(user_id)

# =========================
# RENDER WEB SERVER
# =========================

async def handle(request):
    return web.Response(text="VAMO Cafe Bot is running!")

async def start_webserver():
    app = web.Application()
    app.router.add_get('/', handle)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 10000))

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# =========================
# START BOT
# =========================

async def on_startup(dp):
    asyncio.create_task(start_webserver())
    print("VAMO Cafe Bot started")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)