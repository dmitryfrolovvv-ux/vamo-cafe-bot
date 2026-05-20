from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

ADMIN_ID = 1472777680


# =========================
# FSM
# =========================

class AdminStates(StatesGroup):
    add_category = State()

    delete_category = State()

    add_product_category = State()
    add_product_name = State()
    add_product_price = State()

    delete_product = State()


# =========================
# KEYBOARD
# =========================

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


# =========================
# REGISTER
# =========================

def register_admin(dp, conn, cur):

    # =========================
    # ADMIN PANEL
    # =========================

    @dp.message_handler(commands=["admin"])
    async def admin_panel(message: types.Message):

        if message.from_user.id != ADMIN_ID:
            return

        await message.answer(
            "⚙ ADMIN PANEL",
            reply_markup=admin_menu()
        )

    # =========================
    # ADD CATEGORY
    # =========================

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

            await message.answer("✅ Category added")

        except Exception as e:

            conn.rollback()

            await message.answer(str(e))

        await state.finish()

    # =========================
    # DELETE CATEGORY
    # =========================

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

            conn.commit()

            await message.answer("✅ Category deleted")

        except Exception as e:

            conn.rollback()

            await message.answer(str(e))

        await state.finish()

    # =========================
    # ADD PRODUCT
    # =========================

    @dp.message_handler(lambda m: m.text == "➕ Add product")
    async def add_product_category(message: types.Message):

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

            await message.answer("✅ Product added")

        except Exception as e:

            conn.rollback()

            await message.answer(str(e))

        await state.finish()

    # =========================
    # DELETE PRODUCT
    # =========================

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

            await message.answer("✅ Product deleted")

        except Exception as e:

            conn.rollback()

            await message.answer(str(e))

        await state.finish()
