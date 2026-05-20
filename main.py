# =========================================
# VAMO CAFE BOT
# FULL MAIN.PY
# =========================================

import logging
import asyncio
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

import psycopg2

from flask import Flask
from threading import Thread

# =========================================
# CONFIG
# =========================================

TOKEN = "8729557900:AAGQceOGd-V5erYJpSXV5M95wrFU_JeMd4Q"

ADMIN_ID = 5199302693

DATABASE_URL = "postgresql://postgres.gtglvcebuvuampyhtaze:froLOV580530.@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

# =========================================
# DB CONNECT
# =========================================

conn = psycopg2.connect(
    DATABASE_URL,
    sslmode="require"
)

cur = conn.cursor()

# =========================================
# CREATE TABLES
# =========================================

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    username TEXT,
    full_name TEXT,
    product_name TEXT,
    total INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    category TEXT,
    name TEXT,
    price INTEGER
)
""")

conn.commit()

# =========================================
# DEFAULT PRODUCTS
# =========================================

cur.execute("SELECT COUNT(*) FROM products")
count = cur.fetchone()[0]

if count == 0:

    products = [

        ("🌭 Hot Dogs", "Classic Hot Dog", 150),
        ("🌭 Hot Dogs", "Cheese Hot Dog", 180),
        ("🌭 Hot Dogs", "Double Hot Dog", 220),

        ("🌯 Shawarma", "Chicken Shawarma", 210),
        ("🌯 Shawarma", "Big Shawarma", 260),

        ("🥤 Drinks", "Cola", 60),
        ("🥤 Drinks", "Ayran", 50),

    ]

    for p in products:

        cur.execute("""
        INSERT INTO products(category,name,price)
        VALUES(%s,%s,%s)
        """, p)

    conn.commit()

# =========================================
# BOT
# =========================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)

dp = Dispatcher(bot)

# =========================================
# FLASK
# =========================================

app = Flask('')

@app.route('/')
def home():
    return "VAMO BOT WORKING"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# =========================================
# MEMORY
# =========================================

user_carts = {}

user_states = {}

# =========================================
# KEYBOARDS
# =========================================

def main_menu():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    cur.execute("""
    SELECT DISTINCT category
    FROM products
    ORDER BY category
    """)

    categories = cur.fetchall()

    for c in categories:

        kb.add(KeyboardButton(c[0]))

    kb.add(KeyboardButton("🛒 Cart"))

    return kb

def admin_menu():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("📦 Orders"))
    kb.add(KeyboardButton("📊 Statistics"))

    kb.add(KeyboardButton("➕ Add Product"))
    kb.add(KeyboardButton("❌ Delete Category"))

    kb.add(KeyboardButton("⬅ Back"))

    return kb

# =========================================
# START
# =========================================

@dp.message_handler(commands=["start"])
async def start(message: types.Message):

    await message.answer(
        "🍔 Welcome to VAMO Cafe",
        reply_markup=main_menu()
    )

# =========================================
# ADMIN
# =========================================

@dp.message_handler(commands=["admin"])
async def admin(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "⚙ ADMIN PANEL",
        reply_markup=admin_menu()
    )

# =========================================
# ORDERS
# =========================================

@dp.message_handler(lambda m: m.text == "📦 Orders")
async def orders(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    cur.execute("""
    SELECT id, full_name, total
    FROM orders
    ORDER BY id DESC
    LIMIT 10
    """)

    rows = cur.fetchall()

    if not rows:

        await message.answer("No orders")
        return

    text = "📦 LAST ORDERS\n\n"

    for row in rows:

        text += f"#{row[0]} | {row[1]} | {row[2]} TL\n"

    await message.answer(text)

# =========================================
# STATS
# =========================================

@dp.message_handler(lambda m: m.text == "📊 Statistics")
async def stats(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    cur.execute("SELECT COUNT(*) FROM orders")

    orders_count = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(total),0) FROM orders")

    income = cur.fetchone()[0]

    await message.answer(
        f"""
📊 Statistics

📦 Orders: {orders_count}

