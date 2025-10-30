from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from services.sheets import append_lead_row
from services.backup import backup_to_csv

router = Router()

class LeadForm(StatesGroup):
    name = State()
    contact = State()
    age = State()
    is_mshp_student = State()
    time = State()

@router.message(F.text == "/start")
async def start_registration(message: types.Message, state: FSMContext):
    await message.answer("Как Вас зовут?")
    await state.set_state(LeadForm.name)

@router.message(LeadForm.name)
async def handle_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить контакт", request_contact=True)]],
        resize_keyboard=True
    )
    await message.answer("Отправьте контакт 👇", reply_markup=kb)
    await state.set_state(LeadForm.contact)

@router.message(LeadForm.contact, F.contact)
async def handle_contact(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("Сколько лет ребёнку?")
    await state.set_state(LeadForm.age)

@router.message(LeadForm.age)
async def finish(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    data = await state.get_data()
    try:
        append_lead_row(data)
    except Exception:
        backup_to_csv(data)
    await message.answer("✅ Спасибо, данные сохранены!")
    await state.clear()
