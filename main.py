import os
import asyncio
import logging
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.utils import executor
import psycopg2
from psycopg2.extras import RealDictCursor

# =========================
# CONFIG
# =========================

TOKEN = "8729557900:AAGQceOGd-V5erYJpSXV5M95wrFU_JeMd4Q"
ADMIN_ID = 1472777680

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:froLOV580530@db.gtglvcebuvuampyhtaze.supabase.co:5432/postgres"
)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# =========================
# FLASK KEEP ALIVE
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "VAMO Cafe Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =========================
# DATABASE
# =========================

conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    username TEXT,
    full_name TEXT,
    items TEXT,
    total INTEGER,
    phone TEXT,
    address TEXT,
    complex_code TEXT,
    door_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# =========================
# MENU
# =========================

menu = {
    "🌭 Hot Dogs": {
        "Classic Hot Dog": 150,
        "Cheese Hot Dog": 180,
        "Double Hot Dog": 220,
    },
    "🌯 Shawarma": {
        "Chicken Shawarma": 200,
        "Big Shawarma": 260,
    },
    "🥟 Chebureki": {
        "Classic Chebureki": 140,
        "Cheese Chebureki": 160,
        "Meat Chebureki": 190,
    },
    "🥤 Drinks": {
        "Cola": 60,
        "Ayran": 50,
        "Water": 30,
    }
}

# =========================
# USER DATA
# =========================

user_cart = {}
waiting_phone = {}
waiting_address = {}
waiting_complex = {}
waiting_door = {}

# =========================
# KEYBOARDS
# =========================

def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    for category in menu.keys():
        kb.add(KeyboardButton(category))

    kb.add(KeyboardButton("🛒 Cart"))
    kb.add(KeyboardButton("🌐 Change Language"))

    return kb

def cart_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("✅ Checkout"))
    kb.add(KeyboardButton("⬅ Back"))
    return kb

# =========================
# START
# =========================

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_cart[message.from_user.id] = []

    text = (
        "🍔 Welcome to VAMO Cafe!\n\n"
        "Choose category:"
    )

    await message.answer(text, reply_markup=main_keyboard())

# =========================
# ADMIN PANEL
# =========================

@dp.message_handler(commands=["admin"])
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📦 Orders")
    kb.add("📊 Statistics")
    kb.add("⬅ Back")

    await message.answer("⚙ Admin Panel", reply_markup=kb)

# =========================
# ORDERS
# =========================

