import streamlit as st
import json
from datetime import datetime
from flatlib import const, ephem
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
    pos = GeoPos(location.latitude, location.longitude)

    # デバッグ内容出力
    print("fdate:", fdate)
    print("pos:", pos)

    chart = Chart(fdate, pos)

    # 黄経からサイン名を返す関数
    def get_sign(lon):
        signs = [
            const.ARIES, const.TAURUS, const.GEMINI, const.CANCER, const.LEO, const.VIRGO,
            const.LIBRA, const.SCORPIO, const.SAGITTARIUS, const.CAPRICORN, const.AQUARIUS, const.PISCES
        ]
        idx = int(lon // 30) % 12
        return signs[idx]
    
    # ---- 惑星（SUN〜SATURN, ASC, MC） ----
    objects = [
        const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
        const.JUPITER, const.SATURN,
        const.ASC, const.MC
    ]
    
    planets = {}
    for obj in objects:
        body = chart.get(obj)
        data = {
            "sign": body.sign,
            "lon": body.lon,
            "lat": body.lat,
        }
        if hasattr(body, "house"):
            data["house"] = body.house
        planets[obj] = data
    
    # ---- 外惑星（Uranus, Neptune, Pluto） ----
    for name in ["URANUS", "NEPTUNE", "PLUTO"]:
        body = ephem.getObject(name, date, pos)
        planets[name] = {
            "sign": body.sign,
            "lon": body.lon,
            "lat": body.lat,
            "house": body.house
        }
    
    # DESC = 第7ハウス始まり
    desc_lon = chart.houses[6]
    planets["DESC"] = {
        "lon": desc_lon,
        "sign": get_sign(desc_lon),
        "lat": None,
        "house": 7
    }
    
    # IC = 第4ハウス始まり
    ic_lon = chart.houses[3]
    planets["IC"] = {
        "lon": ic_lon,
        "sign": get_sign(ic_lon),
        "lat": None,
        "house": 4
    }
    
    # ASC と MC にも house を明示
    planets["ASC"]["house"] = 1
    planets["MC"]["house"] = 10

    # ------------------------
    # ハウス
    # ------------------------
    houses = {}
    for i, cusp in enumerate(chart.houses):
        houses[f"House {i+1}"] = cusp

    # ------------------------
    # アスペクト
    # ------------------------
    aspect_list = []
    asp = aspects.getAspects(chart.objects, aspects.MAJOR_ASPECTS)
    for a in asp:
        aspect_list.append({
            "p1": a.obj1,
            "p2": a.obj2,
            "type": a.type,
            "orb": a.orb
        })

    # ------------------------
    # JSON 出力
    # ------------------------
    result = {
        "birth_data": {
            "date": fdate,
            "time": ftime,
            "place": birth_place,
            "timezone": tz_str,
        },
        "planets_and_points": planets,
        "houses": houses,
        "aspects": aspect_list
    }

    st.subheader("計算結果 (JSON)")
    st.json(result)
    
    json_str = json.dumps(chart_data, ensure_ascii=False, indent=2)
    st.download_button(
        label="ホロスコープJSONをダウンロード",
        data=json_str,
        file_name=f"{name}_horoscope.json",
        mime="application/json"
    )
