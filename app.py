import streamlit as st
import json
from datetime import datetime

st.title("多占術総合占断アプリ（試作）")

# ---- 入力フォーム ----
with st.form("input_form"):
    name = st.text_input("名前")
    birth_date = st.date_input("生年月日", datetime(1990,1,1))
    birth_time = st.time_input("出生時間", datetime.now().time())
    birth_place = st.text_input("出生地（都市名など）", "Tokyo")
    gender = st.selectbox("性別", ["male", "female"])
    school = st.selectbox("流派", ["north", "south"])
    submitted = st.form_submit_button("占断する")

if submitted:
    # 仮の命盤データ（本当はここでライブラリを使って計算する）
    result = {
        "name": name,
        "birth": str(birth_date) + " " + str(birth_time),
        "place": birth_place,
        "gender": gender,
        "school": school,
        "chart": {
            "ziwei": {"命宮": "天同", "身宮": "太陰"},
            "astrology": {"Sun": "26° Sagittarius", "Moon": "12° Leo"},
            "numerology": {"life_path": 7}
        }
    }

    st.subheader("命盤データ（JSON形式）")
    st.json(result)

    # ---- GPT APIに投げる ----
    import openai
    openai.api_key = st.secrets["OPENAI_API_KEY"]

    prompt = f"以下の占術データを総合して、2000字程度で詳細に占断してください：\n\n{json.dumps(result, ensure_ascii=False, indent=2)}"
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    st.subheader("GPTによる総合占断")
    st.write(response["choices"][0]["message"]["content"])
