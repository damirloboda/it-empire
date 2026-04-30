import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn

logging.basicConfig(level=logging.INFO)

# ── Токен и URL ──────────────────────────────────────────────
API_TOKEN = os.getenv("BOT_TOKEN", "8650810573:AAHuuyKsSO5rzlQIu9ZIRfzAYuLZkwSuiEQ")
# Railway автоматически даёт PUBLIC_URL, ngrok передаётся через WEBAPP_URL
WEBAPP_URL = os.getenv("WEBAPP_URL") or os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
if WEBAPP_URL and not WEBAPP_URL.startswith("http"):
    WEBAPP_URL = f"https://{WEBAPP_URL}"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ── Текст приветствия ─────────────────────────────────────────
WELCOME_TEXT = (
    "🚀 <b>IT Empire Tycoon</b>\n\n"
    "Построй свою IT-империю с нуля!\n\n"
    "🖥 <b>Кликай</b> по ноутбуку — зарабатывай деньги\n"
    "🛒 <b>Магазин</b> — покупай оборудование и нанимай команду\n"
    "⚙️ <b>Крафт</b> — создавай мощные предметы из ресурсов\n"
    "📊 <b>Статистика</b> — следи за прогрессом и достижениями\n"
    "👥 <b>Друзья</b> — приглашай и получай бонусы\n"
    "⚡ <b>Престиж</b> — обнули прогресс при $1М и получи множитель!\n\n"
    "Нажми кнопку ниже, чтобы начать! 👇"
)

HOW_TO_PLAY_TEXT = (
    "📖 <b>Как играть в IT Empire Tycoon</b>\n\n"
    "1️⃣ <b>КЛИК</b> — тапай по ноутбуку, чтобы зарабатывать $\n"
    "   • Чем быстрее тапаешь — тем больше комбо-множитель 🔥\n\n"
    "2️⃣ <b>МАГАЗИН</b> — трать деньги на прокачку\n"
    "   • Железо: Old Laptop → Gaming PC → Workstation → Server Farm\n"
    "   • Команда: Junior Dev, Senior Dev, AI Agent, CTO\n"
    "   • Спецапгрейды: увеличивают доход и клики\n\n"
    "3️⃣ <b>КРАФТ</b> — собирай ресурсы и крафти предметы\n"
    "   • 🔧 Компоненты — за клики (каждые 10)\n"
    "   • 💡 Чипы — за клики (каждые 100)\n"
    "   • ⚛️ Ядра и 📐 Чертежи — пассивный доход\n\n"
    "4️⃣ <b>ПРЕСТИЖ</b> — при $1,000,000 нажми ⚡ PRESTIGE\n"
    "   • Прогресс сбрасывается, но получаешь ×1.5 к доходу навсегда\n"
    "   • Можно престижить несколько раз — множители складываются!\n\n"
    "5️⃣ <b>ДРУЗЬЯ</b> — пригласи друга, оба получите $1,000 бонус\n\n"
    "🏆 <b>10 достижений</b> ждут тебя в разделе Статистика!\n\n"
    "Удачи в построении империи! 🚀"
)


@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    url = WEBAPP_URL or "https://t.me/IT_Empire_ycoon_BOT"

    # Кнопки
    buttons = []
    if WEBAPP_URL:
        buttons.append([
            InlineKeyboardButton(
                text="🚀 Открыть IT Empire",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ])
    buttons.append([
        InlineKeyboardButton(
            text="📖 Как играть",
            callback_data="how_to_play"
        )
    ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(WELCOME_TEXT, parse_mode="HTML", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "how_to_play")
async def how_to_play_callback(callback: types.CallbackQuery):
    url = WEBAPP_URL or ""
    buttons = []
    if url:
        buttons.append([
            InlineKeyboardButton(
                text="🚀 Открыть игру",
                web_app=WebAppInfo(url=url)
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")
    ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(HOW_TO_PLAY_TEXT, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(lambda c: c.data == "back_to_start")
async def back_to_start(callback: types.CallbackQuery):
    url = WEBAPP_URL or ""
    buttons = []
    if url:
        buttons.append([
            InlineKeyboardButton(
                text="🚀 Открыть IT Empire",
                web_app=WebAppInfo(url=url)
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="📖 Как играть", callback_data="how_to_play")
    ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(WELCOME_TEXT, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


# ── FastAPI ───────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    polling_task = asyncio.create_task(dp.start_polling(bot))
    logging.info(f"Бот запущен! WEBAPP_URL={WEBAPP_URL}")
    yield
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)


def add_ngrok_header(response):
    """Добавляет заголовок, убирающий предупреждение ngrok."""
    response.headers["ngrok-skip-browser-warning"] = "true"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.get("/")
async def serve_game():
    game_file = Path(__file__).parent / "index.html"
    response = FileResponse(str(game_file), media_type="text/html")
    return add_ngrok_header(response)


@app.get("/health")
async def health():
    return {"status": "ok", "webapp_url": WEBAPP_URL}


@app.middleware("http")
async def ngrok_middleware(request: Request, call_next):
    """Автоматически добавляет ngrok заголовок ко всем ответам."""
    response = await call_next(request)
    response.headers["ngrok-skip-browser-warning"] = "true"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
