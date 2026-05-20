import os
import logging
import psycopg2

from flask import Flask
from threading import Thread

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup

# =========================
# CONFIG
# =========================

BOT_TOKEN = "8729557900:AAGQceOGd-V5erYJpSXV5M95wrFU_JeMd4Q"
ADMIN_ID = 5199302693

DATABASE_URL = "postgresql://postgres.gtglvcebuvuampyhtaze:froLOV580530.@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

logging.basicConfig(level=logging.INFO)

# =========================
# FLASK
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =========================
# BOT
# =========================

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# =========================
# CARTS
# =========================

user_carts = {}

# =========================
# DATABASE
# =========================

conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cur = conn.cursor()

def create_tables():
    cur.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE
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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        username TEXT,
        full_name TEXT,
        product_name TEXT,
        total INTEGER
    )
    """)

    conn.commit()

create_tables()

# =========================
# DEFAULT CATEGORIES
# =========================

def create_default_categories():
    categories = [
        "🌭 Hot Dogs",
        "🌯 Shawarma",
        "🥤 Drinks"
    ]

    for cat in categories:
        cur.execute("""
        INSERT INTO categories (name)
        VALUES (%s)
        ON CONFLICT DO NOTHING
        """, (cat,))

    conn.commit()

create_default_categories()

# =========================
# STATES
# =========================

class AdminStates(StatesGroup):
    add_category = State()

    add_product_category = State()
    add_product_name = State()
    add_product_price = State()

# =========================
# HELPERS
# =========================

def get_categories():
    cur.execute("""
    SELECT name
    FROM categories
    ORDER BY id
    """)

    rows = cur.fetchall()

    return [r[0] for r in rows]

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    categories = get_categories()

    for cat in categories:
        kb.add(cat)

    kb.add("🛒 Cart")

    return kb

# =========================
# START
# =========================

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "🍴 Welcome to VAMO Cafe",
        reply_markup=main_menu()
    )

# =========================
# SHOW PRODUCTS
# =========================

@dp.message_handler(lambda m: m.text in get_categories())
async def show_products(message: types.Message):
    category = message.text

    cur.execute("""
    SELECT id, name, price
    FROM products
    WHERE category=%s
    """, (category,))

    products = cur.fetchall()

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    text = f"{category}\n\n"

    if not products:
        text += "No products"

    for p in products:
        product_button = f"{p[1]} — {p[2]} TL"

        kb.add(product_button)

        text += f"• {product_button}\n"

    kb.add("⬅️ Back")

    await message.answer(
        text,
        reply_markup=kb
    )

# =========================
# ADD TO CART
# =========================

@dp.message_handler(lambda m: "—" in m.text and "TL" in m.text)
async def add_to_cart(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_carts:
        user_carts[user_id] = []

    product = message.text

    user_carts[user_id].append(product)

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("✅ Checkout")
    kb.add("🗑 Clear Cart")
    kb.add("⬅️ Back")

    await message.answer(
        f"✅ Added to cart:\n{product}",
        reply_markup=kb
    )

# =========================
# CART
# =========================

@dp.message_handler(lambda m: m.text == "🛒 Cart")
async def cart(message: types.Message):
    user_id = message.from_user.id

    cart_items = user_carts.get(user_id, [])

    if not cart_items:
        await message.answer(
            "🛒 Cart is empty",
            reply_markup=main_menu()
        )
        return

    text = "🛒 YOUR CART\n\n"

    total = 0

    for item in cart_items:
        text += f"• {item}\n"

        try:
            price = int(item.split("—")[1].replace("TL", "").strip())
            total += price
        except:
            pass

    text += f"\n💰 Total: {total} TL"

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("✅ Checkout")
    kb.add("🗑 Clear Cart")
    kb.add("⬅️ Back")

    await message.answer(
        text,
        reply_markup=kb
    )

# =========================
# CLEAR CART
# =========================

@dp.message_handler(lambda m: m.text == "🗑 Clear Cart")
async def clear_cart(message: types.Message):
    user_id = message.from_user.id

    user_carts[user_id] = []

    await message.answer(
        "🗑 Cart cleared",
        reply_markup=main_menu()
    )

# =========================
# CHECKOUT
# =========================

@dp.message_handler(lambda m: m.text == "✅ Checkout")
async def checkout(message: types.Message):
    user_id = message.from_user.id

    cart_items = user_carts.get(user_id, [])

    if not cart_items:
        await message.answer("🛒 Cart is empty")
        return

    total = 0

    for item in cart_items:
        try:
            price = int(item.split("—")[1].replace("TL", "").strip())
            total += price
        except:
            pass

    products_text = ", ".join(cart_items)

    cur.execute("""
    INSERT INTO orders (
        user_id,
        username,
        full_name,
        product_name,
        total
    )
    VALUES (%s, %s, %s, %s, %s)
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
        "✅ Order placed successfully!",
        reply_markup=main_menu()
    )

    await bot.send_message(
        ADMIN_ID,
        f"""
🔥 NEW ORDER

👤 {message.from_user.full_name}
📦 {products_text}

💰 Total: {total} TL
"""
    )

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

    kb.add("📂 Categories")

    kb.add("➕ Add Product")
    kb.add("❌ Delete Category")

    kb.add("⬅️ Back")

    await message.answer(
        "⚙️ ADMIN PANEL",
        reply_markup=kb
    )