@dp.message_handler(lambda m: m.text == "📦 Orders")
async def show_orders(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    cur.execute("""
    SELECT * FROM orders
    ORDER BY id DESC
    LIMIT 10
    """)

    orders = cur.fetchall()

    if not orders:
        await message.answer("No orders yet.")
        return

    for order in orders:
        text = (
            f"📦 ORDER #{order[0]}\n\n"
            f"👤 {order[3]}\n"
            f"📱 {order[6]}\n"
            f"🏠 {order[7]}\n\n"
            f"{order[4]}\n\n"
            f"💰 {order[5]} TL"
        )

        await message.answer(text)

# =========================
# STATISTICS
# =========================

@dp.message_handler(lambda m: m.text == "📊 Statistics")
async def statistics(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    cur.execute("SELECT COUNT(*) FROM orders")
    total_orders = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(total),0) FROM orders")
    total_money = cur.fetchone()[0]

    text = (
        f"📊 Statistics\n\n"
        f"📦 Orders: {total_orders}\n"
        f"💰 Revenue: {total_money} TL"
    )

    await message.answer(text)

# =========================
# BACK
# =========================

@dp.message_handler(lambda m: m.text == "⬅ Back")
async def back(message: types.Message):
    await message.answer(
        "Returned to main menu",
        reply_markup=main_keyboard()
    )

# =========================
# CHANGE LANGUAGE
# =========================

@dp.message_handler(lambda m: m.text == "🌐 Change Language")
async def change_language(message: types.Message):
    await message.answer(
        "🌍 Language changed!\n\nChoose category:",
        reply_markup=main_keyboard()
    )

# =========================
# CATEGORY
# =========================

@dp.message_handler(lambda m: m.text in menu)
async def category_handler(message: types.Message):
    category = message.text

    text = f"{category} Menu\n\n"

    for item, price in menu[category].items():
        text += f"• {item} — {price} TL\n"

    text += "\nTap button again to add item."

    await message.answer(text)

# =========================
# ADD ITEM
# =========================

@dp.message_handler()
async def all_messages(message: types.Message):
    user_id = message.from_user.id
    text = message.text

    # ADD ITEM
    for category, items in menu.items():
        if text in items:
            if user_id not in user_cart:
                user_cart[user_id] = []

            user_cart[user_id].append((text, items[text]))

            await message.answer(
                f"✅ Added: {text}",
                reply_markup=main_keyboard()
            )
            return

    # CART
    if text == "🛒 Cart":
        cart = user_cart.get(user_id, [])

        if not cart:
            await message.answer("🛒 Your cart is empty!")
            return

        msg = "🛒 Your Cart\n\n"

        total = 0

        for item, price in cart:
            msg += f"• {item} — {price} TL\n"
            total += price

        msg += f"\n💰 Total: {total} TL"

        await message.answer(msg, reply_markup=cart_keyboard())
        return

    # CHECKOUT
    if text == "✅ Checkout":
        waiting_phone[user_id] = True

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("📱 Send phone number", request_contact=True))

        await message.answer(
            "📞 Send your phone number:\n\nExample:\n+905551112233",
            reply_markup=kb
        )
        return

    # PHONE
    if user_id in waiting_phone:
        phone = text

        if message.contact:
            phone = message.contact.phone_number

        waiting_phone.pop(user_id)

        waiting_address[user_id] = phone

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("📍 Send location", request_location=True))
        kb.add(KeyboardButton("⏭ Skip"))

        await message.answer(
            "📍 Send your address or location:",
            reply_markup=kb
        )
        return

    # ADDRESS
    if user_id in waiting_address:
        address = text

        if message.location:
            address = (
                f"https://maps.google.com/?q="
                f"{message.location.latitude},"
                f"{message.location.longitude}"
            )

        if text == "⏭ Skip":
            address = "Skip"

        phone = waiting_address[user_id]
        waiting_address.pop(user_id)

        waiting_complex[user_id] = {
            "phone": phone,
            "address": address
        }

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("⏭ Skip"))

        await message.answer(
            "🏢 Enter complex/building code:\n\n(optional)",
            reply_markup=kb
        )
        return

    # COMPLEX CODE
    if user_id in waiting_complex:
        complex_code = text

        if text == "⏭ Skip":
            complex_code = "Not provided"

        data = waiting_complex[user_id]
        waiting_complex.pop(user_id)

        waiting_door[user_id] = {
            "phone": data["phone"],
            "address": data["address"],
            "complex": complex_code
        }

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("⏭ Skip"))

        await message.answer(
            "🚪 Enter door code:\n\n(optional)",
            reply_markup=kb
        )
        return

    # DOOR CODE
    if user_id in waiting_door:
        door_code = text

        if text == "⏭ Skip":
            door_code = "Not provided"

        data = waiting_door[user_id]
        waiting_door.pop(user_id)

        cart = user_cart.get(user_id, [])

        total = sum(price for _, price in cart)

        order_text = ""

        for item, price in cart:
            order_text += f"• {item} — {price} TL\n"

        username = (
            f"@{message.from_user.username}"
            if message.from_user.username
            else "No username"
        )

        full_name = message.from_user.full_name

        # SAVE TO DATABASE
        cur.execute("""
        INSERT INTO orders (
            user_id,
            username,
            full_name,
            items,
            total,
            phone,
            address,
            complex_code,
            door_code
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            user_id,
            username,
            full_name,
            order_text,
            total,
            data["phone"],
            data["address"],
            data["complex"],
            door_code
        ))

        conn.commit()

        final_text = (
            f"📦 NEW ORDER\n\n"
            f"{order_text}\n"
            f"💰 Total: {total} TL\n"
            f"📞 Phone: {data['phone']}\n"
            f"🏠 Address: {data['address']}\n"
            f"🏢 Complex code: {data['complex']}\n"
            f"🚪 Door code: {door_code}\n\n"
            f"👤 Client: {full_name}\n"
            f"🆔 ID: {user_id}\n"
            f"🔗 Username: {username}"
        )

        await bot.send_message(ADMIN_ID, final_text)

        await message.answer(
            "✅ Order sent successfully!\n\n"
            "VAMO Cafe will contact you soon.",
            reply_markup=main_keyboard()
        )

        user_cart[user_id] = []

# =========================
# RUN
# =========================

if __name__ == "__main__":
    Thread(target=run_web).start()
    executor.start_polling(dp, skip_updates=True)
