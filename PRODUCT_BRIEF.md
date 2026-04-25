# PRODUCT_BRIEF.md

## Product

- Product name: 세일즈 노트 / 영업노트
- Current public title: 영업 보고 시스템
- URL: https://web-production-5096.up.railway.app/
- Product type: Korean sales reporting and sales management system

## Current public observation

The public page is a login page.
The privacy policy describes the service purpose as:

- Customer management
- Sales opportunity management
- Quote and contract creation
- Schedule management
- Service improvement and usage analysis

Because the authenticated application screens are not publicly visible, Copilot must inspect the repository before making implementation decisions.

## Product goal

Build and improve a practical internal sales management system for Korean companies.

The system should make it easy to:

- Write sales reports
- Manage customers and contacts
- Track opportunities/deals
- Manage quotes and contracts
- Manage schedules and follow-up tasks
- Review team performance
- Protect personal and business data

## Primary users

### 1. Sales representative

Needs:
- 빠르게 영업보고 작성
- 오늘의 일정 확인
- 고객 방문/통화 기록
- 후속 조치 등록
- 영업기회 상태 업데이트
- 견적/계약 현황 확인

Key pain points:
- 보고서 작성 시간이 오래 걸림
- 고객/기회/일정이 따로 관리됨
- 이전 방문 이력 찾기 어려움
- 후속 조치 누락

### 2. Sales manager

Needs:
- 팀원별 보고 현황 확인
- 미검토 보고서 확인
- 영업기회 단계별 현황 확인
- 매출/계약 예상 파이프라인 확인
- 지연된 후속 조치 확인

Key pain points:
- 팀 영업 활동이 한눈에 보이지 않음
- 보고서 품질 편차
- 영업기회 업데이트 누락
- 실적 예측 어려움

### 3. Admin

Needs:
- 사용자 관리
- 팀/권한 관리
- 데이터 관리
- 시스템 설정
- 개인정보 처리 안정성 확인

Key pain points:
- 권한 오류
- 개인정보 노출 위험
- 데이터 정합성 문제
- 배포 후 장애

## Core modules

- Dashboard
- Sales Reports
- Customers / Companies
- Contacts
- Opportunities / Deals
- Schedules / Tasks
- Quotes / Contracts
- Files / Attachments
- Notifications
- Admin / Users / Roles
- Privacy / Security

## Key business objects

Use existing repository names if they already exist.

Recommended conceptual objects:

| Object | Korean label | Purpose |
|---|---|---|
| User | 사용자 | 로그인 사용자 |
| Team | 팀 | 영업 조직 |
| CustomerCompany | 고객사 / 거래처 | 고객 회사 |
| ContactPerson | 담당자 | 고객사 담당자 |
| SalesReport | 영업보고 | 방문/통화/미팅 보고 |
| SalesActivity | 영업활동 | 고객 접점 기록 |
| Opportunity | 영업기회 | 딜/수주 가능성 관리 |
| Quote | 견적 | 견적 제안 |
| Contract | 계약 | 계약/수주 관리 |
| Schedule | 일정 | 미팅/방문/통화 일정 |
| Task | 할 일 | 후속 조치 |
| Attachment | 첨부파일 | 문서/이미지 |
| Comment | 코멘트 | 관리자 피드백 |
| Notification | 알림 | 업무 알림 |
| AuditLog | 감사 로그 | 중요 변경 이력 |

## Success metrics

- 영업보고 작성 완료율
- 영업보고 작성 소요 시간
- 팀원별 보고 제출률
- 미검토 보고서 수
- 지연된 후속 조치 수
- 영업기회 단계별 전환율
- 견적 → 계약 전환율
- 고객별 최근 활동 조회율
- 모바일 사용 시 폼 완료율
- 로그인 실패/보안 이벤트 수

## Non-goals

Do not implement unless explicitly requested:

- Public marketing homepage redesign
- Product catalog website
- E-commerce checkout
- Bio/life-science distributor pages
- Brand/product catalog download pages
- Public quote request website