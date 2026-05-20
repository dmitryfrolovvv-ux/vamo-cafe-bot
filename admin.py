# =========================================
# ADMIN.PY
# =========================================

from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

ADMIN_ID = 1472777680

# =========================================
# STATES
# =========================================

class AdminStates(StatesGroup):

    add_category = State()

    delete_category = State()

    add_product_category = State()
    add_product_name = State()
    add_product_price = State()

    delete_product = State()

# =========================================
# MENU
# =========================================

def admin_menu():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("➕ Add category"))
    kb.add(KeyboardButton("➖ Delete category"))

    kb.add(KeyboardButton("➕ Add product"))
    kb.add(KeyboardButton("➖ Delete product"))

    kb.add(KeyboardButton("📦 Orders"))
    kb.add(KeyboardButton("📊 Stats"))

    kb.add(KeyboardButton("⬅ Back"))

    return kb

# =========================================
# REGISTER
# =========================================

def register_admin(dp, conn, cur):

    # =====================================
    # ADMIN PANEL
    # =====================================

    @dp.message_handler(commands=["admin"])
    async def admin_panel(message: types.Message):

        if message.from_user.id != ADMIN_ID:
            return

        await message.answer(
            "⚙ ADMIN PANEL",
            reply_markup=admin_menu()
        )

    # =====================================
    # ADD CATEGORY
    # =====================================

    @dp.message_handler(lambda m: m.text == "➕ Add category")
    async def add_category_start(message: types.Message):

        await AdminStates.add_category.set()

        await message.answer("📂 Enter category name")

    @dp.message_handler(state=AdminStates.add_category)
    async def add_category_finish(message: types.Message, state: FSMContext):

        try:

            cur.execute(
                "INSERT INTO categories(name) VALUES(%s)",
                (message.text,)
            )

            conn.commit()

            await message.answer(
                "✅ Category added",
                reply_markup=admin_menu()
            )

        except Exception as e:

            conn.rollback()

            await message.answer(str(e))

        await state.finish()

    # =====================================
    # DELETE CATEGORY
    # =====================================

    @dp.message_handler(lambda m: m.text == "➖ Delete category")
    async def delete_category_start(message: types.Message):

        await AdminStates.delete_category.set()

        await message.answer("🗑 Enter category name")

    @dp.message_handler(state=AdminStates.delete_category)
    async def delete_category_finish(message: types.Message, state: FSMContext):

        try:

            cur.execute(
                "DELETE FROM categories WHERE name=%s",
                (message.text,)
            )

            cur.execute(
                "DELETE FROM products WHERE category=%s",
                (message.text,)
            )

            conn.commit()

            await message.answer(
                "✅ Category deleted",
                reply_markup=admin_menu()
            )

        except Exception as e:

            conn.rollback()

            await message.answer(str(e))

        await state.finish()

    # =====================================
    # ADD PRODUCT
    # =====================================

    @dp.message_handler(lambda m: m.text == "➕ Add product")
    async def add_product_start(message: types.Message):

        await AdminStates.add_product_category.set()

        await message.answer("📂 Enter category")

    @dp.message_handler(state=AdminStates.add_product_category)
    async def add_product_name(message: types.Message, state: FSMContext):

        await state.update_data(category=message.text)

        await AdminStates.add_product_name.set()

        await message.answer("🍔 Enter product name")

    @dp.message_handler(state=AdminStates.add_product_name)
    async def add_product_price(message: types.Message, state: FSMContext):

        await state.update_data(product_name=message.text)

        await AdminStates.add_product_price.set()

        await message.answer("💰 Enter product price")

    @dp.message_handler(state=AdminStates.add_product_price)
    async def add_product_finish(message: types.Message, state: FSMContext):

        data = await state.get_data()

        try:

            cur.execute(
                """
                INSERT INTO products(category, product_name, price)
                VALUES(%s,%s,%s)
                """,
                (
                    data["category"],
                    data["product_name"],
                    int(message.text)
                )
            )

            conn.commit()

            await message.answer(
                "✅ Product added",
                reply_markup=admin_menu()
            )

        except Exception as e:

            conn.rollback()

            await message.answer(str(e))

        await state.finish()

    # =====================================
    # DELETE PRODUCT
    # =====================================

    @dp.message_handler(lambda m: m.text == "➖ Delete product")
    async def delete_product_start(message: types.Message):

        await AdminStates.delete_product.set()

        await message.answer("🗑 Enter product name")

    @dp.message_handler(state=AdminStates.delete_product)
    async def delete_product_finish(message: types.Message, state: FSMContext):

        try:

            cur.execute(
                "DELETE FROM products WHERE product_name=%s",
                (message.text,)
            )

            conn.commit()

            await message.answer(
                "✅ Product deleted",
                reply_markup=admin_menu()
            )

        except Exception as e:

            conn.rollback()

            await message.answer(str(e))

        await state.finish()

    # =====================================
    # ORDERS
    # =====================================

    @dp.message_handler(lambda m: m.text == "📦 Orders")
    async def orders(message: types.Message):

        if message.from_user.id != ADMIN_ID:
            return

        try:

            cur.execute(
                """
                SELECT order_text
                FROM orders
                ORDER BY id DESC
                LIMIT 10
                """
            )

            orders = cur.fetchall()

            if not orders:

                await message.answer("❌ No orders")

                return

            text = "📦 LAST ORDERS\n\n"

            for order in orders:

                text += order[0] + "\n\n"

            await message.answer(text)

        except Exception as e:

            conn.rollback()

            await message.answer(str(e))

    # =====================================
    # STATS
    # =====================================

    @dp.message_handler(lambda m: m.text == "📊 Stats")
    async def stats(message: types.Message):

        if message.from_user.id != ADMIN_ID:
            return

        try:

            cur.execute(
                "SELECT COUNT(*) FROM orders"
            )

            orders_count = cur.fetchone()[0]

            cur.execute(
                """
                SELECT COUNT(*)
                FROM products
                """
            )

            products_count = cur.fetchone()[0]

            cur.execute(
                """
                SELECT COUNT(*)
                FROM categories
                """
            )

            categories_count = cur.fetchone()[0]

            text = f"""
📊 STATISTICS

📦 Orders: {orders_count}

🍔 Products: {products_count}

📂 Categories: {categories_count}
"""

            await message.answer(text)

        except Exception as e:

            conn.rollback()

            await message.answer(str(e))
