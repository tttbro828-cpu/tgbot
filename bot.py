import asyncio
import random
import time
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

# ================== НАСТРОЙКИ ==================
TOKEN = "7960395324:AAHdKfvfDlcyPQSMLASinEY-fdaEz5-WMUA"
HUNT_COOLDOWN = 240  # 4 минуты
EXP_PER_LEVEL = 500
ADMIN_ID = 6924481166  # Ваш ID

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

EQUIPMENT = {
    "Приманка": {
        "price": 500,
        "description": "+5% к поиску опасных животных",
        "bonus": {"Опасные": 5}
    },
    "Маскировка": {
        "price": 2000,
        "description": "+5% к поиску опасных и +5% к поиску тяжелых животных",
        "bonus": {"Опасные": 5, "Тяжелые": 5}
    },
    "Локатор": {
        "price": 10000,
        "description": "+10% к поиску опасных, +5% к поиску тяжелых и +3% к поиску титанов",
        "bonus": {"Опасные": 10, "Тяжелые": 5, "Титаны": 3}
    },
    "Продвинутый искатель": {
        "price": 15000,
        "description": "100% шанс найти хотя бы одно животное",
        "bonus": {"Мелкая дичь": 100, "Средние": 100, "Опасные": 100, "Тяжелые": 100, "Титаны": 100}
    }
}

STICKERS = {"Заяц": "", "Белка": "", "Бобр": "", "Кабан": "", "Лев": "", "Тираннозавр": ""}

# ================== БАЗА ДАННЫХ ==================
db = sqlite3.connect("hunt.db", check_same_thread=False)
sql = db.cursor()

