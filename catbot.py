import os
import random
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import URLInputFile
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CAT_API_KEY = os.getenv("CAT_API_KEY")  # Получи на thecatapi.com

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Только мемные категории котов (из документации API)
MEME_CATEGORIES = [
    1,  # "hats" - коты в шляпах
    2,  # "space" - коты в космосе
    4,  # "sunglasses" - в очках
    5,  # "boxes" - коты в коробках
    7,  # "ties",
    9,  # "dream",
    10, # "sinks"
]


async def get_meme_cat():
    """Тянем мемного кота через TheCatAPI"""
    url = "https://api.thecatapi.com/v1/images/search"
    params = {
        "api_key": CAT_API_KEY,
        "category_ids": random.choice(MEME_CATEGORIES)
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return URLInputFile(data[0]["url"])
        except Exception as e:
            print(f"Ошибка: {e}")
    return None


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "😼 <b>Смешные котики</b>\n"
        "Жми /meme или кнопку внизу!",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="Котики")]],
            resize_keyboard=True
        ),
        parse_mode="HTML"
    )


@dp.message(F.text == "Котики")
@dp.message(Command("meme"))
async def send_meme_cat(message: types.Message):
    cat_file = await get_meme_cat()
    if cat_file:
        await message.answer_photo(
            cat_file,
            caption="Вот такой миленький котеночек"
        )
    else:
        await message.answer("Смешные котики закончились :(")


async def main():
    print("Бот с мемными котами запущен! 🐱💥")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())