import streamlit as st
import json
from datetime import datetime
from flatlib.chart import Chart
from flatlib.geopos import GeoPos
from flatlib.datetime import Datetime as fdt
from flatlib import aspects
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

st.title("西洋占星術ホロスコープ計算アプリ")

# ---- 入力フォーム ----
with st.form("input_form"):
    name = st.text_input("名前")
    birth_date = st.date_input("生年月日", datetime(1990, 1, 1))
    birth_time_str = st.text_input("出生時間", "00:00")
    birth_place_name = st.text_input("出生地（例: 東京, 大阪市天王寺区など）", "東京")
    submitted = st.form_submit_button("ホロスコープを計算する")

if submitted:
    # ---- 住所 → 緯度経度 ----
    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(birth_place_name, language="ja")

    # 入力時間をパース
    birth_time = datetime.strptime(birth_time_str, "%H:%M").time()
    dt = datetime.combine(birth_date, birth_time)

    # flatlib用日時（ここではタイムゾーン+00:00に仮置き）
    date_str = dt.strftime("%Y/%m/%d")
    time_str = dt.strftime("%H:%M")
    fdate = fdt(date_str, time_str, "+00:00")
    pos = GeoPos(birth_place_lat, birth_place_lon)

    chart = Chart(fdate, pos)

    # ---- 惑星＋感受点 ----
    objects = [
        "Sun", "Moon", "Mercury", "Venus", "Mars",
        "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
        "ASC", "MC", "IC", "DSC"
    ]

    planets_data = {}
    for obj in objects:
        item = chart.get(obj)
        planets_data[obj] = {
            "sign": item.sign,
            "lon": item.lon,
            "lat": item.lat,
            "house": item.house,
        }

    # ---- ハウス ----
    houses_data = {}
    for i in range(1, 13):
        houses_data[str(i)] = {
            "sign": chart.houses[i].sign,
            "lon": chart.houses[i].lon
        }

    # ---- アスペクト ----
    aspects_data = []
    for asp in aspects.MAJOR_ASPECTS:
        asp_list = chart.getAspectList(asp, orbs=8)
        for a in asp_list:
            aspects_data.append({
                "p1": a.p1,
                "p2": a.p2,
                "aspect": a.type,
                "orb": a.orb
            })

    # ---- JSON出力 ----
    chart_data = {
        "name": name,
        "birth": str(local_dt),
        "timezone": tz_name,
        "utc_birth": str(utc_dt),
        "location": {
            "name": birth_place_name,
            "lat": birth_place_lat,
            "lon": birth_place_lon
        },
        "planets": planets_data,
        "houses": houses_data,
        "aspects": aspects_data
    }

    st.subheader("ホロスコープデータ（JSON形式）")
    st.json(chart_data)

    json_str = json.dumps(chart_data, ensure_ascii=False, indent=2)
    st.download_button(
        label="ホロスコープJSONをダウンロード",
        data=json_str,
        file_name=f"{name}_horoscope.json",
        mime="application/json"
    )
