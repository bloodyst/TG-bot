import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import asyncio
from datetime import datetime
from fastapi import FastAPI
import uvicorn
import threading
import os

# Создаем фиктивный веб-сервер
app = FastAPI()

@app.get("/")
def home():
    return {"status": "Bot is running!"}

def run_webserver():
    """Запускает веб-сервер в отдельном потоке"""
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 10000)),  # Render сам подставляет порт
        log_level="error"
    )

bot = Bot(token="7247653323:AAFrKE9L1hYCloZTHm32KCrqoeB4fwGBmoU")
dp = Dispatcher()

# Данные игры
players = {}
LOCATIONS = {
    "Лес": {"дерево": (5, 15), "ягоды": (1, 5)},
    "Шахта": {"камень": (10, 20), "руда": (3, 8)},
    "Болото": {"грибы": (2, 7), "грязь": (1, 10)}
}

IMAGE_URLS = {
    "farm": "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExNWl3OTlkczV2enNqYmw3ZzkzOG1tNzBrNTlyNnczcHBqdnd3MXd6cCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/XElbX0BRDLvfh3aCtb/giphy.gif",
    "fight_start": "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExdGt1bG53aWk1eWJpMXE2N2l5Nzl4ZDJwajc4OWRnNWZxYmxuamZhZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/ITbG1hODpTGwrVaAhl/giphy.gif",
    "fight_win": "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExdHZ0eGFkbnJuaGJpa3B5NGF5cjE4OWF5NXIzcDNta3M1NWtqY3lyNCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xwPacBOcCu2z5ttwnw/giphy.gif",
    "fight_lose": "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExejdzNW9icjdjYXQ3MGY3ZWNsY2w1OGVrOWpqODRhaGwzeDExcDEyZiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/ateoIuZ8jvhyOUFwoD/giphy.gif",
    "boss_start": "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExc2pzaHVoMWhtbHl6eGFqNG5nN2lxdjZuaXdtcmR6OWd4OXZ4cmgzYSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/2Pk9newN8fkbu/giphy.gif",  # Заменил на работающую гифку
    "boss_win": "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExamR5bjJrNzJvdXFoYWxmeDUyb2djcHh3azExZ3docmEwOWltdnZyaSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l0HlwGH5lFhL5YAxy/giphy.gif",  # Заменил на работающую гифку
    "boss_lose": "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExem5jZHh1NmZ5Y2g4cm56d3J1cHUwMjJ3ZGFwdnkwb216d3hkcWJlcCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/adhayxttIGZuU/giphy.gif",  # Заменил на работающую гифку
    "inventory": "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExcGZ3dHVjanllNWxmOTBjbnFqaGdsNG01N2F5c29hNXc4MWU3ODQ2OSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l378xcbxNV5QYfygg/giphy.gifm"  # Пример картинки инвентаря
}


class Player:
    def __init__(self, user_id):
        self.user_id = user_id
        self.level = 1
        self.exp = 0
        self.resources = {res: 0 for loc in LOCATIONS.values() for res in loc}
        self.inventory = {
            "меч": 0,
            "броня": 0,
            "зелье": 0,
            "эпический меч": 0,
            "драконья броня": 0
        }
        self.health = 100
        self.max_health = 100
        self.location = "Лес"
        self.farm_count = 0
        self.fight_count = 0
        self.last_farm_time = None
        self.last_fight_time = None

    def add_exp(self, amount):
        self.exp += amount
        if self.exp >= self.level * 100:
            return self.level_up()
        return ""

    def level_up(self):
        self.level += 1
        self.exp = 0
        self.max_health += 20
        self.health = self.max_health
        return f"🎉 Ты достиг {self.level} уровня! Теперь у тебя +20 HP!"

    def get_health_bar(self):
        filled = int(self.health / self.max_health * 10)
        return f"❤️ [{'|' * filled}{'_' * (10 - filled)}] {self.health}%"


CRAFT_RECIPES = {
    "меч": {"дерево": 5, "камень": 3},
    "броня": {"дерево": 8, "камень": 5},
    "зелье": {"ягоды": 3, "грибы": 2},
    "эпический меч": {"руда": 10, "золото": 5},
    "драконья броня": {"руда": 15, "золото": 8}
}


def get_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛠 Фармить"), KeyboardButton(text="⚔️ Драться")],
            [KeyboardButton(text="👑 Босс"), KeyboardButton(text="🌲 Локация")],
            [KeyboardButton(text="🎒 Инвентарь"), KeyboardButton(text="📊 Статы")],
            [KeyboardButton(text="🔧 Крафт")]
        ],
        resize_keyboard=True
    )


def get_location_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌲 Лес"), KeyboardButton(text="⛏️ Шахта")],
            [KeyboardButton(text="🐊 Болото"), KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )


def get_craft_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔨 Крафт меча"), KeyboardButton(text="🛡️ Крафт брони")],
            [KeyboardButton(text="🧪 Крафт зелья"), KeyboardButton(text="⚔️ Крафт эпического меча")],
            [KeyboardButton(text="🐉 Крафт драконьей брони"), KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )


