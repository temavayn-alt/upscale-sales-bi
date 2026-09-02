import streamlit as st
import pandas as pd
import plotly.express as px
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
        st.error(f"❌ Помилка завантаження таблиці. Перевір доступ за посиланням ('Усі, хто має посилання - Читач'). Текст: {e}")
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
    
    # БЕЗПЕЧНА ФІЛЬТРАЦІЯ ЖАНРІВ (БЕЗ NaN ПОМИЛОК)
    genre_col = next((c for c in df.columns if "genre" in c.lower() or "жанр" in c.lower()), None)
    if genre_col:
        # Вичищаємо порожні значення та перетворюємо на чисті рядки
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
k4.metric("Xbox", f"${xbox_rev:,.2f}