# =========================
# ADD CATEGORY
# =========================

@dp.message_handler(lambda m: m.text == "📂 Categories")
async def categories_menu(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("➕ Add Category")
    kb.add("⬅️ Back")

    await message.answer(
        "📂 Categories",
        reply_markup=kb
    )

@dp.message_handler(lambda m: m.text == "➕ Add Category")
async def add_category_start(message: types.Message):
    await AdminStates.add_category.set()

    await message.answer(
        "📂 Enter category name"
    )

@dp.message_handler(state=AdminStates.add_category)
async def add_category_finish(message: types.Message, state: FSMContext):
    category = message.text

    cur.execute("""
    INSERT INTO categories (name)
    VALUES (%s)
    ON CONFLICT DO NOTHING
    """, (category,))

    conn.commit()

    await message.answer(
        "✅ Category added",
        reply_markup=main_menu()
    )

    await state.finish()

# =========================
# DELETE CATEGORY
# =========================

@dp.message_handler(lambda m: m.text == "❌ Delete Category")
async def delete_category(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    categories = get_categories()

    for cat in categories:
        kb.add(cat)

    kb.add("⬅️ Back")

    await message.answer(
        "❌ Select category to delete",
        reply_markup=kb
    )

@dp.message_handler(lambda m: m.text in get_categories())
async def delete_category_confirm(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

# =========================
# ADD PRODUCT
# =========================

@dp.message_handler(lambda m: m.text == "➕ Add Product")
async def add_product_start(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    categories = get_categories()

    for cat in categories:
        kb.add(cat)

    kb.add("⬅️ Back")

    await AdminStates.add_product_category.set()

    await message.answer(
        "📂 Select category",
        reply_markup=kb
    )

@dp.message_handler(state=AdminStates.add_product_category)
async def add_product_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)

    await AdminStates.add_product_name.set()

    await message.answer(
        "🍔 Enter product name"
    )

@dp.message_handler(state=AdminStates.add_product_name)
async def add_product_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)

    await AdminStates.add_product_price.set()

    await message.answer(
        "💰 Enter price"
    )

@dp.message_handler(state=AdminStates.add_product_price)
async def add_product_price(message: types.Message, state: FSMContext):
    data = await state.get_data()

    category = data["category"]
    name = data["name"]

    try:
        price = int(message.text)
    except:
        await message.answer("Enter number")
        return

    cur.execute("""
    INSERT INTO products (category, name, price)
    VALUES (%s, %s, %s)
    """, (category, name, price))

    conn.commit()

    await message.answer(
        "✅ Product added",
        reply_markup=main_menu()
    )

    await state.finish()

# =========================
# ORDERS
# =========================

@dp.message_handler(lambda m: m.text == "📦 Orders")
async def orders(message: types.Message):
    cur.execute("""
    SELECT id, full_name, total
    FROM orders
    ORDER BY id DESC
    LIMIT 10
    """)

    rows = cur.fetchall()

    text = "📦 LAST ORDERS\n\n"

    if not rows:
        text += "No orders"

    for r in rows:
        text += f"#{r[0]} | {r[1]} | {r[2]} TL\n"

    await message.answer(text)

# =========================
# STATS
# =========================

@dp.message_handler(lambda m: m.text == "📊 Statistics")
async def stats(message: types.Message):
    cur.execute("SELECT COUNT(*) FROM orders")
    total_orders = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(total),0) FROM orders")
    income = cur.fetchone()[0]

    text = f"""
📊 Statistics

📦 Orders: {total_orders}
💰 Income: {income} TL
"""

    await message.answer(text)

# =========================
# BACK
# =========================

@dp.message_handler(lambda m: m.text == "⬅️ Back")
async def back(message: types.Message, state: FSMContext):
    await state.finish()

    await message.answer(
        "⬅️ Main menu",
        reply_markup=main_menu()
    )

# =========================
# MAIN
# =========================

async def on_startup(dp):
    print("Bot started")

if __name__ == "__main__":
    Thread(target=run_web).start()

    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup
    )
