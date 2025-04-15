
import streamlit as st
import easyocr
from PIL import Image
import pandas as pd
import uuid
import tempfile

st.set_page_config(page_title="공사일보 자동화 (OCR 통합)", layout="wide")
st.title("📋 공사일보 자동화 시스템 - OCR 통합 버전")

if 'images' not in st.session_state:
    st.session_state.images = []
if 'data' not in st.session_state:
    st.session_state.data = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

uploaded_files = st.file_uploader("📎 손글씨 공사일보 이미지 업로드", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
if uploaded_files:
    st.session_state.images = uploaded_files
    st.session_state.data = [{} for _ in uploaded_files]
    st.session_state.current_index = 0

reader = easyocr.Reader(['ko', 'en'], gpu=False)

def ocr_extract_text(image_file):
    image = Image.open(image_file)
    result = reader.readtext(image, detail=0)
    return "\n".join(result)

def simple_parse_ocr_text(text):
    lines = text.split("\n")
    parsed = {"날짜": "", "공종": "", "세부공종": "", "인원수": 0, "작업내용": ""}
    for line in lines:
        if "공사일보" in line and "-" in line:
            parsed["날짜"] = line.split(" ")[0].strip()
        elif "공사" in line and "(" in line:
            parts = line.split("(")
            parsed["공종"] = parts[0].replace("●", "").strip()
            try:
                parsed["인원수"] = int(parts[1].replace(")", "").strip())
            except:
                parsed["인원수"] = 0
        elif "[" in line and "]" in line:
            parsed["세부공종"] = line.replace("[", "").split("]")[0].strip()
        elif "-" in line:
            parsed["작업내용"] += line.replace("-", "").strip() + " / "
    parsed["작업내용"] = parsed["작업내용"].rstrip(" / ")
    return parsed

total = len(st.session_state.images)
if total > 0:
    idx = st.session_state.current_index
    col1, col2 = st.columns([1, 2])

    with col1:
        st.image(st.session_state.images[idx], caption=f"Page {idx+1}/{total}", use_column_width=True)

    with col2:
        st.subheader("🧠 OCR 추출 또는 수동입력")

        if st.button("🔍 OCR 자동 추출"):
            raw_text = ocr_extract_text(st.session_state.images[idx])
            parsed = simple_parse_ocr_text(raw_text)
            st.session_state.data[idx] = parsed
            st.success("OCR 분석 완료")

        entry = st.session_state.data[idx]
        date = st.text_input("날짜", entry.get("날짜", ""))
        공종 = st.text_input("공종", entry.get("공종", ""))
        세부공종 = st.text_input("세부공종", entry.get("세부공종", ""))
        인원수 = st.number_input("인원수", min_value=0, step=1, value=int(entry.get("인원수", 0)))
        작업내용 = st.text_area("작업내용", entry.get("작업내용", ""), height=150)

        if st.button("💾 저장", key=f"save_{idx}"):
            st.session_state.data[idx] = {
                "날짜": date,
                "공종": 공종,
                "세부공종": 세부공종,
                "인원수": 인원수,
                "작업내용": 작업내용
            }
            st.success("저장 완료")

    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅ 이전") and idx > 0:
            st.session_state.current_index -= 1
    with col_next:
        if st.button("다음 ➡") and idx < total - 1:
            st.session_state.current_index += 1

    if all(st.session_state.data):
        st.markdown("---")
        st.subheader("📊 전체 공사일보 결과")
        df = pd.DataFrame(st.session_state.data)
        st.dataframe(df)
        st.download_button("📥 엑셀 다운로드", data=df.to_excel(index=False), file_name="공사일보_OCR결과.xlsx")
