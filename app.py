import streamlit as st
import json
from datetime import datetime
from flatlib import const
from flatlib.chart import Chart
from flatlib.geopos import GeoPos
from flatlib.datetime import Datetime as fdt
from flatlib.ephem import ephem
from flatlib import aspects
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import traceback

st.title("西洋占星術ホロスコープ計算アプリ")

# ---- 入力フォーム ----
with st.form("input_form"):
    name = st.text_input("名前")
    birth_date = st.date_input("生年月日", datetime(1990, 1, 1))
    birth_time_str = st.text_input("出生時間", "00:00")
    birth_place_name = st.text_input("出生地（例: 東京, 大阪市天王寺区など）", "東京")
    submitted = st.form_submit_button("ホロスコープを計算する")

if submitted:
    try:
        # ---- 住所 → 緯度経度・タイムゾーン ----
        geolocator = Nominatim(user_agent="astro_app")
        location = geolocator.geocode(birth_place_name, language="ja")
        
        if location is None:
            st.error("出生地が見つかりませんでした。より正確な地名を入力してください。")
            st.stop()
            
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=location.longitude, lat=location.latitude)
        
        if tz_name is None:
            st.error("出生地のタイムゾーンを特定できませんでした。")
            st.stop()

        local_tz = pytz.timezone(tz_name)
        
        # 入力時間をパース
        birth_time = datetime.strptime(birth_time_str, "%H:%M").time()
        dt = datetime.combine(birth_date, birth_time)
        
        # タイムゾーンを適用
        localized_dt = local_tz.localize(dt)
        # UTCに変換
        utc_dt = localized_dt.astimezone(pytz.utc)

        # flatlib用日時
        date_str = utc_dt.strftime("%Y/%m/%d")
        time_str = utc_dt.strftime("%H:%M")
        
        # タイムゾーンオフセットを取得し、flatlib形式で設定
        tz_offset_seconds = local_tz.utcoffset(dt).total_seconds()
        tz_offset_hours = int(tz_offset_seconds / 3600)
        tz_offset_sign = "+" if tz_offset_hours >= 0 else ""
        tz_str = f"{tz_offset_sign}{tz_offset_hours:02d}:00"
        
        fdate = fdt(date_str, time_str, tz_str)
        pos = GeoPos(location.latitude, location.longitude)

        print("fdate:", fdate)
        print("pos:", pos)

        chart = Chart(fdate, pos)

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
        IDs = [const.URANUS, const.NEPTUNE, const.PLUTO]
        chart_2 = Chart(fdate, pos, IDs=IDs)
        
        # 修正: chart.housesとchart_2.housesをリストに変換
        chart_houses = list(chart.houses)
        chart_2_houses = list(chart_2.houses)
        
        for body in chart_2.objects:
            # 手動でハウスを特定
            house_id = 1
            for i in range(12):
                house_start_lon = chart_2_houses[i].lon
                next_house_start_lon = chart_2_houses[(i + 1) % 12].lon
                
                # 惑星の黄経がハウスの開始点の間にあるかチェック
                if i < 11:
                    if house_start_lon <= body.lon < next_house_start_lon:
                        house_id = i + 1
                        break
                else:
                    if house_start_lon <= body.lon or body.lon < next_house_start_lon:
                        house_id = i + 1
                        break

            planets[body.id] = {
                "sign": body.sign,
                "lon": body.lon,
                "lat": body.lat,
                "house": house_id
            }
        
        # DESC = 第7ハウス始まり
        desc_lon = chart_houses[6].lon
        planets["DESC"] = {
            "lon": desc_lon,
            "sign": get_sign(desc_lon),
            "lat": None,
            "house": 7
        }
        
        # IC = 第4ハウス始まり
        ic_lon = chart_houses[3].lon
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
        for i, cusp in enumerate(chart_houses):
            houses[f"House {i+1}"] = {
                "lon": cusp.lon,
                "sign": cusp.sign,
            }

        # ------------------------
        # アスペクト
        # ------------------------
        aspect_list = []
        all_objects = chart.objects + chart_2.objects
        asp = aspects.getAspects(all_objects, aspects.MAJOR_ASPECTS)
        for a in asp:
            aspect_list.append({
                "p1": a.obj1.id,
                "p2": a.obj2.id,
                "type": a.type,
                "orb": a.orb
            })

        # ------------------------
        # JSON 出力
        # ------------------------
        result = {
            "birth_data": {
                "name": name,
                "date": str(birth_date),
                "time": birth_time_str,
                "place": birth_place_name,
                "timezone": tz_name,
            },
            "planets_and_points": planets,
            "houses": houses,
            "aspects": aspect_list
        }

        st.subheader("計算結果 (JSON)")
        st.json(result)
        
        json_str = json.dumps(result, ensure_ascii=False, indent=2)
        st.download_button(
            label="ホロスコープJSONをダウンロード",
            data=json_str,
            file_name=f"{name}_horoscope.json",
            mime="application/json"
        )
        
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        st.error(f"詳細: {traceback.format_exc()}")
