import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# ==============================================================================
# 🔗 ТВОЄ ПОСИЛАННЯ НА GOOGLE ТАБЛИЦЮ:
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?usp=sharing"
# ==============================================================================

st.set_page_config(
    page_title="Upscale Studio | Publishing BI & Scouting Hub",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Стилі високої контрастності
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
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
    .game-poster { width: 80px; height: 100px; object-fit: cover; border-radius: 6px; }
    .sandbox-box { background: #171724; border: 1px solid #2f2f45; border-radius: 12px; padding: 20px; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# 16 каліброваних профілів
GENRE_DATABASE = {
    "Animal Chaos / Cat Simulator": {"PS": 4.2, "Switch": 3.2, "Xbox": 1.6, "Decay": 1.35, "Desc": "Топ-сегмент портфоліо (Cat From Hell, Bad Cat, Angry Cat)"},
    "Job / Business Simulator (3D)": {"PS": 2.2, "Switch": 2.6, "Xbox": 1.5, "Decay": 1.30, "Desc": "Switch/PS лідери (Supermarket, Waterpark, Drug Dealer)"},
    "Meme / Viral / Crime Sim (3D)": {"PS": 3.8, "Switch": 1.4, "Xbox": 1.6, "Decay": 1.15, "Desc": "PlayStation трофі-вірусність (Drug Dealer, Mad Taxi)"},
    "3D PSX / VHS / Retro Horror": {"PS": 2.0, "Switch": 0.5, "Xbox": 2.8, "Decay": 1.15, "Desc": "Xbox домінує (Skinwalker $9.4k), Switch слабкий"},
    "3D First-Person Atmospheric Horror": {"PS": 2.2, "Switch": 0.6, "Xbox": 2.2, "Decay": 1.10, "Desc": "Рівний високий попит на PS та Xbox (Cornfield, Death Attraction)"},
    "Bunker / Hardcore Survival (3D/2D)": {"PS": 1.8, "Switch": 1.2, "Xbox": 2.4, "Decay": 1.35, "Desc": "Xbox та PS база (From the Bunker $3.8k)"},
    "Cozy Games & Life Simulators": {"PS": 0.8, "Switch": 3.0, "Xbox": 0.6, "Decay": 1.45, "Desc": "Switch-монополія, стабільний довгий хвіст"},
    "Hidden Object / Point & Click Quest": {"PS": 1.3, "Switch": 1.9, "Xbox": 0.8, "Decay": 1.40, "Desc": "Стабільна окупність (Conquistadorio, Minima)"},
    "Card Game / Deckbuilder / Narrative": {"PS": 1.0, "Switch": 1.4, "Xbox": 1.1, "Decay": 1.40, "Desc": "Стійкі сейл-збори (Choice of Life: Wild Islands)"},
    "Arcade Racing / Physics Crash (3D)": {"PS": 1.8, "Switch": 1.6, "Xbox": 0.9, "Decay": 1.15, "Desc": "Імпульсивні покупки на PS та Switch (Gran Carismo)"},
    "Roguelike (Action / Survivor-like)": {"PS": 1.4, "Switch": 1.5, "Xbox": 1.3, "Decay": 1.35, "Desc": "Збалансований мультиплатформенний попит (Nom Nom)"},
    "Tower Defense / Tactical Strategy": {"PS": 1.1, "Switch": 1.6, "Xbox": 1.2, "Decay": 1.30, "Desc": "Стабільний попит на Switch/Xbox (Epic Empire)"},
    "2D Casual / Mobile-style Puzzle": {"PS": 0.6, "Switch": 2.0, "Xbox": 0.5, "Decay": 1.20, "Desc": "Працює тільки на Switch за ціни $4.99 (Find Sort Match)"},
    "Metroidvania / 2D Pixel Action": {"PS": 1.1, "Switch": 0.4, "Xbox": 0.9, "Decay": 1.15, "Desc": "⚠️ Перенасичений ринок на Switch (Absurdika $84)"},
    "Idle / Clicker Games": {"PS": 0.8, "Switch": 1.0, "Xbox": 0.7, "Decay": 1.30, "Desc": "Помірний результат (Loaders Inc, Funny Animal Cafe)"},
    "Casual Vehicle / Flight Simulator": {"PS": 0.4, "Switch": 0.4, "Xbox": 0.5, "Decay": 1.10, "Desc": "🔴 Зона високого ризику (Paperly $1.3k замість $16k)"}
}

PRICE_MODIFIERS = {4.99: 1.25, 5.99: 1.15, 6.99: 1.10, 9.99: 1.00, 14.99: 0.75, 19.99: 0.55}

def get_export_url(url_or_id):
    if not url_or_id: return ""
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url_or_id)
    sheet_id = match.group(1) if match else url_or_id.strip()
    gid_match = re.search(r"[#&]gid=([0-9]+)", url_or_id)
    gid = gid_match.group(1) if gid_match else "0"
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

@st.cache_data(ttl=300, show_spinner=False)
def load_data(sheet_url):
    if not sheet_url or "ВСТАВ_СЮДИ" in sheet_url:
        return pd.DataFrame()
    csv_url = get_export_url(sheet_url)
    try:
        df = pd.read_csv(csv_url)
    except Exception:
        return pd.DataFrame()

    for col in df.columns:
        col_lower = str(col).lower()
        if any(img_k in col_lower for img_k in ["cover", "image", "постер", "url", "фото", "link"]):
            continue
        if any(k in col_lower for k in ["revenue", "price", "total", "$", "month", "year", "time", "всього", "ціна", "accuracy", "base metric"]):
            df[col] = (
                df[col].astype(str)
                .str.replace("$", "", regex=False)
                .str.replace("€", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.replace(" ", "", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    name_col = next((c for c in df.columns if any(k in c.lower() for k in ["game", "title", "назва"])), df.columns[0])
    df.rename(columns={name_col: "Game_Name_Clean"}, inplace=True)
    df = df[df["Game_Name_Clean"].astype(str).str.strip() != ""]
    return df

raw_df = load_data(GOOGLE_SHEET_URL)

if raw_df.empty:
    st.info("👋 Вкажи валідне посилання на Google Таблицю у рядку `GOOGLE_SHEET_URL` у коді.")
    st.stop()

cover_col = next((c for c in raw_df.columns if any(k in c.lower() for k in ["cover", "image", "постер", "обкладинка"])), None)
DEFAULT_IMAGE = "https://img.icons8.com/isometric/100/controller.png"

# Розділяємо дані на РЕАЛЬНІ РЕЛІЗИ (Факт) та ПОТЕНЦІЙНІ ЛІДИ (Скаутинг)
total_fact_col = next((c for c in raw_df.columns if c.lower() == "total" or "всього" in c.lower()), None)
if not total_fact_col:
    sum_cols = [c for c in raw_df.columns if "all time" in c.lower() or "revenue all" in c.lower()]
    raw_df["Total_Fact"] = raw_df[sum_cols].sum(axis=1) if sum_cols else 0.0
    total_fact_col = "Total_Fact"

# Ігри, де Total > 0 або є реальний виторг — це фактичні релізи
df_released = raw_df[raw_df[total_fact_col] > 0].copy()
# Ігри, де Total == 0, але є Base Metric чи прогноз — це потенційні ліди
df_leads = raw_df[raw_df[total_fact_col] == 0].copy()

# Якщо всі ігри мають Total > 0, показуємо повну базу
if df_leads.empty:
    df_leads = raw_df.copy()

# Сайдбар
with st.sidebar:
    st.header("🎮 Upscale Studio BI")
    if st.button("🔄 Оновити дані з Google Sheets", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.subheader("🔍 Фільтри")
    search = st.text_input("Пошук гри:", "")
    
    genre_col = next((c for c in raw_df.columns if "genre" in c.lower() or "жанр" in c.lower()), None)
    if genre_col:
        available_genres = sorted([str(g).strip() for g in raw_df[genre_col].dropna().unique() if str(g).strip().lower() != 'nan'])
        if available_genres:
            genres = st.multiselect("Жанри:", options=available_genres, default=available_genres)
            if genres:
                df_released = df_released[df_released[genre_col].astype(str).str.strip().isin(genres)]
                df_leads = df_leads[df_leads[genre_col].astype(str).str.strip().isin(genres)]

    if search:
        df_released = df_released[df_released["Game_Name_Clean"].astype(str).str.contains(search, case=False, na=False)]
        df_leads = df_leads[df_leads["Game_Name_Clean"].astype(str).str.contains(search, case=False, na=False)]

# РОЗРАХУНОК ФАКТИЧНИХ МЕТРИК
def get_platform_sum(df_target, keyword):
    cols = [c for c in df_target.columns if keyword in c.lower() and any(k in c.lower() for k in ["all", "total", "revenue"])]
    if cols: return float(df_target[cols[0]].sum())
    return 0.0

total_gross_fact = float(df_released[total_fact_col].sum())
switch_rev_fact = get_platform_sum(df_released, "switch")
ps_rev_fact = get_platform_sum(df_released, "playstation") if get_platform_sum(df_released, "playstation") > 0 else get_platform_sum(df_released, "ps")
xbox_rev_fact = get_platform_sum(df_released, "xbox")

# ГОЛОВНИЙ ЕКРАН
st.title("🚀 Console Publishing & Sourcing Hub")
st.caption(f"Upscale Studio • Релізних ігор (Факт): **{len(df_released)}** | Потенційних лідів у пайплайні: **{len(df_leads)}**")

# ГОЛОВНІ ВКЛАДКИ
tab_released, tab_leads, tab_sandbox, tab_whatif, tab_table = st.tabs([
    "🏆 Релізне портфоліо (ФАКТ)", 
    "🎯 Пайплайн лідів (ПРОГНОЗ)", 
    "🧮 Швидкий Live-Калькулятор", 
    "🔮 What-If Моделювання росту", 
    "📑 Повна база даних"
])

# =========================================================
# 🏆 1. РЕЛІЗНЕ ПОРТФОЛІО (ФАКТИЧНІ РЕЗУЛЬТАТИ)
# =========================================================
with tab_released:
    st.subheader("🏆 Фактичні фінансові показники випущених ігор")
    
    switch_pct = round(switch_rev_fact / max(total_gross_fact, 1) * 100) if total_gross_fact > 0 else 0
    ps_pct = round(ps_rev_fact / max(total_gross_fact, 1) * 100) if total_gross_fact > 0 else 0
    xbox_pct = round(xbox_rev_fact / max(total_gross_fact, 1) * 100) if total_gross_fact > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="kpi-card"><div class="kpi-label">Фактична каса портфоліо</div><div class="kpi-value">${total_gross_fact:,.2f}</div><span class="kpi-badge badge-total">100% Realized</span></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card"><div class="kpi-label">Nintendo Switch</div><div class="kpi-value" style="color:#ff6b6b !important;">${switch_rev_fact:,.2f}</div><span class="kpi-badge badge-switch">↑ {switch_pct}% частка</span></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card"><div class="kpi-label">PlayStation</div><div class="kpi-value" style="color:#60a5fa !important;">${ps_rev_fact:,.2f}</div><span class="kpi-badge badge-ps">↑ {ps_pct}% частка</span></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi-card"><div class="kpi-label">Xbox</div><div class="kpi-value" style="color:#4ade80 !important;">${xbox_rev_fact:,.2f}</div><span class="kpi-badge badge-xbox">↑ {xbox_pct}% частка</span></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    c_left, c_right = st.columns([1, 2])
    with c_left:
        st.subheader("Частка консолей у виручці")
        plat_df = pd.DataFrame({"Platform": ["Nintendo Switch", "PlayStation", "Xbox"], "Revenue": [switch_rev_fact, ps_rev_fact, xbox_rev_fact]})
        plat_df = plat_df[plat_df["Revenue"] > 0]
        if not plat_df.empty:
            fig_pie = px.pie(plat_df, values="Revenue", names="Platform", hole=0.5, color="Platform", color_discrete_map={"Nintendo Switch": "#e60012", "PlayStation": "#3b82f6", "Xbox": "#107c10"})
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0", size=13), margin=dict(t=15, b=15, l=15, r=15))
            st.plotly_chart(fig_pie, use_container_width=True)
    with c_right:
        st.subheader("Топ-10 бестселерів за фактичною касою ($)")
        top_df = df_released.sort_values(by=total_fact_col, ascending=True).tail(10)
        fig_bar = px.bar(top_df, x=total_fact_col, y="Game_Name_Clean", orientation="h", text=total_fact_col, color_discrete_sequence=["#6366f1"])
        fig_bar.update_traces(texttemplate='$%{text:,.0f}', textposition='outside', textfont=dict(color="#ffffff"))
        fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"), xaxis=dict(gridcolor="#28283c", title="Виторг ($)"), yaxis=dict(gridcolor="#28283c", title=""), margin=dict(t=15, b=15, l=15, r=15))
        st.plotly_chart(fig_bar, use_container_width=True)

# =========================================================
# 🎯 2. ПАЙПЛАЙН ПОТЕНЦІЙНИХ ЛІДІВ (СКАУТИНГ)
# =========================================================
with tab_leads:
    st.subheader("🎯 Потенційні ігри для підписання (Pipeline Forecast)")
    st.caption("Оцінка та розрахунок прогнозів для нових знайдених лідів зі Steam / Google Play / Web")

    # Шукаємо колонку з прогнозом M1
    lead_total_col = next((c for c in df_leads.columns if any(k in c.lower() for k in ["total", "forecast", "прогноз", "сума"])), total_fact_col)
    pipeline_potential = float(df_leads[lead_total_col].sum()) if lead_total_col in df_leads.columns else 0.0

    l_c1, l_c2, l_c3 = st.columns(3)
    l_c1.metric("Ігор у скаутинг-пайплайні", len(df_leads))
    l_c2.metric("Сумарний M1 потенціал лідів", f"${pipeline_potential:,.2f}")
    l_c3.metric("Середній очікуваний M1 чек", f"${pipeline_potential / max(len(df_leads), 1):,.2f}")

    st.markdown("---")
    st.subheader("Картки оцінки лідів")
    
    for _, l_row in df_leads.iterrows():
        g_name = l_row["Game_Name_Clean"]
        g_genre = l_row.get(genre_col, "Simulator") if genre_col else "Simulator"
        g_src = l_row.get("Platform", "Steam")
        g_price = l_row.get("Price consoles", 9.99)
        g_pred_total = l_row.get(lead_total_col, 0.0)
        img_url = l_row[cover_col] if cover_col and pd.notna(l_row[cover_col]) and str(l_row[cover_col]).startswith("http") else DEFAULT_IMAGE
        
        # Бейдж окупності
        badge_color = "#10b981" if g_pred_total >= 6000 else ("#f59e0b" if g_pred_total >= 3000 else "#ef4444")
        badge_text = "ТОП ЛІД" if g_pred_total >= 6000 else ("СТАНДАРТ" if g_pred_total >= 3000 else "НИЗЬКИЙ ЧЕК")

        st.markdown(f"""
        <div class="insight-card-flex">
            <img src="{img_url}" class="game-poster" onerror="this.src='{DEFAULT_IMAGE}'">
            <div style="flex-grow: 1;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h4 style="margin:0; color:#ffffff; font-size:16px;">🎮 {g_name} <span style="font-size:12px; color:#94a3b8;">({g_src} • ${g_price})</span></h4>
                    <span style="background-color:{badge_color}; color:#fff; padding:3px 8px; border-radius:12px; font-size:11px; font-weight:bold;">{badge_text}</span>
                </div>
                <p style="margin:4px 0 2px 0; font-size:13px; color:#a5b4fc;"><b>Жанр:</b> {g_genre}</p>
                <p style="margin:0; font-size:15px; color:#34d399; font-weight:bold;">💰 Прогноз M1 Total: ${g_pred_total:,.2f}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# 🧮 3. ШВИДКИЙ LIVE-КАЛЬКУЛЯТОР (SANDBOX)
# =========================================================
with tab_sandbox:
    st.subheader("🧮 Інтерактивний калькулятор для 1 нового ліда")
    st.caption("Введи параметри гри зі Steam/Google Play та отримай прогноз за 16 відкаліброваними піджанрами")

    col_in,
