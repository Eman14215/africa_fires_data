import os
from datetime import datetime, timedelta
import pandas as pd

MAP_KEY = os.environ["NASA_API_KEY"]
africa_coords = "-20,-35,55,38"

# تقسيم الـ 10 أيام على فترتين (كل فترة 5 أيام) لتجنب رفض سيرفر ناسا (Error 400)
today = datetime.utcnow().date()
five_days_ago = (today - timedelta(days=5)).strftime("%Y-%m-%d")

viirs_sensors = ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"]
all_data = []

for sensor in viirs_sensors:
    # الدفعة الأولى: آخر 5 أيام
    url1 = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{sensor}/{africa_coords}/5"
    # الدفعة الثانية: الـ 5 أيام اللي قبلهم
    url2 = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{sensor}/{africa_coords}/5/{five_days_ago}"
    
    for url in [url1, url2]:
        try:
            df = pd.read_csv(url)
            df = df[df['confidence'] != 'l']
            df = df.rename(columns={'bright_ti4': 'brightness', 'bright_ti5': 'bright_t31'})
            df['sensor'] = sensor
            all_data.append(df)
        except Exception as e:
            print(f"Skipped {url}: {e}")

# سحب قمر MODIS على دفعتين (10 أيام كاملة)
modis_urls = [
    f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/MODIS_NRT/{africa_coords}/5",
    f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/MODIS_NRT/{africa_coords}/5/{five_days_ago}"
]

for url in modis_urls:
    try:
        df_modis = pd.read_csv(url)
        df_modis = df_modis[df_modis['confidence'] >= 50]
        df_modis['sensor'] = 'MODIS_NRT'
        all_data.append(df_modis)
    except Exception as e:
        print(f"Skipped {url}: {e}")

# دمج الكل وحذف التكرار وحفظ الملف
final_df = pd.concat(all_data, ignore_index=True)
final_df.drop_duplicates(inplace=True)
final_df.to_csv("africa_fires_latest.csv", index=False)
print(f"Updated successfully! Total fires for last 10 days: {len(final_df)}")
