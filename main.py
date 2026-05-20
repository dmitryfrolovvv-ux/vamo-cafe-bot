import logging
import psycopg2

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from flask import Flask
from threading import Thread

# =========================================
# CONFIG
# =========================================

TOKEN = "8729557900:AAGQceOGd-V5erYJpSXV5M95wrFU_JeMd4Q"

ADMIN_ID = 1472777680

DATABASE_URL = "postgresql://postgres.gtglvcebuvuampyhtaze:froLOV580530.@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

# =========================================
# LOGGING
# =========================================

logging.basicConfig(level=logging.INFO)

# =========================================
# BOT
# =========================================

bot = Bot(token=TOKEN)

dp = Dispatcher(bot)

# =========================================
# FLASK
# =========================================

app = Flask(__name__)

@app.route("/")
def home():
    return "VAMO BOT WORKING"

def run_web():
    app.run(
        host="0.0.0.0",
        port=10000
    )

Thread(target=run_web).start()

# =========================================
# DATABASE
# =========================================

conn = psycopg2.connect(
    DATABASE_URL,
    sslmode="require"
)

cur = conn.cursor()

# =========================================
# TABLES
# =========================================

cur.execute("""
CREATE TABLE IF NOT EXISTS categories(
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS products(
    id SERIAL PRIMARY KEY,
    category TEXT,
    name TEXT,
    price INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders(
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    username TEXT,
    full_name TEXT,
    products TEXT,
    total INTEGER
)
""")

conn.commit()

# =========================================
# MEMORY
# =========================================

admin_states = {}

user_carts = {}

# =========================================
# MAIN MENU
# =========================================

def main_menu():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    cur.execute("SELECT name FROM categories")

    categories = cur.fetchall()

    for cat in categories:

        kb.add(
            KeyboardButton(cat[0])
        )

    kb.add(
        KeyboardButton("🛒 Cart")
    )

    return kb

# =========================================
# ADMIN MENU
# =========================================

def admin_menu():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(
        KeyboardButton("➕ Add Category")
    )

    kb.add(
        KeyboardButton("❌ Delete Category")
    )

    kb.add(
        KeyboardButton("➕ Add Product")
    )

    kb.add(
        KeyboardButton("📦 Orders")
    )

    kb.add(
        KeyboardButton("📊 Statistics")
    )

    kb.add(
        KeyboardButton("⬅ Back")
    )

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
# UNIVERSAL
# =========================================

@dp.message_handler()
async def universal(message: types.Message):

    user_id = message.from_user.id

    text = message.text.strip()

    # =====================================
    # BACK
    # =====================================

    if text == "⬅ Back":

        await message.answer(
            "⬅ Main menu",
            reply_markup=main_menu()
        )

        return

    # =====================================
    # CART
    # =====================================

    if text == "🛒 Cart":

        cart_items = user_carts.get(user_id, [])

        if not cart_items:

            await message.answer(
                "🛒 Cart is empty",
                reply_markup=main_menu()
            )

            return

        total = 0

        cart_text = "🛒 YOUR CART\n\n"

        for item in cart_items:

            cart_text += f"• {item}\n"

            try:

                price = int(
                    item.split("—")[1]
                    .replace("TL", "")
                    .strip()
                )

                total += price

            except:
                pass

        cart_text += f"\n💰 Total: {total} TL"

        kb = ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        kb.add(
            KeyboardButton("✅ Checkout")
        )

        kb.add(
            KeyboardButton("⬅ Back")
        )

        await message.answer(
            cart_text,
            reply_markup=kb
        )

        return

    # =====================================
    # CHECKOUT
    # =====================================

    if "Checkout" in text:

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
        INSERT INTO orders(
            user_id,
            username,
            full_name,
            products,
            total
        )
        VALUES(%s,%s,%s,%s,%s)
        """, (
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
            products_text,
            total
        ))

        conn.commit()

        await bot.send_message(
            ADMIN_ID,
            f"""
🔥 NEW ORDER

👤 Client: {message.from_user.full_name}
🆔 ID: {message.from_user.id}

📦 Products:
{products_text}

