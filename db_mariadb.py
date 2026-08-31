import pymysql
import pandas as pd
import numpy as np

# 1. สร้างการเชื่อมต่อกับ MariaDB
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='accident_db',
    charset='utf8mb4',
    autocommit=True
)
cursor = conn.cursor()

# 2. สร้างตาราง road_accident
create_table_sql = """
CREATE TABLE IF NOT EXISTS road_accident (
    id INT PRIMARY KEY,
    dead_year_en INT,
    dead_date DATE,
    age INT,
    sex VARCHAR(20),
    nationality VARCHAR(50),
    district VARCHAR(100),
    province VARCHAR(100),
    acc_sub_dist VARCHAR(100),
    acc_district VARCHAR(100),
    dead_prov VARCHAR(100),
    latitude FLOAT,
    longitude FLOAT,
    icd_10 VARCHAR(20),
    vehicle VARCHAR(100),
    age_group VARCHAR(50),
    accident_month INT,
    accident_day VARCHAR(20)
);
"""

# สร้าง Table ใหม่
cursor.execute("DROP TABLE IF EXISTS road_accident;")
cursor.execute(create_table_sql)
print("สร้างตาราง 'road_accident' ใน MariaDB สำเร็จ")

# 3. อ่านไฟล์ข้อมูลที่ Clean แล้ว
df = pd.read_csv('cleaned_data_2026.csv')

# แปลงค่า NaN / None ให้เป็น None ของ Python เพื่อให้ลง Database เป็น NULL
df = df.replace({np.nan: None})

# 4. เตรียมคำสั่ง INSERT ลงฐานข้อมูล
insert_sql = """
INSERT INTO road_accident (
    id, dead_year_en, dead_date, age, sex, nationality,
    district, province, acc_sub_dist, acc_district, dead_prov,
    latitude, longitude, icd_10, vehicle, age_group,
    accident_month, accident_day
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
"""

# แปลงข้อมูลใน DataFrame ให้เป็น List ของ Tuple เพื่อเตรียม Insert
data_to_insert = [
    (
        int(row['ID']),
        int(row['DEAD_YEAR_EN']),
        str(row['DeadDate_EN']),
        int(row['Age']),
        str(row['Sex']),
        str(row['Nationality']),
        str(row['District']),
        str(row['Province']),
        str(row['Acc_Sub_Dist']),
        str(row['Acc_District']),
        str(row['Dead_Prov']),
        row['Latitude'],
        row['Longitude'],
        str(row['ICD_10']),
        str(row['Vehicle']),
        str(row['Age_Group']),
        int(row['Accident_Month']),
        str(row['Accident_Day'])
    )
    for _, row in df.iterrows()
]

# Execute
cursor.executemany(insert_sql, data_to_insert)
print(f" นำเข้าข้อมูล {len(data_to_insert)} แถวเข้าสู่ MariaDB สำเร็จ")

cursor.close()
conn.close()