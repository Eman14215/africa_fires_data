import os
import pandas as pd

# قراءة المفتاح السري من إعدادات GitHub
MAP_KEY = os.environ["NASA_API_KEY"]

# إحداثيات قارة أفريقيا بالكامل
africa_coords = "-20,-35,55,38"

# 1. سحب داتا قمر VIIRS (آخر 24 ساعة)
url_viirs = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/VIIRS_SNPP_NRT/{africa_coords}/1"
df_viirs = pd.read_csv(url_viirs)
df_viirs = df_viirs[df_viirs['confidence'] != 'l'] # مسح الإنذارات الضعيفة
df_viirs['sensor'] = 'VIIRS'

# 2. سحب داتا قمر MODIS (آخر 24 ساعة)
url_modis = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/MODIS_NRT/{africa_coords}/1"
df_modis = pd.read_csv(url_modis)
df_modis = df_modis[df_modis['confidence'] >= 50] # مسح الثقة الأقل من 50%
df_modis['sensor'] = 'MODIS'

# 3. دمج القمرين في جدول واحد وحفظه
final_df = pd.concat([df_viirs, df_modis], ignore_index=True)
final_df.to_csv("africa_fires_latest.csv", index=False)
print(f"Updated successfully! Total fires: {len(final_df)}")
