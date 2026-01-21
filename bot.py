import asyncio
import random
import time
import sqlite3

from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# ================== НАСТРОЙКИ ==================
TOKEN = "8537764396:AAEZFTs7mgHqTjQbDh6eSyKtQJvwlPnJazY"
HUNT_COOLDOWN = 240  # 4 минуты
EXP_PER_LEVEL = 500

# ================== ДАННЫЕ ==================
LOCATIONS = {
    "Тайга": {"level": 0, "animals": {
        "Мелкая дичь": ["Заяц", "Белка", "Бурундук", "Рябчик", "Выдра", "Ласка", "Горностай"],
        "Средние": ["Бобр", "Глухарь", "Северный олень", "Косуля"],
        "Опасные": ["Кабан", "Рысь", "Росомаха", "Серый волк", "Бурый медведь"],
        "Тяжелые": [],
        "Титаны": ["Оборотень"]
    }},
    "Саванна": {"level": 10, "animals": {
        "Мелкая дичь": ["Дикобраз", "Мангуст", "Сурикат", "Антилоповый заяц"],
        "Средние": ["Зебра", "Шакал", "Антилопа Гну", "Антилопа Импала", "Страус", "Бородавочник", "Сервал"],
        "Опасные": ["Гиена", "Пума", "Лев"],
        "Тяжелые": ["Жираф", "Буйвол", "Слон"],
        "Титаны": []
    }},
    "Арктика": {"level": 25, "animals": {
        "Мелкая дичь": ["Лемминг", "Песец", "Арктический заяц"],
        "Средние": ["Полярная сова", "Тюлень", "Северный олень (Карибу)"],
        "Опасные": ["Снежный барс", "Белый медведь"],
        "Тяжелые": ["Морж", "Белуха", "Овцебык", "Косатка"],
        "Титаны": ["Мамонт", "Йети"]
    }},
    "Джунгли": {"level": 50, "animals": {
        "Мелкая дичь": ["Капибара", "Ленивец"],
        "Средние": ["Окапи", "Обезьяна", "Казуар", "Тапир"],
        "Опасные": ["Комодский варан", "Крокодил", "Анаконда", "Ягуар", "Горилла", "Тигр", "Пантера"],
        "Тяжелые": ["Носорог"],
        "Титаны": ["Чупакабра"]
    }},
    "Древний мир": {"level": 80, "animals": {
        "Мелкая дичь": [],
        "Средние": ["Велоцираптор", "Динопитек"],
        "Опасные": ["Смилодон", "Энтелодонт", "Келенкен", "Гиенодон"],
        "Тяжелые": ["Трицератопс", "Стегозавр", "Гадрозавр", "Эласмотерии", "Магелания", "Шерстистый носорог"],
        "Титаны": ["Тираннозавр", "Брахиозавр", "Птеродактиль"]
    }},
}

SEARCH_CHANCES = {
    "Мелкая дичь": 60,
    "Средние": 45,
    "Опасные": 20,
    "Тяжелые": 5,
    "Титаны": 1
}

REWARDS = {
    "Мелкая дичь": (30, 50),
    "Средние": (140, 250),
    "Опасные": (600, 1000),
    "Тяжелые": (4000, 3000),
    "Титаны": (20000, 10000)
}

WEAPONS = {
    "Револьвер": [55, 20, 3, 0.5, 0.01],
    "Дробовик": [65, 40, 8, 1, 0.1],
    "Винтовка": [25, 60, 20, 5, 0.5],
    "Карабин": [30, 50, 45, 10, 2],
    "Штуцер": [15, 35, 65, 30, 5],
    "Слонобой": [10, 20, 40, 65, 15],
    "Снайперка": [30, 40, 55, 65, 55]
}

WEAPON_PRICES = {
    "Револьвер": 0,
    "Дробовик": 1500,
    "Винтовка": 6000,
    "Карабин": 18000,
    "Штуцер": 45000,
    "Слонобой": 120000,
    "Снайперка": 400000
}

STICKERS = {"Заяц": "", "Белка": "", "Бобр": "", "Кабан": "", "Лев": "", "Тираннозавр": ""}

# ================== БАЗА ДАННЫХ ==================
db = sqlite3.connect("hunt.db")
sql = db.cursor()

