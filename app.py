import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import math
import json
import re
from anthropic import Anthropic

# ==============================================================================
# 🔗 НАЛАШТУВАННЯ ТАБЛИЦЬ:
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?usp=sharing"
WEEKLY_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?gid=1342107748#gid=1342107748"
GOOGLE_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzrYmeab3xtC4TW9id-N60pI6UmOk6OJj7L2OebkV48omIzqD_h827g3C1mSUpt_WusyA/exec" # (Опціонально) Webhook URL з Apps Script для автозапису
ANTHROPIC_API_KEY = ""  # Залиш порожнім (додай у share.streamlit.io -> Settings -> Secrets)
# ==============================================================================

st.set_page_config(
    page_title="Upscale Studio | Console BI & Growth Hub",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Професійні стилі темної теми + елегантні вкладки
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    
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
        border-bottom: 2px solid #818cf8 !important;
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
        display: flex; gap: 16px; background-color: #171723; border-left: 4px solid #6366f1;
        padding: 14px 18px; border-radius: 8px; margin-bottom: 12px; border: 1px solid #28283c; align-items: center;
    }
    .game-poster { width: 85px; height: 105px; object-fit: cover; border-radius: 6px; flex-shrink: 0; }
    .top-podium-card { background: #181824; border: 1px solid #2b2b3f; border-radius: 10px; padding: 12px; text-align: center; }
    .sandbox-box { background: #171724; border: 1px solid #2f2f45; border-radius: 12px; padding: 20px; margin-bottom: 15px; }
    .report-box { background: #0f172a; border: 1px solid #334155; border-radius: 12px; padding: 24px; color: #f8fafc; }
</style>
""", unsafe_allow_html=True)

# 🎯 ВІДКАЛІБРОВАНІ ЦІЛІ НА 2026 РІК
TARGETS_2026 = {
    "Year 2026 (Весь рік)": {
        "Revenue": 200000.0, "Nintendo_Revenue": 90000.0, "PS_Revenue": 70000.0, "Xbox_Revenue": 40000.0,
        "Deals": 16, "Calls": 80, "Contacts": 400, "Leads": 1200
    },
    "Q1 2026": {
        "Revenue": 35000.0, "Nintendo_Revenue": 15750.0, "PS_Revenue": 12250.0, "Xbox_Revenue": 7000.0,
        "Deals": 3, "Calls": 15, "Contacts": 75, "Leads": 225
    },
    "Q2 2026": {
        "Revenue": 45000.0, "Nintendo_Revenue": 20250.0, "PS_Revenue": 15750.0, "Xbox_Revenue": 9000.0,
        "Deals": 4, "Calls": 20, "Contacts": 100, "Leads": 300
    },
    "Q3 2026": {
        "Revenue": 50000.0, "Nintendo_Revenue": 22500.0, "PS_Revenue": 17500.0, "Xbox_Revenue": 10000.0,
        "Deals": 4, "Calls": 20, "Contacts": 100, "Leads": 300
    },
    "Q4 2026": {
        "Revenue": 70000.0, "Nintendo_Revenue": 31500.0, "PS_Revenue": 24500.0, "Xbox_Revenue": 14000.0,
        "Deals": 5, "Calls": 25, "Contacts": 125, "Leads": 375
    }
}

# Графік розпродажів Nintendo eShop
NINTENDO_SCHEDULE = [
    {"name": "1. Autumn Sale", "start": "2026-09-11", "end": "2026-09-24", "status": "🔥 Найближчий", "region": "Global / EU / US"},
    {"name": "2. Halloween Sale", "start": "2026-10-26", "end": "2026-11-15", "status": "🎃 Сезонний", "region": "Global"},
    {"name": "3. Holiday Sale (EU)", "start": "2026-12-17", "end": "2027-01-10", "status": "🎄 Головний (EU)", "region": "Europe / Australia"},
    {"name": "4. Holiday Sale (US)", "start": "2026-12-21", "end": "2027-01-11", "status": "🎄 Головний (US)", "region": "Americas"}
]

# 30 ВІДКАЛІБРОВАНИХ ПІДЖАНРІВ
GENRE_DATABASE = {
    # 1. Симулятори та Менеджмент (8)
    "Simulator: Animal Chaos / Cat Meme (3D)": {"PS": 3.8, "Xbox": 1.8, "Switch": 2.6, "Decay": 1.35, "Desc": "Cat From Hell, Bad Cat, Angry Cat"},
    "Simulator: Crime / Black Market (3D)": {"PS": 4.2, "Xbox": 3.5, "Switch": 1.2, "Decay": 1.15, "Desc": "Drug Dealer Empire, Thief Sim"},
    "Simulator: Cozy Cafe / Animal Job Sim": {"PS": 2.2, "Xbox": 1.5, "Switch": 2.8, "Decay": 1.30, "Desc": "Funny Animal Cafe, Tricky Monkey Zoo"},
    "Simulator: Shop / Supermarket / Store (3D)": {"PS": 1.8, "Xbox": 1.4, "Switch": 2.5, "Decay": 1.30, "Desc": "My Supermarket Simulator"},
    "Simulator: Job / Service / Business (3D)": {"PS": 2.0, "Xbox": 1.8, "Switch": 2.2, "Decay": 1.25, "Desc": "Waterpark Manager, Street Food Simulator"},
    "Simulator: Truck / Heavy Logistics (3D/2D)": {"PS": 1.5, "Xbox": 2.4, "Switch": 1.8, "Decay": 1.25, "Desc": "Heavy Duty, Trucker Ben"},
    "Simulator: Farming / Homestead / Ranch": {"PS": 0.9, "Xbox": 1.1, "Switch": 3.2, "Decay": 1.40, "Desc": "Монополія аудиторії Nintendo"},
    "Simulator: Casual Flight / Paper Plane": {"PS": 0.4, "Xbox": 0.3, "Switch": 0.4, "Decay": 1.10, "Desc": "🔴 Paperly, Fly for Fly (Зона низького чека)"},

    # 2. Хоррори та Виживання (5)
    "Horror: 3D PSX / Retro / VHS Style": {"PS": 1.8, "Xbox": 2.8, "Switch": 0.5, "Decay": 1.15, "Desc": "Skinwalker, TROX (Xbox домінує)"},
    "Horror: 3D First-Person Atmospheric": {"PS": 1.6, "Xbox": 2.2, "Switch": 0.5, "Decay": 1.10, "Desc": "Cornfield, Death Attraction, Dr. Psycho"},
    "Horror: 3D Anomaly / Walking Sim / Backrooms": {"PS": 2.4, "Xbox": 1.4, "Switch": 1.0, "Decay": 1.15, "Desc": "Exit 8, Don't Scream (PS попит)"},
    "Survival: Bunker / Hardcore Crafting (3D/2D)": {"PS": 2.0, "Xbox": 2.6, "Switch": 1.8, "Decay": 1.35, "Desc": "From the Bunker, Survival After War"},
    "Survival: Open-World / Island Crafting (3D)": {"PS": 1.6, "Xbox": 2.0, "Switch": 1.5, "Decay": 1.30, "Desc": "Call of Island, WinterCraft"},

    # 3. Платформери та Фізика (4)
    "Platformer: 3D Physics / Character Adventure": {"PS": 2.0, "Xbox": 1.5, "Switch": 2.4, "Decay": 1.25, "Desc": "Super Adventure Hand"},
    "Platformer: 3D Obby / Roblox-style": {"PS": 1.8, "Xbox": 1.4, "Switch": 2.4, "Decay": 1.20, "Desc": "Obby Parkour, Blade Ball"},
    "Physics: 3D Ragdoll / Sandbox Chaos": {"PS": 3.0, "Xbox": 1.2, "Switch": 1.8, "Decay": 1.15, "Desc": "Mr. Dude, Action Playground, Car Crash"},
    "Physics: Rage / Climbing / 'Only Up'": {"PS": 1.8, "Xbox": 1.2, "Switch": 1.6, "Decay": 1.15, "Desc": "Super Rock Climber (Only Up вайб)"},

    # 4. Пазли та Козі (4)
    "Cozy: Organization / Packing / Decor": {"PS": 0.8, "Xbox": 0.5, "Switch": 3.5, "Decay": 1.45, "Desc": "Packit List, Unpacking-вайб"},
    "Puzzle: 2D Match-3D / Goods Sort / Nuts": {"PS": 0.6, "Xbox": 0.5, "Switch": 2.4, "Decay": 1.25, "Desc": "Goods Sort, Bus Jam, Bolts & Nuts"},
    "Puzzle: Suika / Drop & Merge / Watermelon": {"PS": 0.5, "Xbox": 0.4, "Switch": 2.8, "Decay": 1.20, "Desc": "Suika Balls, Fruit Merge"},
    "Puzzle: Hidden Object / Detective Quest": {"PS": 1.6, "Xbox": 0.9, "Switch": 1.8, "Decay": 1.40, "Desc": "Conquistadorio, Minima, Dollmaker"},

    # 5. Екшн, Шутери та Перегони (4)
    "Racing: 3D Arcade / Traffic Driving": {"PS": 3.0, "Xbox": 1.0, "Switch": 1.8, "Decay": 1.15, "Desc": "Gran Carismo, Hyper Cars"},
    "Action: 3D Top-Down / Extraction Shooter": {"PS": 1.8, "Xbox": 2.2, "Switch": 1.0, "Decay": 1.25, "Desc": "Bunker 22, Zombiescraper"},
    "Action: 2D Hack'n'Slash / Beat'em Up": {"PS": 1.2, "Xbox": 1.0, "Switch": 1.4, "Decay": 1.20, "Desc": "Bob the Warrior, Street Combat"},
    "Fighting: 2D/3D Local Party / Brawler": {"PS": 0.6, "Xbox": 0.5, "Switch": 0.8, "Decay": 1.15, "Desc": "Street Combat Fighting"},

    # 6. RPG, Роглайки та Стратегії (5)
    "Roguelike: Auto-Shooter / 'Survivor-like'": {"PS": 1.4, "Xbox": 1.4, "Switch": 1.8, "Decay": 1.35, "Desc": "Nom Nom Apocalypse"},
    "Roguelike: Turn-Based / Deckbuilder / Dice": {"PS": 1.0, "Xbox": 1.2, "Switch": 1.6, "Decay": 1.40, "Desc": "Rabbit Samurai, Bag Hero, Slice & Dice"},
    "Metroidvania: 2D Pixel / Action Platformer": {"PS": 1.0, "Xbox": 0.8, "Switch": 0.4, "Decay": 1.15, "Desc": "⚠️ ABSURDIKA: Rebuild"},
    "Strategy: Tower Defense / Castle Defense": {"PS": 1.8, "Xbox": 1.2, "Switch": 1.4, "Decay": 1.30, "Desc": "Epic Empire, Wizard's Fortress"},
    "Visual Novel / Narrative Choice": {"PS": 1.0, "Xbox": 0.3, "Switch": 2.5, "Decay": 1.40, "Desc": "Choice of Life: Wild Islands"}
}

PRICE_MODIFIERS = {4.99: 1.25, 5.99: 1.15, 6.99: 1.10, 9.99: 1.00, 14.99: 0.75, 19.99: 0.55}

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

    for col in df.columns:
        col_lower = str(col).lower()
        if any(img_k in col_lower for img_k in ["cover", "image", "постер", "url", "фото", "link", "посилання", "date", "дата", "name", "назва", "genre", "жанр", "status", "platform"]):
            continue
        df[col] = df[col].apply(clean_num_val)

    name_col = next((c for c in df.columns if any(k in c.lower() for k in ["game", "title", "назва"])), df.columns[0])
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

# Підготовка квартальної структури даних
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

cover_col = next((c for c in raw_df.columns if any(k in c.lower() for k in ["cover", "image", "постер", "обкладинка"])), None)
discount_col = next((c for c in raw_df.columns if any(k in c.lower() for k in ["discount", "знижк"])), None)
DEFAULT_IMAGE = "https://img.icons8.com/isometric/100/controller.png"

if "scouted_leads" not in st.session_state:
    st.session_state.scouted_leads = []

# ==============================================================================
# 🧭 САЙДБАР ТА НАВІГАЦІЯ
# ==============================================================================
with st.sidebar:
    st.header("🎮 Upscale Studio BI")
    
    app_mode = st.radio(
        "📍 Оберіть розділ хабу:",
        [
            "🎮 Наші ігри", 
            "🎯 Цілі та KPI 2026", 
            "📈 Тижнева динаміка (WoW)", 
            "🧮 Калькулятор прогнозів"
        ],
        index=0
    )
    
    st.markdown("---")
    if st.button("🔄 Оновити дані з Google Sheets", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.subheader("🔍 Фільтри")
    search = st.text_input("Пошук гри:", "")
    genre_col = next((c for c in raw_df.columns if "genre" in c.lower() or "жанр" in c.lower()), None)
    
    filtered_df = raw_df.copy()
    if genre_col:
        available_genres = sorted([str(g).strip() for g in raw_df[genre_col].dropna().unique() if str(g).strip().lower() != 'nan'])
        if available_genres:
            genres = st.multiselect("Жанри:", options=available_genres, default=available_genres)
            if genres:
                filtered_df = filtered_df[filtered_df[genre_col].astype(str).str.strip().isin(genres)]

    if search:
        filtered_df = filtered_df[filtered_df["Game_Name_Clean"].astype(str).str.contains(search, case=False, na=False)]

    # AI ЧАТ CLAUDE HAIKU
    st.markdown("---")
    st.subheader("🤖 AI-Аналітик (Claude Haiku)")
    claude_key = ANTHROPIC_API_KEY or st.secrets.get("ANTHROPIC_API_KEY", "")
    
    if not claude_key:
        claude_key = st.text_input("Введи Anthropic API Key:", type="password", placeholder="sk-ant-...")

    ai_query = st.text_area(
        "Запитай будь-що по всій базі:",
        placeholder="Напр.: Які симулятори найкраще продаються на Switch? Або: Як ми йдемо по таргету 2026 року?"
    )
    
    if st.button("⚡ Проаналізувати через Claude", use_container_width=True):
        clean_key = str(claude_key).strip()
        if not clean_key or not clean_key.startswith("sk-ant"):
            st.error("❌ Введи валідний ключ Anthropic (починається на 'sk-ant-...')!")
        elif not ai_query.strip():
            st.warning("Введи запитання.")
        else:
            with st.spinner("Claude аналізує базу даних..."):
                try:
                    client = Anthropic(api_key=clean_key)
                    summary_lines = ["Game|Genre|Price|PS_M1|PS_All|Switch_M1|Switch_All|Xbox_M1|Xbox_All|Total_All"]
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
                        g_price = r.get("Price consoles, $", r.get("Price consoles", 0.0))
                        try: g_price = round(float(g_price), 2)
                        except: g_price = 0.0

                        ps_m1 = find_num(r, ["playstation", "1st"]) or find_num(r, ["ps", "1st"])
                        ps_all = find_num(r, ["playstation", "all"]) or find_num(r, ["ps", "all"])
                        sw_m1 = find_num(r, ["switch", "1st"])
                        sw_all = find_num(r, ["switch", "all"])
                        xb_m1 = find_num(r, ["xbox", "1st"])
                        xb_all = find_num(r, ["xbox", "all"])
                        tot_all = find_num(r, ["total"]) or (ps_all + sw_all + xb_all)
                        summary_lines.append(f"{g_name}|{g_genre}|${g_price}|{ps_m1}|{ps_all}|{sw_m1}|{sw_all}|{xb_m1}|{xb_all}|{tot_all}")

                    compact_dataset = "\n".join(summary_lines)
                    weekly_csv_snippet = weekly_df.to_csv(index=False) if not weekly_df.empty else "No weekly data"

                    prompt = f"""
                    Ти — головний фінансовий директор та аналітик консольного видавництва Upscale Studio (Україна).
                    Ціль на 2026 рік: $200,000 консольної виручки.
                    Дані портфоліо ({len(summary_lines)-1} ігор):
                    {compact_dataset}

                    Тижнева звітність (Weekly Ops):
                    {weekly_csv_snippet}

                    Запитання: "{ai_query}"

                    Дай точну, професійну та реалістичну відповідь українською мовою з реальними цифрами.
                    ВАЖЛИВО: Пиши суми як "USD 1,500" або "\\$1,500" (без одинарного знака $).
                    """

                    try:
                        message = client.messages.create(
                            model="claude-haiku-4-5",
                            max_tokens=900,
                            messages=[{"role": "user", "content": prompt}]
                        )
                        raw_text = message.content[0].text
                    except:
                        message = client.messages.create(
                            model="claude-3-5-haiku-20241022",
                            max_tokens=900,
                            messages=[{"role": "user", "content": prompt}]
                        )
                        raw_text = message.content[0].text

                    clean_output = re.sub(r'(?<!\\)\$', r'\\$', raw_text)
                    st.markdown("### 💡 Результат аналізу:")
                    st.markdown(clean_output)
                except Exception as e:
                    st.error(f"❌ Помилка Anthropic API: {e}")

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
# 🎮 РОЗДІЛ 1: НАШІ ІГРИ (5 ВКЛАДОК)
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

    tab_analytics, tab_insights, tab_sales_tracker, tab_forecast_review, tab_table_report = st.tabs([
        "📈 Аналітика та Динаміка", 
        "🧠 Інсайти та Постери", 
        "📅 Розпродажі Nintendo",
        "🎯 План vs Факт (Точність)",
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
            fig_bar = px.bar(top_df, x=actual_total_col, y="Game_Name_Clean", orientation="h", text=actual_total_col, color_discrete_sequence=["#6366f1"])
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
        st.subheader("📅 Календар розпродажів та Конструктор знижок Nintendo")
        st.caption("Автоматичне зчитування цільових знижок із Google Таблиці та генерація 1-клік Bookmarklet")

        cal_df = pd.DataFrame([
            {"Сейл": s["name"], "Початок": s["start"], "Кінець": s["end"], "Статус": s["status"], "Регіон": s["region"]}
            for s in NINTENDO_SCHEDULE
        ])
        
        fig_timeline = px.timeline(
            cal_df, x_start="Початок", x_end="Кінець", y="Сейл", color="Статус",
            color_discrete_map={"🔥 Найближчий": "#f59e0b", "🎃 Сезонний": "#ec4899", "🎄 Головний (EU)": "#10b981", "🎄 Головний (US)": "#3b82f6"}
        )
        fig_timeline.update_yaxes(autorange="reversed")
        fig_timeline.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#e2e8f0"), height=260, margin=dict(t=10, b=10, l=10, r=10),
            xaxis=dict(gridcolor="#28283c", title="Дати проведення розпродажів")
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

        st.markdown("---")
        sale_choice = st.selectbox(
            "Оберіть плановий розпродаж Nintendo:",
            [f"{s['name']} (Старт: {s['start']} | {s['status']} | {s['region']})" for s in NINTENDO_SCHEDULE],
            index=0
        )
        selected_sale_data = NINTENDO_SCHEDULE[0]
        for s in NINTENDO_SCHEDULE:
            if s["name"] in sale_choice:
                selected_sale_data = s
                break

        target_start_date = datetime.strptime(selected_sale_data["start"], "%Y-%m-%d")
        rel_col = next((c for c in filtered_df.columns if any(k in c.lower() for k in ["release", "date", "дата"])), None)

        tracker_rows = []
        for _, r in filtered_df.iterrows():
            g_name = r["Game_Name_Clean"]
            raw_date_val = r.get(rel_col, None) if rel_col else None
            r_date = parse_flexible_date(raw_date_val)
            
            if not r_date:
                r_date = datetime(2026, 5, 1)
                date_display = "— (Не вказано)"
            else:
                date_display = r_date.strftime("%Y-%m-%d")

            days_since_rel = (target_start_date - r_date).days
            if days_since_rel >= 30:
                sale_status = "🟢 Готова до сейлу"
                note = f"Пройшло {days_since_rel} дн. (Кулдаун OK)"
                is_ready = True
            else:
                sale_status = "🟡 Кулдаун"
                note = f"Залишилось {30 - days_since_rel} дн."
                is_ready = False

            sheet_discount_val = r.get(discount_col, 70.0) if discount_col else 70.0
            try:
                final_discount_num = int(round(float(sheet_discount_val))) if float(sheet_discount_val) > 0 else 70
            except:
                final_discount_num = 70

            tracker_rows.append({
                "Включити": is_ready,
                "Гра": g_name,
                "Знижка % (з Таблиці)": final_discount_num,
                "Реальна дата релізу": date_display,
                "Статус Nintendo": sale_status,
                "Деталі кулдауну": note
            })

        tracker_df = pd.DataFrame(tracker_rows)
        ready_count = len(tracker_df[tracker_df["Статус Nintendo"].str.contains("Готова")])
        
        t_c1, t_c2, t_c3 = st.columns(3)
        t_c1.metric("Цільовий сейл", selected_sale_data["name"], f"Старт: {selected_sale_data['start']}")
        t_c2.metric("Готових ігор до участі", f"{ready_count} з {len(tracker_df)}")
        t_c3.metric("У кулдауні (нові релізи)", len(tracker_df) - ready_count)

        st.markdown("---")
        st.markdown("#### 🛠️ Інтерактивний Конструктор кампанії знижок")
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
            height=380
        )

        st.markdown("---")
        if st.button("⚡ Згенерувати оновлений Bookmarklet для Nintendo", use_container_width=True):
            selected_games = edited_tracker_df[edited_tracker_df["Включити"] == True]
            if selected_games.empty:
                st.warning("Оберіть хоча б одну гру галочкою!")
            else:
                discounts_payload = {}
                names_list = []
                for _, s_row in selected_games.iterrows():
                    g_n = s_row["Гра"].strip().lower()
                    discounts_payload[g_n] = int(s_row["Знижка % (з Таблиці)"])
                    names_list.append(s_row["Гра"].strip())

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

                st.success(f"🎉 Bookmarklet згенеровано для {len(selected_games)} ігор на основі твоїх знижок із Google Таблиці!")
                b_c1, b_c2 = st.columns(2)
                with b_c1:
                    st.markdown("##### 📌 Код закладки (встав у URL закладки Chrome):")
                    st.code(bookmarklet_code, language="javascript")
                with b_c2:
                    st.markdown("##### 📋 Список назв (для швидкого пошуку на порталі Nintendo):")
                    st.text_area("Назви ігор:", "\n".join(names_list), height=180)

    with tab_forecast_review:
        st.subheader("🎯 Порівняння прогнозованих та фактичних результатів")
        st.caption("Аудит точності на основі відкаліброваних 30 піджанрів та джерел")

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

        def get_exact_fact_all(row_s, plat):
            if plat == "PS":
                for c in row_s.index:
                    cl = c.lower()
                    if "playstation" in cl and "all" in cl and "pred" not in cl and "forecast" not in cl:
                        try: return float(row_s[c])
                        except: pass
            elif plat == "Switch":
                for c in row_s.index:
                    cl = c.lower()
                    if "switch" in cl and "all" in cl and not cl.endswith(".1") and "pred" not in cl and "forecast" not in cl:
                        try: return float(row_s[c])
                        except: pass
            elif plat == "Xbox":
                for c in row_s.index:
                    cl = c.lower()
                    if "xbox" in cl and "all" in cl and not cl.endswith(".1") and "pred" not in cl and "forecast" not in cl:
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
            g_price = r.get("Price consoles, $", r.get("Price consoles", 9.99))
            try: g_price = float(g_price)
            except: g_price = 9.99

            ps_m1_fact = get_exact_fact_m1(r, "PS")
            ps_all_fact = get_exact_fact_all(r, "PS")
            sw_m1_fact = get_exact_fact_m1(r, "Switch")
            sw_all_fact = get_exact_fact_all(r, "Switch")
            xb_m1_fact = get_exact_fact_m1(r, "Xbox")
            xb_all_fact = get_exact_fact_all(r, "Xbox")

            active_platforms = []
            if ps_m1_fact > 0 or ps_all_fact > 0: active_platforms.append("PS")
            if sw_m1_fact > 0 or sw_all_fact > 0: active_platforms.append("Switch")
            if xb_m1_fact > 0 or xb_all_fact > 0: active_platforms.append("Xbox")

            if not active_platforms:
                src_plat_text = str(r.get("Platform Source", r.get("Platform", ""))).lower()
                if "switch" in src_plat_text: active_platforms.append("Switch")
                if "ps" in src_plat_text or "playstation" in src_plat_text: active_platforms.append("PS")
                if "xbox" in src_plat_text: active_platforms.append("Xbox")
            
            if not active_platforms:
                active_platforms = ["Switch"]

            platform_badge = " + ".join(active_platforms) if len(active_platforms) < 3 else "Усі 3 консолі"

            base_m = find_val(r, ["base metric"])
            installs_val = find_val(r, ["installs"]) or find_val(r, ["reviews"])
            steam_rev_val = find_val(r, ["steam revenue"])
            src_platform_type = str(r.get("Platform Source", r.get("Platform", ""))).lower()

            if base_m == 0:
                if "steam" in src_platform_type or steam_rev_val > 0:
                    base_m = (steam_rev_val * 0.10) + 500.0
                elif "play" in src_platform_type or ("google" in src_platform_type) or (installs_val >= 10000):
                    base_m = (math.sqrt(installs_val) * 2.0) + 800.0 if installs_val > 0 else 0.0
                elif "crazy" in src_platform_type or ("web" in src_platform_type and installs_val > 0):
                    base_m = (installs_val * 0.05) + 900.0
                elif "itch" in src_platform_type and installs_val > 0:
                    base_m = (installs_val * 10.0) + 400.0

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
                ps_pred, sw_pred, xb_pred, total_pred_m1 = 0.0, 0.0, 0.0, 0.0
                has_valid_forecast = False

            total_m1_fact = (ps_m1_fact if "PS" in active_platforms else 0.0) + \
                            (sw_m1_fact if "Switch" in active_platforms else 0.0) + \
                            (xb_m1_fact if "Xbox" in active_platforms else 0.0)

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
            st.subheader("📊 Графік: Фактичні збори M1 проти Прогнозу ($)")
            chart_plan_df = valid_comp.head(15)
            fig_plan_fact = go.Figure()
            fig_plan_fact.add_trace(go.Bar(x=chart_plan_df["Гра"], y=chart_plan_df["Факт M1 ($)"], name="ФАКТ M1 ($)", marker_color="#10b981"))
            fig_plan_fact.add_trace(go.Bar(x=chart_plan_df["Гра"], y=chart_plan_df["Прогноз M1 ($)"], name="ПРОГНОЗ M1 ($)", marker_color="#6366f1"))
            fig_plan_fact.update_layout(
                barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#e2e8f0"), height=380, margin=dict(t=20, b=20, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_plan_fact, use_container_width=True)

        st.markdown("---")
        st.subheader("📑 Детальна таблиця аудиту (План vs Факт)")
        st.dataframe(comp_df, use_container_width=True, height=480)

    with tab_table_report:
        st.subheader("📑 Повна фінансова таблиця портфоліо")
        column_config = {}
        if cover_col:
            column_config[cover_col] = st.column_config.ImageColumn("Обкладинка", width="small")
        st.dataframe(filtered_df, column_config=column_config, use_container_width=True, height=420)
        
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Експортувати дані (.CSV)", data=csv_data, file_name="console_sales_portfolio.csv", mime="text/csv")


# ==============================================================================
# 🎯 РОЗДІЛ 2: ЦІЛІ ТА KPI 2026 (НОВИЙ БЛОК)
# ==============================================================================
elif app_mode == "🎯 Цілі та KPI 2026":
    st.title("🎯 Виконання річного та квартальних планів (2026)")
    st.caption("Ціль на 2026 рік: **$200,000 консольної виручки** • Дані синхронізуються з Weekly Updates")

    if weekly_df.empty:
        st.warning("⚠️ Вкажи валідне посилання на тижневу вкладку з `#gid=...` у рядку `WEEKLY_SHEET_URL`.")
        st.stop()

    q_df = prepare_quarterly_data(weekly_df)

    if q_df.empty:
        st.info("💡 У щотижневій таблиці немає валідних дат для розрахунку 2026 року.")
        st.stop()

    # Селектор періоду
    col_sel, col_info = st.columns([1.5, 2.5])
    with col_sel:
        period_choice = st.radio(
            "📌 Оберіть період для аналізу:",
            ["Year 2026 (Весь рік)", "Q1 2026", "Q2 2026", "Q3 2026", "Q4 2026"],
            horizontal=True
        )

    # Фільтрація факту під обраний період
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

    # Великий прогрес-бар
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
    sw_pct = (fact_sw / max(target["Nintendo_Revenue"], 1.0)) * 100
    ps_pct = (fact_ps / max(target["PS_Revenue"], 1.0)) * 100
    xb_pct = (fact_xb / max(target["Xbox_Revenue"], 1.0)) * 100

    k1.metric("🔴 Nintendo Switch", f"${fact_sw:,.0f}", f"{sw_pct:.1f}% від цілі ${target['Nintendo_Revenue']:,.0f}")
    k2.metric("🔵 PlayStation", f"${fact_ps:,.0f}", f"{ps_pct:.1f}% від цілі ${target['PS_Revenue']:,.0f}")
    k3.metric("🟢 Xbox", f"${fact_xb:,.0f}", f"{xb_pct:.1f}% від цілі ${target['Xbox_Revenue']:,.0f}")

    st.markdown("---")
    st.subheader("🎯 BizDev Воронка: План vs Факт підписання")
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("🤝 Deals (Угоди)", f"{fact_deals} / {target['Deals']}", f"{(fact_deals/max(target['Deals'],1))*100:.0f}% виконання")
    b2.metric("📞 Calls (Дзвінки)", f"{fact_calls} / {target['Calls']}", f"{(fact_calls/max(target['Calls'],1))*100:.0f}% виконання")
    b3.metric("✉️ Contacts (Контакти)", f"{fact_contacts} / {target['Contacts']}", f"{(fact_contacts/max(target['Contacts'],1))*100:.0f}% виконання")
    b4.metric("🔍 Leads (Знайдено лідів)", f"{fact_leads} / {target['Leads']}", f"{(fact_leads/max(target['Leads'],1))*100:.0f}% виконання")

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
        fig_plan.add_trace(go.Bar(x=chart_plan_df["Платформа"], y=chart_plan_df["План ($)"], name="ПЛАН", marker_color="#6366f1"))
        fig_plan.update_layout(
            barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#e2e8f0"), height=360, margin=dict(t=15, b=15, l=15, r=15)
        )
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
# 📈 РОЗДІЛ 3: ТИЖНЕВА ДИНАМІКА (WEEKLY OPS & GROWTH TRACKER)
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

    prev_w_ps_rev = prev_week.get("PS_Revenue", 0.0)
    prev_w_sw_rev = prev_week.get("Nintendo_Revenue", 0.0)
    prev_w_xb_rev = prev_week.get("Xbox_Revenue", 0.0)
    prev_w_total_rev = prev_w_ps_rev + prev_w_sw_rev + prev_w_xb_rev

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
            
        fig_w_rev = px.bar(
            pd.DataFrame(rev_chart_df), x="Week", y="Revenue", color="Platform", barmode="group",
            color_discrete_map={"Nintendo Switch": "#e60012", "PlayStation": "#3b82f6", "Xbox": "#107c10"}
        )
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
            
        fig_w_sales = px.line(
            pd.DataFrame(sales_chart_df), x="Week", y="Sales", color="Platform", markers=True,
            color_discrete_map={"Nintendo Switch": "#e60012", "PlayStation": "#3b82f6", "Xbox": "#107c10"}
        )
        fig_w_sales.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), yaxis_title="Продано копій (шт)")
        st.plotly_chart(fig_w_sales, use_container_width=True)

    with w_tab2:
        st.subheader("🎯 BizDev Воронка: темпи залучення нових тайтлів")
        bd_cols = [c for c in ["Leads", "Contacts", "Calls", "Deals"] if c in weekly_df.columns]
        if bd_cols:
            fig_bd = px.bar(weekly_df, x="From", y=bd_cols, barmode="group", color_discrete_sequence=["#6366f1", "#3b82f6", "#f59e0b", "#10b981"])
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
# 🧮 РОЗДІЛ 4: КАЛЬКУЛЯТОР ПРОГНОЗІВ
# ==============================================================================
elif app_mode == "🧮 Калькулятор прогнозів":
    st.title("🧮 Sourcing & Lead Forecasting Hub")
    st.caption("Оцінка нових лідів за 30 піджанрами та формування пайплайну")

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
            calc_price = st.selectbox("Планова ціна на консолях ($):", list(PRICE_MODIFIERS.keys()), index=3)
            st.markdown('</div>', unsafe_allow_html=True)

        g_cfg = GENRE_DATABASE[calc_genre]
        p_mod = PRICE_MODIFIERS[calc_price]

        ps_est = b_metric * g_cfg["PS"] * p_mod
        ns_est = b_metric * g_cfg["Switch"] * p_mod
        xb_est = b_metric * g_cfg["Xbox"] * p_mod
        tot_m1 = ps_est + ns_est + xb_est
        tot_year = tot_m1 * g_cfg["Decay"]

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
            t_c1.metric("🔥 Всього за M1", f"${tot_m1:,.0f}")
            t_c2.metric("📅 Річний виторг (1Y)", f"${tot_year:,.0f}", f"{g_cfg['Decay']}x")

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
                        st.warning(f"Збережено локально. Помилка запису в Webhook: {e}")
                else:
                    st.toast(f"✅ Лід '{calc_name}' додано до таблиці!")

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
            k_l2.metric("Потенціал M1 пайплайну", f"${tot_pipeline_val:,.2f}")
            k_l3.metric("Середній очікуваний M1", f"${avg_lead_val:,.2f}")

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
