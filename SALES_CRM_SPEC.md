# SALES_CRM_SPEC.md

## Purpose

This document defines the target direction for the existing Django Sales Note / Sales Management System.

The goal is to improve the internal CRM/reporting workflow, not to build a public website.

## Core user journeys

### 1. Sales rep writes a sales note

User wants to:
- Log in
- Quickly select or search customer/account
- Write activity result
- Set next action
- Set next contact date
- Save without friction
- Return to list or dashboard

Important UX:
- Fast form
- Good mobile layout
- Minimal required fields
- Clear validation
- Recent customers or quick search if feasible

### 2. Sales manager reviews activity

User wants to:
- See today/this week activity
- See who submitted reports
- Find overdue follow-ups
- Filter by salesperson
- Check important opportunities
- Open customer history

Important UX:
- Dashboard cards
- Filterable lists
- Status badges
- Activity timeline

### 3. User checks a customer/account

User wants to:
- See customer basic info
- See all sales notes
- See last contact date
- See next scheduled action
- See current opportunity status
- Add new note

Important UX:
- Customer detail page
- Activity timeline
- Quick add note button
- Related opportunities if existing

### 4. User follows up

User wants to:
- See scheduled follow-ups
- See overdue actions
- Mark follow-up complete
- Create next follow-up
- Update status

Important UX:
- Follow-up list
- Due date badges
- Overdue highlighting
- Clear next action text

## Recommended navigation

Authenticated navigation should prioritize:

- 대시보드
- 영업노트
- 거래처
- 고객/담당자
- 후속조치
- 영업현황
- 보고서
- 설정 or 관리자

Use existing structure where possible.

## Dashboard requirements

Useful dashboard cards:

- 오늘 작성된 영업노트
- 이번 주 영업활동
- 예정된 후속조치
- 지연된 후속조치
- 최근 업데이트 거래처
- 담당자별 활동 현황
- 영업 단계별 현황 if data exists
- 빠른 영업노트 작성

## Sales note list requirements

Recommended improvements:

- Keyword search
- Date range filter
- Salesperson filter
- Customer/account filter
- Activity type filter
- Status/stage filter
- Follow-up due filter
- Sort by recent activity
- Pagination
- Empty state
- Mobile-friendly table or card layout

## Sales note detail requirements

Recommended sections:

1. Basic summary
   - 제목
   - 거래처
   - 담당자
   - 작성자
   - 활동일
   - 상태

2. Activity content
   - 영업 내용
   - 고객 반응
   - 이슈
   - 요청사항

3. Sales status
   - 영업 단계
   - 예상 금액
   - 수주 가능성
   - 견적 여부

4. Follow-up
   - 다음 액션
   - 다음 연락일
   - 완료 여부

5. Actions
   - 수정
   - 삭제 if permitted
   - 후속조치 완료
   - 새 영업노트 작성
   - 거래처 상세 보기

## Sales note form requirements

Recommended fields, depending on existing models:

- 거래처
- 고객/담당자
- 활동 유형
- 활동일
- 제목
- 내용
- 영업 단계
- 예상 금액
- 다음 액션
- 다음 연락일
- 상태

Do not add these fields blindly.
Inspect existing models first.
If model changes are needed, create a plan before migration.

## Customer/account requirements

If customer/account pages exist, improve:

- List search
- Detail page
- Recent activity timeline
- Last contact date
- Next follow-up date
- Assigned salesperson
- Quick add sales note

If they do not exist, propose minimal implementation in AGENT_PLAN.md before adding.

## Follow-up requirements

A follow-up system should show:

- Today’s follow-ups
- Upcoming follow-ups
- Overdue follow-ups
- Owner
- Customer/account
- Next action
- Due date
- Completion status

## Permissions

Preserve existing permission model.

Do not expose:
- Sales notes
- Customer data
- Reports
- Dashboard
- User data

to anonymous users.

## UI style

Use clean internal business-system UI.

Preferred:
- Clear tables
- Filters
- Badges
- Cards
- Timeline
- Quick action buttons
- Sticky action areas where useful

Avoid:
- Public marketing sections
- Hero landing page
- Product category cards
- Brand showcase
- SEO-focused public copy

## Quality standards

- Existing login works
- Existing reporting URLs continue to work
- No internal data exposed publicly
- Forms validate correctly
- Dashboard loads without errors
- List pages handle empty states
- Mobile layout remains usable
- Django checks pass