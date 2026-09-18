import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta, date
import calendar
import math
import json
import os
import re
from anthropic import Anthropic

# ==============================================================================
# 🔗 1. НАЛАШТУВАННЯ ТАБЛИЦЬ ТА АПІ:
# ==============================================================================
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?usp=sharing"
WEEKLY_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?gid=1342107748#gid=1342107748"
NINTENDO_MONTHLY_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?gid=1182691055#gid=1182691055"
XBOX_MONTHLY_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?gid=1981339676#gid=1981339676"  
PIPELINE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1HKBXSvc4pJxDc1Rg2TO-NT8Ww3h3QJBKq_XpInyjhHE/edit?gid=1287937918#gid=1287937918"
ACTIVITY_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?gid=962012405#gid=962012405"      
CALENDAR_SHEET_URL = "https://docs.google.com/spreadsheets/d/1HKBXSvc4pJxDc1Rg2TO-NT8Ww3h3QJBKq_XpInyjhHE/edit?gid=1287937918#gid=1287937918"

GOOGLE_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzrYmeab3xtC4TW9id-N60pI6UmOk6OJj7L2OebkV48omIzqD_h827g3C1mSUpt_WusyA/exec"
ANTHROPIC_API_KEY = ""       

PIPELINE_STORAGE_FILE = "pipeline_master_state.json"
LOGO_FILE = "up4.png"

# ==============================================================================
# 💱 2. ГЛОБАЛЬНИЙ ДОВІДНИК КУРСІВ ВАЛЮТ (FX RATES)
# ==============================================================================
FX_RATES = {
    "USD": 1.00, "EUR": 1.09, "GBP": 1.28, "AUD": 0.67, "NZD": 0.61, "CAD": 0.74,
    "CHF": 1.15, "JPY": 0.0068, "CZK": 0.044, "PLN": 0.26, "ZAR": 0.055, "BRL": 0.18,
    "MXN": 0.052, "SEK": 0.096, "NOK": 0.093, "DKK": 0.146, "CLP": 0.0011, "COP": 0.00024,
    "PEN": 0.27, "ARS": 0.0010, "HKD": 0.128, "KRW": 0.00075, "TWD": 0.031
}

UKR_MONTH_NAMES = ["", "Січ", "Лют", "Бер", "Кві", "Тра", "Чер", "Лип", "Сер", "Вер", "Жов", "Лис", "Гру"]

page_icon_setting = LOGO_FILE if os.path.exists(LOGO_FILE) else "🎮"

