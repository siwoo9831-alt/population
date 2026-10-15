import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 기본 설정 (앱의 탭 제목과 레이아웃 너비 설정)
st.set_page_config(page_title="동네별 인구 피라미드", layout="wide")

# 앱 제목 
st.title("🏘️ 우리 동네 인구 피라미드")
st.markdown("최신 연도의 동네별 연령/성별 인구 구조를 따뜻한 톤의 피라미드 차트로 확인해보세요!")

# 데이터 불러오기 함수 (스트림릿 캐시를 사용하여 매번 다운로드하지 않도록 속도 향상)
@st.cache_data
def load_data():
    # GitHub의 zip 파일 원본(raw) 다운로드 링크
    url = "https://github.com/siwoo9831-alt/population/blob/main/population_ts_yearly_gender.zip?raw=true"
    
    # pandas로 zip 파일 안의 csv를 바로 읽어옵니다.
    # 한글 데이터의 경우 인코딩(utf-8 또는 cp949) 문제가 있을 수 있어 예외 처리를 해줍니다.
    try:
        df = pd.read_csv(url, compression='zip')
    except UnicodeDecodeError:
        df = pd.read_csv(url, compression='zip', encoding='cp949')
        
    return df

# 데이터 로딩 상태 표시
with st.spinner("데이터를 불러오는 중입니다... 잠시만 기다려주세요."):
    df = load_data()

# 1. 가장 최신 연도 찾기 및 데이터 필터링
latest_year = df['연도'].max()
df_latest = df[df['연도'] == latest_year]

st.subheader(f"📅 기준 연도: {latest_year}년")

# 2. 화면 상단에 드롭다운 3개를 나란히 배치하기 위해 컬럼 분할
col1, col2, col3 = st.columns(3)

# 2-1. 시도 선택
sido_list = df_latest['시도'].dropna().unique()
with col1:
    selected_sido = st.selectbox("1. 시도를 선택하세요", sido_list)

# 2-2. 시군구 선택 (선택한 시도에 맞춰 목록 필터링)
df_sigungu = df_latest[df_latest['시도'] == selected_sido]
sigungu_list = df_sigungu['시군구'].dropna().unique()
with col2:
    selected_sigungu = st.selectbox("2. 시군구를 선택하세요", sigungu_list)

# 2-3. 동 선택 (선택한 시군구에 맞춰 목록 필터링)
df_dong = df_sigungu[df_sigungu['시군구'] == selected_sigungu]
dong_list = df_dong['동'].dropna().unique()
with col3:
    selected_dong = st.selectbox("3. 동을 선택하세요", dong_list)

# 3. 최종 선택된 동네의 데이터 추출
final_data = df_dong[df_dong['동'] == selected_dong]

if not final_data.empty:
    # 연령대 라벨 리스트 생성 (0세 ~ 100세 이상)
    ages = [f"{i}세" for i in range(100)] + ["100세 이상"]
    
    # 남/여 열 이름 리스트 생성 (예: 남_0세, 여_0세)
    male_cols = [f"남_{age}" for age in ages]
    female_cols = [f"여_{age}" for age in ages]
    
    # 해당 동네의 인구 값 가져오기 (첫 번째 행 데이터 기준)
    # 남자는 왼쪽(음수)으로 그리기 위해 -1을 곱해줍니다.
    male_pop = final_data[male_cols].iloc[0].values * -1
    female_pop = final_data[female_cols].iloc[0].values
    
    # --- 4. Plotly를 이용한 인구 피라미드 그리기 ---
    fig = go.Figure()

    # 남자 바 차트 추가 (왼쪽 방향, 따뜻한 주황색 톤)
    fig.add_trace(go.Bar(
        y=ages,
        x=male_pop,
        name='남자',
        orientation='h',            # 가로 막대그래프 설정
        marker_color='#F2A65A',     # 따뜻한 주황/살구색
        hoverinfo='y+text',
        text=[f"{abs(val):,}명" for val in male_pop], # 마우스 오버 시에는 양수로 보이게 설정
    ))

    # 여자 바 차트 추가 (오른쪽 방향, 따뜻한 붉은색 톤)
    fig.add_trace(go.Bar(
        y=ages,
        x=female_pop,
        name='여자',
        orientation='h',            # 가로 막대그래프 설정
        marker_color='#D96C6C',     # 따뜻한 로즈/코랄 톤
        hoverinfo='y+text',
        text=[f"{val:,}명" for val in female_pop],
    ))

    # 차트 레이아웃 및 디자인 설정
    fig.update_layout(
        title=f"<b>{selected_sido} {selected_sigungu} {selected_dong} 인구 구조</b>",
        title_x=0.5,                # 제목을 가운데 정렬
        barmode='relative',         # 양수/음수를 기준으로 가운데서부터 양옆으로 뻗어나가는 형태
        yaxis=dict(
            title="나이",
            categoryorder='array',  # [핵심] Y축을 임의로 정렬/뒤집지 않고 지정한 배열 순서에 고정
            categoryarray=ages      # 0세가 맨 처음(아래), 100세 이상이 맨 끝(위)이 되도록 적용
        ),
        xaxis=dict(
            title="인구 수(명)",
            # 마이너스(-) 부호가 보이지 않게 눈금 레이블 수정 (음수를 절댓값으로 표시)
            tickmode='array',
            tickvals=[-max(abs(male_pop) if len(male_pop)>0 else [0]), 0, max(female_pop if len(female_pop)>0 else [0])],
            ticktext=[f"{max(abs(male_pop) if len(male_pop)>0 else [0]):,}", "0", f"{max(female_pop if len(female_pop)>0 else [0]):,}"]
        ),
        plot_bgcolor='rgba(250, 250, 250, 1)', # 배경색을 아주 옅은 웜그레이 톤으로 설정
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=80, b=50)
    )

    # 스트림릿에 완성된 차트 렌더링
    st.plotly_chart(fig, use_container_width=True)
    
else:
    # 데이터가 없을 경우 표시할 경고 메시지
    st.warning("선택하신 조건에 맞는 데이터가 없습니다.")
