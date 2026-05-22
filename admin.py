from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)

ADMIN_ID = 1472777680


# =========================
# STATES
# =========================

class AdminStates(StatesGroup):

    add_category = State()

    add_product_category = State()

    add_product_name = State()

    add_product_price = State()

    add_product_description = State()

    add_product_photo = State()

    deleting_category = State()

    deleting_product = State()
    
    edit_category_banner = State()

    waiting_banner_photo = State()
    
    remove_category_banner = State()

# =========================
# ADMIN MENU
# =========================

def admin_menu():

    kb = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.add(
        KeyboardButton("➕ Add category"),
        KeyboardButton("❌ Delete category")
    )

    kb.add(
        KeyboardButton("➕ Add product"),
        KeyboardButton("❌ Delete product")
    )
    
    kb.add(
        KeyboardButton("🖼 Edit category banner"),
        KeyboardButton("📂 Category editor")
    )

    kb.add(
        KeyboardButton("📦 Orders"),
        KeyboardButton("📊 Stats")
    )

    kb.add(
        KeyboardButton("♻ Reset"),
        KeyboardButton("⬅ Back")
    )

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
    # RESET
    # =====================

    @dp.message_handler(lambda m: "Reset" in m.text, state="*")
    async def reset_btn(message: types.Message, state: FSMContext):

        if message.from_user.id != ADMIN_ID:
            return

        await state.finish()

        await message.answer(
            "✅ State reset",
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

        try:

            cur.execute(
                """
                INSERT INTO categories(name)
                VALUES(%s)
                """,
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
            """
            SELECT name
            FROM categories
            """
        )

        categories = cur.fetchall()

        if not categories:

            await message.answer(
                "❌ No categories"
            )

            return

        kb = ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        for category in categories:

            kb.add(
                KeyboardButton(
                    f"🗑 CATEGORY {category[0]}"
                )
            )

        kb.add(
            KeyboardButton("⬅ Back")
        )

        await message.answer(
            "🗑 Select category",
            reply_markup=kb
        )

        await AdminStates.deleting_category.set()

    @dp.message_handler(
        lambda m: m.text.startswith("🗑 CATEGORY "),
        state=AdminStates.deleting_category
    )
    async def delete_category_finish(message: types.Message, state: FSMContext):

        category = message.text.replace(
            "🗑 CATEGORY ",
            ""
        )

        try:

            cur.execute(
                """
                DELETE FROM products
                WHERE category=%s
                """,
                (category,)
            )

            cur.execute(
                """
                DELETE FROM categories
                WHERE name=%s
                """,
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

        cur.execute(
            """
            SELECT name
            FROM categories
            """
        )

        categories = cur.fetchall()

        if not categories:

            await message.answer(
                "❌ No categories"
            )

            return

        kb = ReplyKeyboardMarkup(
            resize_keyboard=True
        )

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

        await state.update_data(
            category=message.text
        )

        await message.answer(
            "🍔 Enter product name"
        )

        await AdminStates.add_product_name.set()

    @dp.message_handler(state=AdminStates.add_product_name)
    async def add_product_name(message: types.Message, state: FSMContext):

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

        await state.update_data(
            price=int(message.text)
        )

        await message.answer(
            "📝 Enter product description"
        )

        await AdminStates.add_product_description.set()

    # =====================
    # PRODUCT DESCRIPTION
    # =====================

    @dp.message_handler(state=AdminStates.add_product_description)
    async def add_product_description(message: types.Message, state: FSMContext):

        await state.update_data(
            description=message.text
        )

        await message.answer(
            "🖼 Send product photo"
        )

        await AdminStates.add_product_photo.set()

    # =====================
    # PRODUCT PHOTO
    # =====================

    @dp.message_handler(
        content_types=types.ContentType.PHOTO,
        state=AdminStates.add_product_photo
    )
    async def add_product_photo(message: types.Message, state: FSMContext):

        try:

            photo_id = message.photo[-1].file_id

            data = await state.get_data()

            cur.execute(
                """
                INSERT INTO products(
                    category,
                    product_name,
                    description,
                    price,
                    image
                )
                VALUES(%s,%s,%s,%s,%s)
                """,
                (
                    data["category"],
                    data["name"],
                    data["description"],
                    data["price"],
                    photo_id
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
            """
            SELECT product_name
            FROM products
            """
        )

        products = cur.fetchall()

        if not products:

            await message.answer(
                "❌ No products"
            )

            return

        kb = ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        for product in products:

            kb.add(
                KeyboardButton(
                    f"🗑 PRODUCT {product[0]}"
                )
            )

        kb.add(
            KeyboardButton("⬅ Back")
        )

        await message.answer(
            "🗑 Select product",
            reply_markup=kb
        )

        await AdminStates.deleting_product.set()

    @dp.message_handler(
        lambda m: m.text.startswith("🗑 PRODUCT "),
        state=AdminStates.deleting_product
    )
    async def delete_product_finish(message: types.Message, state: FSMContext):

        product_name = message.text.replace(
            "🗑 PRODUCT ",
            ""
        )

        try:

            cur.execute(
                """
                DELETE FROM products
                WHERE product_name=%s
                """,
                (product_name,)
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
    # EDIT CATEGORY BANNER
    # =====================

    @dp.message_handler(
    lambda m: (
        m.text == "🖼 Edit category banner"
        or
        m.text == "🖼 Change banner"
    ),
    state="*"
)
    async def edit_category_banner_start(
        message: types.Message,
        state: FSMContext
    ):

        if message.from_user.id != ADMIN_ID:
            return

        await state.finish()

        cur.execute(
            """
            SELECT name
            FROM categories
            """
        )

        categories = cur.fetchall()

        if not categories:

            await message.answer(
                "❌ No categories"
            )

            return

        kb = ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        for category in categories:

            kb.add(
                KeyboardButton(category[0])
            )

        kb.add(
            KeyboardButton("⬅ Back")
        )

        await message.answer(
            "🖼 Choose category",
            reply_markup=kb
        )

        await AdminStates.edit_category_banner.set()

    # =====================
    # SELECT CATEGORY
    # =====================

    @dp.message_handler(
        state=AdminStates.edit_category_banner
    )
    async def edit_category_banner_select(
        message: types.Message,
        state: FSMContext
    ):

        await state.update_data(
            category=message.text
        )

        await message.answer(
            "📸 Send new banner image"
        )

        await AdminStates.waiting_banner_photo.set()

    # =====================
    # SAVE BANNER
    # =====================

    @dp.message_handler(
        content_types=types.ContentType.PHOTO,
        state=AdminStates.waiting_banner_photo
    )
    async def save_category_banner(
        message: types.Message,
        state: FSMContext
    ):

        try:

            data = await state.get_data()

            category = data["category"]

            photo_id = message.photo[-1].file_id

            cur.execute(
                """
                UPDATE categories
                SET image=%s
                WHERE name=%s
                """,
                (
                    photo_id,
                    category
                )
            )

            conn.commit()

            await message.answer(
                "✅ Category banner updated",
                reply_markup=admin_menu()
            )

        except Exception as e:

            conn.rollback()

            await message.answer(str(e))

        await state.finish()
        
    # =====================
    # CATEGORY EDITOR
    # =====================

    @dp.message_handler(
        lambda m: m.text == "📂 Category editor",
        state="*"
    )
    async def category_editor(
        message: types.Message
    ):

        kb = ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        kb.add(
            KeyboardButton("🖼 Change banner")
        )

        kb.add(
            KeyboardButton("🗑 Remove banner")
        )

        kb.add(
            KeyboardButton("⬅ Back")
        )

        await message.answer(
            "📂 Category editor",
            reply_markup=kb
        )
        
    # =====================
    # REMOVE CATEGORY BANNER
    # =====================

    @dp.message_handler(
        lambda m: m.text == "🗑 Remove banner",
        state="*"
    )
    async def remove_banner_start(
        message: types.Message
    ):

        cur.execute(
            """
            SELECT name
            FROM categories
            """
        )

        categories = cur.fetchall()

        kb = ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        for category in categories:

            kb.add(
                KeyboardButton(category[0])
            )

        kb.add(
            KeyboardButton("⬅ Back")
        )

        await message.answer(
            "🗑 Choose category",
            reply_markup=kb
        )

        await AdminStates.remove_category_banner.set()

    @dp.message_handler(
        state=AdminStates.remove_category_banner
    )
    async def remove_banner_finish(
        message: types.Message,
        state: FSMContext
    ):

        cur.execute(
            """
            UPDATE categories
            SET image=NULL
            WHERE name=%s
            """,
            (message.text,)
        )

        conn.commit()

        await message.answer(
            "✅ Banner removed",
            reply_markup=admin_menu()
        )

        await state.finish()    
        
    # =====================
    # ORDERS
    # =====================

    @dp.message_handler(lambda m: m.text == "📦 Orders", state="*")
    async def orders_handler(message: types.Message, state: FSMContext):

        if message.from_user.id != ADMIN_ID:
            return

        await state.finish()

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

            await message.answer(
                "📭 No orders"
            )

            return

        for order in orders:

            await message.answer(order[0])

    # =====================
    # STATS
    # =====================

    @dp.message_handler(lambda m: m.text == "📊 Stats", state="*")
    async def stats_handler(message: types.Message, state: FSMContext):

        if message.from_user.id != ADMIN_ID:
            return

        await state.finish()

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