st.set_page_config(
    page_title="Upscale Studio | Console BI & Growth Hub",
    page_icon=page_icon_setting,
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 ВИПРАВЛЕНИЙ ТА ЗАХИЩЕНИЙ CSS
st.markdown("""
<style>
    .block-container { padding-top: 1.2rem; padding-bottom: 2.2rem; max-width: 96% !important; }
    
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 1.2rem !important;
    }
    
    section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child,
    section[data-testid="stSidebar"] div[role="radiogroup"] input[type="radio"],
    section[data-testid="stSidebar"] [data-testid="stRadioButtonCustom"],
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        margin: 0 !important;
    }
    
    section[data-testid="stSidebar"] div[role="radiogroup"] {
        display: flex !important;
        flex-direction: column !important;
        gap: 6px !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background-color: #161622 !important;
        border: 1px solid #28283c !important;
        border-radius: 9px !important;
        padding: 10px 14px !important;
        margin: 0 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: #202033 !important;
        border-color: #a855f7 !important;
        transform: translateX(3px) !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked),
    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
        background: linear-gradient(90deg, rgba(217, 70, 239, 0.22) 0%, rgba(249, 115, 22, 0.16) 100%) !important;
        border: 1px solid #d946ef !important;
        box-shadow: 0 3px 12px rgba(217, 70, 239, 0.18) !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label p {
        color: #94a3b8 !important;
        font-size: 13.5px !important;
        font-weight: 600 !important;
        margin: 0 !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p,
    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] p {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 16px;
        border-bottom: 1px solid #28283c;
        background-color: transparent !important;
        padding-bottom: 0px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px;
        background-color: transparent !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        padding: 4px 10px;
        color: #94a3b8 !important;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #e2e8f0 !important; }
    .stTabs [aria-selected="true"] {
        background-color: transparent !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border-bottom: 2px solid #d946ef !important;
    }

    .kpi-card {
        background: linear-gradient(135deg, #1e1e2d 0%, #161622 100%);
        border: 1px solid #2e2e44;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
        margin-bottom: 10px;
    }
    .kpi-label { font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 4px; }
    .kpi-value { font-size: 24px; font-weight: 800; color: #ffffff !important; margin-bottom: 4px; font-family: -apple-system, sans-serif; }
    .kpi-badge { display: inline-block; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px; }
    .badge-total { background-color: rgba(99, 102, 241, 0.2); color: #a5b4fc; }
    .badge-switch { background-color: rgba(230, 0, 18, 0.18); color: #ff6b6b; }
    .badge-ps { background-color: rgba(0, 55, 145, 0.25); color: #60a5fa; }
    .badge-xbox { background-color: rgba(16, 124, 16, 0.25); color: #4ade80; }
    
    .insight-card-flex {
        display: flex; gap: 16px; background-color: #171723; border-left: 4px solid #d946ef;
        padding: 14px 18px; border-radius: 8px; margin-bottom: 12px; border: 1px solid #28283c; align-items: center;
    }
    .game-poster { width: 85px; height: 105px; object-fit: cover; border-radius: 6px; flex-shrink: 0; }
    .top-podium-card { background: #181824; border: 1px solid #2b2b3f; border-radius: 10px; padding: 12px; text-align: center; }
    .sandbox-box { background: #171724; border: 1px solid #2f2f45; border-radius: 12px; padding: 20px; margin-bottom: 15px; }

    /* Стилі Google Calendar */
    .cal-container { background: #13131e; border: 1px solid #28283c; border-radius: 12px; overflow: hidden; margin-top: 15px; }
    .cal-header { display: grid; grid-template-columns: repeat(7, 1fr); background: #1a1a27; border-bottom: 1px solid #28283c; }
    .cal-header-cell { padding: 10px; text-align: center; font-size: 12px; font-weight: 700; color: #94a3b8; text-transform: uppercase; }
    .cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 1px; background: #242436; }
    .cal-day-cell { background: #161622; min-height: 110px; padding: 6px; display: flex; flex-direction: column; transition: background 0.15s ease; }
    .cal-day-cell:hover { background: #1c1c2b; }
    .cal-day-cell.other-month { background: #11111a; opacity: 0.45; }
    .cal-day-cell.today { background: #1d182b; border: 1.5px solid #d946ef; }
    .cal-day-num { font-size: 11px; font-weight: 700; color: #94a3b8; margin-bottom: 5px; text-align: right; }
    .cal-event-pill { font-size: 10px; font-weight: 600; padding: 3px 6px; border-radius: 4px; margin-bottom: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; text-decoration: none; }
    .pill-release { background: rgba(139, 92, 246, 0.25); border-left: 3px solid #a855f7; color: #e9d5ff; }
    .pill-build { background: rgba(56, 189, 248, 0.2); border-left: 3px solid #38bdf8; color: #bae6fd; font-weight: 700; }
    .pill-passed { background: rgba(16, 185, 129, 0.22); border-left: 3px solid #10b981; color: #a7f3d0; font-weight: 700; }
    .pill-nintendo { background: rgba(230, 0, 18, 0.2); border-left: 3px solid #ff4d4f; color: #ffccc7; }
    .pill-xbox { background: rgba(16, 124, 16, 0.22); border-left: 3px solid #52c41a; color: #d9f7be; }
    .pill-deadline { background: rgba(245, 158, 11, 0.25); border-left: 3px solid #faad14; color: #ffe58f; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# 🎯 ВІДКАЛІБРОВАНІ ЦІЛІ НА 2026 РІК ($500k TARGET)
TARGETS_2026 = {
    "Year 2026 (Весь рік)": {
        "Revenue": 500000.0, "Nintendo_Revenue": 130000.0, "PS_Revenue": 250000.0, "Xbox_Revenue": 120000.0,
        "Deals": 20, "Calls": 100, "Contacts": 500, "Leads": 6000
    },
    "Q1 2026": {
        "Revenue": 90000.0, "Nintendo_Revenue": 23500.0, "PS_Revenue": 45000.0, "Xbox_Revenue": 21500.0,
        "Deals": 4, "Calls": 20, "Contacts": 100, "Leads": 1200
    },
    "Q2 2026": {
        "Revenue": 110000.0, "Nintendo_Revenue": 28500.0, "PS_Revenue": 55000.0, "Xbox_Revenue": 26500.0,
        "Deals": 5, "Calls": 25, "Contacts": 125, "Leads": 1500
    },
    "Q3 2026": {
        "Revenue": 130000.0, "Nintendo_Revenue": 34000.0, "PS_Revenue": 65000.0, "Xbox_Revenue": 31000.0,
        "Deals": 5, "Calls": 25, "Contacts": 125, "Leads": 1500
    },
    "Q4 2026": {
        "Revenue": 170000.0, "Nintendo_Revenue": 44000.0, "PS_Revenue": 85000.0, "Xbox_Revenue": 41000.0,
        "Deals": 6, "Calls": 30, "Contacts": 150, "Leads": 1800
    }
}

NINTENDO_SCHEDULE = [
    {"name": "Autumn Sale", "start": "2026-09-11", "end": "2026-09-24", "status": "🔥 Найближчий", "region": "Global / EU / US"},
    {"name": "Halloween Sale", "start": "2026-10-26", "end": "2026-11-15", "status": "🎃 Сезонний", "region": "Global"},
    {"name": "Holiday Sale (EU)", "start": "2026-12-17", "end": "2027-01-10", "status": "🎄 Головний (EU)", "region": "Europe / Australia"},
    {"name": "Holiday Sale (US)", "start": "2026-12-21", "end": "2027-01-11", "status": "🎄 Головний (US)", "region": "Americas"}
]

XBOX_SCHEDULE = [
    {
        "name": "Deep Discounts Sale (ID)",
        "start": "2026-11-05", "end": "2026-11-11", "deadline": "2026-10-01", "feedback": "2026-10-14",
        "limit": 10, "min_price": 0.0, "min_discount": 65, "type": "ID Sale (Глибокі знижки)",
        "note": "Знижка 65% або більше. Ліміт: до 10 тайтлів."
    },
    {
        "name": "Black Friday Sale",
        "start": "2026-11-20", "end": "2026-12-02", "deadline": "2026-10-02", "feedback": "2026-10-15",
        "limit": 5, "min_price": 9.99, "min_discount": 10, "type": "Tentpole Sale",
        "note": "Базова ціна від $9.99. Ліміт: до 5 тайтлів. Кулдаун знято тільки між BF та Countdown."
    },
    {
        "name": "Countdown Sale",
        "start": "2026-12-17", "end": "2027-01-06", "deadline": "2026-10-30", "feedback": "2026-11-13",
        "limit": 5, "min_price": 9.99, "min_discount": 10, "type": "Tentpole Sale",
        "note": "Базова ціна від $9.99. Ліміт: до 5 тайтлів."
    }
]

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
    "Idle / Clicker / Incremental": {"PS": 0.5, "Xbox": 0.4, "Switch": 1.00, "Decay": 1.20, "Desc": "Loaders Inc., Let's Journey"}
}

PRICE_MODIFIERS = {1.99: 1.40, 4.99: 1.20, 5.99: 1.10, 6.99: 1.05, 9.99: 1.00, 14.99: 0.70, 19.99: 0.50, 49.99: 0.20, 99.99: 0.10}

ACTIVITY_CHECKBOX_COLS = [
    "Keymailer page", "Instagram", "YouTube", "PS Form", "PS Trailer",
    "Xbox Trailer", "Xbox Shorts", "Xbox Form", "IGN Trailer", "Press Release", "Trophy Guide", "Keys"
]

# ==============================================================================
# ⚙️ 3. ВСІ ДОПОМІЖНІ ФУНКЦІЇ ТА ПАРСЕРИ (З ГАРАНТОВАНИМ ЗАХИСТОМ ВІД KEYERROR)
# ==============================================================================
def get_export_url(url_or_id):
    if not url_or_id: return ""
    url_str = str(url_or_id).strip()
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url_str)
    sheet_id = match.group(1) if match else url_str
    gid_match = re.search(r"[?#&]gid=([0-9]+)", url_str)
    gid = gid_match.group(1) if gid_match else "0"
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

def parse_flexible_date(d_val):
    if pd.isna(d_val) or not str(d_val).strip() or str(d_val).strip().lower() == 'nan':
        return None
    d_str = str(d_val).strip().replace('\xa0', '').replace(' ', '')
    
    # Авто-фікс порядкових номерів днів Excel (напр. 46223, 46267)
    if d_str.isdigit() and 35000 <= int(d_str) <= 60000:
        return datetime(1899, 12, 30) + timedelta(days=int(d_str))
        
    for fmt in ["%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y.%m.%d", "%m/%d/%Y"]:
        try: return datetime.strptime(d_str[:10], fmt)
        except: continue
    try:
        dt = pd.to_datetime(d_str, dayfirst=True)
        if pd.notna(dt): return dt.to_pydatetime()
    except: pass
    return None

def clean_num_val(val):
    if pd.isna(val): return 0.0
    s = str(val).strip().replace("$", "").replace("€", "").replace("%", "").replace("\xa0", "").replace(" ", "")
    if not s or s.lower() == 'nan': return 0.0
    if "," in s and "." in s:
        if s.find(".") < s.find(","): s = s.replace(".", "").replace(",", ".")
        else: s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try: return float(s)
    except: return 0.0

def is_truthy(val):
    if pd.isna(val): return False
    s = str(val).strip().lower()
    return s in ["true", "истина", "1", "yes", "да", "✅", "done", "t"]

def contains_japanese(text):
    if not text or pd.isna(text): return False
    return bool(re.search(r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]', str(text)))

# Створення безпечного порожнього DataFrame з усіма очікуваними колонками
def get_empty_pipeline_df():
    cols = [
        "Гра", "Розробник", "Художник", "Нюанси", "Ціна", "Дата старту",
        "План фініш Switch", "Плановий строк", "Факт до сабміту", "Switch Білд Дата",
        "Дата релізу", "Статус Lotcheck", "Прийнято Lotcheck", "Днів у Lotcheck",
        "Спроби Lotcheck", "Switch", "Xbox", "PlayStation", "Xbox Концепт", "Xbox TLA", "PS Продукт",
        "Трейлер", "Картинки", "Тексти"
    ]
    return pd.DataFrame(columns=cols)

# Нормалізатор таблиці розкладу та пайплайну (ЗАХИЩЕНИЙ ВІД KEYERROR)
def normalize_pipeline_dataframe(df_in):
    if df_in is None or df_in.empty:
        return get_empty_pipeline_df()
    
    df = df_in.copy()
    rename_rules = {
        "Игра": "Гра", "Title": "Гра", "Game": "Гра",
        "Разработчик": "Розробник", "Developer": "Розробник", "Dev": "Розробник",
        "Художник": "Художник", "Artist": "Художник",
        "Нюансы": "Нюанси", "Notes": "Нюанси",
        "Цена": "Ціна", "Price": "Ціна",
        "Дата старта": "Дата старту", "Start Date": "Дата старту",
        "Планируемая дата финиша релизного билда на Нинтендо": "План фініш Switch",
        "Планируемая дата финиша": "План фініш Switch",
        "Планируемый срок": "Плановий строк",
        "Фактический срок (до сертификации Нинтендо)": "Факт до сабміту",
        "Nintendo Switch релизный билд загружен Дата": "Switch Білд Дата",
        "Дата релиза выбрана": "Дата релізу",
        "Статус сертификации": "Статус Lotcheck",
        "Nintendo Switch релизный принят, дата и с которого раза": "Прийнято Lotcheck",
        "Длительность прохождения сертификации": "Днів у Lotcheck",
        "С какого раза принята сертификация": "Спроби Lotcheck",
        "Nintendo Switch": "Switch", "XBox": "Xbox", "Play Station": "PlayStation",
        "XBox концепт отправлен": "Xbox Концепт", "XBox TLA отправлен": "Xbox TLA", "PS продукт создан": "PS Продукт",
        "Трейлеры все готовы": "Трейлер", "Картинки предоставлены": "Картинки", "Текстовые ресурсы предоставлены": "Тексти"
    }
    
    for old_k, new_k in rename_rules.items():
        if old_k in df.columns and new_k not in df.columns:
            df.rename(columns={old_k: new_k}, inplace=True)
            
    if "Гра" not in df.columns and not df.empty:
        df.rename(columns={df.columns[0]: "Гра"}, inplace=True)

    defaults = {
        "Гра": "Unknown Project", "Розробник": "Не вказано", "Художник": "",
        "Нюанси": "", "Ціна": 0.0, "Дата старту": "", "План фініш Switch": "",
        "Плановий строк": 0, "Факт до сабміту": 0, "Switch Білд Дата": "",
        "Дата релізу": "", "Статус Lotcheck": "In Development",
        "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "",
        "Switch": True, "Xbox": False, "PlayStation": False,
        "Xbox Концепт": False, "Xbox TLA": False, "PS Продукт": False,
        "Трейлер": False, "Картинки": False, "Тексти": False
    }

    for col_name, def_val in defaults.items():
        if col_name not in df.columns:
            df[col_name] = def_val

    def clean_days(val):
        num = clean_num_val(val)
        return int(num) if 0 < num <= 365 else 0

    df["Плановий строк"] = df["Плановий строк"].apply(clean_days)
    df["Факт до сабміту"] = df["Факт до сабміту"].apply(clean_days)
    df["Днів у Lotcheck"] = df["Днів у Lotcheck"].apply(clean_days)
    
    for bool_col in ["Switch", "Xbox", "PlayStation", "Xbox Концепт", "Xbox TLA", "PS Продукт", "Трейлер", "Картинки", "Тексти"]:
        if bool_col in df.columns:
            df[bool_col] = df[bool_col].apply(is_truthy)

    df = df[df["Гра"].astype(str).str.strip() != ""]
    df = df[~df["Гра"].astype(str).str.contains("Что нужно|Резюме|Добавить треккинг|Чистка|Работа с|Горящие|Ожидающие|Коммуникация", case=False, na=False)]
    
    return df.reset_index(drop=True)

# Парсери щомісячних звітів
def parse_nintendo_monthly_data(df_raw):
    date_cols = [c for c in df_raw.columns if re.match(r"^\d{2}/\d{2}/\d{2}$", str(c).strip())]
    if not date_cols:
        return pd.DataFrame(), [], {}
    
    cost_col = next((c for c in df_raw.columns if any(k in c.lower() for k in ["points", "cost", "price", "ціна"])), "Points/Cost")
    curr_col = next((c for c in df_raw.columns if any(k in c.lower() for k in ["curr", "валют"])), "Currency")
    title_code_col = next((c for c in df_raw.columns if "titlecode" in c.lower() or "title code" in c.lower()), None)
    item_col = next((c for c in df_raw.columns if "itemname" in c.lower() or "item name" in c.lower()), None)
    title_col = next((c for c in df_raw.columns if "titlename" in c.lower() or "title name" in c.lower()), None)
    target_name_col = item_col if item_col else (title_col if title_col else df_raw.columns[1])

    code_to_english_map = {}
    if title_code_col:
        for _, r in df_raw.iterrows():
            t_code = str(r.get(title_code_col, "")).strip()
            raw_name = str(r.get(target_name_col, "")).strip()
            if t_code and raw_name and not contains_japanese(raw_name) and raw_name.lower() != 'nan':
                base_code = t_code[:9] if len(t_code) >= 9 else t_code
                if base_code not in code_to_english_map: code_to_english_map[base_code] = raw_name
                if t_code not in code_to_english_map: code_to_english_map[t_code] = raw_name

    def format_month_label(c_str):
        try:
            parts = c_str.split("/")
            m = int(parts[0])
            y = 2000 + int(parts[2])
            if 1 <= m <= 12: return f"{UKR_MONTH_NAMES[m]} {y}"
        except: pass
        return c_str

    month_label_map = {c: format_month_label(c) for c in date_cols}
    
    processed_records = []
    for _, row in df_raw.iterrows():
        raw_name = str(row.get(target_name_col, "Unknown")).strip()
        if not raw_name or raw_name.lower() == 'nan': continue
        
        t_code = str(row.get(title_code_col, "")).strip() if title_code_col else ""
        base_code = t_code[:9] if len(t_code) >= 9 else t_code
        final_item_name = raw_name
        if contains_japanese(raw_name):
            if t_code in code_to_english_map: final_item_name = code_to_english_map[t_code]
            elif base_code in code_to_english_map: final_item_name = code_to_english_map[base_code]

        curr = str(row.get(curr_col, "USD")).strip().upper()
        fx = FX_RATES.get(curr, 1.0)
        cost = clean_num_val(row.get(cost_col, 0.0))
        
        row_dict = {"Назва гри / DLC": final_item_name}
        for d_col in date_cols:
            units = clean_num_val(row.get(d_col, 0.0))
            row_dict[d_col] = units * cost * fx
        processed_records.append(row_dict)
        
    proc_df = pd.DataFrame(processed_records)
    if proc_df.empty: return pd.DataFrame(), [], {}
        
    grouped = proc_df.groupby("Назва гри / DLC")[date_cols].sum().reset_index()
    grouped["Всього ($)"] = grouped[date_cols].sum(axis=1)
    grouped = grouped.sort_values(by="Всього ($)", ascending=False).reset_index(drop=True)
    return grouped.rename(columns=month_label_map), [month_label_map[c] for c in date_cols], month_label_map

def parse_xbox_monthly_data(df_raw):
    if df_raw.empty: return pd.DataFrame(), []
    title_col = next((c for c in df_raw.columns if c.lower().strip() in ["titlename", "parentproductname", "назва", "title"]), None)
    date_col = next((c for c in df_raw.columns if "datestamp" in c.lower().strip() or c.lower().strip() == "date"), None)
    usd_col = next((c for c in df_raw.columns if "purchasepriceusdamount" in c.lower().strip() or "priceusdamount" in c.lower().strip()), None)
    if not title_col or not date_col or not usd_col: return pd.DataFrame(), []

    records = []
    for _, r in df_raw.iterrows():
        t_name = str(r.get(title_col, "")).strip()
        if not t_name or t_name.lower() == 'nan': continue
        dt_val = parse_flexible_date(r.get(date_col))
        if not dt_val: continue
        
        records.append({
            "Назва гри / DLC": t_name, "SortKey": (dt_val.year, dt_val.month),
            "Month": f"{UKR_MONTH_NAMES[dt_val.month]} {dt_val.year}", "USD": clean_num_val(r.get(usd_col, 0.0))
        })
        
    if not records: return pd.DataFrame(), []
    df_rec = pd.DataFrame(records)
    unique_months = df_rec[["SortKey", "Month"]].drop_duplicates().sort_values(by="SortKey")
    ordered_month_labels = unique_months["Month"].tolist()
    pivot = df_rec.pivot_table(index="Назва гри / DLC", columns="Month", values="USD", aggfunc="sum", fill_value=0.0).reset_index()
    existing_months = [m for m in ordered_month_labels if m in pivot.columns]
    pivot = pivot[["Назва гри / DLC"] + existing_months]
    pivot["Всього ($)"] = pivot[existing_months].sum(axis=1)
    return pivot.sort_values(by="Всього ($)", ascending=False).reset_index(drop=True), existing_months

def combine_monthly_matrices(n_matrix, x_matrix, n_months, x_months):
    if n_matrix.empty and x_matrix.empty: return pd.DataFrame(), []
    if n_matrix.empty: return x_matrix.copy(), x_months
    if x_matrix.empty: return n_matrix.copy(), n_months

    month_to_dt = {}
    for m in set(n_months + x_months):
        try:
            parts = m.split(" ")
            month_to_dt[m] = datetime(int(parts[1]), UKR_MONTH_NAMES.index(parts[0]), 1)
        except: month_to_dt[m] = datetime(2000, 1, 1)

    all_sorted_months = sorted(list(month_to_dt.keys()), key=lambda x: month_to_dt[x])
    combined_data = {}

    def ingest(df_in, m_cols):
        for _, row in df_in.iterrows():
            g_name = str(row["Назва гри / DLC"]).strip()
            if g_name not in combined_data: combined_data[g_name] = {m: 0.0 for m in all_sorted_months}
            for mc in m_cols:
                if mc in row: combined_data[g_name][mc] += clean_num_val(row[mc])

    ingest(n_matrix, n_months)
    ingest(x_matrix, x_months)

    rows_out = []
    for g_name, m_dict in combined_data.items():
        r = {"Назва гри / DLC": g_name}
        r.update(m_dict)
        r["Всього ($)"] = sum(m_dict.values())
        rows_out.append(r)

    return pd.DataFrame(rows_out).sort_values(by="Всього ($)", ascending=False).reset_index(drop=True), all_sorted_months

# Завантажувачі даних з Google Sheets
@st.cache_data(ttl=300, show_spinner=False)
def load_data(sheet_url):
    if not sheet_url or "ВСТАВ_СЮДИ" in sheet_url: return pd.DataFrame()
    csv_url = get_export_url(sheet_url)
    try: df = pd.read_csv(csv_url, dtype=str)
    except Exception: return pd.DataFrame()

    text_column_keys = ["cover", "image", "постер", "url", "фото", "link", "посилання", "date", "дата", "name", "назва", "genre", "жанр", "status", "platform", "insights", "formula", "ai"]
    for col in df.columns:
        if any(tk in str(col).lower() for tk in text_column_keys): continue
        df[col] = df[col].apply(clean_num_val)

    name_col = next((c for c in df.columns if any(k in c.lower() for k in ["game name", "game", "title", "назва"])), df.columns[0])
    df.rename(columns={name_col: "Game_Name_Clean"}, inplace=True)
    return df[df["Game_Name_Clean"].astype(str).str.strip() != ""]

@st.cache_data(ttl=300, show_spinner=False)
def load_nintendo_monthly_from_sheet(sheet_url):
    if not sheet_url or "ВСТАВ_СЮДИ" in sheet_url: return pd.DataFrame()
    try: return pd.read_csv(get_export_url(sheet_url), dtype=str)
    except Exception: return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def load_xbox_monthly_from_sheet(sheet_url):
    if not sheet_url or "ВСТАВ_СЮДИ" in sheet_url: return pd.DataFrame()
    try: return pd.read_csv(get_export_url(sheet_url), dtype=str)
    except Exception: return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def load_pipeline_from_sheet(sheet_url):
    if not sheet_url or "ВСТАВ_СЮДИ" in sheet_url: return get_empty_pipeline_df()
    try: return normalize_pipeline_dataframe(pd.read_csv(get_export_url(sheet_url), dtype=str))
    except Exception: return get_empty_pipeline_df()

@st.cache_data(ttl=300, show_spinner=False)
def load_activity_from_sheet(sheet_url):
    if not sheet_url or "ВСТАВ_СЮДИ" in sheet_url: return pd.DataFrame()
    try: return pd.read_csv(get_export_url(sheet_url), dtype=str)
    except Exception: return pd.DataFrame()

def send_calendar_entry_to_google_sheet(webhook_url, payload_dict):
    if not webhook_url: return False, "URL Webhook не вказано"
    try:
        res = requests.post(webhook_url, json={"action": "add_calendar_event", "data": payload_dict}, timeout=8)
        if res.status_code == 200: return True, "Успішно записано в Google Таблицю!"
        return False, f"Помилка сервера: {res.status_code}"
    except Exception as e: return False, str(e)

def load_pipeline_master_data():
    if os.path.exists(PIPELINE_STORAGE_FILE):
        try:
            with open(PIPELINE_STORAGE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data: return normalize_pipeline_dataframe(pd.DataFrame(data))
        except Exception: pass
    return get_empty_pipeline_df()

def save_pipeline_master_data(df):
    try:
        with open(PIPELINE_STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
    except Exception as e: st.error(f"Помилка збереження пайплайну: {e}")

@st.cache_data(ttl=300, show_spinner=False)
def load_weekly_data(sheet_url):
    if not sheet_url or "ВСТАВ_СЮДИ" in sheet_url: return pd.DataFrame()
    csv_url = get_export_url(sheet_url)
    try:
        raw_w = pd.read_csv(csv_url, header=None, dtype=str)
        if raw_w.empty: return pd.DataFrame()

        first_row_str = " ".join([str(x) for x in raw_w.iloc[0].tolist() if pd.notna(x)]).lower()
        second_row_str = " ".join([str(x) for x in raw_w.iloc[1].tolist() if pd.notna(x)]).lower() if len(raw_w) > 1 else ""

        if "from" in second_row_str or "sales" in second_row_str or "to" in second_row_str:
            data_df = raw_w.iloc[2:].copy().reset_index(drop=True)
        elif "from" in first_row_str or "sales" in first_row_str:
            data_df = raw_w.iloc[1:].copy().reset_index(drop=True)
        else:
            data_df = raw_w.copy()

        col_map = {
            0: "From", 1: "To", 2: "Nintendo_Sales", 3: "Nintendo_Sales_Diff",
            4: "Nintendo_Wishlists", 5: "Nintendo_Wishlists_Diff", 6: "Nintendo_Revenue", 7: "Nintendo_Revenue_Diff",
            8: "PS_Sales", 9: "PS_Sales_Diff", 10: "PS_Wishlists", 11: "PS_Wishlists_Diff",
            12: "PS_Revenue", 13: "PS_Revenue_Diff", 14: "Xbox_Sales", 15: "Xbox_Sales_Diff",
            16: "Xbox_Wishlists", 17: "Xbox_Wishlists_Diff", 18: "Xbox_Revenue", 19: "Xbox_Revenue_Diff",
            20: "Leads", 21: "Leads_Diff", 22: "Sequence_Started", 23: "Sequence_Started_Diff",
            24: "Contacts", 25: "Contacts_Diff", 26: "Opportunities", 27: "Opportunities_Diff",
            28: "Calls", 29: "Calls_Diff", 30: "Deals", 31: "Deals_Diff",
            32: "Twitter", 33: "Twitter_Diff", 34: "Instagram", 35: "Instagram_Diff",
            36: "TikTok", 37: "TikTok_Diff", 38: "YouTube", 39: "YouTube_Diff",
            40: "Discord", 41: "Discord_Diff"
        }

        parsed_dict = {}
        for col_idx, col_name in col_map.items():
            if col_idx < data_df.shape[1]: parsed_dict[col_name] = data_df.iloc[:, col_idx]

        df_out = pd.DataFrame(parsed_dict)
        for c in df_out.columns:
            if c not in ["From", "To"]: df_out[c] = df_out[c].apply(clean_num_val)

        df_out = df_out[df_out["From"].astype(str).str.strip().str.lower() != 'nan']
        df_out = df_out[df_out["From"].astype(str).str.strip() != '']
        df_out["Parsed_Date"] = df_out["From"].apply(parse_flexible_date)
        df_out["Month_Label"] = df_out["Parsed_Date"].apply(lambda d: d.strftime("%b %Y") if pd.notna(d) else "—")
        df_out["Total_Revenue"] = df_out.get("PS_Revenue", 0.0) + df_out.get("Nintendo_Revenue", 0.0) + df_out.get("Xbox_Revenue", 0.0)
        df_out["Total_Sales"] = df_out.get("PS_Sales", 0.0) + df_out.get("Nintendo_Sales", 0.0) + df_out.get("Xbox_Sales", 0.0)
        return df_out.reset_index(drop=True)
    except Exception: return pd.DataFrame()

def prepare_quarterly_data(df_weekly):
    if df_weekly.empty or "From" not in df_weekly.columns: return pd.DataFrame()
    df = df_weekly.dropna(subset=["Parsed_Date"]).copy()
    df["Year"] = df["Parsed_Date"].apply(lambda d: d.year)
    df["Quarter"] = df["Parsed_Date"].apply(lambda d: f"Q{math.ceil(d.month/3)} {d.year}")
    return df

# ==============================================================================
# 🚀 4. ЗАВАНТАЖЕННЯ ДАНИХ
# ==============================================================================
raw_df = load_data(GOOGLE_SHEET_URL)
weekly_df = load_weekly_data(WEEKLY_SHEET_URL)
nintendo_monthly_raw_df = load_nintendo_monthly_from_sheet(NINTENDO_MONTHLY_SHEET_URL)
xbox_monthly_raw_df = load_xbox_monthly_from_sheet(XBOX_MONTHLY_SHEET_URL)
sheet_pipeline_df = load_pipeline_from_sheet(PIPELINE_SHEET_URL)
activity_raw_df = load_activity_from_sheet(ACTIVITY_SHEET_URL)

if raw_df.empty:
    st.info("👋 Вкажи валідне посилання на Google Таблицю у рядку `GOOGLE_SHEET_URL`.")
    st.stop()

cover_col = next((c for c in raw_df.columns if any(k in c.lower() for k in ["cover", "image", "постер", "обкладинка"])), None)
discount_col = next((c for c in raw_df.columns if any(k in c.lower() for k in ["target discount", "discount", "знижк"])), None)
porting_cost_col = next((c for c in raw_df.columns if "porting cost" in c.lower() or "porting" in c.lower() or "витрати" in c.lower()), None)
rev_split_col = next((c for c in raw_df.columns if "revenue split" in c.lower() or "split" in c.lower()), None)
recoup_col = next((c for c in raw_df.columns if "recoup" in c.lower() or "рекуп" in c.lower()), None)
status_col = next((c for c in raw_df.columns if "status" in c.lower() or "статус" in c.lower()), None)
rel_date_col = next((c for c in raw_df.columns if any(k in c.lower() for k in ["release date", "release", "date", "дата"])), None)
genre_col = next((c for c in raw_df.columns if "genre" in c.lower() or "жанр" in c.lower()), None)

DEFAULT_IMAGE = "https://img.icons8.com/isometric/100/controller.png"

if "scouted_leads" not in st.session_state:
    st.session_state.scouted_leads = []

# ==============================================================================
# 🧭 5. САЙДБАР
# ==============================================================================
with st.sidebar:
    col_logo, col_title = st.columns([1, 2.8])
    with col_logo:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=64)
        else: st.markdown("<div style='font-size:38px; text-align:center;'>🎮</div>", unsafe_allow_html=True)
    with col_title:
        st.markdown(
            "<h3 style='margin:0; padding-top:2px; font-weight:800; color:#fff; letter-spacing:0.5px; font-size:20px; white-space:nowrap;'>Upscale Studio</h3>"
            "<p style='margin:0; font-size:11px; font-weight:700; color:#d946ef; text-transform:uppercase; letter-spacing:0.8px;'>Publishing BI Hub</p>", 
            unsafe_allow_html=True
        )
    
    st.markdown("<div style='border-bottom: 1px solid #28283c; margin: 12px 0 16px 0;'></div>", unsafe_allow_html=True)

    st.caption("📍 НАВІГАЦІЯ ХАБУ:")
    app_mode = st.radio(
        "Навігація:",
        [
            "🎮 Наші ігри", 
            "📅 Календар релізів і сейлів", 
            "📅 Помісячна динаміка (Monthly)",
            "🚀 Release Pipeline",
            "📋 Release Activity",
            "🎯 Цілі та KPI 2026", 
            "📈 Тижнева динаміка (WoW)", 
            "🧮 Калькулятор прогнозів"
        ],
        index=1,
        label_visibility="collapsed"
    )

    st.markdown("<div style='border-bottom: 1px solid #28283c; margin: 16px 0 14px 0;'></div>", unsafe_allow_html=True)

    st.caption("🔍 ФІЛЬТРАЦІЯ:")
    search = st.text_input("Пошук гри:", "", label_visibility="collapsed", placeholder="Пошук гри...")
    
    filtered_df = raw_df.copy()
    if genre_col:
        available_genres = sorted([str(g).strip() for g in raw_df[genre_col].dropna().unique() if str(g).strip().lower() != 'nan'])
        if available_genres:
            genres = st.multiselect("Жанри:", options=available_genres, default=available_genres, placeholder="Оберіть жанри")
            if genres: filtered_df = filtered_df[filtered_df[genre_col].astype(str).str.strip().isin(genres)]

    if search:
        filtered_df = filtered_df[filtered_df["Game_Name_Clean"].astype(str).str.contains(search, case=False, na=False)]

    st.markdown("<div style='border-bottom: 1px solid #28283c; margin: 16px 0 14px 0;'></div>", unsafe_allow_html=True)

    st.caption("🤖 AI-АНАЛІТИК:")
    claude_key = ANTHROPIC_API_KEY or st.secrets.get("ANTHROPIC_API_KEY", "")
    if not claude_key: claude_key = st.text_input("Anthropic Key:", type="password", placeholder="sk-ant-...")

    ai_query = st.text_area("Запитай базу даних:", placeholder="Напр.: Яка виручка топ-3 тайтлів?")
    
    if st.button("⚡ Запитати Claude", use_container_width=True):
        clean_key = str(claude_key).strip()
        if not clean_key or not clean_key.startswith("sk-ant"): st.error("❌ Введи валідний ключ Anthropic (sk-ant-...)!")
        elif not ai_query.strip(): st.warning("Введи запитання.")
        else:
            with st.spinner("Claude аналізує базу..."):
                try:
                    client = Anthropic(api_key=clean_key)
                    summary_lines = ["Game|Genre|Price|DevCost|DevSplit|Recoup|PS_All|Switch_All|Xbox_All|Total_All"]
                    def find_num(row_s, keys):
                        for c in row_s.index:
                            if all(k in c.lower() for k in keys):
                                try: return int(round(float(row_s[c])))
                                except: pass
                        return 0

                    for _, r in raw_df.iterrows():
                        g_name = str(r["Game_Name_Clean"]).strip()
                        if not g_name or g_name.lower() == 'nan': continue
                        g_genre = str(r.get(genre_col, "—")).strip() if genre_col else "—"
                        g_price = clean_num_val(r.get("Price consoles, $", r.get("Price consoles", 0.0)))
                        g_cost = clean_num_val(r.get(porting_cost_col, 0.0)) if porting_cost_col else 0.0
                        g_split = clean_num_val(r.get(rev_split_col, 50.0)) if rev_split_col else 50.0
                        g_rec = clean_num_val(r.get(recoup_col, 0.0)) if recoup_col else 0.0

                        ps_all = find_num(r, ["playstation", "all"]) or find_num(r, ["ps", "all"])
                        sw_all = find_num(r, ["switch", "all"])
                        xb_all = find_num(r, ["xbox", "all"])
                        tot_all = find_num(r, ["total"]) or (ps_all + sw_all + xb_all)
                        summary_lines.append(f"{g_name}|{g_genre}|${g_price}|Cost:${g_cost}|Split:{g_split}%|Recoup:${g_rec}|PS:${ps_all}|Switch:${sw_all}|Xbox:${xb_all}|Total:${tot_all}")

                    compact_dataset = "\n".join(summary_lines)
                    weekly_csv_snippet = weekly_df.to_csv(index=False) if not weekly_df.empty else "No weekly data"

                    prompt = f"""Ти — головний фінансовий директор видавництва Upscale Studio (Україна).
Дані портфоліо ({len(summary_lines)-1} ігор):
{compact_dataset}
Тижнева звітність та BizDev воронка:
{weekly_csv_snippet}
Запитання: "{ai_query}"
Дай коротку точну відповідь українською мовою з реальними цифрами."""

                    try:
                        msg = client.messages.create(model="claude-haiku-4-5", max_tokens=900, messages=[{"role": "user", "content": prompt}])
                        raw_text = msg.content[0].text
                    except:
                        msg = client.messages.create(model="claude-3-5-haiku-20241022", max_tokens=900, messages=[{"role": "user", "content": prompt}])
                        raw_text = msg.content[0].text

                    st.markdown("### 💡 Результат аналізу:")
                    st.markdown(re.sub(r'(?<!\\)\$', r'\\$', raw_text))
                except Exception as e: st.error(f"❌ Помилка API: {e}")

    st.markdown("<div style='border-bottom: 1px solid #28283c; margin: 16px 0 14px 0;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Оновити дані з Google Sheets", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Чіткий розрахунок All-Time сум
def get_exact_all_time(df_target, plat):
    for c in df_target.columns:
        cl = c.lower()
        if plat.lower() in cl and "all" in cl:
            return float(df_target[c].sum())
    return 0.0

ps_rev = get_exact_all_time(filtered_df, "PS") or get_exact_all_time(filtered_df, "PlayStation")
switch_rev = get_exact_all_time(filtered_df, "Switch")
xbox_rev = get_exact_all_time(filtered_df, "Xbox")
total_col = next((c for c in filtered_df.columns if c.lower() == "total" or "всього" in c.lower()), None)
total_gross = float(filtered_df[total_col].sum()) if total_col else (switch_rev + ps_rev + xbox_rev)

# ==============================================================================
# 🎮 РОЗДІЛ 1: НАШІ ІГРИ (ПОВНІ 6 ВКЛАДОК)
# ==============================================================================
if app_mode == "🎮 Наші ігри":
    st.title("📊 Портфоліо Upscale Studio")
    st.caption(f"Фактичні результати випущених ігор • Всього проаналізовано: **{len(filtered_df)}**")

    switch_pct = round(switch_rev / max(total_gross, 1) * 100) if total_gross > 0 else 0
    ps_pct = round(ps_rev / max(total_gross, 1) * 100) if total_gross > 0 else 0
    xbox_pct = round(xbox_rev / max(total_gross, 1) * 100) if total_gross > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="kpi-card"><div class="kpi-label">Загальна каса (All-Time)</div><div class="kpi-value">${total_gross:,.2f}</div><span class="kpi-badge badge-total">100% Total Gross</span></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card"><div class="kpi-label">Nintendo Switch</div><div class="kpi-value" style="color:#ff6b6b !important;">${switch_rev:,.2f}</div><span class="kpi-badge badge-switch">↑ {switch_pct}% частка</span></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card"><div class="kpi-label">PlayStation</div><div class="kpi-value" style="color:#60a5fa !important;">${ps_rev:,.2f}</div><span class="kpi-badge badge-ps">↑ {ps_pct}% частка</span></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi-card"><div class="kpi-label">Xbox</div><div class="kpi-value" style="color:#4ade80 !important;">${xbox_rev:,.2f}</div><span class="kpi-badge badge-xbox">↑ {xbox_pct}% частка</span></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_analytics, tab_insights, tab_sales_tracker, tab_forecast_review, tab_pnl_royalty, tab_table_report = st.tabs([
        "📈 Аналітика та Динаміка", "🧠 Інсайти та Постери", "📅 Розпродажі (Nintendo & Xbox)",
        "🎯 План vs Факт (Точність)", "💵 P&L, Зарплати та Роялті", "📑 Таблиця та One-Pager Звіт"
    ])

    with tab_analytics:
        st.subheader("🏆 Топ-3 бестселери портфоліо")
        actual_total_col = total_col if total_col else filtered_df.columns[0]
        top3_df = filtered_df.sort_values(by=actual_total_col, ascending=False).head(3)
        p_cols = st.columns(3)
        for idx, (_, top_row) in enumerate(top3_df.iterrows()):
            img_url = top_row[cover_col] if cover_col and pd.notna(top_row[cover_col]) and str(top_row[cover_col]).startswith("http") else DEFAULT_IMAGE
            with p_cols[idx]:
                st.markdown(f'<div class="top-podium-card"><img src="{img_url}" style="width:100%; height:135px; object-fit:cover; border-radius:6px; margin-bottom:8px;"><h4 style="margin:0 0 4px 0; color:#fff;">#{idx+1} {top_row["Game_Name_Clean"]}</h4><p style="margin:0; font-size:18px; color:#34d399; font-weight:bold;">${top_row[actual_total_col]:,.2f}</p></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        c_left, c_right = st.columns([1, 2])
        with c_left:
            st.subheader("Частка консолей у виручці")
            plat_df = pd.DataFrame({"Platform": ["Nintendo Switch", "PlayStation", "Xbox"], "Revenue": [switch_rev, ps_rev, xbox_rev]})
            plat_df = plat_df[plat_df["Revenue"] > 0]
            if not plat_df.empty:
                fig_pie = px.pie(plat_df, values="Revenue", names="Platform", hole=0.5, color="Platform", color_discrete_map={"Nintendo Switch": "#e60012", "PlayStation": "#3b82f6", "Xbox": "#107c10"})
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), margin=dict(t=15, b=15, l=15, r=15))
                st.plotly_chart(fig_pie, use_container_width=True)
        with c_right:
            st.subheader("Топ-15 тайтлів за виторгом ($)")
            top_df = filtered_df.sort_values(by=actual_total_col, ascending=True).tail(15)
            fig_bar = px.bar(top_df, x=actual_total_col, y="Game_Name_Clean", orientation="h", text=actual_total_col, color_discrete_sequence=["#d946ef"])
            fig_bar.update_traces(texttemplate='$%{text:,.0f}', textposition='outside', textfont=dict(color="#ffffff"))
            fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), xaxis=dict(gridcolor="#28283c", title="Виторг ($)"), yaxis=dict(gridcolor="#28283c", title=""), margin=dict(t=15, b=15, l=15, r=15))
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")
        st.subheader("⏳ Крива динаміки виручки (M1 ➔ M3 ➔ M6 ➔ 1Y)")
        time_cols = [c for c in filtered_df.columns if any(p in c.lower() for p in ["1st", "3 month", "6 month", "1 year", "all time"])]
        if time_cols:
            decay_rows = []
            for _, row in filtered_df.iterrows():
                for t_col in time_cols:
                    period_label = t_col
                    if "1st" in t_col.lower() or "m1" in t_col.lower(): period_label = "1. M1"
                    elif "3" in t_col.lower(): period_label = "2. M3"
                    elif "6" in t_col.lower(): period_label = "3. M6"
                    elif "year" in t_col.lower() or "1y" in t_col.lower(): period_label = "4. 1Y"
                    elif "all" in t_col.lower(): period_label = "5. All Time"
                    decay_rows.append({"Game": row["Game_Name_Clean"], "Period": period_label, "Revenue": row[t_col]})
            decay_df = pd.DataFrame(decay_rows).sort_values("Period")
            fig_line = px.line(decay_df, x="Period", y="Revenue", color="Game", markers=True)
            fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), xaxis=dict(gridcolor="#28283c", title="Період"), yaxis=dict(gridcolor="#28283c", title="Накопичений виторг ($)"), margin=dict(t=15, b=15, l=15, r=15))
            st.plotly_chart(fig_line, use_container_width=True)

    with tab_insights:
        st.subheader("Стратегічні висновки та постери тайтлів")
        formula_col = next((c for c in filtered_df.columns if "formula" in c.lower()), None)
        ai_col = next((c for c in filtered_df.columns if "ai" in c.lower()), None)
        actual_total_col = total_col if total_col else filtered_df.columns[0]
        for _, row in filtered_df.iterrows():
            g_name = row["Game_Name_Clean"]
            rev_val = row[actual_total_col]
            f_text = row[formula_col] if formula_col and pd.notna(row[formula_col]) else "—"
            ai_text = row[ai_col] if ai_col and pd.notna(row[ai_col]) else "—"
            img_url = row[cover_col] if cover_col and pd.notna(row[cover_col]) and str(row[cover_col]).startswith("http") else DEFAULT_IMAGE
            st.markdown(f"""
            <div class="insight-card-flex">
                <img src="{img_url}" class="game-poster" onerror="this.src='{DEFAULT_IMAGE}'">
                <div style="flex-grow: 1;">
                    <h4 style="margin:0 0 6px 0; color:#ffffff; font-size:16px;">🎮 {g_name} — <span style="color:#34d399; font-weight:bold;">${rev_val:,.2f}</span></h4>
                    <p style="margin:0 0 4px 0; font-size:13px; color:#a5b4fc;"><b>📐 Формула/Динаміка:</b> {f_text}</p>
                    <p style="margin:0; font-size:13px; color:#cbd5e1; line-height:1.5;"><b>💡 AI Аналіз:</b> {ai_text}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab_sales_tracker:
        st.subheader("📅 Центр управління консольними розпродажами")
        sale_platform_choice = st.radio("Оберіть платформу:", ["🔴 Nintendo eShop", "🟢 Xbox Store"], horizontal=True)

        if sale_platform_choice == "🔴 Nintendo eShop":
            cal_df = pd.DataFrame([{"Сейл": s["name"], "Початок": s["start"], "Кінець": s["end"], "Статус": s["status"], "Регіон": s["region"]} for s in NINTENDO_SCHEDULE])
            fig_timeline = px.timeline(cal_df, x_start="Початок", x_end="Кінець", y="Сейл", color="Статус")
            fig_timeline.update_yaxes(autorange="reversed")
            fig_timeline.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), height=250)
            st.plotly_chart(fig_timeline, use_container_width=True)

            sale_choice = st.selectbox("Оберіть сейл Nintendo:", [s['name'] for s in NINTENDO_SCHEDULE], index=0)
            selected_sale_data = next(s for s in NINTENDO_SCHEDULE if s["name"] == sale_choice)
            target_start_date = datetime.strptime(selected_sale_data["start"], "%Y-%m-%d")

            tracker_rows = []
            for _, r in filtered_df.iterrows():
                g_name = r["Game_Name_Clean"]
                r_date = parse_flexible_date(r.get(rel_date_col, None)) if rel_date_col else None
                days_since_rel = (target_start_date - r_date).days if r_date else 999
                is_ready = days_since_rel >= 30
                sheet_discount_val = clean_num_val(r.get(discount_col, 70.0)) if discount_col else 70.0

                tracker_rows.append({
                    "Включити": is_ready, "Гра": g_name, "Знижка % (з Таблиці)": int(sheet_discount_val) if sheet_discount_val > 0 else 70,
                    "Реальна дата релізу": r_date.strftime("%Y-%m-%d") if r_date else "—", "Статус Nintendo": "🟢 Готова" if is_ready else f"🟡 Кулдаун ({30-days_since_rel}дн)",
                    "Деталі кулдауну": f"Пройшло {days_since_rel} дн." if is_ready else f"Залишилось {30-days_since_rel} дн."
                })

            tracker_df = pd.DataFrame(tracker_rows)
            edited_tracker_df = st.data_editor(
                tracker_df,
                column_config={
                    "Включити": st.column_config.CheckboxColumn("Включити в сейл", default=True),
                    "Знижка % (з Таблиці)": st.column_config.NumberColumn("Знижка (%)", min_value=10, max_value=90, step=5),
                    "Гра": st.column_config.TextColumn("Назва гри", disabled=True),
                    "Статус Nintendo": st.column_config.TextColumn("Статус", disabled=True)
                },
                disabled=["Реальна дата релізу", "Деталі кулдауну"],
                hide_index=True, use_container_width=True, height=340
            )

            if st.button("⚡ Згенерувати оновлений Bookmarklet для Nintendo", use_container_width=True):
                selected_games = edited_tracker_df[edited_tracker_df["Включити"] == True]
                if selected_games.empty: st.warning("Оберіть хоча б одну гру!")
                else:
                    discounts_payload = {s_row["Гра"].strip().lower(): int(s_row["Знижка % (з Таблиці)"]) for _, s_row in selected_games.iterrows()}
                    json_str = json.dumps(discounts_payload, ensure_ascii=False)
                    bookmarklet_code = f"""javascript:(function(){{const discounts = {json_str};function parsePrice(text){{let s=text.trim().replace(/[^0-9.,]/g,'');if(!s)return null;if(s.includes('.')&&s.includes(',')){{if(s.indexOf('.')<s.indexOf(',')){{s=s.replace(/\\./g,'').replace(',','.')}}else{{s=s.replace(/,/g,'')}}}}else if(s.includes(',')){{s=s.replace(',','.')}}return parseFloat(s);}}function getGameTitle(el){{let current=el;while(current&&current!==document.body){{let prev=current.previousElementSibling;while(prev){{let text=prev.innerText||"";if(text.includes('HAC-')&&text.includes(':')){{let rawTitle=text.substring(text.indexOf(':')+1).trim();rawTitle=rawTitle.replace(/\\s*\\(\\d+\\/\\d+\\)\\s*$/, '').trim();return rawTitle;}}prev=prev.previousElementSibling;}}current=current.parentElement;}}return null;}}const sortedKeys=Object.keys(discounts).sort((a,b)=>b.length-a.length);const inputs=Array.from(document.querySelectorAll('input[type="text"]')).filter(inp=>{{const td=inp.closest('td');if(!td)return false;const prevTd=td.previousElementSibling;return prevTd&&/[\\d]/.test(prevTd.innerText);}});let updatedCount=0;inputs.forEach(priceInput=>{{const td=priceInput.closest('td');const regularPriceTd=td.previousElementSibling;if(!regularPriceTd)return;let regularPrice=parsePrice(regularPriceTd.innerText);if(regularPrice===null||isNaN(regularPrice)||regularPrice<=0)return;let gameTitle=getGameTitle(priceInput)||"Default";let cleanTitle=gameTitle.toLowerCase().replace(/\\s+/g,' ').trim();let discountPercent=70;let matched=false;for(let k of sortedKeys){{if(cleanTitle===k){{discountPercent=discounts[k];matched=true;break;}}}}if(!matched){{for(let k of sortedKeys){{if(cleanTitle.includes(k)||k.includes(cleanTitle)){{discountPercent=discounts[k];break;}}}}}}let discountedVal=regularPrice*(1-(discountPercent/100));let finalPriceStr="";if(regularPriceTd.innerText.includes(',')||regularPriceTd.innerText.includes('.')){{finalPriceStr=(Math.floor(discountedVal*100)/100).toFixed(2);}}else{{finalPriceStr=Math.floor(discountedVal).toString();}}priceInput.value=finalPriceStr;priceInput.dispatchEvent(new Event('input',{{bubbles:true}}));priceInput.dispatchEvent(new Event('change',{{bubbles:true}}));const row=priceInput.closest('tr');if(row){{const checkbox=row.querySelector('input[type="checkbox"]');if(checkbox&&!checkbox.checked){{checkbox.click();}}}}updatedCount++;}});alert("🎉 Заповнено цін: "+updatedCount);}})();"""
                    st.success(f"🎉 Bookmarklet згенеровано!")
                    st.code(bookmarklet_code, language="javascript")

        else:
            xb_cal_df = pd.DataFrame([{"Сейл": s["name"], "Початок": s["start"], "Кінець": s["end"], "Тип": s["type"]} for s in XBOX_SCHEDULE])
            fig_xb_tl = px.timeline(xb_cal_df, x_start="Початок", x_end="Кінець", y="Сейл", color="Тип", color_discrete_map={"ID Sale (Глибокі знижки)": "#10b981", "Tentpole Sale": "#d946ef"})
            fig_xb_tl.update_yaxes(autorange="reversed")
            fig_xb_tl.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), height=230)
            st.plotly_chart(fig_xb_tl, use_container_width=True)

            xb_choice = st.selectbox("Оберіть сейл Xbox:", [s['name'] for s in XBOX_SCHEDULE], index=0)
            cur_xb_sale = next(s for s in XBOX_SCHEDULE if s["name"] == xb_choice)
            deadline_dt = datetime.strptime(cur_xb_sale["deadline"], "%Y-%m-%d")
            days_to_deadline = (deadline_dt - datetime.now()).days
            deadline_badge = f"⏳ Залишилось {days_to_deadline} дн." if days_to_deadline > 0 else "🚨 Дедлайн СЬОГОДНІ!"

            xc1, xc2, xc3, xc4 = st.columns(4)
            xc1.metric("🎯 Розпродаж", cur_xb_sale["name"])
            xc2.metric("⏰ Дедлайн подачі", cur_xb_sale["deadline"], deadline_badge)
            xc3.metric("🔒 Ліміт тайтлів", f"до {cur_xb_sale['limit']} ігор")
            xc4.metric("📩 Feedback", cur_xb_sale["feedback"])

    with tab_forecast_review:
        st.subheader("🎯 Порівняння прогнозованих та фактичних результатів")
        st.caption("Аудит точності на основі відкаліброваних 30 піджанрів")

        def get_m1_fact(row_s, plat):
            for c in row_s.index:
                if plat.lower() in c.lower() and ("1st" in c.lower() or "month" in c.lower()) and "pred" not in c.lower():
                    try: return float(row_s[c])
                    except: pass
            return 0.0

        comparison_list = []
        for _, r in filtered_df.iterrows():
            g_name = str(r["Game_Name_Clean"]).strip()
            if not g_name or g_name.lower() == 'nan': continue
            g_genre_str = str(r.get(genre_col, "Simulator: Job / Service / Business (3D)")).strip()
            g_price = clean_num_val(r.get("Price consoles, $", r.get("Price consoles", 9.99))) or 9.99

            ps_m1_fact = get_m1_fact(r, "PS") or get_m1_fact(r, "PlayStation")
            sw_m1_fact = get_m1_fact(r, "Switch")
            xb_m1_fact = get_m1_fact(r, "Xbox")

            active_platforms = []
            if ps_m1_fact > 0: active_platforms.append("PS")
            if sw_m1_fact > 0: active_platforms.append("Switch")
            if xb_m1_fact > 0: active_platforms.append("Xbox")
            if not active_platforms: active_platforms = ["Switch"]

            total_m1_fact = (ps_m1_fact if "PS" in active_platforms else 0.0) + (sw_m1_fact if "Switch" in active_platforms else 0.0) + (xb_m1_fact if "Xbox" in active_platforms else 0.0)

            comparison_list.append({
                "Гра": g_name, "Жанр": g_genre_str, "Ціна ($)": g_price,
                "Платформи": " + ".join(active_platforms), "Факт M1 ($)": round(total_m1_fact, 2) if total_m1_fact > 0 else "—"
            })

        st.dataframe(pd.DataFrame(comparison_list), use_container_width=True, height=400)

    with tab_pnl_royalty:
        st.subheader("💵 Фінансовий P&L, Зарплати портінгу та Роялті девелоперів")
        with st.expander("⚙️ Параметри комісій та податків (Симуляція)", expanded=False):
            sc1, sc2 = st.columns(2)
            sim_store_cut = sc1.slider("Комісія сторів (%):", 15, 35, 30, step=1)
            sim_tax_cut = sc2.slider("Податки та резерви (%):", 0, 15, 7, step=1)

        net_receipt_pct = (100 - sim_store_cut - sim_tax_cut) / 100.0
        pnl_rows = []
        tot_internal_cost = 0.0
        tot_studio_pure = 0.0
        tot_dev_royalty = 0.0
        tot_net_bank = 0.0

        for _, r in filtered_df.iterrows():
            g_name = r["Game_Name_Clean"]
            g_gross = clean_num_val(r[actual_total_col])
            g_porting_salary = clean_num_val(r.get(porting_cost_col, 0.0)) if porting_cost_col else 0.0
            g_dev_split = clean_num_val(r.get(rev_split_col, 50.0)) if rev_split_col else 50.0
            if g_dev_split <= 0: g_dev_split = 50.0
            g_contract_recoup = clean_num_val(r.get(recoup_col, 0.0)) if recoup_col else 0.0

            g_net_rec = g_gross * net_receipt_pct
            if g_contract_recoup > 0:
                recouped = min(g_net_rec, g_contract_recoup)
                distrib = max(0.0, g_net_rec - g_contract_recoup)
                d_royalty = distrib * (g_dev_split / 100.0)
                s_gross_margin = recouped + (distrib * (1.0 - g_dev_split / 100.0))
            else:
                d_royalty = g_net_rec * (g_dev_split / 100.0)
                s_gross_margin = g_net_rec * (1.0 - g_dev_split / 100.0)

            s_pure_net = s_gross_margin - g_porting_salary
            tot_internal_cost += g_porting_salary
            tot_studio_pure += s_pure_net
            tot_dev_royalty += d_royalty
            tot_net_bank += g_net_rec

            pnl_rows.append({
                "Гра": g_name, "Gross ($)": round(g_gross, 2), "Net у банку ($)": round(g_net_rec, 2),
                "Зарплата розробника ($)": round(g_porting_salary, 2), "Роялті автору ($)": round(d_royalty, 2),
                "🔥 Чистий прибуток студії ($)": round(s_pure_net, 2)
            })

        pn1, pn2, pn3 = st.columns(3)
        pn1.metric(f"Net у банку ({net_receipt_pct*100:.0f}%)", f"${tot_net_bank:,.2f}")
        pn2.metric("Виплати роялті авторам", f"${tot_dev_royalty:,.2f}")
        pn3.metric("🔥 Чистий прибуток Upscale Studio", f"${tot_studio_pure:,.2f}", f"Зарплати: ${tot_internal_cost:,.0f}")
        st.dataframe(pd.DataFrame(pnl_rows).sort_values(by="Gross ($)", ascending=False), use_container_width=True, height=400)

    with tab_table_report:
        st.subheader("📑 Повна фінансова таблиця портфоліо")
        st.dataframe(filtered_df, use_container_width=True, height=420)
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Експортувати дані (.CSV)", data=csv_data, file_name="console_sales_portfolio.csv", mime="text/csv")