💰 Total: {total} TL
"""
        )

        user_carts[user_id] = []

        await message.answer(
            "✅ Order confirmed!\n\nVAMO Cafe will contact you soon.",
            reply_markup=main_menu()
        )

        return

    # =====================================
    # ADD CATEGORY
    # =====================================

    if text == "➕ Add Category":

        admin_states[user_id] = "add_category"

        await message.answer(
            "📂 Enter category name"
        )

        return

    # =====================================
    # DELETE CATEGORY
    # =====================================

    if text == "❌ Delete Category":

        cur.execute("SELECT name FROM categories")

        cats = cur.fetchall()

        kb = ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        for cat in cats:

            kb.add(
                KeyboardButton(f"DELETE {cat[0]}")
            )

        kb.add(
            KeyboardButton("⬅ Back")
        )

        await message.answer(
            "❌ Select category",
            reply_markup=kb
        )

        return

    # =====================================
    # DELETE CATEGORY CLICK
    # =====================================

    if text.startswith("DELETE "):

        category = text.replace("DELETE ", "")

        cur.execute(
            "DELETE FROM categories WHERE name=%s",
            (category,)
        )

        cur.execute(
            "DELETE FROM products WHERE category=%s",
            (category,)
        )

        conn.commit()

        await message.answer(
            "✅ Category deleted",
            reply_markup=admin_menu()
        )

        return

    # =====================================
    # ADD PRODUCT
    # =====================================

    if text == "➕ Add Product":

        cur.execute("SELECT name FROM categories")

        cats = cur.fetchall()

        kb = ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        for cat in cats:

            kb.add(
                KeyboardButton(cat[0])
            )

        kb.add(
            KeyboardButton("⬅ Back")
        )

        admin_states[user_id] = "choose_category"

        await message.answer(
            "📂 Select category",
            reply_markup=kb
        )

        return

    # =====================================
    # ADMIN STATES
    # =====================================

    state = admin_states.get(user_id)

    if state == "add_category":

        cur.execute(
            "INSERT INTO categories(name) VALUES(%s)",
            (text,)
        )

        conn.commit()

        admin_states.pop(user_id)

        await message.answer(
            "✅ Category added",
            reply_markup=admin_menu()
        )

        return

    # =====================================
    # CHOOSE CATEGORY
    # =====================================

    if state == "choose_category":

        admin_states[user_id] = {
            "step": "product_name",
            "category": text
        }

        await message.answer(
            "🍔 Enter product name"
        )

        return

    # =====================================
    # PRODUCT NAME
    # =====================================

    if isinstance(state, dict):

        if state["step"] == "product_name":

            state["name"] = text

            state["step"] = "product_price"

            await message.answer(
                "💰 Enter price"
            )

            return

        elif state["step"] == "product_price":

            try:

                price = int(text)

            except:

                await message.answer(
                    "❌ Enter number"
                )

                return

            cur.execute("""
            INSERT INTO products(
                category,
                name,
                price
            )
            VALUES(%s,%s,%s)
            """, (
                state["category"],
                state["name"],
                price
            ))

            conn.commit()

            admin_states.pop(user_id)

            await message.answer(
                "✅ Product added",
                reply_markup=admin_menu()
            )

            return

    # =====================================
    # ORDERS
    # =====================================

    if text == "📦 Orders":

        cur.execute("""
        SELECT full_name,total
        FROM orders
        ORDER BY id DESC
        LIMIT 10
        """)

        orders = cur.fetchall()

        if not orders:

            await message.answer("❌ No orders")
            return

        msg = "📦 LAST ORDERS\n\n"

        for order in orders:

            msg += f"{order[0]} | {order[1]} TL\n"

        await message.answer(msg)

        return

    # =====================================
    # STATS
    # =====================================

    if text == "📊 Statistics":

        cur.execute("SELECT COUNT(*) FROM orders")

        orders = cur.fetchone()[0]

        cur.execute(
            "SELECT COALESCE(SUM(total),0) FROM orders"
        )

        income = cur.fetchone()[0]

        await message.answer(
            f"""
📊 Statistics

📦 Orders: {orders}

💰 Income: {income} TL
"""
        )

        return

    # =====================================
    # CATEGORY CLICK
    # =====================================

    cur.execute(
        "SELECT name,price FROM products WHERE category=%s",
        (text,)
    )

    products = cur.fetchall()

    if products:

        kb = ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        msg = f"🍔 {text}\n\n"

        for p in products:

            btn = f"{p[0]} — {p[1]} TL"

            msg += f"• {btn}\n"

            kb.add(
                KeyboardButton(btn)
            )

        kb.add(
            KeyboardButton("⬅ Back")
        )

        await message.answer(
            msg,
            reply_markup=kb
        )

        return

    # =====================================
    # PRODUCT CLICK
    # =====================================

    cur.execute(
        "SELECT name,price FROM products"
    )

    all_products = cur.fetchall()

    for p in all_products:

        btn = f"{p[0]} — {p[1]} TL"

        if text == btn:

            if user_id not in user_carts:
                user_carts[user_id] = []

            user_carts[user_id].append(btn)

            await message.answer(
                f"✅ Added to cart:\n{btn}",
                reply_markup=main_menu()
            )

            return

# =========================================
# RUN
# =========================================

if __name__ == "__main__":

    executor.start_polling(
        dp,
        skip_updates=True,
        timeout=60
    )
