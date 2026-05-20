import os
import logging
import threading
import psycopg2

from flask import Flask

from aiogram import Bot, Dispatcher, executor, types
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

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# =========================
# FLASK
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "VAMO BOT WORKING"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =========================
# DATABASE
# =========================

conn = psycopg2.connect(
    DATABASE_URL,
    sslmode="require"
)

cur = conn.cursor()

# =========================
# ORDERS TABLE
# =========================

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

# =========================
# PRODUCTS TABLE
# =========================

cur.execute("""
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    category TEXT,
    name TEXT,
    price INTEGER
)
""")

conn.commit()

# =========================
# DEFAULT PRODUCTS
# =========================

cur.execute("SELECT COUNT(*) FROM products")

count_products = cur.fetchone()[0]

if count_products == 0:

    default_products = [

        ("🌭 Hot Dogs", "Classic Hot Dog", 150),
        ("🌭 Hot Dogs", "Cheese Hot Dog", 180),
        ("🌭 Hot Dogs", "Double Hot Dog", 220),

        ("🌯 Shawarma", "Chicken Shawarma", 200),
        ("🌯 Shawarma", "Big Shawarma", 260),

        ("🥟 Chebureki", "Classic Chebureki", 140),
        ("🥟 Chebureki", "Cheese Chebureki", 160),
        ("🥟 Chebureki", "Meat Chebureki", 190),

        ("🥤 Drinks", "Cola", 60),
        ("🥤 Drinks", "Ayran", 50),
        ("🥤 Drinks", "Water", 30)

    ]

    for product in default_products:

        cur.execute("""
        INSERT INTO products (
            category,
            name,
            price
        )
        VALUES (%s,%s,%s)
        """, product)

    conn.commit()

# =========================
# LOAD MENU
# =========================

def load_menu():

    cur.execute("""
    SELECT category, name, price
    FROM products
    ORDER BY id
    """)

    rows = cur.fetchall()

    menu = {}

    for row in rows:

        category = row[0]
        name = row[1]
        price = row[2]

        if category not in menu:
            menu[category] = {}

        menu[category][name] = price

    return menu

menu = load_menu()

# =========================
# MEMORY
# =========================

user_cart = {}

waiting_phone = {}
waiting_address = {}
waiting_complex = {}
waiting_door = {}

user_data = {}

broadcast_mode = {}

adding_product = {}
deleting_product = {}
editing_price = {}

cafe_open = True

# =========================
# MAIN KEYBOARD
# =========================

def main_keyboard():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    for category in menu:
        kb.add(KeyboardButton(category))

    kb.add(KeyboardButton("🛒 Cart"))

    kb.add(KeyboardButton("🌐 Change Language"))

    return kb

# =========================
# START
# =========================

@dp.message_handler(commands=["start"])
async def start(message: types.Message):

    if not cafe_open:

        await message.answer(
            "❌ Cafe is temporarily closed."
        )

        return

    user_cart[message.from_user.id] = []

    await message.answer(
        "🍴 Welcome to VAMO Cafe!\n\nChoose category:",
        reply_markup=main_keyboard()
    )

# =========================
# CATEGORY
# =========================

@dp.message_handler(lambda message: message.text in menu)
async def category_handler(message: types.Message):

    category = message.text

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    text = f"{category} Menu\n\n"

    for item, price in menu[category].items():

        text += f"• {item} — {price} TL\n"

        kb.add(KeyboardButton(item))

    kb.add(KeyboardButton("🛒 Cart"))
    kb.add(KeyboardButton("⬅ Back"))

    await message.answer(
        text,
        reply_markup=kb
    )

# =========================
# BACK
# =========================

@dp.message_handler(lambda message: message.text == "⬅ Back")
async def back_handler(message: types.Message):

    await message.answer(
        "⬅ Returned to main menu",
        reply_markup=main_keyboard()
    )

# =========================
# ADD TO CART
# =========================

@dp.message_handler(lambda message: any(
    message.text in items for items in menu.values()
))
async def add_to_cart(message: types.Message):

    for category in menu.values():

        if message.text in category:

            item_name = message.text
            price = category[item_name]

            if message.from_user.id not in user_cart:
                user_cart[message.from_user.id] = []

            user_cart[message.from_user.id].append(
                (item_name, price)
            )

            await message.answer(
                f"✅ Added:\n{item_name} — {price} TL"
            )

            return

