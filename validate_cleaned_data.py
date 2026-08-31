import pandas as pd

# 1. โหลดไฟล์ที่ Clean แล้ว
df = pd.read_csv('cleaned_data_2026.csv')

print("=== START DATA QUALITY VALIDATION ===")

# 2. ตรวจสอบจำนวนแถวและคอลัมน์
assert len(df) == 4482, f"❌ แถวหาย: พบ {len(df)} แถว (ต้องมี 4482 แถว)"
print(f"✅ Row Count Check Passed: {len(df)} rows")

# 3. ตรวจสอบ Missing Values ในฟิลด์สำคัญ
assert df['Age'].isnull().sum() == 0, "❌ พบคอลัมน์ Age ยังมีค่าว่าง"
assert df['Dead_Prov'].isnull().sum() == 0, "❌ พบคอลัมน์ Dead_Prov มีค่าว่าง"
print("✅ Null Values Check Passed: ไม่มี Missing Values ในฟิลด์หลัก")

# 4. ตรวจสอบช่วงพิกัด Latitude และ Longitude (GIS Validity)
valid_lat = df['Latitude'].dropna().between(5.0, 21.0).all()
valid_long = df['Longitude'].dropna().between(97.0, 106.0).all()

assert valid_lat, "❌ Latitude อยู่นอกช่วงพิกัดประเทศไทย (5 - 21)"
assert valid_long, "❌ Longitude อยู่นอกช่วงพิกัดประเทศไทย (97 - 106)"
print("✅ Coordinates Range Check Passed: พิกัดถูกต้องตามแผนที่ประเทศไทย")

# 5. ตรวจสอบว่าคอลัมน์ที่ตั้งใจลบ ไม่หลงเหลืออยู่
dropped_cols = ['Tumbol', 'RiskHelmet', 'RiskSafetyBelt', 'Date Rec', 'Time Rec', 'Acc_Lat', 'Acc_long']
assert not any(col in df.columns for col in dropped_cols), "❌ พบคอลัมน์ที่ไม่จำเป็นหลงเหลืออยู่"
print("✅ Schema Check Passed: โครงสร้างตารางสะอาด พร้อมนำเข้า Database")

print("\n🎉 ข้อมูลผ่านการทดสอบทั้งหมด พร้อมส่งต่อไปยัง Database / Airflow แล้ว!")