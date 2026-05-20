# main.py

```python
import logging
import os
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import psycopg2

# =========================
# CONFIG
# =========================

TOKEN = "8729557900:AAGQceOGd-V5erYJpSXV5M95wrFU_JeMd4Q"
ADMIN_ID = 1472777680

DATABASE_URL = "postgresql://postgres.gtglvcebuvuampyhtaze:YOUR_PASSWORD@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# =========================
# DB
# =========================

conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cur = conn.cursor()

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
    product_name TEXT,
    price INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS cart (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    product_name TEXT,
    price INTEGER
)
""")

conn.commit()

# =========================
# DEFAULT DATA
# =========================

try:
    cur.execute("SELECT COUNT(*) FROM categories")
    count = cur.fetchone()[0]

    if count == 0:
        cur.execute("INSERT INTO categories (name) VALUES (%s)", ("🌭 Hot Dogs",))
        cur.execute("INSERT INTO categories (name) VALUES (%s)", ("🌯 Shawarma",))
        cur.execute("INSERT INTO categories (name) VALUES (%s)", ("🥤 Drinks",))

        cur.execute(
            "INSERT INTO products (category, product_name, price) VALUES (%s,%s,%s)",
            ("🌭 Hot Dogs", "Classic Hot Dog", 150)
        )

        cur.execute(
            "INSERT INTO products (category, product_name, price) VALUES (%s,%s,%s)",
            ("🌭 Hot Dogs", "Cheese Hot Dog", 180)
        )

        cur.execute(
            "INSERT INTO products (category, product_name, price) VALUES (%s,%s,%s)",
            ("🌭 Hot Dogs", "Double Hot Dog", 220)
        )

        cur.execute(
            "INSERT INTO products (category, product_name, price) VALUES (%s,%s,%s)",
            ("🌯 Shawarma", "Chicken Shawarma", 200)
        )

        cur.execute(
            "INSERT INTO products (category, product_name, price) VALUES (%s,%s,%s)",
            ("🌯 Shawarma", "Big Shawarma", 260)
        )

        cur.execute(
            "INSERT INTO products (category, product_name, price) VALUES (%s,%s,%s)",
            ("🥤 Drinks", "Cola", 60)
        )

        cur.execute(
            "INSERT INTO products (category, product_name, price) VALUES (%s,%s,%s)",
            ("🥤 Drinks", "Ayran", 50)
        )

        conn.commit()

except Exception as e:
    conn.rollback()
    print(e)

# =========================
# FLASK KEEPALIVE
# =========================

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running!'


def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =========================
# MENUS
# =========================


def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    try:
        conn.rollback()

        cur.execute("SELECT name FROM categories")
        categories = cur.fetchall()

        for cat in categories:
            kb.add(KeyboardButton(cat[0]))

        kb.add(KeyboardButton("CART"))

        return kb

    except Exception as e:
        conn.rollback()
        print(e)
        return kb

# =========================
# START
# =========================

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        "🍔 Welcome to VAMO Cafe",
        reply_markup=main_menu()
    )

# =========================
# CART
# =========================

@dp.message_handler(lambda m: m.text == "CART")
async def cart(message: types.Message):

    try:
        user_id = message.from_user.id

        conn.rollback()

        cur.execute(
            "SELECT product_name, price FROM cart WHERE user_id=%s",
            (user_id,)
        )

        items = cur.fetchall()

        if not items:
            await message.answer("🛒 Cart is empty")
            return

        total = 0
        text = "🛒 YOUR CART\n\n"

        for item in items:
            text += f"• {item[0]} — {item[1]} TL\n"
            total += item[1]

        text += f"\n💰 Total: {total} TL"

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("CHECKOUT"))
        kb.add(KeyboardButton("BACK"))

        await message.answer(text, reply_markup=kb)

    except Exception as e:
        conn.rollback()
        print(e)
        await message.answer("❌ Cart error")

# =========================
# CHECKOUT
# =========================

@dp.message_handler(lambda m: m.text == "CHECKOUT")
async def checkout(message: types.Message):

    try:
        user_id = message.from_user.id

        conn.rollback()

        cur.execute(
            "SELECT product_name, price FROM cart WHERE user_id=%s",
            (user_id,)
        )

        items = cur.fetchall()

        if not items:
            await message.answer("Cart is empty")
            return

        total = sum(item[1] for item in items)

        text = "🛍 NEW ORDER\n\n"

        for item in items:
            text += f"• {item[0]} — {item[1]} TL\n"

        text += f"\n💰 Total: {total} TL"

        await bot.send_message(ADMIN_ID, text)

        cur.execute(
            "DELETE FROM cart WHERE user_id=%s",
            (user_id,)
        )

        conn.commit()

        await message.answer(
            "✅ Order sent successfully!",
            reply_markup=main_menu()
        )

    except Exception as e:

        conn.rollback()

        print(e)

        await message.answer(
            "❌ Checkout error"
        )

# =========================
# BACK
# =========================

@dp.message_handler(lambda m: m.text == "BACK")
async def back(message: types.Message):
    await message.answer(
        "⬅ Main menu",
        reply_markup=main_menu()
    )

# =========================
# UNIVERSAL CATEGORY / PRODUCT
# =========================

@dp.message_handler()
async def universal(message: types.Message):

    text = message.text
    user_id = message.from_user.id

    try:
        conn.rollback()

        # CATEGORY
        cur.execute(
            "SELECT name FROM categories WHERE name=%s",
            (text,)
        )

        category = cur.fetchone()

        if category:

            cur.execute(
                "SELECT product_name, price FROM products WHERE category=%s",
                (text,)
            )

            products = cur.fetchall()

            msg = f"{text}\n\n"

            kb = ReplyKeyboardMarkup(resize_keyboard=True)

            for product in products:
                msg += f"• {product[0]} — {product[1]} TL\n"
                kb.add(KeyboardButton(f"{product[0]} — {product[1]} TL"))

            kb.add(KeyboardButton("BACK"))

            await message.answer(msg, reply_markup=kb)
            return

        # PRODUCT
        cur.execute(
            "SELECT product_name, price FROM products"
        )

        products = cur.fetchall()

        for product in products:

            button_text = f"{product[0]} — {product[1]} TL"

            if text == button_text:

                cur.execute(
                    "INSERT INTO cart (user_id, product_name, price) VALUES (%s,%s,%s)",
                    (user_id, product[0], product[1])
                )

                conn.commit()

                await message.answer(
                    f"✅ Added to cart:\n{product[0]} — {product[1]} TL",
                    reply_markup=main_menu()
                )

                return

    except Exception as e:
        conn.rollback()
        print(e)
        await message.answer("❌ Error")

# =========================
# RUN
# =========================

if __name__ == '__main__':

    Thread(target=run_web).start()

    executor.start_polling(
        dp,
        skip_updates=True
    )
```

# requirements.txt

```txt
aiogram==2.25.1
Flask==3.0.3
psycopg2-binary==2.9.9
```

# Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```
