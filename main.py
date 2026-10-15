import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 스타일 정의
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

# 따뜻한 톤의 커스텀 스타일 적용 (CSS)
st.markdown("""
    <style>
    .main {
        background-color: #FAFAFA;
    }
    .stSelectbox label {
        color: #5A3E2B;
        font-weight: bold;
    }
    h1, h2, h3 {
        color: #4A3525;
        font-family: 'Malgun Gothic', sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터 불러오기 (캐싱 적용으로 속도 최적화)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # 압축된 CSV 파일 URL (pandas가 zip 내부 csv를 자동으로 연출)
    url = "https://raw.githubusercontent.com/lse1101/contents/main/population_ts_yearly_gender.zip"
    df = pd.read_csv(url)
    
    # 가장 최신 연도 데이터만 추출
    latest_year = df['연도'].max()
    df_latest = df[df['연도'] == latest_year].copy()
    
    return df_latest, latest_year

# 데이터 로딩 진행
with st.spinner('따뜻한 마음으로 동네 인구 데이터를 불러오는 중입니다...'):
    df, latest_year = load_data()

# -----------------------------------------------------------------------------
# 3. 메인 화면 헤더
# -----------------------------------------------------------------------------
st.title("🏡 우리 동네 인구 피라미드")
st.write(f"가장 최근 수집된 **{latest_year}년** 전국 읍·면·동 인구 데이터를 바탕으로 그려집니다.")
st.markdown("---")

# -----------------------------------------------------------------------------
# 4. 시도 -> 시군구 -> 동 3단계 드롭다운 선택 영역
# -----------------------------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    sido_list = sorted(df['시도'].dropna().unique())
    selected_sido = st.selectbox("1. 시·도 선택", sido_list)

with col2:
    # 선택된 시도에 해당하는 시군구 목록 추출
    sigungu_df = df[df['시도'] == selected_sido]
    sigungu_list = sorted(sigungu_df['시군구'].dropna().unique())
    selected_sigungu = st.selectbox("2. 시·군·구 선택", sigungu_list)

with col3:
    # 선택된 시군구에 해당하는 동 목록 추출
    dong_df = sigungu_df[sigungu_df['시군구'] == selected_sigungu]
    dong_list = sorted(dong_df['동'].dropna().unique())
    selected_dong = st.selectbox("3. 읍·면·동 선택", dong_list)

# -----------------------------------------------------------------------------
# 5. 선택된 지역 데이터 처리 및 Plotly 가로 막대 그래프 작성
# -----------------------------------------------------------------------------
# 선택된 행(row) 추출
target_row = dong_df[dong_df['동'] == selected_dong].iloc[0]

# 0세부터 100세 이상까지 범주 라벨 리스트 생성 (축 순서 고정용)
age_categories = [f"{i}세" for i in range(100)] + ["100세 이상"]

# 남/여 인구수 추출
male_pop = []
female_pop = []

for age in age_categories:
    m_col = f"남_{age}"
    f_col = f"여_{age}"
    
    # 남자는 왼쪽 배치를 위해 음수(-) 값으로 변환
    male_pop.append(-int(target_row[m_col]) if m_col in target_row else 0)
    female_pop.append(int(target_row[f_col]) if f_col in target_row else 0)

# Plotly 피라미드 그래프 그리기
fig = go.Figure()

# 남자 막대 그래프 (왼쪽, 포근한 파스텔 블루)
fig.add_trace(go.Bar(
    y=age_categories,
    x=male_pop,
    name='남자',
    orientation='h',
    marker=dict(color='#82B1FF'),
    hoverinfo='text',
    hovertext=[f"남자 {age}: {abs(val):,}명" for age, val in zip(age_categories, male_pop)]
))

# 여자 막대 그래프 (오른쪽, 따뜻한 코랄 핑크)
fig.add_trace(go.Bar(
    y=age_categories,
    x=female_pop,
    name='여자',
    orientation='h',
    marker=dict(color='#FF8A80'),
    hoverinfo='text',
    hovertext=[f"여자 {age}: {val:,}명" for age, val in zip(age_categories, female_pop)]
))

# 그래프 레이아웃 및 축 세부 설정
fig.update_layout(
    title=dict(
        text=f"<b>[{selected_sido} {selected_sigungu} {selected_dong}]</b> 인구 피라미드",
        font=dict(size=20, color='#4A3525'),
        x=0.5,
        xanchor='center'
    ),
    barmode='relative',
    bargap=0.1,
    xaxis=dict(
        title="인구수 (명)",
        titlefont=dict(color='#5A3E2B'),
        # x축 눈금에 절대값 표시 (음수 기호 제거)
        tickvals=list(range(-max(abs(min(male_pop)), max(female_pop)), 
                           max(abs(min(male_pop)), max(female_pop)) + 1, 
                           max(1, max(abs(min(male_pop)), max(female_pop)) // 5))),
        ticktext=[f"{abs(x):,}" for x in range(-max(abs(min(male_pop)), max(female_pop)), 
                                             max(abs(min(male_pop)), max(female_pop)) + 1, 
                                             max(1, max(abs(min(male_pop)), max(female_pop)) // 5))],
        gridcolor='#E0E0E0'
    ),
    yaxis=dict(
        title="나이",
        titlefont=dict(color='#5A3E2B'),
        # 세로축 순서 고정: 0세가 맨 아래, 100세 이상이 맨 위로 정렬되도록 지정
        type='category',
        categoryorder='array',
        categoryarray=age_categories,
        dtick=5 # 라벨이 너무 촘촘하지 않게 5세 단위 표시
    ),
    plot_bgcolor='#FFFFFF',
    paper_bgcolor='#FAFAFA',
    legend=dict(
        x=0.85,
        y=1.05,
        orientation='h'
    ),
    height=800
)

# -----------------------------------------------------------------------------
# 6. 결과 출력
# -----------------------------------------------------------------------------
st.plotly_chart(fig, use_container_width=True)

# 하단 요약 정보 안내
total_m = sum(abs(x) for x in male_pop)
total_f = sum(female_pop)
st.info(f"💡 **{selected_dong}**의 총 인구는 **{total_m + total_f:,}명**입니다. (남자: {total_m:,}명 / 여자: {total_f:,}명)")# board
