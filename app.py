import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
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
XBOX_MONTHLY_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?gid=1981339676#gid=1981339676"  # Встав посилання на вкладку Xbox (або залиш порожнім для введення в інтерфейсі)
PIPELINE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?usp=sharing"
ACTIVITY_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?gid=962012405#gid=962012405"      # Встав посилання на вкладку Release Activity в Google Sheets (з #gid=...)
GOOGLE_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzrYmeab3xtC4TW9id-N60pI6UmOk6OJj7L2OebkV48omIzqD_h827g3C1mSUpt_WusyA/exec"
ANTHROPIC_API_KEY = ""       # Залиш порожнім або додай у Secrets

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

# 🎨 ВИПРАВЛЕНИЙ ТА ЗАХИЩЕНИЙ CSS (ІДЕАЛЬНИЙ САЙДБАР БЕЗ ЗСУВІВ)
st.markdown("""
<style>
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
    
    /* Захист сайдбару від обрізання та ідеальні відступи */
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem !important;
    }
    
    /* Повне і безкомпромісне приховування кружечків радіо-кнопок */
    section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child,
    section[data-testid="stSidebar"] div[role="radiogroup"] input[type="radio"],
    section[data-testid="stSidebar"] [data-testid="stRadioButtonCustom"] {
        display: none !important;
        width: 0 !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Стилізація інтерактивних плашок меню */
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background-color: #171724 !important;
        border: 1px solid #28283c !important;
        border-radius: 9px !important;
        padding: 10px 14px !important;
        margin-bottom: 7px !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: #222235 !important;
        border-color: #a855f7 !important;
        transform: translateX(3px);
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"],
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(90deg, rgba(192, 38, 211, 0.25) 0%, rgba(249, 115, 22, 0.18) 100%) !important;
        border: 1px solid #d946ef !important;
        box-shadow: 0 2px 10px rgba(217, 70, 239, 0.18) !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] p,
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
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
    .blocker-box { background: #201319; border-left: 4px solid #ef4444; border: 1px solid #3f1a24; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px; }
    .alert-card-red { background: linear-gradient(135deg, #2d141e 0%, #1c0d13 100%); border: 1px solid #7f1d1d; border-left: 5px solid #ef4444; border-radius: 10px; padding: 14px; margin-bottom: 12px; }
    .alert-card-yellow { background: linear-gradient(135deg, #2d2414 0%, #1c170d 100%); border: 1px solid #854d0e; border-left: 5px solid #eab308; border-radius: 10px; padding: 14px; margin-bottom: 12px; }
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
    {"name": "1. Autumn Sale", "start": "2026-09-11", "end": "2026-09-24", "status": "🔥 Найближчий", "region": "Global / EU / US"},
    {"name": "2. Halloween Sale", "start": "2026-10-26", "end": "2026-11-15", "status": "🎃 Сезонний", "region": "Global"},
    {"name": "3. Holiday Sale (EU)", "start": "2026-12-17", "end": "2027-01-10", "status": "🎄 Головний (EU)", "region": "Europe / Australia"},
    {"name": "4. Holiday Sale (US)", "start": "2026-12-21", "end": "2027-01-11", "status": "🎄 Головний (US)", "region": "Americas"}
]

XBOX_SCHEDULE = [
    {
        "name": "Deep Discounts Sale (ID Sale)",
        "start": "2026-11-05", "end": "2026-11-11", "deadline": "2026-10-01", "feedback": "2026-10-14",
        "limit": 10, "min_price": 0.0, "min_discount": 65, "type": "ID Sale (Глибокі знижки)",
        "note": "Знижка 65% або більше. Ліміт: до 10 тайтлів."
    },
    {
        "name": "Black Friday Sale (Tentpole Store Sale)",
        "start": "2026-11-20", "end": "2026-12-02", "deadline": "2026-10-02", "feedback": "2026-10-15",
        "limit": 5, "min_price": 9.99, "min_discount": 10, "type": "Tentpole Sale",
        "note": "Базова ціна від $9.99. Ліміт: до 5 тайтлів. Кулдаун знято тільки між BF та Countdown."
    },
    {
        "name": "Countdown Sale (Tentpole Store Sale)",
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
# ⚙️ 3. ВСІ ДОПОМІЖНІ ФУНКЦІЇ ТА ПАРСЕРИ
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
    d_str = str(d_val).strip()
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

# Парсер щомісячних звітів Nintendo eShop з авто-злиттям японських тайтлів
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
                if base_code not in code_to_english_map:
                    code_to_english_map[base_code] = raw_name
                if t_code not in code_to_english_map:
                    code_to_english_map[t_code] = raw_name

    def format_month_label(c_str):
        try:
            parts = c_str.split("/")
            m = int(parts[0])
            y = 2000 + int(parts[2])
            if 1 <= m <= 12:
                return f"{UKR_MONTH_NAMES[m]} {y}"
        except:
            pass
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
            if t_code in code_to_english_map:
                final_item_name = code_to_english_map[t_code]
            elif base_code in code_to_english_map:
                final_item_name = code_to_english_map[base_code]

        curr = str(row.get(curr_col, "USD")).strip().upper()
        fx = FX_RATES.get(curr, 1.0)
        cost = clean_num_val(row.get(cost_col, 0.0))
        
        row_dict = {"Назва гри / DLC": final_item_name}
        for d_col in date_cols:
            units = clean_num_val(row.get(d_col, 0.0))
            rev_usd = units * cost * fx
            row_dict[d_col] = rev_usd
        processed_records.append(row_dict)
        
    proc_df = pd.DataFrame(processed_records)
    if proc_df.empty:
        return pd.DataFrame(), [], {}
        
    grouped = proc_df.groupby("Назва гри / DLC")[date_cols].sum().reset_index()
    grouped["Всього ($)"] = grouped[date_cols].sum(axis=1)
    grouped = grouped.sort_values(by="Всього ($)", ascending=False).reset_index(drop=True)
    
    grouped_renamed = grouped.rename(columns=month_label_map)
    ordered_month_labels = [month_label_map[c] for c in date_cols]
    
    return grouped_renamed, ordered_month_labels, month_label_map

# Парсер потранзакційного звіту Xbox Store
def parse_xbox_monthly_data(df_raw):
    if df_raw.empty:
        return pd.DataFrame(), []
    
    title_col = next((c for c in df_raw.columns if c.lower().strip() in ["titlename", "parentproductname", "назва", "title"]), None)
    date_col = next((c for c in df_raw.columns if "datestamp" in c.lower().strip() or c.lower().strip() == "date"), None)
    usd_col = next((c for c in df_raw.columns if "purchasepriceusdamount" in c.lower().strip() or "priceusdamount" in c.lower().strip()), None)
    
    if not title_col or not date_col or not usd_col:
        return pd.DataFrame(), []

    records = []
    for _, r in df_raw.iterrows():
        t_name = str(r.get(title_col, "")).strip()
        if not t_name or t_name.lower() == 'nan':
            continue
        
        dt_val = parse_flexible_date(r.get(date_col))
        if not dt_val:
            continue
        
        usd_val = clean_num_val(r.get(usd_col, 0.0))
        m_label = f"{UKR_MONTH_NAMES[dt_val.month]} {dt_val.year}"
        sort_key = (dt_val.year, dt_val.month)
        
        records.append({
            "Назва гри / DLC": t_name,
            "SortKey": sort_key,
            "Month": m_label,
            "USD": usd_val
        })
        
    if not records:
        return pd.DataFrame(), []
        
    df_rec = pd.DataFrame(records)
    unique_months = df_rec[["SortKey", "Month"]].drop_duplicates().sort_values(by="SortKey")
    ordered_month_labels = unique_months["Month"].tolist()
    
    pivot = df_rec.pivot_table(index="Назва гри / DLC", columns="Month", values="USD", aggfunc="sum", fill_value=0.0).reset_index()
    existing_months = [m for m in ordered_month_labels if m in pivot.columns]
    pivot = pivot[["Назва гри / DLC"] + existing_months]
    pivot["Всього ($)"] = pivot[existing_months].sum(axis=1)
    pivot = pivot.sort_values(by="Всього ($)", ascending=False).reset_index(drop=True)
    
    return pivot, existing_months

# Злиття матриць Nintendo + Xbox
def combine_monthly_matrices(n_matrix, x_matrix, n_months, x_months):
    if n_matrix.empty and x_matrix.empty:
        return pd.DataFrame(), []
    if n_matrix.empty:
        return x_matrix.copy(), x_months
    if x_matrix.empty:
        return n_matrix.copy(), n_months

    month_to_dt = {}
    for m in set(n_months + x_months):
        try:
            parts = m.split(" ")
            m_idx = UKR_MONTH_NAMES.index(parts[0])
            y = int(parts[1])
            month_to_dt[m] = datetime(y, m_idx, 1)
        except:
            month_to_dt[m] = datetime(2000, 1, 1)

    all_sorted_months = sorted(list(month_to_dt.keys()), key=lambda x: month_to_dt[x])
    combined_data = {}

    def ingest_matrix(df_in, m_cols):
        for _, row in df_in.iterrows():
            g_name = str(row["Назва гри / DLC"]).strip()
            if g_name not in combined_data:
                combined_data[g_name] = {m: 0.0 for m in all_sorted_months}
            for mc in m_cols:
                if mc in row:
                    combined_data[g_name][mc] += clean_num_val(row[mc])

    ingest_matrix(n_matrix, n_months)
    ingest_matrix(x_matrix, x_months)

    rows_out = []
    for g_name, m_dict in combined_data.items():
        r = {"Назва гри / DLC": g_name}
        r.update(m_dict)
        r["Всього ($)"] = sum(m_dict.values())
        rows_out.append(r)

    c_df = pd.DataFrame(rows_out).sort_values(by="Всього ($)", ascending=False).reset_index(drop=True)
    return c_df, all_sorted_months

# Нормалізатор таблиці Release Pipeline
def normalize_pipeline_dataframe(df_in):
    if df_in.empty:
        return pd.DataFrame()
    
    df = df_in.copy()
    rename_rules = {
        "Игра": "Гра", "Title": "Гра", "Game": "Гра",
        "Разработчик": "Розробник", "Developer": "Розробник", "Dev": "Розробник",
        "Художник": "Художник", "Artist": "Художник",
        "Нюансы": "Нюанси", "Notes": "Нюанси",
        "Дата старта": "Дата старту", "Start Date": "Дата старту",
        "Планируемая дата финиша": "Планова дата", "Finish Date": "Планова дата",
        "Планируемый срок": "Плановий строк", "Plan Days": "Плановий строк",
        "Фактический срок (до сертификации Нинтендо)": "Факт до сабміту", "Fact Days": "Факт до сабміту",
        "Статус сертификации": "Статус Lotcheck", "Lotcheck Status": "Статус Lotcheck",
        "Nintendo Switch": "Switch", "Nintendo Switch релизный билд загружен Дата": "Switch Білд Дата",
        "Nintendo Switch релизный принят, дата и с которого раза": "Прийнято Lotcheck",
        "Длительность прохождения сертификации": "Днів у Lotcheck",
        "С какого раза принята сертификация": "Спроби Lotcheck",
        "XBox": "Xbox", "XBox концепт отправлен": "Xbox Концепт", "XBox TLA отправлен": "Xbox TLA",
        "Play Station": "PlayStation", "PS продукт создан": "PS Продукт",
        "Трейлеры все готовы": "Трейлер", "Трейлер": "Трейлер",
        "Картинки предоставлены": "Картинки", "Картинки": "Картинки",
        "Текстовые ресурсы предоставлены": "Тексти", "Тексти": "Тексти"
    }
    
    for old_k, new_k in rename_rules.items():
        if old_k in df.columns and new_k not in df.columns:
            df.rename(columns={old_k: new_k}, inplace=True)
            
    if "Гра" not in df.columns and not df.empty:
        df.rename(columns={df.columns[0]: "Гра"}, inplace=True)

    defaults = {
        "Гра": "Unknown Project", "Розробник": "Не вказано", "Художник": "",
        "Нюанси": "", "Дата старту": "", "Планова дата": "",
        "Плановий строк": 0, "Факт до сабміту": 0,
        "Трейлер": False, "Картинки": False, "Тексти": False,
        "Switch": True, "Switch Білд Дата": "", "Статус Lotcheck": "In Development",
        "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "",
        "Xbox": False, "Xbox Концепт": False, "Xbox TLA": False,
        "PlayStation": False, "PS Продукт": False
    }

    for col_name, def_val in defaults.items():
        if col_name not in df.columns:
            df[col_name] = def_val

    df["Плановий строк"] = pd.to_numeric(df["Плановий строк"], errors="coerce").fillna(0).astype(int)
    df["Факт до сабміту"] = pd.to_numeric(df["Факт до сабміту"], errors="coerce").fillna(0).astype(int)
    df["Днів у Lotcheck"] = pd.to_numeric(df["Днів у Lotcheck"], errors="coerce").fillna(0).astype(int)
    
    for bool_col in ["Трейлер", "Картинки", "Тексти", "Switch", "Xbox", "Xbox Концепт", "Xbox TLA", "PlayStation", "PS Продукт"]:
        df[bool_col] = df[bool_col].apply(is_truthy)

    df = df[df["Гра"].astype(str).str.strip() != ""]
    df = df[~df["Гра"].astype(str).str.contains("Что нужно|Резюме|Добавить треккинг|Чистка|Работа с|Горящие|Ожидающие|Коммуникация", case=False, na=False)]
    
    return df.reset_index(drop=True)

@st.cache_data(ttl=300, show_spinner=False)
def load_data(sheet_url):
    if not sheet_url or "ВСТАВ_СЮДИ" in sheet_url:
        return pd.DataFrame()
    csv_url = get_export_url(sheet_url)
    try:
        df = pd.read_csv(csv_url, dtype=str)
    except Exception:
        return pd.DataFrame()

    text_column_keys = ["cover", "image", "постер", "url", "фото", "link", "посилання", "date", "дата", "name", "назва", "genre", "жанр", "status", "platform", "insights", "formula", "ai"]
    for col in df.columns:
        col_lower = str(col).lower()
        if any(tk in col_lower for tk in text_column_keys):
            continue
        df[col] = df[col].apply(clean_num_val)

    name_col = next((c for c in df.columns if any(k in c.lower() for k in ["game name", "game", "title", "назва"])), df.columns[0])
    df.rename(columns={name_col: "Game_Name_Clean"}, inplace=True)
    df = df[df["Game_Name_Clean"].astype(str).str.strip() != ""]
    return df

@st.cache_data(ttl=300, show_spinner=False)
def load_nintendo_monthly_from_sheet(sheet_url):
    if not sheet_url or "ВСТАВ_СЮДИ" in sheet_url:
        return pd.DataFrame()
    csv_url = get_export_url(sheet_url)
    try:
        df = pd.read_csv(csv_url, dtype=str)
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def load_xbox_monthly_from_sheet(sheet_url):
    if not sheet_url or "ВСТАВ_СЮДИ" in sheet_url:
        return pd.DataFrame()
    csv_url = get_export_url(sheet_url)
    try:
        df = pd.read_csv(csv_url, dtype=str)
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def load_pipeline_from_sheet(sheet_url):
    if not sheet_url or "ВСТАВ_СЮДИ" in sheet_url:
        return pd.DataFrame()
    csv_url = get_export_url(sheet_url)
    try:
        raw_p = pd.read_csv(csv_url, dtype=str)
        return normalize_pipeline_dataframe(raw_p)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def load_activity_from_sheet(sheet_url):
    if not sheet_url or "ВСТАВ_СЮДИ" in sheet_url:
        return pd.DataFrame()
    csv_url = get_export_url(sheet_url)
    try:
        df = pd.read_csv(csv_url, dtype=str)
        return df
    except Exception:
        return pd.DataFrame()

def load_pipeline_master_data():
    if os.path.exists(PIPELINE_STORAGE_FILE):
        try:
            with open(PIPELINE_STORAGE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data: return normalize_pipeline_dataframe(pd.DataFrame(data))
        except Exception:
            pass
    return pd.DataFrame()

def save_pipeline_master_data(df):
    try:
        with open(PIPELINE_STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Помилка збереження пайплайну: {e}")

def prepare_quarterly_data(df_weekly):
    if df_weekly.empty or "From" not in df_weekly.columns:
        return pd.DataFrame()
    df = df_weekly.copy()
    df = df.dropna(subset=["Parsed_Date"]).copy()
    df["Year"] = df["Parsed_Date"].apply(lambda d: d.year)
    df["Quarter"] = df["Parsed_Date"].apply(lambda d: f"Q{math.ceil(d.month/3)} {d.year}")
    return df

# ==============================================================================
# 🚀 4. ЗАВАНТАЖЕННЯ ДАНИХ ТА ВИЗНАЧЕННЯ ПОЛІВ
# ==============================================================================
raw_df = load_data(GOOGLE_SHEET_URL)

@st.cache_data(ttl=300, show_spinner=False)
def load_weekly_data(sheet_url):
    if not sheet_url or "ВСТАВ_СЮДИ" in sheet_url:
        return pd.DataFrame()
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
            0: "From", 1: "To",
            2: "Nintendo_Sales", 3: "Nintendo_Sales_Diff",
            4: "Nintendo_Wishlists", 5: "Nintendo_Wishlists_Diff",
            6: "Nintendo_Revenue", 7: "Nintendo_Revenue_Diff",
            8: "PS_Sales", 9: "PS_Sales_Diff",
            10: "PS_Wishlists", 11: "PS_Wishlists_Diff",
            12: "PS_Revenue", 13: "PS_Revenue_Diff",
            14: "Xbox_Sales", 15: "Xbox_Sales_Diff",
            16: "Xbox_Wishlists", 17: "Xbox_Wishlists_Diff",
            18: "Xbox_Revenue", 19: "Xbox_Revenue_Diff",
            20: "Leads", 21: "Leads_Diff",
            22: "Sequence_Started", 23: "Sequence_Started_Diff",
            24: "Contacts", 25: "Contacts_Diff",
            26: "Opportunities", 27: "Opportunities_Diff",
            28: "Calls", 29: "Calls_Diff",
            30: "Deals", 31: "Deals_Diff",
            32: "Twitter", 33: "Twitter_Diff",
            34: "Instagram", 35: "Instagram_Diff",
            36: "TikTok", 37: "TikTok_Diff",
            38: "YouTube", 39: "YouTube_Diff",
            40: "Discord", 41: "Discord_Diff"
        }

        parsed_dict = {}
        for col_idx, col_name in col_map.items():
            if col_idx < data_df.shape[1]:
                parsed_dict[col_name] = data_df.iloc[:, col_idx]

        df_out = pd.DataFrame(parsed_dict)
        for c in df_out.columns:
            if c not in ["From", "To"]:
                df_out[c] = df_out[c].apply(clean_num_val)

        df_out = df_out[df_out["From"].astype(str).str.strip().str.lower() != 'nan']
        df_out = df_out[df_out["From"].astype(str).str.strip() != '']
        
        df_out["Parsed_Date"] = df_out["From"].apply(parse_flexible_date)
        df_out["Month_Label"] = df_out["Parsed_Date"].apply(lambda d: d.strftime("%b %Y") if pd.notna(d) else "—")
        df_out["Total_Revenue"] = df_out.get("PS_Revenue", 0.0) + df_out.get("Nintendo_Revenue", 0.0) + df_out.get("Xbox_Revenue", 0.0)
        df_out["Total_Sales"] = df_out.get("PS_Sales", 0.0) + df_out.get("Nintendo_Sales", 0.0) + df_out.get("Xbox_Sales", 0.0)
        
        return df_out.reset_index(drop=True)
    except Exception:
        return pd.DataFrame()

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
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, width=64)
        else:
            st.markdown("<div style='font-size:38px; text-align:center;'>🎮</div>", unsafe_allow_html=True)
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
            "📅 Помісячна динаміка (Monthly)",
            "🚀 Release Pipeline",
            "📋 Release Activity",
            "🎯 Цілі та KPI 2026", 
            "📈 Тижнева динаміка (WoW)", 
            "🧮 Калькулятор прогнозів"
        ],
        index=0,
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
            if genres:
                filtered_df = filtered_df[filtered_df[genre_col].astype(str).str.strip().isin(genres)]

    if search:
        filtered_df = filtered_df[filtered_df["Game_Name_Clean"].astype(str).str.contains(search, case=False, na=False)]

    st.markdown("<div style='border-bottom: 1px solid #28283c; margin: 16px 0 14px 0;'></div>", unsafe_allow_html=True)

    st.caption("🤖 AI-АНАЛІТИК:")
    claude_key = ANTHROPIC_API_KEY or st.secrets.get("ANTHROPIC_API_KEY", "")
    if not claude_key:
        claude_key = st.text_input("Anthropic Key:", type="password", placeholder="sk-ant-...")

    ai_query = st.text_area("Запитай базу даних:", placeholder="Напр.: Яка конверсія лідів у контракти?")
    
    if st.button("⚡ Запитати Claude", use_container_width=True):
        clean_key = str(claude_key).strip()
        if not clean_key or not clean_key.startswith("sk-ant"):
            st.error("❌ Введи валідний ключ Anthropic (sk-ant-...)!")
        elif not ai_query.strip():
            st.warning("Введи запитання.")
        else:
            with st.spinner("Claude аналізує базу..."):
                try:
                    client = Anthropic(api_key=clean_key)
                    summary_lines = ["Game|Genre|Price|DevCost|DevSplit|Recoup|PS_All|Switch_All|Xbox_All|Total_All"]
                    def find_num(row_s, keys, not_keys=[]):
                        for c in row_s.index:
                            cl = c.lower()
                            if all(k in cl for k in keys) and not any(nk in cl for nk in not_keys):
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

                    prompt = f"""
                    Ти — головний фінансовий директор та аналітик консольного видавництва Upscale Studio (Україна).
                    Дані портфоліо ({len(summary_lines)-1} ігор):
                    {compact_dataset}

                    Тижнева звітність та BizDev воронка:
                    {weekly_csv_snippet}

                    Запитання: "{ai_query}"

                    Дай точну відповідь українською мовою з реальними цифрами та висновками.
                    ВАЖЛИВО: Пиши суми як "USD 1,500" або "\\$1,500" (без одинарного знака $).
                    """

                    try:
                        message = client.messages.create(model="claude-haiku-4-5", max_tokens=900, messages=[{"role": "user", "content": prompt}])
                        raw_text = message.content[0].text
                    except:
                        message = client.messages.create(model="claude-3-5-haiku-20241022", max_tokens=900, messages=[{"role": "user", "content": prompt}])
                        raw_text = message.content[0].text

                    clean_output = re.sub(r'(?<!\\)\$', r'\\$', raw_text)
                    st.markdown("### 💡 Результат аналізу:")
                    st.markdown(clean_output)
                except Exception as e:
                    st.error(f"❌ Помилка Anthropic API: {e}")

    st.markdown("<div style='border-bottom: 1px solid #28283c; margin: 16px 0 14px 0;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Оновити дані з Google Sheets", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ЧІТКИЙ РОЗРАХУНОК ALL-TIME СУМ
def get_exact_all_time(df_target, plat):
    if plat == "PS":
        for c in df_target.columns:
            cl = c.lower()
            if "playstation" in cl and "all" in cl:
                return float(df_target[c].sum())
    elif plat == "Switch":
        for c in df_target.columns:
            cl = c.lower()
            if "switch" in cl and "all" in cl:
                return float(df_target[c].sum())
    elif plat == "Xbox":
        for c in df_target.columns:
            cl = c.lower()
            if "xbox" in cl and "all" in cl:
                return float(df_target[c].sum())
    return 0.0

ps_rev = get_exact_all_time(filtered_df, "PS")
switch_rev = get_exact_all_time(filtered_df, "Switch")
xbox_rev = get_exact_all_time(filtered_df, "Xbox")

total_col = next((c for c in filtered_df.columns if c.lower() == "total" or "всього" in c.lower()), None)
if total_col:
    total_gross = float(filtered_df[total_col].sum())
else:
    total_gross = switch_rev + ps_rev + xbox_rev

# ==============================================================================
# 🎮 РОЗДІЛ 1: НАШІ ІГРИ
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
        "📈 Аналітика та Динаміка", 
        "🧠 Інсайти та Постери", 
        "📅 Розпродажі (Nintendo & Xbox)",
        "🎯 План vs Факт (Точність)",
        "💵 P&L, Зарплати та Роялті",
        "📑 Таблиця та One-Pager Звіт"
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
        sale_platform_choice = st.radio("Оберіть консольну платформу:", ["🔴 Nintendo eShop", "🟢 Xbox Store"], horizontal=True)

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
                hide_index=True,
                use_container_width=True,
                height=340
            )

            if st.button("⚡ Згенерувати оновлений Bookmarklet для Nintendo", use_container_width=True):
                selected_games = edited_tracker_df[edited_tracker_df["Включити"] == True]
                if selected_games.empty:
                    st.warning("Оберіть хоча б одну гру галочкою!")
                else:
                    discounts_payload = {s_row["Гра"].strip().lower(): int(s_row["Знижка % (з Таблиці)"]) for _, s_row in selected_games.iterrows()}
                    names_list = [s_row["Гра"].strip() for _, s_row in selected_games.iterrows()]
                    json_str = json.dumps(discounts_payload, ensure_ascii=False)

                    bookmarklet_code = f"""javascript:(function(){{
const discounts = {json_str};
function parsePrice(text){{let s=text.trim().replace(/[^0-9.,]/g,'');if(!s)return null;if(s.includes('.')&&s.includes(',')){{if(s.indexOf('.')<s.indexOf(',')){{s=s.replace(/\\./g,'').replace(',','.')}}else{{s=s.replace(/,/g,'')}}}}else if(s.includes(',')){{s=s.replace(',','.')}}return parseFloat(s);}}
function getGameTitle(el){{let current=el;while(current&&current!==document.body){{let prev=current.previousElementSibling;while(prev){{let text=prev.innerText||"";if(text.includes('HAC-')&&text.includes(':')){{let rawTitle=text.substring(text.indexOf(':')+1).trim();rawTitle=rawTitle.replace(/\\s*\\(\\d+\\/\\d+\\)\\s*$/, '').trim();return rawTitle;}}prev=prev.previousElementSibling;}}current=current.parentElement;}}return null;}}
const sortedKeys=Object.keys(discounts).sort((a,b)=>b.length-a.length);
const inputs=Array.from(document.querySelectorAll('input[type="text"]')).filter(inp=>{{const td=inp.closest('td');if(!td)return false;const prevTd=td.previousElementSibling;return prevTd&&/[\\d]/.test(prevTd.innerText);}});
let updatedCount=0;
inputs.forEach(priceInput=>{{const td=priceInput.closest('td');const regularPriceTd=td.previousElementSibling;if(!regularPriceTd)return;let regularPrice=parsePrice(regularPriceTd.innerText);if(regularPrice===null||isNaN(regularPrice)||regularPrice<=0)return;let gameTitle=getGameTitle(priceInput)||"Default";let cleanTitle=gameTitle.toLowerCase().replace(/\\s+/g,' ').trim();let discountPercent=70;let matched=false;for(let k of sortedKeys){{if(cleanTitle===k){{discountPercent=discounts[k];matched=true;break;}}}}if(!matched){{for(let k of sortedKeys){{if(cleanTitle.includes(k)||k.includes(cleanTitle)){{discountPercent=discounts[k];break;}}}}}}let discountedVal=regularPrice*(1-(discountPercent/100));let finalPriceStr="";if(regularPriceTd.innerText.includes(',')||regularPriceTd.innerText.includes('.')){{finalPriceStr=(Math.floor(discountedVal*100)/100).toFixed(2);}}else{{finalPriceStr=Math.floor(discountedVal).toString();}}priceInput.value=finalPriceStr;priceInput.dispatchEvent(new Event('input',{{bubbles:true}}));priceInput.dispatchEvent(new Event('change',{{bubbles:true}}));const row=priceInput.closest('tr');if(row){{const checkbox=row.querySelector('input[type="checkbox"]');if(checkbox&&!checkbox.checked){{checkbox.click();}}}}updatedCount++;}});
alert("🎉 Заповнено цін для обраних ігор: "+updatedCount);
}})();"""
                    st.success(f"🎉 Bookmarklet згенеровано для {len(selected_games)} ігор!")
                    b_c1, b_c2 = st.columns(2)
                    with b_c1:
                        st.markdown("##### 📌 Код закладки:")
                        st.code(bookmarklet_code, language="javascript")
                    with b_c2:
                        st.markdown("##### 📋 Список назв:")
                        st.text_area("Назви ігор:", "\n".join(names_list), height=160)

        else:
            xb_cal_df = pd.DataFrame([{"Сейл": s["name"], "Початок": s["start"], "Кінець": s["end"], "Тип": s["type"]} for s in XBOX_SCHEDULE])
            fig_xb_tl = px.timeline(xb_cal_df, x_start="Початок", x_end="Кінець", y="Сейл", color="Тип", color_discrete_map={"ID Sale (Глибокі знижки)": "#10b981", "Tentpole Sale": "#d946ef"})
            fig_xb_tl.update_yaxes(autorange="reversed")
            fig_xb_tl.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), height=230)
            st.plotly_chart(fig_xb_tl, use_container_width=True)

            xb_choice = st.selectbox("Оберіть сейл Xbox для перевірки дедлайну та подачі:", [s['name'] for s in XBOX_SCHEDULE], index=0)
            cur_xb_sale = next(s for s in XBOX_SCHEDULE if s["name"] == xb_choice)

            deadline_dt = datetime.strptime(cur_xb_sale["deadline"], "%Y-%m-%d")
            today_dt = datetime.now()
            days_to_deadline = (deadline_dt - today_dt).days
            deadline_badge = f"⏳ Залишилось {days_to_deadline} дн." if days_to_deadline > 0 else "🚨 Дедлайн СЬОГОДНІ!"

            xc1, xc2, xc3, xc4 = st.columns(4)
            xc1.metric("🎯 Цільовий розпродаж", cur_xb_sale["name"].split(" (")[0])
            xc2.metric("⏰ Дедлайн подачі", cur_xb_sale["deadline"], deadline_badge)
            xc3.metric("🔒 Ліміт тайтлів", f"до {cur_xb_sale['limit']} ігор")
            xc4.metric("📩 Approval Feedback", cur_xb_sale["feedback"])

            st.info(f"💡 **Вимоги Microsoft:** {cur_xb_sale['note']}")

            xb_tracker_rows = []
            for _, r in filtered_df.iterrows():
                g_name = r["Game_Name_Clean"]
                g_price = clean_num_val(r.get("Price consoles, $", r.get("Price consoles", 9.99)))
                if g_price == 0: g_price = 9.99
                sheet_disc = clean_num_val(r.get(discount_col, 70.0)) if discount_col else 70.0
                sheet_disc = int(round(sheet_disc)) if sheet_disc > 0 else 70

                is_eligible = True
                fail_reasons = []
                if cur_xb_sale["min_price"] > 0 and g_price < cur_xb_sale["min_price"]:
                    is_eligible = False
                    fail_reasons.append(f"Ціна ${g_price:.2f} < ${cur_xb_sale['min_price']}")
                if cur_xb_sale["min_discount"] > 0 and sheet_disc < cur_xb_sale["min_discount"]:
                    sheet_disc = cur_xb_sale["min_discount"]

                xb_tracker_rows.append({
                    "Подати гру": is_eligible, "Гра": g_name, "Базова ціна ($)": g_price,
                    "Знижка Xbox (%)": sheet_disc, "Ціна на сейлі ($)": round(g_price * (1 - sheet_disc / 100.0), 2),
                    "Статус відповідності": "🟢 Проходить вимоги" if is_eligible else f"🔴 Не підходить ({', '.join(fail_reasons)})"
                })

            edited_xb_df = st.data_editor(
                pd.DataFrame(xb_tracker_rows),
                column_config={
                    "Подати гру": st.column_config.CheckboxColumn("Подати в Microsoft", default=True),
                    "Знижка Xbox (%)": st.column_config.NumberColumn("Знижка (%)", min_value=cur_xb_sale["min_discount"], max_value=90, step=5),
                    "Гра": st.column_config.TextColumn("Назва гри", disabled=True),
                    "Базова ціна ($)": st.column_config.NumberColumn("Base Price ($)", format="$%.2f", disabled=True),
                    "Ціна на сейлі ($)": st.column_config.NumberColumn("Sale Price ($)", format="$%.2f", disabled=True),
                    "Статус відповідності": st.column_config.TextColumn("Вимоги сейлу", disabled=True)
                },
                disabled=["Гра", "Базова ціна ($)", "Ціна на сейлі ($)", "Статус відповідності"],
                hide_index=True,
                use_container_width=True,
                height=340
            )

    with tab_forecast_review:
        st.subheader("🎯 Порівняння прогнозованих та фактичних результатів")
        st.caption("Аудит точності на основі відкаліброваних 30 піджанрів та вхідних джерел")

        def get_exact_fact_m1(row_s, plat):
            if plat == "PS":
                for c in row_s.index:
                    cl = c.lower()
                    if "playstation" in cl and ("1st" in cl or "month" in cl) and "pred" not in cl and "forecast" not in cl:
                        try: return float(row_s[c])
                        except: pass
            elif plat == "Switch":
                for c in row_s.index:
                    cl = c.lower()
                    if "switch" in cl and ("1st" in cl or "month" in cl) and not cl.endswith(".1") and "pred" not in cl and "forecast" not in cl:
                        try: return float(row_s[c])
                        except: pass
            elif plat == "Xbox":
                for c in row_s.index:
                    cl = c.lower()
                    if "xbox" in cl and ("1st" in cl or "month" in cl) and not cl.endswith(".1") and "pred" not in cl and "forecast" not in cl:
                        try: return float(row_s[c])
                        except: pass
            return 0.0

        def find_val(row_s, keys, not_keys=[]):
            for c in row_s.index:
                cl = c.lower()
                if all(k in cl for k in keys) and not any(nk in cl for nk in not_keys):
                    try: return float(row_s[c])
                    except: pass
            return 0.0

        comparison_list = []
        for _, r in filtered_df.iterrows():
            g_name = str(r["Game_Name_Clean"]).strip()
            if not g_name or g_name.lower() == 'nan': continue
            g_genre_str = str(r.get(genre_col, "Simulator: Job / Service / Business (3D)")).strip()
            g_price = clean_num_val(r.get("Price consoles, $", r.get("Price consoles", 9.99)))
            if g_price == 0: g_price = 9.99

            ps_m1_fact = get_exact_fact_m1(r, "PS")
            sw_m1_fact = get_exact_fact_m1(r, "Switch")
            xb_m1_fact = get_exact_fact_m1(r, "Xbox")

            active_platforms = []
            if ps_m1_fact > 0: active_platforms.append("PS")
            if sw_m1_fact > 0: active_platforms.append("Switch")
            if xb_m1_fact > 0: active_platforms.append("Xbox")
            if not active_platforms: active_platforms = ["Switch"]

            platform_badge = " + ".join(active_platforms) if len(active_platforms) < 3 else "Усі 3 консолі"

            base_m = find_val(r, ["base metric"])
            installs_val = find_val(r, ["installs"]) or find_val(r, ["reviews"])
            steam_rev_val = find_val(r, ["steam revenue"])
            src_platform_type = str(r.get("Platform Source", r.get("Platform", ""))).lower()

            if base_m == 0:
                if "steam" in src_platform_type or steam_rev_val > 0: base_m = (steam_rev_val * 0.10) + 500.0
                elif "play" in src_platform_type or ("google" in src_platform_type) or (installs_val >= 10000): base_m = (math.sqrt(installs_val) * 2.0) + 800.0 if installs_val > 0 else 0.0
                elif "crazy" in src_platform_type or ("web" in src_platform_type and installs_val > 0): base_m = (installs_val * 0.05) + 900.0
                elif "itch" in src_platform_type and installs_val > 0: base_m = (installs_val * 10.0) + 400.0

            if base_m > 0:
                matched_g = "Simulator: Job / Service / Business (3D)"
                for k in GENRE_DATABASE:
                    if k.lower() in g_genre_str.lower() or g_genre_str.lower() in k.lower():
                        matched_g = k
                        break
                cfg = GENRE_DATABASE[matched_g]
                p_m = PRICE_MODIFIERS.get(g_price, 1.0)
                ps_pred = base_m * cfg["PS"] * p_m if "PS" in active_platforms else 0.0
                sw_pred = base_m * cfg["Switch"] * p_m if "Switch" in active_platforms else 0.0
                xb_pred = base_m * cfg["Xbox"] * p_m if "Xbox" in active_platforms else 0.0
                total_pred_m1 = ps_pred + sw_pred + xb_pred
                has_valid_forecast = True
            else:
                total_pred_m1, has_valid_forecast = 0.0, False

            total_m1_fact = (ps_m1_fact if "PS" in active_platforms else 0.0) + (sw_m1_fact if "Switch" in active_platforms else 0.0) + (xb_m1_fact if "Xbox" in active_platforms else 0.0)

            if has_valid_forecast and total_m1_fact > 0:
                acc_pct = max(0.0, round((1.0 - abs(total_m1_fact - total_pred_m1) / max(total_m1_fact, total_pred_m1)) * 100, 1))
                delta_usd = total_m1_fact - total_pred_m1
                if total_m1_fact > total_pred_m1 * 1.25: perf_status = "🟢 Перевищила план"
                elif total_m1_fact < total_pred_m1 * 0.70: perf_status = "🔴 Нижче плану"
                else: perf_status = "🟡 У плані (±25%)"
            elif total_m1_fact > 0 and not has_valid_forecast:
                acc_pct, delta_usd, perf_status = None, None, "⚪ Немає вхідних метрик"
            else:
                acc_pct, delta_usd, perf_status = None, None, "⚪ Немає факт даних"

            comparison_list.append({
                "Гра": g_name, "Жанр": g_genre_str, "Ціна ($)": g_price,
                "Платформи релізу": platform_badge, "Base Metric": round(base_m, 1) if base_m > 0 else "—",
                "Факт M1 ($)": round(total_m1_fact, 2) if total_m1_fact > 0 else "—",
                "Прогноз M1 ($)": round(total_pred_m1, 2) if has_valid_forecast else "—",
                "Різниця ($)": round(delta_usd, 2) if delta_usd is not None else "—",
                "Точність (%)": f"{acc_pct:.1f}%" if acc_pct is not None else "—",
                "Статус виконання": perf_status
            })

        comp_df = pd.DataFrame(comparison_list)
        valid_comp = comp_df[comp_df["Точність (%)"] != "—"].copy()
        valid_comp["Acc_Num"] = valid_comp["Точність (%)"].str.replace("%", "").astype(float)
        
        avg_acc = valid_comp["Acc_Num"].mean() if not valid_comp.empty else 0.0
        over_count = len(comp_df[comp_df["Статус виконання"].str.contains("Перевищила")])
        target_count = len(comp_df[comp_df["Статус виконання"].str.contains("У плані")])
        under_count = len(comp_df[comp_df["Статус виконання"].str.contains("Нижче")])

        a_c1, a_c2, a_c3, a_c4 = st.columns(4)
        a_c1.metric("Середня точність моделі", f"{avg_acc:.1f}%" if avg_acc > 0 else "—")
        a_c2.metric("🟢 Перевищили план", f"{over_count} ігор")
        a_c3.metric("🟡 У межах плану (±25%)", f"{target_count} ігор")
        a_c4.metric("🔴 Нижче прогнозу", f"{under_count} ігор")

        st.markdown("---")
        if not valid_comp.empty:
            chart_plan_df = valid_comp.head(15)
            fig_plan_fact = go.Figure()
            fig_plan_fact.add_trace(go.Bar(x=chart_plan_df["Гра"], y=chart_plan_df["Факт M1 ($)"], name="ФАКТ M1 ($)", marker_color="#10b981"))
            fig_plan_fact.add_trace(go.Bar(x=chart_plan_df["Гра"], y=chart_plan_df["Прогноз M1 ($)"], name="ПРОГНОЗ M1 ($)", marker_color="#d946ef"))
            fig_plan_fact.update_layout(
                barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#e2e8f0"), height=360, margin=dict(t=20, b=20, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_plan_fact, use_container_width=True)

        st.dataframe(comp_df, use_container_width=True, height=450)

    with tab_pnl_royalty:
        st.subheader("💵 Фінансовий P&L, Зарплати портінгу та Роялті девелоперів")
        with st.expander("⚙️ Параметри комісій та податків (Симуляція)", expanded=False):
            sc1, sc2 = st.columns(2)
            sim_store_cut = sc1.slider("Комісія сторів (Sony/Nintendo/Xbox %):", 15, 35, 30, step=1)
            sim_tax_cut = sc2.slider("Податки та резерви (Withholding / VAT %):", 0, 15, 7, step=1)

        net_receipt_pct = (100 - sim_store_cut - sim_tax_cut) / 100.0

        pnl_rows = []
        tot_internal_cost = 0.0
        tot_studio_pure = 0.0
        tot_dev_royalty = 0.0
        tot_net_bank = 0.0

        for _, r in filtered_df.iterrows():
            g_name = r["Game_Name_Clean"]
            g_gross = clean_num_val(r[total_col if total_col else filtered_df.columns[0]])
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
            roi_str = f"{s_gross_margin/g_porting_salary:.1f}x ROI" if g_porting_salary > 0 else "—"

            tot_internal_cost += g_porting_salary
            tot_studio_pure += s_pure_net
            tot_dev_royalty += d_royalty
            tot_net_bank += g_net_rec

            pnl_rows.append({
                "Гра": g_name, "Gross ($)": round(g_gross, 2), "Net у банку ($)": round(g_net_rec, 2),
                "Зарплата розробника ($)": round(g_porting_salary, 2), "Роялті автору ($)": round(d_royalty, 2),
                "🔥 Чистий прибуток студії ($)": round(s_pure_net, 2), "ROI": roi_str
            })

        pn1, pn2, pn3 = st.columns(3)
        pn1.metric(f"Net у банку ({net_receipt_pct*100:.0f}%)", f"${tot_net_bank:,.2f}")
        pn2.metric("Виплати роялті авторам", f"${tot_dev_royalty:,.2f}")
        pn3.metric("🔥 Чистий прибуток Upscale Studio", f"${tot_studio_pure:,.2f}", f"Зарплати: ${tot_internal_cost:,.0f}")
        st.dataframe(pd.DataFrame(pnl_rows).sort_values(by="Gross ($)", ascending=False), use_container_width=True, height=400)

    with tab_table_report:
        st.subheader("📑 Повна фінансова таблиця портфоліо")
        column_config = {}
        if cover_col:
            column_config[cover_col] = st.column_config.ImageColumn("Обкладинка", width="small")
        st.dataframe(filtered_df, column_config=column_config, use_container_width=True, height=420)
        
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Експортувати дані (.CSV)", data=csv_data, file_name="console_sales_portfolio.csv", mime="text/csv")

        st.markdown("---")
        st.subheader("📄 One-Pager Executive Звіт")
        
        report_html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Upscale Studio Executive Report</title>
<style>
body {{ background-color: #0f172a; color: #f8fafc; font-family: -apple-system, sans-serif; padding: 30px; }}
.card {{ background-color: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 16px; text-align: center; }}
.grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }}
.title {{ font-size: 24px; font-weight: bold; color: #fff; }}
.val {{ font-size: 26px; font-weight: 800; margin: 6px 0 0 0; }}
</style></head>
<body>
<div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #334155; padding-bottom:15px;">
<div><div class="title">UPSCALE STUDIO</div><div>Console Operations Executive Report</div></div>
<div><b>Date:</b> {datetime.now().strftime('%B %Y')}</div>
</div>
<div class="grid">
<div class="card"><div>TOTAL CONSOLE GROSS</div><div class="val" style="color:#38bdf8;">${total_gross:,.0f}</div></div>
<div class="card"><div>PLAYSTATION</div><div class="val" style="color:#60a5fa;">${ps_rev:,.0f}</div></div>
<div class="card"><div>NINTENDO SWITCH</div><div class="val" style="color:#f87171;">${switch_rev:,.0f}</div></div>
<div class="card"><div>XBOX</div><div class="val" style="color:#4ade80;">${xbox_rev:,.0f}</div></div>
</div>
</body></html>"""

        st.download_button(
            label="📥 Завантажити One-Pager звіт (.HTML / PDF)",
            data=report_html_content,
            file_name=f"Upscale_Studio_Executive_Report_{datetime.now().strftime('%Y_%m')}.html",
            mime="text/html"
        )


# ==============================================================================
# 📅 РОЗДІЛ 2: ПОМІСЯЧНА ДИНАМІКА
# ==============================================================================
elif app_mode == "📅 Помісячна динаміка (Monthly)":
    st.title("📅 Помісячна виручка та Cashflow портфоліо ($ USD)")
    st.caption("Автоматичне зчитування з Google Таблиць • Конвертація валют • Дедуплікація та аналіз")

    with st.expander("⚙️ Джерела даних помісячних звітів (Google Sheets)", expanded=False):
        c_src1, c_src2 = st.columns(2)
        custom_nintendo_url = c_src1.text_input("URL Таблиці Nintendo Monthly:", NINTENDO_MONTHLY_SHEET_URL)
        custom_xbox_url = c_src2.text_input("URL Таблиці Xbox Monthly:", XBOX_MONTHLY_SHEET_URL, placeholder="https://docs.google.com/spreadsheets/d/.../edit#gid=...")
        if st.button("🔄 Оновити дані помісячних звітів"):
            st.cache_data.clear()
            st.rerun()

    active_nintendo_raw = load_nintendo_monthly_from_sheet(custom_nintendo_url)
    active_xbox_raw = load_xbox_monthly_from_sheet(custom_xbox_url)

    n_matrix_df, n_months, _ = parse_nintendo_monthly_data(active_nintendo_raw)
    x_matrix_df, x_months = parse_xbox_monthly_data(active_xbox_raw)
    c_matrix_df, c_months = combine_monthly_matrices(n_matrix_df, x_matrix_df, n_months, x_months)

    selected_platform_mode = st.radio(
        "Оберіть консольну платформу для аналізу:",
        ["🔴 Nintendo eShop", "🟢 Xbox Store", "🌐 Всі консолі (Switch + Xbox)"],
        horizontal=True
    )

    if selected_platform_mode == "🔴 Nintendo eShop":
        active_matrix_df = n_matrix_df
        active_month_labels = n_months
        store_accent_color = "#e60012"
    elif selected_platform_mode == "🟢 Xbox Store":
        active_matrix_df = x_matrix_df
        active_month_labels = x_months
        store_accent_color = "#107c10"
    else:
        active_matrix_df = c_matrix_df
        active_month_labels = c_months
        store_accent_color = "#d946ef"

    if not active_matrix_df.empty and active_month_labels:
        st.markdown("---")
        
        f_mode_col, f_ctrl_col = st.columns([1.2, 2.8])
        with f_mode_col:
            filter_mode = st.radio(
                "Режим фільтрації періоду:",
                ["🗓️ Один місяць", "↔️ Діапазон місяців (Слайдер)", "🎯 Довільний вибір (Мультиселект)", "📅 Всі місяці"],
                index=0
            )
        
        with f_ctrl_col:
            if filter_mode == "🗓️ Один місяць":
                selected_single_m = st.selectbox("Оберіть місяць:", options=active_month_labels, index=len(active_month_labels)-1)
                active_selected_months = [selected_single_m]
            elif filter_mode == "↔️ Діапазон місяців (Слайдер)":
                start_m, end_m = st.select_slider(
                    "Оберіть часовий діапазон місяців:",
                    options=active_month_labels,
                    value=(active_month_labels[max(0, len(active_month_labels)-6)], active_month_labels[-1])
                )
                s_idx = active_month_labels.index(start_m)
                e_idx = active_month_labels.index(end_m)
                active_selected_months = active_month_labels[min(s_idx, e_idx):max(s_idx, e_idx)+1]
            elif filter_mode == "🎯 Довільний вибір (Мультиселект)":
                active_selected_months = st.multiselect(
                    "Оберіть конкретні місяці:",
                    options=active_month_labels,
                    default=[active_month_labels[-1]]
                )
                if not active_selected_months:
                    active_selected_months = [active_month_labels[-1]]
            else:
                active_selected_months = active_month_labels

        period_label_display = f"{active_selected_months[0]} ➔ {active_selected_months[-1]}" if len(active_selected_months) > 1 else active_selected_months[0]
        
        display_period_df = active_matrix_df[["Назва гри / DLC"] + active_selected_months].copy()
        display_period_df["Виторг за період ($)"] = display_period_df[active_selected_months].sum(axis=1)
        display_period_df["All-Time ($)"] = active_matrix_df["Всього ($)"]
        display_period_df = display_period_df[display_period_df["Виторг за період ($)"] > 0].sort_values(by="Виторг за період ($)", ascending=False).reset_index(drop=True)

        total_period_rev = float(display_period_df["Виторг за період ($)"].sum()) if not display_period_df.empty else 0.0
        display_period_df["Частка у періоді (%)"] = display_period_df["Виторг за період ($)"].apply(lambda x: f"{(x / max(total_period_rev, 1.0))*100:.1f}%")

        st.markdown("<br>", unsafe_allow_html=True)
        
        p_c1, p_c2, p_c3, p_c4 = st.columns(4)
        p_c1.markdown(f'<div class="kpi-card"><div class="kpi-label">Виторг ({period_label_display})</div><div class="kpi-value">${total_period_rev:,.2f}</div><span class="kpi-badge badge-total">{len(active_selected_months)} міс. вибрано</span></div>', unsafe_allow_html=True)
        p_c2.markdown(f'<div class="kpi-card"><div class="kpi-label">Активних тайтлів</div><div class="kpi-value">{len(display_period_df)}</div><span class="kpi-badge badge-ps">З продажами</span></div>', unsafe_allow_html=True)
        p_c3.markdown(f'<div class="kpi-card"><div class="kpi-label">Лідер періоду</div><div class="kpi-value" style="font-size:16px; color:#38bdf8 !important;">{display_period_df.iloc[0]["Назва гри / DLC"] if not display_period_df.empty else "—"}</div><span class="kpi-badge badge-xbox">${display_period_df.iloc[0]["Виторг за період ($)"]:,.2f}</span></div>', unsafe_allow_html=True)
        p_c4.markdown(f'<div class="kpi-card"><div class="kpi-label">Каса платформи All-Time</div><div class="kpi-value">${active_matrix_df["Всього ($)"].sum():,.2f}</div><span class="kpi-badge badge-switch">Повна база</span></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        m_tab1, m_tab2, m_tab3 = st.tabs([
            "📊 Топ тайтли та Звіт за період", 
            "📑 Повна матриця за всі місяці ($)", 
            "🔥 Теплова карта (Heatmap) та Тренди"
        ])

        with m_tab1:
            st.subheader(f"🏆 Топ-10 продуктів за обраний період ({period_label_display})")
            if not display_period_df.empty:
                top10_period = display_period_df.head(10)
                fig_p_bar = px.bar(
                    top10_period, x="Виторг за період ($)", y="Назва гри / DLC", orientation="h",
                    text="Виторг за період ($)", color_discrete_sequence=[store_accent_color]
                )
                fig_p_bar.update_traces(texttemplate='$%{text:,.2f}', textposition='outside')
                fig_p_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), height=380, yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_p_bar, use_container_width=True)

            st.markdown("##### 📑 Таблиця продажів за обраний період:")
            format_cfg_period = {
                "Виторг за період ($)": st.column_config.NumberColumn("Виторг за період ($)", format="$%.2f"),
                "All-Time ($)": st.column_config.NumberColumn("All-Time ($)", format="$%.2f")
            }
            for m_col in active_selected_months:
                format_cfg_period[m_col] = st.column_config.NumberColumn(m_col, format="$%.2f")

            st.dataframe(display_period_df, column_config=format_cfg_period, use_container_width=True, height=400)
            csv_p_out = display_period_df.to_csv(index=False).encode('utf-8')
            plat_slug = selected_platform_mode.split(" ")[1].lower()
            st.download_button("📥 Завантажити звіт за період (.CSV)", data=csv_p_out, file_name=f"{plat_slug}_revenue_{period_label_display.replace(' ➔ ', '_')}.csv", mime="text/csv")

        with m_tab2:
            st.subheader(f"📑 Повна помісячна матриця ({selected_platform_mode}) ($ USD)")
            format_cfg_all = {"Всього ($)": st.column_config.NumberColumn("Всього ($)", format="$%.2f")}
            for m_col in active_month_labels:
                format_cfg_all[m_col] = st.column_config.NumberColumn(m_col, format="$%.2f")

            st.dataframe(active_matrix_df, column_config=format_cfg_all, use_container_width=True, height=480)
            csv_m_out = active_matrix_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Завантажити повну матрицю (.CSV)", data=csv_m_out, file_name=f"{plat_slug}_monthly_usd_matrix.csv", mime="text/csv")

        with m_tab3:
            st.subheader("🔥 Теплова карта виторгу (Monthly Heatmap)")
            top_heatmap_df = active_matrix_df.head(20).set_index("Назва гри / DLC")[active_month_labels]
            fig_heat = px.imshow(
                top_heatmap_df, labels=dict(x="Місяць", y="Гра / DLC", color="Виторг ($)"),
                x=active_month_labels, y=top_heatmap_df.index, color_continuous_scale="Purples", aspect="auto"
            )
            fig_heat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), height=480)
            st.plotly_chart(fig_heat, use_container_width=True)

            st.markdown("---")
            st.subheader("📈 Індивідуальний тренд гри")
            selected_item_for_trend = st.selectbox("Оберіть гру або DLC для перегляду помісячного тренду:", options=active_matrix_df["Назва гри / DLC"].tolist(), index=0)
            item_row = active_matrix_df[active_matrix_df["Назва гри / DLC"] == selected_item_for_trend].iloc[0]
            trend_df = pd.DataFrame([{"Місяць": m, "Виторг ($)": item_row[m]} for m in active_month_labels])
            
            fig_trend = px.bar(trend_df, x="Місяць", y="Виторг ($)", text="Виторг ($)", color_discrete_sequence=[store_accent_color])
            fig_trend.update_traces(texttemplate='$%{text:,.2f}', textposition='outside')
            fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), height=350)
            st.plotly_chart(fig_trend, use_container_width=True)

    else:
        st.warning(f"⚠️ Дані для режиму '{selected_platform_mode}' ще не завантажені або містять порожні рядки. Перевір URL в налаштуваннях джерел.")