def check_cooldown(player, action):
    now = datetime.now()
    if action == "farm":
        if player.farm_count >= 3:
            if player.last_farm_time and (now - player.last_farm_time).seconds < 3:
                return f"⏳ Фарм на кулдауне! Жди {3 - (now - player.last_farm_time).seconds} сек."
            player.farm_count = 0
        player.last_farm_time = now
        player.farm_count += 1
    elif action == "fight":
        if player.fight_count >= 2:
            if player.last_fight_time and (now - player.last_fight_time).seconds < 10:
                return f"⏳ Драки на кулдауне! Жди {10 - (now - player.last_fight_time).seconds} сек."
            player.fight_count = 0
        player.last_fight_time = now
        player.fight_count += 1
    return None


@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in players:
        players[user_id] = Player(user_id)
    await message.answer(
        f"🚀 Добро пожаловать в игру!\n"
        f"Текущая локация: 🌲 {players[user_id].location}\n"
        f"{players[user_id].get_health_bar()}",
        reply_markup=get_main_kb()
    )


@dp.message(lambda msg: msg.text == "🔧 Крафт")
async def open_craft(message: types.Message):
    await message.answer("Выбери что крафтить:", reply_markup=get_craft_kb())


@dp.message(lambda msg: msg.text in ["🔨 Крафт меча", "🛡️ Крафт брони", "🧪 Крафт зелья",
                                     "⚔️ Крафт эпического меча", "🐉 Крафт драконьей брони"])
async def handle_craft(message: types.Message):
    user_id = message.from_user.id
    player = players.get(user_id)

    if not player:
        await message.answer("Сначала напиши /start")
        return

    item_map = {
        "🔨 Крафт меча": "меч",
        "🛡️ Крафт брони": "броня",
        "🧪 Крафт зелья": "зелье",
        "⚔️ Крафт эпического меча": "эпический меч",
        "🐉 Крафт драконьей брони": "драконья броня"
    }

    item = item_map.get(message.text)
    if not item:
        await message.answer("❌ Неизвестный предмет")
        return

    recipe = CRAFT_RECIPES.get(item, {})
    missing = []

    for res, needed in recipe.items():
        if player.resources.get(res, 0) < needed:
            missing.append(f"{res} (нужно {needed}, есть {player.resources.get(res, 0)})")

    if missing:
        await message.answer(
            f"❌ Не хватает ресурсов для {item}:\n" + "\n".join(missing),
            reply_markup=get_craft_kb()
        )
    else:
        for res, needed in recipe.items():
            player.resources[res] -= needed
        player.inventory[item] += 1

        await message.answer(
            f"🎉 Ты скрафтил {item}!\n"
            f"Теперь у тебя {player.inventory[item]} шт.",
            reply_markup=get_main_kb()
        )


@dp.message(lambda msg: msg.text == "🎒 Инвентарь")
async def show_inventory(message: types.Message):
    user_id = message.from_user.id
    player = players.get(user_id)

    if not player:
        await message.answer("Сначала напиши /start", reply_markup=ReplyKeyboardRemove())
        return

    try:
        # Формируем текст для предметов
        items_text = "🔮 Предметы:\n"
        has_items = False
        for item, count in player.inventory.items():
            if count > 0:
                items_text += f"• {item.capitalize()}: {count} шт.\n"
                has_items = True

        if not has_items:
            items_text += "Пусто\n"

        # Формируем текст для ресурсов
        resources_text = "\n📦 Ресурсы:\n"
        has_resources = False
        for resource, count in player.resources.items():
            if count > 0:
                resources_text += f"• {resource.capitalize()}: {count} шт.\n"
                has_resources = True

        if not has_resources:
            resources_text += "Пусто\n"

        # Отправляем картинку и текст
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=IMAGE_URLS["inventory"],
            caption=items_text + resources_text,
            reply_markup=get_main_kb()
        )

    except Exception as e:
        print(f"Ошибка в инвентаре: {e}")
        await message.answer("🔧 Инвентарь временно недоступен. Попробуй позже.")


