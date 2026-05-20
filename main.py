import logging
import psycopg2
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

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

user_carts = {}
admin_state = {}

# =========================================
# MAIN MENU
# =========================================

def main_menu():

    try:
        conn.rollback()
    except:
        pass

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    cur.execute("SELECT name FROM categories ORDER BY id")

    categories = cur.fetchall()

    for cat in categories:
        kb.add(KeyboardButton(cat[0]))

    kb.add(KeyboardButton("CART"))

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
async def admin_panel(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("➕ Add Category")
    kb.add("➕ Add Product")
    kb.add("❌ Delete Category")
    kb.add("📦 Orders")
    kb.add("📊 Statistics")
    kb.add("⬅ Back")

    await message.answer(
        "⚙ ADMIN PANEL",
        reply_markup=kb
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

    if text.upper() == "BACK" or text == "⬅ Back":

        await message.answer(
            "⬅ Main menu",
            reply_markup=main_menu()
        )

        return

    # =====================================
    # CART
    # =====================================

    if text.upper() == "CART":

        cart_items = user_carts.get(user_id, [])

        if not cart_items:

            await message.answer(
                "🛒 Cart is empty",
                reply_markup=main_menu()
            )

            return

        total = 0
        txt = "🛒 YOUR CART\n\n"

        for item in cart_items:

            txt += f"• {item}\n"

            try:

                price = int(
                    item.split("—")[1]
                    .replace("TL", "")
                    .strip()
                )

                total += price

            except:
                pass

        txt += f"\n💰 Total: {total} TL"

        kb = ReplyKeyboardMarkup(resize_keyboard=True)

        kb.add("CHECKOUT")
        kb.add("BACK")

        await message.answer(
            txt,
            reply_markup=kb
        )

        return

    # =====================================
    # CHECKOUT
    # =====================================

    if text.upper() == "CHECKOUT":

        try:

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

        except Exception as e:

            conn.rollback()

            print(e)

            await message.answer(
                "❌ Checkout error"
            )

        return

    # =====================================
    # ADMIN BUTTONS
    # =====================================

    if user_id == ADMIN_ID:

        if text == "➕ Add Category":

            admin_state[user_id] = "add_category"

            await message.answer("📂 Enter category name")

            return

        if text == "➕ Add Product":

            admin_state[user_id] = "product_category"

            cur.execute("SELECT name FROM categories")

            cats = cur.fetchall()

            kb = ReplyKeyboardMarkup(resize_keyboard=True)

            for c in cats:
                kb.add(c[0])

            await message.answer(
                "📂 Choose category",
                reply_markup=kb
            )

            return

        if text == "❌ Delete Category":

            admin_state[user_id] = "delete_category"

            cur.execute("SELECT name FROM categories")

            cats = cur.fetchall()

            kb = ReplyKeyboardMarkup(resize_keyboard=True)

            for c in cats:
                kb.add(c[0])

            await message.answer(
                "❌ Choose category",
                reply_markup=kb
            )

            return

        if text == "📦 Orders":

            cur.execute("""
            SELECT id, full_name, total
            FROM orders
            ORDER BY id DESC
            LIMIT 10
            """)

            orders = cur.fetchall()

            txt = "📦 LAST ORDERS\n\n"

            for o in orders:
                txt += f"#{o[0]} | {o[1]} | {o[2]} TL\n"

            await message.answer(txt)

            return

        if text == "📊 Statistics":

            cur.execute("SELECT COUNT(*) FROM orders")
            orders_count = cur.fetchone()[0]

            cur.execute("SELECT COALESCE(SUM(total),0) FROM orders")
            income = cur.fetchone()[0]

            txt = f"""
📊 Statistics

📦 Orders: {orders_count}
💰 Income: {income} TL
"""

            await message.answer(txt)

            return

    # =====================================
    # ADD CATEGORY
    # =====================================

    if admin_state.get(user_id) == "add_category":

        try:

            cur.execute(
                "INSERT INTO categories(name) VALUES(%s)",
                (text,)
            )

            conn.commit()

            await message.answer(
                "✅ Category added",
                reply_markup=main_menu()
            )

        except Exception as e:

            conn.rollback()

            print(e)

            await message.answer("❌ Error")

        admin_state[user_id] = None

        return

    # =====================================
    # DELETE CATEGORY
    # =====================================

    if admin_state.get(user_id) == "delete_category":

        try:

            cur.execute(
                "DELETE FROM products WHERE category=%s",
                (text,)
            )

            cur.execute(
                "DELETE FROM categories WHERE name=%s",
                (text,)
            )

            conn.commit()

            await message.answer(
                "✅ Category deleted",
                reply_markup=main_menu()
            )

        except Exception as e:

            conn.rollback()

            print(e)

        admin_state[user_id] = None

        return

    # =====================================
    # PRODUCT CATEGORY
    # =====================================

    if admin_state.get(user_id) == "product_category":

        admin_state["selected_category"] = text
        admin_state[user_id] = "product_name"

        await message.answer("🍔 Enter product name")

        return

    # =====================================
    # PRODUCT NAME
    # =====================================

    if admin_state.get(user_id) == "product_name":

        admin_state["product_name"] = text
        admin_state[user_id] = "product_price"

        await message.answer("💰 Enter price")

        return

    # =====================================
    # PRODUCT PRICE
    # =====================================

    if admin_state.get(user_id) == "product_price":

        try:

            price = int(text)

            cur.execute("""
            INSERT INTO products(category,name,price)
            VALUES(%s,%s,%s)
            """, (
                admin_state["selected_category"],
                admin_state["product_name"],
                price
            ))

            conn.commit()

            await message.answer(
                "✅ Product added",
                reply_markup=main_menu()
            )

        except Exception as e:

            conn.rollback()

            print(e)

            await message.answer("❌ Error")

        admin_state[user_id] = None

        return

    # =====================================
    # CATEGORY CLICK
    # =====================================

    try:

        cur.execute(
            "SELECT name, price FROM products WHERE category=%s",
            (text,)
        )

        products = cur.fetchall()

        if products:

            txt = f"🍔 {text}\n\n"

            kb = ReplyKeyboardMarkup(resize_keyboard=True)

            for p in products:

                product_text = f"{p[0]} — {p[1]} TL"

                txt += f"• {product_text}\n"

                kb.add(product_text)

            kb.add("BACK")

            await message.answer(
                txt,
                reply_markup=kb
            )

            return

    except Exception as e:

        conn.rollback()
        print(e)

    # =====================================
    # PRODUCT CLICK
    # =====================================

    try:

        cur.execute("SELECT name, price FROM products")

        products = cur.fetchall()

        for p in products:

            btn = f"{p[0]} — {p[1]} TL"

            if text == btn:

                if user_id not in user_carts:
                    user_carts[user_id] = []

                user_carts[user_id].append(btn)

                kb = ReplyKeyboardMarkup(resize_keyboard=True)

                kb.add("CART")
                kb.add("BACK")

                await message.answer(
                    f"✅ Added to cart:\n{btn}",
                    reply_markup=kb
                )

                return

    except Exception as e:

        conn.rollback()
        print(e)

# =========================================
# START POLLING
# =========================================

async def on_startup(dp):

    await bot.delete_webhook(
        drop_pending_updates=True
    )

if __name__ == "__main__":

    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup
    )
