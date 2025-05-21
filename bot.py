from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import sqlite3
from datetime import datetime

# Configuration
ADMIN_ID = 6199518085  
TOKEN = "7571164900:AAH51WCNX73unu9jWhfNd425ISVPRYFw0EE"  

bot = Bot(token=TOKEN)
dp = Dispatcher()

# States
class Form(StatesGroup):
    customer_name = State()
    customer_phone = State()
    customer_email = State()
    customer_status = State()
    deal_amount = State()
    deal_stage = State()
    customer_select = State()
    product_name = State()
    product_price = State()
    product_description = State()

# Database initialization
def init_db():
    conn = sqlite3.connect('crm_bot.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        name TEXT,
        role TEXT DEFAULT 'support'
    )
    """)
    
    # Customers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        email TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Deals table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Deals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        user_id INTEGER,
        amount REAL,
        stage TEXT,
        FOREIGN KEY (customer_id) REFERENCES Customers(id),
        FOREIGN KEY (user_id) REFERENCES Users(id)
    )
    """)
    
    # Products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('crm_bot.db')
    conn.row_factory = sqlite3.Row
    return conn

# Database operations
def add_user(telegram_id, name, role='support'):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Users (telegram_id, name, role) VALUES (?, ?, ?)", 
                      (telegram_id, name, role))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user(telegram_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_customer(name, phone, email, status):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Customers (name, phone, email, status) VALUES (?, ?, ?, ?)",
                  (name, phone, email, status))
    conn.commit()
    customer_id = cursor.lastrowid
    conn.close()
    return customer_id

def get_customers(limit=10):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Customers ORDER BY created_at DESC LIMIT ?", (limit,))
    customers = cursor.fetchall()
    conn.close()
    return customers

def add_deal(customer_id, user_id, amount, stage):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Deals (customer_id, user_id, amount, stage) VALUES (?, ?, ?, ?)",
                  (customer_id, user_id, amount, stage))
    conn.commit()
    deal_id = cursor.lastrowid
    conn.close()
    return deal_id

def get_deals(user_id=None, limit=10):
    conn = get_db()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("""
            SELECT Deals.*, Customers.name as customer_name 
            FROM Deals
            JOIN Customers ON Deals.customer_id = Customers.id
            WHERE user_id = ? 
            ORDER BY Deals.id DESC 
            LIMIT ?
        """, (user_id, limit))
    else:
        cursor.execute("""
            SELECT Deals.*, Customers.name as customer_name 
            FROM Deals
            JOIN Customers ON Deals.customer_id = Customers.id
            ORDER BY Deals.id DESC 
            LIMIT ?
        """, (limit,))
    deals = cursor.fetchall()
    conn.close()
    return deals

def add_product(name, price, description):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Products (name, price, description) VALUES (?, ?, ?)",
                  (name, price, description))
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()
    return product_id

def get_products(limit=10):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Products ORDER BY created_at DESC LIMIT ?", (limit,))
    products = cursor.fetchall()
    conn.close()
    return products

def get_stats():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM Customers")
    total_customers = cursor.fetchone()[0]
    
    cursor.execute("SELECT status, COUNT(*) FROM Customers GROUP BY status")
    status_stats = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM Deals")
    total_deals = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(amount) FROM Deals WHERE stage = 'closed'")
    total_revenue = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM Products")
    total_products = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_customers': total_customers,
        'status_stats': status_stats,
        'total_deals': total_deals,
        'total_revenue': total_revenue,
        'total_products': total_products
    }

# Keyboard helpers
def get_main_menu(role):
    if role == 'admin':
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Мизоҷон"), KeyboardButton(text="Муомилаҳо")],
            [KeyboardButton(text="Маҳсулотҳо"), KeyboardButton(text="Илова кардани мизоҷ")],
            [KeyboardButton(text="Илова кардани муомила"), KeyboardButton(text="Илова кардани маҳсулот")],
            [KeyboardButton(text="Статистика"), KeyboardButton(text="Ёрӣ")]
        ], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Мизоҷон"), KeyboardButton(text="Муомилаҳо")],
            [KeyboardButton(text="Маҳсулотҳо"), KeyboardButton(text="Ёрӣ")]
        ], resize_keyboard=True)

# Handlers
@dp.message(Command("start"))
async def start(message: types.Message):
    user = get_user(message.from_user.id)
    
    if not user:
        role = 'admin' if message.from_user.id == ADMIN_ID else 'support'
        add_user(message.from_user.id, message.from_user.full_name, role)
        user = {'role': role}
    
    await message.answer(
        f"Салом {message.from_user.first_name}!\nНақши шумо: {user['role']}",
        reply_markup=get_main_menu(user['role'])
    )

