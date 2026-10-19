import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 🩸 1. 페이지 기본 설정
st.set_page_config(page_title="핏빛 인구 피라미드", layout="wide")

# 🩸 2. 공포스러운 분위기를 위한 커스텀 CSS (블랙 & 레드)
st.markdown("""
<style>
    /* 전체 배경을 칠흑 같은 검은색으로 */
    .stApp {
        background-color: #050000;
    }
    /* 텍스트를 핏빛 빨간색으로 */
    h1, h2, h3, p, span, div, label {
        color: #8B0000 !important; 
        font-family: '궁서', 'Gungsuh', serif !important;
    }
    /* 지표 카드 스타일링 (어두운 붉은 테두리) */
    [data-testid="metric-container"] {
        background-color: #110000 !important;
        border: 1px solid #4a0000;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 0 10px #4a0000;
    }
    /* 드롭다운 메뉴 스타일 약간 조정 */
    .stSelectbox > div[data-baseweb="select"] {
        background-color: #110000;
        color: #ff0000;
    }
</style>
""", unsafe_allow_html=True)

st.title("🩸 피에 물든 인구 피라미드...")
st.markdown("이 동네에는... 누가 얼마나 살고 있을까요...?")

# 데이터 불러오기 함수
@st.cache_data
def load_data():
    url = "https://github.com/siwoo9831-alt/population/blob/main/population_ts_yearly_gender.zip?raw=true"
    try:
        df = pd.read_csv(url, compression='zip')
    except UnicodeDecodeError:
        df = pd.read_csv(url, compression='zip', encoding='cp949')
    return df

with st.spinner("어둠 속에서 데이터를 끌어올리는 중..."):
    df = load_data()

latest_year = df['연도'].max()
df_latest = df[df['연도'] == latest_year]

# 지역 선택 드롭다운
col1, col2, col3 = st.columns(3)
sido_list = df_latest['시도'].dropna().unique()
with col1:
    selected_sido = st.selectbox("어느 시도를 엿보시겠습니까?", sido_list)

df_sigungu = df_latest[df_latest['시도'] == selected_sido]
sigungu_list = df_sigungu['시군구'].dropna().unique()
with col2:
    selected_sigungu = st.selectbox("어느 시군구를 엿보시겠습니까?", sigungu_list)

df_dong = df_sigungu[df_sigungu['시군구'] == selected_sigungu]
dong_list = df_dong['동'].dropna().unique()
with col3:
    selected_dong = st.selectbox("마지막으로, 동을 선택하십시오...", dong_list)

final_data = df_dong[df_dong['동'] == selected_dong]

if not final_data.empty:
    # 🩸 3. 데이터 계산 (총인구, 평균연령, 고령화율, 유소년/노년층 인구)
    total_pop = 0
    total_age_sum = 0
    elderly_pop = 0 # 65세 이상
    kids_pop = 0    # 0~14세
    
    male_pop = []
    female_pop = []
    ages = []
    
    for i in range(101):
        age_str = "100세 이상" if i == 100 else f"{i}세"
        ages.append(age_str)
        
        m_col = f"남_{age_str}"
        f_col = f"여_{age_str}"
