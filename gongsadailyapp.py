import streamlit as st
import os
from PIL import Image
import pandas as pd
import uuid

st.set_page_config(page_title="공사일보 자동화 시제품", layout="wide")
st.title("📋 공사일보 자동화 시스템 (시제품)")

# 세션 초기화
if 'images' not in st.session_state:
    st.session_state.images = []
if 'data' not in st.session_state:
    st.session_state.data = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

# 파일 업로드
uploaded_files = st.file_uploader("📎 손글씨 공사일보 이미지 업로드 (여러 장 가능)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
if uploaded_files:
    st.session_state.images = uploaded_files
    st.session_state.data = [{} for _ in uploaded_files]
    st.session_state.current_index = 0

# 현재 페이지 표시
total = len(st.session_state.images)
if total > 0:
    idx = st.session_state.current_index
    col1, col2 = st.columns([1, 2])

    # 좌측: 이미지 표시
    with col1:
        st.image(st.session_state.images[idx], caption=f"Page {idx+1}/{total}", use_column_width=True)

    # 우측: 공사일보 정보 입력 폼
    with col2:
        st.subheader("📝 공사일보 정보 입력")
        date = st.text_input("날짜", st.session_state.data[idx].get("날짜", ""))
        공종 = st.text_input("공종", st.session_state.data[idx].get("공종", ""))
        세부공종 = st.text_input("세부공종", st.session_state.data[idx].get("세부공종", ""))
        인원수 = st.number_input("인원수", min_value=0, step=1, value=int(st.session_state.data[idx].get("인원수", 0)))
        작업내용 = st.text_area("작업내용", st.session_state.data[idx].get("작업내용", ""), height=150)

        # 저장 버튼
        if st.button("💾 저장", key=f"save_{idx}"):
            st.session_state.data[idx] = {
                "날짜": date,
                "공종": 공종,
                "세부공종": 세부공종,
                "인원수": 인원수,
                "작업내용": 작업내용
            }
            st.success("저장 완료")

    # 페이지 이동
    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅ 이전") and idx > 0:
            st.session_state.current_index -= 1
    with col_next:
        if st.button("다음 ➡") and idx < total - 1:
            st.session_state.current_index += 1

    # 전체 완료 시 결과 보기
    if all(st.session_state.data):
        st.markdown("---")
        st.subheader("📊 전체 공사일보 결과")
        df = pd.DataFrame(st.session_state.data)
        st.dataframe(df)

        st.download_button("📥 엑셀 다운로드", data=df.to_excel(index=False), file_name="공사일보_결과.xlsx")
