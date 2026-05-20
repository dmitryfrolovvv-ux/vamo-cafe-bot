# =========================================
# MAIN.PY
# =========================================

import logging
import psycopg2
import os

from flask import Flask
from threading import Thread

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from admin import register_admin

# =========================================
# CONFIG
# =========================================

TOKEN = "8729557900:AAGQceOGd-V5erYJpSXV5M95wrFU_JeMd4Q"

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
    app.run(host="0.0.0.0", port=10000)

# =========================================
# DATABASE
# =========================================

conn = psycopg2.connect(
    DATABASE_URL,
    sslmode="require"
)

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
# BOT
# =========================================

bot = Bot(token=TOKEN)

storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)

# =========================================
# ADMIN
# =========================================

register_admin(dp, conn, cur)

# =========================================
# STATES
# =========================================

class OrderState(StatesGroup):
    waiting_address = State()
    waiting_phone = State()
    waiting_comment = State()

# =========================================
# ADMIN BUTTONS
# =========================================

ADMIN_BUTTONS = [
    "➕ Add category",
    "➖ Delete category",
    "➕ Add product",
    "➖ Delete product",
    "📦 Orders",
    "📊 Stats",
    "⬅ Back"
]

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
# START
# =========================================

@dp.message_handler(commands=["start"])
async def start(message: types.Message):

    await message.answer(
        "🍔 Welcome to VAMO Cafe",
        reply_markup=main_menu()
    )

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

        await message.answer(str(e))

# =========================================
# CATEGORY
# =========================================

@dp.message_handler(lambda m:
    m.text not in [
        "🛒 CART",
        "CHECKOUT",
        "BACK"
    ] + ADMIN_BUTTONS
)
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

        await message.answer(
            text,
            reply_markup=kb
        )

    except Exception as e:

        conn.rollback()

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

        await message.answer(
            text,
            reply_markup=kb
        )

    except Exception as e:

        conn.rollback()

        await message.answer(str(e))

# =========================================
# CHECKOUT
# =========================================

@dp.message_handler(lambda m: m.text == "CHECKOUT")
async def checkout(message: types.Message):

    await message.answer("📍 Enter address")

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
            1472777680,
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

        await state.finish()

        await message.answer(
            "✅ Order sent successfully!",
            reply_markup=main_menu()
        )

    except Exception as e:

        conn.rollback()

        await state.finish()

        await message.answer(
            str(e),
            reply_markup=main_menu()
        )

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
