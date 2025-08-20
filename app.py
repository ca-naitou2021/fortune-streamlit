import streamlit as st
import json
from datetime import datetime

# 紫微斗数ライブラリ
from pyziwei import ZiweiChart

st.title("占いアプリ（JSON出力版）")

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
    dt = datetime.combine(birth_date, birth_time)

    # ---- 紫微斗数計算 ----
    # pyziweiは生年月日・出生時間・性別で命盤計算
    chart = ZiweiChart(year=dt.year, month=dt.month, day=dt.day,
                       hour=dt.hour, gender=gender)
    chart.calculate()  # フル計算
    
    # JSON化
    chart_data = {
        "name": name,
        "birth": str(dt),
        "birth_place": birth_place,
        "gender": gender,
        "ziwei_chart": chart.to_dict()  # 十二宮・星曜・吉凶など
    }

    st.subheader("紫微斗数命盤データ（JSON形式）")
    st.json(chart_data)