# =========================
# CART
# =========================

@dp.message_handler(lambda message: message.text == "🛒 Cart")
async def cart_handler(message: types.Message):

    cart = user_cart.get(message.from_user.id, [])

    if not cart:

        await message.answer(
            "🛒 Your cart is empty!"
        )

        return

    text = "🛒 Your Cart\n\n"

    total = 0

    for item, price in cart:

        text += f"• {item} — {price} TL\n"

        total += price

    text += f"\n💰 Total: {total} TL"

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("✅ Checkout"))
    kb.add(KeyboardButton("⬅ Back"))

    await message.answer(
        text,
        reply_markup=kb
    )

# =========================
# CHECKOUT
# =========================

@dp.message_handler(lambda message: message.text == "✅ Checkout")
async def checkout(message: types.Message):

    waiting_phone[message.from_user.id] = True

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("⬅ Back"))

    await message.answer(
        "📞 Send your phone number:\n\nExample:\n+905551112233",
        reply_markup=kb
    )

# =========================
# PHONE
# =========================

@dp.message_handler(lambda message:
    message.from_user.id in waiting_phone
)
async def phone_handler(message: types.Message):

    user_data[message.from_user.id] = {
        "phone": message.text
    }

    waiting_phone.pop(message.from_user.id)

    waiting_address[message.from_user.id] = True

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(
        KeyboardButton(
            "📍 Send Location",
            request_location=True
        )
    )

    kb.add(KeyboardButton("⏭ Skip"))

    await message.answer(
        "🏠 Send address or location:",
        reply_markup=kb
    )

# =========================
# LOCATION
# =========================

@dp.message_handler(content_types=["location"])
async def location_handler(message: types.Message):

    if message.from_user.id not in waiting_address:
        return

    lat = message.location.latitude
    lon = message.location.longitude

    user_data[message.from_user.id]["address"] = (
        f"https://maps.google.com/?q={lat},{lon}"
    )

    waiting_address.pop(message.from_user.id)

    waiting_complex[message.from_user.id] = True

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("⏭ Skip"))

    await message.answer(
        "🏢 Enter complex/building code:\n(optional)",
        reply_markup=kb
    )

# =========================
# ADDRESS
# =========================

@dp.message_handler(lambda message:
    message.from_user.id in waiting_address
)
async def address_handler(message: types.Message):

    if message.text == "⏭ Skip":

        user_data[message.from_user.id]["address"] = (
            "Not provided"
        )

    else:

        user_data[message.from_user.id]["address"] = (
            message.text
        )

    waiting_address.pop(message.from_user.id)

    waiting_complex[message.from_user.id] = True

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("⏭ Skip"))

    await message.answer(
        "🏢 Enter complex/building code:\n(optional)",
        reply_markup=kb
    )

# =========================
# COMPLEX CODE
# =========================

@dp.message_handler(lambda message:
    message.from_user.id in waiting_complex
)
async def complex_handler(message: types.Message):

    if message.text == "⏭ Skip":

        user_data[message.from_user.id]["complex"] = (
            "Not provided"
        )

    else:

        user_data[message.from_user.id]["complex"] = (
            message.text
        )

    waiting_complex.pop(message.from_user.id)

    waiting_door[message.from_user.id] = True

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("⏭ Skip"))

    await message.answer(
        "🚪 Enter door code:\n(optional)",
        reply_markup=kb
    )

# =========================
# DOOR CODE
# =========================

@dp.message_handler(lambda message:
    message.from_user.id in waiting_door
)
async def door_handler(message: types.Message):

    if message.text == "⏭ Skip":

        user_data[message.from_user.id]["door"] = (
            "Not provided"
        )

    else:

        user_data[message.from_user.id]["door"] = (
            message.text
        )

    waiting_door.pop(message.from_user.id)

    cart = user_cart.get(message.from_user.id, [])

    total = sum(price for _, price in cart)

    text = "📦 NEW ORDER\n\n"

    items_text = ""

    for item, price in cart:

        text += f"• {item} — {price} TL\n"

        items_text += f"{item} ({price} TL), "

    text += f"\n💰 Total: {total} TL"

    text += f"\n📞 Phone: {user_data[message.from_user.id]['phone']}"

    text += f"\n🏠 Address: {user_data[message.from_user.id]['address']}"

    text += f"\n🏢 Complex code: {user_data[message.from_user.id]['complex']}"

    text += f"\n🚪 Door code: {user_data[message.from_user.id]['door']}"

    text += f"\n\n👤 Client: {message.from_user.full_name}"

    text += f"\n🆔 ID: {message.from_user.id}"

    if message.from_user.username:

        text += f"\n🔗 Username: @{message.from_user.username}"

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
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
        items_text,
        total,
        user_data[message.from_user.id]["phone"],
        user_data[message.from_user.id]["address"],
        user_data[message.from_user.id]["complex"],
        user_data[message.from_user.id]["door"]
    ))

    conn.commit()

    await bot.send_message(
        ADMIN_ID,
        text
    )

    await message.answer(
        "✅ Order sent successfully!\n\nVAMO Cafe will contact you soon.",
        reply_markup=main_keyboard()
    )

    user_cart[message.from_user.id] = []

