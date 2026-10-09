import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import requests
from datetime import datetime, timedelta, date
import calendar
import math
import json
import os
import re
import urllib.parse

try:
    from anthropic import Anthropic
except ImportError:  # AI-аналітик просто вимкнеться, якщо пакет не встановлено
    Anthropic = None

# ==============================================================================
# 🔗 1. НАЛАШТУВАННЯ ТАБЛИЦЬ ТА API
# ==============================================================================
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?usp=sharing"
WEEKLY_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?gid=1342107748#gid=1342107748"
NINTENDO_MONTHLY_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?gid=1182691055#gid=1182691055"
XBOX_MONTHLY_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?gid=1981339676#gid=1981339676"
ACTIVITY_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?gid=962012405#gid=962012405"
GOOGLE_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzrYmeab3xtC4TW9id-N60pI6UmOk6OJj7L2OebkV48omIzqD_h827g3C1mSUpt_WusyA/exec"
ANTHROPIC_API_KEY = ""

CERTIFICATION_SHEET_NAME = "Certification"
LEADS_SHEET_NAME = "Leads"          # лист, куди webhook записує ліди з калькулятора
LOGO_FILE = "up4.png"
DEFAULT_IMAGE = "https://img.icons8.com/isometric/100/controller.png"

# ==============================================================================
# 💱 2. ДОВІДНИКИ, ЦІЛІ ТА МОДЕЛІ
# ==============================================================================
SECTIONS = [
    "🎮 Портфоліо",
    "💰 Продажі та цілі",
    "📅 Календар і сейли",
    "🚀 Релізи",
    "🧮 Прогнози та ліди",
]

PLATFORMS = ["Switch", "PS", "Xbox"]
PLATFORM_LABEL = {"Switch": "Nintendo Switch", "PS": "PlayStation", "Xbox": "Xbox"}
PLATFORM_COLORS = {"Nintendo Switch": "#e60012", "PlayStation": "#3b82f6", "Xbox": "#107c10"}
WEEKLY_PREFIX = {"Switch": "Nintendo", "PS": "PS", "Xbox": "Xbox"}  # префікси колонок тижневого листа

FX_RATES = {
    "USD": 1.00, "EUR": 1.09, "GBP": 1.28, "AUD": 0.67, "NZD": 0.61, "CAD": 0.74,
    "CHF": 1.15, "JPY": 0.0068, "CZK": 0.044, "PLN": 0.26, "ZAR": 0.055, "BRL": 0.18,
    "MXN": 0.052, "SEK": 0.096, "NOK": 0.093, "DKK": 0.146, "CLP": 0.0011, "COP": 0.00024,
    "PEN": 0.27, "ARS": 0.0010, "HKD": 0.128, "KRW": 0.00075, "TWD": 0.031
}

UKR_MONTH_NAMES = ["", "Січ", "Лют", "Бер", "Кві", "Тра", "Чер", "Лип", "Сер", "Вер", "Жов", "Лис", "Гру"]

# 🎯 ЦІЛІ НА 2026 РІК ($500k)
TARGETS_2026 = {
    "2026 (рік)": {"Revenue": 500000.0, "Nintendo_Revenue": 130000.0, "PS_Revenue": 250000.0, "Xbox_Revenue": 120000.0,
                   "Deals": 20, "Calls": 100, "Contacts": 500, "Leads": 6000},
    "Q1 2026": {"Revenue": 90000.0, "Nintendo_Revenue": 23500.0, "PS_Revenue": 45000.0, "Xbox_Revenue": 21500.0,
                "Deals": 4, "Calls": 20, "Contacts": 100, "Leads": 1200},
    "Q2 2026": {"Revenue": 110000.0, "Nintendo_Revenue": 28500.0, "PS_Revenue": 55000.0, "Xbox_Revenue": 26500.0,
                "Deals": 5, "Calls": 25, "Contacts": 125, "Leads": 1500},
    "Q3 2026": {"Revenue": 130000.0, "Nintendo_Revenue": 34000.0, "PS_Revenue": 65000.0, "Xbox_Revenue": 31000.0,
                "Deals": 5, "Calls": 25, "Contacts": 125, "Leads": 1500},
    "Q4 2026": {"Revenue": 170000.0, "Nintendo_Revenue": 44000.0, "PS_Revenue": 85000.0, "Xbox_Revenue": 41000.0,
                "Deals": 6, "Calls": 30, "Contacts": 150, "Leads": 1800},
}

# Статус сейлу ("йде зараз / майбутній / завершився") тепер рахується автоматично від сьогоднішньої дати
NINTENDO_SCHEDULE = [
    {"name": "Autumn Sale", "start": "2026-09-11", "end": "2026-09-24", "region": "Global / EU / US"},
    {"name": "Halloween Sale", "start": "2026-10-26", "end": "2026-11-15", "region": "Global"},
    {"name": "Holiday Sale (EU)", "start": "2026-12-17", "end": "2027-01-10", "region": "Europe / Australia"},
    {"name": "Holiday Sale (US)", "start": "2026-12-21", "end": "2027-01-11", "region": "Americas"},
]

XBOX_SCHEDULE = [
    {"name": "Deep Discounts Sale (ID)", "start": "2026-11-05", "end": "2026-11-11", "deadline": "2026-10-01", "feedback": "2026-10-14",
     "limit": 10, "min_price": 0.0, "min_discount": 65, "type": "ID Sale (Глибокі знижки)",
     "note": "Знижка 65% або більше. Ліміт: до 10 тайтлів."},
    {"name": "Black Friday Sale", "start": "2026-11-20", "end": "2026-12-02", "deadline": "2026-10-02", "feedback": "2026-10-15",
     "limit": 5, "min_price": 9.99, "min_discount": 10, "type": "Tentpole Sale",
     "note": "Базова ціна від $9.99. Ліміт: до 5 тайтлів. Кулдаун знято тільки між BF та Countdown."},
    {"name": "Countdown Sale", "start": "2026-12-17", "end": "2027-01-06", "deadline": "2026-10-30", "feedback": "2026-11-13",
     "limit": 5, "min_price": 9.99, "min_discount": 10, "type": "Tentpole Sale",
     "note": "Базова ціна від $9.99. Ліміт: до 5 тайтлів."},
]
NINTENDO_COOLDOWN_DAYS = 30

GENRE_DATABASE = {
    "Simulator: Animal Chaos / Cat Meme (3D)": {"PS": 3.2, "Xbox": 1.25, "Switch": 1.35, "Decay": 1.25, "Desc": "Bad Cat, Bad Raccoon, Angry Dog, Smash Cat"},
    "Simulator: Crime / Black Market (3D)": {"PS": 4.0, "Xbox": 4.2, "Switch": 0.4, "Decay": 1.20, "Desc": "Drug Dealer Empire (Xbox феномен)"},
    "Simulator: Cozy Cafe / Animal Job Sim": {"PS": 1.8, "Xbox": 1.1, "Switch": 1.35, "Decay": 1.25, "Desc": "Funny Animal Cafe, Tricky Monkey Zoo, Funny Folks Cafe"},
    "Simulator: Shop / Supermarket / Store (3D)": {"PS": 2.2, "Xbox": 1.2, "Switch": 1.85, "Decay": 1.35, "Desc": "My Supermarket Simulator (Лідер на Switch)"},
    "Simulator: Job / Service / Business (3D)": {"PS": 1.5, "Xbox": 1.1, "Switch": 0.95, "Decay": 1.20, "Desc": "Waterpark Manager, Street Food Simulator, Digging Sim"},
    "Simulator: Truck / Heavy Logistics (3D/2D)": {"PS": 1.4, "Xbox": 1.55, "Switch": 2.10, "Decay": 1.25, "Desc": "Heavy Duty, Trucker Ben"},
    "Simulator: Farming / Homestead / Ranch": {"PS": 0.9, "Xbox": 1.1, "Switch": 2.6, "Decay": 1.35, "Desc": "Монополія аудиторії Nintendo"},
    "Simulator: Casual Flight / Paper Plane": {"PS": 0.3, "Xbox": 0.20, "Switch": 0.25, "Decay": 1.15, "Desc": "🔴 Paperly, Fly for Fly (Зона низької конверсії)"},
    "Horror: 3D PSX / Retro / VHS Style": {"PS": 1.6, "Xbox": 2.6, "Switch": 0.35, "Decay": 1.20, "Desc": "Skinwalker, TROX, Is Today Another Day (Xbox домінує)"},
    "Horror: 3D First-Person Atmospheric": {"PS": 1.4, "Xbox": 1.1, "Switch": 0.32, "Decay": 1.15, "Desc": "Cornfield, Death Attraction, Dr. Psycho, Captive, Seishin"},
    "Horror: 3D Anomaly / Walking Sim / Backrooms": {"PS": 2.4, "Xbox": 1.5, "Switch": 0.8, "Decay": 1.15, "Desc": "Exit 8, Don't Scream (PS попит)"},
    "Survival: Bunker / Hardcore Crafting (3D/2D)": {"PS": 1.8, "Xbox": 3.2, "Switch": 1.8, "Decay": 1.30, "Desc": "From the Bunker, Survival After War (Xbox + Switch)"},
    "Survival: Open-World / Island Crafting (3D)": {"PS": 1.6, "Xbox": 1.8, "Switch": 1.4, "Decay": 1.25, "Desc": "Call of Island, WinterCraft"},
    "Platformer: 3D Physics / Character Adventure": {"PS": 1.8, "Xbox": 1.6, "Switch": 1.5, "Decay": 1.20, "Desc": "Super Adventure Hand"},
    "Platformer: 3D Obby / Roblox-style": {"PS": 1.6, "Xbox": 1.2, "Switch": 1.8, "Decay": 1.20, "Desc": "Obby Parkour, Blade Ball"},
    "Physics: 3D Ragdoll / Sandbox Chaos": {"PS": 2.8, "Xbox": 1.1, "Switch": 1.4, "Decay": 1.15, "Desc": "Mr. Dude, Action Playground, Car Crash"},
    "Physics: Rage / Climbing / 'Only Up'": {"PS": 1.6, "Xbox": 1.0, "Switch": 1.3, "Decay": 1.15, "Desc": "Super Rock Climber"},
    "Cozy: Organization / Packing / Decor": {"PS": 0.7, "Xbox": 0.4, "Switch": 2.6, "Decay": 1.40, "Desc": "Packit List, Unpacking-вайб"},
    "Puzzle: 2D Mobile-style / Jigsaw / Color": {"PS": 0.5, "Xbox": 0.6, "Switch": 1.4, "Decay": 1.30, "Desc": "Find Sort Match, Trainlax, Pixel House"},
    "Puzzle: Suika / Drop & Merge / Watermelon": {"PS": 0.5, "Xbox": 0.4, "Switch": 2.2, "Decay": 1.20, "Desc": "Suika Balls, Fruit Merge"},
    "Puzzle: Hidden Object / Detective Quest": {"PS": 1.4, "Xbox": 0.95, "Switch": 1.70, "Decay": 1.35, "Desc": "Conquistadorio, Minima, Dollmaker"},
    "Racing: 3D Arcade / Traffic Driving": {"PS": 2.2, "Xbox": 0.6, "Switch": 1.30, "Decay": 1.20, "Desc": "Hyper Cars Ramp Crash, Gran Carismo"},
    "Action: 3D Top-Down / Extraction Shooter": {"PS": 1.6, "Xbox": 1.5, "Switch": 1.00, "Decay": 1.25, "Desc": "Bunker 22, Zombiescraper"},
    "Action: 2D Hack'n'Slash / Beat'em Up": {"PS": 1.1, "Xbox": 0.9, "Switch": 1.2, "Decay": 1.20, "Desc": "Bob the Warrior, Street Combat"},
    "Fighting: 2D/3D Local Party / Brawler": {"PS": 0.6, "Xbox": 0.5, "Switch": 0.50, "Decay": 1.15, "Desc": "Street Combat Fighting"},
    "Roguelike: Auto-Shooter / 'Survivor-like'": {"PS": 1.3, "Xbox": 1.75, "Switch": 2.35, "Decay": 1.25, "Desc": "Nom Nom Apocalypse"},
    "Card Game / Deckbuilder / Narrative": {"PS": 0.9, "Xbox": 1.35, "Switch": 0.70, "Decay": 1.20, "Desc": "Rabbit Samurai"},
    "Metroidvania: 2D Pixel / Action Platformer": {"PS": 0.8, "Xbox": 0.47, "Switch": 0.15, "Decay": 1.15, "Desc": "⚠️ ABSURDIKA: Rebuild"},
    "Strategy: Tower Defense / Castle Defense": {"PS": 1.4, "Xbox": 1.10, "Switch": 1.28, "Decay": 1.25, "Desc": "Epic Empire, Wizard's Fortress"},
    "Visual Novel: Western / Narrative Choice": {"PS": 0.8, "Xbox": 0.52, "Switch": 0.31, "Decay": 1.25, "Desc": "Choice of Life: Wild Islands"},
    "Idle / Clicker / Incremental": {"PS": 0.5, "Xbox": 0.4, "Switch": 1.00, "Decay": 1.20, "Desc": "Loaders Inc., Let's Journey"},
}
DEFAULT_GENRE = "Simulator: Job / Service / Business (3D)"

PRICE_MODIFIERS = {1.99: 1.40, 4.99: 1.20, 5.99: 1.10, 6.99: 1.05, 9.99: 1.00, 14.99: 0.70, 19.99: 0.50, 49.99: 0.20, 99.99: 0.10}

# 🧠 Єдина модель життєвого циклу — використовується в «Інсайтах», «Аналітиці» та калькуляторі
LTV_MULT = {"M3": 1.35, "M6": 1.70, "1Y": 3.0}
PERIODS = ["M1", "M3", "M6", "1Y"]
PERIOD_DAYS = {"M1": 30, "M3": 90, "M6": 180, "1Y": 365}
# True  — колонки "3 month", "6 month", "1 year" накопичувальні (виручка з дня релізу)
# False — кожна колонка містить виручку лише за свій відрізок; код сам їх підсумує
PERIOD_COLS_ARE_CUMULATIVE = True
DEV_OK_BAND = 15  # ±% — «в межах моделі»

# 💵 Фінансові параметри за замовчуванням (змінюються слайдерами у «Портфоліо → P&L»)
DEFAULT_STORE_CUT = 30
DEFAULT_TAX_CUT = 7
DEFAULT_DEV_SPLIT = 50

ACTIVITY_CHECKBOX_COLS = [
    "Keymailer page", "Instagram", "YouTube", "PS Form", "PS Trailer",
    "Xbox Trailer", "Xbox Shorts", "Xbox Form", "IGN Trailer", "Press Release", "Trophy Guide", "Keys"
]

TODAY = date.today()

