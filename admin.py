```python
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

    delete_category = State()

    add_product_category = State()

    add_product_name = State()

    add_product_price = State()

    delete_product = State()

# =========================
# MENU
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

def register_admin(dp, conn, cur):

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
            "⬅ Back",
            reply_markup=admin_menu()
        )

    # =====================
    # ADD CATEGORY
    # =====================

    @dp.message_handler(lambda m: m.text == "➕ Add category", state="*")
    async def add_category_start(message: types.Message, state: FSMContext):

        if message.from_user.id != ADMIN_ID:
            return

        await state.finish()

        await message.answer("🗂 Enter category name")

        await AdminStates.add_category.set()

    @dp.message_handler(state=AdminStates.add_category)
    async def add_category_finish(message: types.Message, state: FSMContext):

        category = message.text

        try:

            cur.execute(
                "INSERT INTO categories(name) VALUES(%s)",
                (category,)
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
    async def delete_category_start(message: types.Message, state: FSMContext):

        if message.from_user.id != ADMIN_ID:
            return

        await state.finish()

        await message.answer("🗑 Enter category name")

        await AdminStates.delete_category.set()

    @dp.message_handler(state=AdminStates.delete_category)
    async def delete_category_finish(message: types.Message, state: FSMContext):

        category = message.text

        try:

            cur.execute(
                "DELETE FROM categories WHERE name=%s",
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

        await state.finish()

    # =====================
    # ADD PRODUCT
    # =====================

    @dp.message_handler(lambda m: m.text == "➕ Add product", state="*")
    async def add_product_start(message: types.Message, state: FSMContext):

        if message.from_user.id != ADMIN_ID:
            return

        await state.finish()

        await message.answer("📂 Enter category")

        await AdminStates.add_product_category.set()

    @dp.message_handler(state=AdminStates.add_product_category)
    async def add_product_category(message: types.Message, state: FSMContext):

        await state.update_data(category=message.text)

        await message.answer("🍔 Enter product name")

        await AdminStates.add_product_name.set()

    @dp.message_handler(state=AdminStates.add_product_name)
    async def add_product_name(message: types.Message, state: FSMContext):

        await state.update_data(name=message.text)

        await message.answer("💰 Enter product price")

        await AdminStates.add_product_price.set()

    @dp.message_handler(state=AdminStates.add_product_price)
    async def add_product_price(message: types.Message, state: FSMContext):

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
                (category, name, price)
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
    async def delete_product_start(message: types.Message, state: FSMContext):

        if message.from_user.id != ADMIN_ID:
            return

        await state.finish()

        await message.answer("🗑 Enter product name")

        await AdminStates.delete_product.set()

    @dp.message_handler(state=AdminStates.delete_product)
    async def delete_product_finish(message: types.Message, state: FSMContext):

        product = message.text

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

        await state.finish()

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
                "SELECT order_text FROM orders ORDER BY id DESC LIMIT 10"
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

            cur.execute("SELECT COUNT(*) FROM orders")

            orders_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT user_id) FROM orders")

            users_count = cur.fetchone()[0]

            await message.answer(
                f"📊 STATS\n\n"
                f"📦 Orders: {orders_count}\n"
                f"👤 Users: {users_count}"
            )

        except Exception as e:

            conn.rollback()

            await message.answer(str(e))
```
