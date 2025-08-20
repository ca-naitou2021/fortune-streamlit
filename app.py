import streamlit as st
import json
from datetime import datetime

st.title("占いアプリ（GPTなし試作版）")

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
    # --- ダミーの命盤データ（本来は計算処理を入れる） ---
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

    # --- 簡単な占断メッセージ（AIなし） ---
    st.subheader("占断メッセージ（サンプル）")
    st.write(f"{name}さんは『学びと探究』に強い傾向があります。"
             f"生年月日：{birth_date} を基盤に、人生の課題は「調和」と「直感の活用」です。")
