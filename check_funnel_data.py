import psycopg2
from decimal import Decimal

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
    print('1. 영업기회 상태별 분석')
    print('='*60)
    
    # 전체 영업기회 상태별
    cur.execute("""
        SELECT ot.current_stage, COUNT(*), COALESCE(SUM(ot.expected_revenue), 0)
        FROM reporting_opportunitytracking ot
        JOIN reporting_followup f ON ot.followup_id = f.id
        WHERE f.user_id = %s
        GROUP BY ot.current_stage
        ORDER BY ot.current_stage
    """, (user_id,))
    rows = cur.fetchall()
    
    total_active = 0
    total_active_revenue = 0
    total_closed = 0
    
    print('\n[전체 영업기회]')
    for row in rows:
        stage, count, revenue = row
        print(f'  {stage}: {count}개, 예상매출: {revenue:,.0f}원')
        if stage in ['won', 'lost', 'quote_lost']:
            total_closed += count
        else:
            total_active += count
            total_active_revenue += revenue
    
    print(f'\n  → 활성화된 영업기회: {total_active}개')
    print(f'  → 활성화된 영업기회 예상매출: {total_active_revenue:,.0f}원')
    print(f'  → 종료된 영업기회: {total_closed}개')
    
    # 활성화된 영업기회 상세
    print('\n[활성화된 영업기회 상세]')
    cur.execute("""
        SELECT ot.id, f.customer_name, ot.current_stage, ot.expected_revenue, ot.created_at
        FROM reporting_opportunitytracking ot
        JOIN reporting_followup f ON ot.followup_id = f.id
        WHERE f.user_id = %s AND ot.current_stage NOT IN ('won', 'lost', 'quote_lost')
        ORDER BY ot.created_at DESC
    """, (user_id,))
    rows = cur.fetchall()
    for row in rows:
        id, name, stage, revenue, created = row
        revenue = revenue or 0
        print(f'  ID:{id} | {name} | {stage} | {revenue:,.0f}원 | {created.strftime("%Y-%m-%d")}')
    
    print('\n' + '='*60)
    print('2. 견적 데이터 분석')
    print('='*60)
    
    # 견적 수 (2025년)
    cur.execute("""
        SELECT h.id, f.customer_name, h.delivery_amount, h.created_at, 
               CASE 
                   WHEN s.status = 'completed' AND s.activity_type = 'delivery' THEN 'won'
                   WHEN s.status = 'cancelled' THEN 'lost'
                   ELSE 'pending'
               END as quote_status
        FROM reporting_history h
        JOIN reporting_followup f ON h.followup_id = f.id
        LEFT JOIN reporting_schedule s ON h.schedule_id = s.id
        WHERE f.user_id = %s 
          AND h.action_type = 'quote'
          AND EXTRACT(YEAR FROM h.created_at) = 2025
        ORDER BY h.created_at DESC
    """, (user_id,))
    rows = cur.fetchall()
    
    print(f'\n[2025년 견적 목록] - 총 {len(rows)}개')
    won_count = 0
    lost_count = 0
    pending_count = 0
    for row in rows:
        id, name, amount, created, status = row
        amount = amount or 0
        print(f'  ID:{id} | {name} | {amount:,.0f}원 | {created.strftime("%Y-%m-%d")} | {status}')
        if status == 'won':
            won_count += 1
        elif status == 'lost':
            lost_count += 1
        else:
            pending_count += 1
    
    print(f'\n  → 승: {won_count}개, 패: {lost_count}개, 대기: {pending_count}개')
    
    print('\n' + '='*60)
    print('3. 영업기회와 견적 관계 분석')
    print('='*60)
    
    # 영업기회별 연결된 견적
    cur.execute("""
        SELECT ot.id, f.customer_name, ot.current_stage, 
               (SELECT COUNT(*) FROM reporting_history h2 
                WHERE h2.followup_id = f.id AND h2.action_type = 'quote') as quote_count
        FROM reporting_opportunitytracking ot
        JOIN reporting_followup f ON ot.followup_id = f.id
        WHERE f.user_id = %s
        ORDER BY ot.created_at DESC
    """, (user_id,))
    rows = cur.fetchall()
    
    print('\n[영업기회별 견적 수]')
    for row in rows:
        opp_id, name, stage, quote_count = row
        print(f'  영업기회 ID:{opp_id} | {name} | {stage} | 견적 {quote_count}개')
    
    # 팔로우업별 영업기회 수
    print('\n[팔로우업별 영업기회 수]')
    cur.execute("""
        SELECT f.id, f.customer_name, COUNT(ot.id) as opp_count
        FROM reporting_followup f
        LEFT JOIN reporting_opportunitytracking ot ON ot.followup_id = f.id
        WHERE f.user_id = %s
        GROUP BY f.id, f.customer_name
        HAVING COUNT(ot.id) > 0
        ORDER BY COUNT(ot.id) DESC
    """, (user_id,))
    rows = cur.fetchall()
    for row in rows:
        f_id, name, opp_count = row
        print(f'  팔로우업 ID:{f_id} | {name} | 영업기회 {opp_count}개')

cur.close()
conn.close()
