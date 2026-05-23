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

    adding_category_en = State()

    adding_category_ru = State()

    adding_category_tr = State()

    add_product_category = State()

    add_product_name = State()
    
    adding_product_name_en = State()

    adding_product_name_ru = State()
    
    adding_product_name_tr = State()
    
    adding_product_description_en = State()
    
    adding_product_description_ru = State()
    
    adding_product_description_tr = State()

    add_product_price = State()

    add_product_description = State()

    add_product_photo = State()

    deleting_category = State()

    deleting_product = State()
    
    edit_category_banner = State()

    waiting_banner_photo = State()
    
    remove_category_banner = State()
    
    edit_product = State()

    edit_product_action = State()
    
    waiting_new_price = State()
    
    waiting_new_name = State()
    
    waiting_new_description = State()
    
    waiting_new_photo = State()
    
    waiting_new_category = State()
    
    editing_category_name = State()

    editing_category_name_en = State()

    editing_category_name_ru = State()

    editing_category_name_tr = State()

# =========================
# ADMIN MENU
# =========================

def admin_menu():

    kb = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.add(
        KeyboardButton("📦 Product editor")
    )
    
    kb.add(
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
    
    @dp.message_handler(
        lambda m: m.text == "📦 Product editor",
        state="*"
    )
    async def product_editor(
        message: types.Message
    ):

        kb = ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        kb.add(
            KeyboardButton("➕ Add product"),
            KeyboardButton("❌ Delete product")
        )

        kb.add(
            KeyboardButton("✏ Edit product")
        )

        kb.add(
            KeyboardButton("⬅ Back")
        )

        await message.answer(
            "📦 Product editor",
            reply_markup=kb
        )
        
    # =====================
    # EDIT PRODUCT
    # =====================

    @dp.message_handler(
        lambda m: m.text == "✏ Edit product",
        state="*"
    )
    async def edit_product_start(
        message: types.Message
    ):

        cur.execute(
            """
            SELECT product_name
            FROM products
            ORDER BY product_name
            """
        )

        products = cur.fetchall()

        kb = ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        for product in products:

            kb.add(
                KeyboardButton(product[0])
            )

        kb.add(
            KeyboardButton("⬅ Back")
        )

        await message.answer(
            "✏ Choose product",
            reply_markup=kb
        )

        await AdminStates.edit_product.set()

    @dp.message_handler(
        state=AdminStates.edit_product
    )
    async def edit_product_select(
        message: types.Message,
        state: FSMContext
    ):

        await state.update_data(
            product_name=message.text
        )

        kb = ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        kb.add(
            KeyboardButton("📝 Change name"),
            KeyboardButton("💰 Change price")
        )

        kb.add(
            KeyboardButton("📄 Change description"),
            KeyboardButton("🖼 Change photo")
        )

        kb.add(
            KeyboardButton("📂 Change category")
        )

        kb.add(
            KeyboardButton("⬅ Back")
        )

        await message.answer(
            f"✏ Editing: {message.text}",
            reply_markup=kb
        )

        await AdminStates.edit_product_action.set()
        
    # =====================
    # EDIT CATEGORY NAME
    # =====================

    @dp.message_handler(
        lambda m: m.text == "✏ Edit category name",
        state="*"
    )
    async def edit_category_name_start(
        message: types.Message
    ):

        cur.execute(
            """
            SELECT name
            FROM categories
            ORDER BY name
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
            "📂 Choose category",
            reply_markup=kb
        )

        await AdminStates.editing_category_name.set()

    @dp.message_handler(
        state=AdminStates.editing_category_name
    )
    async def edit_category_name_choose(
        message: types.Message,
        state: FSMContext
    ):

        await state.update_data(
            old_category=message.text
        )

        await message.answer(
            "🇬🇧 Enter new category name (EN)"
        )

        await AdminStates.editing_category_name_en.set()

    @dp.message_handler(
        state=AdminStates.editing_category_name_en
    )
    async def edit_category_name_en(
        message: types.Message,
        state: FSMContext
    ):

        await state.update_data(
            name_en=message.text
        )

        await message.answer(
            "🇷🇺 Enter new category name (RU)"
        )

        await AdminStates.editing_category_name_ru.set()

    @dp.message_handler(
        state=AdminStates.editing_category_name_ru
    )
    async def edit_category_name_ru(
        message: types.Message,
        state: FSMContext
    ):

        await state.update_data(
            name_ru=message.text
        )

        await message.answer(
            "🇹🇷 Enter new category name (TR)"
        )

        await AdminStates.editing_category_name_tr.set()

    @dp.message_handler(
        state=AdminStates.editing_category_name_tr
    )
    async def edit_category_name_tr(
        message: types.Message,
        state: FSMContext
    ):

        data = await state.get_data()

        old_category = data["old_category"]

        name_en = data["name_en"]

        name_ru = data["name_ru"]

        name_tr = message.text

        cur.execute(
            """
            UPDATE categories
            SET
                name=%s,
                name_en=%s,
                name_ru=%s,
                name_tr=%s
            WHERE name=%s
            """,
            (
                name_en,
                name_en,
                name_ru,
                name_tr,
                old_category
            )
        )

        conn.commit()

        await message.answer(
            "✅ Category updated",
            reply_markup=admin_menu()
        )

        await state.finish()
        
    # =====================
    # CHANGE PRICE
    # =====================

    @dp.message_handler(
        lambda m: m.text == "💰 Change price",
        state=AdminStates.edit_product_action
    )
    async def change_price_start(
        message: types.Message
    ):

        await message.answer(
            "💰 Send new price"
        )

        await AdminStates.waiting_new_price.set()

    @dp.message_handler(
        state=AdminStates.waiting_new_price
    )
    async def change_price_finish(
        message: types.Message,
        state: FSMContext
    ):

        try:

            new_price = int(message.text)

            data = await state.get_data()

            product_name = data["product_name"]

            cur.execute(
                """
                UPDATE products
                SET price=%s
                WHERE product_name=%s
                """,
                (
                    new_price,
                    product_name
                )
            )

            conn.commit()

            await message.answer(
                "✅ Price updated",
                reply_markup=admin_menu()
            )

            await state.finish()

        except:

            await message.answer(
                "❌ Send number only"
            )
            
    # =====================
    # CHANGE NAME
    # =====================

    @dp.message_handler(
        lambda m: m.text == "📝 Change name",
        state=AdminStates.edit_product_action
    )
    async def change_name_start(
        message: types.Message
    ):

        await message.answer(
            "📝 Send new product name"
        )

        await AdminStates.waiting_new_name.set()

    @dp.message_handler(
        state=AdminStates.waiting_new_name
    )
    async def change_name_finish(
        message: types.Message,
        state: FSMContext
    ):

        new_name = message.text

        data = await state.get_data()

        old_name = data["product_name"]

        cur.execute(
            """
            UPDATE products
            SET product_name=%s
            WHERE product_name=%s
            """,
            (
                new_name,
                old_name
            )
        )

        conn.commit()

        await message.answer(
            "✅ Product name updated",
            reply_markup=admin_menu()
        )

        await state.finish()
        
    # =====================
    # CHANGE DESCRIPTION
    # =====================

    @dp.message_handler(
        lambda m: m.text == "📄 Change description",
        state=AdminStates.edit_product_action
    )
    async def change_description_start(
        message: types.Message
    ):

        await message.answer(
            "📄 Send new description"
        )

        await AdminStates.waiting_new_description.set()

    @dp.message_handler(
        state=AdminStates.waiting_new_description
    )
    async def change_description_finish(
        message: types.Message,
        state: FSMContext
    ):

        new_description = message.text

        data = await state.get_data()

        product_name = data["product_name"]

        cur.execute(
            """
            UPDATE products
            SET description=%s
            WHERE product_name=%s
            """,
            (
                new_description,
                product_name
            )
        )

        conn.commit()

        await message.answer(
            "✅ Description updated",
            reply_markup=admin_menu()
        )

        await state.finish()
        
    # =====================
    # CHANGE PHOTO
    # =====================

    @dp.message_handler(
        lambda m: m.text == "🖼 Change photo",
        state=AdminStates.edit_product_action
    )
    async def change_photo_start(
        message: types.Message
    ):

        await message.answer(
            "🖼 Send new product photo"
        )

        await AdminStates.waiting_new_photo.set()

    @dp.message_handler(
        content_types=types.ContentType.PHOTO,
        state=AdminStates.waiting_new_photo
    )
    async def change_photo_finish(
        message: types.Message,
        state: FSMContext
    ):

        photo_id = message.photo[-1].file_id

        data = await state.get_data()

        product_name = data["product_name"]

        cur.execute(
            """
            UPDATE products
            SET image=%s
            WHERE product_name=%s
            """,
            (
                photo_id,
                product_name
            )
        )

        conn.commit()

        await message.answer(
            "✅ Product photo updated",
            reply_markup=admin_menu()
        )

        await state.finish()
        
    # =====================
    # CHANGE CATEGORY
    # =====================

    @dp.message_handler(
        lambda m: m.text == "📂 Change category",
        state=AdminStates.edit_product_action
    )
    async def change_category_start(
        message: types.Message
    ):

        cur.execute(
            """
            SELECT name
            FROM categories
            ORDER BY name
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
            "📂 Choose new category",
            reply_markup=kb
        )

        await AdminStates.waiting_new_category.set()

    @dp.message_handler(
        state=AdminStates.waiting_new_category
    )
    async def change_category_finish(
        message: types.Message,
        state: FSMContext
    ):

        new_category = message.text

        data = await state.get_data()

        product_name = data["product_name"]

        cur.execute(
            """
            UPDATE products
            SET category=%s
            WHERE product_name=%s
            """,
            (
                new_category,
                product_name
            )
        )

        conn.commit()

        await message.answer(
            "✅ Product category updated",
            reply_markup=admin_menu()
        )

        await state.finish()
        
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
    # ADD CATEGORY MULTILANGUAGE
    # =====================

    @dp.message_handler(
        lambda m: m.text == "➕ Add category",
        state="*"
    )
    async def add_category_start(
        message: types.Message
    ):

        await message.answer(
            "🇬🇧 Enter category name (EN)"
        )

        await AdminStates.adding_category_en.set()

    @dp.message_handler(
        state=AdminStates.adding_category_en
    )
    async def add_category_en(
        message: types.Message,
        state: FSMContext
    ):

        await state.update_data(
            name_en=message.text
        )

        await message.answer(
            "🇷🇺 Enter category name (RU)"
        )

        await AdminStates.adding_category_ru.set()

    @dp.message_handler(
        state=AdminStates.adding_category_ru
    )
    async def add_category_ru(
        message: types.Message,
        state: FSMContext
    ):

        await state.update_data(
            name_ru=message.text
        )

        await message.answer(
            "🇹🇷 Enter category name (TR)"
        )

        await AdminStates.adding_category_tr.set()

    @dp.message_handler(
        state=AdminStates.adding_category_tr
    )
    async def add_category_tr(
        message: types.Message,
        state: FSMContext
    ):

        data = await state.get_data()

        name_en = data["name_en"]

        name_ru = data["name_ru"]

        name_tr = message.text

        cur.execute(
            """
            INSERT INTO categories(
                name,
                name_en,
                name_ru,
                name_tr
            )
            VALUES(%s,%s,%s,%s)
            """,
            (
                name_en,
                name_en,
                name_ru,
                name_tr
            )
        )

        conn.commit()

        await message.answer(
            "✅ Category added",
            reply_markup=admin_menu()
        )

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
            "🇬🇧 Enter product name (EN)"
        )

        await AdminStates.adding_product_name_en.set()
        
        @dp.message_handler(
        state=AdminStates.adding_product_name_en
    )
    async def add_product_name_en(
        message: types.Message,
        state: FSMContext
    ):

        await state.update_data(
            product_name_en=message.text
        )

        await message.answer(
            "🇷🇺 Enter product name (RU)"
        )

        await AdminStates.adding_product_name_ru.set()

    @dp.message_handler(
        state=AdminStates.adding_product_name_ru
    )
    async def add_product_name_ru(
        message: types.Message,
        state: FSMContext
    ):

        await state.update_data(
            product_name_ru=message.text
        )

        await message.answer(
            "🇹🇷 Enter product name (TR)"
        )

        await AdminStates.adding_product_name_tr.set()

    @dp.message_handler(
        state=AdminStates.adding_product_name_tr
    )
    async def add_product_name_tr(
        message: types.Message,
        state: FSMContext
    ):

        await state.update_data(
            product_name_tr=message.text
        )

        await message.answer(
            "🇬🇧 Enter description (EN)"
        )

        await AdminStates.adding_product_description_en.set()

    @dp.message_handler(
        state=AdminStates.adding_product_description_en
    )
    async def add_product_description_en(
        message: types.Message,
        state: FSMContext
    ):

        await state.update_data(
            description_en=message.text
        )

        await message.answer(
            "🇷🇺 Enter description (RU)"
        )

        await AdminStates.adding_product_description_ru.set()

    @dp.message_handler(
        state=AdminStates.adding_product_description_ru
    )
    async def add_product_description_ru(
        message: types.Message,
        state: FSMContext
    ):

        await state.update_data(
            description_ru=message.text
        )

        await message.answer(
            "🇹🇷 Enter description (TR)"
        )

        await AdminStates.adding_product_description_tr.set()

    @dp.message_handler(
        state=AdminStates.adding_product_description_tr
    )
    async def add_product_description_tr(
        message: types.Message,
        state: FSMContext
    ):

        await state.update_data(
            description_tr=message.text
        )

        await message.answer(
            "💰 Enter product price"
        )

        await AdminStates.adding_product_price.set()
        
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
    KeyboardButton("➕ Add category"),
    KeyboardButton("❌ Delete category"),
            
        )

        kb.add(
    KeyboardButton("🖼 Change banner"),
    KeyboardButton("🗑 Remove banner")
        )

        kb.add(
    KeyboardButton("✏ Edit category name"),
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
