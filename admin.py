from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

ADMIN_ID = 1472777680


# =========================
# STATES
# =========================

class AdminStates(StatesGroup):

    add_category = State()

    add_product_category = State()

    add_product_name = State()

    add_product_price = State()


# =========================
# ADMIN MENU
# =========================

def admin_menu():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("➕ Add category"))

    kb.add(KeyboardButton("❌ Delete category"))

    kb.add(KeyboardButton("➕ Add product"))

    kb.add(KeyboardButton("❌ Delete product"))

    kb.add(KeyboardButton("📦 Orders"))

    kb.add(KeyboardButton("📊 Stats"))

    kb.add(KeyboardButton("⬅ Back"))

    return kb


# =========================
# REGISTER
# =========================

def register_admin(dp, conn, cur, main_menu):

    # =====================
    # ADMIN PANEL
    # =====================

    @dp.message_handler(commands=["admin"], state="*")
    async def admin_panel(message: types.Message, state: FSMContext):

        if message.from_user.id != ADMIN_ID:
            return

        await state.finish()

        await message.answer(
            "⚙ ADMIN PANEL",
            reply_markup=admin_menu()
        )

    # =====================
    # BACK
    # =====================

    @dp.message_handler(lambda m: m.text == "⬅ Back", state="*")
    async def admin_back(message: types.Message, state: FSMContext):

        if message.from_user.id != ADMIN_ID:
            return

        await state.finish()

        await message.answer(
            "🏠 Main menu",
            reply_markup=main_menu()
        )

    # =====================
    # ADD CATEGORY
    # =====================

    @dp.message_handler(lambda m: m.text == "➕ Add category", state="*")
    async def add_category_start(message: types.Message, state: FSMContext):

        if message.from_user.id != ADMIN_ID:
            return

        await state.finish()

        await message.answer(
            "🗂 Enter category name"
        )

        await AdminStates.add_category.set()

    @dp.message_handler(state=AdminStates.add_category)
    async def add_category_finish(message: types.Message, state: FSMContext):

        forbidden = [
            "⬅ Back",
            "📦 Orders",
            "📊 Stats",
            "➕ Add category",
            "❌ Delete category",
            "➕ Add product",
            "❌ Delete product"
        ]

        if message.text in forbidden:

            await message.answer(
                "❌ Enter category name manually"
            )

            return

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

    # =====================
    # DELETE CATEGORY
    # =====================

    @dp.message_handler(lambda m: m.text == "❌ Delete category", state="*")
    async def delete_category_menu(message: types.Message, state: FSMContext):

        if message.from_user.id != ADMIN_ID:
            return

        await state.finish()

        cur.execute(
            "SELECT name FROM categories"
        )

        categories = cur.fetchall()

        if not categories:

            await message.answer("❌ No categories")

            return

        kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for category in categories:

            kb.add(
                KeyboardButton(
                    f"🗑 {category[0]}"
                )
            )

        kb.add(
            KeyboardButton("⬅ Back")
        )

        await message.answer(
            "🗑 Select category to delete",
            reply_markup=kb
        )

    @dp.message_handler(lambda m: m.text.startswith("🗑 "), state="*")
    async def delete_category_finish(message: types.Message):

        if message.from_user.id != ADMIN_ID:
            return

        category = message.text.replace("🗑 ", "")

        try:

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

        except Exception as e:

            conn.rollback()

            await message.answer(str(e))

    # =====================
    # ADD PRODUCT
    # =====================

    @dp.message_handler(lambda m: m.text == "➕ Add product", state="*")
    async def add_product_start(message: types.Message, state: FSMContext):

        if message.from_user.id != ADMIN_ID:
            return

        await state.finish()

        cur.execute(
            "SELECT name FROM categories"
        )

        categories = cur.fetchall()

        if not categories:

            await message.answer("❌ No categories")

            return

        kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for category in categories:

            kb.add(
                KeyboardButton(category[0])
            )

        kb.add(
            KeyboardButton("⬅ Back")
        )

        await message.answer(
            "📂 Select category",
            reply_markup=kb
        )

        await AdminStates.add_product_category.set()

    @dp.message_handler(state=AdminStates.add_product_category)
    async def add_product_category(message: types.Message, state: FSMContext):

        forbidden = [
            "📦 Orders",
            "📊 Stats",
            "➕ Add category",
            "❌ Delete category",
            "➕ Add product",
            "❌ Delete product"
        ]

        if message.text in forbidden:

            await message.answer(
                "❌ Select category only"
            )

            return

        await state.update_data(
            category=message.text
        )

        await message.answer(
            "🍔 Enter product name"
        )

        await AdminStates.add_product_name.set()

    @dp.message_handler(state=AdminStates.add_product_name)
    async def add_product_name(message: types.Message, state: FSMContext):

        forbidden = [
            "⬅ Back",
            "📦 Orders",
            "📊 Stats",
            "➕ Add category",
            "❌ Delete category",
            "➕ Add product",
            "❌ Delete product"
        ]

        if message.text in forbidden:

            await message.answer(
                "❌ Enter product name manually"
            )

            return

        await state.update_data(
            name=message.text
        )

        await message.answer(
            "💰 Enter product price"
        )

        await AdminStates.add_product_price.set()

    @dp.message_handler(state=AdminStates.add_product_price)
    async def add_product_price(message: types.Message, state: FSMContext):

        if not message.text.isdigit():

            await message.answer(
                "❌ Enter only number"
            )

            return

        try:

            price = int(message.text)

            data = await state.get_data()

            category = data["category"]

            name = data["name"]

            cur.execute(
                """
                INSERT INTO products(category, name, price)
                VALUES(%s,%s,%s)
                """,
                (
                    category,
                    name,
                    price
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

    # =====================
    # DELETE PRODUCT
    # =====================

    @dp.message_handler(lambda m: m.text == "❌ Delete product", state="*")
    async def delete_product_menu(message: types.Message, state: FSMContext):

        if message.from_user.id != ADMIN_ID:
            return

        await state.finish()

        cur.execute(
            "SELECT name FROM products"
        )

        products = cur.fetchall()

        if not products:

            await message.answer("❌ No products")

            return

        kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for product in products:

            kb.add(
                KeyboardButton(
                    f"🗑 {product[0]}"
                )
            )

        kb.add(
            KeyboardButton("⬅ Back")
        )

        await message.answer(
            "🗑 Select product to delete",
            reply_markup=kb
        )

    @dp.message_handler(lambda m: m.text.startswith("🗑 "), state="*")
    async def delete_product_finish(message: types.Message):

        if message.from_user.id != ADMIN_ID:
            return

        product = message.text.replace("🗑 ", "")

        try:

            cur.execute(
                "DELETE FROM products WHERE name=%s",
                (product,)
            )

            conn.commit()

            await message.answer(
                "✅ Product deleted",
                reply_markup=admin_menu()
            )

        except Exception as e:

            conn.rollback()

            await message.answer(str(e))

    # =====================
    # ORDERS
    # =====================

    @dp.message_handler(lambda m: m.text == "📦 Orders", state="*")
    async def orders_handler(message: types.Message, state: FSMContext):

        if message.from_user.id != ADMIN_ID:
            return

        await state.finish()

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

                await message.answer("📭 No orders")

                return

            for order in orders:

                await message.answer(order[0])

        except Exception as e:

            conn.rollback()

            await message.answer(str(e))

    # =====================
    # STATS
    # =====================

    @dp.message_handler(lambda m: m.text == "📊 Stats", state="*")
    async def stats_handler(message: types.Message, state: FSMContext):

        if message.from_user.id != ADMIN_ID:
            return

        await state.finish()

        try:

            cur.execute(
                "SELECT COUNT(*) FROM orders"
            )

            orders_count = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM products"
            )

            products_count = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM categories"
            )

            categories_count = cur.fetchone()[0]

            await message.answer(
                f"📊 STATS\n\n"
                f"📦 Orders: {orders_count}\n"
                f"🍔 Products: {products_count}\n"
                f"📂 Categories: {categories_count}"
            )

        except Exception as e:

            conn.rollback()

            await message.answer(str(e))
