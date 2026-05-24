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
CREATE TABLE IF NOT EXISTS users(
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE,
    language TEXT DEFAULT 'en'
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
    
try:
    cur.execute("""
        ALTER TABLE categories
        ADD COLUMN image TEXT
    """)
    conn.commit()

except:
    conn.rollback()

try:
    cur.execute("""
        ALTER TABLE categories
        ADD COLUMN description TEXT
    """)
    conn.commit()

except:
    conn.rollback()
    
try:
    cur.execute("""
        ALTER TABLE orders
        ADD COLUMN status TEXT
        DEFAULT '🟡 New'
    """)
    conn.commit()

except:
    conn.rollback()
    
# =========================
# MULTILANGUAGE CATEGORIES
# =========================

try:
    cur.execute("""
        ALTER TABLE categories
        ADD COLUMN name_en TEXT
    """)
    conn.commit()

except:
    conn.rollback()

try:
    cur.execute("""
        ALTER TABLE categories
        ADD COLUMN name_ru TEXT
    """)
    conn.commit()

except:
    conn.rollback()

try:
    cur.execute("""
        ALTER TABLE categories
        ADD COLUMN name_tr TEXT
    """)
    conn.commit()

except:
    conn.rollback()

# =========================
# MULTILANGUAGE PRODUCTS
# =========================

try:
    cur.execute("""
        ALTER TABLE products
        ADD COLUMN product_name_en TEXT
    """)
    conn.commit()

except:
    conn.rollback()

try:
    cur.execute("""
        ALTER TABLE products
        ADD COLUMN product_name_ru TEXT
    """)
    conn.commit()

except:
    conn.rollback()

try:
    cur.execute("""
        ALTER TABLE products
        ADD COLUMN product_name_tr TEXT
    """)
    conn.commit()

except:
    conn.rollback()

try:
    cur.execute("""
        ALTER TABLE products
        ADD COLUMN description_en TEXT
    """)
    conn.commit()

except:
    conn.rollback()

try:
    cur.execute("""
        ALTER TABLE products
        ADD COLUMN description_ru TEXT
    """)
    conn.commit()

except:
    conn.rollback()

try:
    cur.execute("""
        ALTER TABLE products
        ADD COLUMN description_tr TEXT
    """)
    conn.commit()

except:
    conn.rollback()
    
# =========================
# INLINE MAIN MENU
# =========================

def inline_main_menu(user_id=None):

    kb = InlineKeyboardMarkup(row_width=2)

    language = "en"

    if user_id:

        language = get_user_language(user_id)

    if language == "ru":

        cur.execute(
            """
            SELECT name, name_ru
            FROM categories
            """
        )

    elif language == "tr":

        cur.execute(
            """
            SELECT name, name_tr
            FROM categories
            """
        )

    else:

        cur.execute(
            """
            SELECT name, name_en
            FROM categories
            """
        )

    categories = cur.fetchall()

    buttons = []

    for category in categories:

        original_name = category[0]

        translated_name = category[1] or category[0]

        buttons.append(
            InlineKeyboardButton(
                text=translated_name,
                callback_data=f"category_{original_name}"
            )
        )

    kb.add(*buttons)

    kb.row(
        InlineKeyboardButton(
            text=get_text(user_id, "cart"),
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
# TEXTS
# =========================

TEXTS = {

    "welcome": {

        "en": "🍔 Welcome to VAMO Cafe",

        "ru": "🍔 Добро пожаловать в VAMO Cafe",

        "tr": "🍔 VAMO Cafe'ye hoşgeldiniz"
    },

    "cart": {

        "en": "🛒 Cart",

        "ru": "🛒 Корзина",

        "tr": "🛒 Sepet"
    },

    "main_menu": {

        "en": "🏠 Main menu",

        "ru": "🏠 Главное меню",

        "tr": "🏠 Ana Menü"
    }

    "cart_empty": {
    
        "en": "🛒 Cart is empty",
    
        "ru": "🛒 Корзина пуста",
    
        "tr": "🛒 Sepet boş"
    },
    
    "product_not_found": {
    
        "en": "❌ Product not found",
    
        "ru": "❌ Товар не найден",
    
        "tr": "❌ Ürün bulunamadı"
    },
    
    "no_products": {
    
        "en": "❌ No products",
    
        "ru": "❌ Нет товаров",
    
        "tr": "❌ Ürün yok"
    },
    
    "cart_cleared": {
    
        "en": "🗑 Cart cleared",
    
        "ru": "🗑 Корзина очищена",
    
        "tr": "🗑 Sepet temizlendi"
    },

    "added_to_cart": {
    
        "en": "✅ Added to cart",
    
        "ru": "✅ Добавлено в корзину",
    
        "tr": "✅ Sepete eklendi"
    
    }
}

# =========================
# LANGUAGE MENU
# =========================

def get_user_language(user_id):

    cur.execute(
        """
        SELECT language
        FROM users
        WHERE user_id=%s
        """,
        (user_id,)
    )

    user = cur.fetchone()

    if user:

        return user[0]

    return "en"


def get_text(user_id, key):

    language = get_user_language(user_id)

    return TEXTS[key].get(
        language,
        TEXTS[key]["en"]
    )
def language_menu():

    kb = InlineKeyboardMarkup(row_width=1)

    kb.add(
        InlineKeyboardButton(
            text="🇬🇧 English",
            callback_data="lang_en"
        )
    )

    kb.add(
        InlineKeyboardButton(
            text="🇷🇺 Русский",
            callback_data="lang_ru"
        )
    )

    kb.add(
        InlineKeyboardButton(
            text="🇹🇷 Türkçe",
            callback_data="lang_tr"
        )
    )

    return kb
    
# =========================
# START
# =========================

@dp.message_handler(commands=["start"])
async def start(message: types.Message):

    await message.answer(
    "🌍 Choose language",
    reply_markup=language_menu()
)
    
# =========================
# LANGUAGE SELECT
# =========================

@dp.callback_query_handler(
    lambda c: c.data.startswith("lang_")
)
async def language_select(
    callback: types.CallbackQuery
):

    language = callback.data.replace(
        "lang_",
        ""
    )

    user_id = callback.from_user.id

    cur.execute(
        """
        INSERT INTO users(
            user_id,
            language
        )
        VALUES(%s,%s)
        ON CONFLICT(user_id)
        DO UPDATE SET language=%s
        """,
        (
            user_id,
            language,
            language
        )
    )

    conn.commit()

    await callback.message.answer(
        get_text(user_id, "welcome"),
        reply_markup=inline_main_menu(callback.from_user.id)
    )

    await callback.answer()
    
# =========================
# CATEGORY
# =========================

@dp.callback_query_handler(
    lambda c: c.data.startswith("category_")
)
async def category_callback(callback: types.CallbackQuery):

    category = callback.data.replace(
        "category_",
        ""
    )

    language = get_user_language(
        callback.from_user.id
    )

    if language == "ru":

        cur.execute(
            """
            SELECT
                product_name,
                product_name_ru
            FROM products
            WHERE category=%s
            """,
            (category,)
        )

    elif language == "tr":

        cur.execute(
            """
            SELECT
                product_name,
                product_name_tr
            FROM products
            WHERE category=%s
            """,
            (category,)
        )

    else:

        cur.execute(
            """
            SELECT
                product_name,
                product_name_en
            FROM products
            WHERE category=%s
            """,
            (category,)
        )

    products = cur.fetchall()

    if not products:

        await callback.answer(
            get_text(callback.from_user.id, "no_products"),
            show_alert=True
        )

        return

    products_kb = InlineKeyboardMarkup(row_width=1)

    for product in products:

        original_name = product[0]

        translated_name = product[1] or product[0]

        products_kb.add(
            InlineKeyboardButton(
                text=translated_name,
                callback_data=f"product_{original_name}"
            )
        )

    products_kb.row(
        InlineKeyboardButton(
            text="⬅ Back",
            callback_data="back_main"
        )
    )

    await callback.message.answer(
        f"📋 {category}",
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

    language = get_user_language(
        callback.from_user.id
    )

    if language == "ru":

        cur.execute(
            """
            SELECT
                product_name,
                product_name_ru,
                description_ru,
                price,
                image,
                category
            FROM products
            WHERE product_name=%s
            """,
            (product_name,)
        )

    elif language == "tr":

        cur.execute(
            """
            SELECT
                product_name,
                product_name_tr,
                description_tr,
                price,
                image,
                category
            FROM products
            WHERE product_name=%s
            """,
            (product_name,)
        )

    else:

        cur.execute(
            """
            SELECT
                product_name,
                product_name_en,
                description_en,
                price,
                image,
                category
            FROM products
            WHERE product_name=%s
            """,
            (product_name,)
        )

    product = cur.fetchone()

    if not product:

        await callback.answer(
            get_text(callback.from_user.id, "product_not_found"),
            show_alert=True
        )

        return

    original_name = product[0]

    name = product[1] or product[0]

    description = product[2] or ""

    price = product[3]

    image = product[4]

    category = product[5]

    count = 1

    kb = InlineKeyboardMarkup(row_width=3)

    kb.row(
        InlineKeyboardButton(
            text="➖",
            callback_data=f"minus_{original_name}_{count}_{category}"
        ),

        InlineKeyboardButton(
            text=str(count),
            callback_data="count"
        ),

        InlineKeyboardButton(
            text="➕",
            callback_data=f"plus_{original_name}_{count}_{category}"
        )
    )

    kb.row(
        InlineKeyboardButton(
            text="🛒 Add to cart",
            callback_data=f"add_{original_name}_{count}"
        )
    )

    kb.row(
        InlineKeyboardButton(
            text="⬅ Back",
            callback_data=f"category_{category}"
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
            ),
            reply_markup=kb
        )

    else:

        await callback.message.answer(
            (
                f"🍽 {name}\n\n"
                f"📝 {description}\n\n"
                f"💰 {price} TL"
            ),
            reply_markup=kb
        )

    await callback.answer()

# =========================
# PLUS
# =========================
@dp.callback_query_handler(
    lambda c: c.data.startswith("plus_")
)
async def plus_callback(callback: types.CallbackQuery):

    data = callback.data.replace("plus_", "")

    parts = data.rsplit("_", 2)

    name = parts[0]
    count = int(parts[1])
    category = parts[2]

    count += 1

    kb = InlineKeyboardMarkup(row_width=3)

    kb.row(
        InlineKeyboardButton(
            text="➖",
            callback_data=f"minus_{name}_{count}_{category}"
        ),

        InlineKeyboardButton(
            text=str(count),
            callback_data="count"
        ),

        InlineKeyboardButton(
            text="➕",
            callback_data=f"plus_{name}_{count}_{category}"
        )
    )

    kb.row(
        InlineKeyboardButton(
            text="🛒 Add to cart",
            callback_data=f"add_{name}_{count}"
        )
    )

    kb.row(
        InlineKeyboardButton(
            text="⬅ Back",
            callback_data=f"category_{category}"
        )
    )

    await callback.message.edit_reply_markup(
        reply_markup=kb
    )

    await callback.answer()
# =========================
# MINUS
# =========================

@dp.callback_query_handler(
    lambda c: c.data.startswith("minus_")
)
async def minus_callback(callback: types.CallbackQuery):

    data = callback.data.replace("minus_", "")

    parts = data.rsplit("_", 2)

    name = parts[0]
    count = int(parts[1])
    category = parts[2]

    if count > 1:
        count -= 1

    kb = InlineKeyboardMarkup(row_width=3)

    kb.row(
        InlineKeyboardButton(
            text="➖",
            callback_data=f"minus_{name}_{count}_{category}"
        ),

        InlineKeyboardButton(
            text=str(count),
            callback_data="count"
        ),

        InlineKeyboardButton(
            text="➕",
            callback_data=f"plus_{name}_{count}_{category}"
        )
    )

    kb.row(
        InlineKeyboardButton(
            text="🛒 Add to cart",
            callback_data=f"add_{name}_{count}"
        )
    )

    kb.row(
        InlineKeyboardButton(
            text="⬅ Back",
            callback_data=f"category_{category}"
        )
    )

    await callback.message.edit_reply_markup(
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

    data = callback.data.replace(
        "add_",
        ""
    )

    parts = data.rsplit("_", 1)

    product_name = parts[0]

    count = int(parts[1])

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

    price = price * count

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
        get_text(callback.from_user.id, "added_to_cart")
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
            get_text(callback.from_user.id, "cart_empty"),
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
        get_text(callback.from_user.id, "cart_cleared")
    )

    await callback.message.answer(
        "🏠 Main menu",
        reply_markup=inline_main_menu(callback.from_user.id)
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
        reply_markup=inline_main_menu(callback.from_user.id)
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

        order_text = f"🚨 NEW ORDER {mention}\n\n"

        total = 0

        for item in items:

            order_text += f"• {item[0]} — {item[1]} TL\n"

            total += item[1]

        order_text += f"\n💰 Total: {total} TL"

        order_text += f"\n\n📍 Address:\n{address}"

        order_text += f"\n\n📞 Phone:\n{phone}"

        order_text += f"\n\n🚪 Comment:\n{comment}"

        cur.execute(
            """
            INSERT INTO orders(
                user_id,
                order_text
            )
            VALUES(%s,%s)
            RETURNING id
            """,
            (
                user_id,
                order_text
            )
        )

        order_id = cur.fetchone()[0]

        conn.commit()

        kb = InlineKeyboardMarkup(row_width=2)

        kb.add(
            InlineKeyboardButton(
                text="🧑‍🍳 Preparing",
                callback_data=f"status_preparing_{order_id}"
            ),

            InlineKeyboardButton(
                text="🛵 Delivery",
                callback_data=f"status_delivery_{order_id}"
            )
        )

        kb.add(
            InlineKeyboardButton(
                text="✅ Completed",
                callback_data=f"status_completed_{order_id}"
            ),

            InlineKeyboardButton(
                text="❌ Cancelled",
                callback_data=f"status_cancelled_{order_id}"
            )
        )

        await bot.send_message(
            ADMIN_ID,
            order_text,
            reply_markup=kb
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
            reply_markup=inline_main_menu(message.from_user.id)
        )

        await state.finish()

    except Exception as e:

        conn.rollback()

        print(e)

        await message.answer(
            "❌ Order error"
        )
        
# =========================
# ORDER STATUS
# =========================

@dp.callback_query_handler(
    lambda c: c.data.startswith("status_")
)
async def order_status_callback(
    callback: types.CallbackQuery
):

    data = callback.data.split("_")

    status_type = data[1]

    order_id = data[2]

    if status_type == "preparing":

        new_status = "🧑‍🍳 Preparing"

    elif status_type == "delivery":

        new_status = "🛵 Delivery"

    elif status_type == "completed":

        new_status = "✅ Completed"

    elif status_type == "cancelled":

        new_status = "❌ Cancelled"

    else:

        return

    cur.execute(
        """
        UPDATE orders
        SET status=%s
        WHERE id=%s
        """,
        (
            new_status,
            order_id
        )
    )

    conn.commit()

    cur.execute(
        """
        SELECT user_id
        FROM orders
        WHERE id=%s
        """,
        (order_id,)
    )

    user = cur.fetchone()

    if user:

        user_id = user[0]

        try:

            await bot.send_message(
                user_id,
                f"📦 Order status updated:\n\n{new_status}"
            )

        except:
            pass

    await callback.answer(
        f"✅ {new_status}"
    )
    
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