# ==============================================================================
# 📅 РОЗДІЛ 2: ГОЛОВНИЙ КОНСОЛЬНИЙ КАЛЕНДАР (НАЖИВО З GOOGLE ТАБЛИЦІ)
# ==============================================================================
elif app_mode == "📅 Календар релізів і сейлів":
    st.title("📅 Консольний календар виробництва та розпродажів")
    st.caption("Пряма синхронізація з Google Таблицею виробництва • Контроль фінішу білдів Switch, Lotcheck, релізів та аналітика розробників")

    with st.expander("⚙️ Джерело даних для Календаря (Google Sheets Tab)", expanded=False):
        custom_cal_url = st.text_input("URL вкладки з датами виробництва (з #gid=...):", CALENDAR_SHEET_URL)
        if st.button("🔄 Перечитати таблицю дат"):
            st.cache_data.clear()
            st.rerun()

    calendar_source_df = load_pipeline_from_sheet(custom_cal_url) if custom_cal_url else sheet_pipeline_df
    if calendar_source_df.empty:
        calendar_source_df = get_empty_pipeline_df()

    with st.expander("➕ Додати новий проект / реліз прямо в Google Таблицю", expanded=False):
        with st.form("add_calendar_project_form", clear_on_submit=True):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                in_game = st.text_input("Назва гри (Title):", placeholder="Напр. SCP-3008: Infinite Store")
                in_dev = st.selectbox("Розробник:", ["Ігор", "Влад", "Діма", "Сергій", "Іван", "Максим", "Інший"])
                in_artist = st.text_input("Художник:", "")
            with fc2:
                in_start = st.date_input("Дата старту порту:", datetime.now().date())
                in_finish_switch = st.date_input("План фінішу білда Switch:", datetime.now().date() + timedelta(days=21))
                in_plan_days = st.number_input("Плановий строк (днів):", min_value=1, value=14, step=1)
            with fc3:
                in_rel_date = st.date_input("Цільова дата релізу:", datetime.now().date() + timedelta(days=60))
                in_lotcheck_stat = st.selectbox("Статус Lotcheck:", ["In Development", "In testing", "Submitted for lotcheck", "Passed Lotcheck", "Blocked"])
                in_notes = st.text_area("Нюанси / Примітки:", placeholder="Коментарі до проекту...")

            if st.form_submit_button("🚀 Зберегти проект у Google Таблицю", use_container_width=True):
                if not in_game.strip():
                    st.warning("Введіть назву гри!")
                else:
                    new_item_dict = {
                        "Игра": in_game.strip(), "Разработчик": in_dev, "Художник": in_artist.strip(), "Цена": "9,99", "Нюансы": in_notes.strip(),
                        "Дата старта": in_start.strftime("%d.%m.%Y"), "Планируемая дата финиша релизного билда на Нинтендо": in_finish_switch.strftime("%d.%m.%Y"),
                        "Планируемый срок": int(in_plan_days), "Дата релиза выбрана": in_rel_date.strftime("%d.%m.%Y"), "Статус сертификации": in_lotcheck_stat
                    }
                    with st.spinner("Записую новий рядок у Google Таблицю..."):
                        ok, resp_msg = send_calendar_entry_to_google_sheet(GOOGLE_WEBHOOK_URL, new_item_dict)
                        if ok:
                            st.success(f"🎉 Проект '{in_game}' додано в Google Таблицю! Календар оновлено.")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.warning(f"⚠️ Помилка запису через Webhook: {resp_msg}")

    events_list = []

    # А. Події з живої таблиці Google Sheets
    if not calendar_source_df.empty:
        for _, row in calendar_source_df.iterrows():
            g_name = str(row.get("Гра", "")).strip()
            g_dev = str(row.get("Розробник", "Команда")).strip()
            if not g_name or g_name.lower() == 'nan': continue

            # 1. План фінішу білда Switch
            b_plan_dt = parse_flexible_date(row.get("План фініш Switch"))
            if b_plan_dt:
                events_list.append({
                    "date": b_plan_dt.date(), "title": f"🛠️ Білд: {g_name} ({g_dev})",
                    "type": "build_plan", "desc": f"Плановий фініш білда Switch. Розробник: {g_dev}", "dev": g_dev
                })

            # 2. Дата прийняття білда в Lotcheck
            raw_lotcheck = str(row.get("Прийнято Lotcheck", "")).strip()
            lotcheck_dt = parse_flexible_date(raw_lotcheck[:10])
            if lotcheck_dt:
                att = str(row.get("Спроби Lotcheck", "")).strip()
                att_txt = f" ({att})" if att and att.lower() != 'nan' else ""
                events_list.append({
                    "date": lotcheck_dt.date(), "title": f"🟢 Lotcheck: {g_name} ({g_dev})",
                    "type": "lotcheck_passed", "desc": f"Білд прийнято Nintendo Lotcheck{att_txt}! Розробник: {g_dev}", "dev": g_dev
                })

            # 3. Дата релізу гри
            r_dt = parse_flexible_date(row.get("Дата релізу"))
            if r_dt:
                events_list.append({
                    "date": r_dt.date(), "title": f"🎮 Реліз: {g_name} ({g_dev})",
                    "type": "release", "desc": f"Реліз {g_name} на Nintendo Switch. Розробник: {g_dev}", "dev": g_dev
                })

    # Б. Розпродажі Nintendo eShop
    for ns in NINTENDO_SCHEDULE:
        s_dt = datetime.strptime(ns["start"], "%Y-%m-%d").date()
        e_dt = datetime.strptime(ns["end"], "%Y-%m-%d").date()
        cur_d = s_dt
        while cur_d <= e_dt:
            lbl = f"🔴 NSW: {ns['name']}"
            if cur_d == s_dt: lbl += " (Старт 🔥)"
            elif cur_d == e_dt: lbl += " (Фініш 🏁)"
            events_list.append({"date": cur_d, "title": lbl, "type": "nintendo", "desc": f"Розпродаж Nintendo eShop ({ns['region']})", "dev": ""})
            cur_d += timedelta(days=1)

    # В. Розпродажі та Дедлайни Xbox
    for xs in XBOX_SCHEDULE:
        x_start = datetime.strptime(xs["start"], "%Y-%m-%d").date()
        x_end = datetime.strptime(xs["end"], "%Y-%m-%d").date()
        x_dead = datetime.strptime(xs["deadline"], "%Y-%m-%d").date()
        events_list.append({"date": x_dead, "title": f"⏰ ДЕДЛАЙН: {xs['name']}", "type": "deadline", "desc": f"Дедлайн подачі в ID@Xbox на {xs['name']}", "dev": ""})
        cur_xd = x_start
        while cur_xd <= x_end:
            lbl_x = f"🟢 XB: {xs['name']}"
            if cur_xd == x_start: lbl_x += " (Старт 🔥)"
            elif cur_xd == x_end: lbl_x += " (Фініш 🏁)"
            events_list.append({"date": cur_xd, "title": lbl_x, "type": "xbox", "desc": f"Xbox Sale: {xs['note']}", "dev": ""})
            cur_xd += timedelta(days=1)

    c_tab1, c_tab2 = st.tabs([
        "📅 Google Calendar & Agenda",
        "👨‍💻 Продуктивність та середній час розробників"
    ])

    with c_tab1:
        current_today = date(2026, 9, 18)
        month_options = [
            (2026, 7, "Липень 2026"), (2026, 8, "Серпень 2026"), (2026, 9, "Вересень 2026"),
            (2026, 10, "Жовтень 2026"), (2026, 11, "Листопад 2026"), (2026, 12, "Грудень 2026")
        ]
        
        c_ctl1, c_ctl2, c_ctl3 = st.columns([1.5, 1.8, 1.8])
        with c_ctl1:
            sel_m_idx = st.selectbox("🗓️ Місяць:", options=range(len(month_options)), format_func=lambda i: month_options[i][2], index=2)
            sel_year, sel_month, sel_label = month_options[sel_m_idx]
        with c_ctl2:
            cal_filter = st.radio("Фільтр подій:", ["Всі події", "🎮 Тільки релізи та білди", "🏷️ Тільки розпродажі"], horizontal=True)
        with c_ctl3:
            cal_view_mode = st.radio("Вигляд:", ["📅 Сітка місяця (Google Grid)", "📋 Список подій (Agenda)"], horizontal=True)

        filtered_events = []
        for ev in events_list:
            if cal_filter == "🎮 Тільки релізи та білди" and ev["type"] not in ["release", "build_plan", "lotcheck_passed"]: continue
            if cal_filter == "🏷️ Тільки розпродажі" and ev["type"] not in ["nintendo", "xbox", "deadline"]: continue
            filtered_events.append(ev)

        # GOOGLE CALENDAR GRID
        if cal_view_mode == "📅 Сітка місяця (Google Grid)":
            cal_obj = calendar.Calendar(firstweekday=0)
            month_weeks = cal_obj.monthdatescalendar(sel_year, sel_month)

            cal_parts = []
            cal_parts.append('<div class="cal-container">')
            cal_parts.append(f'''<div style="padding: 12px 18px; background: #1a1a27; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #28283c;">
                <h3 style="margin: 0; color: #fff; font-size: 17px; font-weight: 800;">{sel_label}</h3>
                <div style="font-size: 11px; color: #94a3b8; display: flex; gap: 12px; flex-wrap: wrap;">
                    <span><span style="color:#a855f7;">●</span> Релізи</span>
                    <span><span style="color:#38bdf8;">●</span> Фініш білда Switch</span>
                    <span><span style="color:#10b981;">●</span> Lotcheck Passed</span>
                    <span><span style="color:#ff4d4f;">●</span> Nintendo сейли</span>
                    <span><span style="color:#52c41a;">●</span> Xbox сейли</span>
                </div>
            </div>''')
            cal_parts.append('<div class="cal-header">')
            cal_parts.append('<div class="cal-header-cell">Пн</div><div class="cal-header-cell">Вт</div><div class="cal-header-cell">Ср</div><div class="cal-header-cell">Чт</div><div class="cal-header-cell">Пт</div><div class="cal-header-cell" style="color:#ff6b6b;">Сб</div><div class="cal-header-cell" style="color:#ff6b6b;">Нд</div>')
            cal_parts.append('</div>')
            cal_parts.append('<div class="cal-grid">')

            for week in month_weeks:
                for day in week:
                    is_current_month = (day.month == sel_month)
                    is_today = (day == current_today)
                    cell_classes = ["cal-day-cell"]
                    if not is_current_month: cell_classes.append("other-month")
                    if is_today: cell_classes.append("today")

                    day_events = [e for e in filtered_events if e["date"] == day]
                    events_html = []
                    for dev in day_events[:3]:
                        p_class = "pill-release"
                        if dev["type"] == "build_plan": p_class = "pill-build"
                        elif dev["type"] == "lotcheck_passed": p_class = "pill-passed"
                        elif dev["type"] == "nintendo": p_class = "pill-nintendo"
                        elif dev["type"] == "xbox": p_class = "pill-xbox"
                        elif dev["type"] == "deadline": p_class = "pill-deadline"
                        events_html.append(f'<div class="cal-event-pill {p_class}" title="{dev["desc"]}">{dev["title"]}</div>')

                    if len(day_events) > 3:
                        events_html.append(f'<div style="font-size:9.5px; color:#94a3b8; font-weight:bold; margin-top:2px;">+ ще {len(day_events)-3} подій</div>')

                    joined_events = "".join(events_html)
                    cal_parts.append(f'<div class="{" ".join(cell_classes)}"><div class="cal-day-num">{day.day}</div>{joined_events}</div>')

            cal_parts.append('</div></div>')
            st.markdown("".join(cal_parts), unsafe_allow_html=True)

        else:
            agenda_events = sorted([e for e in filtered_events if e["date"].year == sel_year and e["date"].month == sel_month], key=lambda x: x["date"])
            if agenda_events:
                for a_ev in agenda_events:
                    diff_days = (a_ev["date"] - current_today).days
                    if diff_days == 0: countdown_str = "🔥 СЬОГОДНІ"
                    elif diff_days > 0: countdown_str = f"⏳ Через {diff_days} дн."
                    else: countdown_str = f"Пройшло {-diff_days} дн. тому"

                    b_color = "#a855f7"
                    if a_ev["type"] == "build_plan": b_color = "#38bdf8"
                    elif a_ev["type"] == "lotcheck_passed": b_color = "#10b981"
                    elif a_ev["type"] == "nintendo": b_color = "#e60012"
                    elif a_ev["type"] == "xbox": b_color = "#52c41a"
                    elif a_ev["type"] == "deadline": b_color = "#f59e0b"

                    st.markdown(f"""
                    <div style="background:#171724; border-left: 5px solid {b_color}; border: 1px solid #28283c; border-radius: 8px; padding: 10px 14px; margin-bottom: 7px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <b style="color:#fff; font-size:14px;">{a_ev["title"]}</b>
                            <p style="margin:2px 0 0 0; font-size:12px; color:#94a3b8;">{a_ev["desc"]}</p>
                        </div>
                        <div style="text-align:right;">
                            <span style="font-size:13px; font-weight:700; color:#fff;">{a_ev["date"].strftime('%d.%m.%Y')}</span><br>
                            <span style="font-size:11px; font-weight:bold; color:{'#34d399' if diff_days>=0 else '#64748b'};">{countdown_str}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("💡 У цьому місяці немає подій за обраним фільтром.")

    with c_tab2:
        st.subheader("👨‍💻 Продуктивність та середній час розробників")
        st.caption("Автоматичний розрахунок за живою базою Google Sheets")

        dev_stats = []
        if not calendar_source_df.empty and "Розробник" in calendar_source_df.columns:
            unique_devs = [d for d in calendar_source_df["Розробник"].unique() if str(d).strip() and str(d).lower() != 'nan' and str(d) != "Не вказано"]
        else:
            unique_devs = []

        for dev in unique_devs:
            d_df = calendar_source_df[calendar_source_df["Розробник"] == dev].copy()
            total_proj = len(d_df)

            dev_days_list = []
            for _, row_d in d_df.iterrows():
                f_days = row_d.get("Факт до сабміту", 0)
                if 0 < f_days <= 150:
                    dev_days_list.append(f_days)
                else:
                    s_dt = parse_flexible_date(row_d.get("Дата старту"))
                    b_dt = parse_flexible_date(row_d.get("Switch Білд Дата")) or parse_flexible_date(row_d.get("План фініш Switch"))
                    if s_dt and b_dt and b_dt >= s_dt:
                        calc_d = (b_dt - s_dt).days
                        if 0 < calc_d <= 150: dev_days_list.append(calc_d)

            avg_dev_days = round(sum(dev_days_list) / len(dev_days_list), 1) if dev_days_list else 0.0
            cert_days_list = [d for d in d_df.get("Днів у Lotcheck", []) if 0 < d <= 90]
            avg_cert_days = round(sum(cert_days_list) / len(cert_days_list), 1) if cert_days_list else 0.0
            
            stat_col = d_df.get("Статус Lotcheck", pd.Series())
            passed_cnt = len(d_df[stat_col.astype(str).str.contains("Passed", case=False)]) if not stat_col.empty else 0

            dev_stats.append({
                "Розробник": dev, "Проектів у базі": total_proj, "Прийнято Lotcheck": f"🟢 {passed_cnt} з {total_proj}",
                "Сер. час на порт (днів)": avg_dev_days if avg_dev_days > 0 else "В роботі",
                "Сер. днів у Lotcheck": f"{avg_cert_days} дн." if avg_cert_days > 0 else "—", "Число_днів": avg_dev_days
            })

        stat_table_df = pd.DataFrame(dev_stats)

        if not stat_table_df.empty:
            k_cols = st.columns(min(len(stat_table_df), 4))
            for i, (_, d_row) in enumerate(stat_table_df.iterrows()):
                if i < 4:
                    with k_cols[i]:
                        days_disp = f"{d_row['Сер. час на порт (днів)']} дн." if isinstance(d_row['Сер. час на порт (днів)'], (int, float)) else d_row['Сер. час на порт (днів)']
                        st.markdown(f"""
                        <div class="kpi-card">
                            <div class="kpi-label">РОЗРОБНИК: {d_row['Розробник']}</div>
                            <div class="kpi-value" style="color:#38bdf8 !important;">{days_disp}</div>
                            <span class="kpi-badge badge-ps">Проектів: {d_row['Проектів у базі']}</span>
                            <div style="margin-top:6px; font-size:11.5px; color:#94a3b8;">Lotcheck: {d_row['Сер. днів у Lotcheck']}</div>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown("---")
            c_g1, c_g2 = st.columns([1.5, 1])
            with c_g1:
                st.subheader("📊 Порівняння: Швидкість здачі портів (дні)")
                valid_chart_df = stat_table_df[stat_table_df["Число_днів"] > 0]
                if not valid_chart_df.empty:
                    fig_dev = px.bar(
                        valid_chart_df, x="Розробник", y="Число_днів", text="Число_днів",
                        color="Розробник", color_discrete_sequence=["#38bdf8", "#a855f7", "#10b981", "#f59e0b"]
                    )
                    fig_dev.update_traces(texttemplate='%{text:.1f} дн.', textposition='outside')
                    fig_dev.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), height=320, yaxis_title="Середня кількість днів")
                    st.plotly_chart(fig_dev, use_container_width=True)

            with c_g2:
                st.subheader("📋 Зведення по команді")
                st.dataframe(
                    stat_table_df[["Розробник", "Проектів у базі", "Прийнято Lotcheck", "Сер. час на порт (днів)", "Сер. днів у Lotcheck"]],
                    hide_index=True, use_container_width=True, height=280
                )
        else:
            st.info("💡 Дані про розробників з'являться після підключення повної таблиці виробництва.")

