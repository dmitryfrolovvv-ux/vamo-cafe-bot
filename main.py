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
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
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

app = Flask('')


@app.route('/')
def home():
    return "Bot is running"


def run_web():
    app.run(host='0.0.0.0', port=10000)


def keep_alive():
    t = Thread(target=run_web)
    t.start()

# =========================
# DATABASE
# =========================

conn = psycopg2.connect(
    DATABASE_URL,
    sslmode="require"
)

cur = conn.cursor()

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
# MENU
# =========================

def main_menu():

    kb = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    cur.execute(
        "SELECT name FROM categories"
    )

    categories = cur.fetchall()

    for category in categories:

        kb.add(
            KeyboardButton(category[0])
        )

    kb.add(
        KeyboardButton("🛒 Cart")
    )

    return kb
    
register_admin(
    dp,
    conn,
    cur,
    main_menu
)

# =========================
# START
# =========================

@dp.message_handler(lambda m: "reset" in m.text, state="*")
async def reset_btn(message: types.Message, state: FSMContext):

    if message.from_user.id != ADMIN_ID:
        return

    await state.finish()

    await message.answer(
        "✅ State reset",
        reply_markup=main_menu()
    )

@dp.message_handler(commands=["start"])
async def start(message: types.Message):

    await message.answer(
        "🍔 Welcome to VAMO Cafe",
        reply_markup=main_menu()
    )

def get_categories():

    cur.execute(
        "SELECT name FROM categories"
    )

    return [x[0] for x in cur.fetchall()]
    
@dp.message_handler(lambda m: m.text in get_categories())
async def category_handler(message: types.Message):

    text = message.text

    # =====================
    # IGNORE CART
    # =====================

    if text == "🛒 Cart":
        return

    # =====================
    # BACK
    # =====================

    if text == "⬅ Back":

        await message.answer(
            "🏠 Main menu",
            reply_markup=main_menu()
        )

        return

    # =====================
    # CATEGORY
    # =====================

    cur.execute(
        """
        SELECT product_name, price, image
        FROM products
        WHERE category=%s
        """,
        (text,)
    )

    category_products = cur.fetchall()

    if category_products:

        kb = ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        for product in category_products:

            name = product[0]

            price = product[1]

            image = product[2]

            product_text = f"{name} — {price} TL"

    inline_kb = InlineKeyboardMarkup()
    
    inline_kb.add(
        InlineKeyboardButton(
            text="➕ Add to cart",
            callback_data=f"add_{name}"
        )
    )

            if image:

                await bot.send_photo(
                    message.chat.id,
                    photo=image,
                    caption=f"🍽 {name}\n\n💰 {price} TL",
                    reply_markup=inline_kb
                )    

            else:

                await message.answer(
                    f"🍽 {name}\n\n💰 {price} TL",
                    reply_markup=inline_kb
                )

        kb.add(
            KeyboardButton("⬅ Back")
        )

        await message.answer(
            "⬇ Select product",
            reply_markup=kb
        )

        return

@dp.callback_query_handler(lambda c: c.data.startswith("add_"))
async def add_to_cart_callback(callback: types.CallbackQuery):

    product_name = callback.data.replace("add_", "")

    user_id = callback.from_user.id

    cur.execute(
        """
        SELECT price
        FROM products
        WHERE product_name=%s
        """,
        (product_name,)
    )

    product = cur.fetchone()

    if not product:

        await callback.answer(
            "❌ Product not found",
            show_alert=True
        )

        return

    price = product[0]

    cur.execute(
        """
        INSERT INTO cart(
            user_id,
            product_name,
            price
        )
        VALUES(%s,%s,%s)
        """,
        (
            user_id,
            product_name,
            price
        )
    )

    conn.commit()

    await callback.answer(
        "✅ Added to cart"
    )

# =========================
# UNIVERSAL
# =========================

@dp.message_handler(state=None)
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

    keep_alive()

    executor.start_polling(
        dp,
        skip_updates=True
    )
