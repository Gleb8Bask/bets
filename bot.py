import asyncio
import random
import string
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DB_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

db = None


# ---------- FSM ----------
class JoinForm(StatesGroup):
    name = State()


# ---------- DB ----------
async def create_pool():
    global db
    db = await asyncpg.create_pool(DB_URL)


# ---------- Utils ----------
def generate_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def draw_pairs(users):
    while True:
        shuffled = users[:]
        random.shuffle(shuffled)
        if all(u != s for u, s in zip(users, shuffled)):
            return list(zip(users, shuffled))

# ---------- Menu ----------
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎄 Создать комнату")],
            [KeyboardButton(text="🔑 Войти по коду")]
        ],
        resize_keyboard=True
    )

def creator_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Участники")],
            [KeyboardButton(text="🎲 Провести жеребьёвку")]
        ],
        resize_keyboard=True
    )

def confirm_draw():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data="draw_yes"),
                InlineKeyboardButton(text="❌ Нет", callback_data="draw_no")
            ]
        ]
    )

# ---------- Handlers ----------
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

        await message.answer("Введите своё имя:")
    else:
        await message.answer(
            "🎅 Добро пожаловать в Тайного Санту!",
            reply_markup=main_menu()
        )


@dp.message(lambda m: m.text == "🎄 Создать комнату")
async def create_room(message: types.Message):
    code = generate_code()

    await db.execute(
        "INSERT INTO rooms (code, creator_id) VALUES ($1, $2)",
        code, message.from_user.id
    )

    link = f"https://t.me/{(await bot.me()).username}?start={code}"

    await message.answer(
        f"🎉 Комната создана!\n\n"
        f"🔗 Пригласи друзей:\n{link}",
        reply_markup=creator_menu()
    )


@dp.message(JoinForm.name)
async def join_room(message: types.Message, state: FSMContext):
    data = await state.get_data()
    room_id = data["room_id"]

    await db.execute(
        "INSERT INTO participants (user_id, room_id, name) VALUES ($1, $2, $3)",
        message.from_user.id, room_id, message.text
    )

    await message.answer("✅ Вы в комнате!")
    await state.clear()


@dp.callback_query(lambda c: c.data == "draw_yes")
async def process_draw(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    room = await db.fetchrow(
        "SELECT * FROM rooms WHERE creator_id=$1",
        user_id
    )

    users = await db.fetch(
        "SELECT user_id, name FROM participants WHERE room_id=$1",
        room["id"]
    )

    user_ids = [u["user_id"] for u in users]
    pairs = draw_pairs(user_ids)

    for giver, receiver in pairs:
        receiver_name = next(u["name"] for u in users if u["user_id"] == receiver)

        await bot.send_message(
            giver,
            f"🎁 Ты даришь подарок: {receiver_name}"
        )

    await callback.message.answer("🎉 Готово!")
    await callback.answer()


@dp.message(lambda m: m.text == "🎲 Провести жеребьёвку")
async def confirm(message: types.Message):
    await message.answer(
        "⚠️ Провести жеребьёвку? Это нельзя отменить.",
        reply_markup=confirm_draw()
    )


@dp.message(lambda m: m.text == "👥 Участники")
async def list_participants(message: types.Message):
    room = await db.fetchrow(
        "SELECT * FROM rooms WHERE creator_id=$1",
        message.from_user.id
    )

    users = await db.fetch(
        "SELECT name FROM participants WHERE room_id=$1",
        room["id"]
    )

    text = "👥 Участники:\n\n"
    for u in users:
        text += f"• {u['name']}\n"

    await message.answer(text)



# ---------- MAIN ----------
async def main():
    await create_pool()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
