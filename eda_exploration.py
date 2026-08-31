import pandas as pd

# 1. โหลดข้อมูล
df = pd.read_csv('Dataset/data_2026.csv')

# 2. ดูภาพรวมโครงสร้าง จำนวนแถว/คอลัมน์ และ Data Types
print("=== Overview & Data Types ===")
print(df.info())

# 3. ตรวจสอบจำนวนและสัดส่วนของ Missing Values ในแต่ละคอลัมน์
print("\n=== Missing Values Summary ===")
missing_summary = pd.DataFrame(
    {
        'Missing_Count': df.isnull().sum(),
        'Missing_Percentage': (df.isnull().sum() / len(df)) * 100,
    }
)
print(missing_summary.sort_values(by='Missing_Percentage', ascending=False))

# 4. ดูสถิติพื้นฐานของข้อมูลตัวเลข (เช็ค Min, Max, Mean, Median ของ Age)
print("\n=== Numerical Statistics ===")
print(df.describe())

# 5. ตรวจสอบจำนวนแถวที่ซ้ำกัน (Duplicate Rows)
print("\n=== Duplicate Rows Count ===")
print(f'Duplicate rows: {df.duplicated().sum()}')