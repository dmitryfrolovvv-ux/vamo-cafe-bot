# =========================================
# VAMO CAFE BOT
# FULL MAIN.PY
# =========================================

import logging
import psycopg2

from flask import Flask
from threading import Thread

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# =========================================
# CONFIG
# =========================================

TOKEN = "8729557900:AAGQceOGd-V5erYJpSXV5M95wrFU_JeMd4Q"

ADMIN_ID = 1472777680

DATABASE_URL = "postgresql://postgres.gtglvcebuvuampyhtaze:froLOV580530.@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

logging.basicConfig(level=logging.INFO)

# =========================================
# BOT
# =========================================

bot = Bot(token=TOKEN)

storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)

# =========================================
# FLASK
# =========================================

app = Flask(__name__)

@app.route("/")
def home():
    return "VAMO BOT WORKING"

def run_web():
    app.run(host="0.0.0.0", port=10000)

# =========================================
# DATABASE
# =========================================

conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS categories(
    id SERIAL PRIMARY KEY,
    name TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS products(
    id SERIAL PRIMARY KEY,
    category TEXT,
    product_name TEXT,
    price INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS cart(
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    product_name TEXT,
    price INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders(
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    order_text TEXT
)
""")

conn.commit()

# =========================================
# STATES
# =========================================

class OrderState(StatesGroup):
    waiting_address = State()
    waiting_phone = State()
    waiting_comment = State()

class AdminState(StatesGroup):
    waiting_category = State()
    waiting_product_category = State()
    waiting_product_name = State()
    waiting_product_price = State()
    waiting_delete_category = State()
    waiting_delete_product = State()

# =========================================
# TEMP DATA
# =========================================

temp_product = {}

# =========================================
# MAIN MENU
# =========================================

def main_menu():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    cur.execute("SELECT name FROM categories")

    categories = cur.fetchall()

    for category in categories:
        kb.add(KeyboardButton(category[0]))

    kb.add(KeyboardButton("🛒 CART"))

    return kb

# =========================================
# ADMIN MENU
# =========================================

def admin_menu():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("➕ Add Category"))
    kb.add(KeyboardButton("➕ Add Product"))

    kb.add(KeyboardButton("❌ Delete Category"))
    kb.add(KeyboardButton("❌ Delete Product"))

    kb.add(KeyboardButton("📦 Orders"))
    kb.add(KeyboardButton("📊 Statistics"))

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
# ADMIN PANEL
# =========================================

@dp.message_handler(commands=["admin"])
async def admin_panel(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "⚙ ADMIN PANEL",
        reply_markup=admin_menu()
    )

# =========================================
# ADD CATEGORY
# =========================================

@dp.message_handler(lambda m: m.text == "➕ Add Category")
async def add_category(message: types.Message):

    await message.answer("📂 Enter category name")

    await AdminState.waiting_category.set()

@dp.message_handler(state=AdminState.waiting_category)
async def save_category(message: types.Message, state: FSMContext):

    cur.execute(
        "INSERT INTO categories(name) VALUES(%s)",
        (message.text,)
    )

    conn.commit()

    await message.answer("✅ Category added")

    await state.finish()

# =========================================
# DELETE CATEGORY
# =========================================

@dp.message_handler(lambda m: m.text == "❌ Delete Category")
async def delete_category(message: types.Message):

    await message.answer("❌ Enter category name")

    await AdminState.waiting_delete_category.set()

@dp.message_handler(state=AdminState.waiting_delete_category)
async def remove_category(message: types.Message, state: FSMContext):

    category = message.text

    cur.execute(
        "DELETE FROM categories WHERE name=%s",
        (category,)
    )

    cur.execute(
        "DELETE FROM products WHERE category=%s",
        (category,)
    )

    conn.commit()

    await message.answer("✅ Category deleted")

    await state.finish()

# =========================================
# ADD PRODUCT
# =========================================

@dp.message_handler(lambda m: m.text == "➕ Add Product")
async def add_product(message: types.Message):

    cur.execute("SELECT name FROM categories")

    categories = cur.fetchall()

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    for category in categories:
        kb.add(KeyboardButton(category[0]))

    await message.answer(
        "📂 Choose category",
        reply_markup=kb
    )

    await AdminState.waiting_product_category.set()

@dp.message_handler(state=AdminState.waiting_product_category)
async def get_product_category(message: types.Message, state: FSMContext):

    temp_product["category"] = message.text

    await message.answer("🍔 Enter product name")

    await AdminState.waiting_product_name.set()

@dp.message_handler(state=AdminState.waiting_product_name)
async def get_product_name(message: types.Message, state: FSMContext):

    temp_product["name"] = message.text

    await message.answer("💰 Enter price")

    await AdminState.waiting_product_price.set()

@dp.message_handler(state=AdminState.waiting_product_price)
async def get_product_price(message: types.Message, state: FSMContext):

    category = temp_product["category"]

    name = temp_product["name"]

    price = int(message.text)

    cur.execute(
        """
        INSERT INTO products(category, product_name, price)
        VALUES(%s,%s,%s)
        """,
        (
            category,
            name,
            price
        )
    )

    conn.commit()

    await message.answer(
        "✅ Product added",
        reply_markup=admin_menu()
    )

    await state.finish()

# =========================================
# DELETE PRODUCT
# =========================================

@dp.message_handler(lambda m: m.text == "❌ Delete Product")
async def delete_product(message: types.Message):

    await message.answer("❌ Enter exact product name")

    await AdminState.waiting_delete_product.set()

@dp.message_handler(state=AdminState.waiting_delete_product)
async def remove_product(message: types.Message, state: FSMContext):

    cur.execute(
        "DELETE FROM products WHERE product_name=%s",
        (message.text,)
    )

    conn.commit()

    await message.answer("✅ Product deleted")

    await state.finish()

# =========================================
# ORDERS
# =========================================

@dp.message_handler(lambda m: m.text == "📦 Orders")
async def orders(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    cur.execute(
        "SELECT order_text FROM orders ORDER BY id DESC LIMIT 10"
    )

    orders = cur.fetchall()

    if not orders:

        await message.answer("❌ No orders")

        return

    text = "📦 LAST ORDERS\n\n"

    for order in orders:
        text += order[0] + "\n\n"

    await message.answer(text)

# =========================================
# STATISTICS
# =========================================

@dp.message_handler(lambda m: m.text == "📊 Statistics")
async def statistics(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    cur.execute("SELECT COUNT(*) FROM orders")

    orders_count = cur.fetchone()[0]

    cur.execute("SELECT SUM(price) FROM cart")

    total = cur.fetchone()[0]

    if total is None:
        total = 0

    text = f"""
📊 Statistics

📦 Orders: {orders_count}

💰 Income: {total} TL
"""

    await message.answer(text)

# =========================================
# CATEGORY
# =========================================

@dp.message_handler(lambda m: m.text not in [
    "🛒 CART",
    "CHECKOUT",
    "⬅ Back",
    "BACK"
])
async def category_handler(message: types.Message):

    try:

        category = message.text

        cur.execute(
            """
            SELECT product_name, price
            FROM products
            WHERE category=%s
            """,
            (category,)
        )

        products = cur.fetchall()

        if not products:
            return

        text = f"🍔 {category}\n\n"

        kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for product in products:

            text += f"• {product[0]} — {product[1]} TL\n"

            kb.add(
                KeyboardButton(
                    f"{product[0]} — {product[1]} TL"
                )
            )

        kb.add(KeyboardButton("⬅ Back"))

        await message.answer(text, reply_markup=kb)

    except Exception as e:

        conn.rollback()

        print(e)

        await message.answer(str(e))

# =========================================
# ADD TO CART
# =========================================

@dp.message_handler(lambda m: "—" in m.text)
async def add_to_cart(message: types.Message):

    try:

        text = message.text

        parts = text.split("—")

        product_name = parts[0].strip()

        price = int(
            parts[1]
            .replace("TL", "")
            .strip()
        )

        cur.execute(
            """
            INSERT INTO cart(user_id, product_name, price)
            VALUES(%s,%s,%s)
            """,
            (
                message.from_user.id,
                product_name,
                price
            )
        )

        conn.commit()

        await message.answer(
            f"✅ Added to cart:\n{product_name} — {price} TL",
            reply_markup=main_menu()
        )

    except Exception as e:

        conn.rollback()

        print(e)

        await message.answer(str(e))

# =========================================
# CART
# =========================================

@dp.message_handler(lambda m: m.text == "🛒 CART")
async def cart_handler(message: types.Message):

    try:

        user_id = message.from_user.id

        cur.execute(
            """
            SELECT product_name, price
            FROM cart
            WHERE user_id=%s
            """,
            (user_id,)
        )

        items = cur.fetchall()

        if not items:

            await message.answer(
                "🛒 Cart is empty",
                reply_markup=main_menu()
            )

            return

        text = "🛒 YOUR CART\n\n"

        total = 0

        for item in items:

            text += f"• {item[0]} — {item[1]} TL\n"

            total += item[1]

        text += f"\n💰 Total: {total} TL"

        kb = ReplyKeyboardMarkup(resize_keyboard=True)

        kb.add(KeyboardButton("CHECKOUT"))

        kb.add(KeyboardButton("⬅ Back"))

        await message.answer(text, reply_markup=kb)

    except Exception as e:

        conn.rollback()

        print(e)

        await message.answer(str(e))

# =========================================
# CHECKOUT
# =========================================

@dp.message_handler(lambda m: m.text == "CHECKOUT")
async def checkout(message: types.Message):

    await message.answer("📍 Enter your address")

    await OrderState.waiting_address.set()

# =========================================
# ADDRESS
# =========================================

@dp.message_handler(state=OrderState.waiting_address)
async def get_address(message: types.Message, state: FSMContext):

    await state.update_data(address=message.text)

    await message.answer("📞 Enter phone number")

    await OrderState.waiting_phone.set()

# =========================================
# PHONE
# =========================================

@dp.message_handler(state=OrderState.waiting_phone)
async def get_phone(message: types.Message, state: FSMContext):

    await state.update_data(phone=message.text)

    await message.answer("🚪 Enter comment / door code")

    await OrderState.waiting_comment.set()

# =========================================
# FINISH ORDER
# =========================================

@dp.message_handler(state=OrderState.waiting_comment)
async def finish_order(message: types.Message, state: FSMContext):

    try:

        data = await state.get_data()

        address = data["address"]

        phone = data["phone"]

        comment = message.text

        user_id = message.from_user.id

        cur.execute(
            """
            SELECT product_name, price
            FROM cart
            WHERE user_id=%s
            """,
            (user_id,)
        )

        items = cur.fetchall()

        if not items:

            await message.answer("❌ Cart is empty")

            await state.finish()

            return

        text = "🛍 NEW ORDER\n\n"

        total = 0

        for item in items:

            text += f"• {item[0]} — {item[1]} TL\n"

            total += item[1]

        text += f"\n💰 Total: {total} TL"

        text += f"\n\n📍 Address:\n{address}"

        text += f"\n\n📞 Phone:\n{phone}"

        text += f"\n\n🚪 Comment:\n{comment}"

        await bot.send_message(
            ADMIN_ID,
            text
        )

        cur.execute(
            """
            INSERT INTO orders(user_id, order_text)
            VALUES(%s,%s)
            """,
            (
                user_id,
                text
            )
        )

        cur.execute(
            "DELETE FROM cart WHERE user_id=%s",
            (user_id,)
        )

        conn.commit()

        await message.answer(
            "✅ Order sent successfully!",
            reply_markup=main_menu()
        )

        await state.finish()

    except Exception as e:

        conn.rollback()

        print(e)

        await message.answer(str(e))

# =========================================
# BACK
# =========================================

@dp.message_handler(lambda m: m.text in ["⬅ Back", "BACK"])
async def back_handler(message: types.Message):

    await message.answer(
        "⬅ Main menu",
        reply_markup=main_menu()
    )

# =========================================
# RUN
# =========================================

if __name__ == "__main__":

    Thread(target=run_web).start()

    executor.start_polling(
        dp,
        skip_updates=True
    )
