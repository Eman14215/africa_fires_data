import os
import pandas as pd

MAP_KEY = os.environ["NASA_API_KEY"]
africa_coords = "-20,-35,55,38"
days = 10  # سحب داتا آخر 10 أيام كاملة (أقصى مدة متاحة في API ناسا)

# قائمة بكل أقمار VIIRS المتاحة (SNPP + NOAA-20 + NOAA-21)
viirs_sensors = ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"]
viirs_list = []

for sensor in viirs_sensors:
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{sensor}/{africa_coords}/{days}"
    df = pd.read_csv(url)
    df = df[df['confidence'] != 'l'] # مسح الإنذارات الضعيفة
    df = df.rename(columns={'bright_ti4': 'brightness', 'bright_ti5': 'bright_t31'})
    df['sensor'] = sensor
    viirs_list.append(df)

# سحب داتا قمر MODIS (Terra & Aqua) لآخر 10 أيام
url_modis = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/MODIS_NRT/{africa_coords}/{days}"
df_modis = pd.read_csv(url_modis)
df_modis = df_modis[df_modis['confidence'] >= 50]
df_modis['sensor'] = 'MODIS_NRT'

# دمج كل الأقمار في ملف واحد موحد
final_df = pd.concat(viirs_list + [df_modis], ignore_index=True)

# إزالة أي تكرار محتمل وحفظ الملف
final_df.drop_duplicates(inplace=True)
final_df.to_csv("africa_fires_latest.csv", index=False)
print(f"Updated successfully! Total fires for last {days} days: {len(final_df)}")
