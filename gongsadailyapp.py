import streamlit as st
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import pandas as pd
import re
import tempfile
import os

st.title("📋 공사일보 자동화 시스템")

# 1. 파일 업로드
uploaded_file = st.file_uploader("PDF 파일 업로드 (스캔된 공사일보)", type="pdf")

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        pdf_path = tmp_file.name

    # 2. PDF → 이미지 변환
    images = convert_from_path(pdf_path, dpi=300)

    # 3. OCR 실행
    full_text = ""
    for img in images:
        text = pytesseract.image_to_string(img, lang="kor+eng")
        full_text += text + "\n"

    st.text_area("🔍 OCR 결과 (수정 가능)", value=full_text, height=400, key="ocr_text")

    # 4. 데이터 파싱 함수
    def parse_text(text):
        lines = text.splitlines()
        date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")
        공사일보_date = ""
        공사일보_rows = []
        장비정보 = []
        총인원 = 0
        current_공종, current_세부공종, current_인원 = "", "", 0
        작업내용_buffer = []

        for line in lines:
            line = line.strip()
            if date_pattern.search(line):
                공사일보_date = date_pattern.search(line).group()
            elif line.startswith("●"):
                if 작업내용_buffer:
                    공사일보_rows.append([공사일보_date, current_공종, current_세부공종 or "-", current_인원, " / ".join(작업내용_buffer)])
                    작업내용_buffer = []
                match = re.match(r"●\s*(.*?)\s*\((\d+)\)", line)
                if match:
                    current_공종 = match.group(1).strip()
                    current_인원 = int(match.group(2))
                    current_세부공종 = ""
                    총인원 += current_인원
            elif line.startswith("[") and "]" in line:
                if 작업내용_buffer:
                    공사일보_rows.append([공사일보_date, current_공종, current_세부공종 or "-", current_인원, " / ".join(작업내용_buffer)])
                    작업내용_buffer = []
                match = re.match(r"\[(.*?)\]\s*\((\d+)\)", line)
                if match:
                    current_세부공종 = match.group(1).strip()
                    current_인원 = int(match.group(2))
            elif line.startswith("-"):
                작업내용_buffer.append(line[1:].strip())
            elif "장비" in line:
                장비정보.append(line)
            elif "총출력" in line:
                총출력_match = re.search(r"총출력\s*[:：]\s*(\d+)", line)
                if 총출력_match:
                    총인원 = int(총출력_match.group(1))

        if 작업내용_buffer:
            공사일보_rows.append([공사일보_date, current_공종, current_세부공종 or "-", current_인원, " / ".join(작업내용_buffer)])

        df = pd.DataFrame(공사일보_rows, columns=["날짜", "공종", "세부공종", "인원수", "작업내용"])
        return df, 장비정보, 총인원

    # 5. 결과 출력
    if st.button("✅ 공사일보 표 생성"):
        df, 장비정보, 총인원 = parse_text(st.session_state.ocr_text)
        st.success(f"총 인원: {총인원}명")
        st.dataframe(df)

        if 장비정보:
            st.markdown("### 🚜 장비 정보")
            for line in 장비정보:
                st.write(line)

        st.download_button(
            label="📥 엑셀 다운로드",
            data=df.to_excel(index=False),
            file_name="공사일보_자동화.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # 6. ChatGPT 요약용 텍스트 제공
        chat_prompt = f"""
다음은 건설현장의 공사일보 요약입니다. 아래 표 내용을 참고하여 공사 진행 현황을 요약해줘.
- 날짜: {df['날짜'].iloc[0] if not df.empty else 'N/A'}
- 총 공종 수: {df['공종'].nunique()}
- 총 인원: {총인원}명
- 주요 작업내용 예시:
{df[['공종', '세부공종', '작업내용']].head(5).to_string(index=False)}
        """
        st.markdown("### 🤖 ChatGPT 요약용 프롬프트")
        st.code(chat_prompt, language="markdown")
