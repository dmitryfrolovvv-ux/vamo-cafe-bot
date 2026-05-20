import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)

# =========================
# CONFIG
# =========================

API_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 1472777680

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# =========================
# DATA
# =========================

carts = {}
user_states = {}
user_data = {}

# =========================
# MENU
# =========================

menu = {
    "🌭 Hot Dogs": [
        ("Classic Hot Dog", 150),
        ("Cheese Hot Dog", 180),
        ("Double Hot Dog", 220),
    ],

    "🌯 Shawarma": [
        ("Chicken Shawarma", 200),
        ("Beef Shawarma", 250),
        ("Mega Shawarma", 320),
    ],

    "🥟 Chebureki": [
        ("Classic Chebureki", 140),
        ("Cheese Chebureki", 160),
        ("Meat Chebureki", 190),
    ],

    "🥤 Drinks": [
        ("Cola", 60),
        ("Ayran", 50),
        ("Water", 30),
    ]
}

# =========================
# MAIN KEYBOARD
# =========================

def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("🌭 Hot Dogs")
    kb.add("🌯 Shawarma")
    kb.add("🥟 Chebureki")
    kb.add("🥤 Drinks")
    kb.add("🛒 Cart")
    kb.add("🌐 Change Language")

    return kb

# =========================
# START
# =========================

@dp.message_handler(commands=["start"])
async def start(message: types.Message):

    if message.from_user.id not in carts:
        carts[message.from_user.id] = []

    await message.answer(
        "👋 Welcome to VAMO Cafe!\n\nChoose category:",
        reply_markup=main_keyboard()
    )

# =========================
# CHANGE LANGUAGE
# =========================

@dp.message_handler(lambda message: message.text == "🌐 Change Language")
async def change_language(message: types.Message):

    await message.answer(
        "🌍 Language changed!\n\nChoose category:",
        reply_markup=main_keyboard()
    )

# =========================
# HOT DOGS
# =========================

@dp.message_handler(lambda message: message.text == "🌭 Hot Dogs")
async def hotdogs(message: types.Message):

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("Classic Hot Dog")
    keyboard.add("Cheese Hot Dog")
    keyboard.add("Double Hot Dog")
    keyboard.add("⬅️ Back")

    await message.answer(
        "🌭 Hot Dogs Menu\n\n"
        "Classic Hot Dog — 150 TL\n"
        "Cheese Hot Dog — 180 TL\n"
        "Double Hot Dog — 220 TL",
        reply_markup=keyboard
    )

# =========================
# SHAWARMA
# =========================

@dp.message_handler(lambda message: message.text == "🌯 Shawarma")
async def shawarma(message: types.Message):

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("Chicken Shawarma")
    keyboard.add("Beef Shawarma")
    keyboard.add("Mega Shawarma")
    keyboard.add("⬅️ Back")

    await message.answer(
        "🌯 Shawarma Menu\n\n"
        "Chicken Shawarma — 200 TL\n"
        "Beef Shawarma — 250 TL\n"
        "Mega Shawarma — 320 TL",
        reply_markup=keyboard
    )

# =========================
# CHEBUREKI
# =========================

@dp.message_handler(lambda message: message.text == "🥟 Chebureki")
async def chebureki(message: types.Message):

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("Classic Chebureki")
    keyboard.add("Cheese Chebureki")
    keyboard.add("Meat Chebureki")
    keyboard.add("⬅️ Back")

    await message.answer(
        "🥟 Chebureki Menu\n\n"
        "Classic Chebureki — 140 TL\n"
        "Cheese Chebureki — 160 TL\n"
        "Meat Chebureki — 190 TL",
        reply_markup=keyboard
    )

# =========================
# DRINKS
# =========================

@dp.message_handler(lambda message: message.text == "🥤 Drinks")
async def drinks(message: types.Message):

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("Cola")
    keyboard.add("Ayran")
    keyboard.add("Water")
    keyboard.add("⬅️ Back")

    await message.answer(
        "🥤 Drinks Menu\n\n"
        "Cola — 60 TL\n"
        "Ayran — 50 TL\n"
        "Water — 30 TL",
        reply_markup=keyboard
    )

# =========================
# ADD PRODUCTS
# =========================

products = {
    "Classic Hot Dog": 150,
    "Cheese Hot Dog": 180,
    "Double Hot Dog": 220,

    "Chicken Shawarma": 200,
    "Beef Shawarma": 250,
    "Mega Shawarma": 320,

    "Classic Chebureki": 140,
    "Cheese Chebureki": 160,
    "Meat Chebureki": 190,

    "Cola": 60,
    "Ayran": 50,
    "Water": 30
}

@dp.message_handler(lambda message: message.text in products.keys())
async def add_product(message: types.Message):

    user_id = message.from_user.id

    if user_id not in carts:
        carts[user_id] = []

    carts[user_id].append({
        "name": message.text,
        "price": products[message.text]
    })

    await message.answer(
        f"✅ Added to cart:\n{message.text} — {products[message.text]} TL"
    )

# =========================
# BACK
# =========================

@dp.message_handler(lambda message: message.text == "⬅️ Back")
async def back_handler(message: types.Message):

    await message.answer(
        "⬅️ Returned to main menu",
        reply_markup=main_keyboard()
    )

# =========================
# CART
# =========================

@dp.message_handler(lambda message: message.text == "🛒 Cart")
async def cart_handler(message: types.Message):

    user_id = message.from_user.id

    if user_id not in carts or len(carts[user_id]) == 0:
        await message.answer("🛒 Your cart is empty!")
        return

    text = "🛒 Your Cart\n\n"

    total = 0

    for item in carts[user_id]:
        text += f"• {item['name']} — {item['price']} TL\n"
        total += item["price"]

    text += f"\n💰 Total: {total} TL"

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("✅ Checkout")
    keyboard.add("🗑 Clear Cart")
    keyboard.add("⬅️ Back")

    await message.answer(text, reply_markup=keyboard)

