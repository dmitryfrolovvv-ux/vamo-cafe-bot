import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

user_language = {}
user_cart = {}

ADMIN_ID = 1472777680  # потом заменим

# ---------- LANGUAGES ----------

language_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
language_keyboard.add("🇷🇺 Русский")
language_keyboard.add("🇹🇷 Türkçe")
language_keyboard.add("🇬🇧 English")
language_keyboard.add("🇩🇪 Deutsch")

# ---------- MAIN MENU ----------

def get_main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🌭 Hot Dogs")
    kb.add("🌯 Shawarma")
    kb.add("🥟 Chebureki")
    kb.add("🥤 Drinks")
    kb.add("🛒 Cart")
    kb.add("🌐 Change Language")
    return kb

# ---------- BACK BUTTON ----------

def back_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⬅ Back")
    return kb

# ---------- START ----------

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "👋 Welcome to VAMO Cafe!\n\nChoose language:",
        reply_markup=language_keyboard
    )

# ---------- LANGUAGE ----------

@dp.message_handler(lambda message: message.text in [
    "🇷🇺 Русский",
    "🇹🇷 Türkçe",
    "🇬🇧 English",
    "🇩🇪 Deutsch"
])
async def language_selected(message: types.Message):
    user_language[message.from_user.id] = message.text
    user_cart[message.from_user.id] = []

    await message.answer(
        "✅ Language selected!\n\nChoose category:",
        reply_markup=get_main_menu()
    )

# ---------- CHANGE LANGUAGE ----------

@dp.message_handler(lambda message: message.text == "🌐 Change Language")
async def change_language(message: types.Message):
    await message.answer(
        "🌍 Choose new language:",
        reply_markup=language_keyboard
    )

# ---------- HOT DOGS ----------

@dp.message_handler(lambda message: message.text == "🌭 Hot Dogs")
async def hotdogs(message: types.Message):
    text = (
        "🌭 Hot Dogs Menu\n\n"
        "1️⃣ Classic Hot Dog — 150 TL\n"
        "2️⃣ Cheese Hot Dog — 180 TL\n"
        "3️⃣ Double Hot Dog — 220 TL"
    )

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Classic Hot Dog")
    kb.add("Cheese Hot Dog")
    kb.add("Double Hot Dog")
    kb.add("⬅ Back")

    await message.answer(text, reply_markup=kb)

# ---------- SHAWARMA ----------

@dp.message_handler(lambda message: message.text == "🌯 Shawarma")
async def shawarma(message: types.Message):
    text = (
        "🌯 Shawarma Menu\n\n"
        "1️⃣ Chicken Shawarma — 200 TL\n"
        "2️⃣ Beef Shawarma — 250 TL\n"
        "3️⃣ Mega Shawarma — 320 TL"
    )

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Chicken Shawarma")
    kb.add("Beef Shawarma")
    kb.add("Mega Shawarma")
    kb.add("⬅ Back")

    await message.answer(text, reply_markup=kb)

# ---------- CHEBUREKI ----------

@dp.message_handler(lambda message: message.text == "🥟 Chebureki")
async def chebureki(message: types.Message):
    text = (
        "🥟 Chebureki Menu\n\n"
        "1️⃣ Beef Cheburek — 170 TL\n"
        "2️⃣ Cheese Cheburek — 150 TL\n"
        "3️⃣ Mixed Cheburek — 190 TL"
    )

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Beef Cheburek")
    kb.add("Cheese Cheburek")
    kb.add("Mixed Cheburek")
    kb.add("⬅ Back")

    await message.answer(text, reply_markup=kb)

# ---------- DRINKS ----------

@dp.message_handler(lambda message: message.text == "🥤 Drinks")
async def drinks(message: types.Message):
    text = (
        "🥤 Drinks Menu\n\n"
        "1️⃣ Cola — 50 TL\n"
        "2️⃣ Ayran — 40 TL\n"
        "3️⃣ Water — 20 TL"
    )

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Cola")
    kb.add("Ayran")
    kb.add("Water")
    kb.add("⬅ Back")

    await message.answer(text, reply_markup=kb)

# ---------- ADD TO CART ----------

prices = {
    "Classic Hot Dog": 150,
    "Cheese Hot Dog": 180,
    "Double Hot Dog": 220,

    "Chicken Shawarma": 200,
    "Beef Shawarma": 250,
    "Mega Shawarma": 320,

    "Beef Cheburek": 170,
    "Cheese Cheburek": 150,
    "Mixed Cheburek": 190,

    "Cola": 50,
    "Ayran": 40,
    "Water": 20
}

@dp.message_handler(lambda message: message.text in prices)
async def add_to_cart(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_cart:
        user_cart[user_id] = []

    item = message.text
    price = prices[item]

    user_cart[user_id].append((item, price))

    await message.answer(
        f"✅ {item} added to cart!\n💰 {price} TL",
        reply_markup=get_main_menu()
    )

# ---------- CART ----------

@dp.message_handler(lambda message: message.text == "🛒 Cart")
async def cart(message: types.Message):
    user_id = message.from_user.id

    cart_items = user_cart.get(user_id, [])

    if not cart_items:
        await message.answer(
            "🛒 Your cart is empty!",
            reply_markup=get_main_menu()
        )
        return

    text = "🛒 Your Cart\n\n"

    total = 0

    for item, price in cart_items:
        text += f"🌭 {item} — {price} TL\n"
        total += price

    text += f"\n💰 Total: {total} TL"

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✅ Checkout")
    kb.add("🗑 Clear Cart")
    kb.add("⬅ Back")

    await message.answer(text, reply_markup=kb)

# ---------- CLEAR CART ----------

@dp.message_handler(lambda message: message.text == "🗑 Clear Cart")
async def clear_cart(message: types.Message):
    user_cart[message.from_user.id] = []

    await message.answer(
        "🗑 Cart cleared!",
        reply_markup=get_main_menu()
    )

# ---------- CHECKOUT ----------

@dp.message_handler(lambda message: message.text == "✅ Checkout")
async def checkout(message: types.Message):
    await message.answer(
        "📞 Send your phone number:",
        reply_markup=back_keyboard()
    )

# ---------- PHONE ----------

@dp.message_handler(lambda message: message.text.startswith("+"))
async def phone(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_cart:
        return

    phone_number = message.text

    cart_items = user_cart[user_id]

    text = "🛍 NEW ORDER\n\n"

    total = 0

    for item, price in cart_items:
        text += f"• {item} — {price} TL\n"
        total += price

    text += f"\n💰 Total: {total} TL"
    text += f"\n📞 Phone: {phone_number}"
    text += f"\n👤 User: @{message.from_user.username}"

    await bot.send_message(ADMIN_ID, text)

    user_cart[user_id] = []

    await message.answer(
        "✅ Order sent successfully!\n\nVAMO Cafe will contact you soon.",
        reply_markup=get_main_menu()
    )

# ---------- BACK ----------

@dp.message_handler(lambda message: message.text == "⬅ Back")
async def back(message: types.Message):
    await message.answer(
        "⬅ Returned to main menu",
        reply_markup=get_main_menu()
    )

# ---------- RUN ----------

if __name__ == "__main__":
    print("VAMO Cafe Bot started")
    executor.start_polling(dp, skip_updates=True)