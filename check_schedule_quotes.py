import psycopg2

conn = psycopg2.connect(
    host='yamabiko.proxy.rlwy.net',
    port=24047,
    database='railway',
    user='postgres',
    password='jruoTtzRtLhhIxVLtVYoLXwjuAzgNjBC'
)
cur = conn.cursor()

# hana008 사용자 ID 찾기
cur.execute("SELECT id, username FROM auth_user WHERE username = 'hana008'")
user = cur.fetchone()
print(f'사용자: {user}')

if user:
    user_id = user[0]
    
    print('\n' + '='*60)
    print('Schedule 테이블의 견적(quote) 일정 분석')
    print('='*60)
    
    # Schedule에서 견적 일정 (2025년)
    cur.execute("""
        SELECT s.id, f.customer_name, s.status, s.visit_date, s.expected_revenue
        FROM reporting_schedule s
        JOIN reporting_followup f ON s.followup_id = f.id
        WHERE s.user_id = %s 
          AND s.activity_type = 'quote'
          AND EXTRACT(YEAR FROM s.visit_date) = 2025
        ORDER BY s.visit_date DESC
    """, (user_id,))
    rows = cur.fetchall()
    
    print(f'\n[2025년 견적 일정 목록 (Schedule)] - 총 {len(rows)}개')
    completed = 0
    cancelled = 0
    scheduled = 0
    for row in rows:
        id, name, status, visit_date, revenue = row
        revenue = revenue or 0
        print(f'  ID:{id} | {name} | {status} | {visit_date} | {revenue:,.0f}원')
        if status == 'completed':
            completed += 1
        elif status == 'cancelled':
            cancelled += 1
        else:
            scheduled += 1
    
    print(f'\n  → 완료(승): {completed}개, 취소(패): {cancelled}개, 예정(대기): {scheduled}개')
    print(f'  → 전체: {len(rows)}개')

cur.close()
conn.close()
