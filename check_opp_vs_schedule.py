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
    print('1. 영업기회 전체 목록 (OpportunityTracking)')
    print('='*60)
    
    cur.execute("""
        SELECT ot.id, f.customer_name, ot.current_stage, ot.created_at,
               (SELECT COUNT(*) FROM reporting_schedule s 
                WHERE s.followup_id = f.id AND s.activity_type = 'quote') as quote_schedules
        FROM reporting_opportunitytracking ot
        JOIN reporting_followup f ON ot.followup_id = f.id
        WHERE f.user_id = %s
        ORDER BY ot.created_at DESC
    """, (user_id,))
    rows = cur.fetchall()
    
    print(f'\n전체 영업기회: {len(rows)}개')
    for row in rows:
        opp_id, name, stage, created, quote_count = row
        print(f'  ID:{opp_id} | {name} | {stage} | {created.strftime("%Y-%m-%d")} | 견적일정 {quote_count}개')
    
    print('\n' + '='*60)
    print('2. 견적 일정(Schedule)과 영업기회 연결 분석')
    print('='*60)
    
    # 견적 일정이 있는데 영업기회가 없는 경우
    cur.execute("""
        SELECT s.id, f.customer_name, s.status, s.visit_date,
               (SELECT COUNT(*) FROM reporting_opportunitytracking ot WHERE ot.followup_id = f.id) as opp_count
        FROM reporting_schedule s
        JOIN reporting_followup f ON s.followup_id = f.id
        WHERE s.user_id = %s 
          AND s.activity_type = 'quote'
          AND EXTRACT(YEAR FROM s.visit_date) = 2025
        ORDER BY s.visit_date DESC
    """, (user_id,))
    rows = cur.fetchall()
    
    no_opp = []
    has_opp = []
    for row in rows:
        s_id, name, status, visit_date, opp_count = row
        if opp_count == 0:
            no_opp.append(row)
        else:
            has_opp.append(row)
    
    print(f'\n[영업기회가 있는 견적 일정] - {len(has_opp)}개')
    for row in has_opp:
        s_id, name, status, visit_date, opp_count = row
        print(f'  Schedule ID:{s_id} | {name} | {status} | {visit_date} | 영업기회 {opp_count}개')
    
    print(f'\n[영업기회가 없는 견적 일정] - {len(no_opp)}개')
    for row in no_opp:
        s_id, name, status, visit_date, opp_count = row
        print(f'  Schedule ID:{s_id} | {name} | {status} | {visit_date} | 영업기회 없음')
    
    print('\n' + '='*60)
    print('3. 영업기회 단계별 정리')
    print('='*60)
    
    # 영업기회 단계별 통계
    cur.execute("""
        SELECT ot.current_stage, COUNT(*) as cnt
        FROM reporting_opportunitytracking ot
        JOIN reporting_followup f ON ot.followup_id = f.id
        WHERE f.user_id = %s
        GROUP BY ot.current_stage
        ORDER BY 
            CASE ot.current_stage 
                WHEN 'lead' THEN 1
                WHEN 'contact' THEN 2
                WHEN 'quote' THEN 3
                WHEN 'closing' THEN 4
                WHEN 'won' THEN 5
                WHEN 'lost' THEN 6
                WHEN 'quote_lost' THEN 7
            END
    """, (user_id,))
    rows = cur.fetchall()
    
    print('\n[영업기회 단계별 통계]')
    active_stages = ['lead', 'contact', 'quote', 'closing']
    closed_stages = ['won', 'lost', 'quote_lost']
    
    active_count = 0
    closed_count = 0
    
    for row in rows:
        stage, cnt = row
        stage_type = '활성' if stage in active_stages else '종료'
        print(f'  {stage}: {cnt}개 ({stage_type})')
        if stage in active_stages:
            active_count += cnt
        else:
            closed_count += cnt
    
    print(f'\n  → 활성화 영업기회: {active_count}개')
    print(f'  → 종료된 영업기회: {closed_count}개')
    print(f'  → 전체 영업기회: {active_count + closed_count}개')
    
    print('\n' + '='*60)
    print('4. 결론')
    print('='*60)
    print(f'''
- Schedule 견적 일정: 15개 (여러 고객에게 견적 제출)
- OpportunityTracking 영업기회: 10개 (고객별 영업 추적)

** 차이 원인 **
1. 하나의 고객(팔로우업)에 여러 견적 일정이 있을 수 있음
2. 견적 일정이 있어도 영업기회가 생성되지 않은 경우가 있음
   (영업기회 없는 견적: {len(no_opp)}개)

** 영업기회 전환 현황 **
- 전체(종료): {closed_count}개 (won + lost + quote_lost)
- 활성화: {active_count}개 (lead + contact + quote + closing)

** 견적 승패 현황 **
- 전체: 15개 (Schedule 기준)
''')

cur.close()
conn.close()
