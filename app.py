import streamlit as st
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import aspects, const
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz
import json
from datetime import datetime

st.title("西洋占星術ホロスコープ計算アプリ")

name = st.text_input("名前")
birth_date = st.date_input("生年月日")  # → datetime.date 型
birth_time = st.text_input("出生時間 (HH:MM)")  # → 手入力
birth_place = st.text_input("出生地 (例: 東京, 大阪市天王寺区など)")

if st.button("ホロスコープを計算する"):
    try:
        # --- 位置情報を取得 ---
        geolocator = Nominatim(user_agent="astro_app")
        location = geolocator.geocode(birth_place)
        if not location:
            st.error("出生地が見つかりません。別の表記を試してください。")
        else:
            lat, lon = location.latitude, location.longitude

            # --- タイムゾーンを算出 ---
            tf = TimezoneFinder()
            tz_name = tf.timezone_at(lat=lat, lng=lon)
            if tz_name is None:
                st.error("タイムゾーンが見つかりません。")
            else:
                tz = pytz.timezone(tz_name)

                # --- Python datetime用 ---
                # birth_time をパースして datetime.time に変換
                try:
                    time_obj = datetime.strptime(birth_time, "%H:%M").time()
                except ValueError:
                    st.error("出生時間は HH:MM 形式で入力してください。")
                    st.stop()

                naive_dt = datetime.combine(birth_date, time_obj)
                local_dt = tz.localize(naive_dt)

                # --- flatlib Datetime用 ---
                date_str = birth_date.strftime("%Y/%m/%d")  # flatlibはスラッシュ形式
                time_str = time_obj.strftime("%H:%M")
                offset = local_dt.strftime("%z")
                offset = offset[:3] + ":" + offset[3:]
                dt = Datetime(date_str, time_str, offset)

                # --- チャート作成 ---
                pos = GeoPos(lat, lon)
                chart = Chart(dt, pos, hsys='Placidus')

                # --- 惑星情報 ---
                planets_data = {}
                for p in const.LIST_OBJECTS:
                    obj = chart.get(p)
                    planets_data[p] = {
                        "sign": obj.sign,
                        "house": obj.house,
                        "lon": round(obj.lon, 2),
                    }

                # --- アスペクト情報 ---
                objs = [chart.get(obj) for obj in const.LIST_OBJECTS]
                asp_list = aspects.getAspects(objs, aspects.MAJOR_ASPECTS, 8)
                aspect_data = []
                for asp in asp_list:
                    aspect_data.append({
                        "p1": asp.obj1,
                        "p2": asp.obj2,
                        "type": asp.type,
                        "orb": round(asp.orb, 2)
                    })

                # --- JSON 出力 ---
                chart_json = {
                    "metadata": {
                        "name": name,
                        "datetime_local": local_dt.isoformat(),
                        "datetime_utc": local_dt.astimezone(pytz.utc).isoformat(),
                        "timezone": tz_name,
                        "location": {
                            "place": birth_place,
                            "lat": lat,
                            "lon": lon
                        },
                        "house_system": "Placidus",
                        "zodiac": "tropical"
                    },
                    "planets": planets_data,
                    "aspects": aspect_data
                }

                st.subheader("ホロスコープJSON")
                st.json(chart_json)

                json_str = json.dumps(chart_json, ensure_ascii=False, indent=2)
                st.download_button("JSONをダウンロード", json_str, file_name=f"{name}_chart.json")

    except Exception as e:
        st.error(f"エラー: {e}")