# ==============================================================================
# 📅 РОЗДІЛ 3: ПОМІСЯЧНА ДИНАМІКА
# ==============================================================================
elif app_mode == "📅 Помісячна динаміка (Monthly)":
    st.title("📅 Помісячна виручка та Cashflow портфоліо ($ USD)")
    st.caption("Автоматичне зчитування з Google Таблиць • Конвертація валют • Дедуплікація та аналіз")

    with st.expander("⚙️ Джерела даних помісячних звітів (Google Sheets)", expanded=False):
        c_src1, c_src2 = st.columns(2)
        custom_nintendo_url = c_src1.text_input("URL Таблиці Nintendo Monthly:", NINTENDO_MONTHLY_SHEET_URL)
        custom_xbox_url = c_src2.text_input("URL Таблиці Xbox Monthly:", XBOX_MONTHLY_SHEET_URL)
        if st.button("🔄 Оновити дані помісячних звітів"):
            st.cache_data.clear()
            st.rerun()

    active_nintendo_raw = load_nintendo_monthly_from_sheet(custom_nintendo_url)
    active_xbox_raw = load_xbox_monthly_from_sheet(custom_xbox_url)

    n_matrix_df, n_months, _ = parse_nintendo_monthly_data(active_nintendo_raw)
    x_matrix_df, x_months = parse_xbox_monthly_data(active_xbox_raw)
    c_matrix_df, c_months = combine_monthly_matrices(n_matrix_df, x_matrix_df, n_months, x_months)

    selected_platform_mode = st.radio("Оберіть платформу:", ["🔴 Nintendo eShop", "🟢 Xbox Store", "🌐 Всі консолі (Switch + Xbox)"], horizontal=True)

    if selected_platform_mode == "🔴 Nintendo eShop":
        active_matrix_df, active_month_labels, store_accent_color = n_matrix_df, n_months, "#e60012"
    elif selected_platform_mode == "🟢 Xbox Store":
        active_matrix_df, active_month_labels, store_accent_color = x_matrix_df, x_months, "#107c10"
    else:
        active_matrix_df, active_month_labels, store_accent_color = c_matrix_df, c_months, "#d946ef"

    if not active_matrix_df.empty and active_month_labels:
        st.markdown("---")
        filter_mode = st.radio("Режим фільтрації:", ["🗓️ Один місяць", "↔️ Діапазон місяців (Слайдер)", "🎯 Довільний вибір (Мультиселект)", "📅 Всі місяці"], horizontal=True)

        if filter_mode == "🗓️ Один місяць":
            active_selected_months = [st.selectbox("Оберіть місяць:", options=active_month_labels, index=len(active_month_labels)-1)]
        elif filter_mode == "↔️ Діапазон місяців (Слайдер)":
            start_m, end_m = st.select_slider("Діапазон:", options=active_month_labels, value=(active_month_labels[max(0, len(active_month_labels)-6)], active_month_labels[-1]))
            s_idx, e_idx = active_month_labels.index(start_m), active_month_labels.index(end_m)
            active_selected_months = active_month_labels[min(s_idx, e_idx):max(s_idx, e_idx)+1]
        elif filter_mode == "🎯 Довільний вибір (Мультиселект)":
            active_selected_months = st.multiselect("Місяці:", options=active_month_labels, default=[active_month_labels[-1]])
            if not active_selected_months: active_selected_months = [active_month_labels[-1]]
        else:
            active_selected_months = active_month_labels

        display_period_df = active_matrix_df[["Назва гри / DLC"] + active_selected_months].copy()
        display_period_df["Виторг за період ($)"] = display_period_df[active_selected_months].sum(axis=1)
        display_period_df["All-Time ($)"] = active_matrix_df["Всього ($)"]
        display_period_df = display_period_df[display_period_df["Виторг за період ($)"] > 0].sort_values(by="Виторг за період ($)", ascending=False).reset_index(drop=True)
        total_period_rev = float(display_period_df["Виторг за період ($)"].sum()) if not display_period_df.empty else 0.0

        p_c1, p_c2, p_c3, p_c4 = st.columns(4)
        p_c1.markdown(f'<div class="kpi-card"><div class="kpi-label">Виторг за період</div><div class="kpi-value">${total_period_rev:,.2f}</div><span class="kpi-badge badge-total">{len(active_selected_months)} міс. вибрано</span></div>', unsafe_allow_html=True)
        p_c2.markdown(f'<div class="kpi-card"><div class="kpi-label">Активних тайтлів</div><div class="kpi-value">{len(display_period_df)}</div><span class="kpi-badge badge-ps">З продажами</span></div>', unsafe_allow_html=True)
        p_c3.markdown(f'<div class="kpi-card"><div class="kpi-label">Лідер періоду</div><div class="kpi-value" style="font-size:16px; color:#38bdf8 !important;">{display_period_df.iloc[0]["Назва гри / DLC"] if not display_period_df.empty else "—"}</div><span class="kpi-badge badge-xbox">${display_period_df.iloc[0]["Виторг за період ($)"] if not display_period_df.empty else 0:,.2f}</span></div>', unsafe_allow_html=True)
        p_c4.markdown(f'<div class="kpi-card"><div class="kpi-label">Каса All-Time</div><div class="kpi-value">${active_matrix_df["Всього ($)"].sum():,.2f}</div><span class="kpi-badge badge-switch">Повна база</span></div>', unsafe_allow_html=True)

        m_tab1, m_tab2, m_tab3 = st.tabs(["📊 Топ тайтли та Звіт", "📑 Повна матриця ($)", "🔥 Теплова карта та Тренди"])
        with m_tab1:
            if not display_period_df.empty:
                top10_period = display_period_df.head(10)
                fig_p_bar = px.bar(top10_period, x="Виторг за період ($)", y="Назва гри / DLC", orientation="h", text="Виторг за період ($)", color_discrete_sequence=[store_accent_color])
                fig_p_bar.update_traces(texttemplate='$%{text:,.2f}', textposition='outside')
                fig_p_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), height=380, yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_p_bar, use_container_width=True)

            format_cfg_period = {"Виторг за період ($)": st.column_config.NumberColumn("Виторг ($)", format="$%.2f"), "All-Time ($)": st.column_config.NumberColumn("All-Time ($)", format="$%.2f")}
            for m_col in active_selected_months: format_cfg_period[m_col] = st.column_config.NumberColumn(m_col, format="$%.2f")
            st.dataframe(display_period_df, column_config=format_cfg_period, use_container_width=True, height=400)

        with m_tab2:
            format_cfg_all = {"Всього ($)": st.column_config.NumberColumn("Всього ($)", format="$%.2f")}
            for m_col in active_month_labels: format_cfg_all[m_col] = st.column_config.NumberColumn(m_col, format="$%.2f")
            st.dataframe(active_matrix_df, column_config=format_cfg_all, use_container_width=True, height=480)

        with m_tab3:
            top_heatmap_df = active_matrix_df.head(20).set_index("Назва гри / DLC")[active_month_labels]
            fig_heat = px.imshow(top_heatmap_df, labels=dict(x="Місяць", y="Гра", color="Виторг ($)"), x=active_month_labels, y=top_heatmap_df.index, color_continuous_scale="Purples", aspect="auto")
            fig_heat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), height=480)
            st.plotly_chart(fig_heat, use_container_width=True)