# =========================
# BIG ADMIN PANEL
# =========================

@dp.message_handler(commands=["admin"])
async def admin_panel(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(
        KeyboardButton("📦 Orders"),
        KeyboardButton("📊 Statistics")
    )

    kb.add(
        KeyboardButton("👥 Clients"),
        KeyboardButton("🍔 Menu")
    )

    kb.add(
        KeyboardButton("➕ Add Product"),
        KeyboardButton("❌ Delete Product")
    )

    kb.add(
        KeyboardButton("✏ Edit Price"),
        KeyboardButton("💰 Income Today")
    )

    kb.add(
        KeyboardButton("📈 Analytics"),
        KeyboardButton("📢 Broadcast")
    )

    kb.add(
        KeyboardButton("🟢 Cafe Status"),
        KeyboardButton("⭐ Reviews")
    )

    kb.add(
        KeyboardButton("🚫 Ban User")
    )

    kb.add(
        KeyboardButton("⬅ Back")
    )

    await message.answer(
        "⚙ BIG ADMIN PANEL",
        reply_markup=kb
    )

# =========================
# ADD PRODUCT
# =========================

@dp.message_handler(lambda message:
    message.text == "➕ Add Product"
)
async def add_product_start(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    adding_product[message.from_user.id] = {}

    await message.answer(
        "📂 Enter category:"
    )

# =========================
# ADD PRODUCT FLOW
# =========================

@dp.message_handler(lambda message:
    message.from_user.id in adding_product
)
async def add_product_flow(message: types.Message):

    data = adding_product[message.from_user.id]

    if "category" not in data:

        data["category"] = message.text

        await message.answer(
            "🍔 Enter product name:"
        )

        return

    if "name" not in data:

        data["name"] = message.text

        await message.answer(
            "💰 Enter product price:"
        )

        return

    if "price" not in data:

        try:
            price = int(message.text)

        except:

            await message.answer(
                "❌ Enter only number"
            )

            return

        data["price"] = price

        cur.execute("""
        INSERT INTO products (
            category,
            name,
            price
        )
        VALUES (%s,%s,%s)
        """, (
            data["category"],
            data["name"],
            data["price"]
        ))

        conn.commit()

        global menu

        menu = load_menu()

        adding_product.pop(message.from_user.id)

        await message.answer(
            "✅ Product added"
        )

# =========================
# DELETE PRODUCT
# =========================

@dp.message_handler(lambda message:
    message.text == "❌ Delete Product"
)
async def delete_product_start(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    cur.execute("""
    SELECT id, name, price
    FROM products
    ORDER BY id
    """)

    products = cur.fetchall()

    text = "❌ PRODUCTS\n\n"

    for product in products:

        text += (
            f"{product[0]}. "
            f"{product[1]} — "
            f"{product[2]} TL\n"
        )

    deleting_product[message.from_user.id] = True

    await message.answer(
        text + "\n\nSend product ID:"
    )

# =========================
# DELETE FLOW
# =========================

@dp.message_handler(lambda message:
    message.from_user.id in deleting_product
)
async def delete_product_flow(message: types.Message):

    try:

        product_id = int(message.text)

    except:

        await message.answer(
            "❌ Invalid ID"
        )

        return

    cur.execute("""
    DELETE FROM products
    WHERE id=%s
    """, (product_id,))

    conn.commit()

    global menu

    menu = load_menu()

    deleting_product.pop(message.from_user.id)

    await message.answer(
        "✅ Product deleted"
    )
