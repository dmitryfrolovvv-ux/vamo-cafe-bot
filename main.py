# =========================
# MAIN.PY
# =========================

import logging
import psycopg2

from aiogram import Bot, Dispatcher, executor, types
from admin import register_admin
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
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

try:
    cur.execute("""
        ALTER TABLE products
        ADD COLUMN description TEXT
    """)
    conn.commit()

except:
    conn.rollback()

# =========================
# INLINE MAIN MENU
# =========================

def inline_main_menu():

    kb = InlineKeyboardMarkup(row_width=2)

    cur.execute(
        """
        SELECT name
        FROM categories
        """
    )

    categories = cur.fetchall()

    buttons = []

    for category in categories:

        buttons.append(
            InlineKeyboardButton(
                text=category[0],
                callback_data=f"category_{category[0]}"
            )
        )

    kb.add(*buttons)

    kb.row(
        InlineKeyboardButton(
            text="🛒 Cart",
            callback_data="open_cart"
        )
    )

    return kb

# =========================
# SIMPLE MENU FOR ADMIN
# =========================

def simple_menu():

    kb = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.add(
        KeyboardButton("/start")
    )

    return kb

# =========================
# REGISTER ADMIN
# =========================

register_admin(
    dp,
    conn,
    cur,
    simple_menu
)

# =========================
# RESET
# =========================

@dp.message_handler(lambda m: "reset" in m.text.lower(), state="*")
async def reset_btn(message: types.Message, state: FSMContext):

    if message.from_user.id != ADMIN_ID:
        return

    await state.finish()

    await message.answer(
        "✅ State reset"
    )

# =========================
# START
# =========================

@dp.message_handler(commands=["start"])
async def start(message: types.Message):

    await message.answer(
        "🍔 Welcome to VAMO Cafe",
        reply_markup=inline_main_menu()
    )

# =========================
# CATEGORY
# =========================

@dp.callback_query_handler(
    lambda c: c.data.startswith("category_")
)
async def category_callback(callback: types.CallbackQuery):

    category_name = callback.data.replace(
        "category_",
        ""
    )

    cur.execute(
        """
        SELECT product_name
        FROM products
        WHERE category=%s
        """,
        (category_name,)
    )

    products = cur.fetchall()

    if not products:

        await callback.answer(
            "❌ No products",
            show_alert=True
        )

        return

    products_kb = InlineKeyboardMarkup(row_width=1)

    for product in products:

        product_name = product[0]

        products_kb.add(
            InlineKeyboardButton(
                text=product_name,
                callback_data=f"product_{product_name}"
            )
        )

    products_kb.row(
        InlineKeyboardButton(
            text="⬅ Back",
            callback_data="back_main"
        )
    )

    await callback.message.answer(
        f"📋 {category_name}",
        reply_markup=products_kb
    )

    await callback.answer()

# =========================
# PRODUCT CARD
# =========================

@dp.callback_query_handler(
    lambda c: c.data.startswith("product_")
)
async def product_card(callback: types.CallbackQuery):

    product_name = callback.data.replace(
        "product_",
        ""
    )

    cur.execute(
        """
        SELECT product_name, description, price, image
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

    name = product[0]

    description = product[1]

    price = product[2]
    
    image = product[3]

    kb = InlineKeyboardMarkup(row_width=1)

    kb.add(
        InlineKeyboardButton(
            text="➕ Add to cart",
            callback_data=f"add_{name}"
        )
    )

    kb.add(
        InlineKeyboardButton(
            text="⬅ Back",
            callback_data="back_main"
        )
    )

    if image:

        await bot.send_photo(
            callback.message.chat.id,
            photo=image,
            caption=(
            f"🍽 {name}\n\n"
            f"📝 {description}\n\n"
            f"💰 {price} TL"
)

    else:

        await callback.message.answer(
            f"🍽 {name}\n\n💰 {price} TL",
            reply_markup=kb
        )

        await callback.answer()
# =========================
# ADD TO CART
# =========================

@dp.callback_query_handler(
    lambda c: c.data.startswith("add_")
)
async def add_to_cart_callback(callback: types.CallbackQuery):

    product_name = callback.data.replace(
        "add_",
        ""
    )

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
# OPEN CART
# =========================

@dp.callback_query_handler(
    lambda c: c.data == "open_cart"
)
async def open_cart(callback: types.CallbackQuery):

    user_id = callback.from_user.id

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

        await callback.answer(
            "🛒 Cart is empty",
            show_alert=True
        )

        return

    text = "🛒 YOUR CART\n\n"

    total = 0

    for item in items:

        text += f"• {item[0]} — {item[1]} TL\n"

        total += item[1]

    text += f"\n💰 Total: {total} TL"

    kb = InlineKeyboardMarkup(row_width=1)

    kb.add(
        InlineKeyboardButton(
            text="✅ Checkout",
            callback_data="checkout"
        )
    )

    kb.add(
        InlineKeyboardButton(
            text="🗑 Clear cart",
            callback_data="clear_cart"
        )
    )

    kb.add(
        InlineKeyboardButton(
            text="⬅ Back",
            callback_data="back_main"
        )
    )

    await callback.message.answer(
        text,
        reply_markup=kb
    )

    await callback.answer()

# =========================
# CLEAR CART
# =========================

@dp.callback_query_handler(
    lambda c: c.data == "clear_cart"
)
async def clear_cart(callback: types.CallbackQuery):

    user_id = callback.from_user.id

    cur.execute(
        """
        DELETE FROM cart
        WHERE user_id=%s
        """,
        (user_id,)
    )

    conn.commit()

    await callback.answer(
        "🗑 Cart cleared"
    )

    await callback.message.answer(
        "🏠 Main menu",
        reply_markup=inline_main_menu()
    )

# =========================
# BACK MAIN
# =========================

@dp.callback_query_handler(
    lambda c: c.data == "back_main"
)
async def back_main(callback: types.CallbackQuery):

    await callback.message.answer(
        "🏠 Main menu",
        reply_markup=inline_main_menu()
    )

    await callback.answer()

# =========================
# CHECKOUT
# =========================

@dp.callback_query_handler(
    lambda c: c.data == "checkout"
)
async def checkout_start(callback: types.CallbackQuery):

    kb = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.add(
        KeyboardButton(
            "📍 Send location",
            request_location=True
        )
    )

    kb.add(
        KeyboardButton("⏭ Skip")
    )

    await callback.message.answer(
        "📍 Send location or skip",
        reply_markup=kb
    )

    await Checkout.address.set()

    await callback.answer()

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

        cur.execute(
            """
            INSERT INTO orders(
                user_id,
                order_text
            )
            VALUES(%s,%s)
            """,
            (
                user_id,
                text
            )
        )

        cur.execute(
            """
            DELETE FROM cart
            WHERE user_id=%s
            """,
            (user_id,)
        )

        conn.commit()

        await message.answer(
            "✅ Order sent successfully!",
            reply_markup=inline_main_menu()
        )

        await state.finish()

    except Exception as e:

        conn.rollback()

        await message.answer(str(e))

# =========================
# RUN
# =========================

if __name__ == "__main__":

    import asyncio

    asyncio.set_event_loop_policy(
        asyncio.DefaultEventLoopPolicy()
    )

    executor.start_polling(
        dp,
        skip_updates=True,
        timeout=60,
        relax=0.1,
        fast=True
    )
