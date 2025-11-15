from db import RegistrationState

import logging
import os
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from config import BOT_TOKEN, HOST
from handlers import agreement, registration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://{HOST}{WEBHOOK_PATH}"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Подключаем роутеры
dp.include_router(agreement.router)
dp.include_router(registration.router)

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    if get_uvicorn_worker_index() == 1:
        logger.info("Устанавливаю webhook...")
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
        logger.info("Webhook установлен: %s", WEBHOOK_URL)


@app.on_event("shutdown")
async def on_shutdown():
    if get_uvicorn_worker_index() == 1:
        logger.info("Удаляю webhook...")
        await bot.delete_webhook()
        logger.info("Webhook удалён")
        await bot.session.close()


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    update = Update.model_validate(await request.json())
    telegram_id = get_telegram_id(update)
    user_data = get_or_create_user_data_from_db(telegram_id)

    remove_all_buttons()

    if update.callback_query.data == 'reset':
        set_registration_state(user_data, RegistrationState.START_BOT)
        await dp.feed_update(bot, update)
        return {"ok": True}

    if user_data['registration_state'] == RegistrationState.START_BOT:  # /start command sent to bot
        send_hello_message()
        create_agreement_and_confidence_buttons(confidence_ok=user_data['confidence_ok'], agreement_ok=user_data['agreement_ok'], add_reset_button=True)
        set_registration_state(user_data, RegistrationState.WAIT_FOR_CONFIDENCE_AND_AGREEMENT)
    elif user_data['registration_state'] in [
        RegistrationState.WAIT_FOR_CONFIDENCE_AND_AGREEMENT,
        RegistrationState.CONFIDENCE_ACCEPTED,
        RegistrationState.CONFIDENCE_REJECTED_AND_AGREEMENT_ACCEPTED
    ]:  # wait for confidence and agreement
        if update.callback_query.data == 'continue':  # continue button pressed, but not both confidence and agreement are accepted
            send_need_both_confidence_and_agreement_message()
        if update.callback_query.data == 'agreement_ok':  # agreement button pressed
            set_agreement_ok(user_data, True)
            next_registration_state = str(user_data['registration_state'])
            next_registration_state[2] = '1'
            next_registration_state = int(next_registration_state)
            set_registration_state(user_data, next_registration_state)
        elif update.callback_query.data == 'confidence_ok':  # confidence button pressed
            set_confidence_ok(user_data, True)
            next_registration_state = str(user_data['registration_state'])
            next_registration_state[1] = '1'
            next_registration_state = int(next_registration_state)
            set_registration_state(user_data, next_registration_state)
        create_agreement_and_confidence_buttons(confidence_ok=user_data['confidence_ok'], agreement_ok=user_data['agreement_ok'], add_reset_button=True)
    elif user_data['registration_state'] == RegistrationState.BOTH_CONFIDENCE_AND_AGREEMENT_ACCEPTED:  # both confidence and agreement are accepted
        send_user_name_message()
        create_user_name_buttons(add_reset_button=True)
        set_registration_state(user_data, RegistrationState.WAIT_FOR_USER_NAME)
    elif user_data['registration_state'] == RegistrationState.WAIT_FOR_USER_NAME:
        user_name = get_user_name(update)
        validate_status = validate_user_name(user_name)
        if validate_status:
            set_user_name(user_data, user_name)
            send_user_contact_message()
            create_user_contact_buttons(add_reset_button=True)
            set_registration_state(user_data, RegistrationState.WAIT_FOR_USER_CONTACT)
        else:
            send_user_name_validation_error_message()
            create_user_name_buttons(add_reset_button=True)

    elif user_data['registration_state'] == RegistrationState.WAIT_FOR_USER_CONTACT:
        if update.callback_query.data == 'sending_contact':
            user_contact = get_user_contact_entity(update)
            set_user_contact(user_data, user_contact)
        else:
            user_contact = get_user_contact_from_text(update)
            validate_status = validate_user_contact(user_contact)
            if validate_status:
                set_user_contact(user_data, user_contact)
                send_user_age_message()
                set_registration_state(user_data, RegistrationState.WAIT_FOR_USER_AGE)
            else:
                send_user_contact_validation_error_message()
                create_user_contact_buttons(add_reset_button=True)

    elif user_data['registration_state'] == RegistrationState.WAIT_FOR_USER_AGE:
        user_age = get_user_age(update)
        validate_status = validate_user_age(user_age)
        if validate_status:
            set_user_age(user_data, user_age)
            send_is_our_student_message()
            create_is_our_student_buttons(add_reset_button=True)
            set_registration_state(user_data, RegistrationState.WAIT_FOR_IS_OUR_STUDENT)
        else:
            send_user_age_validation_error_message()

    elif user_data['registration_state'] == RegistrationState.WAIT_FOR_IS_OUR_STUDENT:
        if update.callback_query.data == 'is_our_student_yes':
            set_is_our_student(user_data, True)
        else:
            set_is_our_student(user_data, False)
        timeslots = get_active_timeslots_from_db()
        send_event_timeslot_message(timeslots=timeslots)
        create_event_timeslot_buttons(timeslots=timeslots, add_reset_button=True)
        set_registration_state(user_data, RegistrationState.WAIT_FOR_EVENT_TIMESLOT)

    elif user_data['registration_state'] == RegistrationState.WAIT_FOR_EVENT_TIMESLOT:
        if update.callback_query.data.startswith == 'timeslot_':
            timeslot = update.callback_query.data.split('_')[1]
            set_event_timeslot(user_data, timeslot)
            send_data_writing_message()
            set_registration_state(user_data, RegistrationState.WAIT_FOR_DATA_WRITTEN_TO_SPREADSHEETS)
            add_data_save_task_to_queue(user_data, on_complete=finish_registration)
        else:
            send_event_timeslot_validation_error_message()
            timeslots = get_active_timeslots_from_db()
            create_event_timeslot_buttons(timeslots=timeslots, add_reset_button=True)

    await dp.feed_update(bot, update)
    return {"ok": True}


async def finish_registration(user_data: dict):
    remove_all_buttons()
    set_registration_state(user_data, RegistrationState.REGISTRATION_COMPLETE)
    send_registration_complete_message()
