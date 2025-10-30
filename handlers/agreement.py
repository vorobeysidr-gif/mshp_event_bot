from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import FSInputFile

# Используем состояния формы регистрации из registration
from .registration import LeadForm
from config import POLICY_URL

router = Router()


def build_agreement_kb(policy_ok: bool, consent_ok: bool) -> InlineKeyboardMarkup:
	policy_text = ("✅ " if policy_ok else "⬜ ") + "Политика конфиденциальности"
	consent_text = ("✅ " if consent_ok else "⬜ ") + "Согласие на обработку персональных данных"

	buttons = [
		[InlineKeyboardButton(text=policy_text, callback_data="toggle:policy")],
		[InlineKeyboardButton(text=consent_text, callback_data="toggle:consent")],
	]

	# Кнопки для открытия документов
	if POLICY_URL:
		buttons.append([InlineKeyboardButton(text="Открыть политику", url=POLICY_URL)])
	else:
		buttons.append([InlineKeyboardButton(text="Открыть политику", callback_data="open:policy")])

	buttons.append([InlineKeyboardButton(text="Открыть согласие", callback_data="open:consent")])

	# Кнопку «Продолжить» показываем только когда оба чекбокса отмечены
	if policy_ok and consent_ok:
		buttons.append([InlineKeyboardButton(text="✅ Продолжить", callback_data="continue")])

	return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
	await state.clear()
	await state.set_state(LeadForm.agreement)
	await state.update_data(agree_policy=False, agree_consent=False)

	text = (
		"Добрый день! 😊\n\n"
		"Для записи на мастер-класс необходимо ваше согласие с документами ниже.\n"
		"Пожалуйста, ознакомьтесь и отметьте оба пункта:"
	)

	kb = build_agreement_kb(False, False)
	await message.answer(text, reply_markup=kb)


@router.callback_query(LeadForm.agreement, F.data.startswith("toggle:"))
async def toggle_agreement(cb: types.CallbackQuery, state: FSMContext):
	data = await state.get_data()
	policy_ok = bool(data.get("agree_policy"))
	consent_ok = bool(data.get("agree_consent"))

	what = cb.data.split(":", 1)[1]
	if what == "policy":
		policy_ok = not policy_ok
		await state.update_data(agree_policy=policy_ok)
	elif what == "consent":
		consent_ok = not consent_ok
		await state.update_data(agree_consent=consent_ok)

	await cb.message.edit_reply_markup(reply_markup=build_agreement_kb(policy_ok, consent_ok))
	await cb.answer()


@router.callback_query(LeadForm.agreement, F.data == "open:consent")
async def open_consent(cb: types.CallbackQuery):
	# Локальный PDF с согласием на обработку персональных данных
	try:
		doc = FSInputFile("согласние_на_обработку_Москва_на_сайт_для_маркетинга.pdf")
		await cb.message.answer_document(doc, caption="Согласие на обработку персональных данных")
	except Exception:
		await cb.message.answer("Файл согласия не найден в папке проекта. Обратитесь к администратору.")
	await cb.answer()


@router.callback_query(LeadForm.agreement, F.data == "open:policy")
async def open_policy(cb: types.CallbackQuery):
	# Запасной сценарий, если POLICY_URL не задана
	await cb.message.answer("Ссылка на политику конфиденциальности временно недоступна. Обратитесь к администратору.")
	await cb.answer()


@router.callback_query(LeadForm.agreement, F.data == "continue")
async def proceed(cb: types.CallbackQuery, state: FSMContext):
	data = await state.get_data()
	if not (data.get("agree_policy") and data.get("agree_consent")):
		await cb.answer("Отметьте оба пункта, чтобы продолжить", show_alert=True)
		return

	await state.set_state(LeadForm.name)
	await cb.message.answer("Спасибо! Как Вас зовут?")
	await cb.answer()


# Вспомогательная команда для отладки: позволяет удостовериться,
# что именно эта версия бота отвечает на сообщения.
@router.message(Command("version"))
async def version_cmd(message: types.Message):
	from datetime import datetime
	# Метка времени процесса: когда модуль был импортирован
	# (приблизительно соответствует времени старта бота)
	ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	await message.answer(f"Версия бота активна. Время процесса: {ts}")
