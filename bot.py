import asyncio
import random
import string
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
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
        await message.answer("🎅 /create — создать комнату")


@dp.message(Command("create"))
async def create_room(message: types.Message):
    code = generate_code()

    await db.execute(
        "INSERT INTO rooms (code, creator_id) VALUES ($1, $2)",
        code, message.from_user.id
    )

    link = f"https://t.me/{(await bot.me()).username}?start={code}"

    await message.answer(f"🎄 Комната создана!\nСсылка для друзей:\n{link}")


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


@dp.message(Command("draw"))
async def draw(message: types.Message):
    room = await db.fetchrow(
        "SELECT * FROM rooms WHERE creator_id=$1",
        message.from_user.id
    )

    if not room:
        await message.answer("❌ Вы не создатель комнаты")
        return

    if room["is_drawn"]:
        await message.answer("⚠️ Жеребьёвка уже была")
        return

    users = await db.fetch(
        "SELECT user_id, name FROM participants WHERE room_id=$1",
        room["id"]
    )

    if len(users) < 2:
        await message.answer("❌ Нужно минимум 2 участника")
        return

    user_ids = [u["user_id"] for u in users]
    pairs = draw_pairs(user_ids)

    for giver, receiver in pairs:
        receiver_name = next(u["name"] for u in users if u["user_id"] == receiver)

        await bot.send_message(
            giver,
            f"🎁 Ты даришь подарок: {receiver_name}"
        )

        await db.execute(
            "INSERT INTO assignments (giver_id, receiver_id, room_id) VALUES ($1, $2, $3)",
            giver, receiver, room["id"]
        )

    await db.execute(
        "UPDATE rooms SET is_drawn=TRUE WHERE id=$1",
        room["id"]
    )

    await message.answer("🎉 Жеребьёвка проведена!")


# ---------- MAIN ----------
async def main():
    await create_pool()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())