# ==============================================================================
# 🚀 РОЗДІЛ 3: RELEASE PIPELINE
# ==============================================================================
elif app_mode == "🚀 Release Pipeline":
    st.title("🚀 Console Release Pipeline & Lotcheck Tracker")
    st.caption("Повний цикл виробництва консольних портів • Пряма синхронізація з Google Таблицею • Контроль зриву дедлайнів")

    if not sheet_pipeline_df.empty:
        live_pipeline_df = sheet_pipeline_df.copy()
    else:
        live_pipeline_df = load_pipeline_master_data()

    if "pipeline_live_state" not in st.session_state or st.session_state.pipeline_live_state.empty:
        st.session_state.pipeline_live_state = live_pipeline_df

    pipeline_df = normalize_pipeline_dataframe(st.session_state.pipeline_live_state.copy())

    with st.expander("➕ Додати нову гру в пайплайн портінгу", expanded=False):
        with st.form("add_new_pipeline_game_form", clear_on_submit=True):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                new_title = st.text_input("Назва гри (Title):", placeholder="Напр. Dark Nightmare 3D")
                new_dev = st.selectbox("Розробник порту:", ["Ігор", "Сергій", "Іван", "Максим", "Влад", "Діма", "Інший"])
                new_artist = st.selectbox("Художниця (Арт/Капсули):", ["", "Анна", "Анна Коваленко", "Інша"])
            with f_col2:
                new_start_date = st.date_input("Дата старту робіт:", datetime.now())
                new_finish_date = st.date_input("Планова дата фінішу:", datetime.now() + timedelta(days=21))
                new_plan_days = st.number_input("Плановий строк (днів):", min_value=0, value=14, step=1)
                new_lotcheck_status = st.selectbox("Статус Lotcheck:", ["In Development", "In testing", "Submitted for lotcheck", "Passed Lotcheck", "Blocked"])
            with f_col3:
                st.write("**Платформи виходу:**")
                new_sw = st.checkbox("Nintendo Switch", value=True)
                new_xb = st.checkbox("Xbox", value=False)
                new_ps = st.checkbox("PlayStation", value=False)
                new_notes = st.text_area("Нюанси / Примітки:", placeholder="Хто кого чекає, блокери, баги...")

            if st.form_submit_button("🚀 Зберегти проект у пайплайн", use_container_width=True):
                if not new_title.strip():
                    st.warning("Введіть назву гри!")
                else:
                    new_project_row = {
                        "Гра": new_title.strip(), "Розробник": new_dev, "Художник": new_artist,
                        "Нюанси": new_notes.strip(), "Дата старту": new_start_date.strftime("%Y-%m-%d"),
                        "Планова дата": new_finish_date.strftime("%Y-%m-%d"), "Плановий строк": int(new_plan_days),
                        "Факт до сабміту": 0, "Трейлер": False, "Картинки": False, "Тексти": False,
                        "Switch": new_sw, "Switch Білд Дата": "", "Статус Lotcheck": new_lotcheck_status,
                        "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "",
                        "Xbox": new_xb, "Xbox Концепт": False, "Xbox TLA": False, "PlayStation": new_ps, "PS Продукт": False
                    }
                    st.session_state.pipeline_live_state = pd.concat([pd.DataFrame([new_project_row]), pipeline_df], ignore_index=True)
                    save_pipeline_master_data(st.session_state.pipeline_live_state)
                    st.success(f"🎉 Проект '{new_title}' додано до пайплайну!")
                    st.rerun()

    pipe_tab1, pipe_tab2, pipe_tab3 = st.tabs([
        "📑 Головний трекер (Master View)", 
        "🎮 Консольні кабінети (Lotcheck & Контроль строків)", 
        "🚨 Блокери, QA та Команда"
    ])

    with pipe_tab1:
        st.markdown("### 📊 Оперативний статус виробництва")
        
        for col_chk in ["Плановий строк", "Факт до сабміту"]:
            if col_chk not in pipeline_df.columns:
                pipeline_df[col_chk] = 0

        overrun_projects = pipeline_df[(pipeline_df["Факт до сабміту"] > pipeline_df["Плановий строк"]) & (pipeline_df["Плановий строк"] > 0)]
        overrun_count = len(overrun_projects)
        in_dev_count = len(pipeline_df[pipeline_df["Статус Lotcheck"].astype(str).str.contains("Development|testing", case=False)])
        in_cert_count = len(pipeline_df[pipeline_df["Статус Lotcheck"].astype(str).str.contains("Submitted", case=False)])
        passed_count = len(pipeline_df[pipeline_df["Статус Lotcheck"].astype(str).str.contains("Passed", case=False)])

        p_k1, p_k2, p_k3, p_k4 = st.columns(4)
        p_k1.markdown(f'<div class="kpi-card"><div class="kpi-label">🛠️ В розробці / QA</div><div class="kpi-value">{in_dev_count}</div><span class="kpi-badge badge-total">Всього: {len(pipeline_df)} проектів</span></div>', unsafe_allow_html=True)
        p_k2.markdown(f'<div class="kpi-card"><div class="kpi-label">⏳ На сертифікації (Lotcheck)</div><div class="kpi-value" style="color:#38bdf8 !important;">{in_cert_count}</div><span class="kpi-badge badge-ps">Чекають відповіді</span></div>', unsafe_allow_html=True)
        p_k3.markdown(f'<div class="kpi-card"><div class="kpi-label">🟢 Сертифіковано (Passed)</div><div class="kpi-value" style="color:#4ade80 !important;">{passed_count}</div><span class="kpi-badge badge-xbox">Готові до релізу</span></div>', unsafe_allow_html=True)
        p_k4.markdown(f'<div class="kpi-card"><div class="kpi-label">🚨 ЗРИВ СТРОКІВ (Факт > План)</div><div class="kpi-value" style="color:#ef4444 !important;">{overrun_count}</div><span class="kpi-badge badge-switch">Потребують уваги</span></div>', unsafe_allow_html=True)

        if overrun_count > 0:
            st.markdown("#### 🚨 Проекти з критичним зривом термінів до сертифікації:")
            for _, o_row in overrun_projects.iterrows():
                delay_days = int(o_row['Факт до сабміту'] - o_row['Плановий строк'])
                st.markdown(f"""
                <div class="alert-card-red">
                    <b style="color:#fff; font-size:15px;">🎮 {o_row['Гра']} (Розробник: {o_row['Розробник']})</b> ➔ 
                    <span style="color:#f87171; font-weight:bold;">План: {o_row['Плановий строк']} дн. | Факт до сабміту: {o_row['Факт до сабміту']} дн. (🔴 +{delay_days} днів затримки!)</span>
                    <p style="margin:4px 0 0 0; font-size:12px; color:#cbd5e1;">Нюанси: {o_row['Нюанси']}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        f_c1, f_c2 = st.columns([1, 2])
        with f_c1:
            dev_options = sorted([str(x) for x in pipeline_df["Розробник"].dropna().unique() if str(x).strip() and str(x).lower() != 'nan'])
            dev_filter = st.multiselect("Фільтр за розробником:", options=dev_options, default=[])
        with f_c2:
            show_multi_only = st.checkbox("Показати тільки мультиплатформи (Switch + Xbox/PS)", value=False)

        view_df = pipeline_df.copy()
        if dev_filter:
            view_df = view_df[view_df["Розробник"].isin(dev_filter)]
        if show_multi_only:
            view_df = view_df[(view_df["Xbox"] == True) | (view_df["PlayStation"] == True)]

        master_cols_config = {
            "Гра": st.column_config.TextColumn("Гра", width="medium"),
            "Розробник": st.column_config.SelectboxColumn("Розробник", options=["Ігор", "Сергій", "Іван", "Максим", "Влад", "Діма", "Інший"], width="small"),
            "Художник": st.column_config.TextColumn("Художник", width="small"),
            "Планова дата": st.column_config.TextColumn("Дедлайн", width="small"),
            "Плановий строк": st.column_config.NumberColumn("План (дн)", width="small"),
            "Факт до сабміту": st.column_config.NumberColumn("Факт (дн)", width="small"),
            "Трейлер": st.column_config.CheckboxColumn("🎬 Трейлер", default=False),
            "Картинки": st.column_config.CheckboxColumn("🎨 Капсули", default=False),
            "Тексти": st.column_config.CheckboxColumn("📝 Тексти", default=False),
            "Статус Lotcheck": st.column_config.SelectboxColumn("Статус Lotcheck", options=["In Development", "In testing", "Submitted for lotcheck", "Passed Lotcheck", "Blocked"], width="medium"),
            "Switch": st.column_config.CheckboxColumn("🔴 NSW", default=True),
            "Xbox": st.column_config.CheckboxColumn("🟢 XB", default=False),
            "PlayStation": st.column_config.CheckboxColumn("🔵 PS", default=False),
            "Нюанси": st.column_config.TextColumn("Нюанси / Примітки", width="large")
        }

        display_cols = [c for c in ["Гра", "Розробник", "Художник", "Планова дата", "Плановий строк", "Факт до сабміту", "Трейлер", "Картинки", "Тексти", "Статус Lotcheck", "Switch", "Xbox", "PlayStation", "Нюанси"] if c in view_df.columns]
        edited_master_df = st.data_editor(
            view_df[display_cols],
            column_config=master_cols_config,
            hide_index=True,
            use_container_width=True,
            height=480
        )

        if st.button("💾 Зберегти зміни головного пайплайну на сервері", use_container_width=True):
            for _, erow in edited_master_df.iterrows():
                match_idx = pipeline_df[pipeline_df["Гра"] == erow["Гра"]].index
                if not match_idx.empty:
                    for col_k in display_cols:
                        if col_k in erow:
                            pipeline_df.loc[match_idx[0], col_k] = erow[col_k]
            st.session_state.pipeline_live_state = pipeline_df
            save_pipeline_master_data(pipeline_df)
            st.success("🎉 Усі зміни збережено!")

    with pipe_tab2:
        st.markdown("### 🎮 Детальний контроль консольних кабінетів та строків")
        cab_choice = st.radio("Оберіть консольну платформу:", ["🔴 Nintendo Switch (Lotcheck Deep-Dive & Строки)", "🟢 Xbox (ID@Xbox воронка)", "🔵 PlayStation (Safe Publisher Setup)"], horizontal=True)

        if "Nintendo" in cab_choice:
            st.markdown("#### 🔴 Nintendo Switch: Статус сертифікації та контроль витраченого часу")
            chart_timing_df = pipeline_df[pipeline_df["Плановий строк"] > 0].copy()
            if not chart_timing_df.empty:
                fig_timing = go.Figure()
                fig_timing.add_trace(go.Bar(x=chart_timing_df["Гра"], y=chart_timing_df["Плановий строк"], name="Плановий строк (днів)", marker_color="#3b82f6"))
                fig_timing.add_trace(go.Bar(x=chart_timing_df["Гра"], y=chart_timing_df["Факт до сабміту"], name="Фактичний строк (днів)", marker_color="#ef4444"))
                fig_timing.update_layout(
                    barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#e2e8f0"), height=300, margin=dict(t=20, b=20, l=10, r=10),
                    title="Порівняння: Плановий строк розробки проти Фактичного до сертифікації (дні)"
                )
                st.plotly_chart(fig_timing, use_container_width=True)

            sw_cols = [c for c in ["Гра", "Розробник", "Плановий строк", "Факт до сабміту", "Switch Білд Дата", "Статус Lotcheck", "Прийнято Lotcheck", "Днів у Lotcheck", "Спроби Lotcheck"] if c in pipeline_df.columns]
            sw_df = pipeline_df[pipeline_df["Switch"] == True][sw_cols].copy()
            
            edited_sw_df = st.data_editor(
                sw_df,
                column_config={
                    "Плановий строк": st.column_config.NumberColumn("План (дн)"),
                    "Факт до сабміту": st.column_config.NumberColumn("Факт (дн)"),
                    "Днів у Lotcheck": st.column_config.NumberColumn("Днів у Lotcheck"),
                    "Статус Lotcheck": st.column_config.SelectboxColumn("Результат Lotcheck", options=["In Development", "In testing", "Submitted for lotcheck", "Passed Lotcheck", "Blocked"])
                },
                hide_index=True,
                use_container_width=True,
                height=420
            )

        elif "Xbox" in cab_choice:
            st.markdown("#### 🟢 Xbox: Пайплайн подачі та схвалення концептів")
            st.caption("ℹ️ Рескіни тільки для Switch автоматично приховано:")
            xb_cols = [c for c in ["Гра", "Розробник", "Xbox", "Xbox Концепт", "Xbox TLA", "Планова дата", "Нюанси"] if c in pipeline_df.columns]
            xb_df = pipeline_df[pipeline_df["Xbox"] == True][xb_cols].copy()
            
            edited_xb_df = st.data_editor(
                xb_df,
                column_config={
                    "Xbox": st.column_config.CheckboxColumn("Участь у Xbox"),
                    "Xbox Концепт": st.column_config.CheckboxColumn("Концепт відправлено / схвалено"),
                    "Xbox TLA": st.column_config.CheckboxColumn("TLA підписано")
                },
                hide_index=True,
                use_container_width=True,
                height=380
            )

        else:
            st.markdown("#### 🔵 PlayStation: Статус розгортання продуктів")
            st.info("🔒 **Політика студії:** Флагманські проекти (наприклад, Мелтопія) не випускаються з акаунтів розробників. Очікуємо налаштування власного безпечного акаунту видавця.")
            ps_cols = [c for c in ["Гра", "Розробник", "PlayStation", "PS Продукт", "Планова дата", "Нюанси"] if c in pipeline_df.columns]
            ps_df = pipeline_df[pipeline_df["PlayStation"] == True][ps_cols].copy()
            st.dataframe(ps_df, hide_index=True, use_container_width=True, height=380)

    with pipe_tab3:
        st.markdown("### 🚨 Оперативні блокери та розподіл задач")
        b_left, b_right = st.columns(2)
        with b_left:
            st.markdown("#### 🧪 Очікують перевірки QA (Антон перед сабмітом):")
            qa_waiting = pipeline_df[pipeline_df["Нюанси"].astype(str).str.contains("Антон|тест|issue", case=False)]
            for _, q_row in qa_waiting.iterrows():
                st.markdown(f"""
                <div class="blocker-box">
                    <h5 style="margin:0; color:#fff;">🎮 {q_row['Гра']} ({q_row['Розробник']})</h5>
                    <p style="margin:4px 0 0 0; font-size:12px; color:#fca5a5;"><b>Статус:</b> {q_row['Нюанси']}</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("#### 🎨 Задачі на арт-відділ (Художниці):")
            art_waiting = pipeline_df[pipeline_df["Художник"].astype(str).str.strip() != ""]
            for _, a_row in art_waiting.iterrows():
                st.markdown(f"""
                <div style="background:#171724; border-left:4px solid #a855f7; border:1px solid #28283c; border-radius:8px; padding:10px 14px; margin-bottom:8px;">
                    <b style="color:#fff;">{a_row['Гра']}</b> ➔ Художник: <span style="color:#d946ef;">{a_row['Художник']}</span>
                    <p style="margin:2px 0 0 0; font-size:12px; color:#94a3b8;">{a_row['Нюанси']}</p>
                </div>
                """, unsafe_allow_html=True)

        with b_right:
            st.markdown("#### 🧠 Ключові принципи та правила виробництва:")
            st.markdown("""
            * **🎯 Стратегія рескінів:** Усі ігри-рескіни (*Gnome from Hell, Monkey Shop, Bad Dog, Cat Simulator, Dead Seek, 11 o'clock, Tsunami*) виходять **виключно на Nintendo Switch**.
            * **⚠️ Відхилення на Lotcheck $\\neq$ Патч:** Якщо білд завернули з багами під час сертифікації — це доопрацювання поточного білда. Патч створюється тільки після успішного релізу.
            * **🔞 Вікові рейтинги (IARC / E-rating):** Інформацію на 100% заповнює розробник, оскільки він знає всі деталі контенту.
            * **📞 Підготовка до планорок:** Статуси сертифікації у порталах перевіряються перед дзвінком, щоб одразу оголошувати результат команді.
            """)


# ==============================================================================
# 📋 РОЗДІЛ 4: RELEASE ACTIVITY (ПОВНА СИНХРОНІЗАЦІЯ З GOOGLE SHEETS)
# ==============================================================================
elif app_mode == "📋 Release Activity":
    st.title("📋 Release Marketing & Launch Activity Hub")
    st.caption("Маркетинговий чек-лист підготовки до релізів • Джерело правди: Google Sheets • Автоматичний прорахунок готовності")

    # Джерело даних: або окрема вкладка ACTIVITY_SHEET_URL, або основний аркуш
    active_act_source = ACTIVITY_SHEET_URL if ACTIVITY_SHEET_URL else GOOGLE_SHEET_URL

    with st.expander("⚙️ Налаштування джерела Google Sheets для Release Activity", expanded=False):
        c_act_url = st.text_input("URL Таблиці з маркетинговими чекбоксами (з #gid=...):", active_act_source)
        if st.button("🔄 Оновити дані активностей"):
            st.cache_data.clear()
            st.rerun()

    sheet_data = load_activity_from_sheet(c_act_url) if c_act_url else pd.DataFrame()
    base_df = sheet_data if not sheet_data.empty else raw_df.copy()

    # Пошук назви гри та дати
    act_title_col = next((c for c in base_df.columns if any(k in c.lower() for k in ["title", "гра", "game", "назва"])), base_df.columns[0])
    act_date_col = next((c for c in base_df.columns if any(k in c.lower() for k in ["release date", "release", "date", "дата"])), None)
    act_status_col = next((c for c in base_df.columns if "status" in c.lower() or "статус" in c.lower()), None)

    activity_rows = []
    overdue_alerts = []
    now_date = datetime.now()

    for _, r in base_df.iterrows():
        g_name = str(r.get(act_title_col, "")).strip()
        if not g_name or g_name.lower() == 'nan' or g_name.lower() == 'none':
            continue

        raw_d = r.get(act_date_col, "—") if act_date_col else "—"
        parsed_dt = parse_flexible_date(raw_d)
        date_str = parsed_dt.strftime("%d.%m.%Y") if parsed_dt else str(raw_d)

        raw_stat = str(r.get(act_status_col, "In Progress")).strip()
        if "released" in raw_stat.lower() or "done" in raw_stat.lower():
            status_badge = "🟢 Done"
        else:
            status_badge = "🟡 In Progress"

        row_item = {
            "Гра": g_name,
            "Дата релізу": date_str,
            "Статус": status_badge
        }

        checked_count = 0
        for task in ACTIVITY_CHECKBOX_COLS:
            is_done = is_truthy(r.get(task, False))
            row_item[task] = is_done
            if is_done:
                checked_count += 1

        pct_val = int(round((checked_count / len(ACTIVITY_CHECKBOX_COLS)) * 100))
        row_item["Готовність (%)"] = pct_val
        activity_rows.append(row_item)

        # Контроль тривожних релізів: якщо реліз скоро (< 14 дн.), а маркетинг < 70%
        if parsed_dt and status_badge == "🟡 In Progress":
            days_left = (parsed_dt - now_date).days
            if 0 <= days_left <= 14 and pct_val < 70:
                overdue_alerts.append((g_name, days_left, pct_val))

    act_df = pd.DataFrame(activity_rows)

    if not act_df.empty:
        # KPI Метрики
        total_tracked = len(act_df)
        in_progress_count = len(act_df[act_df["Статус"].str.contains("Progress")])
        done_count = len(act_df[act_df["Статус"].str.contains("Done")])
        avg_progress = int(round(act_df["Готовність (%)"].mean()))

        ak1, ak2, ak3, ak4 = st.columns(4)
        ak1.markdown(f'<div class="kpi-card"><div class="kpi-label">🎮 Ігор у трекері</div><div class="kpi-value">{total_tracked}</div><span class="kpi-badge badge-total">Повний каталог</span></div>', unsafe_allow_html=True)
        ak2.markdown(f'<div class="kpi-card"><div class="kpi-label">🛠️ В роботі (In Progress)</div><div class="kpi-value" style="color:#f59e0b !important;">{in_progress_count}</div><span class="kpi-badge badge-switch">Підготовка</span></div>', unsafe_allow_html=True)
        ak3.markdown(f'<div class="kpi-card"><div class="kpi-label">🟢 Випущено (Done)</div><div class="kpi-value" style="color:#4ade80 !important;">{done_count}</div><span class="kpi-badge badge-xbox">100% готовність</span></div>', unsafe_allow_html=True)
        ak4.markdown(f'<div class="kpi-card"><div class="kpi-label">📊 Середня готовність</div><div class="kpi-value" style="color:#38bdf8 !important;">{avg_progress}%</div><span class="kpi-badge badge-ps">По всій базі</span></div>', unsafe_allow_html=True)

        # Сповіщення про гарячі дедлайни
        if overdue_alerts:
            st.markdown("<br>", unsafe_allow_html=True)
            for g_alert, d_left, p_val in overdue_alerts:
                st.markdown(f"""
                <div class="alert-card-yellow">
                    <b style="color:#fff; font-size:15px;">⏳ Увага! {g_alert}</b> ➔ 
                    <span style="color:#fde047; font-weight:bold;">Реліз через {d_left} дн., а маркетинг готовий лише на {p_val}%!</span>
                    <p style="margin:2px 0 0 0; font-size:12px; color:#cbd5e1;">Необхідно терміново закрити хвости по трейлерах, формах або Keymailer.</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Фільтр
        f_c1, f_c2 = st.columns([2, 1.5])
        with f_c1:
            display_filter = st.radio("Показати проекти:", ["Всі проекти", "Тільки в роботі (In Progress)", "Тільки завершені (Done)"], horizontal=True)
        with f_c2:
            if c_act_url:
                st.link_button("↗️ Відкрити Google Таблицю для редагування", c_act_url, use_container_width=True)

        if display_filter == "Тільки в роботі (In Progress)":
            view_act_df = act_df[act_df["Статус"].str.contains("Progress")].copy()
        elif display_filter == "Тільки завершені (Done)":
            view_act_df = act_df[act_df["Статус"].str.contains("Done")].copy()
        else:
            view_act_df = act_df.copy()

        # Конфігурація колонок: красивий прогрес-бар, фіксована ширина без обрізання тексту
        col_view_config = {
            "Гра": st.column_config.TextColumn("Назва гри (Title)", width="medium"),
            "Дата релізу": st.column_config.TextColumn("Дата релізу", width="small"),
            "Статус": st.column_config.TextColumn("Статус", width="small"),
            "Готовність (%)": st.column_config.ProgressColumn(
                "Готовність маркетингу",
                format="%d%%",
                min_value=0,
                max_value=100,
                width="medium"
            )
        }
        
        for task in ACTIVITY_CHECKBOX_COLS:
            col_view_config[task] = st.column_config.CheckboxColumn(task, width="small", disabled=True)

        ordered_cols = ["Гра", "Дата релізу", "Статус", "Готовність (%)"] + ACTIVITY_CHECKBOX_COLS
        st.dataframe(
            view_act_df[ordered_cols],
            column_config=col_view_config,
            hide_index=True,
            use_container_width=True,
            height=520
        )

        csv_act_out = view_act_df[ordered_cols].to_csv(index=False).encode('utf-8')
        st.download_button("📥 Експортувати звіт активностей (.CSV)", data=csv_act_out, file_name="release_activities_report.csv", mime="text/csv")
    else:
        st.info("💡 Не знайдено проектів для відображення.")


# ==============================================================================
# 🎯 РОЗДІЛ 5: ЦІЛІ ТА KPI 2026
# ==============================================================================
elif app_mode == "🎯 Цілі та KPI 2026":
    st.title("🎯 Виконання річного та квартальних планів (2026)")
    st.caption("Ціль на 2026 рік: **$500,000 консольної виручки** • Дані синхронізуються з Weekly Updates")

    if weekly_df.empty:
        st.warning("⚠️ Вкажи валідне посилання на тижневу вкладку з `#gid=...` у рядку `WEEKLY_SHEET_URL`.")
        st.stop()

    q_df = prepare_quarterly_data(weekly_df)
    if q_df.empty:
        st.info("💡 У щотижневій таблиці немає валідних дат для розрахунку 2026 року.")
        st.stop()

    col_sel, col_info = st.columns([1.5, 2.5])
    with col_sel:
        period_choice = st.radio("📌 Оберіть період для аналізу:", ["Year 2026 (Весь рік)", "Q1 2026", "Q2 2026", "Q3 2026", "Q4 2026"], horizontal=True)

    if period_choice == "Year 2026 (Весь рік)":
        fact_period_df = q_df[q_df["Year"] == 2026]
    else:
        q_label = period_choice.split(" ")[0] + " 2026"
        fact_period_df = q_df[q_df["Quarter"] == q_label]

    fact_rev = float(fact_period_df["Total_Revenue"].sum()) if not fact_period_df.empty else 0.0
    fact_sw = float(fact_period_df["Nintendo_Revenue"].sum()) if not fact_period_df.empty else 0.0
    fact_ps = float(fact_period_df["PS_Revenue"].sum()) if not fact_period_df.empty else 0.0
    fact_xb = float(fact_period_df["Xbox_Revenue"].sum()) if not fact_period_df.empty else 0.0

    fact_deals = int(fact_period_df["Deals"].sum()) if "Deals" in fact_period_df.columns else 0
    fact_calls = int(fact_period_df["Calls"].sum()) if "Calls" in fact_period_df.columns else 0
    fact_contacts = int(fact_period_df["Contacts"].sum()) if "Contacts" in fact_period_df.columns else 0
    fact_leads = int(fact_period_df["Leads"].sum()) if "Leads" in fact_period_df.columns else 0

    target = TARGETS_2026[period_choice]
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

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🎮 Виконання плану виручки за платформами")
    k1, k2, k3 = st.columns(3)
    k1.metric("🔴 Nintendo Switch", f"${fact_sw:,.0f}", f"{(fact_sw/max(target['Nintendo_Revenue'],1.0))*100:.1f}% від цілі")
    k2.metric("🔵 PlayStation", f"${fact_ps:,.0f}", f"{(fact_ps/max(target['PS_Revenue'],1.0))*100:.1f}% від цілі")
    k3.metric("🟢 Xbox", f"${fact_xb:,.0f}", f"{(fact_xb/max(target['Xbox_Revenue'],1.0))*100:.1f}% від цілі")

    st.markdown("---")
    st.subheader("🎯 BizDev Воронка: План vs Факт підписання")
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("🤝 Deals (Угоди)", f"{fact_deals} / {target['Deals']}")
    b2.metric("📞 Calls (Дзвінки)", f"{fact_calls} / {target['Calls']}")
    b3.metric("✉️ Contacts (Контакти)", f"{fact_contacts} / {target['Contacts']}")
    b4.metric("🔍 Leads (Знайдено лідів)", f"{fact_leads} / {target['Leads']}")

    st.markdown("---")
    c_p1, c_p2 = st.columns([1.5, 1])
    with c_p1:
        st.subheader("📊 Порівняння: План vs Факт по платформах ($)")
        chart_plan_df = pd.DataFrame({
            "Платформа": ["Nintendo Switch", "PlayStation", "Xbox"],
            "Факт ($)": [fact_sw, fact_ps, fact_xb],
            "План ($)": [target["Nintendo_Revenue"], target["PS_Revenue"], target["Xbox_Revenue"]]
        })
        fig_plan = go.Figure()
        fig_plan.add_trace(go.Bar(x=chart_plan_df["Платформа"], y=chart_plan_df["Факт ($)"], name="ФАКТ", marker_color="#10b981"))
        fig_plan.add_trace(go.Bar(x=chart_plan_df["Платформа"], y=chart_plan_df["План ($)"], name="ПЛАН", marker_color="#d946ef"))
        fig_plan.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), height=360)
        st.plotly_chart(fig_plan, use_container_width=True)

    with c_p2:
        st.subheader("📋 Зведена таблиця кварталів 2026")
        q_summary = []
        for q_key in ["Q1 2026", "Q2 2026", "Q3 2026", "Q4 2026"]:
            q_f = q_df[q_df["Quarter"] == q_key]
            q_rev_fact = float(q_f["Total_Revenue"].sum()) if not q_f.empty else 0.0
            q_target_rev = TARGETS_2026[q_key]["Revenue"]
            q_deals_fact = int(q_f["Deals"].sum()) if "Deals" in q_f.columns else 0
            q_deals_target = TARGETS_2026[q_key]["Deals"]
            q_summary.append({
                "Квартал": q_key,
                "Факт ($)": f"${q_rev_fact:,.0f}",
                "План ($)": f"${q_target_rev:,.0f}",
                "Виконання": f"{(q_rev_fact/q_target_rev)*100:.1f}%",
                "Угоди": f"{q_deals_fact}/{q_deals_target}"
            })
        st.dataframe(pd.DataFrame(q_summary), use_container_width=True, hide_index=True)


# ==============================================================================
# 📈 РОЗДІЛ 6: ТИЖНЕВА ДИНАМІКА
# ==============================================================================
elif app_mode == "📈 Тижнева динаміка (WoW)":
    st.title("📈 Тижневий пульс видавництва (Week-over-Week)")
    st.caption("Динаміка консольних зборів, вішлістів, повна воронка лідогенерації та соцмережі")

    if weekly_df.empty:
        st.warning("⚠️ Вкажи валідне посилання на тижневу вкладку з `#gid=...` у рядку `WEEKLY_SHEET_URL`.")
        st.stop()

    st.markdown("---")
    w_f_col1, w_f_col2 = st.columns([1.2, 2.8])
    with w_f_col1:
        w_period_mode = st.radio(
            "Період аналізу тижнів:",
            ["📅 Весь період", "🗓️ Діапазон дат (Start / End)"],
            index=0
        )

    valid_dates = weekly_df["Parsed_Date"].dropna()
    min_d = valid_dates.min().date() if not valid_dates.empty else datetime.now().date() - timedelta(days=90)
    max_d = valid_dates.max().date() if not valid_dates.empty else datetime.now().date()

    with w_f_col2:
        if w_period_mode == "🗓️ Діапазон дат (Start / End)":
            date_range = st.date_input(
                "Оберіть діапазон (Start Date ➔ End Date):",
                value=(min_d, max_d),
                min_value=min_d,
                max_value=max_d + timedelta(days=365)
            )
            if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
                start_val, end_val = date_range
                active_weekly_df = weekly_df[(weekly_df["Parsed_Date"].dt.date >= start_val) & (weekly_df["Parsed_Date"].dt.date <= end_val)].copy()
            else:
                active_weekly_df = weekly_df.copy()
        else:
            active_weekly_df = weekly_df.copy()

    st.markdown("<br>", unsafe_allow_html=True)

    last_week = active_weekly_df.iloc[-1] if not active_weekly_df.empty else weekly_df.iloc[-1]
    prev_week = active_weekly_df.iloc[-2] if len(active_weekly_df) > 1 else last_week

    tot_w_rev = active_weekly_df["Total_Revenue"].sum()
    tot_w_sales = active_weekly_df["Total_Sales"].sum()
    last_w_total_rev = last_week.get("Total_Revenue", 0.0)
    prev_w_total_rev = prev_week.get("Total_Revenue", 0.0)
    wow_delta = ((last_w_total_rev - prev_w_total_rev) / max(prev_w_total_rev, 1.0)) * 100

    wk1, wk2, wk3, wk4 = st.columns(4)
    wk1.metric(f"Виторг за обраний період ({len(active_weekly_df)} тиж.)", f"${tot_w_rev:,.2f}", f"{wow_delta:+.1f}% останній тиждень")
    wk2.metric("PlayStation виторг", f"${active_weekly_df['PS_Revenue'].sum():,.2f}")
    wk3.metric("Nintendo Switch виторг", f"${active_weekly_df['Nintendo_Revenue'].sum():,.2f}")
    wk4.metric("Xbox виторг", f"${active_weekly_df['Xbox_Revenue'].sum():,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)

    w_tab1, w_tab2, w_tab3, w_tab4 = st.tabs([
        "💰 Консольний виторг & Продажі",
        "🎯 BizDev Воронка & Конверсії",
        "📱 Маркетинг & Аудиторія",
        "📑 Повна тижнева таблиця"
    ])

    with w_tab1:
        st.subheader("Динаміка виторгу по тижнях ($)")
        rev_chart_df = []
        for _, rw in active_weekly_df.iterrows():
            lbl = f"{rw.get('From', '')}"
            rev_chart_df.append({"Week": lbl, "Platform": "PlayStation", "Revenue": rw.get("PS_Revenue", 0.0)})
            rev_chart_df.append({"Week": lbl, "Platform": "Nintendo Switch", "Revenue": rw.get("Nintendo_Revenue", 0.0)})
            rev_chart_df.append({"Week": lbl, "Platform": "Xbox", "Revenue": rw.get("Xbox_Revenue", 0.0)})
            
        fig_w_rev = px.bar(pd.DataFrame(rev_chart_df), x="Week", y="Revenue", color="Platform", barmode="group", color_discrete_map={"Nintendo Switch": "#e60012", "PlayStation": "#3b82f6", "Xbox": "#107c10"})
        fig_w_rev.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), yaxis_title="Виторг ($)")
        st.plotly_chart(fig_w_rev, use_container_width=True)

        st.markdown("---")
        st.subheader("Динаміка продажів у копіях (Units Sold)")
        sales_chart_df = []
        for _, rw in active_weekly_df.iterrows():
            lbl = f"{rw.get('From', '')}"
            sales_chart_df.append({"Week": lbl, "Platform": "PlayStation", "Sales": rw.get("PS_Sales", 0.0)})
            sales_chart_df.append({"Week": lbl, "Platform": "Nintendo Switch", "Sales": rw.get("Nintendo_Sales", 0.0)})
            sales_chart_df.append({"Week": lbl, "Platform": "Xbox", "Sales": rw.get("Xbox_Sales", 0.0)})
            
        fig_w_sales = px.line(pd.DataFrame(sales_chart_df), x="Week", y="Sales", color="Platform", markers=True, color_discrete_map={"Nintendo Switch": "#e60012", "PlayStation": "#3b82f6", "Xbox": "#107c10"})
        fig_w_sales.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), yaxis_title="Продано копій (шт)")
        st.plotly_chart(fig_w_sales, use_container_width=True)

    with w_tab2:
        st.subheader("🎯 Повна воронка залучення проектів (Leads ➔ Deals)")
        st.caption("Аналіз конверсії: Додано лідів ➔ Запущено Sequence ➔ Отримано відповідей ➔ Зацікавлені ➔ Дзвінки ➔ Угоди")

        tot_leads = float(active_weekly_df["Leads"].sum()) if "Leads" in active_weekly_df.columns else 0.0
        tot_seq = float(active_weekly_df["Sequence_Started"].sum()) if "Sequence_Started" in active_weekly_df.columns else 0.0
        tot_contacts = float(active_weekly_df["Contacts"].sum()) if "Contacts" in active_weekly_df.columns else 0.0
        tot_opps = float(active_weekly_df["Opportunities"].sum()) if "Opportunities" in active_weekly_df.columns else 0.0
        tot_calls = float(active_weekly_df["Calls"].sum()) if "Calls" in active_weekly_df.columns else 0.0
        tot_deals = float(active_weekly_df["Deals"].sum()) if "Deals" in active_weekly_df.columns else 0.0

        conv_leads_seq = (tot_seq / max(tot_leads, 1.0)) * 100
        conv_seq_contacts = (tot_contacts / max(tot_seq if tot_seq > 0 else tot_leads, 1.0)) * 100
        conv_contacts_opps = (tot_opps / max(tot_contacts, 1.0)) * 100 if tot_opps > 0 else 100.0
        conv_opps_calls = (tot_calls / max(tot_opps if tot_opps > 0 else tot_contacts, 1.0)) * 100
        conv_calls_deals = (tot_deals / max(tot_calls, 1.0)) * 100

        fc1, fc2, fc3, fc4, fc5, fc6 = st.columns(6)
        fc1.metric("🔍 1. Leads", f"{int(tot_leads):,}", "Додано")
        fc2.metric("🚀 2. Sequence", f"{int(tot_seq):,}", f"{conv_leads_seq:.1f}% аутріч")
        fc3.metric("✉️ 3. Contacts", f"{int(tot_contacts):,}", f"{conv_seq_contacts:.1f}% відповіли")
        fc4.metric("🎯 4. Opps", f"{int(tot_opps):,}", f"{conv_contacts_opps:.1f}% інтерес" if tot_opps > 0 else "—")
        fc5.metric("📞 5. Calls", f"{int(tot_calls):,}", f"{conv_opps_calls:.1f}% коли")
        fc6.metric("🤝 6. Deals", f"{int(tot_deals):,}", f"{conv_calls_deals:.1f}% закриття")

        st.markdown("<br>", unsafe_allow_html=True)

        funnel_stages = [
            "1. Leads (Додані ліди)",
            "2. Sequence Started (Кому написали)",
            "3. Contacts (Отримано відповідей)",
            "4. Opportunities (Зацікавлені)",
            "5. Calls (Дзвінки / Коли)",
            "6. Deals (Підписані договори)"
        ]
        funnel_values = [tot_leads, tot_seq if tot_seq > 0 else tot_leads * 0.8, tot_contacts, tot_opps if tot_opps > 0 else tot_contacts * 0.7, tot_calls, tot_deals]

        fig_funnel = go.Figure(go.Funnel(
            y=funnel_stages,
            x=funnel_values,
            textinfo="value+percent initial+percent previous",
            marker=dict(color=["#6366f1", "#8b5cf6", "#a855f7", "#d946ef", "#f59e0b", "#10b981"]),
            connector={"line": {"color": "#475569", "width": 1.5}}
        ))
        fig_funnel.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), height=380, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_funnel, use_container_width=True)

        st.markdown("---")
        st.subheader("📊 Тижнева динаміка воронки (Leads ➔ Deals)")
        bd_cols_chart = [c for c in ["Leads", "Sequence_Started", "Contacts", "Opportunities", "Calls", "Deals"] if c in active_weekly_df.columns]
        fig_bd_bar = px.bar(active_weekly_df, x="From", y=bd_cols_chart, barmode="group", color_discrete_sequence=["#6366f1", "#8b5cf6", "#a855f7", "#d946ef", "#f59e0b", "#10b981"])
        fig_bd_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), xaxis_title="Тиждень", yaxis_title="Кількість")
        st.plotly_chart(fig_bd_bar, use_container_width=True)

    with w_tab3:
        st.subheader("📱 Ріст аудиторії та соцмереж видавництва")
        social_cols = [c for c in ["Twitter", "TikTok", "YouTube", "Discord", "Instagram"] if c in active_weekly_df.columns]
        if social_cols:
            fig_social = px.line(active_weekly_df, x="From", y=social_cols, markers=True)
            fig_social.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), xaxis_title="Тиждень", yaxis_title="Підписників")
            st.plotly_chart(fig_social, use_container_width=True)

    with w_tab4:
        st.subheader("📑 Повний архів щотижневої звітності")
        st.dataframe(active_weekly_df, use_container_width=True, height=450)
        csv_w = active_weekly_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Експортувати тижневий звіт (.CSV)", data=csv_w, file_name="upscale_weekly_reporting.csv", mime="text/csv")


# ==============================================================================
# 🧮 РОЗДІЛ 7: КАЛЬКУЛЯТОР ПРОГНОЗІВ
# ==============================================================================
elif app_mode == "🧮 Калькулятор прогнозів":
    st.title("🧮 Sourcing & Lead Forecasting Hub")
    st.caption("Оцінка нових лідів за відкаліброваними 30 піджанрами та формування пайплайну")

    calc_tab1, calc_tab2 = st.tabs([
        "🧮 Інтерактивний калькулятор ліда",
        "📋 Таблиця куди збираються ліди"
    ])

    with calc_tab1:
        sb_left, sb_right = st.columns([1, 1.25])

        with sb_left:
            st.markdown('<div class="sandbox-box">', unsafe_allow_html=True)
            st.markdown("#### 1. Вхідні дані ліда")
            
            calc_name = st.text_input("Назва гри / ліда:", "Project Prototype")
            calc_link = st.text_input("🔗 Посилання на гру (Steam / GP / itch / Web):", "https://store.steampowered.com/app/...")
            calc_src = st.selectbox("Джерело аналізу:", ["Steam", "Google Play", "CrazyGames / Web", "itch.io"])
            
            if calc_src == "Steam":
                s_rev = st.number_input("Steam All-Time Revenue ($):", min_value=0, value=6000, step=1000)
                b_metric = (s_rev * 0.10) + 500.0
            elif calc_src == "Google Play":
                gp_installs = st.number_input("Завантаження Google Play (Installs):", min_value=0, value=500000, step=50000)
                b_metric = (math.sqrt(gp_installs) * 2.0) + 800.0 if gp_installs > 0 else 0.0
            elif calc_src == "CrazyGames / Web":
                cg_r = st.number_input("Кількість відгуків / оцінок:", min_value=0, value=3500, step=500)
                b_metric = (cg_r * 0.05) + 900.0
            else:
                itch_r = st.number_input("Оцінки itch.io:", min_value=0, value=40, step=5)
                b_metric = (itch_r * 10.0) + 400.0

            st.markdown("---")
            st.markdown("#### 2. Жанр і Ціноутворення")
            calc_genre = st.selectbox("Точний піджанр гри:", list(GENRE_DATABASE.keys()))
            calc_price = st.selectbox("Планова ціна на консолях ($):", list(PRICE_MODIFIERS.keys()), index=4)
            st.markdown('</div>', unsafe_allow_html=True)

        g_cfg = GENRE_DATABASE[calc_genre]
        p_mod = PRICE_MODIFIERS.get(calc_price, 1.0)

        ps_est = b_metric * g_cfg["PS"] * p_mod
        ns_est = b_metric * g_cfg["Switch"] * p_mod
        xb_est = b_metric * g_cfg["Xbox"] * p_mod
        tot_m1 = ps_est + ns_est + xb_est
        tot_year = tot_m1 * g_cfg["Decay"]

        studio_gross_margin_m1 = tot_m1 * 0.315
        studio_gross_margin_year = tot_year * 0.315

        with sb_right:
            st.markdown('<div class="sandbox-box">', unsafe_allow_html=True)
            st.markdown(f"### 📈 Розрахунок: **{calc_name}**")
            st.caption(f"💡 *{g_cfg['Desc']}*")
            st.caption(f"Органічна база: **${b_metric:,.1f}** | Ціновий множник: **{p_mod}x**")
            
            if tot_m1 >= 6500:
                st.success("🟢 **ТОП ЛІД:** Рекомендовано надсилати пітч (M1 > $6.5k)")
                status_rec = "✅ ТОП ЛІД"
            elif tot_m1 >= 3000:
                st.info("🟡 **СТАНДАРТНИЙ ТАЙТЛ:** Стабільний кандидат ($3k–$6.5k)")
                status_rec = "⚠️ СТАНДАРТ"
            else:
                st.warning("🔴 **ВИСОКИЙ РИЗИК:** Низька прогнозована каса (M1 < $3k)")
                status_rec = "❌ РИЗИК"

            st.markdown("---")
            m_c1, m_c2, m_c3 = st.columns(3)
            m_c1.metric("PlayStation (M1)", f"${ps_est:,.0f}", f"{g_cfg['PS']}x")
            m_c2.metric("Nintendo Switch (M1)", f"${ns_est:,.0f}", f"{g_cfg['Switch']}x")
            m_c3.metric("Xbox (M1)", f"${xb_est:,.0f}", f"{g_cfg['Xbox']}x")

            st.markdown("<br>", unsafe_allow_html=True)
            t_c1, t_c2 = st.columns(2)
            t_c1.metric("🔥 Всього Gross M1", f"${tot_m1:,.0f}", f"Дохід студії: ${studio_gross_margin_m1:,.0f}")
            t_c2.metric("📅 Річний Gross (1Y)", f"${tot_year:,.0f}", f"Дохід студії: ${studio_gross_margin_year:,.0f}")

            if st.button("➕ Зберегти цей лід (в таблицю та Google Sheets)", use_container_width=True):
                new_lead_entry = {
                    "Дата": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Назва гри": calc_name,
                    "Посилання": calc_link,
                    "Джерело": calc_src,
                    "Жанр": calc_genre,
                    "Ціна ($)": calc_price,
                    "Base Metric": round(b_metric, 1),
                    "PS M1 ($)": round(ps_est, 1),
                    "Switch M1 ($)": round(ns_est, 1),
                    "Xbox M1 ($)": round(xb_est, 1),
                    "Total M1 ($)": round(tot_m1, 1),
                    "Studio Margin M1 ($)": round(studio_gross_margin_m1, 1),
                    "1Y LTV ($)": round(tot_year, 1),
                    "Рекомендація": status_rec
                }
                st.session_state.scouted_leads.append(new_lead_entry)
                
                if GOOGLE_WEBHOOK_URL:
                    try:
                        res = requests.post(GOOGLE_WEBHOOK_URL, json=new_lead_entry, timeout=5)
                        if res.status_code == 200:
                            st.toast("🚀 Успішно записано в Google Таблицю на вкладку Leads!")
                    except Exception as e:
                        st.warning(f"Збережено локально. Помилка Webhook: {e}")
                else:
                    st.toast(f"✅ Лід '{calc_name}' збережено!")

            st.markdown('</div>', unsafe_allow_html=True)

    with calc_tab2:
        st.subheader("📋 Сформований пайплайн нових лідів")
        if st.session_state.scouted_leads:
            leads_df = pd.DataFrame(st.session_state.scouted_leads)
            total_lead_col = next((c for c in leads_df.columns if "total" in c.lower()), None)
            if total_lead_col:
                leads_df[total_lead_col] = pd.to_numeric(leads_df[total_lead_col], errors="coerce").fillna(0.0)
                tot_pipeline_val = float(leads_df[total_lead_col].sum())
                avg_lead_val = float(leads_df[total_lead_col].mean())
            else:
                tot_pipeline_val, avg_lead_val = 0.0, 0.0
            
            k_l1, k_l2, k_l3 = st.columns(3)
            k_l1.metric("Зібрано лідів", len(leads_df))
            k_l2.metric("Потенціал Gross M1", f"${tot_pipeline_val:,.2f}")
            k_l3.metric("Очікуваний дохід студії (31.5%)", f"${tot_pipeline_val * 0.315:,.2f}")

            st.markdown("---")
            lead_cfg = {}
            if "Посилання" in leads_df.columns:
                lead_cfg["Посилання"] = st.column_config.LinkColumn("Посилання на гру", display_text="Відкрити ↗")
            
            st.dataframe(leads_df, column_config=lead_cfg, use_container_width=True, height=400)
            
            c_d1, c_d2 = st.columns([1, 4])
            with c_d1:
                csv_leads = leads_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Експортувати ліди (.CSV)", data=csv_leads, file_name="upscale_scouted_leads.csv", mime="text/csv")
            with c_d2:
                if st.button("🗑️ Очистити список лідів"):
                    st.session_state.scouted_leads = []
                    st.rerun()
        else:
            st.info("💡 Таблиця лідів порожня. Розрахуй гру у вкладці калькулятора та натисни '➕ Зберегти цей лід'.")