# ==============================================================================
# 🚀 РОЗДІЛ 4: RELEASE PIPELINE
# ==============================================================================
elif app_mode == "🚀 Release Pipeline":
    st.title("🚀 Console Release Pipeline & Lotcheck Tracker")
    st.caption("Повний цикл виробництва консольних портів • Пряма синхронізація з Google Таблицею • Контроль зриву дедлайнів")

    pipeline_df = sheet_pipeline_df if not sheet_pipeline_df.empty else load_pipeline_master_data()
    if pipeline_df.empty:
        pipeline_df = get_empty_pipeline_df()

    if not pipeline_df.empty and "Факт до сабміту" in pipeline_df.columns and "Плановий строк" in pipeline_df.columns:
        overrun_projects = pipeline_df[(pipeline_df["Факт до сабміту"] > pipeline_df["Плановий строк"]) & (pipeline_df["Плановий строк"] > 0)]
    else:
        overrun_projects = pd.DataFrame()

    stat_lot = pipeline_df.get("Статус Lotcheck", pd.Series())
    in_dev_count = len(pipeline_df[stat_lot.astype(str).str.contains("Development|testing", case=False)]) if not stat_lot.empty else 0
    in_cert_count = len(pipeline_df[stat_lot.astype(str).str.contains("Submitted", case=False)]) if not stat_lot.empty else 0
    passed_count = len(pipeline_df[stat_lot.astype(str).str.contains("Passed", case=False)]) if not stat_lot.empty else 0

    p_k1, p_k2, p_k3, p_k4 = st.columns(4)
    p_k1.markdown(f'<div class="kpi-card"><div class="kpi-label">🛠️ В розробці / QA</div><div class="kpi-value">{in_dev_count}</div><span class="kpi-badge badge-total">Всього: {len(pipeline_df)} проектів</span></div>', unsafe_allow_html=True)
    p_k2.markdown(f'<div class="kpi-card"><div class="kpi-label">⏳ На сертифікації (Lotcheck)</div><div class="kpi-value" style="color:#38bdf8 !important;">{in_cert_count}</div><span class="kpi-badge badge-ps">Чекають відповіді</span></div>', unsafe_allow_html=True)
    p_k3.markdown(f'<div class="kpi-card"><div class="kpi-label">🟢 Сертифіковано (Passed)</div><div class="kpi-value" style="color:#4ade80 !important;">{passed_count}</div><span class="kpi-badge badge-xbox">Готові до релізу</span></div>', unsafe_allow_html=True)
    p_k4.markdown(f'<div class="kpi-card"><div class="kpi-label">🚨 ЗРИВ СТРОКІВ (Факт > План)</div><div class="kpi-value" style="color:#ef4444 !important;">{len(overrun_projects)}</div><span class="kpi-badge badge-switch">Потребують уваги</span></div>', unsafe_allow_html=True)

    if not overrun_projects.empty:
        for _, o_row in overrun_projects.iterrows():
            delay_days = int(o_row.get('Факт до сабміту', 0) - o_row.get('Плановий строк', 0))
            st.markdown(f"""
            <div class="alert-card-red">
                <b style="color:#fff; font-size:15px;">🎮 {o_row.get('Гра', 'Проект')} ({o_row.get('Розробник', 'Девелопер')})</b> ➔ 
                <span style="color:#f87171; font-weight:bold;">План: {o_row.get('Плановий строк', 0)} дн. | Факт: {o_row.get('Факт до сабміту', 0)} дн. (🔴 +{delay_days} днів затримки!)</span>
            </div>
            """, unsafe_allow_html=True)

    display_cols = [c for c in ["Гра", "Розробник", "Художник", "Дата релізу", "Плановий строк", "Факт до сабміту", "Статус Lotcheck", "Switch", "Xbox", "PlayStation", "Нюанси"] if c in pipeline_df.columns]
    if not pipeline_df.empty and display_cols:
        st.dataframe(pipeline_df[display_cols], hide_index=True, use_container_width=True, height=480)
    else:
        st.info("💡 Немає даних для відображення пайплайну.")

