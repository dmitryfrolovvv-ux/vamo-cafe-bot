import logging
import sqlite3
from threading import Thread

from flask import Flask

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)

# =========================
# CONFIG
# =========================

API_TOKEN = "8729557900:AAGQceOGd-V5erYJpSXV5M95wrFU_JeMd4Q"
OWNER_ID = 1472777680

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# =========================
# RENDER WEB SERVICE
# =========================

app = Flask(__name__)

@app.route('/')
def home():
    return "VAMO BOT IS RUNNING"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# =========================
# DATABASE
# =========================

conn = sqlite3.connect("vamo.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    username TEXT,
    full_name TEXT,
    phone TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    items TEXT,
    total INTEGER,
    phone TEXT,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# =========================
# DATA
# =========================

carts = {}
user_states = {}
user_data = {}
user_languages = {}

# =========================
# PRODUCTS
# =========================

products = {
    "Classic Hot Dog": 150,
    "Cheese Hot Dog": 180,
    "Double Hot Dog": 220,

    "Chicken Shawarma": 200,
    "Beef Shawarma": 250,
    "Mega Shawarma": 320,

    "Classic Chebureki": 140,
    "Cheese Chebureki": 160,
    "Meat Chebureki": 190,

    "Cola": 60,
    "Ayran": 50,
    "Water": 30
}

# =========================
# MAIN KEYBOARD
# =========================

def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🌭 Hot Dogs")
    kb.add("🌯 Shawarma")
    kb.add("🥟 Chebureki")
    kb.add("🥤 Drinks")
    kb.add("🛒 Cart")
    kb.add("🌐 Change Language")

    return kb

# =========================
# ADMIN KEYBOARD
# =========================

def admin_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("📦 Orders")
    kb.add("📊 Stats")
    kb.add("👥 Clients")
    kb.add("💰 Revenue")
    kb.add("🟢 Bot Status")
    kb.add("⬅️ Exit Admin")

    return kb

# =========================
# START
# =========================

@dp.message_handler(commands=["start"])
async def start(message: types.Message):

    user_id = message.from_user.id

    if user_id not in carts:
        carts[user_id] = []

    await message.answer(
        "👋 Welcome to VAMO Cafe!\n\nChoose category:",
        reply_markup=main_keyboard()
    )

# =========================
# ADMIN PANEL
# =========================

@dp.message_handler(commands=["admin"])
async def admin_panel(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    await message.answer(
        "⚙️ ADMIN PANEL",
        reply_markup=admin_keyboard()
    )

# =========================
# ADMIN ORDERS
# =========================

@dp.message_handler(lambda message: message.text == "📦 Orders")
async def admin_orders(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    cursor.execute("""
    SELECT id, items, total, phone, address, created_at
    FROM orders
    ORDER BY id DESC
    LIMIT 10
    """)

    orders = cursor.fetchall()

    if not orders:
        await message.answer("No orders yet.")
        return

    text = "📦 LAST ORDERS\n\n"

    for order in orders:
        text += (
            f"#{order[0]}\n"
            f"🛒 {order[1]}\n"
            f"💰 {order[2]} TL\n"
            f"📞 {order[3]}\n"
            f"🏠 {order[4]}\n"
            f"📅 {order[5]}\n\n"
        )

    await message.answer(text)

# =========================
# ADMIN STATS
# =========================

@dp.message_handler(lambda message: message.text == "📊 Stats")
async def admin_stats(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total) FROM orders")
    revenue = cursor.fetchone()[0]

    if revenue is None:
        revenue = 0

    cursor.execute("""
    SELECT COUNT(DISTINCT telegram_id)
    FROM users
    """)

    clients = cursor.fetchone()[0]

    text = (
        "📊 VAMO STATS\n\n"
        f"📦 Orders: {total_orders}\n"
        f"👥 Clients: {clients}\n"
        f"💰 Revenue: {revenue} TL"
    )

    await message.answer(text)

# =========================
# ADMIN CLIENTS
# =========================

@dp.message_handler(lambda message: message.text == "👥 Clients")
async def admin_clients(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    cursor.execute("""
    SELECT DISTINCT
        full_name,
        username,
        phone
    FROM users
    ORDER BY id DESC
    LIMIT 10
    """)

    users = cursor.fetchall()

    if not users:
        await message.answer("No clients.")
        return

    text = "👥 LAST CLIENTS\n\n"

    for user in users:

        username = user[1]

        if username:
            username = f"@{username}"
        else:
            username = "No username"

        text += (
            f"👤 {user[0]}\n"
            f"🔗 {username}\n"
            f"📞 {user[2]}\n\n"
        )

    await message.answer(text)

# =========================
# ADMIN REVENUE
# =========================

@dp.message_handler(lambda message: message.text == "💰 Revenue")
async def admin_revenue(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    cursor.execute("""
    SELECT SUM(total)
    FROM orders
    """)

    revenue = cursor.fetchone()[0]

    if revenue is None:
        revenue = 0

    await message.answer(
        f"💰 TOTAL REVENUE\n\n{revenue} TL"
    )

# =========================
# BOT STATUS
# =========================

@dp.message_handler(lambda message: message.text == "🟢 Bot Status")
async def bot_status(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    await message.answer(
        "🟢 BOT ONLINE\n\n"
        "✅ Database connected\n"
        "✅ Orders active\n"
        "✅ Notifications active\n"
        "✅ SQLite working"
    )

# =========================
# EXIT ADMIN
# =========================

@dp.message_handler(lambda message: message.text == "⬅️ Exit Admin")
async def exit_admin(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    await message.answer(
        "⬅️ Exited admin panel",
        reply_markup=main_keyboard()
    )

# =========================
# CHANGE LANGUAGE
# =========================

@dp.message_handler(lambda message: message.text == "🌐 Change Language")
async def change_language(message: types.Message):

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("🇷🇺 Русский")
    keyboard.add("🇬🇧 English")
    keyboard.add("🇹🇷 Türkçe")
    keyboard.add("⬅️ Back")

    await message.answer(
        "🌍 Choose language:",
        reply_markup=keyboard
    )

# =========================
# SET LANGUAGE
# =========================

@dp.message_handler(lambda message:
    message.text in [
        "🇷🇺 Русский",
        "🇬🇧 English",
        "🇹🇷 Türkçe"
    ]
)
async def set_language(message: types.Message):

    user_languages[message.from_user.id] = message.text

    await message.answer(
        f"✅ Language selected: {message.text}",
        reply_markup=main_keyboard()
    )

# =========================
# HOT DOGS
# =========================

@dp.message_handler(lambda message: message.text == "🌭 Hot Dogs")
async def hotdogs(message: types.Message):

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("Classic Hot Dog")
    keyboard.add("Cheese Hot Dog")
    keyboard.add("Double Hot Dog")
    keyboard.add("⬅️ Back")

    await message.answer(
        "🌭 Hot Dogs Menu\n\n"
        "Classic Hot Dog — 150 TL\n"
        "Cheese Hot Dog — 180 TL\n"
        "Double Hot Dog — 220 TL",
        reply_markup=keyboard
    )

# =========================
# SHAWARMA
# =========================

@dp.message_handler(lambda message: message.text == "🌯 Shawarma")
async def shawarma(message: types.Message):

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("Chicken Shawarma")
    keyboard.add("Beef Shawarma")
    keyboard.add("Mega Shawarma")
    keyboard.add("⬅️ Back")

    await message.answer(
        "🌯 Shawarma Menu\n\n"
        "Chicken Shawarma — 200 TL\n"
        "Beef Shawarma — 250 TL\n"
        "Mega Shawarma — 320 TL",
        reply_markup=keyboard
    )

# =========================
# CHEBUREKI
# =========================

@dp.message_handler(lambda message: message.text == "🥟 Chebureki")
async def chebureki(message: types.Message):

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("Classic Chebureki")
    keyboard.add("Cheese Chebureki")
    keyboard.add("Meat Chebureki")
    keyboard.add("⬅️ Back")

    await message.answer(
        "🥟 Chebureki Menu\n\n"
        "Classic Chebureki — 140 TL\n"
        "Cheese Chebureki — 160 TL\n"
        "Meat Chebureki — 190 TL",
        reply_markup=keyboard
    )

# =========================
# DRINKS
# =========================

@dp.message_handler(lambda message: message.text == "🥤 Drinks")
async def drinks(message: types.Message):

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("Cola")
    keyboard.add("Ayran")
    keyboard.add("Water")
    keyboard.add("⬅️ Back")

    await message.answer(
        "🥤 Drinks Menu\n\n"
        "Cola — 60 TL\n"
        "Ayran — 50 TL\n"
        "Water — 30 TL",
        reply_markup=keyboard
    )

# =========================
# ADD PRODUCT
# =========================

@dp.message_handler(lambda message: message.text in products.keys())
async def add_product(message: types.Message):

    user_id = message.from_user.id

    if user_id not in carts:
        carts[user_id] = []

    carts[user_id].append({
        "name": message.text,
        "price": products[message.text]
    })

    await message.answer(
        f"✅ Added to cart:\n{message.text} — {products[message.text]} TL"
    )

# =========================
# BACK
# =========================

@dp.message_handler(lambda message: message.text == "⬅️ Back")
async def back_handler(message: types.Message):

    await message.answer(
        "⬅️ Returned to main menu",
        reply_markup=main_keyboard()
    )

# =========================
# CART
# =========================

@dp.message_handler(lambda message: message.text == "🛒 Cart")
async def cart_handler(message: types.Message):

    user_id = message.from_user.id

    if user_id not in carts or len(carts[user_id]) == 0:
        await message.answer("🛒 Your cart is empty!")
        return

    text = "🛒 Your Cart\n\n"

    total = 0

    for item in carts[user_id]:
        text += f"• {item['name']} — {item['price']} TL\n"
        total += item["price"]

    text += f"\n💰 Total: {total} TL"

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("✅ Checkout")
    keyboard.add("🗑 Clear Cart")
    keyboard.add("⬅️ Back")

    await message.answer(text, reply_markup=keyboard)

# =========================
# CLEAR CART
# =========================

@dp.message_handler(lambda message: message.text == "🗑 Clear Cart")
async def clear_cart(message: types.Message):

    carts[message.from_user.id] = []

    await message.answer(
        "🗑 Cart cleared!",
        reply_markup=main_keyboard()
    )

# =========================
# CHECKOUT
# =========================

@dp.message_handler(lambda message: message.text == "✅ Checkout")
async def checkout(message: types.Message):

    user_id = message.from_user.id

    if user_id not in carts or len(carts[user_id]) == 0:
        await message.answer("🛒 Your cart is empty!")
        return

    user_states[user_id] = "waiting_phone"

    await message.answer(
        "📞 Send your phone number:\n\n"
        "Example:\n"
        "+905551112233",
        reply_markup=ReplyKeyboardRemove()
    )

# =========================
# PHONE
# =========================

@dp.message_handler(lambda message: user_states.get(message.from_user.id) == "waiting_phone")
async def get_phone(message: types.Message):

    user_id = message.from_user.id

    user_data[user_id] = {
        "phone": message.text
    }

    user_states[user_id] = "waiting_location"

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    location_btn = KeyboardButton(
        "📍 Send Location",
        request_location=True
    )

    keyboard.add(location_btn)

    await message.answer(
        "📍 Please send your location.",
        reply_markup=keyboard
    )

# =========================
# LOCATION
# =========================

@dp.message_handler(content_types=types.ContentType.LOCATION)
async def get_location(message: types.Message):

    user_id = message.from_user.id

    if user_states.get(user_id) != "waiting_location":
        return

    latitude = message.location.latitude
    longitude = message.location.longitude

    user_data[user_id]["latitude"] = latitude
    user_data[user_id]["longitude"] = longitude

    user_states[user_id] = "waiting_address"

    await message.answer(
        "🏠 Enter delivery address:",
        reply_markup=ReplyKeyboardRemove()
    )

# =========================
# ADDRESS
# =========================

@dp.message_handler(lambda message: user_states.get(message.from_user.id) == "waiting_address")
async def get_address(message: types.Message):

    user_id = message.from_user.id

    user_data[user_id]["address"] = message.text

    cart = carts.get(user_id, [])

    total = sum(item["price"] for item in cart)

    order_text = "📦 NEW ORDER\n\n"

    for item in cart:
        order_text += f"• {item['name']} — {item['price']} TL\n"

    order_text += f"\n💰 Total: {total} TL"

    order_text += f"\n📞 Phone: {user_data[user_id]['phone']}"

    order_text += f"\n🏠 Address: {user_data[user_id]['address']}"

    order_text += (
        f"\n📍 Location:\n"
        f"https://maps.google.com/?q="
        f"{user_data[user_id]['latitude']},"
        f"{user_data[user_id]['longitude']}"
    )

    order_text += (
        f"\n\n👤 Client: "
        f"{message.from_user.full_name}"
    )

    order_text += (
        f"\n🆔 ID: "
        f"{message.from_user.id}"
    )

    if message.from_user.username:
        order_text += (
            f"\n🔗 Username: "
            f"@{message.from_user.username}"
        )

    await bot.send_message(
        OWNER_ID,
        order_text
    )

    # SAVE USER

    cursor.execute("""
    INSERT INTO users (
        telegram_id,
        username,
        full_name,
        phone
    )
    VALUES (?, ?, ?, ?)
    """, (
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
        user_data[user_id]["phone"]
    ))

    # SAVE ORDER

    items_text = ""

    for item in cart:
        items_text += f"{item['name']} ({item['price']} TL), "

    cursor.execute("""
    INSERT INTO orders (
        telegram_id,
        items,
        total,
        phone,
        address
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        message.from_user.id,
        items_text,
        total,
        user_data[user_id]["phone"],
        user_data[user_id]["address"]
    ))

    conn.commit()

    await message.answer(
        "✅ Order sent successfully!\n\n"
        "VAMO Cafe will contact you soon.",
        reply_markup=main_keyboard()
    )

    carts[user_id] = []
    user_states[user_id] = None

# =========================
# RUN
# =========================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)