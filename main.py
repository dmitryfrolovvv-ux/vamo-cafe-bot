# =========================
# MAIN.PY
# =========================

import logging
import psycopg2

from flask import Flask
from threading import Thread

from aiogram import Bot, Dispatcher, executor, types
from admin import register_admin
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)

# =========================
# CONFIG
# =========================

TOKEN = "8729557900:AAGQceOGd-V5erYJpSXV5M95wrFU_JeMd4Q"

ADMIN_ID = 1472777680

DATABASE_URL = "postgresql://postgres.gtglvcebuvuampyhtaze:froLOV580530.@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

logging.basicConfig(level=logging.INFO)

# =========================
# BOT
# =========================

bot = Bot(token=TOKEN)

storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)

# =========================
# FLASK
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "VAMO BOT WORKING"

# =========================
# DATABASE
# =========================

conn = psycopg2.connect(
    DATABASE_URL,
    sslmode="require"
)

cur = conn.cursor()

register_admin(dp, conn, cur, main_menu)

# =========================
# STATES
# =========================

class Checkout(StatesGroup):

    address = State()

    phone = State()

    comment = State()

# =========================
# TABLES
# =========================

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
    order_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# =========================
# PRODUCTS
# =========================

products = {

    "🌭 Hot Dogs": [

        ("Classic Hot Dog", 150),

        ("Cheese Hot Dog", 180),

        ("Double Hot Dog", 220)

    ],

    "🌯 Shawarma": [

        ("Chicken Shawarma", 200),

        ("Big Shawarma", 260)

    ],

    "🥤 Drinks": [

        ("Cola", 60),

        ("Ayran", 50)

    ]
}

# =========================
# MENU
# =========================

def main_menu():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    for category in products.keys():

        kb.add(
            KeyboardButton(category)
        )

    kb.add(
        KeyboardButton("🛒 Cart")
    )

    return kb

# =========================
# START
# =========================

@dp.message_handler(commands=["start"])
async def start(message: types.Message):

    await message.answer(
        "🍔 Welcome to VAMO Cafe",
        reply_markup=main_menu()
    )

# =========================
# CATEGORY
# =========================

@dp.message_handler(lambda m: m.text in products.keys())
async def category_handler(message: types.Message):

    category = message.text

    text = f"{category}\n\n"

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    for item in products[category]:

        text += f"• {item[0]} — {item[1]} TL\n"

        kb.add(
            KeyboardButton(
                f"{item[0]} — {item[1]} TL"
            )
        )

    kb.add(
        KeyboardButton("⬅ Back")
    )

    await message.answer(
        text,
        reply_markup=kb
    )

# =========================
# UNIVERSAL
# =========================

@dp.message_handler()
async def universal(message: types.Message):

    text = message.text

    # =====================
    # BACK
    # =====================

    if text == "⬅ Back":

        await message.answer(
            "⬅ Main menu",
            reply_markup=main_menu()
        )

        return

    # =====================
    # CART
    # =====================

    if text == "🛒 Cart":

        user_id = message.from_user.id

        cur.execute("""
        SELECT product_name, price
        FROM cart
        WHERE user_id=%s
        """, (user_id,))

        items = cur.fetchall()

        if not items:

            await message.answer(
                "🛒 Cart is empty"
            )

            return

        total = 0

        cart_text = "🛒 YOUR CART\n\n"

        for item in items:

            cart_text += f"• {item[0]} — {item[1]} TL\n"

            total += item[1]

        cart_text += f"\n💰 Total: {total} TL"

        kb = ReplyKeyboardMarkup(resize_keyboard=True)

        kb.add(
            KeyboardButton("✅ Checkout")
        )

        kb.add(
            KeyboardButton("❌ Clear cart")
        )

        kb.add(
            KeyboardButton("⬅ Back")
        )

        await message.answer(
            cart_text,
            reply_markup=kb
        )

        return

    # =====================
    # CLEAR CART
    # =====================

    if text == "❌ Clear cart":

        user_id = message.from_user.id

        cur.execute("""
        DELETE FROM cart
        WHERE user_id=%s
        """, (user_id,))

        conn.commit()

        await message.answer(
            "🗑 Cart cleared",
            reply_markup=main_menu()
        )

        return

    # =====================
    # CHECKOUT
    # =====================

    if text == "✅ Checkout":

        kb = ReplyKeyboardMarkup(resize_keyboard=True)

        kb.add(
            KeyboardButton(
                "📍 Send location",
                request_location=True
            )
        )

        kb.add(
            KeyboardButton("⏭ Skip")
        )

        await message.answer(
            "📍 Send location or skip",
            reply_markup=kb
        )

        await Checkout.address.set()

        return

    # =====================
    # ADD PRODUCT
    # =====================

    for category in products.values():

        for item in category:

            product_text = f"{item[0]} — {item[1]} TL"

            if text == product_text:

                user_id = message.from_user.id

                cur.execute("""
                INSERT INTO cart(
                    user_id,
                    product_name,
                    price
                )
                VALUES(%s,%s,%s)
                """, (
                    user_id,
                    item[0],
                    item[1]
                ))

                conn.commit()

                await message.answer(
                    f"✅ Added to cart:\n{item[0]} — {item[1]} TL"
                )

                return