💰 Income: {income} TL
"""
    )

# =========================================
# ADD PRODUCT
# =========================================

@dp.message_handler(lambda m: m.text == "➕ Add Product")
async def add_product(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    cur.execute("""
    SELECT DISTINCT category
    FROM products
    ORDER BY category
    """)

    cats = cur.fetchall()

    text = "📂 Choose category:\n\n"

    for c in cats:
        text += f"{c[0]}\n"

    await message.answer(text)

    user_states[message.from_user.id] = {
        "step": "category"
    }

# =========================================
# DELETE CATEGORY
# =========================================

@dp.message_handler(lambda m: m.text == "❌ Delete Category")
async def delete_category(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    cur.execute("""
    SELECT DISTINCT category
    FROM products
    """)

    cats = cur.fetchall()

    text = "❌ Send category name to delete:\n\n"

    for c in cats:
        text += f"{c[0]}\n"

    await message.answer(text)

    user_states[message.from_user.id] = {
        "step": "delete_category"
    }

# =========================================
# CART
# =========================================

@dp.message_handler(lambda m: m.text == "🛒 Cart")
async def cart(message: types.Message):

    user_id = message.from_user.id

    cart_items = user_carts.get(user_id, [])

    if not cart_items:

        await message.answer(
            "🛒 Cart is empty"
        )

        return

    text = "🛒 YOUR CART\n\n"

    total = 0

    for item in cart_items:

        text += f"• {item}\n"

        try:
            price = int(
                item.split("—")[1]
                .replace("TL", "")
                .strip()
            )

            total += price

        except:
            pass

    text += f"\n💰 Total: {total} TL"

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("✅ Checkout"))
    kb.add(KeyboardButton("⬅ Back"))

    await message.answer(text, reply_markup=kb)

# =========================================
# CHECKOUT
# =========================================

@dp.message_handler(lambda m: m.text == "✅ Checkout")
async def checkout(message: types.Message):

    user_id = message.from_user.id

    cart_items = user_carts.get(user_id, [])

    if not cart_items:

        await message.answer(
            "🛒 Cart is empty",
            reply_markup=main_menu()
        )

        return

    total = 0

    for item in cart_items:

        try:

            price = int(
                item.split("—")[1]
                .replace("TL", "")
                .strip()
            )

            total += price

        except:
            pass

    products_text = "\n".join(cart_items)

    cur.execute("""
    INSERT INTO orders (
        user_id,
        username,
        full_name,
        product_name,
        total
    )
    VALUES (%s,%s,%s,%s,%s)
    """, (
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
        products_text,
        total
    ))

    conn.commit()

    user_carts[user_id] = []

    await message.answer(
        f"""
✅ ORDER CONFIRMED

📦 Products:
{products_text}

💰 Total: {total} TL

VAMO Cafe will contact you soon.
""",
        reply_markup=main_menu()
    )

    await bot.send_message(
        ADMIN_ID,
        f"""
🔥 NEW ORDER

👤 Client: {message.from_user.full_name}
🆔 ID: {message.from_user.id}

📦 Order:
{products_text}

💰 Total: {total} TL
"""
    )

# =========================================
# UNIVERSAL
# =========================================

@dp.message_handler()
async def universal(message: types.Message):

    user_id = message.from_user.id

    text = message.text

    # =========================
    # BACK
    # =========================

    if text == "⬅ Back":

        await message.answer(
            "⬅ Main menu",
            reply_markup=main_menu()
        )

        return

    # =========================
    # ADMIN STATES
    # =========================

    if user_id in user_states:

        state = user_states[user_id]

        # ADD PRODUCT

        if state["step"] == "category":

            state["category"] = text

            state["step"] = "name"

            await message.answer("🍔 Enter product name")

            return

        elif state["step"] == "name":

            state["name"] = text

            state["step"] = "price"

            await message.answer("💰 Enter price")

            return

        elif state["step"] == "price":

            try:

                price = int(text)

            except:

                await message.answer("Enter number")
                return

            cur.execute("""
            INSERT INTO products(category,name,price)
            VALUES(%s,%s,%s)
            """, (
                state["category"],
                state["name"],
                price
            ))

            conn.commit()

            del user_states[user_id]

            await message.answer(
                "✅ Product added",
                reply_markup=admin_menu()
            )

            return

        # DELETE CATEGORY

        elif state["step"] == "delete_category":

            cur.execute("""
            DELETE FROM products
            WHERE category=%s
            """, (text,))

            conn.commit()

            del user_states[user_id]

            await message.answer(
                "✅ Category deleted",
                reply_markup=admin_menu()
            )

            return

    # =========================
    # CATEGORY CLICK
    # =========================

    cur.execute("""
    SELECT name, price
    FROM products
    WHERE category=%s
    """, (text,))

    rows = cur.fetchall()

    if rows:

        kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for row in rows:

            product_text = f"{row[0]} — {row[1]} TL"

            kb.add(KeyboardButton(product_text))

        kb.add(KeyboardButton("⬅ Back"))

        menu_text = f"{text}\n\n"

        for row in rows:

            menu_text += f"• {row[0]} — {row[1]} TL\n"

        await message.answer(
            menu_text,
            reply_markup=kb
        )

        return

    # =========================
    # PRODUCT CLICK
    # =========================

    cur.execute("""
    SELECT name, price
    FROM products
    """)

    all_products = cur.fetchall()

    for product in all_products:

        btn = f"{product[0]} — {product[1]} TL"

        if text == btn:

            if user_id not in user_carts:
                user_carts[user_id] = []

            user_carts[user_id].append(btn)

            kb = ReplyKeyboardMarkup(resize_keyboard=True)

            kb.add(KeyboardButton("🛒 Cart"))
            kb.add(KeyboardButton("⬅ Back"))

            await message.answer(
                f"✅ Added to cart:\n{btn}",
                reply_markup=kb
            )

            return

# =========================================
# RUN
# =========================================

async def on_startup(dp):

    print("BOT STARTED")

if __name__ == "__main__":

    keep_alive()

    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup
    )
