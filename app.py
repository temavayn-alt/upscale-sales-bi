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
# 🔗 НАЛАШТУВАННЯ ТАБЛИЦЬ ТА ЗБЕРЕЖЕННЯ:
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?usp=sharing"
WEEKLY_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?gid=1342107748#gid=1342107748"
GOOGLE_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzrYmeab3xtC4TW9id-N60pI6UmOk6OJj7L2OebkV48omIzqD_h827g3C1mSUpt_WusyA/exec"
ANTHROPIC_API_KEY = ""  # Залиш порожнім або додай у Secrets
ACTIVITY_STORAGE_FILE = "release_activity_state.json"
PIPELINE_STORAGE_FILE = "pipeline_master_state.json"
LOGO_FILE = "up4.png"
# ==============================================================================

# Перевірка наявності логотипу для favicon
page_icon_setting = LOGO_FILE if os.path.exists(LOGO_FILE) else "🎮"

st.set_page_config(
    page_title="Upscale Studio | Console BI & Growth Hub",
    page_icon=page_icon_setting,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Професійні стилі темної теми + градієнти бренду + елегантне меню без кружечків
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    
    /* 1. СТИЛЬНІ ПЛАШКИ-КНОПКИ В МЕНЮ САЙДБАРУ */
    section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background-color: #171724 !important;
        border: 1px solid #28283c !important;
        border-radius: 9px !important;
        padding: 9px 14px !important;
        margin-bottom: 6px !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: #222235 !important;
        border-color: #a855f7 !important;
        transform: translateX(2px);
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"],
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(90deg, rgba(192, 38, 211, 0.22) 0%, rgba(249, 115, 22, 0.16) 100%) !important;
        border: 1px solid #d946ef !important;
        box-shadow: 0 2px 10px rgba(217, 70, 239, 0.15) !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] p,
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* 2. ВКЛАДКИ З ФІРМОВИМ ГРАДІЄНТОМ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 16px;
        border-bottom: 1px solid #28283c;
        background-color: transparent !important;
        padding-bottom: 0px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px;
        background-color: transparent !important;
        background: transparent !important;
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
        background: transparent !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border-bottom: 2px solid #d946ef !important;
    }

    /* 3. КАРТКИ МЕТРИК ТА ІНСАЙТІВ */
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
    .report-box { background: #0f172a; border: 1px solid #334155; border-radius: 12px; padding: 24px; color: #f8fafc; }
    .blocker-box { background: #201319; border-left: 4px solid #ef4444; border: 1px solid #3f1a24; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px; }
    .alert-card-red { background: linear-gradient(135deg, #2d141e 0%, #1c0d13 100%); border: 1px solid #7f1d1d; border-left: 5px solid #ef4444; border-radius: 10px; padding: 14px; margin-bottom: 12px; }
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

# 🗓️ ГРАФІК РОЗПРОДАЖІВ NINTENDO
NINTENDO_SCHEDULE = [
    {"name": "1. Autumn Sale", "start": "2026-09-11", "end": "2026-09-24", "status": "🔥 Найближчий", "region": "Global / EU / US"},
    {"name": "2. Halloween Sale", "start": "2026-10-26", "end": "2026-11-15", "status": "🎃 Сезонний", "region": "Global"},
    {"name": "3. Holiday Sale (EU)", "start": "2026-12-17", "end": "2027-01-10", "status": "🎄 Головний (EU)", "region": "Europe / Australia"},
    {"name": "4. Holiday Sale (US)", "start": "2026-12-21", "end": "2027-01-11", "status": "🎄 Головний (US)", "region": "Americas"}
]

# 🗓️ ГРАФІК ТА ПРАВИЛА РОЗПРОДАЖІВ XBOX (2026)
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

# 30 ВІДКАЛІБРОВАНИХ ПІДЖАНРІВ
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
def load_weekly_data(sheet_url):
    if not sheet_url or "ВСТАВ_СЮДИ" in sheet_url:
        return pd.DataFrame()
    csv_url = get_export_url(sheet_url)
    try:
        raw_w = pd.read_csv(csv_url, header=None, dtype=str)
        if raw_w.empty: return pd.DataFrame()

        first_row_str = " ".join([str(x) for x in raw_w.iloc[0].tolist() if pd.notna(x)]).lower()
        second_row_str = " ".join([str(x) for x in raw_w.iloc[1].tolist() if pd.notna(x)]).lower() if len(raw_w) > 1 else ""

        if "from" in second_row_str or "sales" in second_row_str:
            data_df = raw_w.iloc[2:].copy().reset_index(drop=True)
        elif "from" in first_row_str or "sales" in first_row_str:
            data_df = raw_w.iloc[1:].copy().reset_index(drop=True)
        else:
            data_df = raw_w.copy()

        col_map = {
            0: "From", 1: "To",
            2: "Nintendo_Sales", 4: "Nintendo_Wishlists", 6: "Nintendo_Revenue",
            8: "PS_Sales", 10: "PS_Wishlists", 12: "PS_Revenue",
            14: "Xbox_Sales", 16: "Xbox_Wishlists", 18: "Xbox_Revenue",
            20: "Leads", 22: "Contacts", 24: "Calls", 26: "Deals",
            28: "Twitter", 30: "Instagram", 32: "TikTok", 34: "YouTube", 36: "Discord"
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
        return df_out.reset_index(drop=True)
    except Exception:
        return pd.DataFrame()

def prepare_quarterly_data(df_weekly):
    if df_weekly.empty or "From" not in df_weekly.columns:
        return pd.DataFrame()
    df = df_weekly.copy()
    df["Parsed_Date"] = df["From"].apply(parse_flexible_date)
    df = df.dropna(subset=["Parsed_Date"]).copy()
    df["Year"] = df["Parsed_Date"].apply(lambda d: d.year)
    df["Quarter"] = df["Parsed_Date"].apply(lambda d: f"Q{math.ceil(d.month/3)} {d.year}")
    df["Total_Revenue"] = df.get("PS_Revenue", 0.0) + df.get("Nintendo_Revenue", 0.0) + df.get("Xbox_Revenue", 0.0)
    return df

raw_df = load_data(GOOGLE_SHEET_URL)
weekly_df = load_weekly_data(WEEKLY_SHEET_URL)

if raw_df.empty:
    st.info("👋 Вкажи валідне посилання на Google Таблицю у рядку `GOOGLE_SHEET_URL`.")
    st.stop()

# Точне автовиявлення колонок з Google Таблиці
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
# 💾 ВСІ 23 ПРОЕКТИ ПАЙПЛАЙНУ ТА СТРОКИ СЕРТИФІКАЦІЇ
# ==============================================================================
SEEDED_PIPELINE_PROJECTS = [
    {"Гра": "Cat Simulator", "Розробник": "Ігор", "Художник": "", "Нюанси": "Lotcheck пройдено з 3-го разу", "Дата старту": "2026-08-06", "Планова дата": "2026-08-12", "Плановий строк": 6, "Факт до сабміту": 33, "Трейлер": True, "Картинки": True, "Тексти": True, "Дата обрана": "2026-08-12", "Switch": True, "Switch Продукт": True, "Switch Матеріали": True, "Switch Білд": True, "Switch Білд Дата": "2026-08-13", "Статус Lotcheck": "Passed Lotcheck", "Прийнято Lotcheck": "2026-09-08", "Днів у Lotcheck": 26, "Спроби Lotcheck": "3 (було 2 issues)", "Xbox": False, "Xbox Концепт": True, "Xbox TLA": False, "PlayStation": False, "PS Продукт": False},
    {"Гра": "Dead Seek", "Розробник": "Сергій", "Художник": "", "Нюанси": "Рескін тільки для Switch", "Дата старту": "", "Планова дата": "2026-10-02", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": True, "Картинки": True, "Тексти": True, "Дата обрана": "2026-10-02", "Switch": True, "Switch Продукт": True, "Switch Матеріали": True, "Switch Білд": True, "Switch Білд Дата": "", "Статус Lotcheck": "Passed Lotcheck", "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "1", "Xbox": False, "Xbox Концепт": True, "Xbox TLA": False, "PlayStation": False, "PS Продукт": False},
    {"Гра": "Hidden Objects", "Розробник": "Ігор", "Художник": "", "Нюанси": "Слабкий проект, чекаємо виправлень від дева", "Дата старту": "", "Планова дата": "2026-10-02", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": True, "Картинки": True, "Тексти": True, "Дата обрана": "2026-10-02", "Switch": True, "Switch Продукт": True, "Switch Матеріали": True, "Switch Білд": True, "Switch Білд Дата": "", "Статус Lotcheck": "Passed Lotcheck", "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "1", "Xbox": True, "Xbox Концепт": True, "Xbox TLA": True, "PlayStation": True, "PS Продукт": False},
    {"Гра": "Mother Simulation", "Розробник": "Сергій", "Художник": "", "Нюанси": "Відправлено на лотчек 08.09", "Дата старту": "", "Планова дата": "2026-09-25", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": False, "Картинки": False, "Тексти": False, "Дата обрана": "", "Switch": True, "Switch Продукт": True, "Switch Матеріали": True, "Switch Білд": True, "Switch Білд Дата": "2026-09-08", "Статус Lotcheck": "Submitted for lotcheck", "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "", "Xbox": False, "Xbox Концепт": False, "Xbox TLA": False, "PlayStation": False, "PS Продукт": False},
    {"Гра": "Escape Immersion", "Розробник": "Сергій", "Художник": "", "Нюанси": "В першу чергу Нінтендо. Xbox після апруву", "Дата старту": "", "Планова дата": "2026-09-28", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": True, "Картинки": True, "Тексти": True, "Дата обрана": "", "Switch": True, "Switch Продукт": True, "Switch Матеріали": True, "Switch Білд": True, "Switch Білд Дата": "", "Статус Lotcheck": "In testing", "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "", "Xbox": True, "Xbox Концепт": True, "Xbox TLA": False, "PlayStation": True, "PS Продукт": False},
    {"Гра": "11 o'clock", "Розробник": "Іван", "Художник": "", "Нюанси": "Білди скинуто, чекаємо перевірки Антона", "Дата старту": "", "Планова дата": "2026-09-25", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": True, "Картинки": True, "Тексти": True, "Дата обрана": "", "Switch": True, "Switch Продукт": True, "Switch Матеріали": True, "Switch Білд": False, "Switch Білд Дата": "", "Статус Lotcheck": "In testing", "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "", "Xbox": False, "Xbox Концепт": False, "Xbox TLA": False, "PlayStation": False, "PS Продукт": False},
    {"Гра": "Tsunami Escape", "Розробник": "Іван", "Художник": "", "Нюанси": "Порт займе близько 2 тижнів", "Дата старту": "2026-09-03", "Планова дата": "2026-09-21", "Плановий строк": 18, "Факт до сабміту": 0, "Трейлер": True, "Картинки": False, "Тексти": True, "Дата обрана": "", "Switch": True, "Switch Продукт": False, "Switch Матеріали": False, "Switch Білд": False, "Switch Білд Дата": "", "Статус Lotcheck": "In Development", "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "", "Xbox": False, "Xbox Концепт": False, "Xbox TLA": False, "PlayStation": False, "PS Продукт": False},
    {"Гра": "Five Nights at Pizzeria 2", "Розробник": "Сергій", "Художник": "", "Нюанси": "В процесі активного портінгу", "Дата старту": "2026-09-03", "Планова дата": "2026-09-18", "Плановий строк": 15, "Факт до сабміту": 0, "Трейлер": False, "Картинки": False, "Тексти": False, "Дата обрана": "", "Switch": True, "Switch Продукт": False, "Switch Матеріали": False, "Switch Білд": False, "Switch Білд Дата": "", "Статус Lotcheck": "In Development", "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "", "Xbox": False, "Xbox Концепт": False, "Xbox TLA": False, "PlayStation": False, "PS Продукт": False},
    {"Гра": "Race Condition", "Розробник": "Іван", "Художник": "", "Нюанси": "Чекаємо налаштування кросплатформеного онлайну", "Дата старту": "", "Планова дата": "2026-10-15", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": True, "Картинки": True, "Тексти": True, "Дата обрана": "", "Switch": True, "Switch Продукт": True, "Switch Матеріали": True, "Switch Білд": False, "Switch Білд Дата": "", "Статус Lotcheck": "In testing", "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "", "Xbox": True, "Xbox Концепт": True, "Xbox TLA": False, "PlayStation": True, "PS Продукт": False},
    {"Гра": "SCP: Infinite Store", "Розробник": "Ігор", "Художник": "", "Нюанси": "Флагман. Подати Xbox документацію", "Дата старту": "", "Планова дата": "2026-10-30", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": True, "Картинки": True, "Тексти": True, "Дата обрана": "", "Switch": True, "Switch Продукт": True, "Switch Матеріали": True, "Switch Білд": False, "Switch Білд Дата": "", "Статус Lotcheck": "In Development", "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "", "Xbox": True, "Xbox Концепт": True, "Xbox TLA": True, "PlayStation": True, "PS Продукт": False},
    {"Гра": "Мелтопия", "Розробник": "Влад", "Художник": "Анна", "Нюанси": "Флагман 2.5GB. Чекаємо апдейту матеріалів від дева", "Дата старту": "", "Планова дата": "2026-11-10", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": False, "Картинки": False, "Тексти": False, "Дата обрана": "", "Switch": True, "Switch Продукт": False, "Switch Матеріали": False, "Switch Білд": False, "Switch Білд Дата": "", "Статус Lotcheck": "In Development", "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "", "Xbox": True, "Xbox Концепт": True, "Xbox TLA": False, "PlayStation": True, "PS Продукт": False},
    {"Гра": "Gnome from Hell", "Розробник": "Діма", "Художник": "", "Нюанси": "Рескін тільки для Switch", "Дата старту": "", "Планова дата": "2026-09-30", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": True, "Картинки": True, "Тексти": True, "Дата обрана": "", "Switch": True, "Switch Продукт": False, "Switch Матеріали": False, "Switch Білд": False, "Switch Білд Дата": "", "Статус Lotcheck": "In Development", "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "", "Xbox": False, "Xbox Концепт": False, "Xbox TLA": False, "PlayStation": False, "PS Продукт": False},
    {"Гра": "Monkey Shop", "Розробник": "Максим", "Художник": "", "Нюанси": "Заблоковано! Місяць шлють багований білд", "Дата старту": "", "Планова дата": "2026-10-05", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": False, "Картинки": False, "Тексти": False, "Дата обрана": "", "Switch": True, "Switch Продукт": False, "Switch Матеріали": False, "Switch Білд": False, "Switch Білд Дата": "", "Статус Lotcheck": "Blocked", "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "", "Xbox": False, "Xbox Концепт": False, "Xbox TLA": False, "PlayStation": False, "PS Продукт": False},
    {"Гра": "Bad Dog", "Розробник": "Максим", "Художник": "Анна", "Нюанси": "Чекаємо перевірки Антоном PC-білда + нова капсула", "Дата старту": "", "Планова дата": "2026-10-10", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": False, "Картинки": False, "Тексти": True, "Дата обрана": "", "Switch": True, "Switch Продукт": False, "Switch Матеріали": False, "Switch Білд": False, "Switch Білд Дата": "", "Статус Lotcheck": "In Development", "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "", "Xbox": False, "Xbox Концепт": False, "Xbox TLA": False, "PlayStation": False, "PS Продукт": False},
    {"Гра": "Angry Panda", "Розробник": "Максим", "Художник": "Анна Коваленко", "Нюанси": "Переробка капсули Angry Cat на панду", "Дата старту": "", "Планова дата": "2026-10-15", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": False, "Картинки": False, "Тексти": False, "Дата обрана": "", "Switch": True, "Switch Продукт": False, "Switch Матеріали": False, "Switch Білд": False, "Switch Білд Дата": "", "Статус Lotcheck": "In Development", "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "", "Xbox": False, "Xbox Концепт": False, "Xbox TLA": False, "PlayStation": False, "PS Продукт": False},
    {"Гра": "Anime Puzzle Story", "Розробник": "Максим", "Художник": "", "Нюанси": "Можливо не будемо доробляти (пріоритет рескіни)", "Дата старту": "", "Планова дата": "", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": False, "Картинки": False, "Тексти": False, "Дата обрана": "", "Switch": True, "Switch Продукт": False, "Switch Матеріали": False, "Switch Білд": False, "Switch Білд Дата": "", "Статус Lotcheck": "Blocked", "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "", "Xbox": False, "Xbox Концепт": False, "Xbox TLA": False, "PlayStation": False, "PS Продукт": False},
    {"Гра": "Dog From Hell", "Розробник": "Максим", "Художник": "Анна", "Нюанси": "Nintendo Switch сертифікацію пройдено", "Дата старту": "", "Планова дата": "", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": False, "Картинки": False, "Тексти": False, "Дата обрана": "", "Switch": True, "Switch Продукт": False, "Switch Матеріали": False, "Switch Білд": False, "Switch Білд Дата": "", "Статус Lotcheck": "Passed Lotcheck", "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "1", "Xbox": False, "Xbox Концепт": False, "Xbox TLA": False, "PlayStation": False, "PS Продукт": False},
    {"Гра": "My Mart", "Розробник": "Іван", "Художник": "", "Нюанси": "Все готово, чекаємо статус Approved по США", "Дата старту": "", "Планова дата": "2026-09-11", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": True, "Картинки": True, "Тексти": True, "Дата обрана": "2026-09-11", "Switch": True, "Switch Продукт": True, "Switch Матеріали": True, "Switch Білд": True, "Switch Білд Дата": "", "Статус Lotcheck": "Passed Lotcheck", "Прийнято Lotcheck": "2026-09-05", "Днів у Lotcheck": 0, "Спроби Lotcheck": "1", "Xbox": False, "Xbox Концепт": False, "Xbox TLA": False, "PlayStation": False, "PS Продукт": False},
    {"Гра": "Naughty Baby", "Розробник": "Сергій", "Художник": "", "Нюанси": "Реліз призначено на 11.09", "Дата старту": "", "Планова дата": "2026-09-11", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": True, "Картинки": True, "Тексти": True, "Дата обрана": "2026-09-11", "Switch": True, "Switch Продукт": True, "Switch Матеріали": True, "Switch Білд": True, "Switch Білд Дата": "", "Статус Lotcheck": "Passed Lotcheck", "Прийнято Lotcheck": "2026-09-04", "Днів у Lotcheck": 0, "Спроби Lotcheck": "1", "Xbox": False, "Xbox Концепт": False, "Xbox TLA": False, "PlayStation": False, "PS Продукт": False},
    {"Гра": "My Clothing Store Simulator", "Розробник": "Ігор", "Художник": "", "Нюанси": "Залишилось відео приєднати", "Дата старту": "", "Планова дата": "2026-09-18", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": True, "Картинки": True, "Тексти": True, "Дата обрана": "2026-09-18", "Switch": True, "Switch Продукт": True, "Switch Матеріали": True, "Switch Білд": True, "Switch Білд Дата": "", "Статус Lotcheck": "Passed Lotcheck", "Прийнято Lotcheck": "2026-09-06", "Днів у Lotcheck": 0, "Спроби Lotcheck": "1", "Xbox": False, "Xbox Концепт": False, "Xbox TLA": False, "PlayStation": False, "PS Продукт": False},
    {"Гра": "Scary Ring", "Розробник": "Сергій", "Художник": "", "Нюанси": "Все готово, чекаємо Approved", "Дата старту": "", "Планова дата": "2026-09-18", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": True, "Картинки": True, "Тексти": True, "Дата обрана": "2026-09-18", "Switch": True, "Switch Продукт": True, "Switch Матеріали": True, "Switch Білд": True, "Switch Білд Дата": "", "Статус Lotcheck": "Passed Lotcheck", "Прийнято Lotcheck": "2026-09-07", "Днів у Lotcheck": 0, "Спроби Lotcheck": "1", "Xbox": False, "Xbox Концепт": False, "Xbox TLA": False, "PlayStation": False, "PS Продукт": False},
    {"Гра": "Nom Nom Apocalypse", "Розробник": "Діма", "Художник": "", "Нюанси": "Кирило хоче взагалі цей контракт розірвати", "Дата старту": "", "Планова дата": "", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": False, "Картинки": False, "Тексти": False, "Дата обрана": "", "Switch": True, "Switch Продукт": False, "Switch Матеріали": False, "Switch Білд": False, "Switch Білд Дата": "", "Статус Lotcheck": "Blocked", "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "", "Xbox": False, "Xbox Концепт": False, "Xbox TLA": False, "PlayStation": False, "PS Продукт": False},
    {"Гра": "Lethal love", "Розробник": "Ігор", "Художник": "", "Нюанси": "Після Xbox та PS інших проектів", "Дата старту": "", "Планова дата": "", "Плановий строк": 0, "Факт до сабміту": 0, "Трейлер": False, "Картинки": False, "Тексти": False, "Дата обрана": "", "Switch": True, "Switch Продукт": False, "Switch Матеріали": False, "Switch Білд": False, "Switch Білд Дата": "", "Статус Lotcheck": "In Development", "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "", "Xbox": False, "Xbox Концепт": False, "Xbox TLA": False, "PlayStation": False, "PS Продукт": False}
]

def load_pipeline_master_data():
    if os.path.exists(PIPELINE_STORAGE_FILE):
        try:
            with open(PIPELINE_STORAGE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data: return pd.DataFrame(data)
        except Exception:
            pass
    return pd.DataFrame(SEEDED_PIPELINE_PROJECTS)

def save_pipeline_master_data(df):
    try:
        with open(PIPELINE_STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Помилка збереження пайплайну: {e}")

# ==============================================================================
# 💾 ЛОГІКА ЗБЕРЕЖЕННЯ ДАНИХ ДЛЯ RELEASE ACTIVITY
# ==============================================================================
ACTIVITY_CHECKBOX_COLS = [
    "Keymailer page", "Instagram", "YouTube", "PS Form", "PS Trailer",
    "Xbox Trailer", "Xbox Shorts", "Xbox Form", "IGN Trailer", "Press Release", "Trophy Guide", "Keys"
]

def load_saved_activities():
    if os.path.exists(ACTIVITY_STORAGE_FILE):
        try:
            with open(ACTIVITY_STORAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_activities_to_disk(data_dict):
    try:
        with open(ACTIVITY_STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Помилка збереження: {e}")

# ==============================================================================
# 🧭 САЙДБАР (БРЕНДОВАНА ШАПКА + NAV PILLS + КНОПКА ВНИЗУ)
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

    ai_query = st.text_area("Запитай базу даних:", placeholder="Напр.: Скільки симуляторів у нас вийшло?")
    
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

                    Тижнева звітність:
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
# 🎮 РОЗДІЛ 1: НАШІ ІГРИ (6 ПОВНИХ ВКЛАДОК)
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
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0", size=13), margin=dict(t=15, b=15, l=15, r=15))
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


# ==============================================================================
# 🚀 РОЗДІЛ 2: RELEASE PIPELINE (ПОВНІ 23 ПРОЕКТИ ТА КОНТРОЛЬ ЗРИВУ ТЕРМІНІВ)
# ==============================================================================
elif app_mode == "🚀 Release Pipeline":
    st.title("🚀 Console Release Pipeline & Lotcheck Tracker")
    st.caption("Повний цикл виробництва консольних портів • Всі 23 проекти • Контроль зриву дедлайнів сертифікації")

    pipeline_df = load_pipeline_master_data()

    # ФОРМА ДОДАВАННЯ НОВОГО ПРОЕКТУ
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
                        "Дата обрана": "", "Switch": new_sw, "Switch Продукт": False, "Switch Матеріали": False,
                        "Switch Білд": False, "Switch Білд Дата": "", "Статус Lotcheck": new_lotcheck_status,
                        "Прийнято Lotcheck": "", "Днів у Lotcheck": 0, "Спроби Lotcheck": "",
                        "Xbox": new_xb, "Xbox Концепт": False, "Xbox TLA": False, "PlayStation": new_ps, "PS Продукт": False
                    }
                    updated_pipe_df = pd.concat([pd.DataFrame([new_project_row]), pipeline_df], ignore_index=True)
                    save_pipeline_master_data(updated_pipe_df)
                    st.success(f"🎉 Проект '{new_title}' додано до пайплайну!")
                    st.rerun()

    pipe_tab1, pipe_tab2, pipe_tab3 = st.tabs([
        "📑 Головний трекер (Master View)", 
        "🎮 Консольні кабінети (Lotcheck & Контроль строків)", 
        "🚨 Блокери, QA та Команда"
    ])

    # 1. ГОЛОВНИЙ ТРЕКЕР
    with pipe_tab1:
        st.markdown("### 📊 Оперативний статус виробництва (Всі 23 проекти)")
        
        # Обчислення зривів строків
        pipeline_df["Плановий строк"] = pd.to_numeric(pipeline_df.get("Плановий строк", 0), errors="coerce").fillna(0).astype(int)
        pipeline_df["Факт до сабміту"] = pd.to_numeric(pipeline_df.get("Факт до сабміту", 0), errors="coerce").fillna(0).astype(int)
        
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
            dev_filter = st.multiselect("Фільтр за розробником:", options=sorted([str(x) for x in pipeline_df["Розробник"].dropna().unique() if x]), default=[])
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

        display_master_df = view_df[["Гра", "Розробник", "Художник", "Планова дата", "Плановий строк", "Факт до сабміту", "Трейлер", "Картинки", "Тексти", "Статус Lotcheck", "Switch", "Xbox", "PlayStation", "Нюанси"]].copy()
        edited_master_df = st.data_editor(
            display_master_df,
            column_config=master_cols_config,
            hide_index=True,
            use_container_width=True,
            height=480
        )

        if st.button("💾 Зберегти зміни головного пайплайну", use_container_width=True):
            for _, erow in edited_master_df.iterrows():
                match_idx = pipeline_df[pipeline_df["Гра"] == erow["Гра"]].index
                if not match_idx.empty:
                    for col_k in ["Розробник", "Художник", "Планова дата", "Плановий строк", "Факт до сабміту", "Трейлер", "Картинки", "Тексти", "Статус Lotcheck", "Switch", "Xbox", "PlayStation", "Нюанси"]:
                        pipeline_df.loc[match_idx[0], col_k] = erow[col_k]
            save_pipeline_master_data(pipeline_df)
            st.success("🎉 Усі зміни збережено у файл `pipeline_master_state.json`!")

    # 2. КОНСОЛЬНІ КАБІНЕТИ ТА ДЕТАЛЬНИЙ КОНТРОЛЬ ЛОТЧЕКУ
    with pipe_tab2:
        st.markdown("### 🎮 Детальний контроль консольних кабінетів та строків сертифікації")
        cab_choice = st.radio("Оберіть консольну платформу:", ["🔴 Nintendo Switch (Lotcheck Deep-Dive & Строки)", "🟢 Xbox (ID@Xbox воронка)", "🔵 PlayStation (Safe Publisher Setup)"], horizontal=True)

        if "Nintendo" in cab_choice:
            st.markdown("#### 🔴 Nintendo Switch: Статус сертифікації та контроль витраченого часу")
            
            # Візуальний графік відхилення Plan vs Fact
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

            sw_cols = ["Гра", "Розробник", "Плановий строк", "Факт до сабміту", "Switch Білд Дата", "Статус Lotcheck", "Прийнято Lotcheck", "Днів у Lotcheck", "Спроби Lotcheck"]
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
            st.caption("ℹ️ Рескіни тільки для Switch автоматично приховано, відображаються лише повноцінні мультиплатформи:")
            xb_cols = ["Гра", "Розробник", "Xbox", "Xbox Концепт", "Xbox TLA", "Планова дата", "Нюанси"]
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
            ps_cols = ["Гра", "Розробник", "PlayStation", "PS Продукт", "Планова дата", "Нюанси"]
            ps_df = pipeline_df[pipeline_df["PlayStation"] == True][ps_cols].copy()
            st.dataframe(ps_df, hide_index=True, use_container_width=True, height=380)

    # 3. БЛОКЕРИ, QA ТА КОМАНДА
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
# 📋 РОЗДІЛ 3: RELEASE ACTIVITY
# ==============================================================================
elif app_mode == "📋 Release Activity":
    st.title("📋 Release Marketing & Launch Activity Tracker")
    st.caption("Інтерактивний чек-лист підготовки до релізу • Галочки зберігаються автоматично на сервері")

    saved_state = load_saved_activities()

    activity_rows = []
    for _, r in raw_df.iterrows():
        g_name = str(r["Game_Name_Clean"]).strip()
        if not g_name or g_name.lower() == 'nan': continue
        
        r_date_val = r.get(rel_date_col, "—") if rel_date_col else "—"
        r_status = str(r.get(status_col, "In porting")).strip() if status_col else "In porting"

        game_saved = saved_state.get(g_name, {})

        row_dict = {
            "Гра (Title)": g_name,
            "Дата релізу": str(r_date_val),
            "Статус": "🟢 Done" if r_status.lower() == "released" else "🟡 In Progress"
        }

        checked_count = 0
        for task in ACTIVITY_CHECKBOX_COLS:
            is_checked = bool(game_saved.get(task, False))
            row_dict[task] = is_checked
            if is_checked: checked_count += 1

        row_dict["Готовність (%)"] = f"{int(round((checked_count / len(ACTIVITY_CHECKBOX_COLS)) * 100))}%"
        activity_rows.append(row_dict)

    activity_df = pd.DataFrame(activity_rows)

    act_filter = st.radio("Показати ігри:", ["Всі ігри", "Тільки в розробці (In porting)", "Тільки випущені"], horizontal=True)
    if act_filter == "Тільки в розробці (In porting)":
        display_df = activity_df[activity_df["Статус"].str.contains("Progress")].copy()
    elif act_filter == "Тільки випущені":
        display_df = activity_df[activity_df["Статус"].str.contains("Done")].copy()
    else:
        display_df = activity_df.copy()

    st.markdown("#### 🛠️ Інтерактивна матриця маркетингових задач:")

    col_config = {
        "Гра (Title)": st.column_config.TextColumn("Title", disabled=True, width="medium"),
        "Дата релізу": st.column_config.TextColumn("Release Date", disabled=True, width="small"),
        "Статус": st.column_config.TextColumn("Status", disabled=True, width="small"),
        "Готовність (%)": st.column_config.TextColumn("Progress", disabled=True, width="small")
    }
    for task in ACTIVITY_CHECKBOX_COLS:
        col_config[task] = st.column_config.CheckboxColumn(task, default=False)

    edited_act_df = st.data_editor(
        display_df,
        column_config=col_config,
        disabled=["Гра (Title)", "Дата релізу", "Статус", "Готовність (%)"],
        hide_index=True,
        use_container_width=True,
        height=520
    )

    if st.button("💾 Зберегти зміни чек-листа на сервері", use_container_width=True):
        new_state_to_save = saved_state.copy()
        for _, erow in edited_act_df.iterrows():
            g_n = erow["Гра (Title)"]
            new_state_to_save[g_n] = {task: bool(erow[task]) for task in ACTIVITY_CHECKBOX_COLS}
        
        save_activities_to_disk(new_state_to_save)
        st.success("🎉 Усі відмітки успішно збережено!")

    c_e1, c_e2 = st.columns([1, 4])
    with c_e1:
        csv_act = edited_act_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Експортувати активності (.CSV)", data=csv_act, file_name="upscale_release_activities.csv", mime="text/csv")


# ==============================================================================
# 🎯 РОЗДІЛ 4: ЦІЛІ ТА KPI 2026
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
# 📈 РОЗДІЛ 5: ТИЖНЕВА ДИНАМІКА (WoW)
# ==============================================================================
elif app_mode == "📈 Тижнева динаміка (WoW)":
    st.title("📈 Тижневий пульс видавництва (Week-over-Week)")
    st.caption("Динаміка консольних зборів, вішлістів, лідогенерації та соцмереж по тижнях")

    if weekly_df.empty:
        st.warning("⚠️ Вкажи валідне посилання на тижневу вкладку з `#gid=...` у рядку `WEEKLY_SHEET_URL`.")
        st.stop()

    last_week = weekly_df.iloc[-1]
    prev_week = weekly_df.iloc[-2] if len(weekly_df) > 1 else last_week

    last_w_ps_rev = last_week.get("PS_Revenue", 0.0)
    last_w_sw_rev = last_week.get("Nintendo_Revenue", 0.0)
    last_w_xb_rev = last_week.get("Xbox_Revenue", 0.0)
    last_w_total_rev = last_w_ps_rev + last_w_sw_rev + last_w_xb_rev

    prev_w_total_rev = prev_week.get("PS_Revenue", 0.0) + prev_week.get("Nintendo_Revenue", 0.0) + prev_week.get("Xbox_Revenue", 0.0)
    wow_delta = ((last_w_total_rev - prev_w_total_rev) / max(prev_w_total_rev, 1.0)) * 100

    wk1, wk2, wk3, wk4 = st.columns(4)
    wk1.metric(f"Виторг тижня ({last_week.get('From', '')})", f"${last_w_total_rev:,.2f}", f"{wow_delta:+.1f}% WoW")
    wk2.metric("PlayStation тиждень", f"${last_w_ps_rev:,.2f}")
    wk3.metric("Nintendo Switch тиждень", f"${last_w_sw_rev:,.2f}")
    wk4.metric("Xbox тиждень", f"${last_w_xb_rev:,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)

    w_tab1, w_tab2, w_tab3, w_tab4 = st.tabs([
        "💰 Консольний виторг & Продажі",
        "🎯 BizDev Пайплайн (Leads ➔ Deals)",
        "📱 Маркетинг & Аудиторія",
        "📑 Повна тижнева таблиця"
    ])

    with w_tab1:
        st.subheader("Динаміка виторгу по тижнях ($)")
        rev_chart_df = []
        for _, rw in weekly_df.iterrows():
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
        for _, rw in weekly_df.iterrows():
            lbl = f"{rw.get('From', '')}"
            sales_chart_df.append({"Week": lbl, "Platform": "PlayStation", "Sales": rw.get("PS_Sales", 0.0)})
            sales_chart_df.append({"Week": lbl, "Platform": "Nintendo Switch", "Sales": rw.get("Nintendo_Sales", 0.0)})
            sales_chart_df.append({"Week": lbl, "Platform": "Xbox", "Sales": rw.get("Xbox_Sales", 0.0)})
            
        fig_w_sales = px.line(pd.DataFrame(sales_chart_df), x="Week", y="Sales", color="Platform", markers=True, color_discrete_map={"Nintendo Switch": "#e60012", "PlayStation": "#3b82f6", "Xbox": "#107c10"})
        fig_w_sales.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), yaxis_title="Продано копій (шт)")
        st.plotly_chart(fig_w_sales, use_container_width=True)

    with w_tab2:
        st.subheader("🎯 BizDev Воронка: темпи залучення нових тайтлів")
        bd_cols = [c for c in ["Leads", "Contacts", "Calls", "Deals"] if c in weekly_df.columns]
        if bd_cols:
            fig_bd = px.bar(weekly_df, x="From", y=bd_cols, barmode="group", color_discrete_sequence=["#d946ef", "#3b82f6", "#f59e0b", "#10b981"])
            fig_bd.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), xaxis_title="Тиждень", yaxis_title="Кількість")
            st.plotly_chart(fig_bd, use_container_width=True)
            
            b_c1, b_c2, b_c3, b_c4 = st.columns(4)
            b_c1.metric("Всього лідів", int(weekly_df["Leads"].sum()) if "Leads" in weekly_df.columns else 0)
            b_c2.metric("Контактів", int(weekly_df["Contacts"].sum()) if "Contacts" in weekly_df.columns else 0)
            b_c3.metric("Дзвінків (Calls)", int(weekly_df["Calls"].sum()) if "Calls" in weekly_df.columns else 0)
            b_c4.metric("Угод (Deals)", int(weekly_df["Deals"].sum()) if "Deals" in weekly_df.columns else 0)

    with w_tab3:
        st.subheader("📱 Ріст аудиторії та соцмереж видавництва")
        social_cols = [c for c in ["Twitter", "TikTok", "YouTube", "Discord", "Instagram"] if c in weekly_df.columns]
        if social_cols:
            fig_social = px.line(weekly_df, x="From", y=social_cols, markers=True)
            fig_social.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), xaxis_title="Тиждень", yaxis_title="Підписників")
            st.plotly_chart(fig_social, use_container_width=True)

    with w_tab4:
        st.subheader("📑 Повний архів щотижневої звітності")
        st.dataframe(weekly_df, use_container_width=True, height=450)
        csv_w = weekly_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Експортувати тижневий звіт (.CSV)", data=csv_w, file_name="upscale_weekly_reporting.csv", mime="text/csv")


# ==============================================================================
# 🧮 РОЗДІЛ 6: КАЛЬКУЛЯТОР ПРОГНОЗІВ
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
