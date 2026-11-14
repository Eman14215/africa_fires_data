import os
from datetime import datetime, timedelta, timezone
import pandas as pd

MAP_KEY = os.environ["NASA_API_KEY"]
africa_coords = "-20,-35,55,38"

today = datetime.now(timezone.utc).date()
viirs_sensors = ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"]
all_data = []

# سحب الـ 10 أيام يوم بيوم لضمان عدم رفض السيرفر ودمجهم بالكامل
for day_offset in range(10):
    target_date = (today - timedelta(days=day_offset)).strftime("%Y-%m-%d")
    
    # 1. سحب أقمار VIIRS لليوم المحدد
    for sensor in viirs_sensors:
        url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{sensor}/{africa_coords}/1/{target_date}"
        try:
            df = pd.read_csv(url)
            if not df.empty:
                df = df[df['confidence'] != 'l']
                df = df.rename(columns={'bright_ti4': 'brightness', 'bright_ti5': 'bright_t31'})
                df['sensor'] = sensor
                all_data.append(df)
        except Exception as e:
            print(f"Skipped {sensor} on {target_date}: {e}")

    # 2. سحب قمر MODIS لليوم المحدد
    url_modis = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/MODIS_NRT/{africa_coords}/1/{target_date}"
    try:
        df_modis = pd.read_csv(url_modis)
        if not df_modis.empty:
            df_modis = df_modis[df_modis['confidence'] >= 50]
            df_modis['sensor'] = 'MODIS_NRT'
            all_data.append(df_modis)
    except Exception as e:
        print(f"Skipped MODIS on {target_date}: {e}")

# دمج الـ 10 أيام كلها في جدول واحد وحذف أي تكرار
final_df = pd.concat(all_data, ignore_index=True)
final_df.drop_duplicates(inplace=True)
final_df.to_csv("africa_fires_latest.csv", index=False)
print(f"Done! Total fires across 10 days: {len(final_df)}")
