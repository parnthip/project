from datetime import datetime, timedelta
import os
import pandas as pd
import numpy as np
import pymysql
import requests

from airflow import DAG
from airflow.operators.python import PythonOperator

# -------------------------------------------------------------
# 1. กำหนด Configuration และ Path ให้อิงตาม Container
# -------------------------------------------------------------
DAGS_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(DAGS_DIR, "dataset")
os.makedirs(DATASET_DIR, exist_ok=True)

RAW_DATA_PATH = os.path.join(DATASET_DIR, "data_2026.csv")
CLEAN_DATA_PATH = os.path.join(DATASET_DIR, "cleaned_accident_data_2026.csv")

# การตั้งค่า Network ภายใน Docker Compose
DB_CONFIG = {
    'host': os.getenv('MARIADB_HOST', 'mariadb'),
    'user': os.getenv('MARIADB_USER', 'root'),
    'password': os.getenv('MARIADB_PASSWORD', 'rootpassword'),
    'database': 'accident_db',
    'charset': 'utf8mb4',
    'autocommit': True
}

# n8n Service ภายใน Docker Network
N8N_WEBHOOK_URL = 'http://n8n:5678/webhook/accident-alert'

default_args = {
    'owner': 'data_engineer_team',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=3),
}

# -------------------------------------------------------------
# Task 1: Extract & Transform
# -------------------------------------------------------------
def extract_and_transform():
    if not os.path.exists(RAW_DATA_PATH):
        raise FileNotFoundError(f"ไม่พบไฟล์ข้อมูลที่: {RAW_DATA_PATH}")

    df = pd.read_csv(RAW_DATA_PATH)

    # 1. ลบคอลัมน์ที่เป็นค่าว่าง 100% และคอลัมน์ปี พ.ศ. ที่ซ้ำซ้อน
    cols_to_drop = ['Tumbol', 'RiskHelmet', 'RiskSafetyBelt', 'Date Rec', 'Time Rec', 'DEAD_YEAR_TH']
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

    # 2. จัดการ Missing Values
    df['Age'] = df['Age'].fillna(df['Age'].median()).astype(int)
    text_cols = ['Nationality', 'District', 'Province', 'Acc_Sub_Dist', 'ICD_10']
    df[text_cols] = df[text_cols].fillna('ไม่ระบุ')

    # 3. สลับพิกัด Lat <-> Long ให้ถูกต้องตามพิกัดไทย
    df['Latitude'] = df['Acc_long']
    df['Longitude'] = df['Acc_Lat']
    df = df.drop(columns=['Acc_Lat', 'Acc_long'])

    # 4. สร้างกลุ่มอายุและมิติเวลา
    age_bins = [0, 15, 24, 60, 120]
    age_labels = ['0-15 ปี', '16-24 ปี (วัยรุ่น)', '25-59 ปี (วัยทำงาน)', '60 ปีขึ้นไป']
    df['Age_Group'] = pd.cut(df['Age'], bins=age_bins, labels=age_labels, right=False)

    df['DeadDate_EN'] = pd.to_datetime(df['DeadDate_EN'])
    df['Accident_Month'] = df['DeadDate_EN'].dt.month
    df['Accident_Day'] = df['DeadDate_EN'].dt.day_name()

    # บันทึกไฟล์ผลลัพธ์
    df.to_csv(CLEAN_DATA_PATH, index=False)
    print(f"Task 1 Success: บันทึก Cleaned Data ไว้ที่ {CLEAN_DATA_PATH}")

# -------------------------------------------------------------
# Task 2: Load Data to MariaDB
# -------------------------------------------------------------
def load_to_mariadb():
    if not os.path.exists(CLEAN_DATA_PATH):
        raise FileNotFoundError(f"ไม่พบไฟล์ Cleaned Data ที่: {CLEAN_DATA_PATH}")

    df = pd.read_csv(CLEAN_DATA_PATH)
    df = df.replace({np.nan: None})

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    create_sql = """
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
    cursor.execute("DROP TABLE IF EXISTS road_accident;")
    cursor.execute(create_sql)

    insert_sql = """
    INSERT INTO road_accident (
        id, dead_year_en, dead_date, age, sex, nationality,
        district, province, acc_sub_dist, acc_district, dead_prov,
        latitude, longitude, icd_10, vehicle, age_group,
        accident_month, accident_day
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    data_to_insert = [
        (
            int(r['ID']), int(r['DEAD_YEAR_EN']), str(r['DeadDate_EN']), int(r['Age']),
            str(r['Sex']), str(r['Nationality']), str(r['District']), str(r['Province']),
            str(r['Acc_Sub_Dist']), str(r['Acc_District']), str(r['Dead_Prov']),
            r['Latitude'], r['Longitude'], str(r['ICD_10']), str(r['Vehicle']),
            str(r['Age_Group']), int(r['Accident_Month']), str(r['Accident_Day'])
        )
        for _, r in df.iterrows()
    ]

    cursor.executemany(insert_sql, data_to_insert)
    cursor.close()
    conn.close()
    print(f"Task 2 Success: นำเข้าข้อมูล {len(data_to_insert)} แถวลง MariaDB สำเร็จ")

# -------------------------------------------------------------
# Task 3: Query Hotspots & Trigger Agentic AI Webhook (n8n)
# -------------------------------------------------------------
def trigger_agentic_ai():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
    SELECT dead_prov, acc_district, latitude, longitude, vehicle, COUNT(id) AS count
    FROM road_accident
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    GROUP BY dead_prov, acc_district, vehicle
    ORDER BY count DESC
    LIMIT 3;
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    risk_data = [
        {
            "province": r[0],
            "district": r[1],
            "latitude": r[2],
            "longitude": r[3],
            "vehicle_type": r[4],
            "fatalities_count": r[5]
        }
        for r in rows
    ]

    payload = {
        "report_title": "Road Accident Risk Intelligence Report",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "top_risk_hotspots": risk_data
    }

    try:
        res = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
        print(f"Task 3 Success: ส่งข้อมูลเข้า n8n Webhook สำเร็จ (Status: {res.status_code})")
    except Exception as e:
        print(f"Task 3 Warning: ยิง Webhook ไม่สำเร็จ ({e})")

# -------------------------------------------------------------
# 2. นิยาม DAG Pipeline และ Schedule
# -------------------------------------------------------------
with DAG(
    dag_id='road_accident_risk_pipeline',
    default_args=default_args,
    description='Automated ETL & Agentic AI Alert Pipeline',
    schedule='0 8 * * 1',
    catchup=False,
    tags=['road_safety', 'mariadb', 'agentic_ai']
) as dag:

    task_clean = PythonOperator(
        task_id='clean_data_task',
        python_callable=extract_and_transform
    )

    task_load = PythonOperator(
        task_id='load_to_mariadb_task',
        python_callable=load_to_mariadb
    )

    task_alert = PythonOperator(
        task_id='trigger_ai_alert_task',
        python_callable=trigger_agentic_ai
    )

    task_clean >> task_load >> task_alert