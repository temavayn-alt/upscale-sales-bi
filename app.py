import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime
import re
from groq import Groq

# ==============================================================================
# 🔗 НАЛАШТУВАННЯ ТАБЛИЦЬ ТА БЕЗКОШТОВНОГО ШІ:
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?usp=sharing"
GOOGLE_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzrYmeab3xtC4TW9id-N60pI6UmOk6OJj7L2OebkV48omIzqD_h827g3C1mSUpt_WusyA/exec" # (Опціонально) Webhook URL для автозапису лідів
GROQ_API_KEY = ""       # 🎁 Встав безкоштовний ключ Groq (gsk_...) або вводитимеш у додатку
# ==============================================================================

st.set_page_config(
    page_title="Upscale Studio | Console BI & Sales Hub",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Стилі темної теми високої контрастності
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
    .game-poster { width: 85px; height: 105px; object-fit: cover; border-radius: 6px; flex-shrink: 0; }
    .top-podium-card { background: #181824; border: 1px solid #2b2b3f; border-radius: 10px; padding: 12px; text-align: center; }
    .sandbox-box { background: #171724; border: 1px solid #2f2f45; border-radius: 12px; padding: 20px; margin-bottom: 15px; }
    .one-pager-container { background-color: #111827; color: #f8fafc; padding: 25px; border-radius: 12px; border: 1px solid #374151; }
</style>
""", unsafe_allow_html=True)

NINTENDO_SCHEDULE = [
    {"name": "1. Autumn Sale", "start": "2026-09-11", "end": "2026-09-24", "status": "🔥 Найближчий"},
    {"name": "2. Halloween Sale", "start": "2026-10-26", "end": "2026-11-15", "status": "🎃 Сезонний"},
    {"name": "3. Holiday Sale (EU)", "start": "2026-12-17", "end": "2027-01-10", "status": "🎄 Головний (EU)"},
    {"name": "4. Holiday Sale (US)", "start": "2026-12-21", "end": "2027-01-11", "status": "🎄 Головний (US)"}
]

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

if "scouted_leads" not in st.session_state:
    st.session_state.scouted_leads = []

# Сайдбар
with st.sidebar:
    st.header("🎮 Upscale Studio BI")
    
    app_mode = st.radio(
        "📍 Оберіть розділ хабу:",
        ["🎮 Наші ігри", "🧮 Калькулятор прогнозів"],
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

    # =========================================================
    # 🤖 БЕЗКОШТОВНИЙ AI-АСИСТЕНТ (GROQ LLAMA 3.3 70B)
    # =========================================================
    st.markdown("---")
    st.subheader("🤖 Безкоштовний AI (Llama 3.3)")
    groq_key = GROQ_API_KEY or st.secrets.get("GROQ_API_KEY", "")
    
    if not groq_key:
        groq_key = st.text_input("Введи безкоштовний Groq Key:", type="password", placeholder="gsk_...")
        st.caption("🎁 Отримати безкоштовний ключ: [console.groq.com](https://console.groq.com/)")

    ai_query = st.text_area("Запитай щось у бази:", placeholder="Напр.: Які топ-3 хоррори принесли найбільше грошей на PlayStation?")
    
    if st.button("⚡ Запитати у ШІ", use_container_width=True):
        if not groq_key:
            st.error("Введи ключ Groq (gsk_...)! Він повністю безкоштовний на console.groq.com.")
        elif not ai_query.strip():
            st.warning("Введи запитання.")
        else:
            with st.spinner("Llama 3.3 70B аналізує портфоліо..."):
                try:
                    client = Groq(api_key=groq_key)
                    cols_for_ai = ["Game_Name_Clean"]
                    if genre_col: cols_for_ai.append(genre_col)
                    revenue_cols = [c for c in filtered_df.columns if any(k in c.lower() for k in ["revenue", "total", "price", "switch", "playstation", "xbox"])]
                    cols_for_ai.extend(revenue_cols[:8])
                    cols_for_ai = list(dict.fromkeys([c for c in cols_for_ai if c in filtered_df.columns]))
                    
                    data_summary_csv = filtered_df[cols_for_ai].head(45).to_csv(index=False)
                    
                    prompt = f"""
                    Ти провідний фінансовий аналітик консольного видавництва Upscale Studio (Харків, Україна).
                    Ось дані портфоліо видавництва:
                    {data_summary_csv}
                    
                    Запитання користувача: {ai_query}
                    
                    Дай чітку, структуровану відповідь українською мовою з конкретними цифрами з бази, висновками та бізнес-рекомендаціями. Без зайвої води.
                    """
                    
                    chat_completion = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.3-70b-versatile",
                        temperature=0.2,
                        max_tokens=700
                    )
                    st.info(chat_completion.choices[0].message.content)
                except Exception as e:
                    st.error(f"Помилка Groq API: {e}")

# Розрахунок All-Time сум
def get_platform_all_time_sum(df_target, keyword):
    exact_cols = [c for c in df_target.columns if keyword in c.lower() and any(k in c.lower() for k in ["all time", "all_time", "all", "разом"])]
    if exact_cols: return float(df_target[exact_cols[0]].sum())
    fallback_cols = [c for c in df_target.columns if keyword in c.lower() and "revenue" in c.lower() and "1st" not in c.lower() and "3" not in c.lower() and "6" not in c.lower()]
    if fallback_cols: return float(df_target[fallback_cols[0]].sum())
    return 0.0

switch_rev = get_platform_all_time_sum(filtered_df, "switch")
ps_rev = get_platform_all_time_sum(filtered_df, "playstation") if get_platform_all_time_sum(filtered_df, "playstation") > 0 else get_platform_all_time_sum(filtered_df, "ps")
xbox_rev = get_platform_all_time_sum(filtered_df, "xbox")
steam_rev = get_platform_all_time_sum(filtered_df, "steam")

total_col = next((c for c in filtered_df.columns if c.lower() == "total" or "всього" in c.lower()), None)
if total_col:
    total_gross = float(filtered_df[total_col].sum())
else:
    total_gross = switch_rev + ps_rev + xbox_rev + steam_rev

# ==============================================================================
# 🎮 РОЗДІЛ 1: НАШІ ІГРИ (7 ВКЛАДОК)
# ==============================================================================
if app_mode == "🎮 Наші ігри":
    st.title("📊 Портфоліо Upscale Studio")
    st.caption(f"Фактичні результати випущених ігор • Всього проаналізовано: **{len(filtered_df)}**")

    switch_pct = round(switch_rev / max(total_gross, 1) * 100) if total_gross > 0 else 0
    ps_pct = round(ps_rev / max(total_gross, 1) * 100) if total_gross > 0 else 0
    xbox_pct = round(xbox_rev / max(total_gross, 1) * 100) if total_gross > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="kpi-card"><div class="kpi-label">Загальна каса портфоліо (All-Time)</div><div class="kpi-value">${total_gross:,.2f}</div><span class="kpi-badge badge-total">100% Total Gross</span></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card"><div class="kpi-label">Nintendo Switch (All-Time)</div><div class="kpi-value" style="color:#ff6b6b !important;">${switch_rev:,.2f}</div><span class="kpi-badge badge-switch">↑ {switch_pct}% частка</span></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card"><div class="kpi-label">PlayStation (All-Time)</div><div class="kpi-value" style="color:#60a5fa !important;">${ps_rev:,.2f}</div><span class="kpi-badge badge-ps">↑ {ps_pct}% частка</span></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi-card"><div class="kpi-label">Xbox (All-Time)</div><div class="kpi-value" style="color:#4ade80 !important;">${xbox_rev:,.2f}</div><span class="kpi-badge badge-xbox">↑ {xbox_pct}% частка</span></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_overview, tab_decay, tab_insights, tab_sales_tracker, tab_one_pager, tab_forecast_review, tab_table = st.tabs([
        "📈 Огляд і Топ ігор", 
        "⏳ Динаміка каси (M1 ➔ 1Y)", 
        "🧠 Formula & AI Insights", 
        "📅 Трекер розпродажів Nintendo",
        "📄 One-Pager Звіт (PDF)",
        "🎯 Прогнози наших ігор (План vs Факт)",
        "📑 Повна фінансова таблиця"
    ])

    with tab_overview:
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

    with tab_decay:
        st.subheader("Крива динаміки виручки (M1 ➔ M3 ➔ M6 ➔ 1Y)")
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
        st.subheader("📅 Трекер вікон розпродажів Nintendo eShop")
        sale_choice = st.selectbox(
            "Оберіть плановий розпродаж Nintendo:",
            [f"{s['name']} (Старт: {s['start']} | {s['status']})" for s in NINTENDO_SCHEDULE],
            index=0
        )
        selected_sale_data = NINTENDO_SCHEDULE[0]
        for s in NINTENDO_SCHEDULE:
            if s["name"] in sale_choice:
                selected_sale_data = s
                break

        target_start_date = datetime.strptime(selected_sale_data["start"], "%Y-%m-%d")
        rel_col = next((c for c in filtered_df.columns if "release" in c.lower() or "date" in c.lower() or "дата" in c.lower()), None)
        
        tracker_rows = []
        for _, r in filtered_df.iterrows():
            g_name = r["Game_Name_Clean"]
            r_date_str = str(r[rel_col]).strip() if rel_col and pd.notna(r[rel_col]) else "2026-05-01"
            try: r_date = datetime.strptime(r_date_str[:10], "%Y-%m-%d")
            except: r_date = datetime(2026, 5, 1)

            days_since_rel = (target_start_date - r_date).days
            if days_since_rel >= 30:
                sale_status = "🟢 Готова до сейлу"
                note = f"Пройшло {days_since_rel} дн. (Кулдаун OK)"
            else:
                sale_status = "🟡 Кулдаун"
                note = f"Залишилось {30 - days_since_rel} дн."

            tracker_rows.append({
                "Гра": g_name,
                "Дата релізу": r_date.strftime("%Y-%m-%d"),
                "Цільовий сейл": selected_sale_data["name"],
                "Статус Nintendo": sale_status,
                "Деталі": note
            })

        tracker_df = pd.DataFrame(tracker_rows)
        ready_count = len(tracker_df[tracker_df["Статус Nintendo"].str.contains("Готова")])
        
        t_c1, t_c2, t_c3 = st.columns(3)
        t_c1.metric("Цільовий сейл", selected_sale_data["name"], selected_sale_data["start"])
        t_c2.metric("Готових ігор", f"{ready_count} з {len(tracker_df)}")
        t_c3.metric("У кулдауні", len(tracker_df) - ready_count)

        st.markdown("---")
        st.dataframe(tracker_df, use_container_width=True, height=360)

    with tab_one_pager:
        st.subheader("📄 One-Pager Executive Звіт (Social Proof для пітчів)")
        st.markdown(f"""
        <div class="one-pager-container">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #334155; padding-bottom:12px; margin-bottom:16px;">
                <div>
                    <h2 style="margin:0; color:#ffffff; letter-spacing:0.5px;">UPSCALE STUDIO</h2>
                    <p style="margin:0; color:#94a3b8; font-size:13px;">Console Publishing & Porting Operations Report</p>
                </div>
                <div style="text-align:right;">
                    <span style="background:#4f46e5; color:#fff; padding:4px 10px; border-radius:6px; font-weight:bold; font-size:12px;">PORTFOLIO AUDIT</span>
                    <p style="margin:4px 0 0 0; color:#64748b; font-size:11px;">Data as of {datetime.now().strftime('%B %Y')}</p>
                </div>
            </div>

            <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:12px; margin-bottom:20px;">
                <div style="background:#1e293b; padding:14px; border-radius:8px; text-align:center;">
                    <p style="margin:0; font-size:11px; color:#94a3b8;">TOTAL CONSOLE GROSS</p>
                    <h3 style="margin:4px 0 0 0; color:#38bdf8;">${total_gross:,.0f}</h3>
                </div>
                <div style="background:#1e293b; padding:14px; border-radius:8px; text-align:center;">
                    <p style="margin:0; font-size:11px; color:#94a3b8;">PLAYSTATION</p>
                    <h3 style="margin:4px 0 0 0; color:#60a5fa;">${ps_rev:,.0f}</h3>
                </div>
                <div style="background:#1e293b; padding:14px; border-radius:8px; text-align:center;">
                    <p style="margin:0; font-size:11px; color:#94a3b8;">NINTENDO SWITCH</p>
                    <h3 style="margin:4px 0 0 0; color:#f87171;">${switch_rev:,.0f}</h3>
                </div>
                <div style="background:#1e293b; padding:14px; border-radius:8px; text-align:center;">
                    <p style="margin:0; font-size:11px; color:#94a3b8;">XBOX</p>
                    <h3 style="margin:4px 0 0 0; color:#4ade80;">${xbox_rev:,.0f}</h3>
                </div>
            </div>

            <h4 style="color:#f1f5f9; margin-bottom:8px;">🏆 Key Portfolio Breakouts:</h4>
            <p style="color:#cbd5e1; font-size:13px; line-height:1.6; margin:0 0 10px 0;">
                • <b>Cat From Hell:</b> Multi-platform hit ($119k+ All-Time Gross) driven by viral PlayStation engagement.<br>
                • <b>Bad Cat:</b> Outstanding Switch & PS performance ($78k+ All-Time Gross).<br>
                • <b>Skinwalker:</b> High-converting Xbox 3D Horror breakout ($21k+ All-Time).<br>
                • <b>Conquistadorio:</b> High-price tier ($19.99) quest success ($25k+ All-Time).
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("💡 Щоб зберегти як PDF: натисни **Ctrl + P (Cmd + P на Mac)** ➔ обери *Зберегти як PDF*.")

    with tab_forecast_review:
        st.subheader("🎯 Порівняння прогнозованих та