@dp.message(lambda msg: msg.text in ["🛠 Фармить", "⚔️ Драться", "👑 Босс", "📊 Статы", "🌲 Локация"])
async def handle_actions(message: types.Message):
    user_id = message.from_user.id
    player = players.get(user_id)

    if not player:
        await message.answer("Сначала напиши /start", reply_markup=ReplyKeyboardRemove())
        return

    action = message.text

    if action == "🛠 Фармить":
        cooldown_msg = check_cooldown(player, "farm")
        if cooldown_msg:
            await message.answer(cooldown_msg)
            return

        await bot.send_animation(
            chat_id=message.chat.id,
            animation=IMAGE_URLS["farm"],
            caption=f"🛠 Ты фармишь в {player.location}..."
        )

        resources = LOCATIONS[player.location]
        resource = random.choice(list(resources.keys()))
        amount = random.randint(*resources[resource])
        player.resources[resource] += amount
        level_up_msg = player.add_exp(5)

        response = (
            f"🛠 Ты добыл {amount} {resource}!\n"
            f"📦 Теперь у тебя: {player.resources[resource]} {resource}\n"
            f"🔥 +5 опыта!\n\n"
            f"{player.get_health_bar()}"
        )

        if level_up_msg:
            response += f"\n\n{level_up_msg}"

    elif action == "⚔️ Драться":
        cooldown_msg = check_cooldown(player, "fight")
        if cooldown_msg:
            await message.answer(cooldown_msg)
            return

        await bot.send_animation(
            chat_id=message.chat.id,
            animation=IMAGE_URLS["fight_start"],
            caption="⚔️ Ты вступаешь в бой!"
        )

        enemy_hp = random.randint(10, 30)
        player_dmg = random.randint(5, 15) + (player.inventory["меч"] * 5) + (player.inventory["эпический меч"] * 15)
        enemy_dmg = random.randint(3, 10)

        response = (
            f"⚔️ Битва началась! У врага {enemy_hp} HP.\n"
            f"Ты наносишь {player_dmg} урона.\n\n"
            f"{player.get_health_bar()}"
        )

        while enemy_hp > 0 and player.health > 0:
            enemy_hp -= player_dmg
            if enemy_hp <= 0:
                await bot.send_animation(
                    chat_id=message.chat.id,
                    animation=IMAGE_URLS["fight_win"],
                    caption="✅ Ты победил врага!"
                )
                level_up_msg = player.add_exp(15)
                loot = random.choice(["меч", "броня", "зелье"])
                player.inventory[loot] += 1
                response += f"\n\n🎁 Получено: 1 {loot}!\n🔥 +15 опыта!"
                if level_up_msg:
                    response += f"\n\n{level_up_msg}"
                break

            player.health -= max(1, enemy_dmg - player.inventory["броня"] * 3 - player.inventory["драконья броня"] * 5)
            if player.health <= 0:
                player.health = 1
                await bot.send_animation(
                    chat_id=message.chat.id,
                    animation=IMAGE_URLS["fight_lose"],
                    caption="💀 Ты еле выжил..."
                )
                response += "\n\nВраг тебя почти добил."
                break

    elif action == "👑 Босс":
        if player.level < 3:
            await message.answer("❌ Ты слишком слаб для босса! Набери 3+ уровень.")
            return

        cooldown_msg = check_cooldown(player, "fight")
        if cooldown_msg:
            await message.answer(cooldown_msg)
            return

        await bot.send_animation(
            chat_id=message.chat.id,
            animation=IMAGE_URLS["boss_start"],
            caption="👹 Появился БОСС! Он страшный!"
        )

        boss_hp = 100
        player_dmg = random.randint(10, 25) + (player.inventory["меч"] * 5) + (player.inventory["эпический меч"] * 15)
        boss_dmg = random.randint(15, 30)

        response = (
            f"👹 Босс: 100 HP\n"
            f"Ты наносишь {player_dmg} урона.\n\n"
            f"{player.get_health_bar()}"
        )

        while boss_hp > 0 and player.health > 0:
            boss_hp -= player_dmg
            if boss_hp <= 0:
                await bot.send_animation(
                    chat_id=message.chat.id,
                    animation=IMAGE_URLS["boss_win"],
                    caption="🎖 Ты УБИЛ БОССА!"
                )
                level_up_msg = player.add_exp(50)
                player.resources["золото"] += 50
                response += "\n\n💰 +50 золота!\n🔥 +50 опыта!"
                if level_up_msg:
                    response += f"\n\n{level_up_msg}"
                break

            player.health -= max(1, boss_dmg - player.inventory["броня"] * 3 - player.inventory["драконья броня"] * 5)
            if player.health <= 0:
                player.health = 1
                await bot.send_animation(
                    chat_id=message.chat.id,
                    animation=IMAGE_URLS["boss_lose"],
                    caption="☠️ Босс тебя размазал..."
                )
                response += "\n\nЕле выжил."
                break

    elif action == "🌲 Локация":
        await message.answer("Выбери локацию:", reply_markup=get_location_kb())
        return

    elif action == "📊 Статы":
        response = (
            f"📊 Твоя статистика:\n"
            f"📍 Локация: {player.location}\n"
            f"{player.get_health_bar()}\n"
            f"📈 Уровень: {player.level}\n"
            f"🔥 Опыт: {player.exp}/{player.level * 100}\n"
            f"🗡️ Урон: {10 + player.inventory['меч'] * 5 + player.inventory['эпический меч'] * 15}\n"
            f"🛡️ Защита: {player.inventory['броня'] * 3 + player.inventory['драконья броня'] * 5}"
        )

    await message.answer(response, reply_markup=get_main_kb())


@dp.message(lambda msg: msg.text in ["🌲 Лес", "⛏️ Шахта", "🐊 Болото", "🔙 Назад"])
async def handle_locations(message: types.Message):
    user_id = message.from_user.id
    player = players.get(user_id)

    if not player:
        await message.answer("Сначала напиши /start")
        return

    if message.text == "🔙 Назад":
        await message.answer("Меню:", reply_markup=get_main_kb())
        return

    player.location = message.text.split()[1]
    await message.answer(
        f"Ты переместился в {player.location}!",
        reply_markup=get_main_kb()
    )


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
