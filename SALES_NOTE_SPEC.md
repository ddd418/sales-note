# SALES_NOTE_SPEC.md

## Product direction

세일즈 노트는 영업사원이 보고서를 빠르게 작성하고, 관리자가 팀의 영업 현황을 한눈에 파악할 수 있는 영업관리 시스템이어야 한다.

Focus on:
- 입력 속도
- 데이터 연결성
- 조회 편의성
- 관리자 리뷰
- 후속 조치 누락 방지
- 모바일 접근성
- 개인정보 보호

## Recommended navigation

Use existing routing if already defined.

Recommended main navigation:

- 대시보드
- 영업보고
- 고객관리
- 영업기회
- 일정 / 할 일
- 견적 / 계약
- 알림
- 관리자

## Dashboard

### Purpose

Show the most important sales status at a glance.

### Recommended widgets

For sales representatives:
- 오늘의 일정
- 작성 대기 영업보고
- 최근 고객 활동
- 진행 중 영업기회
- 예정된 후속 조치
- 이번 주 보고 현황

For managers:
- 팀 영업보고 제출 현황
- 미검토 보고서
- 지연된 후속 조치
- 영업기회 단계별 현황
- 예상 매출 / 계약 예정
- 팀원별 활동량

### UX rules

- Use cards for summary numbers.
- Use tables for report/opportunity lists.
- Use status badges.
- Link each widget to the relevant list/detail page.
- Empty states must guide the user to the next action.

## Sales reports

### List page

Required:
- Search
- Date range filter
- Author filter if manager/admin
- Customer filter
- Status filter
- Sort by latest
- Pagination
- Quick link to create report

Recommended columns:
- 작성일
- 작성자
- 고객사
- 활동 유형
- 요약
- 다음 조치
- 상태
- 검토 여부

### Detail page

Required:
- Report summary
- Customer/company
- Contact person
- Activity type
- Meeting/call date
- Content
- Result
- Next action
- Related opportunity
- Attachments
- Manager comment/review area
- Edit button if permitted

### Create/edit form

Required:
- Customer/company
- Contact person
- Activity date
- Activity type
- Summary
- Detailed content
- Result
- Next action
- Next action due date
- Related opportunity
- Attachments if supported

UX:
- Use Korean validation messages.
- Save draft if supported.
- Prevent accidental loss if possible.
- Show clear success message.

## Customer management

### Customer list

Required:
- Search by company name
- Filter by owner/team/status if supported
- Recent activity indicator
- Last contact date
- Next follow-up date

### Customer detail

Required:
- Company profile
- Contact people
- Sales reports
- Opportunities
- Quotes/contracts
- Schedules/tasks
- Attachments
- Internal notes

## Opportunities

### Pipeline list

Required:
- Stage filter
- Owner filter
- Customer filter
- Expected close date
- Expected amount if supported
- Probability if supported
- Next action

Recommended stages:
- 신규
- 접촉
- 제안
- 견적
- 협상
- 계약
- 보류
- 실패

Use existing stages if already defined.

### Opportunity detail

Required:
- Customer
- Contact person
- Stage
- Expected amount
- Expected close date
- Probability
- Recent activities
- Related reports
- Related quotes/contracts
- Next action
- Notes

## Schedule / tasks

Required:
- Calendar or list view
- Today / this week filter
- Assigned user
- Customer/opportunity link
- Status: 예정, 완료, 지연, 취소
- Reminder/notification if supported

## Quotes / contracts

Required:
- Customer
- Opportunity
- Quote/contract number if supported
- Status
- Amount
- Issue date
- Expected contract date
- Attachments
- Notes

Do not implement accounting/tax functionality unless already present.

## Notifications

Useful notification types:
- New manager comment
- Report review required
- Next action due today
- Overdue follow-up
- Opportunity stage changed
- Quote/contract status changed

## Admin

Recommended:
- User management
- Team management
- Role/permission management
- Basic system settings
- Data export if supported
- Audit log if supported

## Permission model

Respect existing permissions.

Recommended conceptual roles:
- Sales rep
- Manager
- Admin

Rules:
- Sales reps should access their own data and assigned customer/opportunity data.
- Managers should access team data.
- Admins can manage users/settings.
- Sensitive data must not be exposed to unauthorized users.

## Korean UX messages

Examples:

- “영업보고를 저장했습니다.”
- “고객사를 선택해 주세요.”
- “다음 조치 예정일을 입력해 주세요.”
- “검토 의견을 등록했습니다.”
- “삭제 후에는 복구할 수 없습니다.”
- “권한이 없어 접근할 수 없습니다.”
- “검색 결과가 없습니다.”
- “아직 등록된 영업기회가 없습니다.”

## Empty states

Use actionable empty states.

Examples:
- “등록된 영업보고가 없습니다. 첫 영업보고를 작성해 보세요.”
- “진행 중인 영업기회가 없습니다. 고객 상세 화면에서 새 기회를 등록할 수 있습니다.”
- “오늘 예정된 일정이 없습니다.”
- “검색 조건에 맞는 고객사가 없습니다.”

## Mobile UX

Important pages should work on mobile:

- Login
- Dashboard
- Sales report create/edit
- Sales report list/detail
- Customer detail
- Schedule/task list

Mobile rules:
- Avoid wide tables without responsive handling.
- Use stacked cards for lists if needed.
- Keep primary actions visible.
- Use large enough touch targets.