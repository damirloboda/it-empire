import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv("BOT_TOKEN", "8650810573:AAHuuyKsSO5rzlQIu9ZIRfzAYuLZkwSuiEQ")
WEBAPP_URL = os.getenv("WEBAPP_URL") or os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
if WEBAPP_URL and not WEBAPP_URL.startswith("http"):
    WEBAPP_URL = f"https://{WEBAPP_URL}"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

WELCOME_TEXT = (
    "🚀 <b>IT Empire Tycoon</b>\n\n"
    "Построй свою IT-империю с нуля!\n\n"
    "🖥 <b>Кликай</b> по ноутбуку — зарабатывай деньги\n"
    "🛒 <b>Магазин</b> — покупай оборудование и нанимай команду\n"
    "⚙️ <b>Крафт</b> — создавай мощные предметы из ресурсов\n"
    "📊 <b>Статистика</b> — следи за прогрессом и достижениями\n"
    "👥 <b>Друзья</b> — приглашай и получай бонусы\n"
    "⚡ <b>Престиж</b> — 10 уровней перерождения!\n\n"
    "Нажми кнопку ниже, чтобы начать! 👇"
)

HELP_TEXT = (
    "📖 <b>IT Empire Tycoon — Полное руководство</b>\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "💻 <b>КЛИК</b>\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "• Тапай по ноутбуку чтобы зарабатывать деньги\n"
    "• Чем быстрее тапаешь — тем выше КОМБО 🔥\n"
    "• КОМБО ×2 (10), ×3 (25), ×4 (50), ×5 (100 кликов)\n"
    "• Каждые 10 кликов = 1 🔧 компонент\n"
    "• Каждые 100 кликов = 1 💡 чип\n"
    "• Каждые 1000 кликов = 1 ⚛️ ядро\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "🛒 <b>МАГАЗИН</b>\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "🖥 <b>Железо</b> (сила клика):\n"
    "  • Old Laptop — $200\n"
    "  • MacBook Pro — $5,000\n"
    "  • Dual Monitor Rig — $80,000\n"
    "  • Server Farm — $2,000,000\n\n"
    "👥 <b>Команда</b> (пассив в сек):\n"
    "  • Junior Dev — $0.5/сек\n"
    "  • Senior Dev — $4/сек\n"
    "  • AI Agent — $15/сек\n"
    "  • CTO — $80/сек\n\n"
    "⭐ <b>Спецапгрейды</b>:\n"
    "  • Cloud Infra — пассив ×1.5 ($5M)\n"
    "  • AI Suite — клик ×2 ($25M)\n"
    "  • Data Centers — всё ×3 ($500M)\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "⚡ <b>ПРЕСТИЖ</b> (10 уровней)\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "  1️⃣ $1M → ×1.5   2️⃣ $50M → ×2.0\n"
    "  3️⃣ $200M → ×2.5  4️⃣ $500M → ×3.0\n"
    "  5️⃣ $1B → ×3.5    6️⃣ $3B → ×4.0\n"
    "  7️⃣ $10B → ×4.5   8️⃣ $50B → ×5.0\n"
    "  9️⃣ $200B → ×5.5  🔟 $1T → ×6.0 MAX!\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "👥 <b>ДРУЗЬЯ</b>\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "• Друг по ссылке получает +$1,000\n"
    "• Ты получаешь +$500 за каждого друга\n"
    "• Уведомление приходит прямо в этот чат!\n\n"
    "🏆 Удачи в построении IT-империи! 🚀"
)

HOW_TO_PLAY_TEXT = (
    "📖 <b>Как играть в IT Empire Tycoon</b>\n\n"
    "1️⃣ <b>КЛИК</b> — тапай по ноутбуку, зарабатывай $\n"
    "   Быстрее тапаешь = больше комбо-множитель 🔥\n\n"
    "2️⃣ <b>МАГАЗИН</b> — трать деньги на прокачку\n"
    "   Железо повышает силу клика, команда — пассив\n\n"
    "3️⃣ <b>КРАФТ</b> — собирай ресурсы из кликов\n"
    "   Крафти предметы для постоянных бонусов\n\n"
    "4️⃣ <b>ПРЕСТИЖ</b> — 10 уровней перерождения!\n"
    "   Каждый даёт постоянный множитель к доходу\n\n"
    "5️⃣ <b>ДРУЗЬЯ</b> — приглашай, получай бонусы\n\n"
    "Пиши /help для полного гайда! 🚀"
)


