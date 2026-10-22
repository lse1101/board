import json
import requests
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="전국 고령화 단계구분도 (2026년)",
    layout="wide"
)

st.title("🗺️ 2026년 전국 시군구별 고령화율 단계구분도")
st.caption("2026년 6월 기준 읍·면·동 인구 데이터를 시군구 단위(5자리 코드)로 집계한 지도입니다.")

@st.cache_data
def load_data():
    # 1. GeoJSON 경계 데이터 로드 (requests)
    geojson_url = "https://raw.githubusercontent.com/first2022-cyber/contents//main/sigungu_kr.geojson"
    res = requests.get(geojson_url)
    res.raise_for_status()
    geojson_data = res.json()

    # GeoJSON property 내 '코드' 속성 5자리 문자열 보장
    for feature in geojson_data['features']:
        feature['properties']['코드'] = str(feature['properties']['코드']).zfill(5)

    # 2. 인구 CSV 데이터 로드 (압축 zip)
    csv_url = "https://raw.githubusercontent.com/lse1101/contents//main/population_ts_yearly_gender.zip"
    df = pd.read_csv(csv_url)

    # 3. 2026년 데이터만 추출
    df_2026 = df[df['연도'].astype(str) == '2026'].copy()

    # 4. 시군구 코드 생성 (동 '코드' 열의 앞 5자리 추출 및 5자리 문자열 처리)
    df_2026['sigungu_code'] = df_2026['코드'].astype(str).str.zfill(5).str[:5]

    # 5. 전체 인구 열 ('계_'로 시작) 및 65세 이상 인구 열 추출
    total_pop_cols = [c for c in df_2026.columns if c.startswith('계_')]

    # '계_65세' ~ '계_100세 이상' 구분
    def is_65_or_over(col):
        val = col.replace('계_', '').replace('세 이상', '').replace('세', '')
        return val.isdigit() and int(val) >= 65

    elderly_pop_cols = [c for c in total_pop_cols if is_65_or_over(c)]

    # 6. 전체 인구 / 고령 인구 행별 계산
    df_2026['전체인구'] = df_2026[total_pop_cols].sum(axis=1)
    df_2026['고령인구'] = df_2026[elderly_pop_cols].sum(axis=1)

    # 7. 시군구(5자리 코드) 단위 그룹화
    sigungu_df = df_2026.groupby('sigungu_code', as_index=False)[['전체인구', '고령인구']].sum()

    # 8. 고령화율(%) 계산
    sigungu_df['고령화율'] = (sigungu_df['고령인구'] / sigungu_df['전체인구']) * 100
    sigungu_df['고령화율'] = sigungu_df['고령화율'].round(2)

    return geojson_data, sigungu_df

with st.spinner("데이터를 로드하는 중입니다..."):
    geojson_data, df_sigungu = load_data()

# GeoJSON 코드로 시군구 이름 매핑 사전 생성
code_to_name = {
    f['properties']['코드']: f"{f['properties'].get('시도', '')} {f['properties'].get('시군구', '')}".strip()
    for f in geojson_data['features']
}

# DataFrame에 시군구명 매핑
df_sigungu['시군구명'] = df_sigungu['sigungu_code'].map(code_to_name).fillna(df_sigungu['sigungu_code'])

# Plotly Choropleth 생성
fig = px.choropleth(
    df_sigungu,
    geojson=geojson_data,
    locations='sigungu_code',
    featureidkey='properties.코드',
    color='고령화율',
    color_continuous_scale='Reds',
    hover_name='시군구명',
    hover_data={
        'sigungu_code': False,
        '시군구명': False,
        '고령화율': ':.2f%'
    }
)

# 호버 툴팁 포맷 설정 (시군구 이름 및 고령화율만 표시)
fig.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>고령화율: %{z:.2f}%<extra></extra>"
)

# 배경 타일 없이 경계선만 설정
fig.update_geos(
    fitbounds="locations",
    visible=False
)

fig.update_layout(
    margin={"r": 0, "t": 20, "l": 0, "b": 0},
    height=750,
    coloraxis_colorbar=dict(
        title="고령화율 (%)",
        thickness=15,
        len=0.6
    )
)

st.plotly_chart(fig, use_container_width=True)

with st.expander("📊 시군구별 상세 데이터 보기"):
    st.dataframe(
        df_sigungu[['sigungu_code', '시군구명', '전체인구', '고령인구', '고령화율']]
        .sort_values(by='고령화율', ascending=False),
        use_container_width=True
    )
