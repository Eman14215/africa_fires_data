import os
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd

MAP_KEY = os.environ["NASA_API_KEY"]
africa_coords = "-20,-35,55,38"

today = datetime.now(timezone.utc).date()
viirs_sensors = ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"]
all_data = []

for day_offset in range(10):
    target_date = (today - timedelta(days=day_offset)).strftime("%Y-%m-%d")
    
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

    url_modis = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/MODIS_NRT/{africa_coords}/1/{target_date}"
    try:
        df_modis = pd.read_csv(url_modis)
        if not df_modis.empty:
            df_modis = df_modis[df_modis['confidence'] >= 50]
            df_modis['sensor'] = 'MODIS_NRT'
            all_data.append(df_modis)
    except Exception as e:
        print(f"Skipped MODIS on {target_date}: {e}")

# 1. حفظ الملف الخام الموحد لـ Power BI عشان ما يتأثرش
final_df = pd.concat(all_data, ignore_index=True)
final_df.drop_duplicates(inplace=True)
final_df.to_csv("africa_fires_latest.csv", index=False)

# 2. عمل نسخة Cleaned بالكامل وحفظها في ملف منفصل على GitHub
clean_df = final_df.copy()
clean_df = clean_df[
    (clean_df['latitude'].between(-35, 38)) &
    (clean_df['longitude'].between(-20, 55)) &
    (clean_df['brightness'] > 0) &
    (clean_df['frp'] >= 0)
]

# توحيد الثقة (Confidence_Level)
def unify_conf(val):
    try:
        return "High" if float(val) >= 80 else "Nominal"
    except ValueError:
        return "High" if str(val).lower() == 'h' else "Nominal"

clean_df['Confidence_Level'] = clean_df['confidence'].apply(unify_conf)

# تنسيق الوقت واستخراج الساعة
padded_time = clean_df['acq_time'].astype(str).str.strip().str.zfill(4)
clean_df['Fire_Time'] = padded_time.str[:2] + ":" + padded_time.str[2:]
clean_df['Fire_Hour'] = padded_time.str[:2].astype(int)

# تحسين أسماء الليل/النهار والأقمار
clean_df['daynight'] = clean_df['daynight'].replace({'D': 'Day', 'N': 'Night'})
clean_df['satellite'] = clean_df['satellite'].replace({'N': 'Suomi NPP', 'N20': 'NOAA-20', 'N21': 'NOAA-21'})

# إضافة الأعمدة التحليلية (الحرارة بالمئوي، شدة الحريق، والإقليم)
clean_df['Temp_Celsius'] = (clean_df['brightness'] - 273.15).round(1)
clean_df['Thermal_Anomaly'] = (clean_df['brightness'] - clean_df['bright_t31']).round(2)

clean_df['Fire_Severity'] = np.select(
    [clean_df['frp'] < 10, clean_df['frp'] < 50, clean_df['frp'] < 100],
    ["Low (< 10 MW)", "Moderate (10-50 MW)", "High (50-100 MW)"],
    default="Extreme (> 100 MW)"
)

clean_df['Africa_Region'] = np.select(
    [clean_df['latitude'] > 15, clean_df['latitude'] < -10, clean_df['longitude'] < 10, clean_df['longitude'] > 30],
    ["North Africa", "Southern Africa", "West Africa", "East Africa"],
    default="Central Africa"
)

clean_df.to_csv("africa_fires_cleaned.csv", index=False)
print(f"Done! Saved raw ({len(final_df)}) and cleaned ({len(clean_df)}) datasets.")
