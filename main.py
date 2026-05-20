import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.utils import executor

# =========================
# CONFIG
# =========================

API_TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = 1472777680

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# =========================
# CART STORAGE
# =========================

carts = {}

# =========================
# MENU
# =========================

menu = {
    "Hot Dogs": [
        {"name": "Classic Hot Dog", "price": 150},
        {"name": "Cheese Hot Dog", "price": 180},
        {"name": "Double Hot Dog", "price": 220},
    ],
    "Shawarma": [
        {"name": "Chicken Shawarma", "price": 200},
        {"name": "Beef Shawarma", "price": 250},
        {"name": "Mega Shawarma", "price": 320},
    ],
    "Chebureki": [
        {"name": "Classic Cheburek", "price": 170},
        {"name": "Cheese Cheburek", "price": 190},
    ],
    "Drinks": [
        {"name": "Cola", "price": 60},
        {"name": "Ayran", "price": 50},
        {"name": "Water", "price": 30},
    ]
}

# =========================
# MAIN MENU
# =========================

def get_main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("🌭 Hot Dogs"))
    kb.add(KeyboardButton("🌯 Shawarma"))
    kb.add(KeyboardButton("🥟 Chebureki"))
    kb.add(KeyboardButton("🥤 Drinks"))
    kb.add(KeyboardButton("🛒 Cart"))
    kb.add(KeyboardButton("🌐 Change Language"))

    return kb

# =========================
# START
# =========================

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("🇷🇺 Русский"))
    kb.add(KeyboardButton("🇹🇷 Türkçe"))
    kb.add(KeyboardButton("🇬🇧 English"))
    kb.add(KeyboardButton("🇩🇪 Deutsch"))

    await message.answer(
        "👋 Welcome to VAMO Cafe!\n\nChoose language:",
        reply_markup=kb
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
async def choose_language(message: types.Message):

    await message.answer(
        "✅ Language selected!\n\nChoose category:",
        reply_markup=get_main_menu()
    )

# =========================
# CATEGORY MENU
# =========================

@dp.message_handler(lambda message: message.text in [
    "🌭 Hot Dogs",
    "🌯 Shawarma",
    "🥟 Chebureki",
    "🥤 Drinks"
])
async def show_category(message: types.Message):

    category = message.text.replace("🌭 ", "").replace("🌯 ", "").replace("🥟 ", "").replace("🥤 ", "")

    items = menu.get(category, [])

    text = f"{message.text} Menu\n\n"

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    for item in items:
        text += f"{item['name']} — {item['price']} TL\n"

        kb.add(
            KeyboardButton(
                f"➕ {item['name']} ({item['price']} TL)"
            )
        )

    kb.add(KeyboardButton("⬅️ Back"))

    await message.answer(text, reply_markup=kb)

# =========================
# ADD TO CART
# =========================

@dp.message_handler(lambda message: message.text.startswith("➕"))
async def add_to_cart(message: types.Message):

    user_id = message.from_user.id

    if user_id not in carts:
        carts[user_id] = []

    text = message.text

    for category in menu.values():
        for item in category:

            button_text = f"➕ {item['name']} ({item['price']} TL)"

            if text == button_text:
                carts[user_id].append(item)

                await message.answer(
                    f"✅ Added to cart:\n\n{item['name']} — {item['price']} TL"
                )
                return

# =========================
# VIEW CART
# =========================

@dp.message_handler(lambda message: message.text == "🛒 Cart")
async def show_cart(message: types.Message):

    user_id = message.from_user.id

    if user_id not in carts or not carts[user_id]:
        await message.answer("🛒 Your cart is empty!")
        return

    total = 0
    text = "🛒 Your Cart\n\n"

    for item in carts[user_id]:
        text += f"🌭 {item['name']} — {item['price']} TL\n"
        total += item['price']

    text += f"\n💰 Total: {total} TL"

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("✅ Checkout"))
    kb.add(KeyboardButton("🗑 Clear Cart"))
    kb.add(KeyboardButton("⬅️ Back"))

    await message.answer(text, reply_markup=kb)

# =========================
# CLEAR CART
# =========================

@dp.message_handler(lambda message: message.text == "🗑 Clear Cart")
async def clear_cart(message: types.Message):

    user_id = message.from_user.id

    carts[user_id] = []

    await message.answer(
        "🗑 Cart cleared.",
        reply_markup=get_main_menu()
    )

# =========================
# BACK BUTTON
# =========================

@dp.message_handler(lambda message: message.text == "⬅️ Back")
async def back_to_main(message: types.Message):

    await message.answer(
        "⬅️ Returned to main menu",
        reply_markup=get_main_menu()
    )

# =========================
# CHECKOUT
# =========================

@dp.message_handler(lambda message: message.text == "✅ Checkout")
async def checkout(message: types.Message):

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    contact_btn = KeyboardButton(
        "📞 Send phone number",
        request_contact=True
    )

    kb.add(contact_btn)

    await message.answer(
        "📞 Send your phone number:",
        reply_markup=kb
    )

# =========================
# RECEIVE CONTACT
# =========================

@dp.message_handler(content_types=['contact'])
async def process_contact(message: types.Message):

    user_id = message.from_user.id

    if user_id not in carts or not carts[user_id]:
        await message.answer("🛒 Your cart is empty!")
        return

    phone = message.contact.phone_number

    cart_items = carts[user_id]

    total = 0
    cart_text = ""

    for item in cart_items:
        name = item["name"]
        price = item["price"]

        cart_text += f"• {name} — {price} TL\n"
        total += price

    username = message.from_user.username

    if username:
        username_text = f"@{username}"
    else:
        username_text = "No username"

    order_text = f"""
📦 NEW ORDER

{cart_text}

💰 Total: {total} TL
📞 Phone: {phone}
👤 User: {username_text}
"""

    # SEND ORDER TO OWNER
    await bot.send_message(OWNER_ID, order_text)

    # CLIENT RESPONSE
    await message.answer(
        "✅ Order sent successfully!\n\nVAMO Cafe will contact you soon.",
        reply_markup=get_main_menu()
    )

    # CLEAR CART
    carts[user_id] = []

# =========================
# KEEP RENDER ALIVE
# =========================

async def healthcheck(request):
    return web.Response(text="Bot is running!")

async def on_startup(dp):
    app = web.Application()
    app.router.add_get('/', healthcheck)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 10000))

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"✅ Web server started on port {port}")

# =========================
# RUN
# =========================

if __name__ == "__main__":
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup
    )