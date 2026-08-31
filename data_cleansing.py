import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import platform

os_name = platform.system()

if os_name == 'Windows':
    plt.rcParams['font.family'] = 'Tahoma'  # หรือ 'Leelawadee UI', 'Angsana New'
elif os_name == 'Darwin':  # macOS
    plt.rcParams['font.family'] = 'Thonburi'  # หรือ 'Sukhumvit Set'
else:  # Linux / Ubuntu
    plt.rcParams['font.family'] = 'Garuda'
# จัดการแกนลบและสระลอย
plt.rcParams['axes.unicode_minus'] = False

# 0. โหลดข้อมูลตั้งต้น
df = pd.read_csv('Dataset/data_2026.csv')

# ==========================================
# 1.1 เทคนิคที่ 1: การจัดการ Missing Values และ Drop คอลัมน์ซ้ำซ้อน/ว่างเปล่า (3 คะแนน)
# ==========================================

# 1. ลบคอลัมน์ที่เป็นค่าว่าง 100%
cols_to_drop = [
    'Tumbol',
    'RiskHelmet',
    'RiskSafetyBelt',
    'Date Rec',
    'Time Rec',
    'DEAD_YEAR_TH',
]  # ตัดปี พ.ศ. ทิ้งเพราะซ้ำกับ DEAD_YEAR_EN
df = df.drop(columns=cols_to_drop)

# 2. Imputation ค่าอายุ (Age) ที่หายไป 81 แถว ด้วยค่ามัธยฐาน (Median)
median_age = df['Age'].median()
df['Age'] = df['Age'].fillna(median_age)

# 3. เติมค่าว่างของคอลัมน์ข้อความด้วยคำว่า 'ไม่ระบุ'
text_impute_cols = [
    'Nationality',
    'District',
    'Province',
    'Acc_Sub_Dist',
    'ICD_10',
]
df[text_impute_cols] = df[text_impute_cols].fillna('ไม่ระบุ')


# ==========================================
# 1.2 เทคนิคที่ 2: การแก้ไขข้อมูลพิกัดสลับที่ และแปลง Data Types (3 คะแนน)
# ==========================================

# 1. สลับพิกัด ละติจูด-ลองจิจูด ให้ถูกต้องตามตำแหน่งประเทศไทย
# พิกัดไทย: Latitude อยู่ช่วง ~5.6 - 20.4, Longitude อยู่ช่วง ~97.3 - 105.6
df['Latitude'] = df['Acc_long']
df['Longitude'] = df['Acc_Lat']
df = df.drop(columns=['Acc_Lat', 'Acc_long'])

# 2. แปลง DeadDate_EN จาก Data String เป็น Datetime
df['DeadDate_EN'] = pd.to_datetime(df['DeadDate_EN'], format='%Y-%m-%d')

# 3. แปลง Age ให้เป็นจำนวนเต็ม (Integer)
df['Age'] = df['Age'].astype(int)

# 4. ตัดช่องว่างส่วนเกินในข้อมูลข้อความ (Strip whitespace)
str_columns = df.select_dtypes(include=['object']).columns
for col in str_columns:
  df[col] = df[col].astype(str).str.strip()


# ==========================================
# 1.3 เทคนิคที่ 3: Data Transformation & Visualization (4 คะแนน)
# ==========================================

# 1. สร้างช่วงอายุ (Age Groups) และวัน/เดือนที่เกิดเหตุ
age_bins = [0, 15, 24, 60, 120]
age_labels = ['0-15 ปี', '16-24 ปี (วัยรุ่น)', '25-59 ปี (วัยทำงาน)', '60 ปีขึ้นไป']
df['Age_Group'] = pd.cut(
    df['Age'], bins=age_bins, labels=age_labels, right=False
)

df['Accident_Month'] = df['DeadDate_EN'].dt.month
df['Accident_Day'] = df['DeadDate_EN'].dt.day_name()

# 2. Data Aggregation: สรุปพื้นที่จุดเสี่ยง 10 อันดับแรก (Top 10 High-Risk Provinces)
top_provinces = df['Dead_Prov'].value_counts().head(10)

# 3. สร้างกราฟแท่ง
fig, ax = plt.subplots(figsize=(11, 6))
bars = ax.bar(
    top_provinces.index, 
    top_provinces.values, 
    color='#e63946', 
    edgecolor='black', 
    width=0.6
)

ax.bar_label(bars, padding=4, fontsize=11, fontweight='bold', color='#1d3557')

ax.set_ylim(0, top_provinces.values.max() * 1.15)
ax.set_title('10 อันดับจังหวัดที่มีผู้เสียชีวิตจากอุบัติเหตุสูงสุด (ปี 2569)', fontsize=15, pad=15)
ax.set_xlabel('จังหวัด', fontsize=12)
ax.set_ylabel('จำนวนผู้เสียชีวิต (ราย)', fontsize=12)

plt.xticks(rotation=45, ha='right', fontsize=11)
plt.yticks(fontsize=10)
plt.grid(axis='y', linestyle='--', alpha=0.5)  # เส้น Grid แนวนอนช่วยให้อ่านค่าง่ายขึ้น
plt.tight_layout()

plt.savefig('top_10_risk_provinces.png', dpi=300)
plt.show()

# บันทึกไฟล์ข้อมูลที่ Clean เสร็จแล้ว สำหรับนำไปใช้ในขั้นตอน Database
df.to_csv('cleaned_data_2026.csv', index=False)
print(
    "Data Cleansing & Transformation complete! Saved to 'cleaned_data_2026.csv'"
)