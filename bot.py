import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

# Если удобнее из .env, можно заменить на dotenv; здесь для простоты:
from config import TOKEN

logging.basicConfig(level=logging.INFO)

# --- Инициализация бота/диспетчера ---
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- Состояния формы ---
class Form(StatesGroup):
    name = State()
    age = State()
    grade = State()

# --- Инициализация БД и таблицы ---
def init_db():
    conn = sqlite3.connect('school_data.db')  # по заданию
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            grade TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Хэндлеры ---
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Привет! Давай запишем тебя в базу.\nКак тебя зовут?")
    await state.set_state(Form.name)

@dp.message(Form.name)
async def get_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if not name:
        await message.answer("Имя не может быть пустым. Введи имя ещё раз:")
        return
    await state.update_data(name=name)
    await message.answer("Сколько тебе лет? (целое число)")
    await state.set_state(Form.age)

@dp.message(Form.age)
async def get_age(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    try:
        age = int(text)
        if age <= 0 or age > 120:
            await message.answer("Возраст должен быть от 1 до 120. Введи возраст ещё раз:")
            return
    except ValueError:
        await message.answer("Нужно целое число. Введи возраст ещё раз:")
        return

    await state.update_data(age=age)
    await message.answer("В каком ты классе (grade)? Например: 5А, 7 или 10Б.")
    await state.set_state(Form.grade)

@dp.message(Form.grade)
async def get_grade(message: Message, state: FSMContext):
    grade = (message.text or "").strip()
    if not grade:
        await message.answer("Класс (grade) не может быть пустым. Укажи класс ещё раз:")
        return

    data = await state.update_data(grade=grade)
    data = await state.get_data()

    # --- Сохранение в БД ---
    conn = sqlite3.connect('school_data.db')
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO students (name, age, grade) VALUES (?, ?, ?)",
        (data["name"], data["age"], data["grade"])
    )
    conn.commit()
    conn.close()

    await message.answer(
        "Готово! Я записал данные в базу:\n"
        f"Имя: {data['name']}\n"
        f"Возраст: {data['age']}\n"
        f"Класс: {data['grade']}"
    )

    await state.clear()

# --- Точка входа ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