@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('ref_'):
        referrer_id = args[1].replace('ref_', '')
        new_user_name = message.from_user.first_name or message.from_user.username or "Новый игрок"
        if referrer_id != str(message.from_user.id):
            try:
                await bot.send_message(
                    chat_id=int(referrer_id),
                    text=f"🎉 Твой друг <b>{new_user_name}</b> зашёл в IT Empire по твоей ссылке!\n\n"
                         f"💰 Ты получаешь <b>+$500</b> бонус!\n"
                         f"👥 Открой игру — бонус уже у тебя в игре.",
                    parse_mode="HTML"
                )
            except Exception as e:
                logging.warning(f"Could not notify referrer {referrer_id}: {e}")

    buttons = []
    if WEBAPP_URL:
        buttons.append([
            InlineKeyboardButton(
                text="🚀 Открыть IT Empire",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="📖 Как играть", callback_data="how_to_play"),
        InlineKeyboardButton(text="❓ Помощь", callback_data="help_full")
    ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(WELCOME_TEXT, parse_mode="HTML", reply_markup=keyboard)


@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    buttons = []
    if WEBAPP_URL:
        buttons.append([
            InlineKeyboardButton(
                text="🚀 Открыть IT Empire",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_start")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(HELP_TEXT, parse_mode="HTML", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "help_full")
async def help_callback(callback: types.CallbackQuery):
    buttons = []
    if WEBAPP_URL:
        buttons.append([
            InlineKeyboardButton(
                text="🚀 Открыть игру",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(HELP_TEXT, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(lambda c: c.data == "how_to_play")
async def how_to_play_callback(callback: types.CallbackQuery):
    buttons = []
    if WEBAPP_URL:
        buttons.append([
            InlineKeyboardButton(
                text="🚀 Открыть игру",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(HOW_TO_PLAY_TEXT, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(lambda c: c.data == "back_to_start")
async def back_to_start(callback: types.CallbackQuery):
    buttons = []
    if WEBAPP_URL:
        buttons.append([
            InlineKeyboardButton(
                text="🚀 Открыть IT Empire",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="📖 Как играть", callback_data="how_to_play"),
        InlineKeyboardButton(text="❓ Помощь", callback_data="help_full")
    ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(WELCOME_TEXT, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.set_my_commands([
        types.BotCommand(command="start", description="🚀 Запустить IT Empire"),
        types.BotCommand(command="help", description="❓ Полный гайд по игре"),
    ])
    polling_task = asyncio.create_task(dp.start_polling(bot))
    logging.info(f"Бот запущен! WEBAPP_URL={WEBAPP_URL}")
    yield
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def ngrok_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["ngrok-skip-browser-warning"] = "true"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.get("/")
async def serve_game():
    game_file = Path(__file__).parent / "index.html"
    return FileResponse(str(game_file), media_type="text/html")


@app.get("/health")
async def health():
    return {"status": "ok", "webapp_url": WEBAPP_URL}


@app.post("/referral")
async def handle_referral(request: Request):
    try:
        data = await request.json()
        referrer_id = data.get("referrer_id")
        new_user_name = data.get("new_user_name", "Игрок")
        new_user_id = data.get("new_user_id")
        if referrer_id and referrer_id != new_user_id:
            try:
                await bot.send_message(
                    chat_id=int(referrer_id),
                    text=f"🎉 Твой друг <b>{new_user_name}</b> зашёл в IT Empire!\n\n"
                         f"💰 Ты получаешь <b>+$500</b> бонус в игре!\n"
                         f"👥 Открой игру чтобы увидеть бонус.",
                    parse_mode="HTML"
                )
            except Exception as e:
                logging.warning(f"Could not notify referrer {referrer_id}: {e}")
        return JSONResponse({"ok": True})
    except Exception as e:
        logging.error(f"Referral error: {e}")
        return JSONResponse({"ok": False})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