# Создание таблиц с полной структурой
sql.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    coins INTEGER DEFAULT 0,
    exp INTEGER DEFAULT 0,
    weapon TEXT DEFAULT 'Револьвер',
    location TEXT DEFAULT 'Тайга',
    last_hunt INTEGER DEFAULT 0,
    daily_kills INTEGER DEFAULT 0,
    total_kills INTEGER DEFAULT 0,
    username TEXT
)
""")

sql.execute("""
CREATE TABLE IF NOT EXISTS trophies (
    user_id INTEGER,
    animal TEXT,
    count INTEGER DEFAULT 0,
    UNIQUE(user_id, animal),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
""")

sql.execute("""
CREATE TABLE IF NOT EXISTS user_weapons (
    user_id INTEGER,
    weapon TEXT,
    UNIQUE(user_id, weapon),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
""")

sql.execute("""
CREATE TABLE IF NOT EXISTS user_equipment (
    user_id INTEGER,
    equipment TEXT,
    UNIQUE(user_id, equipment),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
""")

sql.execute("""
CREATE TABLE IF NOT EXISTS stats_daily (
    user_id INTEGER,
    date TEXT,
    kills INTEGER DEFAULT 0,
    UNIQUE(user_id, date),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
""")

# Функция для обновления структуры БД при необходимости
def update_database():
    """Обновляет структуру базы данных при необходимости"""
    columns_to_add = [
        ("daily_kills", "INTEGER DEFAULT 0"),
        ("total_kills", "INTEGER DEFAULT 0"),
        ("username", "TEXT")
    ]
    
    for column_name, column_type in columns_to_add:
        try:
            sql.execute(f"SELECT {column_name} FROM users LIMIT 1")
        except sqlite3.OperationalError:
            sql.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
            print(f"✅ Добавлена колонка {column_name}")
    
    db.commit()

update_database()
db.commit()

# ================== ФУНКЦИИ ==================
def get_level(exp: int) -> int:
    return exp // EXP_PER_LEVEL

def ensure_user(user_id: int, username: str = None):
    user = sql.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not user:
        sql.execute(
            "INSERT INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        sql.execute(
            "INSERT OR IGNORE INTO user_weapons VALUES (?, ?)",
            (user_id, "Револьver")
        )
        db.commit()
        user = sql.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    elif username and username != user[8]:
        sql.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
        db.commit()
    return user

def get_user_equipment(user_id: int):
    equipment = sql.execute(
        "SELECT equipment FROM user_equipment WHERE user_id = ?", 
        (user_id,)
    ).fetchall()
    return [eq[0] for eq in equipment]

def get_equipment_bonuses(user_id: int):
    equipment = get_user_equipment(user_id)
    bonuses = {"Мелкая дичь": 0, "Средние": 0, "Опасные": 0, "Тяжелые": 0, "Титаны": 0}
    
    for eq_name in equipment:
        if eq_name in EQUIPMENT:
            for group, bonus in EQUIPMENT[eq_name]["bonus"].items():
                if group in bonuses:
                    bonuses[group] += bonus
    return bonuses

def choose_animal(location: str, user_id: int):
    available_groups = [g for g in SEARCH_CHANCES if LOCATIONS[location]["animals"].get(g) and LOCATIONS[location]["animals"][g]]
    if not available_groups:
        return None, None
    
    bonuses = get_equipment_bonuses(user_id)
    equipment = get_user_equipment(user_id)
    
    if "Продвинутый искатель" in equipment:
        weights = [SEARCH_CHANCES[g] + bonuses.get(g, 0) + 20 for g in available_groups]
        group = random.choices(available_groups, weights=weights)[0]
        animal = random.choice(LOCATIONS[location]["animals"][group])
        return group, animal
    
    weights = [SEARCH_CHANCES[g] + bonuses.get(g, 0) for g in available_groups]
    group = random.choices(available_groups, weights=weights)[0]
    
    search_chance = SEARCH_CHANCES[group] + bonuses.get(group, 0)
    if random.randint(1, 100) > search_chance:
        return None, None
    
    animal = random.choice(LOCATIONS[location]["animals"][group])
    return group, animal

def check_hit(weapon: str, group: str):
    groups = ["Мелкая дичь", "Средние", "Опасные", "Тяжелые", "Титаны"]
    if group not in groups:
        return False
    idx = groups.index(group)
    chance = WEAPONS[weapon][idx]
    return random.uniform(0, 100) <= chance

def can_use_location(user_level: int, location_name: str) -> bool:
    return user_level >= LOCATIONS[location_name]["level"]

def reset_daily_stats():
    today = datetime.now().strftime("%Y-%m-%d")
    sql.execute("UPDATE users SET daily_kills = 0")
    sql.execute("DELETE FROM stats_daily WHERE date != ?", (today,))
    db.commit()

# ================== БОТ ==================
bot = Bot(TOKEN)
dp = Dispatcher()

# ================== АДМИН КОМАНДЫ ==================
ADMIN_USERNAME = "DeepSleep01"  # Твой username в Telegram

@dp.message(lambda msg: msg.text and msg.text.startswith("дипскип") and msg.from_user.username == ADMIN_USERNAME)
async def admin_skip(msg: Message):
    try:
        parts = msg.text.split()
        if len(parts) >= 2 and "@" in parts[1]:
            username = parts[1].replace("@", "").strip()
            user = sql.execute("SELECT user_id FROM users WHERE username = ?", (username,)).fetchone()
            if user:
                sql.execute("UPDATE users SET last_hunt = 0 WHERE user_id = ?", (user[0],))
                db.commit()
                await msg.answer(f"✅ Таймер сброшен для @{username}")
            else:
                await msg.answer(f"❌ Пользователь @{username} не найден в базе")
        else:
            await msg.answer("❌ Используйте: дипскип @username\nПример: дипскип @player123")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {str(e)}")

@dp.message(lambda msg: msg.text and msg.text.startswith("дипмонеты") and msg.from_user.username == ADMIN_USERNAME)
async def admin_coins(msg: Message):
    try:
        parts = msg.text.split()
        if len(parts) >= 3 and "@" in parts[2]:
            amount = int(parts[1])
            username = parts[2].replace("@", "").strip()
            user = sql.execute("SELECT user_id FROM users WHERE username = ?", (username,)).fetchone()
            if user:
                sql.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, user[0]))
                db.commit()
                await msg.answer(f"✅ Выдано {amount} монет пользователю @{username}")
            else:
                await msg.answer(f"❌ Пользователь @{username} не найден в базе")
        else:
            await msg.answer("❌ Используйте: дипмонеты 100 @username\nПример: дипмонеты 500 @player123")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {str(e)}")

@dp.message(lambda msg: msg.text and msg.text.startswith("дипопыт") and msg.from_user.username == ADMIN_USERNAME)
async def admin_exp(msg: Message):
    try:
        parts = msg.text.split()
        if len(parts) >= 3 and "@" in parts[2]:
            amount = int(parts[1])
            username = parts[2].replace("@", "").strip()
            user = sql.execute("SELECT user_id FROM users WHERE username = ?", (username,)).fetchone()
            if user:
                sql.execute("UPDATE users SET exp = exp + ? WHERE user_id = ?", (amount, user[0]))
                db.commit()
                await msg.answer(f"✅ Выдано {amount} опыта пользователю @{username}")
            else:
                await msg.answer(f"❌ Пользователь @{username} не найден в базе")
        else:
            await msg.answer("❌ Используйте: дипопыт 500 @username\nПример: дипопыт 1000 @player123")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {str(e)}")

@dp.message(lambda msg: msg.text and msg.text.startswith("дипуровни") and msg.from_user.username == ADMIN_USERNAME)
async def admin_level(msg: Message):
    try:
        parts = msg.text.split()
        if len(parts) >= 3 and "@" in parts[2]:
            levels = int(parts[1])
            username = parts[2].replace("@", "").strip()
            user = sql.execute("SELECT user_id FROM users WHERE username = ?", (username,)).fetchone()
            if user:
                exp_needed = levels * EXP_PER_LEVEL
                sql.execute("UPDATE users SET exp = exp + ? WHERE user_id = ?", (exp_needed, user[0]))
                db.commit()
                await msg.answer(f"✅ Выдано {levels} уровней ({exp_needed} опыта) пользователю @{username}")
            else:
                await msg.answer(f"❌ Пользователь @{username} не найден в базе")
        else:
            await msg.answer("❌ Используйте: дипуровни 5 @username\nПример: дипуровни 3 @player123")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {str(e)}")
# ================== /start ==================
@dp.message(Command("start"))
async def start(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    await msg.answer("🏹 Добро пожаловать на охоту!\n\nКоманды:\n• Хант — начать охоту\n• Инв — посмотреть снаряжение\n• Магазин — купить оружие\n• Локации — выбрать локацию\n• Топы — таблица лидеров\n• Справка — информация о боте")

# ================== СПРАВКА ==================
@dp.message(lambda msg: msg.text and msg.text.lower() == "справка")
async def help_command(msg: Message):
    await msg.answer("Если есть вопросы/проблемы с ботом/идеи для обновлений то напиши @DeepSleep01")

# ================== ХАНТ ==================
@dp.message(lambda msg: msg.text and msg.text.lower() == "хант")
async def hunt(msg: Message):
    user = ensure_user(msg.from_user.id, msg.from_user.username)
    now = int(time.time())
    if now - user[5] < HUNT_COOLDOWN:
        wait = HUNT_COOLDOWN - (now - user[5])
        await msg.answer(f"⏳ Подожди {wait // 60} мин {wait % 60} сек.")
        return
    
    sql.execute("UPDATE users SET last_hunt = ? WHERE user_id = ?", (now, msg.from_user.id))
    db.commit()
    
    group, animal = choose_animal(user[4], msg.from_user.id)
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
async def shoot(call: CallbackQuery):
    data_parts = call.data.split(":")
    if len(data_parts) < 4:
        await call.answer("❌ Ошибка данных", show_alert=True)
        return
    
    owner_id, group, animal = data_parts[1:]
    if int(owner_id) != call.from_user.id:
        await call.answer("❌ Это не твоя охота!", show_alert=True)
        return
    
    user = ensure_user(call.from_user.id)
    if not check_hit(user[3], group):
        await call.message.edit_text("❌ К сожалению, вы промахнулись.")
        return
    
    if group not in REWARDS:
        await call.message.edit_text("❌ Ошибка награды")
        return
    
    coins, exp = REWARDS[group]
    sql.execute("UPDATE users SET coins = coins + ?, exp = exp + ?, daily_kills = daily_kills + 1, total_kills = total_kills + 1 WHERE user_id = ?", 
                (coins, exp, call.from_user.id))
    
    today = datetime.now().strftime("%Y-%m-%d")
    stats = sql.execute("SELECT kills FROM stats_daily WHERE user_id = ? AND date = ?", (call.from_user.id, today)).fetchone()
    if stats:
        sql.execute("UPDATE stats_daily SET kills = kills + 1 WHERE user_id = ? AND date = ?", (call.from_user.id, today))
    else:
        sql.execute("INSERT INTO stats_daily VALUES (?, ?, ?)", (call.from_user.id, today, 1))
    
    trophy = sql.execute("SELECT count FROM trophies WHERE user_id = ? AND animal = ?", (call.from_user.id, animal)).fetchone()
    if trophy:
        sql.execute("UPDATE trophies SET count = count + 1 WHERE user_id = ? AND animal = ?", (call.from_user.id, animal))
    else:
        sql.execute("INSERT INTO trophies VALUES (?, ?, ?)", (call.from_user.id, animal, 1))
    
    db.commit()
    
    if animal in STICKERS and STICKERS[animal]:
        await call.message.answer_sticker(STICKERS[animal])
    
    await call.message.edit_text(f"🎯 Прямое попадание!\n\nТрофей: {animal}\n💰 Монеты: +{coins}\n⭐ Опыт: +{exp}")

# ================== ИНВЕНТАРЬ ==================
@dp.message(lambda msg: msg.text and msg.text.lower() in ["инв", "инвен", "инвентарь"])
async def inventory(msg: Message):
    user = ensure_user(msg.from_user.id, msg.from_user.username)
    
    # Получаем трофеи пользователя
    trophies = sql.execute("SELECT animal, count FROM trophies WHERE user_id = ?", (msg.from_user.id,)).fetchall()
    
    # Получаем снаряжение пользователя
    equipment = get_user_equipment(msg.from_user.id)
    equipment_bonuses = get_equipment_bonuses(msg.from_user.id)
    
    # Группируем трофеи по категориям
    groups = ["Мелкая дичь", "Средние", "Опасные", "Тяжелые", "Титаны"]
    grouped_trophies = {g: [] for g in groups}
    
    for animal, count in trophies:
        for location_name, location_data in LOCATIONS.items():
            for group, animals_list in location_data["animals"].items():
                if animal in animals_list:
                    grouped_trophies[group].append((animal, count))
                    break
    
    # Формируем текст инвентаря
    text = f"🎒 Инвентарь\n\n"
    text += f"🔫 Оружие: {user[3]}\n"
    text += f"📍 Локация: {user[4]}\n"
    text += f"💰 Монеты: {user[1]}\n"
    text += f"⭐ Уровень: {get_level(user[2])}\n"
    text += f"📊 Опыт: {user[2]}/{EXP_PER_LEVEL}\n"
    text += f"🎯 Убийств сегодня: {user[6]}\n"
    text += f"🎯 Всего убийств: {user[7]}\n\n"
    
    # Снаряжение
    if equipment:
        text += f"🎩 Снаряжение: {', '.join(equipment)}\n\n"
        
        # Бонусы от снаряжения
        has_bonuses = False
        bonus_text = "📈 Бонусы от снаряжения:\n"
        for group in groups:
            bonus = equipment_bonuses.get(group, 0)
            if bonus > 0:
                bonus_text += f"• {group}: +{bonus}%\n"
                has_bonuses = True
        
        if has_bonuses:
            text += bonus_text + "\n"
    else:
        text += "🎩 Снаряжение: нет\n\n"
    
    # Трофеи
    text += "🏆 Трофеи:\n"
    
    has_trophies = False
    for group in groups:
        if grouped_trophies[group]:
            has_trophies = True
            text += f"\n{group}:\n"
            for animal_name, count in grouped_trophies[group]:
                text += f"• {animal_name} — {count} шт.\n"
    
    if not has_trophies:
        text += "\n— пока нет трофеев —"
    
    await msg.answer(text)

# ================== МАГАЗИН ==================
@dp.message(lambda msg: msg.text and msg.text.lower() == "магазин")
async def shop(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔫 Оружие", callback_data=f"shop_weapons:{msg.from_user.id}")],
        [InlineKeyboardButton(text="🎩 Снаряжение", callback_data=f"shop_equipment:{msg.from_user.id}")]
    ])
    await msg.answer("Выберите категорию:", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("shop_weapons"))
async def shop_weapons(call: CallbackQuery):
    user_id = call.data.split(":")[1]
    
    if int(user_id) != call.from_user.id:
        await call.answer("❌ Это не ваш магазин!", show_alert=True)
        return
    
    user = ensure_user(call.from_user.id)
    
    buttons = []
    for weapon, price in WEAPON_PRICES.items():
        owned = sql.execute("SELECT 1 FROM user_weapons WHERE user_id = ? AND weapon = ?", 
                          (call.from_user.id, weapon)).fetchone()
        status = "✅ " if owned else ""
        buttons.append([InlineKeyboardButton(
            text=f"{status}{weapon} — {price}💰",
            callback_data=f"buy_weapon:{call.from_user.id}:{weapon}"
        )])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text(f"💰 Ваш баланс: {user[1]} монет\n\n🔫 Выберите оружие:", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("shop_equipment"))
async def shop_equipment(call: CallbackQuery):
    user_id = call.data.split(":")[1]
    
    if int(user_id) != call.from_user.id:
        await call.answer("❌ Это не ваш магазин!", show_alert=True)
        return
    
    user = ensure_user(call.from_user.id)
    owned_equipment = get_user_equipment(call.from_user.id)
    
    buttons = []
    for eq_name, eq_data in EQUIPMENT.items():
        owned = "✅ " if eq_name in owned_equipment else ""
        buttons.append([InlineKeyboardButton(
            text=f"{owned}{eq_name} — {eq_data['price']}💰",
            callback_data=f"view_eq:{call.from_user.id}:{eq_name}"
        )])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"shop_back:{call.from_user.id}")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text(f"💰 Ваш баланс: {user[1]} монет\n\n🎩 Выберите снаряжение:", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("view_eq"))
async def view_equipment(call: CallbackQuery):
    data_parts = call.data.split(":")
    if len(data_parts) < 3:
        await call.answer("❌ Ошибка данных", show_alert=True)
        return
    
    user_id, eq_name = data_parts[1:]
    
    if int(user_id) != call.from_user.id:
        await call.answer("❌ Это не ваш магазин!", show_alert=True)
        return
    
    if eq_name not in EQUIPMENT:
        await call.message.edit_text("❌ Этот предмет не найден.")
        return
    
    eq_data = EQUIPMENT[eq_name]
    user = ensure_user(call.from_user.id)
    owned_equipment = get_user_equipment(call.from_user.id)
    
    if eq_name in owned_equipment:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Уже куплено", callback_data="no_action")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"shop_equipment:{call.from_user.id}")]
        ])
        status_text = "✅ Этот предмет уже куплен"
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"💰 Купить за {eq_data['price']} монет", callback_data=f"buy_eq:{call.from_user.id}:{eq_name}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"shop_equipment:{call.from_user.id}")]
        ])
        status_text = f"💳 Ваш баланс: {user[1]} монет\n{'❌ Недостаточно средств' if user[1] < eq_data['price'] else '✅ Достаточно средств'}"
    
    await call.message.edit_text(
        f"🎩 {eq_name}\n\n"
        f"📝 Описание: {eq_data['description']}\n\n"
        f"💰 Цена: {eq_data['price']} монет\n"
        f"{status_text}",
        reply_markup=kb
    )

@dp.callback_query(lambda c: c.data.startswith("buy_eq"))
async def buy_equipment(call: CallbackQuery):
    data_parts = call.data.split(":")
    if len(data_parts) < 3:
        await call.answer("❌ Ошибка данных", show_alert=True)
        return
    
    user_id, eq_name = data_parts[1:]
    
    if int(user_id) != call.from_user.id:
        await call.answer("❌ Это не ваша покупка!", show_alert=True)
        return
    
    if eq_name not in EQUIPMENT:
        await call.message.edit_text("❌ Этот предмет не найден.")
        return
    
    eq_data = EQUIPMENT[eq_name]
    user = ensure_user(call.from_user.id)
    
    owned = sql.execute(
        "SELECT 1 FROM user_equipment WHERE user_id = ? AND equipment = ?",
        (call.from_user.id, eq_name)
    ).fetchone()
    
    if owned:
        await call.message.edit_text("✅ Вы уже купили этот предмет!")
        return
    
    if user[1] < eq_data['price']:
        await call.message.edit_text("❌ Недостаточно монет.")
        return
    
    sql.execute(
        "UPDATE users SET coins = coins - ? WHERE user_id = ?",
        (eq_data['price'], call.from_user.id)
    )
    sql.execute(
        "INSERT INTO user_equipment VALUES (?, ?)",
        (call.from_user.id, eq_name)
    )
    db.commit()
    
    await call.message.edit_text(f"✅ Вы купили {eq_name}!\n\n{eq_data['description']}\n\nБонусы применены автоматически.")

@dp.callback_query(lambda c: c.data == "no_action")
async def no_action(call: CallbackQuery):
    await call.answer("✅ Этот предмет уже куплен", show_alert=True)

@dp.callback_query(lambda c: c.data.startswith("shop_back"))
async def shop_back(call: CallbackQuery):
    user_id = call.data.split(":")[1]
    
    if int(user_id) != call.from_user.id:
        await call.answer("❌ Это не ваш магазин!", show_alert=True)
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔫 Оружие", callback_data=f"shop_weapons:{call.from_user.id}")],
        [InlineKeyboardButton(text="🎩 Снаряжение", callback_data=f"shop_equipment:{call.from_user.id}")]
    ])
    await call.message.edit_text("Выберите категорию:", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("buy_weapon"))
async def buy_weapon(call: CallbackQuery):
    data_parts = call.data.split(":")
    if len(data_parts) < 3:
        await call.answer("❌ Ошибка данных", show_alert=True)
        return
    
    user_id, weapon = data_parts[1:]
    
    if int(user_id) != call.from_user.id:
        await call.answer("❌ Это не ваша покупка!", show_alert=True)
        return
    
    user = ensure_user(call.from_user.id)
    
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

    if weapon not in WEAPON_PRICES:
        await call.message.edit_text("❌ Это оружие не найдено.")
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
        "INSERT INTO user_weapons VALUES (?, ?)",
        (call.from_user.id, weapon)
    )
    sql.execute(
        "UPDATE users SET weapon = ? WHERE user_id = ?",
        (weapon, call.from_user.id)
    )
    db.commit()

    await call.message.edit_text(f"✅ Вы купили {weapon} и выбрали его!")

# ================== ТОП ==================
@dp.message(lambda msg: msg.text and msg.text.lower() == "топы")
async def top(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Топ по убийствам (все время)", callback_data=f"top_total:{msg.from_user.id}")],
        [InlineKeyboardButton(text="📊 Топ по убийствам (за день)", callback_data=f"top_daily:{msg.from_user.id}")],
        [InlineKeyboardButton(text="⭐ Топ по опыту", callback_data=f"top_exp:{msg.from_user.id}")],
        [InlineKeyboardButton(text="💰 Топ по монетам", callback_data=f"top_coins:{msg.from_user.id}")],
        [InlineKeyboardButton(text="🎯 Топ по титанам", callback_data=f"top_titans:{msg.from_user.id}")]
    ])
    await msg.answer("Выберите категорию топа:", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("top_total"))
async def top_total(call: CallbackQuery):
    user_id = call.data.split(":")[1]
    
    if int(user_id) != call.from_user.id:
        await call.answer("❌ Это не ваш топ!", show_alert=True)
        return
    
    top_users = sql.execute(
        "SELECT username, total_kills FROM users WHERE username IS NOT NULL AND total_kills > 0 ORDER BY total_kills DESC LIMIT 10"
    ).fetchall()
    
    if not top_users:
        await call.message.edit_text("📭 Пока нет данных в этой категории.")
        return
    
    text = "🏆 Топ по убийствам (все время):\n\n"
    for i, (username, kills) in enumerate(top_users, 1):
        text += f"{i}. @{username} — {kills} убийств\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"top_back:{call.from_user.id}")]
    ])
    
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("top_daily"))
async def top_daily(call: CallbackQuery):
    user_id = call.data.split(":")[1]
    
    if int(user_id) != call.from_user.id:
        await call.answer("❌ Это не ваш топ!", show_alert=True)
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    top_users = sql.execute(
        "SELECT u.username, s.kills FROM users u "
        "JOIN stats_daily s ON u.user_id = s.user_id "
        "WHERE s.date = ? AND u.username IS NOT NULL AND s.kills > 0 "
        "ORDER BY s.kills DESC LIMIT 10",
        (today,)
    ).fetchall()
    
    if not top_users:
        await call.message.edit_text("📭 Пока нет данных в этой категории.")
        return
    
    text = f"📊 Топ по убийствам (за день, {today}):\n\n"
    for i, (username, kills) in enumerate(top_users, 1):
        text += f"{i}. @{username} — {kills} убийств\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"top_back:{call.from_user.id}")]
    ])
    
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("top_exp"))
async def top_exp(call: CallbackQuery):
    user_id = call.data.split(":")[1]
    
    if int(user_id) != call.from_user.id:
        await call.answer("❌ Это не ваш топ!", show_alert=True)
        return
    
    top_users = sql.execute(
        "SELECT username, exp, exp/500 as level FROM users "
        "WHERE username IS NOT NULL AND exp > 0 ORDER BY exp DESC LIMIT 10"
    ).fetchall()
    
    if not top_users:
        await call.message.edit_text("📭 Пока нет данных в этой категории.")
        return
    
    text = "⭐ Топ по опыту (и уровню):\n\n"
    for i, (username, exp, level) in enumerate(top_users, 1):
        text += f"{i}. @{username} — Опыт: {exp} (Уровень: {int(level)})\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"top_back:{call.from_user.id}")]
    ])
    
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("top_coins"))
async def top_coins(call: CallbackQuery):
    user_id = call.data.split(":")[1]
    
    if int(user_id) != call.from_user.id:
        await call.answer("❌ Это не ваш топ!", show_alert=True)
        return
    
    top_users = sql.execute(
        "SELECT username, coins FROM users "
        "WHERE username IS NOT NULL AND coins > 0 ORDER BY coins DESC LIMIT 10"
    ).fetchall()
    
    if not top_users:
        await call.message.edit_text("📭 Пока нет данных в этой категории.")
        return
    
    text = "💰 Топ по монетам:\n\n"
    for i, (username, coins) in enumerate(top_users, 1):
        text += f"{i}. @{username} — {coins} монет\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"top_back:{call.from_user.id}")]
    ])
    
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("top_titans"))
async def top_titans(call: CallbackQuery):
    user_id = call.data.split(":")[1]
    
    if int(user_id) != call.from_user.id:
        await call.answer("❌ Это не ваш топ!", show_alert=True)
        return
    
    # Собираем всех титанов из всех локаций
    titan_animals = []
    for location_name, location_data in LOCATIONS.items():
        if "Титаны" in location_data["animals"]:
            titan_animals.extend(location_data["animals"]["Титаны"])
    
    if not titan_animals:
        await call.message.edit_text("🎯 В игре пока нет титанов.")
        return
    
    # Считаем количество убитых титанов для каждого пользователя
    titan_counts = {}
    
    for username, user_id in sql.execute("SELECT username, user_id FROM users WHERE username IS NOT NULL").fetchall():
        total_titans = 0
        for animal in titan_animals:
            result = sql.execute(
                "SELECT count FROM trophies WHERE user_id = ? AND animal = ?",
                (user_id, animal)
            ).fetchone()
            if result:
                total_titans += result[0]
        
        if total_titans > 0:
            titan_counts[username] = total_titans
    
    if not titan_counts:
        await call.message.edit_text("🎯 Пока никто не убил ни одного титана.")
        return
    
    # Сортируем по количеству титанов
    sorted_titans = sorted(titan_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    text = "🎯 Топ по убийству титанов:\n\n"
    for i, (username, count) in enumerate(sorted_titans, 1):
        text += f"{i}. @{username} — {count} титанов\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"top_back:{call.from_user.id}")]
    ])
    
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("top_back"))
async def top_back(call: CallbackQuery):
    user_id = call.data.split(":")[1]
    
    if int(user_id) != call.from_user.id:
        await call.answer("❌ Это не ваш топ!", show_alert=True)
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Топ по убийствам (все время)", callback_data=f"top_total:{call.from_user.id}")],
        [InlineKeyboardButton(text="📊 Топ по убийствам (за день)", callback_data=f"top_daily:{call.from_user.id}")],
        [InlineKeyboardButton(text="⭐ Топ по опыту", callback_data=f"top_exp:{call.from_user.id}")],
        [InlineKeyboardButton(text="💰 Топ по монетам", callback_data=f"top_coins:{call.from_user.id}")],
        [InlineKeyboardButton(text="🎯 Топ по титанам", callback_data=f"top_titans:{call.from_user.id}")]
    ])
    await call.message.edit_text("Выберите категорию топа:", reply_markup=kb)

# ================== ЛОКАЦИИ ==================
@dp.message(lambda msg: msg.text and msg.text.lower() == "локации")
async def choose_location(msg: Message):
    user = ensure_user(msg.from_user.id, msg.from_user.username)
    level = get_level(user[2])
    
    buttons = []
    for name, data in LOCATIONS.items():
        available = level >= data["level"]
        status = "📍 " if user[4] == name else ""
        lock = "🔒 " if not available else ""
        level_req = f" (ур. {data['level']}+)" if not available else ""
        
        if available:
            buttons.append([InlineKeyboardButton(
                text=f"{status}{lock}{name}{level_req}",
                callback_data=f"loc_set:{msg.from_user.id}:{name}"
            )])
        else:
            buttons.append([InlineKeyboardButton(
                text=f"{lock}{name}{level_req}",
                callback_data="loc_locked"
            )])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await msg.answer(f"📍 Выберите локацию (Ваш уровень: {level}):", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("loc_set"))
async def set_location(call: CallbackQuery):
    data_parts = call.data.split(":")
    if len(data_parts) < 3:
        await call.answer("❌ Ошибка данных", show_alert=True)
        return
    
    owner_id, location = data_parts[1:]
    
    if int(owner_id) != call.from_user.id:
        await call.answer("❌ Это не твоя локация!", show_alert=True)
        return
    
    user = ensure_user(call.from_user.id)
    level = get_level(user[2])
    
    if location not in LOCATIONS:
        await call.message.edit_text("❌ Эта локация не существует.")
        return
    
    if not can_use_location(level, location):
        await call.message.edit_text(f"❌ Эта локация доступна с уровня {LOCATIONS[location]['level']}.")
        return
    
    sql.execute("UPDATE users SET location = ? WHERE user_id = ?", (location, call.from_user.id))
    db.commit()
    
    # Создаем подробный список животных для этой локации
    animals_text = "\n\n🐾 Животные в этой локации:\n"
    
    for group_name, animals_list in LOCATIONS[location]["animals"].items():
        if animals_list:  # Проверяем, что список не пустой
            animals_text += f"\n{group_name}:\n"
            # Добавляем всех животных из списка
            animals_text += "• " + "\n• ".join(animals_list) + "\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад к локациям", callback_data=f"loc_back:{call.from_user.id}")]
    ])
    
    await call.message.edit_text(
        f"✅ Локация изменена на {location}!\n\n"
        f"📊 Уровень доступа: {LOCATIONS[location]['level']}+"
        f"{animals_text}",
        reply_markup=kb
    )

@dp.callback_query(lambda c: c.data == "loc_locked")
async def loc_locked(call: CallbackQuery):
    await call.answer("❌ Эта локация недоступна на вашем уровне!", show_alert=True)

@dp.callback_query(lambda c: c.data.startswith("loc_back"))
async def location_back(call: CallbackQuery):
    user_id = call.data.split(":")[1]
    
    if int(user_id) != call.from_user.id:
        await call.answer("❌ Это не ваше меню!", show_alert=True)
        return
    
    user = ensure_user(call.from_user.id)
    level = get_level(user[2])
    
    buttons = []
    for name, data in LOCATIONS.items():
        available = level >= data["level"]
        status = "📍 " if user[4] == name else ""
        lock = "🔒 " if not available else ""
        level_req = f" (ур. {data['level']}+)" if not available else ""
        
        if available:
            buttons.append([InlineKeyboardButton(
                text=f"{status}{lock}{name}{level_req}",
                callback_data=f"loc_set:{call.from_user.id}:{name}"
            )])
        else:
            buttons.append([InlineKeyboardButton(
                text=f"{lock}{name}{level_req}",
                callback_data="loc_locked"
            )])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text(f"📍 Выберите локацию (Ваш уровень: {level}):", reply_markup=kb)

# ================== ЗАПУСК ==================
async def main():
    """Основная функция запуска бота"""
    print("=" * 50)
    print("🔧 Обновление структуры базы данных...")
    update_database()
    
    print("🔄 Сброс дневной статистики...")
    reset_daily_stats()
    
    print("🤖 Бот запущен! Ожидание сообщений...")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print("=" * 50)
    print("📊 Доступные команды:")
    print("• /start - Начало работы")
    print("• Хант - Начать охоту")
    print("• Инв - Инвентарь")
    print("• Магазин - Магазин оружия и снаряжения")
    print("• Локации - Выбор локации")
    print("• Топы - Таблица лидеров")
    print("• Справка - Помощь")
    print("=" * 50)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
