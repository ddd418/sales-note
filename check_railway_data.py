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
    
    # 전체 영업기회 수
    cur.execute("""
        SELECT COUNT(*) FROM reporting_opportunitytracking ot
        JOIN reporting_followup f ON ot.followup_id = f.id
        WHERE f.user_id = %s
    """, (user_id,))
    total = cur.fetchone()[0]
    print(f'\n전체 영업기회 수: {total}')
    
    # 올해 등록된 영업기회
    cur.execute("""
        SELECT COUNT(*) FROM reporting_opportunitytracking ot
        JOIN reporting_followup f ON ot.followup_id = f.id
        WHERE f.user_id = %s AND EXTRACT(YEAR FROM ot.created_at) = 2025
    """, (user_id,))
    this_year = cur.fetchone()[0]
    print(f'올해(2025) 등록된 영업기회 수: {this_year}')
    
    # 상태별 분류
    print('\n--- 올해 영업기회 상태별 ---')
    for stage in ['lead', 'contact', 'quote', 'closing', 'won', 'lost']:
        cur.execute("""
            SELECT COUNT(*) FROM reporting_opportunitytracking ot
            JOIN reporting_followup f ON ot.followup_id = f.id
            WHERE f.user_id = %s AND EXTRACT(YEAR FROM ot.created_at) = 2025 AND ot.current_stage = %s
        """, (user_id, stage))
        count = cur.fetchone()[0]
        print(f'{stage}: {count}개')
    
    # won + lost
    cur.execute("""
        SELECT COUNT(*) FROM reporting_opportunitytracking ot
        JOIN reporting_followup f ON ot.followup_id = f.id
        WHERE f.user_id = %s AND EXTRACT(YEAR FROM ot.created_at) = 2025 AND ot.current_stage IN ('won', 'lost')
    """, (user_id,))
    closed = cur.fetchone()[0]
    print(f'\n종료된 영업기회 (won+lost): {closed}개')
    
    # 전체 기간
    print('\n--- 전체 기간 상태별 ---')
    cur.execute("""
        SELECT current_stage, COUNT(*) FROM reporting_opportunitytracking ot
        JOIN reporting_followup f ON ot.followup_id = f.id
        WHERE f.user_id = %s
        GROUP BY current_stage
    """, (user_id,))
    for row in cur.fetchall():
        print(f'{row[0]}: {row[1]}개')

conn.close()