sql.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    coins INTEGER,
    exp INTEGER,
    weapon TEXT,
    location TEXT,
    last_hunt INTEGER
)
""")
sql.execute("""
CREATE TABLE IF NOT EXISTS trophies (
    user_id INTEGER,
    animal TEXT,
    count INTEGER
)
""")
sql.execute("""
CREATE TABLE IF NOT EXISTS user_weapons (
    user_id INTEGER,
    weapon TEXT,
    UNIQUE(user_id, weapon)
)
""")
db.commit()

# ================== ФУНКЦИИ ==================
def get_level(exp: int) -> int:
    return exp // EXP_PER_LEVEL

def ensure_user(user_id: int):
    user = sql.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not user:
        sql.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, 0, 0, "Револьвер", "Тайга", 0)
        )
        sql.execute(
            "INSERT OR IGNORE INTO user_weapons VALUES (?, ?)",
            (user_id, "Револьвер")
        )
        db.commit()
        user = sql.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return user

def choose_animal(location: str):
    available_groups = [g for g in SEARCH_CHANCES if LOCATIONS[location]["animals"].get(g)]
    if not available_groups:
        return None, None
    weights = [SEARCH_CHANCES[g] for g in available_groups]
    group = random.choices(available_groups, weights=weights)[0]
    if random.randint(1, 100) > SEARCH_CHANCES[group]:
        return None, None
    animal = random.choice(LOCATIONS[location]["animals"][group])
    return group, animal

def check_hit(weapon: str, group: str):
    idx = ["Мелкая дичь", "Средние", "Опасные", "Тяжелые", "Титаны"].index(group)
    chance = WEAPONS[weapon][idx]
    return random.uniform(0, 100) <= chance

def can_use_location(user_level: int, location_name: str) -> bool:
    return user_level >= LOCATIONS[location_name]["level"]

# ================== БОТ ==================
bot = Bot(TOKEN)
dp = Dispatcher()

# ================== /start ==================
@dp.message(Command("start"))
async def start(msg: Message):
    ensure_user(msg.from_user.id)
    await msg.answer("🏹 Добро пожаловать на охоту!\nКоманды:\nХант — начать охоту\nИнв — посмотреть снаряжение\nМагазин — купить оружие\nЛокация — выбрать локацию\nСправка — информация о боте")

# ================== СПРАВКА ==================
@dp.message(lambda msg: msg.text and msg.text.lower() == "справка")
async def help_command(msg: Message):
    await msg.answer("Если есть вопросы/проблемы с ботом/идеи для обновлений то напиши @DeepSleep01")

# ================== ХАНТ ==================
@dp.message(lambda msg: msg.text and msg.text.lower() == "хант")
async def hunt(msg: Message):
    user = ensure_user(msg.from_user.id)
    now = int(time.time())
    if now - user[5] < HUNT_COOLDOWN:
        wait = HUNT_COOLDOWN - (now - user[5])
        await msg.answer(f"⏳ Подожди {wait // 60} мин {wait % 60} сек.")
        return
    sql.execute("UPDATE users SET last_hunt = ? WHERE user_id = ?", (now, msg.from_user.id))
    db.commit()
    group, animal = choose_animal(user[4])
    if not animal:
        await msg.answer(f"Ты блуждаешь по {user[4]}, но поиски безуспешны.")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
        text="🔫 Выстрел",
        callback_data=f"shoot:{msg.from_user.id}:{group}:{animal}"
    )]])
    await msg.answer(f"Ты блуждаешь по {user[4]} и внезапно замечаешь {animal}!", reply_markup=kb)

# ================== ВЫСТРЕЛ ==================
@dp.callback_query(lambda c: c.data.startswith("shoot"))
async def shoot(call):
    owner_id, group, animal = call.data.split(":")[1:]
    if int(owner_id) != call.from_user.id:
        await call.answer("❌ Это не твоя охота!", show_alert=True)
        return
    user = ensure_user(call.from_user.id)
    if not check_hit(user[3], group):
        await call.message.edit_text("❌ К сожалению, вы промахнулись.")
        return
    coins, exp = REWARDS[group]
    sql.execute("UPDATE users SET coins = coins + ?, exp = exp + ? WHERE user_id = ?", (coins, exp, call.from_user.id))
    trophy = sql.execute("SELECT count FROM trophies WHERE user_id = ? AND animal = ?", (call.from_user.id, animal)).fetchone()
    if trophy:
        sql.execute("UPDATE trophies SET count = count + 1 WHERE user_id = ? AND animal = ?", (call.from_user.id, animal))
    else:
        sql.execute("INSERT INTO trophies VALUES (?, ?, ?)", (call.from_user.id, animal, 1))
    db.commit()
    if STICKERS.get(animal):
        await call.message.answer_sticker(STICKERS[animal])
    await call.message.edit_text(f"🎯 Прямое попадание!\nТрофей: {animal}\nМонеты: +{coins}\nОпыт: +{exp}")

# ================== ИНВЕНТАРЬ ==================
@dp.message(lambda msg: msg.text and msg.text.lower() == "инв")
async def inventory(msg: Message):
    user = ensure_user(msg.from_user.id)
    trophies = sql.execute("SELECT animal, count FROM trophies WHERE user_id = ?", (msg.from_user.id,)).fetchall()
    
    groups = ["Мелкая дичь", "Средние", "Опасные", "Тяжелые", "Титаны"]
    grouped_trophies = {g: [] for g in groups}
    
    for animal, count in trophies:
        for group, animals_in_group in LOCATIONS[user[4]]["animals"].items():
            if animal in animals_in_group:
                grouped_trophies[group].append((animal, count))
                break
    
    text = f"🎒 Инвентарь\n\n🔫 Оружие: {user[3]}\n📍 Локация: {user[4]}\n💰 Монеты: {user[1]}\n⭐ Уровень: {get_level(user[2])}\n📊 Опыт: {user[2]}\n\n🏆 Трофеи:\n"
    
    for group in groups:
        text += f"\n{group}:\n"
        if grouped_trophies[group]:
            for a, c in grouped_trophies[group]:
                text += f"{a} — {c} шт.\n"
        else:
            text += "— нет трофеев —\n"
    
    await msg.answer(text)

# ================== МАГАЗИН ==================
@dp.message(lambda msg: msg.text and msg.text.lower() == "магазин")
async def shop(msg: Message):
    user = ensure_user(msg.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
        text=f"{w} — {p}💰",
        callback_data=f"buy:{msg.from_user.id}:{w}"
    )] for w, p in WEAPON_PRICES.items()])
    await msg.answer(f"💰 Монеты: {user[1]}\nВыберите оружие для покупки:", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("buy"))
async def buy(call):
    user = ensure_user(call.from_user.id)
    weapon = call.data.split(":")[2]  # <-- Исправлено

    owned = sql.execute(
        "SELECT 1 FROM user_weapons WHERE user_id = ? AND weapon = ?",
        (call.from_user.id, weapon)
    ).fetchone()

    if owned:
        sql.execute(
            "UPDATE users SET weapon = ? WHERE user_id = ?",
            (weapon, call.from_user.id)
        )
        db.commit()
        await call.message.edit_text(f"🔄 Вы выбрали оружие: {weapon}")
        return

    price = WEAPON_PRICES[weapon]
    if user[1] < price:
        await call.message.edit_text("❌ Недостаточно монет.")
        return

    sql.execute(
        "UPDATE users SET coins = coins - ? WHERE user_id = ?",
        (price, call.from_user.id)
    )
    sql.execute(
        "INSERT OR IGNORE INTO user_weapons VALUES (?, ?)",
        (call.from_user.id, weapon)
    )
    sql.execute(
        "UPDATE users SET weapon = ? WHERE user_id = ?",
        (weapon, call.from_user.id)
    )
    db.commit()

    await call.message.edit_text(f"✅ Вы купили {weapon} и выбрали его!")

# ================== ЛОКАЦИИ ==================
@dp.message(lambda msg: msg.text and msg.text.lower() == "локация")
async def choose_location(msg: Message):
    user = ensure_user(msg.from_user.id)
    level = get_level(user[2])
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
        text=name,
        callback_data=f"setloc:{msg.from_user.id}:{name}"
    )] for name in LOCATIONS])
    await msg.answer(f"Выберите локацию (Ваш уровень: {level}):", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("setloc"))
async def set_location(call):
    owner_id, location = call.data.split(":")[1:]
    if int(owner_id) != call.from_user.id:
        await call.answer("❌ Это не твоя локация!", show_alert=True)
        return
    user = ensure_user(call.from_user.id)
    level = get_level(user[2])
    if not can_use_location(level, location):
        await call.message.edit_text(f"❌ Эта локация доступна с уровня {LOCATIONS[location]['level']}.")
        return
    sql.execute("UPDATE users SET location = ? WHERE user_id = ?", (location, call.from_user.id))
    db.commit()
    await call.message.edit_text(f"✅ Локация изменена на {location}!")

# ================== ЗАПУСК ==================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


