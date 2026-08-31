import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='accident_db',
    charset='utf8mb4'
)
cursor = conn.cursor()

print("=" * 60)
print(" รายงานการวิเคราะห์จุดเสี่ยงอุบัติเหตุ")
print("=" * 60)

# 5 อันดับจังหวัดที่มีผู้เสียชีวิตสูงสุด
print("5 อันดับจังหวัดที่มีผู้เสียชีวิตสูงสุด:")
sql_1 = """
SELECT dead_prov, COUNT(id) AS total_deaths
FROM road_accident
GROUP BY dead_prov
ORDER BY total_deaths DESC
LIMIT 5;
"""
cursor.execute(sql_1)
results_1 = cursor.fetchall()

print(f"{'จังหวัด':<25}{'จำนวนผู้เสียชีวิต (ราย)':<15}")
print("-" * 45)
for row in results_1:
    print(f"{row[0]:<25}{row[1]:<15}")


# ประเภทยานพาหนะและกลุ่มอายุที่เกิดเหตุมากที่สุด
print("\n" + "=" * 60)
print("กลุ่มยานพาหนะและช่วงอายุที่เกิดเหตุสูงสุด:")
sql_2 = """
SELECT vehicle, age_group, COUNT(id) AS incident_count
FROM road_accident
WHERE vehicle != 'ไม่ระบุพาหนะ'
GROUP BY vehicle, age_group
ORDER BY incident_count DESC
LIMIT 5;
"""
cursor.execute(sql_2)
results_2 = cursor.fetchall()

print(f"{'ประเภทยานพาหนะ':<25}{'กลุ่มอายุ':<25}{'จำนวน (ราย)':<10}")
print("-" * 60)
for row in results_2:
    print(f"{row[0]:<25}{row[1]:<25}{row[2]:<10}")


# พิกัดจุดเสี่ยงสำหรับ
print("\n" + "=" * 60)
print("พิกัดจุดเสี่ยง :")
sql_3 = """
SELECT dead_prov, acc_district, latitude, longitude, COUNT(id) AS risk_count
FROM road_accident
WHERE latitude IS NOT NULL AND longitude IS NOT NULL
GROUP BY dead_prov, acc_district
ORDER BY risk_count DESC
LIMIT 5;
"""
cursor.execute(sql_3)
results_3 = cursor.fetchall()

print(f"{'จังหวัด':<18}{'อำเภอ':<18}{'พิกัด (Lat, Long)':<25}{'จำนวนเหตุ':<10}")
print("-" * 75)
for row in results_3:
    coords = f"{row[2]:.4f}, {row[3]:.4f}"
    print(f"{row[0]:<18}{row[1]:<18}{coords:<25}{row[4]:<10}")

# ปิดการเชื่อมต่อ
cursor.close()
conn.close()