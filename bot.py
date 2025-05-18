from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from db import *

ADMIN_ID = 6199518085  
TOKEN = "7571164900:AAH51WCNX73unu9jWhfNd425ISVPRYFw0EE"  

bot = Bot(token=TOKEN)
dp = Dispatcher()

class Form(StatesGroup):
    customer_name = State()
    customer_phone = State()
    customer_email = State()
    customer_status = State()
    deal_amount = State()
    deal_stage = State()
    customer_select = State()

def get_main_menu(role):
    if role == 'admin':
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Мизоҷон"), KeyboardButton(text="Муомилаҳо")],
            [KeyboardButton(text="Илова кардани мизоҷ"), KeyboardButton(text="Илова кардани муомила")],
            [KeyboardButton(text="Статистика")]
        ], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="Мизоҷон"), KeyboardButton(text="Муомилаҳо")]
        ], resize_keyboard=True)

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
        f"💰 Ҳамагӣ даромад: ${stats['total_revenue']:.2f}"
    )
    
    await message.answer(response)

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())