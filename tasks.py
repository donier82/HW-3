from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
import logging, sqlite3, asyncio
from config import token

bot = Bot(token=token)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

connection = sqlite3.connect("tasks.db", check_same_thread=False)
cursor = connection.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_id INTEGER,
        task TEXT
);
""")
connection.commit()

@dp.message(Command('start'))
async def start(message: Message):
    await message.answer("Привет! Я бот для управления задачами. Используй команду /add, чтобы добавить задачу, /view — чтобы посмотреть все задачи, и /delete — чтобы удалить задачу.")

@dp.message(Command('add'))
async def add_task(message: Message):
    await message.answer("Введите задачу в следующем сообщении:")

@dp.message(Command('view'))
async def view_notes(message: Message):
    cursor.execute("SELECT task FROM tasks WHERE user_id = ?", (message.from_user.id,))
    tasks = cursor.fetchall()
    if tasks:
        response = '\n'.join([note[0] for note in tasks])
    else:
        response = "У вас нет задач."
    await message.answer(response)

@dp.message()
async def save_task(message:Message):
    cursor.execute('INSERT INTO tasks (id, user_id, task) VALUES (?, ?, ?)', (message.message_id, message.from_user.id, message.text))
    connection.commit()
    await message.answer("Задача сохранена!")

@dp.message(Command('delete'))
async def delete(message: Message):
    cursor.execute("SELECT id, task FROM tasks WHERE user_id = ?", (message.from_user.id,))
    tasks = cursor.fetchall()

    if tasks:
        response = '\n'.join([f"{task[0]}. {task[1]}" for task in tasks])
        response += "\nВведите номер задачи, которую хотите удалить."
        await message.answer(response)
    else:
        await message.answer("У вас нет задач для удаления.")

@dp.message()
async def handle_message(message: Message):
    if message.reply_to_message:
        # Проверка на добавление задачи
        if 'Введите задачу в следующем сообщении' in message.reply_to_message.text:
            task_text = message.text
            print(f"Attempting to add task: {task_text}")  # Отладочное сообщение
            cursor.execute('INSERT INTO tasks (user_id, task) VALUES (?, ?)', (message.from_user.id, task_text))
            connection.commit()
            print("Task added successfully!")  # Отладочное сообщение
            await message.answer("Задача сохранена!")
        
        # Проверка на удаление задачи
        elif 'Введите номер задачи, которую хотите удалить' in message.reply_to_message.text:
            try:
                task_id = int(message.text)
                cursor.execute("SELECT id FROM tasks WHERE id = ? AND user_id = ?", (task_id, message.from_user.id))
                task = cursor.fetchone()
                if task:
                    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                    connection.commit()
                    await message.answer("Задача удалена!")
                else:
                    await message.answer("Задача с таким номером не найдена.")
            except ValueError:
                await message.answer("Пожалуйста, введите корректный номер задачи.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
