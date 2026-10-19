import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 🩸 1. 페이지 기본 설정
st.set_page_config(page_title="핏빛 인구 피라미드", layout="wide")

# 🩸 2. 공포스러운 분위기를 위한 커스텀 CSS (블랙 & 다크 레드)
st.markdown("""
<style>
    /* 전체 배경을 칠흑 같은 검은색으로 */
    .stApp {
        background-color: #050000;
    }
    /* 텍스트를 핏빛 빨간색으로, 글꼴은 궁서체로 */
    h1, h2, h3, p, span, div, label {
        color: #8B0000 !important; 
        font-family: '궁서', 'Gungsuh', serif !important;
    }
    /* 지표 카드 스타일링 (어두운 붉은 테두리와 그림자) */
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

# 데이터 불러오기 함수 (캐시 적용)
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

# 최신 연도 필터링
latest_year = df['연도'].max()
df_latest = df[df['연도'] == latest_year]

# 지역 선택 드롭다운 (3단계)
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

# ▼ 에러가 났던 바로 그 부분! 올바르게 수정되었습니다. ▼
final_data = df_dong[df_dong['동'] == selected_dong]

if not final_data.empty:
    # 🩸 3. 데이터 집계 및 계산 (총인구, 평균연령, 고령화율)
    total_pop = 0
    total_age_sum = 0
    elderly_pop = 0 # 65세 이상
    kids_pop = 0    # 0~14세
    
    male_pop = []
    female_pop = []
    ages = []
    
    # [핵심] 0세부터 100세 이상까지 순서대로 배열 생성
    for i in range(101):
        age_str = "100세 이상" if i == 100 else f"{i}세"
        ages.append(age_str)
        
        m_col = f"남_{age_str}"
        f_col = f"여_{age_str}"
        
        m_val = int(final_data[m_col].iloc[0])
        f_val = int(final_data[f_col].iloc[0])
        
        male_pop.append(m_val)
        female_pop.append(f_val)
        
        pop_sum = m_val + f_val
        total_pop += pop_sum
        total_age_sum += pop_sum * i
        
        if i >= 65:
            elderly_pop += pop_sum
        if i <= 14:
            kids_pop += pop_sum

    avg_age = total_age_sum / total_pop if total_pop > 0 else 0
    aging_rate = (elderly_pop / total_pop * 100) if total_pop > 0 else 0

    st.write("---")
    
    # 🩸 4. 상단 지표 카드 3개 나란히 배치
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    
    with metric_col1:
        st.metric("💀 총인구", f"{total_pop:,}명")
    with metric_col2:
        st.metric("⏳ 평균연령", f"{avg_age:.1f}세")
    with metric_col3:
        # 고령화율 20% 초과 시 초고령 위험 경고
        warning_sign = " 🚨 (초고령 위험)" if aging_rate > 20 else ""
        st.metric("🍂 고령화율(65세 이상)", f"{aging_rate:.1f}%{warning_sign}")

    st.write("---")

    # 남자는 그래프상 왼쪽으로 그려야 하므로 음수로 변환
    male_pop_neg = [-v for v in male_pop]
    
    # X축 눈금을 이쁘게 만들기 위한 절댓값 틱 계산 (마이너스 부호 숨김 처리)
    max_val = max(max(male_pop) if male_pop else 0, max(female_pop) if female_pop else 0)
    tick_step = 500 if max_val <= 2000 else (1000 if max_val <= 5000 else 2000)
    tickvals = list(range(-((max_val//tick_step)+1)*tick_step, ((max_val//tick_step)+1)*tick_step + 1, tick_step))
    ticktext = [f"{abs(v):,}" for v in tickvals]

    # 🩸 5. 공포스러운 분위기의 Plotly 피라미드 차트
    fig = go.Figure()

    # 남자 바 (검붉은 색, 왼쪽으로 뻗어나감)
    fig.add_trace(go.Bar(
        y=ages,
        x=male_pop_neg,
        name='남자',
        orientation='h',
        marker_color='#4A0000', # 어두운 붉은색
        hoverinfo='y+text',
        text=[f"남자 {val:,}명" for val in male_pop], # 마우스 오버 시 절댓값과 설명 표시
    ))

    # 여자 바 (선명한 핏빛, 오른쪽으로 뻗어나감)
    fig.add_trace(go.Bar(
        y=ages,
        x=female_pop,
        name='여자',
        orientation='h',
        marker_color='#8A0303', # 선명한 핏빛
        hoverinfo='y+text',
        text=[f"여자 {val:,}명" for val in female_pop],
    ))

    fig.update_layout(
        title=f"<b>{selected_dong}... 이곳에 존재하는 자들의 흔적</b>",
