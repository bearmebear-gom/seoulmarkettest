import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Page Config
st.set_page_config(page_title="서울시 상권 분석 대시보드", layout="wide")

# Constants & Mapping
# 배포를 위해 절대 경로 대신 상대 경로를 사용합니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "team project", "서울시 상권분석서비스(추정매출-상권).csv")

KEYWORD_TO_DISTRICT = {
    '종로': '종로구', '혜화': '종로구', '창신': '종로구', '인사동': '종로구',
    '명동': '중구', '남대문': '중구', '북창동': '중구', '을지로': '중구',
    '이태원': '용산구', '한남': '용산구', '보광': '용산구', '용산': '용산구',
    '마장': '성동구', '성수': '성동구', '행당': '성동구',
    '건대': '광진구', '준양': '광진구', '화양': '광진구', '자양': '광진구',
    '장안': '동대문구', '청량리': '동대문구', '제기': '동대문구',
    '면목': '중랑구', '상봉': '중랑구', '중화': '중랑구',
    '돈암': '성북구', '안암': '성북구', '종암': '성북구',
    '수유': '강북구', '미아': '강북구', '번동': '강북구',
    '쌍문': '도봉구', '창동': '도봉구', '방학': '도봉구',
    '상계': '노원구', '중계': '노원구', '하계': '노원구',
    '연서': '은평구', '응암': '은평구', '불광': '은평구',
    '이대': '서대문구', '신촌': '서대문구', '연희': '서대문구',
    '홍대': '마포구', '합정': '마포구', '망원': '마포구', '공덕': '마포구',
    '목동': '양천구', '신정': '양천구', '신월': '양천구',
    '화곡': '강서구', '발산': '강서구', '마곡': '강서구',
    '구로': '구로구', '개봉': '구로구', '오류': '구로구', '신도림': '구로구',
    '가산': '금천구', '시흥': '금천구', '독산': '금천구',
    '영등포': '영등포구', '당산': '영등포구', '문래': '영등포구', '여의도': '영등포구',
    '노량진': '동작구', '상도': '동작구', '사당': '동작구', '흑석': '동작구',
    '신림': '관악구', '봉천': '관악구', '남현': '관악구',
    '강남역': '서초구', '교대': '서초구', '방배': '서초구', '양재': '서초구',
    '압구정': '강남구', '청담': '강남구', '삼성동': '강남구', '역삼': '강남구', '논현': '강남구', '신사': '강남구', '가로수길': '강남구',
    '잠실': '송파구', '가락': '송파구', '문정': '송파구', '석촌': '송파구',
    '천호': '강동구', '명일': '강동구', '암사': '강동구', '성내': '강동구'
}

@st.cache_data
def load_data():
    if not os.path.exists(FILE_PATH):
        st.error(f"파일을 찾을 수 없습니다: {FILE_PATH}")
        return pd.DataFrame()
    
    df = pd.read_csv(FILE_PATH, encoding='cp949')
    
    # Preprocessing
    def match_district(name):
        for kw, dist in KEYWORD_TO_DISTRICT.items():
            if kw in str(name): return dist
        return "기타/미분류"
    
    df['자치구'] = df['상권_코드_명'].apply(match_district)
    
    # Ensure numeric
    numeric_cols = df.columns[df.columns.str.contains('매출_금액|매출_건수')]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
    return df

# Main App
st.title("📊 서울시 상권 소비 주체 & 업종 분석 대시보드")

df = load_data()

if not df.empty:
    # Sidebar
    st.sidebar.header("🔍 분석 필터")
    
    districts = sorted([d for d in df['자치구'].unique() if d != "기타/미분류"])
    selected_dist = st.sidebar.selectbox("자치구 선택", districts, index=districts.index("강남구") if "강남구" in districts else 0)
    
    quarters = sorted(df['기준_년분기_코드'].unique(), reverse=True)
    options_q = ["전체"] + [str(q) for q in quarters]
    selected_q = st.sidebar.selectbox("분기 선택", options_q)
    
    # Filter Data
    if selected_q == "전체":
        sub_df = df[df['자치구'] == selected_dist]
    else:
        sub_df = df[(df['자치구'] == selected_dist) & (df['기준_년분기_코드'] == int(selected_q))]
    
    if sub_df.empty:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    else:
        # --- 1. Key Metrics ---
        st.subheader(f"📍 {selected_dist} 상권 요약 ({selected_q})")
        
        # Calculate Demographic Totals
        age_cols = [c for c in df.columns if '연령대' in c and '매출_금액' in c]
        age_totals = sub_df[age_cols].sum()
        main_age_group = age_totals.idxmax().split('_')[1] + "대"
        
        # Calculate Industry Max Mean
        industry_rank = sub_df.groupby('서비스_업종_코드_명')['당월_매출_금액'].mean().sort_values(ascending=False)
        top_industry = industry_rank.index[0]
        top_industry_val = industry_rank.values[0]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("총 매출액", f"₩{int(sub_df['당월_매출_금액'].sum()):,}")
        m2.metric("주 소비 연령대", main_age_group)
        m3.metric("최고 평균 매출 업종", top_industry)
        
        st.divider()
        
        # --- 2. Demographic Analysis ---
        c1, c2 = st.columns(2)
        
        with c1:
            st.write("👥 **연령대별 매출 분포**")
            age_display_data = pd.DataFrame({
                '연령대': [c.split('_')[1] + "대" for c in age_cols],
                '매출액': age_totals.values
            })
            fig_age = px.bar(age_display_data, x='연령대', y='매출액', color='연령대', 
                             text_auto=',.0f', title=f"{selected_dist} 연령대별 매출 현황")
            st.plotly_chart(fig_age, use_container_width=True)
            
        with c2:
            st.write("🚻 **성별 매출 비중**")
            gender_data = {
                '성별': ['남성', '여성'],
                '매출액': [sub_df['남성_매출_금액'].sum(), sub_df['여성_매출_금액'].sum()]
            }
            fig_gender = px.pie(gender_data, names='성별', values='매출액', hole=.4,
                                color_discrete_sequence=['skyblue', 'pink'], title=f"{selected_dist} 성별 매출 비중")
            st.plotly_chart(fig_gender, use_container_width=True)
            
        st.divider()
        
        # --- 3. Industry Analysis ---
        st.write(f"🏢 **{selected_dist} 업종별 평균 매출액 순위 (Top 10)**")
        
        top_10_df = industry_rank.head(10).reset_index()
        top_10_df.columns = ['업종명', '평균 매출액(원)']
        
        col_t1, col_t2 = st.columns([1, 1])
        
        with col_t1:
            st.dataframe(top_10_df.style.format({'평균 매출액(원)': '{:,.0f}'}), use_container_width=True)
            
        with col_t2:
            fig_ind = px.bar(top_10_df, x='평균 매출액(원)', y='업종명', orientation='h',
                             title=f"{selected_dist} 상위 업종 매출액 비교",
                             color='평균 매출액(원)', color_continuous_scale='Viridis')
            st.plotly_chart(fig_ind, use_container_width=True)

        # Insight Text
        st.info(f"""
        **💡 {selected_dist} 분석 인사이트:**
        - 이 지역의 가장 강력한 소비 권력은 **{main_age_group}**입니다.
        - **{top_industry}** 업종이 개별 상권당 평균 **{int(top_industry_val):,}원**의 매출을 기록하며 시장을 리드하고 있습니다.
        """)

st.sidebar.markdown("---")
st.sidebar.info("v1.0 - 서울시 상권분석 서비스 데이터 분석기")