# ==============================================================================
# 📋 РОЗДІЛ 5: RELEASE ACTIVITY
# ==============================================================================
elif app_mode == "📋 Release Activity":
    st.title("📋 Release Marketing & Launch Activity Hub")
    st.caption("Маркетинговий чек-лист підготовки до релізів • Джерело правди: Google Sheets")

    active_act_source = ACTIVITY_SHEET_URL if ACTIVITY_SHEET_URL else GOOGLE_SHEET_URL
    sheet_data = load_activity_from_sheet(active_act_source)
    base_df = sheet_data if not sheet_data.empty else raw_df.copy()

    act_title_col = next((c for c in base_df.columns if any(k in c.lower() for k in ["title", "гра", "game", "назва"])), base_df.columns[0])
    act_date_col = next((c for c in base_df.columns if any(k in c.lower() for k in ["release date", "release", "date", "дата"])), None)
    act_status_col = next((c for c in base_df.columns if "status" in c.lower() or "статус" in c.lower()), None)

    activity_rows = []
    for _, r in base_df.iterrows():
        g_name = str(r.get(act_title_col, "")).strip()
        if not g_name or g_name.lower() == 'nan': continue
        raw_d = r.get(act_date_col, "—")
        raw_stat = str(r.get(act_status_col, "In Progress")).strip()
        status_badge = "🟢 Done" if ("released" in raw_stat.lower() or "done" in raw_stat.lower()) else "🟡 In Progress"

        row_item = {"Гра": g_name, "Дата релізу": str(raw_d), "Статус": status_badge}
        checked_count = 0
        for task in ACTIVITY_CHECKBOX_COLS:
            is_done = is_truthy(r.get(task, False))
            row_item[task] = is_done
            if is_done: checked_count += 1

        row_item["Готовність (%)"] = int(round((checked_count / len(ACTIVITY_CHECKBOX_COLS)) * 100))
        activity_rows.append(row_item)

    act_df = pd.DataFrame(activity_rows)
    if not act_df.empty:
        col_view_config = {
            "Гра": st.column_config.TextColumn("Назва гри (Title)", width="medium"),
            "Дата релізу": st.column_config.TextColumn("Дата релізу", width="small"),
            "Статус": st.column_config.TextColumn("Статус", width="small"),
            "Готовність (%)": st.column_config.ProgressColumn("Готовність маркетингу", format="%d%%", min_value=0, max_value=100, width="medium")
        }
        for task in ACTIVITY_CHECKBOX_COLS: col_view_config[task] = st.column_config.CheckboxColumn(task, width="small", disabled=True)
        st.dataframe(act_df[["Гра", "Дата релізу", "Статус", "Готовність (%)"] + ACTIVITY_CHECKBOX_COLS], column_config=col_view_config, hide_index=True, use_container_width=True, height=520)