# ==============================================================================
# 🎨 3. СТОРІНКА, CSS ТА ТЕМА ГРАФІКІВ
# ==============================================================================
st.set_page_config(
    page_title="Upscale Studio | Console BI & Growth Hub",
    page_icon=LOGO_FILE if os.path.exists(LOGO_FILE) else "🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2.5rem; max-width: 96% !important; }
    section[data-testid="stSidebar"] > div:first-child { padding-top: 1.2rem !important; }

    section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child,
    section[data-testid="stSidebar"] div[role="radiogroup"] input[type="radio"],
    section[data-testid="stSidebar"] [data-testid="stRadioButtonCustom"],
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
        display: none !important; visibility: hidden !important; width: 0 !important; height: 0 !important; margin: 0 !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] { display: flex !important; flex-direction: column !important; gap: 6px !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background-color: #161622 !important; border: 1px solid #28283c !important; border-radius: 9px !important;
        padding: 10px 14px !important; margin: 0 !important; cursor: pointer !important; transition: all 0.2s ease !important;
        display: flex !important; align-items: center !important; width: 100% !important; box-sizing: border-box !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: #202033 !important; border-color: #a855f7 !important; transform: translateX(3px) !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked),
    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
        background: linear-gradient(90deg, rgba(217, 70, 239, 0.22) 0%, rgba(249, 115, 22, 0.16) 100%) !important;
        border: 1px solid #d946ef !important; box-shadow: 0 3px 12px rgba(217, 70, 239, 0.18) !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label p { color: #94a3b8 !important; font-size: 13.5px !important; font-weight: 600 !important; margin: 0 !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p,
    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] p { color: #ffffff !important; font-weight: 700 !important; }

    .stTabs [data-baseweb="tab-list"] { gap: 16px; border-bottom: 1px solid #28283c; background-color: transparent !important; padding-bottom: 0px; }
    .stTabs [data-baseweb="tab"] {
        height: 38px; background-color: transparent !important; border: none !important; border-bottom: 2px solid transparent !important;
        padding: 4px 10px; color: #94a3b8 !important; font-size: 14px; font-weight: 500; transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #e2e8f0 !important; }
    .stTabs [aria-selected="true"] { background-color: transparent !important; color: #ffffff !important; font-weight: 700 !important; border-bottom: 2px solid #d946ef !important; }

    .kpi-card {
        background: linear-gradient(135deg, #1e1e2d 0%, #161622 100%); border: 1px solid #2e2e44; border-radius: 12px;
        padding: 16px 20px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25); margin-bottom: 10px; height: 100%;
        display: flex; flex-direction: column; justify-content: space-between;
    }
    .kpi-label { font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 4px; }
    .kpi-value { font-size: 24px; font-weight: 800; color: #ffffff; margin-bottom: 4px; font-family: -apple-system, sans-serif; }
    .kpi-badge { display: inline-block; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px; width: fit-content; }
    .badge-total { background-color: rgba(99, 102, 241, 0.2); color: #a5b4fc; }
    .badge-switch { background-color: rgba(230, 0, 18, 0.18); color: #ff6b6b; }
    .badge-ps { background-color: rgba(0, 55, 145, 0.25); color: #60a5fa; }
    .badge-xbox { background-color: rgba(16, 124, 16, 0.25); color: #4ade80; }

    .top-podium-card { background: #181824; border: 1px solid #2b2b3f; border-radius: 10px; padding: 12px; text-align: center; }
    .sandbox-box { background: #171724; border: 1px solid #2f2f45; border-radius: 12px; padding: 20px; margin-bottom: 15px; }
    .alert-card-red { background: linear-gradient(135deg, #2d141e 0%, #1c0d13 100%); border: 1px solid #7f1d1d; border-left: 5px solid #ef4444; border-radius: 10px; padding: 14px; margin-bottom: 12px; }
    .alert-card-yellow { background: linear-gradient(135deg, #2d2414 0%, #1c170d 100%); border: 1px solid #854d0e; border-left: 5px solid #eab308; border-radius: 10px; padding: 14px; margin-bottom: 12px; }

    .cal-container { background: #13131e; border: 1px solid #28283c; border-radius: 12px; overflow: hidden; margin-top: 15px; }
    .cal-header { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); background: #1a1a27; border-bottom: 1px solid #28283c; }
    .cal-header-cell { padding: 10px; text-align: center; font-size: 12px; font-weight: 700; color: #94a3b8; text-transform: uppercase; }
    .cal-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 1px; background: #242436; }
    .cal-day-cell { background: #161622; min-width: 0; min-height: 110px; padding: 6px; display: flex; flex-direction: column; transition: background 0.15s ease; }
    .cal-day-cell:hover { background: #1c1c2b; }
    .cal-day-cell.other-month { background: #11111a; opacity: 0.45; }
    .cal-day-cell.today { background: #1d182b; border: 1.5px solid #d946ef; }
    .cal-day-num { font-size: 11px; font-weight: 700; color: #94a3b8; margin-bottom: 5px; text-align: right; }
    .cal-event-pill { font-size: 10px; font-weight: 600; padding: 3px 6px; border-radius: 4px; margin-bottom: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; }
    .pill-release { background: rgba(139, 92, 246, 0.25); border-left: 3px solid #a855f7; color: #e9d5ff; }
    .pill-nintendo { background: rgba(230, 0, 18, 0.2); border-left: 3px solid #ff4d4f; color: #ffccc7; }
    .pill-xbox { background: rgba(16, 124, 16, 0.22); border-left: 3px solid #52c41a; color: #d9f7be; }
    .pill-deadline { background: rgba(245, 158, 11, 0.25); border-left: 3px solid #faad14; color: #ffe58f; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# Одна тема для всіх графіків замість повторення paper_bgcolor/plot_bgcolor у кожному
pio.templates["upscale"] = go.layout.Template(layout=dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"),
    xaxis=dict(gridcolor="#28283c", zerolinecolor="#28283c"), yaxis=dict(gridcolor="#28283c", zerolinecolor="#28283c"),
    margin=dict(t=30, b=20, l=10, r=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text=""),
))
pio.templates.default = "plotly_dark+upscale"

# ==============================================================================
# ⚙️ 4. БАЗОВІ ХЕЛПЕРИ
# ==============================================================================
def is_blank(v):
    if v is None:
        return True
    try:
        if pd.isna(v):
            return True
    except (TypeError, ValueError):
        pass
    return str(v).strip().lower() in ("", "nan", "none", "null", "-", "—", "nat")


def safe_str(v):
    return "" if is_blank(v) else str(v).strip()


def parse_flexible_date(d_val):
    if is_blank(d_val):
        return None
    if isinstance(d_val, datetime):
        return d_val
    if isinstance(d_val, date):
        return datetime(d_val.year, d_val.month, d_val.day)
    d_str = str(d_val).strip()
    for fmt in ["%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y.%m.%d", "%m/%d/%Y"]:
        try:
            return datetime.strptime(d_str[:10], fmt)
        except ValueError:
            continue
    try:
        dt = pd.to_datetime(d_str, dayfirst=True)
        if pd.notna(dt):
            return dt.to_pydatetime()
    except Exception:
        pass
    return None


def to_date(v):
    dt = parse_flexible_date(v)
    return dt.date() if dt else None


def clean_num_val(val):
    if is_blank(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace("$", "").replace("€", "").replace("%", "").replace("\xa0", "").replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.find(".") < s.find(",") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def is_truthy(val):
    return (not is_blank(val)) and str(val).strip().lower() in ["true", "истина", "1", "yes", "да", "✅", "done", "t"]


def contains_japanese(text):
    return bool(text) and bool(re.search(r"[぀-ヿ㐀-䶿一-鿿]", str(text)))


def find_col(columns, *patterns, exclude=()):
    """Перша колонка, що містить один із patterns (у порядку пріоритету) і не містить exclude."""
    cols = list(columns)
    for p in patterns:
        for c in cols:
            cl = str(c).lower()
            if p in cl and not any(x in cl for x in exclude):
                return c
    return None


def fmt_usd(v, force_decimals=False):
    if v is None:
        return "—"
    if force_decimals or abs(v) < 100:
        return f"${v:,.2f}"
    return f"${v:,.0f}"


def safe_pct(part, whole):
    return (part / whole * 100) if whole else None


def kpi_card(col, label, value, badge="", badge_cls="badge-total", color=None):
    style = f' style="color:{color};"' if color else ""
    badge_html = f'<span class="kpi-badge {badge_cls}">{badge}</span>' if badge else ""
    col.markdown(
        f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value"{style}>{value}</div>{badge_html}</div>',
        unsafe_allow_html=True,
    )


def show_fig(fig, height=None, **layout):
    if height:
        layout["height"] = height
    if layout:
        fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, theme=None)


def csv_button(df, label, file_name, key=None):
    st.download_button(label, data=df.to_csv(index=False).encode("utf-8"), file_name=file_name, mime="text/csv", key=key)


# ---------------- Періоди (одна логіка вибору кварталу/року на весь застосунок) ----------------
def quarter_of(d):
    return (d.month - 1) // 3 + 1


def month_label(d):
    return f"{UKR_MONTH_NAMES[d.month]} {d.year}"


def month_label_to_date(label):
    try:
        name, y = str(label).split(" ")
        return date(int(y), UKR_MONTH_NAMES.index(name), 1)
    except (ValueError, IndexError):
        return None


def period_options(dates, include_months=False, extras=()):
    ds = sorted({d for d in (to_date(x) for x in dates) if d})
    opts = list(extras) + ["Весь період"]
    for y in sorted({d.year for d in ds}, reverse=True):
        opts.append(f"{y} (рік)")
        for q in sorted({quarter_of(d) for d in ds if d.year == y}, reverse=True):
            opts.append(f"Q{q} {y}")
            if include_months:
                for m in sorted({d.month for d in ds if d.year == y and quarter_of(d) == q}, reverse=True):
                    opts.append(f"{UKR_MONTH_NAMES[m]} {y}")
    return opts


def period_bounds(label):
    """Повертає (start, end) для 'Весь період' / '2026 (рік)' / 'Q3 2026' / 'Жов 2026'."""
    m = re.match(r"^(\d{4}) \(рік\)$", label)
    if m:
        y = int(m.group(1))
        return date(y, 1, 1), date(y, 12, 31)
    m = re.match(r"^Q([1-4]) (\d{4})$", label)
    if m:
        q, y = int(m.group(1)), int(m.group(2))
        end_month = q * 3
        return date(y, end_month - 2, 1), date(y, end_month, calendar.monthrange(y, end_month)[1])
    d = month_label_to_date(label)
    if d:
        return d, date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])
    return None, None


def period_picker(dates, key, label="Період:", include_months=False, extras=(), default=None):
    opts = period_options(dates, include_months=include_months, extras=extras)
    default = default or f"Q{quarter_of(TODAY)} {TODAY.year}"
    idx = opts.index(default) if default in opts else opts.index("Весь період")
    return st.selectbox(label, opts, index=idx, key=key)


def in_bounds(d, start, end):
    d = to_date(d)
    if d is None:
        return start is None and end is None
    return (start is None or d >= start) and (end is None or d <= end)


# ==============================================================================
# 📥 5. ЗАВАНТАЖЕННЯ ДАНИХ
# ==============================================================================
def get_export_url(url_or_id, sheet_name=None):
    if not url_or_id:
        return ""
    url_str = str(url_or_id).strip()
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url_str)
    sheet_id = match.group(1) if match else url_str
    if sheet_name:
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(str(sheet_name).strip())}"
    gid_match = re.search(r"[?#&]gid=([0-9]+)", url_str)
    gid = gid_match.group(1) if gid_match else "0"
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


@st.cache_data(ttl=300, show_spinner=False)
def load_sheet(url, sheet_name=None, no_header=False):
    """Єдиний завантажувач будь-якого листа Google Sheets у DataFrame (усі значення — текст)."""
    if not url:
        return pd.DataFrame()
    try:
        return pd.read_csv(get_export_url(url, sheet_name), dtype=str, header=None if no_header else "infer")
    except Exception:
        return pd.DataFrame()


TEXT_COLUMN_KEYS = ["cover", "image", "постер", "url", "фото", "link", "посилання", "date", "дата", "name", "назва",
                    "genre", "жанр", "status", "статус", "platform", "insights", "formula", "source", "developer"]


def load_catalog(url):
    df = load_sheet(url).copy()
    if df.empty:
        return df
    for col in df.columns:
        cl = str(col).lower()
        # "ai" шукаємо як окреме слово, щоб не зачепити Retail / Daily / Gain
        if any(k in cl for k in TEXT_COLUMN_KEYS) or re.search(r"\bai\b", cl):
            continue
        df[col] = df[col].apply(clean_num_val)
    name_col = find_col(df.columns, "game name", "game", "title", "назва") or df.columns[0]
    df = df.rename(columns={name_col: "Game_Name_Clean"})
    df["Game_Name_Clean"] = df["Game_Name_Clean"].apply(safe_str)
    return df[df["Game_Name_Clean"] != ""].reset_index(drop=True)


WEEKLY_COL_MAP = [
    "From", "To",
    "Nintendo_Sales", "Nintendo_Sales_Diff", "Nintendo_Wishlists", "Nintendo_Wishlists_Diff", "Nintendo_Revenue", "Nintendo_Revenue_Diff",
    "PS_Sales", "PS_Sales_Diff", "PS_Wishlists", "PS_Wishlists_Diff", "PS_Revenue", "PS_Revenue_Diff",
    "Xbox_Sales", "Xbox_Sales_Diff", "Xbox_Wishlists", "Xbox_Wishlists_Diff", "Xbox_Revenue", "Xbox_Revenue_Diff",
    "Leads", "Leads_Diff", "Sequence_Started", "Sequence_Started_Diff", "Contacts", "Contacts_Diff",
    "Opportunities", "Opportunities_Diff", "Calls", "Calls_Diff", "Deals", "Deals_Diff",
    "Twitter", "Twitter_Diff", "Instagram", "Instagram_Diff", "TikTok", "TikTok_Diff", "YouTube", "YouTube_Diff", "Discord", "Discord_Diff",
]
FUNNEL_STAGES = [("Leads", "🔍 Leads", "Додані ліди"), ("Sequence_Started", "🚀 Sequence", "Кому написали"),
                 ("Contacts", "✉️ Contacts", "Отримано відповідей"), ("Opportunities", "🎯 Opps", "Зацікавлені"),
                 ("Calls", "📞 Calls", "Дзвінки"), ("Deals", "🤝 Deals", "Підписані договори")]
SOCIAL_COLS = ["Twitter", "TikTok", "YouTube", "Discord", "Instagram"]


def load_weekly(url):
    raw_w = load_sheet(url, no_header=True)
    if raw_w.empty:
        return pd.DataFrame()
    head_rows = [" ".join(str(x) for x in raw_w.iloc[i].tolist() if not is_blank(x)).lower() for i in range(min(2, len(raw_w)))]
    if len(head_rows) > 1 and any(k in head_rows[1] for k in ["from", "sales", "to"]):
        data_df = raw_w.iloc[2:]
    elif any(k in head_rows[0] for k in ["from", "sales"]):
        data_df = raw_w.iloc[1:]
    else:
        data_df = raw_w
    data_df = data_df.reset_index(drop=True)

    out = pd.DataFrame({name: data_df.iloc[:, i] for i, name in enumerate(WEEKLY_COL_MAP) if i < data_df.shape[1]})
    for c in out.columns:
        if c not in ("From", "To"):
            out[c] = out[c].apply(clean_num_val)
    out["Parsed_Date"] = pd.to_datetime(out["From"].apply(parse_flexible_date), errors="coerce")
    # сортуємо за датою — «останній тиждень» і WoW більше не залежать від порядку рядків у листі
    out = out.dropna(subset=["Parsed_Date"]).sort_values("Parsed_Date").reset_index(drop=True)
    for col in ["PS_Revenue", "Nintendo_Revenue", "Xbox_Revenue", "PS_Sales", "Nintendo_Sales", "Xbox_Sales"]:
        if col not in out.columns:
            out[col] = 0.0
    out["Total_Revenue"] = out["PS_Revenue"] + out["Nintendo_Revenue"] + out["Xbox_Revenue"]
    out["Total_Sales"] = out["PS_Sales"] + out["Nintendo_Sales"] + out["Xbox_Sales"]
    out["Week"] = out["Parsed_Date"].dt.strftime("%d.%m.%Y")
    return out


# ---------------- Помісячні звіти сторів ----------------
def parse_nintendo_monthly_data(df_raw):
    date_cols = [c for c in df_raw.columns if re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", str(c).strip())]
    if not date_cols:
        return pd.DataFrame(), []

    cost_col = find_col(df_raw.columns, "points", "cost", "price", "ціна")
    curr_col = find_col(df_raw.columns, "curr", "валют")
    title_code_col = find_col(df_raw.columns, "titlecode", "title code")
    target_name_col = find_col(df_raw.columns, "itemname", "item name") or find_col(df_raw.columns, "titlename", "title name") or df_raw.columns[1]

    code_to_english = {}
    if title_code_col:
        for _, r in df_raw.iterrows():
            t_code, name = safe_str(r.get(title_code_col)), safe_str(r.get(target_name_col))
            if t_code and name and not contains_japanese(name):
                code_to_english.setdefault(t_code[:9], name)
                code_to_english.setdefault(t_code, name)

    def label_for(c_str):
        try:
            m, _, y = c_str.split("/")
            y = int(y) if int(y) >= 2000 else 2000 + int(y)
            return f"{UKR_MONTH_NAMES[int(m)]} {y}"
        except (ValueError, IndexError):
            return c_str

    label_map = {c: label_for(c) for c in date_cols}
    records = []
    for _, row in df_raw.iterrows():
        name = safe_str(row.get(target_name_col))
        if not name:
            continue
        t_code = safe_str(row.get(title_code_col)) if title_code_col else ""
        if contains_japanese(name):
            name = code_to_english.get(t_code) or code_to_english.get(t_code[:9]) or name
        fx = FX_RATES.get(safe_str(row.get(curr_col)).upper() or "USD", 1.0) if curr_col else 1.0
        cost = clean_num_val(row.get(cost_col)) if cost_col else 0.0
        rec = {"Назва гри / DLC": name}
        for d in date_cols:
            rec[label_map[d]] = rec.get(label_map[d], 0.0) + clean_num_val(row.get(d)) * cost * fx
        records.append(rec)
    if not records:
        return pd.DataFrame(), []

    labels = sorted(set(label_map.values()), key=lambda l: month_label_to_date(l) or date(2000, 1, 1))
    grouped = pd.DataFrame(records).groupby("Назва гри / DLC")[labels].sum().reset_index()
    grouped["Всього ($)"] = grouped[labels].sum(axis=1)
    return grouped.sort_values("Всього ($)", ascending=False).reset_index(drop=True), labels


def parse_xbox_monthly_data(df_raw):
    if df_raw.empty:
        return pd.DataFrame(), []
    title_col = next((c for c in df_raw.columns if c.lower().strip() in ["titlename", "parentproductname", "назва", "title"]), None)
    date_col = next((c for c in df_raw.columns if "datestamp" in c.lower() or c.lower().strip() == "date"), None)
    usd_col = find_col(df_raw.columns, "purchasepriceusdamount", "priceusdamount")
    if not (title_col and date_col and usd_col):
        return pd.DataFrame(), []

    df = pd.DataFrame({
        "Назва гри / DLC": df_raw[title_col].apply(safe_str),
        "d": df_raw[date_col].apply(to_date),
        "USD": df_raw[usd_col].apply(clean_num_val),
    })
    df = df[(df["Назва гри / DLC"] != "") & df["d"].notna()]
    if df.empty:
        return pd.DataFrame(), []
    df["Month"] = df["d"].apply(month_label)
    labels = sorted(df["Month"].unique(), key=month_label_to_date)
    pivot = df.pivot_table(index="Назва гри / DLC", columns="Month", values="USD", aggfunc="sum", fill_value=0.0).reset_index()
    pivot = pivot[["Назва гри / DLC"] + labels]
    pivot.columns.name = None
    pivot["Всього ($)"] = pivot[labels].sum(axis=1)
    return pivot.sort_values("Всього ($)", ascending=False).reset_index(drop=True), labels


def combine_monthly_matrices(n_matrix, x_matrix, n_months, x_months):
    frames = [m for m in (n_matrix, x_matrix) if not m.empty]
    if not frames:
        return pd.DataFrame(), []
    months = sorted(set(n_months) | set(x_months), key=lambda l: month_label_to_date(l) or date(2000, 1, 1))
    combined = pd.concat([f.drop(columns=["Всього ($)"]) for f in frames], ignore_index=True).fillna(0.0)
    combined = combined.groupby("Назва гри / DLC")[months].sum().reset_index()
    combined["Всього ($)"] = combined[months].sum(axis=1)
    return combined.sort_values("Всього ($)", ascending=False).reset_index(drop=True), months


# ==============================================================================
# 🧩 6. ДОМЕННА ЛОГІКА
# ==============================================================================
# ---------------- Каталог: колонки ----------------
def detect_catalog_columns(df):
    cols = df.columns
    return {
        "cover": find_col(cols, "cover", "image", "постер", "обкладинка"),
        "discount": find_col(cols, "target discount", "discount", "знижк"),
        "porting": find_col(cols, "porting cost", "porting", "витрати"),
        "split": find_col(cols, "revenue split", "split"),
        "recoup": find_col(cols, "recoup", "рекуп"),
        "release": find_col(cols, "release date", "дата релізу", "дата релиза", "release", exclude=("pred",)) or find_col(cols, "date", "дата"),
        "genre": find_col(cols, "genre", "жанр"),
        "price": find_col(cols, "price consoles", "ціна", "price", exclude=("pred", "forecast")),
        "total": next((c for c in cols if str(c).lower().strip() == "total" or "всього" in str(c).lower()), None),
        "source": find_col(cols, "platform source", "source", "джерело"),
    }


def platform_of(cl):
    if "playstation" in cl or re.search(r"(^|[^a-z])ps\d?([^a-z]|$)", cl):
        return "PS"
    if "switch" in cl or "nintendo" in cl or "nsw" in cl:
        return "Switch"
    if "xbox" in cl:
        return "Xbox"
    return None


def match_period(cl):
    """До якого періоду (M1/M3/M6/1Y) належить колонка ФАКТИЧНИХ продажів. Прогнози й дублікати (.1) ігноруються."""
    if any(x in cl for x in ["pred", "forecast", "план", "target", "прогноз", "all"]) or re.search(r"\.\d+$", cl):
        return None
    if "year" in cl or re.search(r"(^|[^a-z0-9])1y([^a-z0-9]|$)", cl):
        return "1Y"
    if re.search(r"6\s*month", cl) or re.search(r"(^|[^a-z0-9])m6([^0-9]|$)", cl):
        return "M6"
    if re.search(r"3\s*month", cl) or re.search(r"(^|[^a-z0-9])m3([^0-9]|$)", cl):
        return "M3"
    if "1st" in cl or "month 1" in cl or re.search(r"(^|[^a-z0-9])m1([^0-9]|$)", cl):
        return "M1"
    return None


def classify_sales_columns(df):
    period_cols = {p: {k: [] for k in PLATFORMS + [None]} for p in PERIODS}
    all_time = {k: [] for k in PLATFORMS}
    for c in df.columns:
        cl = str(c).lower()
        plat = platform_of(cl)
        p = match_period(cl)
        if p:
            period_cols[p][plat].append(c)
        elif plat and "all" in cl and not any(x in cl for x in ["pred", "forecast"]):
            all_time[plat].append(c)
    return period_cols, all_time


def row_period_fact(r, p, plat=None):
    """Факт за період: по платформі або сума платформ (якщо платформних колонок немає — загальні)."""
    if plat:
        cols = PERIOD_COLS[p][plat]
    else:
        cols = [c for k in PLATFORMS for c in PERIOD_COLS[p][k]] or PERIOD_COLS[p][None]
    total = sum(v for v in (clean_num_val(r[c]) for c in cols) if v > 0)
    return total if total > 0 else None


def game_price(r):
    return clean_num_val(r.get(COL["price"])) if COL["price"] else 0.0


def game_cover(r):
    v = safe_str(r.get(COL["cover"])) if COL["cover"] else ""
    return v if v.startswith("http") else DEFAULT_IMAGE


def game_release(r):
    return to_date(r.get(COL["release"])) if COL["release"] else None


def game_total(r):
    if COL["total"]:
        return clean_num_val(r.get(COL["total"]))
    return sum(clean_num_val(r.get(ALL_TIME_COLS[p][0])) for p in PLATFORMS if ALL_TIME_COLS[p])


def portfolio_totals(df):
    plat = {p: float(df[ALL_TIME_COLS[p][0]].apply(clean_num_val).sum()) if ALL_TIME_COLS[p] else 0.0 for p in PLATFORMS}
    total = float(df[COL["total"]].apply(clean_num_val).sum()) if COL["total"] else sum(plat.values())
    return total, plat


# ---------------- Життєвий цикл / LTV ----------------
def period_state(p, days_live):
    if days_live is None:
        return "unknown"
    if days_live < 0:
        return "future"
    return "done" if days_live >= PERIOD_DAYS[p] else "running"


def build_lifecycle(df):
    items = []
    for _, r in df.iterrows():
        name = safe_str(r.get("Game_Name_Clean"))
        if not name:
            continue
        facts = {p: row_period_fact(r, p) for p in PERIODS}
        if not PERIOD_COLS_ARE_CUMULATIVE:
            running = 0.0
            for p in PERIODS:
                if facts[p] is not None:
                    running += facts[p]
                    facts[p] = running
        m1 = facts["M1"] or 0.0
        rel = game_release(r)
        days_live = (TODAY - rel).days if rel else None

        forecasts, states, devs = {}, {}, {}
        for p in PERIODS:
            states[p] = period_state(p, days_live)
            if p == "M1":
                continue
            forecasts[p] = m1 * LTV_MULT[p] if m1 > 0 else None
            ok = forecasts[p] and facts[p] and states[p] in ("done", "unknown")
            devs[p] = (facts[p] - forecasts[p]) / forecasts[p] * 100 if ok else None
        last_dev_p = next((p for p in ["1Y", "M6", "M3"] if devs.get(p) is not None), None)

        items.append({
            "name": name, "img": game_cover(r), "price": game_price(r), "rel": rel, "days_live": days_live,
            "m1": m1, "m1_by_plat": {p: row_period_fact(r, "M1", p) or 0.0 for p in PLATFORMS},
            "facts": facts, "forecasts": forecasts, "states": states, "devs": devs,
            "last_dev_p": last_dev_p, "last_dev": devs.get(last_dev_p) if last_dev_p else None,
        })
    return items


# ---------------- Прогноз M1 (одна формула для калькулятора й аудиту точності) ----------------
def base_metric_from_source(source, value):
    s = str(source).lower()
    if value <= 0:
        return 0.0
    if "steam" in s:
        return value * 0.10 + 500.0
    if "google" in s or "play" in s:
        return math.sqrt(value) * 2.0 + 800.0
    if "crazy" in s or "web" in s:
        return value * 0.05 + 900.0
    if "itch" in s:
        return value * 10.0 + 400.0
    return 0.0


def match_genre(genre_str):
    g = safe_str(genre_str).lower()
    if g:
        for k in GENRE_DATABASE:
            if k.lower() in g or g in k.lower():
                return k
    return DEFAULT_GENRE


def forecast_m1(base, genre_key, price, platforms=PLATFORMS):
    cfg = GENRE_DATABASE[genre_key]
    pm = PRICE_MODIFIERS.get(round(price, 2), 1.0)
    return {p: (base * cfg[p] * pm if p in platforms else 0.0) for p in PLATFORMS}


def finance_settings():
    store = st.session_state.get("fin_store", DEFAULT_STORE_CUT)
    tax = st.session_state.get("fin_tax", DEFAULT_TAX_CUT)
    split = st.session_state.get("fin_split", DEFAULT_DEV_SPLIT)
    return store, tax, split


def studio_share():
    """Частка студії від gross (без рекупу): (100 − комісія стору − податки) × (1 − спліт девелопера)."""
    store, tax, split = finance_settings()
    return (100 - store - tax) / 100.0 * (1 - split / 100.0)


# ---------------- Сертифікація ----------------
STAGE_DONE, STAGE_WIP, STAGE_OVERDUE, STAGE_BACKLOG = "Uploaded / In Cert", "In Porting", "Overdue Dev", "Backlog"


def normalize_dev_name(raw_name):
    n = safe_str(raw_name)
    if not n:
        return "Не призначено"
    nl = n.lower()
    for keys, canon in [(("серг",), "Сергій"), (("ігор", "игор"), "Ігор"), (("іван", "иван"), "Іван"),
                        (("максим",), "Максим"), (("дим", "дмитр"), "Дмитро"), (("влад",), "Влад")]:
        if any(k in nl for k in keys):
            return canon
    return n


def process_certification_table(df_raw):
    if df_raw.empty:
        return pd.DataFrame()
    cols = df_raw.columns
    c_game = find_col(cols, "game name", "игра", "назва", "title") or cols[0]
    c_status = find_col(cols, "status", "статус")
    c_dev = find_col(cols, "developer", "разработчик", "розробник", "dev")
    c_rel = find_col(cols, "release date", "дата релиза")
    c_start = find_col(cols, "старт", "start")
    c_plan = find_col(cols, "планируемая дата", "plan finish")
    c_upload = find_col(cols, "загружен", "uploaded")
    c_plan_days = find_col(cols, "планируемый срок", "plan days")
    c_fact_days = find_col(cols, "фактический срок", "fact days")
    g = lambda r, c: r.get(c) if c else None

    records = []
    for _, r in df_raw.iterrows():
        name = safe_str(g(r, c_game))
        if not name:
            continue
        d_start, d_plan, d_upload, d_rel = (parse_flexible_date(g(r, c)) for c in (c_start, c_plan, c_upload, c_rel))

        p_days = clean_num_val(g(r, c_plan_days))
        if p_days == 0 and d_start and d_plan:
            p_days = max(1, (d_plan - d_start).days)
        f_days = clean_num_val(g(r, c_fact_days))
        if f_days == 0 and d_start and d_upload:
            f_days = max(1, (d_upload - d_start).days)

        delta = None
        if f_days > 0 and p_days > 0:
            delta = int(f_days - p_days)
        elif d_upload and d_plan:
            delta = (d_upload - d_plan).days

        if d_upload:
            stage = STAGE_DONE
            verdict = "🟢 Білд завантажено" if delta is None else ("🟢 Вчасно здано" if delta <= 0 else f"🔴 Затримка (+{delta} дн)")
        elif d_start and d_plan and TODAY > d_plan.date():
            stage, verdict = STAGE_OVERDUE, f"🚨 Прострочено (+{(TODAY - d_plan.date()).days} дн)"
        elif d_start:
            stage, verdict = STAGE_WIP, "⏳ В розробці (у плані)"
        else:
            stage, verdict = STAGE_BACKLOG, "⚪ В черзі"

        fmt = lambda d: d.strftime("%d.%m.%Y") if d else "—"
        records.append({
            "Гра": name, "Розробник": normalize_dev_name(g(r, c_dev)),
            "Статус у базі": safe_str(g(r, c_status)) or stage, "Етап": stage,
            "Дата старту": fmt(d_start), "План здачі білда": fmt(d_plan), "Дата завантаження білда": fmt(d_upload),
            "Реліз Nintendo": fmt(d_rel),
            "План (дн)": int(p_days) if p_days > 0 else None, "Факт (дн)": int(f_days) if f_days > 0 else None,
            "Відхилення (дн)": delta, "Вердикт": verdict,
            "_d_start": d_start, "_d_plan": d_plan, "_d_upload": d_upload, "_d_release": d_rel, "_delta": delta,
        })
    return pd.DataFrame(records)


def project_date(row):
    """Дата, за якою проєкт потрапляє в період: план здачі → завантаження → старт."""
    for cand in (row.get("_d_plan"), row.get("_d_upload"), row.get("_d_start")):
        if cand is not None and not pd.isna(cand):
            return to_date(cand)
    return None


def build_dev_kpi(df_sub, devs):
    rows = []
    for dev in devs:
        g = df_sub[df_sub["Розробник"] == dev]
        tot = len(g)
        done = int((g["Етап"] == STAGE_DONE).sum())
        overdue = int((g["Етап"] == STAGE_OVERDUE).sum())
        plan_d = pd.to_numeric(g["План (дн)"], errors="coerce").dropna()
        fact_d = pd.to_numeric(g["Факт (дн)"], errors="coerce").dropna()
        deltas = pd.to_numeric(g["_delta"], errors="coerce").dropna()
        on_time = float((deltas <= 0).mean() * 100) if not deltas.empty else None
        avg_delay = float(deltas.mean()) if not deltas.empty else None

        if tot:
            score = done / tot * 45 + (on_time * 0.35 if on_time is not None else 25.0) + 20.0
            score -= max(0.0, (avg_delay or 0.0) * 2) + overdue * 5
            kpi = round(min(100.0, max(0.0, score)), 1)
        else:
            kpi = None
        status = ("⚪ Немає проєктів" if kpi is None else "🟢 Топ-перформер" if kpi >= 80
                  else "🟡 Норма" if kpi >= 65 else "🔴 Зона ботлнеку")
        rows.append({
            "Розробник": dev, "Всього ігор": tot, "Здано білдів": done,
            "В роботі": int((g["Етап"] == STAGE_WIP).sum()), "Прострочено": overdue,
            "В черзі": int((g["Етап"] == STAGE_BACKLOG).sum()),
            "Сер. план (дн)": round(plan_d.mean(), 1) if not plan_d.empty else None,
            "Сер. факт (дн)": round(fact_d.mean(), 1) if not fact_d.empty else None,
            "Сер. відхилення (дн)": round(avg_delay, 1) if avg_delay is not None else None,
            "% вчасно": round(on_time) if on_time is not None else None,
            "KPI (0-100)": kpi, "Статус": status,
        })
    out = pd.DataFrame(rows)
    return out if out.empty else out.sort_values(["Всього ігор", "KPI (0-100)"], ascending=[False, False], na_position="last").reset_index(drop=True)


# ---------------- Сейли ----------------
def sale_dates(s):
    return (datetime.strptime(s["start"], "%Y-%m-%d").date(), datetime.strptime(s["end"], "%Y-%m-%d").date())


def sale_status(s):
    start, end = sale_dates(s)
    if TODAY < start:
        return f"🗓️ Через {(start - TODAY).days} дн."
    if TODAY <= end:
        return "🔥 Йде зараз"
    return "✔️ Завершився"


def default_sale_index(schedule, key_date="start"):
    """Перший сейл, який ще не завершився (або в якого ще не минув дедлайн)."""
    for i, s in enumerate(schedule):
        d = datetime.strptime(s[key_date] if key_date in s else s["end"], "%Y-%m-%d").date()
        if d >= TODAY:
            return i
    return len(schedule) - 1


def deadline_badge(deadline_str):
    d = datetime.strptime(deadline_str, "%Y-%m-%d").date()
    days = (d - TODAY).days
    if days > 0:
        return f"⏳ Залишилось {days} дн."
    if days == 0:
        return "🚨 Дедлайн СЬОГОДНІ!"
    return f"✖️ Минув {-days} дн. тому"

# ==============================================================================
# 🚀 7. ЗАВАНТАЖЕННЯ ОСНОВНИХ ДАНИХ
# ==============================================================================
raw_df = load_catalog(GOOGLE_SHEET_URL)
if raw_df.empty:
    st.info("👋 Вкажи валідне посилання на Google Таблицю у рядку `GOOGLE_SHEET_URL`.")
    st.stop()

COL = detect_catalog_columns(raw_df)
PERIOD_COLS, ALL_TIME_COLS = classify_sales_columns(raw_df)
pipe_df = process_certification_table(load_sheet(GOOGLE_SHEET_URL, CERTIFICATION_SHEET_NAME))
weekly_df = load_weekly(WEEKLY_SHEET_URL)


def build_ai_context():
    lines = ["Game|Genre|Price|DevCost|DevSplit|Recoup|Release|M1|PS_All|Switch_All|Xbox_All|Total"]
    for _, r in raw_df.iterrows():
        plat_all = {p: int(clean_num_val(r.get(ALL_TIME_COLS[p][0]))) if ALL_TIME_COLS[p] else 0 for p in PLATFORMS}
        rel = game_release(r)
        lines.append("|".join(str(x) for x in [
            r["Game_Name_Clean"], safe_str(r.get(COL["genre"])) if COL["genre"] else "—", game_price(r),
            clean_num_val(r.get(COL["porting"])) if COL["porting"] else 0,
            clean_num_val(r.get(COL["split"])) if COL["split"] else DEFAULT_DEV_SPLIT,
            clean_num_val(r.get(COL["recoup"])) if COL["recoup"] else 0,
            rel.isoformat() if rel else "—", int(row_period_fact(r, "M1") or 0),
            plat_all["PS"], plat_all["Switch"], plat_all["Xbox"], int(game_total(r)),
        ]))
    pipe_txt = pipe_df[["Гра", "Розробник", "Вердикт", "Відхилення (дн)"]].to_csv(index=False) if not pipe_df.empty else "No cert data"
    weekly_cols = ["Week", "Total_Revenue", "PS_Revenue", "Nintendo_Revenue", "Xbox_Revenue"] + [s[0] for s in FUNNEL_STAGES]
    weekly_txt = weekly_df[[c for c in weekly_cols if c in weekly_df.columns]].tail(26).to_csv(index=False) if not weekly_df.empty else "No weekly data"
    return "\n".join(lines), pipe_txt, weekly_txt


# ==============================================================================
# 🧭 8. САЙДБАР
# ==============================================================================
with st.sidebar:
    col_logo, col_title = st.columns([1, 2.8])
    with col_logo:
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, width=64)
        else:
            st.markdown("<div style='font-size:38px; text-align:center;'>🎮</div>", unsafe_allow_html=True)
    with col_title:
        st.markdown(
            "<h3 style='margin:0; padding-top:2px; font-weight:800; color:#fff; letter-spacing:0.5px; font-size:20px; white-space:nowrap;'>Upscale Studio</h3>"
            "<p style='margin:0; font-size:11px; font-weight:700; color:#d946ef; text-transform:uppercase; letter-spacing:0.8px;'>Publishing BI Hub</p>",
            unsafe_allow_html=True,
        )
    divider = "<div style='border-bottom: 1px solid #28283c; margin: 14px 0;'></div>"
    st.markdown(divider, unsafe_allow_html=True)

    st.caption("📍 НАВІГАЦІЯ ХАБУ:")
    app_mode = st.radio("Навігація:", SECTIONS, index=0, label_visibility="collapsed")

    # Фільтри каталогу показуємо лише там, де вони працюють
    filtered_df = raw_df
    if app_mode == SECTIONS[0]:
        st.markdown(divider, unsafe_allow_html=True)
        st.caption("🔍 ФІЛЬТРАЦІЯ КАТАЛОГУ:")
        search = st.text_input("Пошук гри:", "", label_visibility="collapsed", placeholder="Пошук гри...")
        if COL["genre"]:
            genres_all = sorted({safe_str(g) for g in raw_df[COL["genre"]] if safe_str(g)})
            sel_genres = st.multiselect("Жанри:", genres_all, default=[], placeholder="Усі жанри")
            if sel_genres:
                filtered_df = filtered_df[filtered_df[COL["genre"]].apply(safe_str).isin(sel_genres)]
        if search:
            filtered_df = filtered_df[filtered_df["Game_Name_Clean"].str.contains(search, case=False, na=False, regex=False)]

    st.markdown(divider, unsafe_allow_html=True)
    if st.button("🔄 Оновити дані з Google Sheets", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(divider, unsafe_allow_html=True)
    with st.expander("🤖 AI-аналітик", expanded=False):
        claude_key = ANTHROPIC_API_KEY
        if not claude_key:
            try:
                claude_key = st.secrets.get("ANTHROPIC_API_KEY", "")
            except Exception:  # немає secrets.toml
                claude_key = ""
        if not claude_key:
            claude_key = st.text_input("Anthropic Key:", type="password", placeholder="sk-ant-...")
        ai_query = st.text_area("Запитай базу даних:", placeholder="Напр.: Яка конверсія лідів у контракти?")
        if st.button("⚡ Запитати Claude", use_container_width=True):
            key = str(claude_key or "").strip()
            if Anthropic is None:
                st.error("Пакет `anthropic` не встановлено.")
            elif not key.startswith("sk-ant"):
                st.error("❌ Введи валідний ключ Anthropic (sk-ant-...)!")
            elif not ai_query.strip():
                st.warning("Введи запитання.")
            else:
                with st.spinner("Claude аналізує базу..."):
                    try:
                        portfolio_txt, pipe_txt, weekly_txt = build_ai_context()
                        prompt = (
                            "Ти — фінансовий директор і аналітик консольного видавництва Upscale Studio (Україна).\n"
                            f"Портфоліо ({len(raw_df)} ігор):\n{portfolio_txt}\n\n"
                            f"Сертифікація та швидкість девелоперів:\n{pipe_txt}\n\n"
                            f"Тижнева звітність і BizDev воронка (останні 26 тижнів):\n{weekly_txt}\n\n"
                            f'Запитання: "{ai_query}"\n\n'
                            "Дай точну відповідь українською з реальними цифрами та висновками. Суми пиши як \"USD 1,500\"."
                        )
                        client = Anthropic(api_key=key)
                        try:
                            msg = client.messages.create(model="claude-haiku-4-5", max_tokens=900, messages=[{"role": "user", "content": prompt}])
                        except Exception:
                            msg = client.messages.create(model="claude-3-5-haiku-20241022", max_tokens=900, messages=[{"role": "user", "content": prompt}])
                        st.markdown("##### 💡 Результат аналізу:")
                        st.markdown(re.sub(r"(?<!\\)\$", r"\\$", msg.content[0].text))
                    except Exception as e:
                        st.error(f"❌ Помилка Anthropic API: {e}")

# ==============================================================================
# 🎮 РОЗДІЛ 1: ПОРТФОЛІО
# ==============================================================================
def render_portfolio():
    st.title("📊 Портфоліо Upscale Studio")
    st.caption(f"Фактичні результати випущених ігор • У вибірці: **{len(filtered_df)}** ігор")

    total_gross, plat_rev = portfolio_totals(filtered_df)
    share = lambda v: f"↑ {round(v / total_gross * 100) if total_gross else 0}% частка"
    c = st.columns(4)
    kpi_card(c[0], "Загальна каса (All-Time)", fmt_usd(total_gross, True), "100% Total Gross")
    kpi_card(c[1], "Nintendo Switch", fmt_usd(plat_rev["Switch"], True), share(plat_rev["Switch"]), "badge-switch", "#ff6b6b")
    kpi_card(c[2], "PlayStation", fmt_usd(plat_rev["PS"], True), share(plat_rev["PS"]), "badge-ps", "#60a5fa")
    kpi_card(c[3], "Xbox", fmt_usd(plat_rev["Xbox"], True), share(plat_rev["Xbox"]), "badge-xbox", "#4ade80")
    st.markdown("<br>", unsafe_allow_html=True)

    items = build_lifecycle(filtered_df)
    tab_analytics, tab_insights, tab_pnl, tab_table = st.tabs([
        "📈 Аналітика", "🧠 Інсайти (LTV)", "💵 P&L, зарплати та роялті", "📑 Таблиця та One-Pager",
    ])

    with tab_analytics:
        render_portfolio_analytics(items, plat_rev)
    with tab_insights:
        render_insights(items)
    with tab_pnl:
        render_pnl()
    with tab_table:
        render_table_report(total_gross, plat_rev)


def render_portfolio_analytics(items, plat_rev):
    df = filtered_df.assign(_total=filtered_df.apply(game_total, axis=1))

    st.subheader("🏆 Топ-3 бестселери портфоліо")
    p_cols = st.columns(3)
    for idx, (_, row) in enumerate(df.nlargest(3, "_total").iterrows()):
        p_cols[idx].markdown(
            f'<div class="top-podium-card"><img src="{game_cover(row)}" style="width:100%; height:135px; object-fit:cover; border-radius:6px; margin-bottom:8px;">'
            f'<h4 style="margin:0 0 4px 0; color:#fff;">#{idx + 1} {row["Game_Name_Clean"]}</h4>'
            f'<p style="margin:0; font-size:18px; color:#34d399; font-weight:bold;">{fmt_usd(row["_total"], True)}</p></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    c_left, c_right = st.columns([1, 2])
    with c_left:
        st.subheader("Частка консолей у виручці")
        plat_df = pd.DataFrame({"Platform": [PLATFORM_LABEL[p] for p in PLATFORMS], "Revenue": [plat_rev[p] for p in PLATFORMS]})
        plat_df = plat_df[plat_df["Revenue"] > 0]
        if not plat_df.empty:
            show_fig(px.pie(plat_df, values="Revenue", names="Platform", hole=0.5, color="Platform", color_discrete_map=PLATFORM_COLORS))
    with c_right:
        st.subheader("Топ-15 тайтлів за виторгом ($)")
        top_df = df.nlargest(15, "_total").sort_values("_total")
        fig = px.bar(top_df, x="_total", y="Game_Name_Clean", orientation="h", text="_total", color_discrete_sequence=["#d946ef"])
        fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside", cliponaxis=False)
        show_fig(fig, xaxis_title="Виторг ($)", yaxis_title="")

    # Замість «спагеті» з лінією на кожну гру — одна крива: реальний медіанний множник vs модель
    st.markdown("---")
    st.subheader("⏳ Крива життєвого циклу: факт vs модель")
    st.caption("Медіанний множник до M1 по іграх, у яких період уже повністю минув. Деталі по кожній грі — у вкладці «Інсайти».")
    curve = []
    for p in ["M3", "M6", "1Y"]:
        ratios = [it["facts"][p] / it["m1"] for it in items
                  if it["m1"] > 0 and it["facts"][p] and it["states"][p] in ("done", "unknown")]
        curve.append({"Період": p, "Факт (медіана)": round(pd.Series(ratios).median(), 2) if ratios else None,
                      "Модель": LTV_MULT[p], "Ігор": len(ratios)})
    curve_df = pd.DataFrame([{"Період": "M1", "Факт (медіана)": 1.0, "Модель": 1.0, "Ігор": None}] + curve)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=curve_df["Період"], y=curve_df["Модель"], name="Модель", mode="lines+markers",
                             line=dict(color="#d946ef", dash="dash")))
    fig.add_trace(go.Scatter(x=curve_df["Період"], y=curve_df["Факт (медіана)"], name="Факт (медіана)", mode="lines+markers+text",
                             text=[f"{v:.2f}x" if v else "" for v in curve_df["Факт (медіана)"]], textposition="top center",
                             line=dict(color="#34d399", width=3)))
    show_fig(fig, height=340, yaxis_title="× від M1")
    st.caption(" • ".join(f"{r['Період']}: {r['Ігор']} ігор" for r in curve))


def lifecycle_badge(m1):
    if m1 >= 3000:
        return ("🔥 Сильний старт", "rgba(16,185,129,0.2)", "#34d399",
                "Високий органічний попит. Рекомендовано тримати знижки не глибше 30–45% у перші 6 місяців.")
    if m1 >= 1000:
        return ("🟡 Стабільна динаміка", "rgba(56,189,248,0.2)", "#38bdf8",
                "Збалансований темп. Основний добір каси — між 3-м та 6-м місяцями на сезонних сейлах (60–70%).")
    return ("⚠️ Слабкий M1", "rgba(245,158,11,0.2)", "#fbbf24",
            "Органіки за фулпрайс недостатньо. Рекомендовано швидше виходити на імпульсну ціну ($1.99–$2.49) для потрапляння в 'Great Deals'.")


def dev_badge(dev):
    if dev is None:
        return ""
    if dev >= DEV_OK_BAND:
        color, bg = "#34d399", "rgba(16,185,129,0.18)"
    elif dev <= -DEV_OK_BAND:
        color, bg = "#f87171", "rgba(239,68,68,0.18)"
    else:
        color, bg = "#fbbf24", "rgba(245,158,11,0.16)"
    return f'<span style="background:{bg}; color:{color}; font-weight:700; padding:1px 6px; border-radius:4px; margin-left:4px;">{dev:+.0f}%</span>'


def trajectory_svg(it):
    w, h, pad_x, pad_top, pad_bot = 190, 78, 14, 10, 18
    fc_vals = [it["m1"]] + [it["forecasts"][p] for p in ["M3", "M6", "1Y"]]
    fact_vals = [it["facts"]["M1"]] + [it["facts"][p] if it["states"][p] != "future" else None for p in ["M3", "M6", "1Y"]]
    all_v = [v for v in fc_vals + fact_vals if v]
    if not all_v:
        return ""
    top = max(all_v) * 1.05
    xs = [pad_x + i * (w - 2 * pad_x) / 3 for i in range(4)]
    y = lambda v: pad_top + (1 - v / top) * (h - pad_top - pad_bot)
    fc_pts = " ".join(f"{xs[i]:.1f},{y(v):.1f}" for i, v in enumerate(fc_vals) if v)
    fact_idx = [i for i, v in enumerate(fact_vals) if v]
    fact_pts = " ".join(f"{xs[i]:.1f},{y(fact_vals[i]):.1f}" for i in fact_idx)
    dots = "".join(
        f'<circle cx="{xs[i]:.1f}" cy="{y(fact_vals[i]):.1f}" r="3.2" '
        f'fill="{"#161622" if i > 0 and it["states"][PERIODS[i]] == "running" else "#34d399"}" stroke="#34d399" stroke-width="1.5"/>'
        for i in fact_idx
    )
    labels = "".join(f'<text x="{xs[i]:.1f}" y="{h - 4}" fill="#64748b" font-size="9" text-anchor="middle">{p}</text>' for i, p in enumerate(PERIODS))
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="flex-shrink:0;">'
        f'<polyline points="{fc_pts}" fill="none" stroke="#d946ef" stroke-width="1.8" stroke-dasharray="4 3"/>'
        f'<polyline points="{fact_pts}" fill="none" stroke="#34d399" stroke-width="2"/>{dots}{labels}</svg>'
        '<div style="font-size:10px; color:#94a3b8; text-align:center; margin-top:2px;">'
        '<span style="color:#d946ef;">┅</span> прогноз &nbsp; <span style="color:#34d399;">━</span> факт</div>'
    )


def render_insights(items):
    st.subheader("🧠 Життєвий цикл та LTV (M1 ➔ M3 ➔ M6 ➔ 1Y)")
    st.caption(f"Модель: M3 = {LTV_MULT['M3']}×M1 • M6 = {LTV_MULT['M6']}×M1 • 1Y = {LTV_MULT['1Y']}×M1 • "
               "Факт порівнюється з прогнозом лише за періоди, які вже повністю минули від дати релізу")

    f1, f2 = st.columns([1.3, 1])
    only_m1 = f1.checkbox("Показати тільки ігри з зафіксованим фактом M1", value=False)
    sort_mode = f2.selectbox("Сортування:", ["Як у таблиці", "Найбільше відхилення від прогнозу", "Найновіші релізи", "Найбільший M1"],
                             label_visibility="collapsed")

    cards = [it for it in items if it["m1"] > 0] if only_m1 else list(items)
    if sort_mode == "Найбільше відхилення від прогнозу":
        cards.sort(key=lambda it: abs(it["last_dev"]) if it["last_dev"] is not None else -1, reverse=True)
    elif sort_mode == "Найновіші релізи":
        cards.sort(key=lambda it: it["rel"] or date(1900, 1, 1), reverse=True)
    elif sort_mode == "Найбільший M1":
        cards.sort(key=lambda it: it["m1"], reverse=True)

    chip_style = "background:#13131e; border:1px solid #28283c; border-radius:6px; padding:6px 10px; font-size:12px; min-width:150px;"
    period_color = {"M3": "#38bdf8", "M6": "#a855f7", "1Y": "#d946ef"}
    badge_tpl = '<span style="background:{bg}; color:{fg}; font-size:11px; font-weight:bold; padding:2px 8px; border-radius:5px;">{txt}</span>'

    for it in cards:
        m1 = it["m1"]
        price_tag = f"${it['price']:.2f}" if it["price"] > 0 else "—"
        if it["rel"]:
            live = f" · {it['days_live']} дн. у продажу" if it["days_live"] >= 0 else f" · вихід через {-it['days_live']} дн."
            rel_tag = f"Реліз: {it['rel'].strftime('%d.%m.%Y')}{live}"
        else:
            rel_tag = "Реліз: —"

        if m1 > 0:
            txt, bg, fg, base_text = lifecycle_badge(m1)
            badge = badge_tpl.format(bg=bg, fg=fg, txt=txt)
            chips = [f'<div style="{chip_style}"><div style="color:#94a3b8;">Факт M1</div>'
                     f'<div style="color:#34d399; font-size:14px; font-weight:700;">{fmt_usd(m1)}</div>'
                     f'<div style="color:#64748b; font-size:11px;">база для прогнозу</div></div>']
            for p in ["M3", "M6", "1Y"]:
                fact_v, st_p = it["facts"][p], it["states"][p]
                if st_p in ("done", "unknown") and fact_v:
                    fact_line = f'Факт: <b style="color:#e2e8f0;">{fmt_usd(fact_v)}</b>{dev_badge(it["devs"][p])}'
                elif st_p == "running":
                    now_v = f"{fmt_usd(fact_v)} · " if fact_v else ""
                    fact_line = f'<span style="color:#64748b;">Зараз: {now_v}ще {PERIOD_DAYS[p] - it["days_live"]} дн.</span>'
                elif st_p == "future":
                    fact_line = '<span style="color:#64748b;">Ще не вийшла</span>'
                else:
                    fact_line = '<span style="color:#64748b;">Факт: немає даних</span>'
                chips.append(f'<div style="{chip_style}"><div style="color:#94a3b8;">Прогноз {p} ({LTV_MULT[p]:.2f}x)</div>'
                             f'<div style="color:{period_color[p]}; font-size:14px; font-weight:700;">{fmt_usd(it["forecasts"][p])}</div>'
                             f'<div style="font-size:11px; color:#94a3b8; margin-top:2px;">{fact_line}</div></div>')
            projections = '<div style="display:flex; flex-wrap:wrap; gap:8px; margin:10px 0;">' + "".join(chips) + "</div>"

            if it["last_dev"] is not None:
                p, d = it["last_dev_p"], it["last_dev"]
                if d >= DEV_OK_BAND:
                    dev_text = f" 📈 Факт {p} випереджає модель на <b>{d:+.0f}%</b> — довгий хвіст сильніший за середній, з глибокими знижками можна не поспішати."
                elif d <= -DEV_OK_BAND:
                    dev_text = f" 📉 Факт {p} відстає від моделі на <b>{d:.0f}%</b> — хвіст продажів слабший, варто раніше підключати сейли та бандли."
                else:
                    dev_text = f" ✅ Факт {p} у межах ±{DEV_OK_BAND}% від моделі ({d:+.0f}%)."
            else:
                dev_text = f" Очікуваний річний LTV: <b>~{fmt_usd(it['forecasts']['1Y'])}</b>."
            insight = base_text + dev_text
            svg = f'<div style="display:flex; flex-direction:column; align-items:center;">{trajectory_svg(it)}</div>'
        else:
            badge = badge_tpl.format(bg="rgba(100,116,139,0.2)", fg="#94a3b8", txt="⏳ Очікує релізу / Немає M1")
            projections = '<div style="margin:8px 0; font-size:12px; color:#64748b;"><i>Прогноз життєвого циклу розрахується автоматично після появи продажів за перший місяць.</i></div>'
            insight = "Тайтл перебуває в розробці, на сертифікації або ще не накопичив звітних даних першого місяця."
            svg = ""

        st.markdown(
            '<div style="display:flex; gap:16px; background:#161622; border:1px solid #28283c; border-radius:12px; padding:16px; margin-bottom:12px; align-items:flex-start;">'
            f'<img src="{it["img"]}" style="width:85px; height:105px; object-fit:cover; border-radius:8px; flex-shrink:0;" onerror="this.src=\'{DEFAULT_IMAGE}\'">'
            '<div style="flex-grow:1; min-width:0;">'
            '<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">'
            f'<h4 style="margin:0; color:#fff; font-size:16px;">🎮 {it["name"]} '
            f'<span style="font-size:12px; color:#94a3b8; font-weight:normal;">(Ціна: {price_tag} · {rel_tag})</span></h4>{badge}</div>'
            f'<div style="display:flex; gap:14px; align-items:center; flex-wrap:wrap;"><div style="flex-grow:1;">{projections}</div>{svg}</div>'
            '<div style="background:#0f0f17; border-left:3px solid #d946ef; border-radius:4px; padding:8px 12px; font-size:12px; color:#cbd5e1; line-height:1.4;">'
            f'💡 <b>Інсайт та рекомендація:</b> {insight}</div></div></div>',
            unsafe_allow_html=True,
        )


def render_pnl():
    st.subheader("💵 Фінансовий P&L, зарплати портингу та роялті девелоперів")
    with st.expander("⚙️ Параметри комісій і податків (діють і в калькуляторі лідів)", expanded=False):
        s1, s2, s3 = st.columns(3)
        store, tax, default_split = finance_settings()
        # зберігаємо в окремі (не віджетні) ключі, щоб значення жили і на інших сторінках
        st.session_state["fin_store"] = s1.slider("Комісія сторів (%):", 15, 35, store, step=1)
        st.session_state["fin_tax"] = s2.slider("Податки та резерви (%):", 0, 15, tax, step=1)
        st.session_state["fin_split"] = s3.slider("Спліт девелопера за замовчуванням (%):", 0, 100, default_split, step=5,
                                                  help="Використовується, якщо в каталозі немає колонки Revenue Split для гри")
    store, tax, default_split = finance_settings()
    net_pct = (100 - store - tax) / 100.0

    rows = []
    for _, r in filtered_df.iterrows():
        gross = game_total(r)
        salary = clean_num_val(r.get(COL["porting"])) if COL["porting"] else 0.0
        split = clean_num_val(r.get(COL["split"])) if COL["split"] else 0.0
        split = split if split > 0 else default_split
        recoup = clean_num_val(r.get(COL["recoup"])) if COL["recoup"] else 0.0

        net = gross * net_pct
        if recoup > 0:
            recouped, distrib = min(net, recoup), max(0.0, net - recoup)
            royalty = distrib * split / 100
            margin = recouped + distrib * (1 - split / 100)
        else:
            royalty = net * split / 100
            margin = net * (1 - split / 100)
        rows.append({
            "Гра": r["Game_Name_Clean"], "Gross ($)": round(gross, 2), "Net у банку ($)": round(net, 2),
            "Зарплата розробника ($)": round(salary, 2), "Роялті автору ($)": round(royalty, 2),
            "🔥 Чистий прибуток студії ($)": round(margin - salary, 2),
            "ROI": round(margin / salary, 1) if salary > 0 else None,
        })
    pnl = pd.DataFrame(rows)
    if pnl.empty:
        st.info("Немає ігор у вибірці.")
        return
    p = st.columns(3)
    p[0].metric(f"Net у банку ({net_pct * 100:.0f}%)", fmt_usd(pnl["Net у банку ($)"].sum(), True))
    p[1].metric("Виплати роялті авторам", fmt_usd(pnl["Роялті автору ($)"].sum(), True))
    p[2].metric("🔥 Чистий прибуток Upscale Studio", fmt_usd(pnl["🔥 Чистий прибуток студії ($)"].sum(), True),
                f"Зарплати: {fmt_usd(pnl['Зарплата розробника ($)'].sum())}", delta_color="off")
    st.dataframe(pnl.sort_values("Gross ($)", ascending=False), hide_index=True, use_container_width=True, height=400,
                 column_config={"ROI": st.column_config.NumberColumn(format="%.1fx")})


def render_table_report(total_gross, plat_rev):
    st.subheader("📑 Повна фінансова таблиця портфоліо")
    cfg = {COL["cover"]: st.column_config.ImageColumn("Обкладинка", width="small")} if COL["cover"] else {}
    st.dataframe(filtered_df, column_config=cfg, use_container_width=True, height=420)
    csv_button(filtered_df, "📥 Експортувати дані (.CSV)", "console_sales_portfolio.csv")

    st.markdown("---")
    st.subheader("📄 One-Pager Executive звіт")
    cards = [("TOTAL CONSOLE GROSS", total_gross, "#38bdf8"), ("PLAYSTATION", plat_rev["PS"], "#60a5fa"),
             ("NINTENDO SWITCH", plat_rev["Switch"], "#f87171"), ("XBOX", plat_rev["Xbox"], "#4ade80")]
    cards_html = "".join(f'<div class="card"><div>{t}</div><div class="val" style="color:{c};">${v:,.0f}</div></div>' for t, v, c in cards)
    report = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Upscale Studio Executive Report</title>
<style>
body {{ background:#0f172a; color:#f8fafc; font-family:-apple-system, sans-serif; padding:30px; }}
.card {{ background:#1e293b; border:1px solid #334155; border-radius:10px; padding:16px; text-align:center; }}
.grid {{ display:grid; grid-template-columns:repeat(4, 1fr); gap:15px; margin:20px 0; }}
.title {{ font-size:24px; font-weight:bold; }} .val {{ font-size:26px; font-weight:800; margin-top:6px; }}
</style></head><body>
<div style="display:flex; justify-content:space-between; border-bottom:1px solid #334155; padding-bottom:15px;">
<div><div class="title">UPSCALE STUDIO</div><div>Console Operations Executive Report</div></div>
<div><b>Date:</b> {datetime.now().strftime('%B %Y')}</div></div>
<div class="grid">{cards_html}</div></body></html>"""
    st.download_button("📥 Завантажити One-Pager (.HTML / PDF)", data=report,
                       file_name=f"Upscale_Studio_Executive_Report_{datetime.now().strftime('%Y_%m')}.html", mime="text/html")

# ==============================================================================
# 💰 РОЗДІЛ 2: ПРОДАЖІ ТА ЦІЛІ (Тижні + Цілі + Воронка + Помісячно)
# ==============================================================================
def render_sales():
    st.title("💰 Продажі та цілі")
    st.caption("Тижнева звітність, виконання плану 2026, BizDev воронка та помісячні звіти сторів — з одним фільтром періоду")

    n_matrix, n_months = parse_nintendo_monthly_data(load_sheet(NINTENDO_MONTHLY_SHEET_URL))
    x_matrix, x_months = parse_xbox_monthly_data(load_sheet(XBOX_MONTHLY_SHEET_URL))
    c_matrix, c_months = combine_monthly_matrices(n_matrix, x_matrix, n_months, x_months)

    all_dates = (list(weekly_df["Parsed_Date"]) if not weekly_df.empty else []) + [month_label_to_date(m) for m in c_months]
    if not all_dates:
        st.warning("⚠️ Немає ні тижневих, ні помісячних даних. Перевір `WEEKLY_SHEET_URL` та посилання на звіти сторів.")
        return

    c_sel, c_info = st.columns([1.2, 3])
    with c_sel:
        sel = period_picker(all_dates, key="sales_period", extras=("Останній тиждень",) if not weekly_df.empty else ())

    if sel == "Останній тиждень":
        wk = weekly_df.tail(1)
        start = end = wk["Parsed_Date"].iloc[0].date()
    else:
        start, end = period_bounds(sel)
        wk = weekly_df[weekly_df["Parsed_Date"].apply(lambda d: in_bounds(d, start, end))] if not weekly_df.empty else weekly_df
    c_info.caption(f"Тижневих звітів у періоді: **{len(wk)}**" + (f" • {start.strftime('%d.%m.%Y')} — {end.strftime('%d.%m.%Y')}" if start else ""))

    # ---- KPI + WoW останнього тижня періоду ----
    if not wk.empty:
        last = wk.iloc[-1]
        pos = weekly_df.index[weekly_df["Parsed_Date"] == last["Parsed_Date"]][0]
        prev_rev = weekly_df.loc[pos - 1, "Total_Revenue"] if pos > 0 else None
        wow = safe_pct(last["Total_Revenue"] - prev_rev, prev_rev) if prev_rev else None
        k = st.columns(4)
        k[0].metric("Виторг за період", fmt_usd(wk["Total_Revenue"].sum(), True),
                    f"{wow:+.1f}% WoW (тиждень {last['Week']})" if wow is not None else None)
        for i, p in enumerate(["PS", "Switch", "Xbox"], start=1):
            k[i].metric(f"{PLATFORM_LABEL[p]}", fmt_usd(wk[f"{WEEKLY_PREFIX[p]}_Revenue"].sum(), True))

    st.markdown("<br>", unsafe_allow_html=True)
    t_week, t_goals, t_funnel, t_month, t_social, t_table = st.tabs([
        "📈 Тижнева динаміка", "🎯 Цілі 2026", "🤝 BizDev воронка", "🗓️ Помісячно (звіти сторів)", "📱 Соцмережі", "📑 Таблиця",
    ])

    with t_week:
        if wk.empty:
            st.info("Немає тижневих даних за обраний період.")
        else:
            long_rev = wk.melt(id_vars="Week", value_vars=[f"{WEEKLY_PREFIX[p]}_Revenue" for p in PLATFORMS], var_name="Platform", value_name="Revenue")
            long_rev["Platform"] = long_rev["Platform"].map({f"{WEEKLY_PREFIX[p]}_Revenue": PLATFORM_LABEL[p] for p in PLATFORMS})
            st.subheader("Виторг по тижнях ($)")
            show_fig(px.bar(long_rev, x="Week", y="Revenue", color="Platform", color_discrete_map=PLATFORM_COLORS), yaxis_title="Виторг ($)", xaxis_title="")

            long_sales = wk.melt(id_vars="Week", value_vars=[f"{WEEKLY_PREFIX[p]}_Sales" for p in PLATFORMS], var_name="Platform", value_name="Sales")
            long_sales["Platform"] = long_sales["Platform"].map({f"{WEEKLY_PREFIX[p]}_Sales": PLATFORM_LABEL[p] for p in PLATFORMS})
            st.subheader("Продажі в копіях (Units Sold)")
            show_fig(px.line(long_sales, x="Week", y="Sales", color="Platform", markers=True, color_discrete_map=PLATFORM_COLORS),
                     yaxis_title="Копій (шт)", xaxis_title="")

    with t_goals:
        render_goals(sel, start, end)

    with t_funnel:
        render_funnel(wk)

    with t_month:
        render_monthly(start, end, {"🔴 Nintendo eShop": (n_matrix, n_months, "#e60012"),
                                    "🟢 Xbox Store": (x_matrix, x_months, "#107c10"),
                                    "🌐 Всі консолі (Switch + Xbox)": (c_matrix, c_months, "#d946ef")})

    with t_social:
        cols = [c for c in SOCIAL_COLS if c in wk.columns]
        if wk.empty or not cols:
            st.info("Немає даних соцмереж за обраний період.")
        else:
            st.subheader("📱 Ріст аудиторії та соцмереж")
            show_fig(px.line(wk, x="Week", y=cols, markers=True), height=380, xaxis_title="", yaxis_title="")

    with t_table:
        if wk.empty:
            st.info("Немає тижневих даних за обраний період.")
        else:
            st.dataframe(wk.drop(columns=["Parsed_Date"]), use_container_width=True, height=450, hide_index=True)
            csv_button(wk.drop(columns=["Parsed_Date"]), "📥 Експортувати тижневий звіт (.CSV)", "upscale_weekly_reporting.csv")


def render_goals(sel, start, end):
    if weekly_df.empty:
        st.info("Немає тижневих даних — факт для цілей береться з тижневого листа.")
        return
    target_key = sel if sel in TARGETS_2026 else None
    if target_key is None:
        st.info("🎯 Цілі задані для 2026 року та його кварталів. Обери у фільтрі періоду «2026 (рік)» або «Q1–Q4 2026». Нижче — зведення по кварталах.")
    else:
        target = TARGETS_2026[target_key]
        fact = weekly_df[weekly_df["Parsed_Date"].apply(lambda d: in_bounds(d, start, end))]
        f_rev = float(fact["Total_Revenue"].sum())
        rev_pct = safe_pct(f_rev, target["Revenue"]) or 0.0
        # скільки часу періоду вже минуло — щоб бачити, чи йдемо за графіком
        elapsed = min(1.0, max(0.0, ((TODAY - start).days + 1) / ((end - start).days + 1)))
        pace_target = target["Revenue"] * elapsed
        pace_pct = safe_pct(f_rev, pace_target) if pace_target else None
        color = "#10b981" if rev_pct >= 80 or (pace_pct or 0) >= 95 else ("#f59e0b" if (pace_pct or 0) >= 70 else "#ef4444")

        st.markdown(f"""
        <div style="background:#171724; border:1px solid #2f2f45; border-radius:12px; padding:22px; margin:10px 0 15px 0;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
            <div>
              <span style="font-size:12px; font-weight:600; color:#94a3b8; text-transform:uppercase;">Фінансовий таргет • {target_key}</span>
              <h2 style="margin:2px 0 0 0; color:#fff;">💰 Виручка: ${f_rev:,.0f} <span style="font-size:18px; color:#94a3b8; font-weight:normal;">/ ${target['Revenue']:,.0f}</span></h2>
              <p style="margin:4px 0 0 0; font-size:12px; color:#94a3b8;">Минуло {elapsed * 100:.0f}% періоду • очікувано на сьогодні: ${pace_target:,.0f}
              {f"• темп: <b style='color:{color};'>{pace_pct:.0f}% від графіка</b>" if pace_pct is not None else ""}</p>
            </div>
            <div style="text-align:right;">
              <span style="font-size:28px; font-weight:800; color:{color};">{rev_pct:.1f}%</span>
              <p style="margin:0; font-size:12px; color:#94a3b8;">виконання плану</p>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
        st.progress(min(rev_pct / 100.0, 1.0))

        st.subheader("🎮 План виручки за платформами")
        k = st.columns(3)
        plat_rows = []
        for i, p in enumerate(PLATFORMS):
            f_v = float(fact[f"{WEEKLY_PREFIX[p]}_Revenue"].sum())
            t_v = target[f"{WEEKLY_PREFIX[p]}_Revenue"]
            k[i].metric(PLATFORM_LABEL[p], fmt_usd(f_v), f"{safe_pct(f_v, t_v):.1f}% від цілі ({fmt_usd(t_v)})", delta_color="off")
            plat_rows += [{"Платформа": PLATFORM_LABEL[p], "Тип": "Факт", "$": f_v}, {"Платформа": PLATFORM_LABEL[p], "Тип": "План", "$": t_v}]
        show_fig(px.bar(pd.DataFrame(plat_rows), x="Платформа", y="$", color="Тип", barmode="group",
                        color_discrete_map={"Факт": "#10b981", "План": "#d946ef"}), height=340, xaxis_title="", yaxis_title="$")

        st.subheader("🤝 BizDev: план vs факт")
        b = st.columns(4)
        for i, (col, lbl) in enumerate([("Deals", "🤝 Deals"), ("Calls", "📞 Calls"), ("Contacts", "✉️ Contacts"), ("Leads", "🔍 Leads")]):
            f_v = int(fact[col].sum()) if col in fact.columns else 0
            b[i].metric(lbl, f"{f_v} / {target[col]}", f"{safe_pct(f_v, target[col]):.0f}%", delta_color="off")

    st.markdown("---")
    st.subheader("📋 Зведення по кварталах 2026")
    rows = []
    for q in ["Q1 2026", "Q2 2026", "Q3 2026", "Q4 2026"]:
        qs, qe = period_bounds(q)
        qf = weekly_df[weekly_df["Parsed_Date"].apply(lambda d: in_bounds(d, qs, qe))]
        f_rev = float(qf["Total_Revenue"].sum())
        rows.append({"Квартал": q, "Факт ($)": f_rev, "План ($)": TARGETS_2026[q]["Revenue"],
                     "Виконання (%)": safe_pct(f_rev, TARGETS_2026[q]["Revenue"]),
                     "Угоди": f"{int(qf['Deals'].sum()) if 'Deals' in qf.columns else 0}/{TARGETS_2026[q]['Deals']}"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, column_config={
        "Факт ($)": st.column_config.NumberColumn(format="$%.0f"), "План ($)": st.column_config.NumberColumn(format="$%.0f"),
        "Виконання (%)": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
    })


def render_funnel(wk):
    st.subheader("🎯 Воронка залучення проєктів (Leads ➔ Deals)")
    present = [s for s in FUNNEL_STAGES if s[0] in wk.columns]
    if wk.empty or not present:
        st.info("Немає даних воронки за обраний період.")
        return
    totals = {s[0]: float(wk[s[0]].sum()) for s in present}
    cols = st.columns(len(present))
    prev = None
    for i, (key, lbl, _) in enumerate(present):
        conv = safe_pct(totals[key], totals[prev]) if prev else None
        cols[i].metric(lbl, f"{int(totals[key]):,}", f"{conv:.1f}% від попер." if conv is not None else None, delta_color="off")
        prev = key
    st.caption("Конверсія рахується лише з реальних даних; якщо на попередньому етапі 0 — показується без %.")

    fig = go.Figure(go.Funnel(
        y=[f"{lbl} ({desc})" for _, lbl, desc in present], x=[totals[k] for k, _, _ in present],
        textinfo="value+percent initial+percent previous",
        marker=dict(color=["#6366f1", "#8b5cf6", "#a855f7", "#d946ef", "#f59e0b", "#10b981"][:len(present)]),
        connector={"line": {"color": "#475569", "width": 1.5}},
    ))
    show_fig(fig, height=380)

    st.subheader("📊 Тижнева динаміка воронки")
    show_fig(px.bar(wk, x="Week", y=[k for k, _, _ in present], barmode="group",
                    color_discrete_sequence=["#6366f1", "#8b5cf6", "#a855f7", "#d946ef", "#f59e0b", "#10b981"]),
             height=380, xaxis_title="", yaxis_title="")


def render_monthly(start, end, sources):
    plat_choice = st.radio("Платформа:", list(sources.keys()), horizontal=True, key="monthly_platform")
    matrix, months, accent = sources[plat_choice]
    if matrix.empty or not months:
        st.info("Немає даних помісячного звіту для цієї платформи. Перевір посилання на звіт у налаштуваннях.")
        return

    sel_months = [m for m in months if in_bounds(month_label_to_date(m), start, end)]
    if not sel_months:
        st.info(f"У звіті немає місяців за обраний період. Доступні місяці: {months[0]} — {months[-1]}.")
        return
    period_lbl = sel_months[0] if len(sel_months) == 1 else f"{sel_months[0]} ➔ {sel_months[-1]}"

    view = matrix[["Назва гри / DLC"] + sel_months].copy()
    view["Виторг за період ($)"] = view[sel_months].sum(axis=1)
    view["All-Time ($)"] = matrix["Всього ($)"]
    view = view[view["Виторг за період ($)"] > 0].sort_values("Виторг за період ($)", ascending=False).reset_index(drop=True)
    total = float(view["Виторг за період ($)"].sum())
    view["Частка (%)"] = view["Виторг за період ($)"] / total * 100 if total else 0.0

    k = st.columns(4)
    kpi_card(k[0], f"Виторг ({period_lbl})", fmt_usd(total, True), f"{len(sel_months)} міс.")
    kpi_card(k[1], "Активних тайтлів", len(view), "З продажами", "badge-ps")
    kpi_card(k[2], "Лідер періоду", view.iloc[0]["Назва гри / DLC"] if not view.empty else "—",
             fmt_usd(view.iloc[0]["Виторг за період ($)"], True) if not view.empty else "", "badge-xbox", "#38bdf8")
    kpi_card(k[3], "Каса платформи All-Time", fmt_usd(matrix["Всього ($)"].sum(), True), "Повна база", "badge-switch")

    if not view.empty:
        st.subheader(f"🏆 Топ-10 за період ({period_lbl})")
        fig = px.bar(view.head(10), x="Виторг за період ($)", y="Назва гри / DLC", orientation="h", text="Виторг за період ($)",
                     color_discrete_sequence=[accent])
        fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside", cliponaxis=False)
        show_fig(fig, height=380, yaxis=dict(autorange="reversed", title=""))

    money = {c: st.column_config.NumberColumn(c, format="$%.2f") for c in sel_months + ["Виторг за період ($)", "All-Time ($)"]}
    money["Частка (%)"] = st.column_config.NumberColumn(format="%.1f%%")
    st.dataframe(view, column_config=money, use_container_width=True, height=400, hide_index=True)
    slug = "nintendo" if "Nintendo" in plat_choice else "xbox" if "Xbox" in plat_choice else "all"
    csv_button(view, "📥 Звіт за період (.CSV)", f"{slug}_revenue_{period_lbl.replace(' ➔ ', '_')}.csv")

    heat_months = sel_months if len(sel_months) >= 2 else months
    st.subheader("🔥 Теплова карта виторгу (топ-20)")
    heat = matrix.set_index("Назва гри / DLC")[heat_months]
    heat = heat.loc[heat.sum(axis=1).sort_values(ascending=False).index[:20]]
    show_fig(px.imshow(heat, labels=dict(x="Місяць", y="", color="$"), color_continuous_scale="Purples", aspect="auto"), height=480)

    st.subheader("📈 Тренд окремої гри")
    game = st.selectbox("Гра:", matrix["Назва гри / DLC"].tolist(), key="monthly_trend_game")
    row = matrix[matrix["Назва гри / DLC"] == game].iloc[0]
    trend = pd.DataFrame({"Місяць": months, "Виторг ($)": [row[m] for m in months]})
    fig = px.bar(trend, x="Місяць", y="Виторг ($)", text="Виторг ($)", color_discrete_sequence=[accent])
    fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside", cliponaxis=False)
    show_fig(fig, height=350, xaxis_title="")

    with st.expander("📑 Повна помісячна матриця за всі місяці"):
        st.dataframe(matrix, use_container_width=True, height=420, hide_index=True,
                     column_config={c: st.column_config.NumberColumn(c, format="$%.2f") for c in months + ["Всього ($)"]})
        csv_button(matrix, "📥 Повна матриця (.CSV)", f"{slug}_monthly_usd_matrix.csv", key="full_matrix_csv")

# ==============================================================================
# 📅 РОЗДІЛ 3: КАЛЕНДАР І СЕЙЛИ
# ==============================================================================
EVENT_STYLE = {
    "release": ("pill-release", "#a855f7"), "nintendo": ("pill-nintendo", "#e60012"),
    "xbox": ("pill-xbox", "#107c10"), "deadline": ("pill-deadline", "#f59e0b"),
}


def build_calendar_events():
    """Кожна подія має start/end — сейл зберігається одним записом, а не окремо на кожен день."""
    events, seen = [], set()
    for _, r in raw_df.iterrows():
        d = game_release(r)
        if d:
            name = r["Game_Name_Clean"]
            seen.add((name.lower(), d))
            events.append({"start": d, "end": d, "type": "release", "title": f"🎮 Реліз: {name}", "desc": f"Вихід гри {name} на консолях"})
    if not pipe_df.empty:
        for _, pr in pipe_df.iterrows():
            d = to_date(pr["_d_release"])
            if d and (pr["Гра"].lower(), d) not in seen:
                events.append({"start": d, "end": d, "type": "release", "title": f"🚀 Реліз NSW: {pr['Гра']}",
                               "desc": f"Плановий вихід порту (розробник: {pr['Розробник']})"})
    for s in NINTENDO_SCHEDULE:
        a, b = sale_dates(s)
        events.append({"start": a, "end": b, "type": "nintendo", "title": f"🔴 NSW: {s['name']}", "desc": f"Розпродаж Nintendo eShop ({s['region']})"})
    for s in XBOX_SCHEDULE:
        a, b = sale_dates(s)
        events.append({"start": a, "end": b, "type": "xbox", "title": f"🟢 XB: {s['name']}", "desc": f"Xbox Sale: {s['note']}"})
        dl = datetime.strptime(s["deadline"], "%Y-%m-%d").date()
        events.append({"start": dl, "end": dl, "type": "deadline", "title": f"⏰ ДЕДЛАЙН: {s['name']}",
                       "desc": f"Крайній строк подачі в Microsoft. {s['note']}"})
    return events


def render_calendar_section():
    st.title("📅 Календар релізів і розпродажів")
    st.caption("Релізи портфоліо й пайплайну, сейли Nintendo/Xbox і дедлайни подачі — плюс інструменти підготовки сейлів")
    t_cal, t_ns, t_xb = st.tabs(["📅 Календар", "🔴 Сейл Nintendo (bookmarklet)", "🟢 Сейл Xbox (подача)"])
    with t_cal:
        render_calendar(build_calendar_events())
    with t_ns:
        render_nintendo_sale()
    with t_xb:
        render_xbox_sale()


def render_calendar(events):
    # Місяці генеруються від реальних подій (± поточний місяць), а не жорстким списком
    first = min([e["start"] for e in events] + [TODAY]).replace(day=1)
    last = max([e["end"] for e in events] + [TODAY]).replace(day=1)
    months = []
    cur = first
    while cur <= last:
        months.append(cur)
        cur = date(cur.year + (cur.month == 12), cur.month % 12 + 1, 1)
    cur_m = TODAY.replace(day=1)

    c1, c2, c3 = st.columns([1.5, 1.7, 2])
    sel_m = c1.selectbox("🗓️ Місяць:", months, index=months.index(cur_m), format_func=month_label, key="cal_month")
    flt = c2.radio("Фільтр:", ["Всі події", "🎮 Релізи", "🏷️ Сейли й дедлайни"], horizontal=True, key="cal_filter")
    view = c3.radio("Вигляд:", ["📅 Місяць", "📋 Список (Agenda)"], horizontal=True, key="cal_view")

    if flt == "🎮 Релізи":
        events = [e for e in events if e["type"] == "release"]
    elif flt == "🏷️ Сейли й дедлайни":
        events = [e for e in events if e["type"] != "release"]

    m_start = sel_m
    m_end = date(sel_m.year, sel_m.month, calendar.monthrange(sel_m.year, sel_m.month)[1])

    if view == "📅 Місяць":
        legend = "".join(f'<span><span style="color:{c};">●</span> {t}</span>' for t, c in
                         [("Релізи", "#a855f7"), ("Nintendo сейли", "#ff4d4f"), ("Xbox сейли", "#52c41a"), ("Дедлайни подачі", "#faad14")])
        parts = ['<div class="cal-container">',
                 f'<div style="padding:14px 20px; background:#1a1a27; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #28283c;">'
                 f'<h3 style="margin:0; color:#fff; font-size:18px; font-weight:800;">{month_label(sel_m)}</h3>'
                 f'<div style="font-size:12px; color:#94a3b8; display:flex; gap:14px;">{legend}</div></div>',
                 '<div class="cal-header">' + "".join(
                     '<div class="cal-header-cell"' + (' style="color:#ff6b6b;"' if i >= 5 else "") + f">{d}</div>"
                     for i, d in enumerate(["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"])) + "</div>",
                 '<div class="cal-grid">']
        for week in calendar.Calendar(firstweekday=0).monthdatescalendar(sel_m.year, sel_m.month):
            for day in week:
                classes = "cal-day-cell" + (" other-month" if day.month != sel_m.month else "") + (" today" if day == TODAY else "")
                day_ev = [e for e in events if e["start"] <= day <= e["end"]]
                pills = []
                for e in day_ev[:3]:
                    mark = " (Старт 🔥)" if e["start"] == day and e["end"] != day else (" (Фініш 🏁)" if e["end"] == day and e["start"] != day else "")
                    pills.append(f'<div class="cal-event-pill {EVENT_STYLE[e["type"]][0]}" title="{e["desc"]}">{e["title"]}{mark}</div>')
                if len(day_ev) > 3:
                    pills.append(f'<div style="font-size:9.5px; color:#94a3b8; font-weight:bold; margin-top:2px;">+ ще {len(day_ev) - 3}</div>')
                parts.append(f'<div class="{classes}"><div class="cal-day-num">{day.day}</div>{"".join(pills)}</div>')
        parts.append("</div></div>")
        st.markdown("".join(parts), unsafe_allow_html=True)
    else:
        agenda = sorted([e for e in events if e["start"] <= m_end and e["end"] >= m_start], key=lambda e: e["start"])
        if not agenda:
            st.info("💡 У цьому місяці немає подій.")
        for e in agenda:
            diff = (e["start"] - TODAY).days
            if e["start"] <= TODAY <= e["end"]:
                countdown, cd_color = ("🔥 СЬОГОДНІ" if e["start"] == e["end"] else "🔥 Йде зараз"), "#34d399"
            elif diff > 0:
                countdown, cd_color = f"⏳ Через {diff} дн.", "#34d399"
            else:
                countdown, cd_color = f"Минуло {(TODAY - e['end']).days} дн. тому", "#64748b"
            dates = e["start"].strftime("%d.%m.%Y") if e["start"] == e["end"] else f"{e['start'].strftime('%d.%m')} – {e['end'].strftime('%d.%m.%Y')}"
            st.markdown(
                f'<div style="background:#171724; border:1px solid #28283c; border-left:5px solid {EVENT_STYLE[e["type"]][1]}; border-radius:8px; '
                f'padding:12px 16px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">'
                f'<div><b style="color:#fff; font-size:15px;">{e["title"]}</b><p style="margin:2px 0 0 0; font-size:12px; color:#94a3b8;">{e["desc"]}</p></div>'
                f'<div style="text-align:right;"><span style="font-size:14px; font-weight:700; color:#fff;">{dates}</span><br>'
                f'<span style="font-size:11px; font-weight:bold; color:{cd_color};">{countdown}</span></div></div>',
                unsafe_allow_html=True,
            )


def sales_timeline(schedule, color_key=None, color_map=None, height=240):
    df = pd.DataFrame([{"Сейл": s["name"], "Початок": s["start"], "Кінець": s["end"], "Статус": sale_status(s),
                        "Тип": s.get("type", "")} for s in schedule])
    fig = px.timeline(df, x_start="Початок", x_end="Кінець", y="Сейл", color=color_key or "Статус", color_discrete_map=color_map)
    fig.update_yaxes(autorange="reversed", title="")
    fig.add_vline(x=datetime.combine(TODAY, datetime.min.time()).timestamp() * 1000, line_dash="dash", line_color="#fbbf24",
                  annotation_text="сьогодні", annotation_font_color="#fbbf24")
    show_fig(fig, height=height)


BOOKMARKLET_TEMPLATE = """javascript:(function(){{
const discounts = {json_str};
function parsePrice(text){{let s=text.trim().replace(/[^0-9.,]/g,'');if(!s)return null;if(s.includes('.')&&s.includes(',')){{if(s.indexOf('.')<s.indexOf(',')){{s=s.replace(/\\./g,'').replace(',','.')}}else{{s=s.replace(/,/g,'')}}}}else if(s.includes(',')){{s=s.replace(',','.')}}return parseFloat(s);}}
function getGameTitle(el){{let current=el;while(current&&current!==document.body){{let prev=current.previousElementSibling;while(prev){{let text=prev.innerText||"";if(text.includes('HAC-')&&text.includes(':')){{let rawTitle=text.substring(text.indexOf(':')+1).trim();rawTitle=rawTitle.replace(/\\s*\\(\\d+\\/\\d+\\)\\s*$/, '').trim();return rawTitle;}}prev=prev.previousElementSibling;}}current=current.parentElement;}}return null;}}
const sortedKeys=Object.keys(discounts).sort((a,b)=>b.length-a.length);
const inputs=Array.from(document.querySelectorAll('input[type="text"]')).filter(inp=>{{const td=inp.closest('td');if(!td)return false;const prevTd=td.previousElementSibling;return prevTd&&/[\\d]/.test(prevTd.innerText);}});
let updatedCount=0;
inputs.forEach(priceInput=>{{const td=priceInput.closest('td');const regularPriceTd=td.previousElementSibling;if(!regularPriceTd)return;let regularPrice=parsePrice(regularPriceTd.innerText);if(regularPrice===null||isNaN(regularPrice)||regularPrice<=0)return;let gameTitle=getGameTitle(priceInput)||"Default";let cleanTitle=gameTitle.toLowerCase().replace(/\\s+/g,' ').trim();let discountPercent=70;let matched=false;for(let k of sortedKeys){{if(cleanTitle===k){{discountPercent=discounts[k];matched=true;break;}}}}if(!matched){{for(let k of sortedKeys){{if(cleanTitle.includes(k)||k.includes(cleanTitle)){{discountPercent=discounts[k];break;}}}}}}let discountedVal=regularPrice*(1-(discountPercent/100));let finalPriceStr="";if(regularPriceTd.innerText.includes(',')||regularPriceTd.innerText.includes('.')){{finalPriceStr=(Math.floor(discountedVal*100)/100).toFixed(2);}}else{{finalPriceStr=Math.floor(discountedVal).toString();}}priceInput.value=finalPriceStr;priceInput.dispatchEvent(new Event('input',{{bubbles:true}}));priceInput.dispatchEvent(new Event('change',{{bubbles:true}}));const row=priceInput.closest('tr');if(row){{const checkbox=row.querySelector('input[type="checkbox"]');if(checkbox&&!checkbox.checked){{checkbox.click();}}}}updatedCount++;}});
alert("🎉 Заповнено цін для обраних ігор: "+updatedCount);
}})();"""


def sheet_discount(r, minimum=0):
    v = clean_num_val(r.get(COL["discount"])) if COL["discount"] else 0.0
    v = int(round(v)) if v > 0 else 70
    return max(v, minimum)


def render_nintendo_sale():
    st.subheader("🔴 Підготовка розпродажу Nintendo eShop")
    sales_timeline(NINTENDO_SCHEDULE)

    idx = default_sale_index(NINTENDO_SCHEDULE, key_date="end")
    names = [f"{s['name']} — {sale_status(s)}" for s in NINTENDO_SCHEDULE]
    choice = st.selectbox("Сейл:", range(len(names)), index=idx, format_func=lambda i: names[i], key="ns_sale")
    sale_start = sale_dates(NINTENDO_SCHEDULE[choice])[0]

    rows = []
    for _, r in raw_df.iterrows():
        rel = game_release(r)
        if rel is None:
            ready, status = False, "⚪ Немає дати релізу"
        elif rel > sale_start:
            ready, status = False, "⏳ Вийде після старту сейлу"
        else:
            since = (sale_start - rel).days
            ready = since >= NINTENDO_COOLDOWN_DAYS
            status = "🟢 Готова" if ready else f"🟡 Кулдаун (ще {NINTENDO_COOLDOWN_DAYS - since} дн.)"
        rows.append({"Включити": ready, "Гра": r["Game_Name_Clean"], "Знижка (%)": sheet_discount(r),
                     "Дата релізу": rel.strftime("%d.%m.%Y") if rel else "—", "Статус": status})

    edited = st.data_editor(
        pd.DataFrame(rows), hide_index=True, use_container_width=True, height=360, key="ns_editor",
        column_config={"Включити": st.column_config.CheckboxColumn("Включити в сейл"),
                       "Знижка (%)": st.column_config.NumberColumn(min_value=10, max_value=90, step=5)},
        disabled=["Гра", "Дата релізу", "Статус"],
    )
    picked = edited[edited["Включити"]]
    st.caption(f"Обрано ігор: **{len(picked)}**")

    if st.button("⚡ Згенерувати Bookmarklet для Nintendo", use_container_width=True):
        if picked.empty:
            st.warning("Оберіть хоча б одну гру галочкою!")
        else:
            payload = {row["Гра"].strip().lower(): int(row["Знижка (%)"]) for _, row in picked.iterrows()}
            code = BOOKMARKLET_TEMPLATE.format(json_str=json.dumps(payload, ensure_ascii=False))
            st.success(f"🎉 Bookmarklet згенеровано для {len(picked)} ігор!")
            b1, b2 = st.columns(2)
            with b1:
                st.markdown("##### 📌 Код закладки:")
                st.code(code, language="javascript")
            with b2:
                st.markdown("##### 📋 Список назв:")
                st.text_area("Назви ігор:", "\n".join(picked["Гра"].str.strip()), height=160)


def render_xbox_sale():
    st.subheader("🟢 Подача на розпродажі Xbox")
    sales_timeline(XBOX_SCHEDULE, color_key="Тип", color_map={"ID Sale (Глибокі знижки)": "#10b981", "Tentpole Sale": "#d946ef"}, height=220)

    idx = default_sale_index(XBOX_SCHEDULE, key_date="deadline")
    names = [f"{s['name']} — дедлайн {s['deadline']} ({deadline_badge(s['deadline'])})" for s in XBOX_SCHEDULE]
    choice = st.selectbox("Сейл:", range(len(names)), index=idx, format_func=lambda i: names[i], key="xb_sale")
    sale = XBOX_SCHEDULE[choice]

    x = st.columns(4)
    x[0].metric("🎯 Розпродаж", sale["name"], sale_status(sale), delta_color="off")
    x[1].metric("⏰ Дедлайн подачі", sale["deadline"], deadline_badge(sale["deadline"]), delta_color="off")
    x[2].metric("🔒 Ліміт тайтлів", f"до {sale['limit']} ігор")
    x[3].metric("📩 Approval Feedback", sale["feedback"])
    st.info(f"💡 **Вимоги Microsoft:** {sale['note']}")

    rows = []
    for _, r in raw_df.iterrows():
        price = game_price(r) or 9.99
        disc = sheet_discount(r, minimum=sale["min_discount"])
        fails = [f"ціна ${price:.2f} < ${sale['min_price']}"] if sale["min_price"] and price < sale["min_price"] else []
        rows.append({"Подати": not fails, "Гра": r["Game_Name_Clean"], "Базова ціна ($)": price, "Знижка (%)": disc,
                     "Ціна на сейлі ($)": round(price * (1 - disc / 100), 2),
                     "Вимоги": "🟢 Проходить" if not fails else f"🔴 Не підходить ({', '.join(fails)})"})

    edited = st.data_editor(
        pd.DataFrame(rows), hide_index=True, use_container_width=True, height=360, key="xb_editor",
        column_config={"Подати": st.column_config.CheckboxColumn("Подати в Microsoft"),
                       "Знижка (%)": st.column_config.NumberColumn(min_value=sale["min_discount"], max_value=90, step=5),
                       "Базова ціна ($)": st.column_config.NumberColumn(format="$%.2f"),
                       "Ціна на сейлі ($)": st.column_config.NumberColumn(format="$%.2f")},
        disabled=["Гра", "Базова ціна ($)", "Ціна на сейлі ($)", "Вимоги"],
    )
    picked = edited[edited["Подати"]]
    if len(picked) > sale["limit"]:
        st.warning(f"⚠️ Обрано {len(picked)} ігор, а ліміт сейлу — {sale['limit']}. Зніми зайві галочки.")
    else:
        st.caption(f"Обрано {len(picked)} з {sale['limit']} можливих.")
    csv_button(picked.drop(columns=["Подати"]), "📥 Список для подачі (.CSV)", f"xbox_{sale['name'].replace(' ', '_')}.csv")

# ==============================================================================
# 🚀 РОЗДІЛ 4: РЕЛІЗИ (сертифікація + команда + roadmap + маркетинг)
# ==============================================================================
def build_activity_table():
    """Маркетинговий чек-лист. Без фолбеку на каталог — якщо листа немає, так і кажемо."""
    src = load_sheet(ACTIVITY_SHEET_URL)
    if src.empty:
        return pd.DataFrame()
    t_col = find_col(src.columns, "title", "гра", "game", "назва") or src.columns[0]
    d_col = find_col(src.columns, "release date", "release", "date", "дата")
    s_col = find_col(src.columns, "status", "статус")
    rows = []
    for _, r in src.iterrows():
        name = safe_str(r.get(t_col))
        if not name:
            continue
        rel = to_date(r.get(d_col)) if d_col else None
        raw_stat = safe_str(r.get(s_col)).lower() if s_col else ""
        done = sum(is_truthy(r.get(t)) for t in ACTIVITY_CHECKBOX_COLS)
        row = {"Гра": name, "Дата релізу": rel, "Статус": "🟢 Done" if ("released" in raw_stat or "done" in raw_stat) else "🟡 In Progress",
               "Готовність (%)": int(round(done / len(ACTIVITY_CHECKBOX_COLS) * 100))}
        row.update({t: is_truthy(r.get(t)) for t in ACTIVITY_CHECKBOX_COLS})
        rows.append(row)
    return pd.DataFrame(rows)


def render_releases():
    st.title("🚀 Релізи: сертифікація, команда та маркетинг")
    st.caption(f"Лист **'{CERTIFICATION_SHEET_NAME}'** + маркетинговий чек-лист • Контроль швидкості портування та готовності до релізу")

    act_df = build_activity_table()
    has_pipe = not pipe_df.empty
    if not has_pipe:
        st.warning(f"⚠️ Не вдалося завантажити лист **'{CERTIFICATION_SHEET_NAME}'**. Перевір назву листа в Google Таблиці.")

    if has_pipe:
        deltas = pd.to_numeric(pipe_df["_delta"], errors="coerce").dropna()
        on_time = float((deltas <= 0).mean() * 100) if not deltas.empty else 0.0
        k = st.columns(5)
        kpi_card(k[0], "Всього тайтлів", len(pipe_df), "Лист Certification")
        kpi_card(k[1], "Білдів завантажено", int((pipe_df["Етап"] == STAGE_DONE).sum()), "Готові до сабміту", "badge-xbox", "#4ade80")
        kpi_card(k[2], "Зараз у роботі", int(pipe_df["Етап"].isin([STAGE_WIP, STAGE_OVERDUE]).sum()), "Включно з простроченими", "badge-ps", "#38bdf8")
        kpi_card(k[3], "Зриви дедлайнів", int(pipe_df["Вердикт"].str.contains("Прострочено|Затримка").sum()), "Затримка / Прострочено", "badge-switch", "#ef4444")
        kpi_card(k[4], "Вчасність здачі", f"{on_time:.0f}%", "On-Time Rate", "badge-total", "#10b981" if on_time >= 70 else "#f59e0b")

        overdue = pipe_df[pipe_df["Етап"] == STAGE_OVERDUE]
        if not overdue.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander(f"🚨 Критичні зриви: {len(overdue)} білд(ів) прострочено й досі не завантажено", expanded=True):
                for _, cr in overdue.iterrows():
                    st.markdown(
                        f'<div class="alert-card-red"><b style="color:#fff; font-size:15px;">{cr["Гра"]} (Розробник: {cr["Розробник"]})</b> ➔ '
                        f'<span style="color:#fca5a5; font-weight:bold;">План фінішу був {cr["План здачі білда"]}</span>'
                        f'<p style="margin:3px 0 0 0; font-size:12px; color:#cbd5e1;">Старт: {cr["Дата старту"]} • Вердикт: {cr["Вердикт"]}</p></div>',
                        unsafe_allow_html=True,
                    )

    st.markdown("<br>", unsafe_allow_html=True)
    t_tracker, t_team, t_roadmap, t_marketing = st.tabs(["📋 Трекер і дедлайни", "👨‍💻 Команда: KPI", "📅 Roadmap", "📣 Маркетинг-готовність"])
    with t_tracker:
        render_cert_tracker(act_df) if has_pipe else st.info("Немає даних сертифікації.")
    with t_team:
        render_team_kpi() if has_pipe else st.info("Немає даних сертифікації.")
    with t_roadmap:
        render_roadmap() if has_pipe else st.info("Немає даних сертифікації.")
    with t_marketing:
        render_marketing(act_df)


def render_cert_tracker(act_df):
    all_devs = sorted(d for d in pipe_df["Розробник"].unique() if d != "Не призначено")
    c1, c2 = st.columns([1.5, 2.5])
    sel_dev = c1.selectbox("Розробник:", ["Всі розробники"] + all_devs + ["Не призначено"], key="pipe_dev")
    sel_stage = c2.radio("Етап:", ["Всі", "🟢 Завантажені", "⏳ В роботі", "🚨 Затримка / прострочка", "⚪ В черзі"], horizontal=True, key="pipe_stage")

    view = pipe_df.copy()
    if sel_dev != "Всі розробники":
        view = view[view["Розробник"] == sel_dev]
    stage_filters = {
        "🟢 Завантажені": view["Етап"] == STAGE_DONE,
        "⏳ В роботі": view["Етап"].isin([STAGE_WIP, STAGE_OVERDUE]),
        "🚨 Затримка / прострочка": view["Вердикт"].str.contains("Затримка|Прострочено"),
        "⚪ В черзі": view["Етап"] == STAGE_BACKLOG,
    }
    if sel_stage in stage_filters:
        view = view[stage_filters[sel_stage]]

    # Підтягуємо маркетингову готовність з чек-листа — сертифікація і маркетинг в одному рядку
    if not act_df.empty:
        ready_map = {n.lower(): v for n, v in zip(act_df["Гра"], act_df["Готовність (%)"])}
        view["Маркетинг (%)"] = view["Гра"].str.lower().map(ready_map)

    cols = ["Гра", "Розробник", "Вердикт", "Дата старту", "План здачі білда", "Дата завантаження білда",
            "Реліз Nintendo", "План (дн)", "Факт (дн)", "Відхилення (дн)"] + (["Маркетинг (%)"] if "Маркетинг (%)" in view.columns else [])
    st.dataframe(view[cols], hide_index=True, use_container_width=True, height=420, column_config={
        "Маркетинг (%)": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d%%"),
        "Відхилення (дн)": st.column_config.NumberColumn(format="%+d"),
    })
    csv_button(view[cols], "📥 Експортувати реєстр (.CSV)", "nintendo_certification_pipeline.csv")

    st.markdown("---")
    st.subheader("⏳ План vs Факт по здачі білдів")
    st.caption("Ті самі фільтри, що й у таблиці • Червоне = затримка, зелене = вчасно або раніше")
    dv = view[pd.to_numeric(view["_delta"], errors="coerce").notna()].copy()
    if dv.empty:
        st.info("Для обраного фільтра ще немає зданих білдів із планом і фактом.")
        return
    dv["_delta"] = dv["_delta"].astype(float)
    fig = px.bar(dv.sort_values("_delta", ascending=False), x="Гра", y="_delta", color="_delta", text="_delta",
                 color_continuous_scale=["#10b981", "#eab308", "#ef4444"], labels={"_delta": "Відхилення (днів)"}, hover_data={"Розробник": True})
    fig.update_traces(texttemplate="%{text:+.0f} дн", textposition="outside", cliponaxis=False)
    show_fig(fig, height=360, xaxis_title="")


def render_team_kpi():
    all_devs = sorted(d for d in pipe_df["Розробник"].unique() if d != "Не призначено")
    dated = pipe_df.assign(_pdate=pipe_df.apply(project_date, axis=1))
    c_p, _ = st.columns([1.2, 3])
    with c_p:
        sel = period_picker(dated["_pdate"], key="team_period")
    start, end = period_bounds(sel)
    period_df = dated if sel == "Весь період" else dated[dated["_pdate"].apply(lambda d: in_bounds(d, start, end))]
    st.caption(f"Проєкт потрапляє в період за датою плану здачі (або завантаження / старту) • У вибірці: **{len(period_df)}** ігор")

    kpi = build_dev_kpi(period_df, all_devs)
    active = kpi[kpi["Всього ігор"] > 0] if not kpi.empty else kpi
    if active.empty:
        st.info("За цей період немає проєктів із призначеним розробником.")
        return

    st.markdown(f"##### 📊 Завантаження команди ({sel})")
    fig = go.Figure()
    for col, name, color in [("Здано білдів", "Здано", "#10b981"), ("В роботі", "В роботі", "#38bdf8"),
                             ("Прострочено", "Прострочено", "#ef4444"), ("В черзі", "В черзі", "#64748b")]:
        fig.add_trace(go.Bar(x=active["Розробник"], y=active[col], name=name, marker_color=color))
    show_fig(fig, height=330, barmode="stack", yaxis=dict(dtick=1))

    st.markdown(f"##### 📋 KPI розробників ({sel})")
    st.dataframe(kpi, hide_index=True, use_container_width=True, column_config={
        "Сер. план (дн)": st.column_config.NumberColumn(format="%.1f"),
        "Сер. факт (дн)": st.column_config.NumberColumn(format="%.1f"),
        "Сер. відхилення (дн)": st.column_config.NumberColumn(format="%+.1f дн"),
        "% вчасно": st.column_config.NumberColumn(format="%d%%"),
        "KPI (0-100)": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
    })
    with st.expander("ℹ️ Як рахується KPI"):
        st.markdown("- **45 балів** — частка зданих білдів від усіх ігор розробника за період\n"
                    "- **35 балів** — % здач вчасно (якщо зданих ще немає — нейтральні 25)\n"
                    "- **+20** базових балів\n"
                    "- **−2** за кожен день середньої затримки, **−5** за кожну гру, прострочену зараз\n\n"
                    "🟢 ≥ 80 • 🟡 65–79 • 🔴 < 65")


def render_roadmap():
    st.subheader("📅 Графік зайнятості та план здачі ігор")
    st.caption("Жовта лінія — сьогодні • Повзунок унизу — масштабування")
    recs = []
    for _, r in pipe_df.iterrows():
        dev = r["Розробник"]
        d_s, d_p, d_u = r["_d_start"], r["_d_plan"], r["_d_upload"]
        if dev == "Не призначено" or (pd.isna(d_s) and pd.isna(d_p)):
            continue
        start_d = d_s if pd.notna(d_s) else d_p - timedelta(days=14)
        end_d = d_p if pd.notna(d_p) else d_s + timedelta(days=14)
        if start_d > end_d:
            start_d, end_d = end_d, start_d
        if pd.notna(d_u):
            status = "🟢 Здано вчасно" if pd.notna(d_p) and d_u.date() <= d_p.date() else "🔴 Здано з затримкою"
        elif pd.notna(d_s):
            status = "🚨 Прострочено" if pd.notna(d_p) and TODAY > d_p.date() else "🔵 В роботі"
        else:
            status = "🟣 Заплановано"
        recs.append({"Гра": r["Гра"], "Розробник": f"👨‍💻 {dev}", "Start": start_d, "End": end_d, "Статус": status,
                     "Старт": r["Дата старту"], "План": r["План здачі білда"], "Факт": r["Дата завантаження білда"],
                     "Тривалість": f"{(end_d - start_d).days} дн."})
    if not recs:
        st.info("Немає даних із датами для побудови графіка.")
        return
    fig = px.timeline(
        pd.DataFrame(recs), x_start="Start", x_end="End", y="Розробник", color="Статус", text="Гра",
        color_discrete_map={"🟢 Здано вчасно": "#10b981", "🔴 Здано з затримкою": "#ef4444", "🚨 Прострочено": "#f43f5e",
                            "🔵 В роботі": "#38bdf8", "🟣 Заплановано": "#a855f7"},
        hover_data={"Гра": True, "Статус": True, "Старт": True, "План": True, "Факт": True, "Тривалість": True,
                    "Start": False, "End": False, "Розробник": False},
    )
    fig.update_yaxes(autorange="reversed", showgrid=True, gridcolor="rgba(255,255,255,0.12)", tickfont=dict(size=14, color="#ffffff"), title="")
    fig.add_vline(x=datetime.combine(TODAY, datetime.min.time()).timestamp() * 1000, line_width=2.5, line_dash="dash", line_color="#fbbf24",
                  annotation_text=f"СЬОГОДНІ ({TODAY.strftime('%d.%m')})", annotation_position="top left",
                  annotation_font_color="#fbbf24", annotation_font_size=11)
    fig.update_traces(textposition="inside", insidetextanchor="middle", textfont=dict(color="#ffffff", size=11.5))
    show_fig(fig, height=580, xaxis=dict(type="date", range=[TODAY - timedelta(days=10), TODAY + timedelta(days=100)],
                                         rangeslider=dict(visible=True, thickness=0.07, bgcolor="#161622", bordercolor="#28283c")))


def render_marketing(act_df):
    st.subheader("📣 Маркетингова готовність до релізів")
    if act_df.empty:
        st.warning("⚠️ Не вдалося завантажити маркетинговий чек-лист. Перевір `ACTIVITY_SHEET_URL`.")
        return

    k = st.columns(4)
    kpi_card(k[0], "🎮 Ігор у трекері", len(act_df))
    kpi_card(k[1], "🛠️ В роботі", int(act_df["Статус"].str.contains("Progress").sum()), "Підготовка", "badge-switch", "#f59e0b")
    kpi_card(k[2], "🟢 Випущено", int(act_df["Статус"].str.contains("Done").sum()), "Done", "badge-xbox", "#4ade80")
    kpi_card(k[3], "📊 Середня готовність", f"{act_df['Готовність (%)'].mean():.0f}%", "По всій базі", "badge-ps", "#38bdf8")

    for _, r in act_df.iterrows():
        if r["Дата релізу"] and r["Статус"].startswith("🟡"):
            days_left = (r["Дата релізу"] - TODAY).days
            if 0 <= days_left <= 14 and r["Готовність (%)"] < 70:
                missing = [t for t in ACTIVITY_CHECKBOX_COLS if not r[t]]
                st.markdown(
                    f'<div class="alert-card-yellow"><b style="color:#fff; font-size:15px;">⏳ {r["Гра"]}</b> ➔ '
                    f'<span style="color:#fde047; font-weight:bold;">реліз через {days_left} дн., маркетинг готовий на {r["Готовність (%)"]}%</span>'
                    f'<p style="margin:2px 0 0 0; font-size:12px; color:#cbd5e1;">Не закрито: {", ".join(missing)}</p></div>',
                    unsafe_allow_html=True,
                )

    cfg = {"Дата релізу": st.column_config.DateColumn(format="DD.MM.YYYY"),
           "Готовність (%)": st.column_config.ProgressColumn("Готовність", format="%d%%", min_value=0, max_value=100)}
    cfg.update({t: st.column_config.CheckboxColumn(t, width="small", disabled=True) for t in ACTIVITY_CHECKBOX_COLS})
    order = ["Гра", "Дата релізу", "Статус", "Готовність (%)"] + ACTIVITY_CHECKBOX_COLS
    st.dataframe(act_df[order], column_config=cfg, hide_index=True, use_container_width=True, height=520)
    csv_button(act_df[order], "📥 Експортувати звіт активностей (.CSV)", "release_activities_report.csv")

# ==============================================================================
# 🧮 РОЗДІЛ 5: ПРОГНОЗИ ТА ЛІДИ
# ==============================================================================
SOURCE_INPUTS = {
    "Steam": ("Steam All-Time Revenue ($):", 6000, 1000),
    "Google Play": ("Завантаження Google Play (Installs):", 500000, 50000),
    "CrazyGames / Web": ("Кількість відгуків / оцінок:", 3500, 500),
    "itch.io": ("Оцінки itch.io:", 40, 5),
}
LEAD_COLUMNS_REQUIRED = {"Назва гри", "Total M1 ($)"}


def render_forecasts():
    st.title("🧮 Прогнози та ліди")
    st.caption("Оцінка нових лідів за 30 піджанрами, пайплайн лідів і перевірка точності моделі на випущених іграх")
    t_calc, t_leads, t_acc = st.tabs(["🧮 Калькулятор ліда", "📋 Пайплайн лідів", "🎯 Точність моделі (план vs факт M1)"])
    with t_calc:
        render_calculator()
    with t_leads:
        render_leads()
    with t_acc:
        render_accuracy()


def render_calculator():
    left, right = st.columns([1, 1.25])
    with left:
        st.markdown('<div class="sandbox-box">', unsafe_allow_html=True)
        st.markdown("#### 1. Вхідні дані ліда")
        name = st.text_input("Назва гри / ліда:", "Project Prototype")
        link = st.text_input("🔗 Посилання на гру (Steam / GP / itch / Web):", "https://store.steampowered.com/app/...")
        source = st.selectbox("Джерело аналізу:", list(SOURCE_INPUTS.keys()))
        lbl, default, step = SOURCE_INPUTS[source]
        value = st.number_input(lbl, min_value=0, value=default, step=step)
        base = base_metric_from_source(source, value)
        st.markdown("---")
        st.markdown("#### 2. Жанр і ціна")
        genre = st.selectbox("Точний піджанр гри:", list(GENRE_DATABASE.keys()))
        price = st.selectbox("Планова ціна на консолях ($):", list(PRICE_MODIFIERS.keys()), index=4)
        st.markdown("</div>", unsafe_allow_html=True)

    cfg = GENRE_DATABASE[genre]
    est = forecast_m1(base, genre, price)
    tot_m1 = sum(est.values())
    share = studio_share()
    ltv = {p: tot_m1 * LTV_MULT[p] for p in ["M3", "M6", "1Y"]}

    with right:
        st.markdown('<div class="sandbox-box">', unsafe_allow_html=True)
        st.markdown(f"### 📈 Розрахунок: **{name}**")
        st.caption(f"💡 *{cfg['Desc']}*")
        st.caption(f"Органічна база: **${base:,.1f}** • Ціновий множник: **{PRICE_MODIFIERS.get(price, 1.0)}x** • "
                   f"Частка студії: **{share * 100:.1f}%** (з налаштувань P&L)")
        if tot_m1 >= 6500:
            st.success("🟢 **ТОП ЛІД:** рекомендовано надсилати пітч (M1 > $6.5k)")
            rec = "✅ ТОП ЛІД"
        elif tot_m1 >= 3000:
            st.info("🟡 **СТАНДАРТНИЙ ТАЙТЛ:** стабільний кандидат ($3k–$6.5k)")
            rec = "⚠️ СТАНДАРТ"
        else:
            st.warning("🔴 **ВИСОКИЙ РИЗИК:** низька прогнозована каса (M1 < $3k)")
            rec = "❌ РИЗИК"

        m = st.columns(3)
        for i, p in enumerate(["PS", "Switch", "Xbox"]):
            m[i].metric(f"{PLATFORM_LABEL[p]} (M1)", fmt_usd(est[p]), f"{cfg[p]}x", delta_color="off")
        t = st.columns(3)
        t[0].metric("🔥 Gross M1", fmt_usd(tot_m1), f"Студії: {fmt_usd(tot_m1 * share)}", delta_color="off")
        t[1].metric(f"📈 Gross M6 ({LTV_MULT['M6']}x)", fmt_usd(ltv["M6"]), f"Студії: {fmt_usd(ltv['M6'] * share)}", delta_color="off")
        t[2].metric(f"📅 Gross 1Y ({LTV_MULT['1Y']}x)", fmt_usd(ltv["1Y"]), f"Студії: {fmt_usd(ltv['1Y'] * share)}", delta_color="off")

        if st.button("➕ Зберегти лід (у таблицю та Google Sheets)", use_container_width=True):
            lead = {
                "Дата": datetime.now().strftime("%Y-%m-%d %H:%M"), "Назва гри": name, "Посилання": link, "Джерело": source,
                "Жанр": genre, "Ціна ($)": price, "Base Metric": round(base, 1),
                "PS M1 ($)": round(est["PS"], 1), "Switch M1 ($)": round(est["Switch"], 1), "Xbox M1 ($)": round(est["Xbox"], 1),
                "Total M1 ($)": round(tot_m1, 1), "Studio Margin M1 ($)": round(tot_m1 * share, 1),
                "1Y LTV ($)": round(ltv["1Y"], 1), "Рекомендація": rec,
            }
            st.session_state.setdefault("scouted_leads", []).append(lead)
            if GOOGLE_WEBHOOK_URL:
                try:
                    res = requests.post(GOOGLE_WEBHOOK_URL, json=lead, timeout=5)
                    st.toast("🚀 Записано в Google Таблицю (лист Leads)!" if res.status_code == 200 else f"⚠️ Webhook відповів {res.status_code}, лід збережено локально")
                except Exception as e:
                    st.warning(f"Збережено локально. Помилка webhook: {e}")
            else:
                st.toast(f"✅ Лід '{name}' збережено!")
        st.markdown("</div>", unsafe_allow_html=True)


def render_leads():
    st.subheader("📋 Пайплайн нових лідів")
    sheet = load_sheet(GOOGLE_SHEET_URL, LEADS_SHEET_NAME)
    # gviz повертає перший лист, якщо листа з такою назвою немає — тому перевіряємо колонки
    sheet = sheet if LEAD_COLUMNS_REQUIRED.issubset(set(sheet.columns)) else pd.DataFrame()
    session = pd.DataFrame(st.session_state.get("scouted_leads", []))
    leads = pd.concat([sheet, session], ignore_index=True) if not session.empty else sheet
    if not leads.empty and {"Назва гри", "Дата"}.issubset(leads.columns):
        leads = leads.drop_duplicates(subset=["Назва гри", "Дата"], keep="first")

    if leads.empty:
        st.info("💡 Лідів поки немає. Розрахуй гру в калькуляторі та натисни «➕ Зберегти лід».")
        return
    st.caption(f"З Google Sheets: **{len(sheet)}** • Додано в цій сесії: **{len(session)}** (ще не підтягнулись із таблиці)")

    total = pd.to_numeric(leads.get("Total M1 ($)"), errors="coerce").fillna(0.0) if "Total M1 ($)" in leads.columns else pd.Series(dtype=float)
    k = st.columns(3)
    k[0].metric("Зібрано лідів", len(leads))
    k[1].metric("Потенціал Gross M1", fmt_usd(float(total.sum()), True))
    k[2].metric(f"Очікуваний дохід студії ({studio_share() * 100:.1f}%)", fmt_usd(float(total.sum()) * studio_share(), True))

    cfg = {"Посилання": st.column_config.LinkColumn("Посилання", display_text="Відкрити ↗")} if "Посилання" in leads.columns else {}
    st.dataframe(leads, column_config=cfg, use_container_width=True, height=400, hide_index=True)
    c1, c2 = st.columns([1, 4])
    with c1:
        csv_button(leads, "📥 Експортувати ліди (.CSV)", "upscale_scouted_leads.csv")
    with c2:
        if st.button("🗑️ Очистити ліди цієї сесії"):
            st.session_state["scouted_leads"] = []
            st.rerun()


def row_base_metric(r):
    base = clean_num_val(r.get(find_col(r.index, "base metric"))) if find_col(r.index, "base metric") else 0.0
    if base > 0:
        return base
    source = safe_str(r.get(COL["source"])).lower() if COL["source"] else ""
    steam = clean_num_val(r.get(find_col(r.index, "steam revenue"))) if find_col(r.index, "steam revenue") else 0.0
    installs_col = find_col(r.index, "installs", "reviews")
    installs = clean_num_val(r.get(installs_col)) if installs_col else 0.0
    if "steam" in source or steam > 0:
        return base_metric_from_source("steam", steam) or 500.0
    if "play" in source or "google" in source or installs >= 10000:
        return base_metric_from_source("google play", installs)
    if "crazy" in source or "web" in source:
        return base_metric_from_source("web", installs)
    if "itch" in source:
        return base_metric_from_source("itch", installs)
    return 0.0


def render_accuracy():
    st.subheader("🎯 Точність прогнозу M1 на випущених іграх")
    st.caption("Та сама формула, що й у калькуляторі: база з джерела × жанровий коефіцієнт × ціновий множник")
    rows = []
    for _, r in raw_df.iterrows():
        m1_plat = {p: row_period_fact(r, "M1", p) or 0.0 for p in PLATFORMS}
        platforms = [p for p in PLATFORMS if m1_plat[p] > 0]
        fact = sum(m1_plat.values())
        base = row_base_metric(r)
        genre_key = match_genre(r.get(COL["genre"]) if COL["genre"] else "")
        price = game_price(r) or 9.99
        pred = sum(forecast_m1(base, genre_key, price, platforms or ["Switch"]).values()) if base > 0 else None

        if pred and fact > 0:
            acc = max(0.0, (1 - abs(fact - pred) / max(fact, pred)) * 100)
            status = "🟢 Перевищила план" if fact > pred * 1.25 else ("🔴 Нижче плану" if fact < pred * 0.70 else "🟡 У плані (±25%)")
        else:
            acc, status = None, ("⚪ Немає вхідних метрик" if fact > 0 else "⚪ Немає факту M1")
        rows.append({"Гра": r["Game_Name_Clean"], "Жанр (модель)": genre_key, "Ціна ($)": price,
                     "Платформи": " + ".join(platforms) if platforms else "—", "Base Metric": round(base, 1) if base else None,
                     "Факт M1 ($)": round(fact, 2) if fact else None, "Прогноз M1 ($)": round(pred, 2) if pred else None,
                     "Різниця ($)": round(fact - pred, 2) if acc is not None else None,
                     "Точність (%)": round(acc, 1) if acc is not None else None, "Статус": status})
    comp = pd.DataFrame(rows)
    valid = comp.dropna(subset=["Точність (%)"])

    a = st.columns(4)
    a[0].metric("Середня точність моделі", f"{valid['Точність (%)'].mean():.1f}%" if not valid.empty else "—")
    a[1].metric("🟢 Перевищили план", f"{comp['Статус'].str.contains('Перевищила').sum()} ігор")
    a[2].metric("🟡 У межах (±25%)", f"{comp['Статус'].str.contains('У плані').sum()} ігор")
    a[3].metric("🔴 Нижче прогнозу", f"{comp['Статус'].str.contains('Нижче').sum()} ігор")

    if not valid.empty:
        top = valid.nlargest(15, "Факт M1 ($)")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=top["Гра"], y=top["Факт M1 ($)"], name="Факт M1", marker_color="#10b981"))
        fig.add_trace(go.Bar(x=top["Гра"], y=top["Прогноз M1 ($)"], name="Прогноз M1", marker_color="#d946ef"))
        show_fig(fig, height=360, barmode="group", xaxis_title="", yaxis_title="$")
    st.dataframe(comp, use_container_width=True, height=450, hide_index=True, column_config={
        "Точність (%)": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
        "Факт M1 ($)": st.column_config.NumberColumn(format="$%.0f"), "Прогноз M1 ($)": st.column_config.NumberColumn(format="$%.0f"),
        "Різниця ($)": st.column_config.NumberColumn(format="$%+.0f"),
    })


# ==============================================================================
# 🧭 9. РОУТИНГ
# ==============================================================================
PAGES = {
    SECTIONS[0]: render_portfolio,
    SECTIONS[1]: render_sales,
    SECTIONS[2]: render_calendar_section,
    SECTIONS[3]: render_releases,
    SECTIONS[4]: render_forecasts,
}
PAGES[app_mode]()
