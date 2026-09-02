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
    page_title="Upscale Studio | Console Analytics Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Преміальні стилі темної теми високої контрастності
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    
    .kpi-card {
        background: linear-gradient(135deg, #1e1e2d 0%, #161622 100%);
        border: 1px solid #2e2e44;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
        margin-bottom: 10px;
    }
    .kpi-label { font-size: 12px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px; }
    .kpi-value { font-size: 26px; font-weight: 800; color: #ffffff !important; margin-bottom: 6px; font-family: -apple-system, sans-serif; }
    .kpi-badge { display: inline-block; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 6px; }
    .badge-total { background-color: rgba(99, 102, 241, 0.2); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.3); }
    .badge-switch { background-color: rgba(230, 0, 18, 0.18); color: #ff6b6b; border: 1px solid rgba(230, 0, 18, 0.3); }
    .badge-ps { background-color: rgba(0, 55, 145, 0.25); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
    .badge-xbox { background-color: rgba(16, 124, 16, 0.25); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.3); }
    
    .insight-card-flex {
        display: flex;
        gap: 16px;
        background-color: #171723;
        border-left: 4px solid #6366f1;
        padding: 14px 18px;
        border-radius: 8px;
        margin-bottom: 14px;
        border-top: 1px solid #28283c;
        border-right: 1px solid #28283c;
        border-bottom: 1px solid #28283c;
        align-items: center;
    }
    .game-poster {
        width: 85px;
        height: 105px;
        object-fit: cover;
        border-radius: 6px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.4);
        flex-shrink: 0;
        background-color: #1f1f2e;
    }
    .top-podium-card {
        background: #181824;
        border: 1px solid #2b2b3f;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
    }
    .sandbox-box {
        background: #171724;
        border: 1px solid #2f2f45;
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# 16 каліброваних профілів для Sandbox
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
        st.warning("⚠️ Вкажи посилання на свою Google Таблицю у рядку GOOGLE_SHEET_URL.")
        return pd.DataFrame()
        
    csv_url = get_export_url(sheet_url)
    try:
        df = pd.read_csv(csv_url)
    except Exception as e:
        st.error(f"❌ Помилка завантаження таблиці. Перевір доступ за посиланням. Текст: {e}")
        return pd.DataFrame()

    for col in df.columns:
        col_lower = str(col).lower()
        if any(img_k in col_lower for img_k in ["cover", "image", "постер", "url", "фото", "link"]):
            continue
        if any(k in col_lower for k in ["revenue", "price", "total", "$", "month", "year", "time", "всього", "ціна"]):
            df[col] = (
                df[col]
                .astype(str)
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

df = load_data(GOOGLE_SHEET_URL)

if df.empty:
    st.stop()

cover_col = next((c for c in df.columns if any(k in c.lower() for k in ["cover", "image", "постер", "обкладинка"])), None)
DEFAULT_IMAGE = "https://img.icons8.com/isometric/100/controller.png"

total_col = next((c for c in df.columns if c.lower() == "total" or "всього" in c.lower()), None)
if not total_col:
    total_col = "Calculated_Total"
    sum_cols = [c for c in df.columns if "all" in c.lower() or "total" in c.lower()]
    df[total_col] = df[sum_cols].sum(axis=1) if sum_cols else 0.0

with st.sidebar:
    st.header("📊 Upscale BI")
    if st.button("🔄 Оновити дані з таблиці", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.subheader("🔍 Фільтри")
    
    search = st.text_input("Пошук за назвою гри:", "")
    
    genre_col = next((c for c in df.columns if "genre" in c.lower() or "жанр" in c.lower()), None)
    if genre_col:
        available_genres = sorted([
            str(g).strip() for g in df[genre_col].dropna().unique() 
            if str(g).strip() and str(g).strip().lower() != 'nan'
        ])
        if available_genres:
            genres = st.multiselect("Жанри:", options=available_genres, default=available_genres)
            if genres:
                df = df[df[genre_col].astype(str).str.strip().isin(genres)]

    if search:
        df = df[df["Game_Name_Clean"].astype(str).str.contains(search, case=False, na=False)]

def get_platform_sum(keyword):
    cols = [c for c in df.columns if keyword in c.lower() and any(k in c.lower() for k in ["all", "total", "revenue"])]
    if cols:
        return float(df[cols[0]].sum())
    return 0.0

total_gross = float(df[total_col].sum())
switch_rev = get_platform_sum("switch")
ps_rev = get_platform_sum("playstation") if get_platform_sum("playstation") > 0 else get_platform_sum("ps")
xbox_rev = get_platform_sum("xbox")

# Заголовок
st.title("📊 Console Sales & Revenue Intelligence")
st.caption(f"Портфоліо Upscale Studio • Всього проаналізовано тайтлів: **{len(df)}**")

# Головні KPI-картки
switch_pct = round(switch_rev / max(total_gross, 1) * 100) if total_gross > 0 else 0
ps_pct = round(ps_rev / max(total_gross, 1) * 100) if total_gross > 0 else 0
xbox_pct = round(xbox_rev / max(total_gross, 1) * 100) if total_gross > 0 else 0

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Загальна каса портфоліо</div>
        <div class="kpi-value">${total_gross:,.2f}</div>
        <span class="kpi-badge badge-total">100% Total Gross</span>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Nintendo Switch</div>
        <div class="kpi-value" style="color:#ff6b6b !important;">${switch_rev:,.2f}</div>
        <span class="kpi-badge badge-switch">↑ {switch_pct}% частка</span>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">PlayStation</div>
        <div class="kpi-value" style="color:#60a5fa !important;">${ps_rev:,.2f}</div>
        <span class="kpi-badge badge-ps">↑ {ps_pct}% частка</span>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Xbox</div>
        <div class="kpi-value" style="color:#4ade80 !important;">${xbox_rev:,.2f}</div>
        <span class="kpi-badge badge-xbox">↑ {xbox_pct}% частка</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 5 Вкладок: 4 твоїх рідних + 1 новий Sandbox
tab_overview, tab_decay, tab_insights, tab_table, tab_sandbox = st.tabs([
    "📈 Огляд і Топ ігор", 
    "⏳ Динаміка каси (M1 ➔ 1Y)", 
    "🧠 Formula & AI Insights", 
    "📑 Повна фінансова таблиця",
    "🧮 Forecasting Sandbox (Калькулятор)"
])

# --- ВКЛАДКА 1: ОГЛЯД (Топ-3 подіум + Спліт + Топ-15) ---
with tab_overview:
    st.subheader("🏆 Топ-3 бестселери портфоліо")
    top3_df = df.sort_values(by=total_col, ascending=False).head(3)
    p_cols = st.columns(3)
    
    for idx, (_, top_row) in enumerate(top3_df.iterrows()):
        img_url = top_row[cover_col] if cover_col and pd.notna(top_row[cover_col]) and str(top_row[cover_col]).startswith("http") else DEFAULT_IMAGE
        with p_cols[idx]:
            st.markdown(f"""
            <div class="top-podium-card">
                <img src="{img_url}" style="width:100%; height:140px; object-fit:cover; border-radius:6px; margin-bottom:8px;">
                <h4 style="margin:0 0 4px 0; color:#fff;">#{idx+1} {top_row['Game_Name_Clean']}</h4>
                <p style="margin:0; font-size:18px; color:#34d399; font-weight:bold;">${top_row[total_col]:,.2f}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c_left, c_right = st.columns([1, 2])
    with c_left:
        st.subheader("Частка консолей у виручці")
        plat_df = pd.DataFrame({
            "Platform": ["Nintendo Switch", "PlayStation", "Xbox"],
            "Revenue": [switch_rev, ps_rev, xbox_rev]
        })
        plat_df = plat_df[plat_df["Revenue"] > 0]
        if not plat_df.empty:
            fig_pie = px.pie(
                plat_df, values="Revenue", names="Platform", hole=0.5,
                color="Platform",
                color_discrete_map={"Nintendo Switch": "#e60012", "PlayStation": "#3b82f6", "Xbox": "#10b981"}
            )
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#e2e8f0", size=13),
                margin=dict(t=15, b=15, l=15, r=15)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Дані по платформах відсутні.")

    with c_right:
        st.subheader("Топ-15 тайтлів за виторгом ($)")
        top_df = df.sort_values(by=total_col, ascending=True).tail(15)
        fig_bar = px.bar(
            top_df, x=total_col, y="Game_Name_Clean", orientation="h",
            text=total_col, color_discrete_sequence=["#6366f1"]
        )
        fig_bar.update_traces(texttemplate='$%{text:,.0f}', textposition='outside', textfont=dict(color="#ffffff"))
        fig_bar.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#e2e8f0"),
            xaxis=dict(gridcolor="#28283c", title="Виторг ($)"),
            yaxis=dict(gridcolor="#28283c", title=""),
            margin=dict(t=15, b=15, l=15, r=15)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# --- ВКЛАДКА 2: ДИНАМІКА КАСИ ---
with tab_decay:
    st.subheader("Крива динаміки виручки (M1 ➔ M3 ➔ M6 ➔ 1Y)")
    time_cols = [c for c in df.columns if any(p in c.lower() for p in ["1st", "3 month", "6 month", "1 year", "all time"])]
    
    if time_cols:
        decay_rows = []
        for _, row in df.iterrows():
            for t_col in time_cols:
                period_label = t_col
                if "1st" in t_col.lower() or "m1" in t_col.lower(): period_label = "1. M1"
                elif "3" in t_col.lower(): period_label = "2. M3"
                elif "6" in t_col.lower(): period_label = "3. M6"
                elif "year" in t_col.lower() or "1y" in t_col.lower(): period_label = "4. 1Y"
                elif "all" in t_col.lower(): period_label = "5. All Time"
                
                decay_rows.append({
                    "Game": row["Game_Name_Clean"],
                    "Period": period_label,
                    "Revenue": row[t_col]
                })
        
        decay_df = pd.DataFrame(decay_rows).sort_values("Period")
        fig_line = px.line(decay_df, x="Period", y="Revenue", color="Game", markers=True)
        fig_line.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#e2e8f0"),
            xaxis=dict(gridcolor="#28283c", title="Період"),
            yaxis=dict(gridcolor="#28283c", title="Накопичений виторг ($)"),
            margin=dict(t=15, b=15, l=15, r=15)
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Колонки часових періодів не знайдено.")

# --- ВКЛАДКА 3: ІНСАЙТИ З ПОСТЕРАМИ ---
with tab_insights:
    st.subheader("Стратегічні висновки та постери тайтлів")
    formula_col = next((c for c in df.columns if "formula" in c.lower()), None)
    ai_col = next((c for c in df.columns if "ai" in c.lower()), None)
    
    for _, row in df.iterrows():
        g_name = row["Game_Name_Clean"]
        rev_val = row[total_col]
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

# --- ВКЛАДКА 4: ТАБЛИЦЯ З МІНІАТЮРАМИ ---
with tab_table:
    st.subheader("Повна фінансова таблиця")
    
    column_config = {}
    if cover_col:
        column_config[cover_col] = st.column_config.ImageColumn("Обкладинка", width="small")
    
    st.dataframe(df, column_config=column_config, use_container_width=True, height=520)
    
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Експортувати у CSV", data=csv_data, file_name="console_sales_full.csv", mime="text/csv")

# --- ВКЛАДКА 5: FORECASTING SANDBOX (16 Жанрів) ---
with tab_sandbox:
    st.subheader("🧮 Інтерактивний калькулятор для нового ліда")
    st.caption("Матриця коефіцієнтів відкалібрована на базі 35+ реальних запусків Upscale Studio")

    sb_left, sb_right = st.columns([1, 1.25])

    with sb_left:
        st.markdown('<div class="sandbox-box">', unsafe_allow_html=True)
        st.markdown("#### 1. Вхідні дані гри")
        
        sb_name = st.text_input("Назва гри / ліда:", "New Game Lead")
        sb_src = st.selectbox("Джерело аналізу:", ["Steam", "Google Play", "CrazyGames / Web", "itch.io"])
        
        if sb_src == "Steam":
            s_rev = st.number_input("Steam All-Time Revenue ($):", min_value=0, value=5000, step=1000)
            s_revs = st.number_input("Steam Reviews:", min_value=0, value=80, step=10)
            b_metric = max(500.0, min(6500.0, s_rev * 0.16 + s_revs * 6.5))
        elif sb_src == "Google Play":
            gp_opts = st.selectbox("Завантаження Google Play:", [
                "10,000 - 50,000 (Нішева)",
                "100,000 (Стандартний лід)",
                "500,000 (Популярний лід)",
                "1,000,000 (Топ лід)",
                "5,000,000 - 10,000,000+ (Гіперкажуал)"
            ], index=1)
            if "10,000" in gp_opts: b_metric = 750.0
            elif "100,000" in gp_opts: b_metric = 1432.5
            elif "500,000" in gp_opts: b_metric = 2214.2
            elif "1,000,000" in gp_opts: b_metric = 2800.0
            else: b_metric = 5272.0
        elif sb_src == "CrazyGames / Web":
            cg_r = st.number_input("Кількість відгуків / оцінок:", min_value=0, value=3500, step=500)
            b_metric = max(600.0, min(3500.0, 900.0 + (cg_r / 1000.0) * 120.0))
        else:
            itch_r = st.number_input("Оцінки itch.io:", min_value=0, value=35, step=5)
            b_metric = max(400.0, min(2500.0, 400.0 + itch_r * 15.0))

        st.markdown("---")
        st.markdown("#### 2. Жанр і Ціноутворення")
        sb_genre = st.selectbox("Точний піджанр гри:", list(GENRE_DATABASE.keys()))
        sb_price = st.selectbox("Планова ціна на консолях ($):", list(PRICE_MODIFIERS.keys()), index=3)
        st.markdown('</div>', unsafe_allow_html=True)

    g_cfg = GENRE_DATABASE[sb_genre]
    p_mod = PRICE_MODIFIERS[sb_price]

    ps_est = b_metric * g_cfg["PS"] * p_mod
    ns_est = b_metric * g_cfg["Switch"] * p_mod
    xb_est = b_metric * g_cfg["Xbox"] * p_mod
    tot_m1 = ps_est + ns_est + xb_est
    tot_year = tot_m1 * g_cfg["Decay"]

    with sb_right:
        st.markdown('<div class="sandbox-box">', unsafe_allow_html=True)
        st.markdown(f"### 📈 Розрахунок: **{sb_name}**")
        st.caption(f"💡 *{g_cfg['Desc']}*")
        st.caption(f"Органічна база: **${b_metric:,.1f}** | Ціновий множник: **{p_mod}x**")
        
        if tot_m1 >= 6500:
            st.success("🟢 **ТОП ЛІД:** Рекомендовано надсилати пітч (M1 > $6.5k)")
        elif tot_m1 >= 3000:
            st.info("🟡 **СТАНДАРТНИЙ ТАЙТЛ:** Стабільний портфоліо-кандидат ($3k–$6.5k)")
        else:
            st.warning("🔴 **ВИСОКИЙ РИЗИК:** Низька прогнозована окупність (M1 < $3k)")

        st.markdown("---")
        
        m_c1, m_c2, m_c3 = st.columns(3)
        m_c1.metric("PlayStation (M1)", f"${ps_est:,.0f}", f"{g_cfg['PS']}x")
        m_c2.metric("Nintendo Switch (M1)", f"${ns_est:,.0f}", f"{g_cfg['Switch']}x")
        m_c3.metric("Xbox (M1)", f"${xb_est:,.0f}", f"{g_cfg['Xbox']}x")

        st.markdown("<br>", unsafe_allow_html=True)
        t_c1, t_c2 = st.columns(2)
        t_c1.metric("🔥 Разом за 1-й місяць (M1)", f"${tot_m1:,.0f}")
        t_c2.metric("📅 Річний виторг (1 Year LTV)", f"${tot_year:,.0f}", f"{g_cfg['Decay']}x")

        sb_chart_df = pd.DataFrame({
            "Platform": ["Nintendo Switch", "PlayStation", "Xbox"],
            "Forecast ($)": [ns_est, ps_est, xb_est]
        })
        fig_sb = px.bar(
            sb_chart_df, x="Platform", y="Forecast ($)", color="Platform", text="Forecast ($)",
            color_discrete_map={"Nintendo Switch": "#e60012", "PlayStation": "#3b82f6", "Xbox": "#107c10"}
        )
        fig_sb.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        fig_sb.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#e2e8f0"),
            height=250, margin=dict(t=15, b=10, l=10, r=10), showlegend=False
        )
        st.plotly_chart(fig_sb, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