# ==============================================================================
# 🎯 РОЗДІЛ 6: ЦІЛІ ТА KPI 2026
# ==============================================================================
elif app_mode == "🎯 Цілі та KPI 2026":
    st.title("🎯 Виконання річного та квартальних планів (2026)")
    st.caption("Ціль на 2026 рік: **$500,000 консольної виручки** • Дані синхронізуються з Weekly Updates")

    q_df = prepare_quarterly_data(weekly_df)
    period_choice = st.radio("📌 Період:", ["Year 2026 (Весь рік)", "Q1 2026", "Q2 2026", "Q3 2026", "Q4 2026"], horizontal=True)
    target = TARGETS_2026[period_choice]

    if not q_df.empty:
        if period_choice == "Year 2026 (Весь рік)": fact_period_df = q_df[q_df["Year"] == 2026]
        else: fact_period_df = q_df[q_df["Quarter"] == period_choice.split(" ")[0] + " 2026"]
        fact_rev = float(fact_period_df["Total_Revenue"].sum()) if not fact_period_df.empty else 0.0
        fact_sw = float(fact_period_df["Nintendo_Revenue"].sum()) if not fact_period_df.empty else 0.0
        fact_ps = float(fact_period_df["PS_Revenue"].sum()) if not fact_period_df.empty else 0.0
        fact_xb = float(fact_period_df["Xbox_Revenue"].sum()) if not fact_period_df.empty else 0.0
    else:
        fact_rev, fact_sw, fact_ps, fact_xb = 0.0, 0.0, 0.0, 0.0

    rev_pct = round((fact_rev / max(target["Revenue"], 1.0)) * 100, 1)

    st.markdown(f"""
    <div style="background:#171724; border:1px solid #2f2f45; border-radius:12px; padding:22px; margin-top:10px; margin-bottom:15px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="font-size:12px; font-weight:600; color:#94a3b8; text-transform:uppercase;">ФІНАНСОВИЙ ТАРГЕТ</span>
                <h2 style="margin:2px 0 0 0; color:#ffffff;">💰 Виручка: ${fact_rev:,.2f} <span style="font-size:18px; color:#94a3b8; font-weight:normal;">/ ${target['Revenue']:,.0f}</span></h2>
            </div>
            <div style="text-align:right;">
                <span style="font-size:28px; font-weight:800; color:{'#10b981' if rev_pct >= 80 else ('#f59e0b' if rev_pct >= 40 else '#ef4444')};">{rev_pct}%</span>
                <p style="margin:0; font-size:12px; color:#94a3b8;">виконання плану</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(min(rev_pct / 100.0, 1.0))

    k1, k2, k3 = st.columns(3)
    k1.metric("🔴 Nintendo Switch", f"${fact_sw:,.0f}", f"{(fact_sw/max(target['Nintendo_Revenue'],1.0))*100:.1f}% від цілі")
    k2.metric("🔵 PlayStation", f"${fact_ps:,.0f}", f"{(fact_ps/max(target['PS_Revenue'],1.0))*100:.1f}% від цілі")
    k3.metric("🟢 Xbox", f"${fact_xb:,.0f}", f"{(fact_xb/max(target['Xbox_Revenue'],1.0))*100:.1f}% від цілі")

# ==============================================================================
# 📈 РОЗДІЛ 7: ТИЖНЕВА ДИНАМІКА (WoW)
# ==============================================================================
elif app_mode == "📈 Тижнева динаміка (WoW)":
    st.title("📈 Тижневий пульс видавництва (Week-over-Week)")
    st.caption("Динаміка консольних зборів, вішлістів, повна воронка лідогенерації та соцмережі")

    if not weekly_df.empty:
        w_tab1, w_tab2, w_tab3, w_tab4 = st.tabs(["💰 Консольний виторг & Продажі", "🎯 BizDev Воронка & Конверсії", "📱 Маркетинг & Аудиторія", "📑 Повна таблиця"])
        with w_tab1:
            rev_chart_df = []
            for _, rw in weekly_df.iterrows():
                lbl = f"{rw.get('From', '')}"
                rev_chart_df.append({"Week": lbl, "Platform": "PlayStation", "Revenue": rw.get("PS_Revenue", 0.0)})
                rev_chart_df.append({"Week": lbl, "Platform": "Nintendo Switch", "Revenue": rw.get("Nintendo_Revenue", 0.0)})
                rev_chart_df.append({"Week": lbl, "Platform": "Xbox", "Revenue": rw.get("Xbox_Revenue", 0.0)})
            fig_w_rev = px.bar(pd.DataFrame(rev_chart_df), x="Week", y="Revenue", color="Platform", barmode="group", color_discrete_map={"Nintendo Switch": "#e60012", "PlayStation": "#3b82f6", "Xbox": "#107c10"})
            fig_w_rev.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), yaxis_title="Виторг ($)")
            st.plotly_chart(fig_w_rev, use_container_width=True)

        with w_tab2:
            tot_leads = float(weekly_df["Leads"].sum()) if "Leads" in weekly_df.columns else 0.0
            tot_seq = float(weekly_df["Sequence_Started"].sum()) if "Sequence_Started" in weekly_df.columns else 0.0
            tot_contacts = float(weekly_df["Contacts"].sum()) if "Contacts" in weekly_df.columns else 0.0
            tot_opps = float(weekly_df["Opportunities"].sum()) if "Opportunities" in weekly_df.columns else 0.0
            tot_calls = float(weekly_df["Calls"].sum()) if "Calls" in weekly_df.columns else 0.0
            tot_deals = float(weekly_df["Deals"].sum()) if "Deals" in weekly_df.columns else 0.0

            fig_funnel = go.Figure(go.Funnel(
                y=["1. Leads", "2. Sequence", "3. Contacts", "4. Opportunities", "5. Calls", "6. Deals"],
                x=[tot_leads, tot_seq if tot_seq > 0 else tot_leads*0.8, tot_contacts, tot_opps if tot_opps > 0 else tot_contacts*0.7, tot_calls, tot_deals],
                textinfo="value+percent initial", marker=dict(color=["#6366f1", "#8b5cf6", "#a855f7", "#d946ef", "#f59e0b", "#10b981"])
            ))
            fig_funnel.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), height=380)
            st.plotly_chart(fig_funnel, use_container_width=True)

        with w_tab3:
            social_cols = [c for c in ["Twitter", "TikTok", "YouTube", "Discord", "Instagram"] if c in weekly_df.columns]
            if social_cols:
                fig_social = px.line(weekly_df, x="From", y=social_cols, markers=True)
                fig_social.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), yaxis_title="Підписників")
                st.plotly_chart(fig_social, use_container_width=True)

        with w_tab4:
            st.dataframe(weekly_df, use_container_width=True, height=450)

# ==============================================================================
# 🧮 РОЗДІЛ 8: КАЛЬКУЛЯТОР ПРОГНОЗІВ
# ==============================================================================
elif app_mode == "🧮 Калькулятор прогнозів":
    st.title("🧮 Sourcing & Lead Forecasting Hub")
    st.caption("Оцінка нових лідів за відкаліброваними 30 піджанрами та формування пайплайну")

    calc_tab1, calc_tab2 = st.tabs(["🧮 Інтерактивний калькулятор ліда", "📋 Сформований пайплайн"])
    with calc_tab1:
        sb_left, sb_right = st.columns([1, 1.25])
        with sb_left:
            st.markdown('<div class="sandbox-box">', unsafe_allow_html=True)
            calc_name = st.text_input("Назва гри / ліда:", "Project Prototype")
            calc_link = st.text_input("🔗 Посилання на гру:", "https://store.steampowered.com/app/...")
            calc_src = st.selectbox("Джерело аналізу:", ["Steam", "Google Play", "CrazyGames / Web", "itch.io"])
            
            if calc_src == "Steam":
                s_rev = st.number_input("Steam Revenue ($):", min_value=0, value=6000, step=1000)
                b_metric = (s_rev * 0.10) + 500.0
            elif calc_src == "Google Play":
                gp_installs = st.number_input("Installs Google Play:", min_value=0, value=500000, step=50000)
                b_metric = (math.sqrt(gp_installs) * 2.0) + 800.0 if gp_installs > 0 else 0.0
            elif calc_src == "CrazyGames / Web":
                cg_r = st.number_input("Reviews / Plays:", min_value=0, value=3500, step=500)
                b_metric = (cg_r * 0.05) + 900.0
            else:
                itch_r = st.number_input("Ratings itch.io:", min_value=0, value=40, step=5)
                b_metric = (itch_r * 10.0) + 400.0

            calc_genre = st.selectbox("Точний піджанр:", list(GENRE_DATABASE.keys()))
            calc_price = st.selectbox("Планова ціна на консолях ($):", list(PRICE_MODIFIERS.keys()), index=4)
            st.markdown('</div>', unsafe_allow_html=True)

        g_cfg = GENRE_DATABASE[calc_genre]
        p_mod = PRICE_MODIFIERS.get(calc_price, 1.0)
        ps_est = b_metric * g_cfg["PS"] * p_mod
        ns_est = b_metric * g_cfg["Switch"] * p_mod
        xb_est = b_metric * g_cfg["Xbox"] * p_mod
        tot_m1 = ps_est + ns_est + xb_est
        tot_year = tot_m1 * g_cfg["Decay"]

        with sb_right:
            st.markdown('<div class="sandbox-box">', unsafe_allow_html=True)
            st.markdown(f"### 📈 Розрахунок: **{calc_name}**")
            st.caption(f"Органічна база: **${b_metric:,.1f}** | Множник: **{p_mod}x**")
            
            m_c1, m_c2, m_c3 = st.columns(3)
            m_c1.metric("PlayStation (M1)", f"${ps_est:,.0f}")
            m_c2.metric("Switch (M1)", f"${ns_est:,.0f}")
            m_c3.metric("Xbox (M1)", f"${xb_est:,.0f}")

            t_c1, t_c2 = st.columns(2)
            t_c1.metric("🔥 Gross M1", f"${tot_m1:,.0f}", f"Дохід: ${tot_m1*0.315:,.0f}")
            t_c2.metric("📅 Річний Gross", f"${tot_year:,.0f}", f"Дохід: ${tot_year*0.315:,.0f}")

            if st.button("➕ Зберегти лід", use_container_width=True):
                new_lead = {"Дата": datetime.now().strftime("%Y-%m-%d %H:%M"), "Назва гри": calc_name, "Посилання": calc_link, "Жанр": calc_genre, "Total M1 ($)": round(tot_m1, 1)}
                st.session_state.scouted_leads.append(new_lead)
                st.toast(f"✅ Лід '{calc_name}' збережено!")
            st.markdown('</div>', unsafe_allow_html=True)

    with calc_tab2:
        if st.session_state.scouted_leads:
            st.dataframe(pd.DataFrame(st.session_state.scouted_leads), use_container_width=True)
        else:
            st.info("💡 Таблиця лідів порожня. Розрахуй гру у вкладці калькулятора та натисни '➕ Зберегти лід'.")
