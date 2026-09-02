import streamlit as st
import pandas as pd
import plotly.express as px
import re

# ==============================================================================
# 🔗 ТВОЄ ПОСИЛАННЯ НА GOOGLE ТАБЛИЦЮ:
# (Переконайся, що в доступі стоїть: "Усі, хто має посилання - Читач")
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fUOV3bYgqMHd23lFp-dL7fkO3SxsbO0c2CCoRi8BczQ/edit?usp=sharing"
# ==============================================================================

st.set_page_config(
    page_title="Upscale Studio | Console Analytics Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Стилі для темного інтерфейсу
st.markdown("""
<style>
    .insight-card {
        background-color: #1e1e2f;
        border-left: 5px solid #6366f1;
        padding: 14px 18px;
        border-radius: 8px;
        margin-bottom: 12px;
        border: 1px solid #2d2d42;
    }
    .stMetric { background-color: #1a1a26; padding: 12px; border-radius: 8px; border: 1px solid #2d2d3d; }
</style>
""", unsafe_allow_html=True)

def get_export_url(url_or_id):
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url_or_id)
    sheet_id = match.group(1) if match else url_or_id.strip()
    gid_match = re.search(r"[#&]gid=([0-9]+)", url_or_id)
    gid = gid_match.group(1) if gid_match else "0"
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

@st.cache_data(ttl=300, show_spinner=False)
def load_data(sheet_url):
    if not sheet_url or "ВСТАВ_СЮДИ" in sheet_url:
        st.warning("⚠️ Вкажи посилання на свою Google Таблицю у рядку `GOOGLE_SHEET_URL`.")
        return pd.DataFrame()
        
    csv_url = get_export_url(sheet_url)
    try:
        df = pd.read_csv(csv_url)
    except Exception as e:
        st.error(f"❌ Помилка завантаження таблиці. Перевір доступ за посиланням. Текст: {e}")
        return pd.DataFrame()

    # Очищення числових колонок
    for col in df.columns:
        col_lower = str(col).lower()
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

    # Визначаємо назву гри
    name_col = next((c for c in df.columns if "game" in c.lower() or "title" in c.lower() or "назва" in c.lower()), df.columns[0])
    df.rename(columns={name_col: "Game_Name_Clean"}, inplace=True)
    df = df[df["Game_Name_Clean"].astype(str).str.strip() != ""]
    return df

df = load_data(GOOGLE_SHEET_URL)

if df.empty:
    st.stop()

# Автопошук колонки Total
total_col = next((c for c in df.columns if c.lower() == "total" or "всього" in c.lower()), None)
if not total_col:
    total_col = "Calculated_Total"
    df[total_col] = df[[c for c in df.columns if "all" in c.lower() or "total" in c.lower()]].sum(axis=1)

# Бічна панель: Фільтри та кнопка оновлення
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
        genres = st.multiselect("Жанри:", options=df[genre_col].unique(), default=df[genre_col].unique())
        df = df[df[genre_col].isin(genres)]

    if search:
        df = df[df["Game_Name_Clean"].astype(str).str.contains(search, case=False, na=False)]

# Розрахунок платформних сум
def get_platform_sum(keyword):
    cols = [c for c in df.columns if keyword in c.lower() and ("all" in c.lower() or "total" in c.lower() or "revenue" in c.lower())]
    if cols:
        return df[cols[0]].sum()
    return 0.0

total_gross = df[total_col].sum()
switch_rev = get_platform_sum("switch")
ps_rev = get_platform_sum("playstation") or get_platform_sum("ps")
xbox_rev = get_platform_sum("xbox")

# Головні KPI
st.title("📊 Console Sales & Revenue Intelligence")
st.caption(f"Портфоліо Upscale Studio • Всього тайтлів: {len(df)}")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Загальна каса портфоліо", f"${total_gross:,.2f}")
k2.metric("Nintendo Switch", f"${switch_rev:,.2f}", f"{round(switch_rev/max(total_gross, 1)*100)}% частка" if total_gross > 0 else "0%")
k3.metric("PlayStation", f"${ps_rev:,.2f}", f"{round(ps_rev/max(total_gross, 1)*100)}% частка" if total_gross > 0 else "0%")
k4.metric("Xbox", f"${xbox_rev:,.2f}", f"{round(xbox_rev/max(total_gross, 1)*100)}% частка" if total_gross > 0 else "0%")

st.markdown("---")

# Вкладки
tab_overview, tab_decay, tab_insights, tab_table = st.tabs([
    "📈 Огляд і Топ ігор", 
    "⏳ Динаміка каси (M1 ➔ 1Y)", 
    "🧠 Formula & AI Insights", 
    "📑 Повна фінансова таблиця"
])

# --- ВКЛАДКА 1: ОГЛЯД ---
with tab_overview:
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
                plat_df, values="Revenue", names="Platform", hole=0.45,
                color="Platform",
                color_discrete_map={"Nintendo Switch": "#e60012", "PlayStation": "#003791", "Xbox": "#107c10"}
            )
            fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Дані по платформах відсутні.")

    with c_right:
        st.subheader("Топ тайтлів за виторгом ($)")
        top_df = df.sort_values(by=total_col, ascending=True).tail(15)
        fig_bar = px.bar(
            top_df, x=total_col, y="Game_Name_Clean", orientation="h",
            text=total_col, color_discrete_sequence=["#6366f1"]
        )
        fig_bar.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        fig_bar.update_layout(margin=dict(t=10, b=10, l=10, r=10), xaxis_title="Виторг ($)", yaxis_title="")
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
        fig_line.update_layout(yaxis_title="Накопичений виторг ($)", xaxis_title="Період")
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Колонки часових періодів не знайдено.")

# --- ВКЛАДКА 3: ІНСАЙТИ ---
with tab_insights:
    st.subheader("Стратегічні висновки (Formula & AI Insights)")
    formula_col = next((c for c in df.columns if "formula" in c.lower()), None)
    ai_col = next((c for c in df.columns if "ai" in c.lower()), None)
    
    for _, row in df.iterrows():
        g_name = row["Game_Name_Clean"]
        rev_val = row[total_col]
        f_text = row[formula_col] if formula_col and pd.notna(row[formula_col]) else "—"
        ai_text = row[ai_col] if ai_col and pd.notna(row[ai_col]) else "—"
        
        st.markdown(f"""
        <div class="insight-card">
            <h4 style="margin:0 0 6px 0; color:#fff;">🎮 {g_name} — <span style="color:#10b981;">${rev_val:,.2f}</span></h4>
            <p style="margin:0 0 4px 0; font-size:13px; color:#818cf8;"><b>📐 Формула:</b> {f_text}</p>
            <p style="margin:0; font-size:13px; color:#cbd5e1;"><b>💡 AI Аналіз:</b> {ai_text}</p>
        </div>
        """, unsafe_allow_html=True)

# --- ВКЛАДКА 4: ТАБЛИЦЯ ---
with tab_table:
    st.subheader("Повна фінансова таблиця")
    st.dataframe(df, use_container_width=True, height=500)
    
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Експортувати у CSV", data=csv_data, file_name="console_sales_full.csv", mime="text/csv")
