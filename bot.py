import asyncio
import random
import string
import os
import asyncpg

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton
)

# ---------- INIT ----------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DB_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

db = None


# ---------- FSM ----------
class JoinForm(StatesGroup):
    name = State()


class PollForm(StatesGroup):
    question = State()
    options = State()

class BetForm(StatesGroup):
    question = State()
    payment_link = State()

# ---------- DB ----------
async def create_pool():
    global db
    db = await asyncpg.create_pool(DB_URL)


# ---------- UTILS ----------
def generate_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


# ---------- KEYBOARDS ----------
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎄 Создать комнату")],
        ],
        resize_keyboard=True
    )


def creator_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Участники")],
            [KeyboardButton(text="💰 Опрос с оплатой")]
        ],
        resize_keyboard=True
    )


# ---------- START ----------
@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    args = message.text.split()

    if len(args) > 1:
        code = args[1]

        room = await db.fetchrow("SELECT * FROM rooms WHERE code=$1", code)
        if not room:
            await message.answer("❌ Комната не найдена")
            return

        await state.update_data(room_id=room["id"])
        await state.set_state(JoinForm.name)

        await message.answer("Введите ваше имя:")
    else:
        await message.answer(
            "Добро пожаловать!",
            reply_markup=main_menu()
        )


# ---------- CREATE ROOM ----------
@dp.message(F.text == "🎄 Создать комнату")
async def create_room(message: types.Message):
    code = generate_code()

    await db.execute(
        "INSERT INTO rooms (code, creator_id) VALUES ($1, $2)",
        code, message.from_user.id
    )

    link = f"https://t.me/{(await bot.me()).username}?start={code}"

    await message.answer(
        f"Комната создана!\n\nСсылка:\n{link}",
        reply_markup=creator_menu()
    )


# ---------- JOIN ----------
@dp.message(JoinForm.name)
async def join_room(message: types.Message, state: FSMContext):
    data = await state.get_data()
    room_id = data["room_id"]

    exists = await db.fetchrow(
        "SELECT * FROM participants WHERE user_id=$1 AND room_id=$2",
        message.from_user.id, room_id
    )

    if exists:
        await message.answer("Вы уже в комнате")
        await state.clear()
        return

    await db.execute(
        "INSERT INTO participants (user_id, room_id, name) VALUES ($1, $2, $3)",
        message.from_user.id, room_id, message.text
    )

    await message.answer("Вы вошли в комнату")
    await state.clear()


# ---------- LIST PARTICIPANTS ----------
@dp.message(F.text == "👥 Участники")
async def list_participants(message: types.Message):
    room = await db.fetchrow(
        "SELECT * FROM rooms WHERE creator_id=$1",
        message.from_user.id
    )

    if not room:
        await message.answer("Вы не создатель комнаты")
        return

    users = await db.fetch(
        "SELECT name FROM participants WHERE room_id=$1",
        room["id"]
    )

    text = "Участники:\n\n"
    for u in users:
        text += f"• {u['name']}\n"

    await message.answer(text)


@dp.message(F.text == "💰 Опрос с оплатой")
async def start_bet(message: types.Message, state: FSMContext):
    await state.set_state(BetForm.question)
    await message.answer("❓ Введите вопрос:")


@dp.message(BetForm.question)
async def get_question(message: types.Message, state: FSMContext):
    await state.update_data(question=message.text)
    await state.set_state(BetForm.payment_link)

    await message.answer("💰 Вставь ссылку на оплату:")


@dp.message(BetForm.payment_link)
async def send_poll(message: types.Message, state: FSMContext):
    data = await state.get_data()
    question = data["question"]
    link = message.text

    # проверяем комнату
    room = await db.fetchrow(
        "SELECT * FROM rooms WHERE creator_id=$1",
        message.from_user.id
    )

    if not room:
        await message.answer("❌ Ты не создатель комнаты")
        return

    users = await db.fetch(
        "SELECT user_id FROM participants WHERE room_id=$1",
        room["id"]
    )

    if not users:
        await message.answer("❌ Нет участников")
        return

    sent = 0

    for user in users:
        try:
            # сообщение
            await bot.send_message(
                chat_id=user["user_id"],
                text=(
                    f"❓ {question}\n\n"
                    f"🗳 Проголосуй ниже\n"
                    f"💰 Участвовать:\n{link}"
                )
            )

            # poll
            await bot.send_poll(
                chat_id=user["user_id"],
                question=question,
                options=["Да", "Нет"],
                is_anonymous=False
            )

            sent += 1

        except:
            pass  # пользователь не открыл чат

    await message.answer(f"✅ Отправлено: {sent} участникам")
    await state.clear()


# ---------- MAIN ----------
async def main():
    await create_pool()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
