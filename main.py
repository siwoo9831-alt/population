
# 2026년 데이터만 필터링
df_2026 = df[df['연도'] == 2026].copy()

# 코드를 5자리 문자열로 변환 (시군구 코드 추출)
df_2026['sigungu_code'] = df_2026['코드'].astype(str).str[:5]

# '계_' 로 시작하는 열 찾기
all_age_cols = [col for col in df_2026.columns if col.startswith('계_')]

# 65세 이상 열 찾기 ('계_65세' ~ '계_100세 이상')
# 나이 숫자를 추출하여 65 이상인지 확인
senior_cols = []
for col in all_age_cols:
    age_str = col.replace('계_', '').replace('세 이상', '').replace('세', '')
    try:
        if int(age_str) >= 65:
            senior_cols.append(col)
    except ValueError:
        pass # 예외적인 컬럼명이 있다면 무시

# 시군구별로 인구 합산
# 전체 인구와 65세 이상 인구를 각각 시군구별로 먼저 합산
agg_dict = {col: 'sum' for col in all_age_cols}
df_sigungu = df_2026.groupby('sigungu_code')[all_age_cols].sum().reset_index()

# 시군구별 총 인구 및 고령 인구 계산
df_sigungu['total_pop'] = df_sigungu[all_age_cols].sum(axis=1)
df_sigungu['senior_pop'] = df_sigungu[senior_cols].sum(axis=1)

# 고령화율(%) 계산
df_sigungu['aging_rate'] = (df_sigungu['senior_pop'] / df_sigungu['total_pop']) * 100

# 2. GeoJSON 데이터 로드
geojson_url = "https://github.com/siwoo9831-alt/population/raw/main/sigungu_kr.geojson.txt"
response = requests.get(geojson_url)
geojson_data = response.json()

# GeoJSON의 feature에서 '코드' 속성을 확인하고 일치시키기 위해 데이터프레임에 이름 추가 (호버용)
code_to_name = {}
for feature in geojson_data['features']:
    props = feature['properties']
    code_to_name[str(props['코드'])] = props.get('시군구', '알 수 없음')
    
df_sigungu['sigungu_name'] = df_sigungu['sigungu_code'].map(code_to_name)

return df_sigungu, geojson_data


with st.spinner("데이터를 불러오고 처리하는 중입니다... (최초 로딩 시 시간이 걸릴 수 있습니다)"):
try:
df_sigungu, geojson_data = load_data()

    # Plotly Choropleth 맵 생성
    fig = px.choropleth(
        df_sigungu,
        geojson=geojson_data,
        locations='sigungu_code',
        featureidkey='properties.코드', # GeoJSON의 어떤 속성과 매칭할지
        color='aging_rate',
        color_continuous_scale='Reds', # 고령화율이 높을수록 진하게
        hover_name='sigungu_name',
        hover_data={'sigungu_code': False, 'aging_rate': ':.1f%'},
        labels={'aging_rate': '고령화율 (%)'}
    )

    fig.update_geos(
        fitbounds="locations", 
        visible=False # 배경 지도(타일), 해안선 등 모두 숨김
    )

    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        coloraxis_colorbar=dict(title="고령화율(%)")
    )

    st.plotly_chart(fig, use_container_width=True)
    
    st.info("지도에 마우스를 올리면 시군구 이름과 고령화율을 확인할 수 있습니다.")

except Exception as e:
    st.error(f"데이터를 불러오거나 처리하는 중 오류가 발생했습니다: {e}")