# =========================
# CLEAR CART
# =========================

@dp.message_handler(lambda message: message.text == "🗑 Clear Cart")
async def clear_cart(message: types.Message):

    carts[message.from_user.id] = []

    await message.answer(
        "🗑 Cart cleared!",
        reply_markup=main_keyboard()
    )

# =========================
# CHECKOUT
# =========================

@dp.message_handler(lambda message: message.text == "✅ Checkout")
async def checkout(message: types.Message):

    user_id = message.from_user.id

    if user_id not in carts or len(carts[user_id]) == 0:
        await message.answer("🛒 Your cart is empty!")
        return

    user_states[user_id] = "waiting_phone"

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    contact_btn = KeyboardButton(
        "📞 Send phone number",
        request_contact=True
    )

    keyboard.add(contact_btn)

    await message.answer(
        "📞 Send your phone number:\n\n"
        "Example:\n"
        "+905551112233",
        reply_markup=keyboard
    )

# =========================
# PHONE
# =========================

@dp.message_handler(content_types=types.ContentType.CONTACT)
async def get_contact(message: types.Message):

    user_id = message.from_user.id

    if user_states.get(user_id) != "waiting_phone":
        return

    phone = message.contact.phone_number

    user_data[user_id] = {
        "phone": phone
    }

    user_states[user_id] = "waiting_location"

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    location_btn = KeyboardButton(
        "📍 Send Location",
        request_location=True
    )

    keyboard.add(location_btn)

    await message.answer(
        "📍 Please send your location.",
        reply_markup=keyboard
    )

@dp.message_handler(lambda message: user_states.get(message.from_user.id) == "waiting_phone")
async def manual_phone(message: types.Message):

    user_id = message.from_user.id

    phone = message.text

    user_data[user_id] = {
        "phone": phone
    }

    user_states[user_id] = "waiting_location"

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    location_btn = KeyboardButton(
        "📍 Send Location",
        request_location=True
    )

    keyboard.add(location_btn)

    await message.answer(
        "📍 Please send your location.",
        reply_markup=keyboard
    )

# =========================
# LOCATION
# =========================

@dp.message_handler(content_types=types.ContentType.LOCATION)
async def get_location(message: types.Message):

    user_id = message.from_user.id

    if user_states.get(user_id) != "waiting_location":
        return

    latitude = message.location.latitude
    longitude = message.location.longitude

    user_data[user_id]["latitude"] = latitude
    user_data[user_id]["longitude"] = longitude

    user_states[user_id] = "waiting_address"

    await message.answer(
        "🏠 Enter delivery address:",
        reply_markup=ReplyKeyboardRemove()
    )

# =========================
# ADDRESS
# =========================

@dp.message_handler(lambda message: user_states.get(message.from_user.id) == "waiting_address")
async def get_address(message: types.Message):

    user_id = message.from_user.id

    user_data[user_id]["address"] = message.text

    user_states[user_id] = "waiting_complex_code"

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Skip")

    await message.answer(
        "🏢 Enter complex/gate code (optional):",
        reply_markup=keyboard
    )

# =========================
# COMPLEX CODE
# =========================

@dp.message_handler(lambda message: user_states.get(message.from_user.id) == "waiting_complex_code")
async def get_complex_code(message: types.Message):

    user_id = message.from_user.id

    if message.text.lower() == "skip":
        complex_code = "Not provided"
    else:
        complex_code = message.text

    user_data[user_id]["complex_code"] = complex_code

    user_states[user_id] = "waiting_door_code"

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Skip")

    await message.answer(
        "🚪 Enter apartment door code (optional):",
        reply_markup=keyboard
    )

# =========================
# DOOR CODE + SEND ORDER
# =========================

@dp.message_handler(lambda message: user_states.get(message.from_user.id) == "waiting_door_code")
async def get_door_code(message: types.Message):

    user_id = message.from_user.id

    if message.text.lower() == "skip":
        door_code = "Not provided"
    else:
        door_code = message.text

    user_data[user_id]["door_code"] = door_code

    cart = carts.get(user_id, [])

    total = sum(item["price"] for item in cart)

    order_text = "📦 NEW ORDER\n\n"

    for item in cart:
        order_text += f"• {item['name']} — {item['price']} TL\n"

    order_text += f"\n💰 Total: {total} TL"

    order_text += f"\n📞 Phone: {user_data[user_id]['phone']}"

    order_text += f"\n🏠 Address: {user_data[user_id]['address']}"

    order_text += (
        f"\n📍 Location:\n"
        f"https://maps.google.com/?q="
        f"{user_data[user_id]['latitude']},"
        f"{user_data[user_id]['longitude']}"
    )

    order_text += (
        f"\n🏢 Complex code: "
        f"{user_data[user_id]['complex_code']}"
    )

    order_text += (
        f"\n🚪 Door code: "
        f"{user_data[user_id]['door_code']}"
    )

    order_text += (
        f"\n\n👤 Client: "
        f"{message.from_user.full_name}"
    )

    order_text += (
        f"\n🆔 ID: "
        f"{message.from_user.id}"
    )

    if message.from_user.username:
        order_text += (
            f"\n🔗 Username: "
            f"@{message.from_user.username}"
        )

    await bot.send_message(
        OWNER_ID,
        order_text
    )

    await message.answer(
        "✅ Order sent successfully!\n\n"
        "VAMO Cafe will contact you soon.",
        reply_markup=main_keyboard()
    )

    carts[user_id] = []
    user_states[user_id] = None

# =========================
# RUN
# =========================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)