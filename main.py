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

# =========================================
# CONFIG
# =========================================

TOKEN = "8729557900:AAGQceOGd-V5erYJpSXV5M95wrFU_JeMd4Q"

ADMIN_ID = 1472777680

DATABASE_URL = "postgresql://postgres.gtglvcebuvuampyhtaze:froLOV580530.@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

logging.basicConfig(level=logging.INFO)

# =========================================
# FLASK
# =========================================

app = Flask(__name__)

@app.route("/")
def home():
    return "VAMO BOT WORKING"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =========================================
# BOT
# =========================================

storage = MemoryStorage()

bot = Bot(token=TOKEN)

dp = Dispatcher(bot, storage=storage)

# =========================================
# DATABASE
# =========================================

conn = psycopg2.connect(
    DATABASE_URL,
    sslmode="require"
)

cur = conn.cursor()

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

# =========================================
# MENU
# =========================================

menu_data = {
    "🌭 Hot Dogs": [
        ("Classic Hot Dog", 150),
        ("Cheese Hot Dog", 180),
        ("Double Hot Dog", 220)
    ],

    "🌯 Shawarma": [
        ("Chicken Shawarma", 220),
        ("Big Shawarma", 260)
    ],

    "🥤 Drinks": [
        ("Cola", 60),
        ("Ayran", 50)
    ]
}

# =========================================
# CARTS
# =========================================

user_carts = {}

# =========================================
# STATES
# =========================================

class AddProduct(StatesGroup):
    category = State()
    product_name = State()
    product_price = State()

class DeleteCategory(StatesGroup):
    waiting = State()

# =========================================
# KEYBOARDS
# =========================================

def main_menu():

    kb = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    for category in menu_data.keys():
        kb.add(category)

    kb.add("🛒 Cart")

    return kb

def category_keyboard(category):

    kb = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    for name, price in menu_data[category]:
        kb.add(f"{name} — {price} TL")

    kb.add("⬅️ Back")

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
# OPEN CATEGORY
# =========================================

@dp.message_handler(lambda m: m.text in menu_data)
async def open_category(message: types.Message):

    category = message.text

    text = f"{category}\n\n"

    for name, price in menu_data[category]:
        text += f"• {name} — {price} TL\n"

    await message.answer(
        text,
        reply_markup=category_keyboard(category)
    )

# =========================================
# CART
# =========================================

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

    total = 0

    text = "🛒 YOUR CART\n\n"

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

    kb = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.add("Checkout")
    kb.add("⬅️ Back")

    await message.answer(
        text,
        reply_markup=kb
    )

# =========================================
# ADMIN PANEL
# =========================================

@dp.message_handler(commands=["admin"])
@dp.message_handler(lambda m: m.text.lower() in ["admins", "/admins"])
async def admin_panel(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    kb = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

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

# =========================================
# ORDERS
# =========================================

@dp.message_handler(lambda m: m.text == "📦 Orders")
async def orders(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    cur.execute("""
    SELECT full_name, total
    FROM orders
    ORDER BY id DESC
    LIMIT 10
    """)

    rows = cur.fetchall()

    if not rows:

        await message.answer(
            "No orders"
        )

        return

    text = "📦 LAST ORDERS\n\n"

    for i, row in enumerate(rows, start=1):
        text += f"#{i} | {row[0]} | {row[1]} TL\n"

    await message.answer(text)

# =========================================
# STATS
# =========================================

@dp.message_handler(lambda m: m.text == "📊 Statistics")
async def statistics(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    cur.execute("""
    SELECT COUNT(*), COALESCE(SUM(total),0)
    FROM orders
    """)

    data = cur.fetchone()

    await message.answer(
        f"""
📊 Statistics

📦 Orders: {data[0]}
💰 Income: {data[1]} TL
"""
    )

# =========================================
# SHOW CATEGORIES
# =========================================

@dp.message_handler(lambda m: m.text == "📂 Categories")
async def categories(message: types.Message):

    text = "📂 Categories:\n\n"

    for category in menu_data.keys():
        text += f"• {category}\n"

    await message.answer(text)

# =========================================
# ADD PRODUCT
# =========================================

@dp.message_handler(lambda m: m.text == "➕ Add Product")
async def add_product(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    text = "📂 Choose category:\n\n"

    for category in menu_data.keys():
        text += f"• {category}\n"

    await message.answer(text)

    await AddProduct.category.set()

@dp.message_handler(state=AddProduct.category)
async def add_product_category(message: types.Message, state: FSMContext):

    category = message.text

    if category not in menu_data:

        await message.answer(
            "❌ Category not found"
        )

        return

    await state.update_data(category=category)

    await message.answer(
        "🍔 Enter product name"
    )

    await AddProduct.product_name.set()

@dp.message_handler(state=AddProduct.product_name)
async def add_product_name(message: types.Message, state: FSMContext):

    await state.update_data(name=message.text)

    await message.answer(
        "💰 Enter product price"
    )

    await AddProduct.product_price.set()

@dp.message_handler(state=AddProduct.product_price)
async def add_product_price(message: types.Message, state: FSMContext):

    data = await state.get_data()

    category = data["category"]
    name = data["name"]

    try:
        price = int(message.text)

    except:

        await message.answer(
            "❌ Enter only numbers"
        )

        return

    menu_data[category].append(
        (name, price)
    )

    await message.answer(
        "✅ Product added",
        reply_markup=main_menu()
    )

    await state.finish()

# =========================================
# DELETE CATEGORY
# =========================================

@dp.message_handler(lambda m: m.text == "❌ Delete Category")
async def delete_category(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    text = "❌ Enter category name:\n\n"

    for category in menu_data.keys():
        text += f"• {category}\n"

    await message.answer(text)

    await DeleteCategory.waiting.set()

@dp.message_handler(state=DeleteCategory.waiting)
async def delete_category_confirm(message: types.Message, state: FSMContext):

    category = message.text

    if category in menu_data:

        del menu_data[category]

        await message.answer(
            "✅ Category deleted",
            reply_markup=main_menu()
        )

    else:

        await message.answer(
            "❌ Category not found"
        )

    await state.finish()

# =========================================
# BACK
# =========================================

@dp.message_handler(lambda m: m.text == "⬅️ Back")
async def back(message: types.Message, state: FSMContext):

    await state.finish()

    await message.answer(
        "⬅️ Main menu",
        reply_markup=main_menu()
    )

# =========================================
# UNIVERSAL HANDLER
# =========================================

@dp.message_handler()
async def universal_handler(message: types.Message):

    text = message.text

    # =====================================
    # ADD PRODUCT TO CART
    # =====================================

    for category in menu_data.values():

        for name, price in category:

            product_text = f"{name} — {price} TL"

            if text == product_text:

                user_id = message.from_user.id

                if user_id not in user_carts:
                    user_carts[user_id] = []

                user_carts[user_id].append(product_text)

                await message.answer(
                    f"✅ Added to cart:\n{product_text}",
                    reply_markup=main_menu()
                )

                return

    # =====================================
    # CHECKOUT
    # =====================================

    if text == "Checkout":

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

        return

# =========================================
# RUN
# =========================================

if __name__ == "__main__":

    Thread(target=run_web).start()

    executor.start_polling(
        dp,
        skip_updates=True
    )