@dp.message(F.text == "Ёрӣ")
async def show_help(message: types.Message):
    user = get_user(message.from_user.id)
    role = user['role'] if user else 'support'
    
    help_text = """
<b>Дастурҳои дастрас:</b>

👤 <b>Мизоҷон</b> - Рӯйхати мизоҷон
💼 <b>Муомилаҳо</b> - Рӯйхати муомилаҳо
🛍️ <b>Маҳсулотҳо</b> - Рӯйхати маҳсулотҳо
🆘 <b>Ёрӣ</b> - Информатсия оид ба дастурҳо
"""
    
    if role == 'admin':
        help_text += """
<b>Дастурҳои иловагӣ барои админ:</b>

➕ <b>Илова кардани мизоҷ</b> - Илова кардани мизоҷи нав
➕ <b>Илова кардани муомила</b> - Илова кардани муомилаи нав
➕ <b>Илова кардани маҳсулот</b> - Илова кардани маҳсулоти нав
📊 <b>Статистика</b> - Омори умумии система
"""
    
    await message.answer(help_text, parse_mode="HTML")

@dp.message(F.text == "Мизоҷон")
async def list_customers(message: types.Message):
    customers = get_customers()
    if not customers:
        await message.answer("Ҳоло мизоҷон нестанд")
        return
    
    response = "📋 Мизоҷон:\n\n"
    for customer in customers:
        response += (
            f"👤 Ном: {customer['name']}\n"
            f"📞 Телефон: {customer['phone']}\n"
            f"✉️ Почта: {customer['email']}\n"
            f"🔹 Вазъият: {customer['status']}\n"
            f"🆔 ID: {customer['id']}\n\n"
        )
    await message.answer(response)

@dp.message(F.text == "Илова кардани мизоҷ")
async def add_customer_start(message: types.Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user['role'] != 'admin':
        await message.answer("Шумо иҷозат надоред!")
        return
    
    await state.set_state(Form.customer_name)
    await message.answer("Номи мизоҷ:", reply_markup=types.ReplyKeyboardRemove())

@dp.message(Form.customer_name)
async def process_customer_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.customer_phone)
    await message.answer("Рақами телефон:")

@dp.message(Form.customer_phone)
async def process_customer_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(Form.customer_email)
    await message.answer("Почтаи электронӣ:")

@dp.message(Form.customer_email)
async def process_customer_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await state.set_state(Form.customer_status)
    
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Фаъол"), KeyboardButton(text="Ғайрифаъол")],
        [KeyboardButton(text="Сарчашма")]
    ], resize_keyboard=True)
    
    await message.answer("Вазъият:", reply_markup=keyboard)

@dp.message(Form.customer_status)
async def process_customer_status(message: types.Message, state: FSMContext):
    status_map = {
        "Фаъол": "active",
        "Ғайрифаъол": "inactive",
        "Сарчашма": "lead"
    }
    
    status = status_map.get(message.text)
    if not status:
        await message.answer("Лутфан аз рӯйхати додашуда интихоб кунед!")
        return
    
    data = await state.get_data()
    customer_id = add_customer(data['name'], data['phone'], data['email'], status)
    
    await message.answer(
        f"✅ Мизоҷ илова шуд!\nID: {customer_id}",
        reply_markup=get_main_menu(get_user(message.from_user.id)['role'])
    )
    await state.clear()

@dp.message(F.text == "Муомилаҳо")
async def list_deals(message: types.Message):
    user = get_user(message.from_user.id)
    deals = get_deals(user['id'] if user['role'] != 'admin' else None)
    
    if not deals:
        await message.answer("Ҳоло муомилаҳо нестанд")
        return
    
    response = "📋 Муомилаҳо:\n\n"
    for deal in deals:
        response += (
            f"💼 ID: {deal['id']}\n"
            f"👤 Мизоҷ: {deal['customer_name']}\n"
            f"💰 Маблағ: ${deal['amount']:.2f}\n"
            f"🔹 Марҳила: {deal['stage']}\n\n"
        )
    await message.answer(response)

@dp.message(F.text == "Илова кардани муомила")
async def add_deal_start(message: types.Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user['role'] != 'admin':
        await message.answer("Шумо иҷозат надоред!")
        return
    
    customers = get_customers()
    if not customers:
        await message.answer("Аввал мизоҷ илова кунед!")
        return
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=f"{c['id']} - {c['name']}")] for c in customers],
        resize_keyboard=True
    )
    
    await state.set_state(Form.customer_select)
    await message.answer("Мизоҷро интихоб кунед:", reply_markup=keyboard)