# =========================
# LOCATION
# =========================

@dp.message_handler(
    content_types=types.ContentType.LOCATION,
    state=Checkout.address
)
async def checkout_location(
    message: types.Message,
    state: FSMContext
):

    lat = message.location.latitude

    lon = message.location.longitude

    address = f"https://maps.google.com/?q={lat},{lon}"

    await state.update_data(
        address=address
    )

    await message.answer(
        "📞 Enter phone number"
    )

    await Checkout.phone.set()

# =========================
# SKIP
# =========================

@dp.message_handler(
    lambda m: m.text == "⏭ Skip",
    state=Checkout.address
)
async def checkout_skip(
    message: types.Message,
    state: FSMContext
):

    await state.update_data(
        address="Not specified"
    )

    await message.answer(
        "📞 Enter phone number"
    )

    await Checkout.phone.set()

# =========================
# ADDRESS
# =========================

@dp.message_handler(state=Checkout.address)
async def checkout_address(
    message: types.Message,
    state: FSMContext
):

    await state.update_data(
        address=message.text
    )

    await message.answer(
        "📞 Enter phone number"
    )

    await Checkout.phone.set()

# =========================
# PHONE
# =========================

@dp.message_handler(state=Checkout.phone)
async def checkout_phone(
    message: types.Message,
    state: FSMContext
):

    await state.update_data(
        phone=message.text
    )

    await message.answer(
        "🚪 Enter comment / door code"
    )

    await Checkout.comment.set()

# =========================
# COMMENT
# =========================

@dp.message_handler(state=Checkout.comment)
async def checkout_comment(
    message: types.Message,
    state: FSMContext
):

    try:

        data = await state.get_data()

        address = data["address"]

        phone = data["phone"]

        comment = message.text

        user_id = message.from_user.id

        cur.execute("""
        SELECT product_name, price
        FROM cart
        WHERE user_id=%s
        """, (user_id,))

        items = cur.fetchall()

        if not items:

            await message.answer(
                "❌ Cart is empty"
            )

            await state.finish()

            return

        username = message.from_user.username

        if username:

            mention = f"@{username}"

        else:

            mention = message.from_user.full_name

        text = f"🚨 NEW ORDER {mention}\n\n"

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

        cur.execute("""
        INSERT INTO orders(
            user_id,
            order_text
        )
        VALUES(%s,%s)
        """, (
            user_id,
            text
        ))

        cur.execute("""
        DELETE FROM cart
        WHERE user_id=%s
        """, (user_id,))

        conn.commit()

        await message.answer(
            "✅ Order sent successfully!",
            reply_markup=main_menu()
        )

        await state.finish()

    except Exception as e:

        conn.rollback()

        await message.answer(str(e))

# =========================
# WEB
# =========================

def run_web():

    app.run(
        host="0.0.0.0",
        port=10000
    )

# =========================
# RUN
# =========================

if __name__ == "__main__":

    Thread(
        target=run_web
    ).start()

    executor.start_polling(
        dp,
        skip_updates=True
    )