@dp.message(Form.customer_select)
async def process_customer_select(message: types.Message, state: FSMContext):
    try:
        customer_id = int(message.text.split()[0])
    except (ValueError, IndexError):
        await message.answer("Лутфан интихобро аз рӯйхат кунед!")
        return
    
    await state.update_data(customer_id=customer_id)
    await state.set_state(Form.deal_amount)
    await message.answer("Маблағи муомила:", reply_markup=types.ReplyKeyboardRemove())

@dp.message(Form.deal_amount)
async def process_deal_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("Лутфан маблағро бо рақам нависед (мисол: 1000 ё 1000.50)")
        return
    
    await state.update_data(amount=amount)
    await state.set_state(Form.deal_stage)
    
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="пешниҳод"), KeyboardButton(text="музокира")],
        [KeyboardButton(text="басташуда")]
    ], resize_keyboard=True)
    
    await message.answer("Марҳилаи муомила:", reply_markup=keyboard)

@dp.message(Form.deal_stage)
async def process_deal_stage(message: types.Message, state: FSMContext):
    stage_map = {
        "пешниҳод": "proposal",
        "музокира": "negotiation",
        "басташуда": "closed"
    }
    
    stage = stage_map.get(message.text.lower())
    if not stage:
        await message.answer("Лутфан марҳилаи дурустро интихоб кунед!")
        return
    
    data = await state.get_data()
    user = get_user(message.from_user.id)
    
    deal_id = add_deal(
        customer_id=data['customer_id'],
        user_id=user['id'],
        amount=data['amount'],
        stage=stage
    )
    
    await message.answer(
        f"✅ Муомила илова шуд!\nID: {deal_id}",
        reply_markup=get_main_menu(user['role'])
    )
    await state.clear()

@dp.message(F.text == "Маҳсулотҳо")
async def list_products(message: types.Message):
    products = get_products()
    if not products:
        await message.answer("Ҳоло маҳсулотҳо нестанд")
        return
    
    response = "🛍️ Маҳсулотҳо:\n\n"
    for product in products:
        response += (
            f"🏷️ Ном: {product['name']}\n"
            f"💰 Нарх: ${product['price']:.2f}\n"
            f"📝 Тавсиф: {product['description']}\n"
            f"🆔 ID: {product['id']}\n\n"
        )
    await message.answer(response)

@dp.message(F.text == "Илова кардани маҳсулот")
async def add_product_start(message: types.Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user['role'] != 'admin':
        await message.answer("Шумо иҷозат надоред!")
        return
    
    await state.set_state(Form.product_name)
    await message.answer("Номи маҳсулот:", reply_markup=types.ReplyKeyboardRemove())

@dp.message(Form.product_name)
async def process_product_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.product_price)
    await message.answer("Нархи маҳсулот:")

@dp.message(Form.product_price)
async def process_product_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
    except ValueError:
        await message.answer("Лутфан нархро бо рақам нависед (мисол: 100 ё 99.99)")
        return
    
    await state.update_data(price=price)
    await state.set_state(Form.product_description)
    await message.answer("Тавсифи маҳсулот:")

@dp.message(Form.product_description)
async def process_product_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    product_id = add_product(data['name'], data['price'], message.text)
    
    await message.answer(
        f"✅ Маҳсулот илова шуд!\nID: {product_id}",
        reply_markup=get_main_menu(get_user(message.from_user.id)['role'])
    )
    await state.clear()

@dp.message(F.text == "Статистика")
async def show_stats(message: types.Message):
    user = get_user(message.from_user.id)
    if user['role'] != 'admin':
        await message.answer("Шумо иҷозат надоред!")
        return
    
    stats = get_stats()
    
    status_translation = {
        "active": "Фаъол",
        "inactive": "Ғайрифаъол",
        "lead": "Сарчашма"
    }
    
    response = (
        "📊 Омор:\n\n"
        f"👥 Ҳамагӣ мизоҷон: {stats['total_customers']}\n"
        "Вазъиятҳо:\n"
    )
    
    for status, count in stats['status_stats']:
        response += f"  {status_translation.get(status, status)}: {count}\n"
    
    response += (
        f"\n💼 Ҳамагӣ муомилаҳо: {stats['total_deals']}\n"
        f"💰 Ҳамагӣ даромад: ${stats['total_revenue']:.2f}\n"
        f"🛍️ Ҳамагӣ маҳсулотҳо: {stats['total_products']}"
    )
    
    await message.answer(response)

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    
    
    
    
    


    