"""기록을 켜기 전 한 주의 단계 변경을 일정 근거로 복원한다(기본은 미리보기, --apply 로 저장).

근거가 있는 것만 넣는다. 일정 없이 보드에서 직접 옮긴 건은 복원되지 않으므로, 넣은 기록은
source='backfill' 로 구분해 회의 화면에 "복원한 주"라고 밝히고 언제든 지울 수 있게 한다.

- 실주: 그 주에 취소된 견적 일정 + 카드가 지금 실주
- 수주: 그 주의 완료 납품 + 카드가 지금 수주 + 올해 그 전에 납품이 없음(이미 수주였던 건 변화가 아님)
- 견적 제출: 그 주의 완료 견적 + 카드가 지금 견적/협상 + 올해 그 전에 완료 견적이 없음
"""

from datetime import date, datetime, time, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from reporting.models import PipelineStageChange, Schedule
from reporting.views import delivered_schedule_ids


def _noon(day):
    return timezone.make_aware(datetime.combine(day, time(12, 0)), timezone.get_current_timezone())


def collect_rows(week_start):
    week_end = week_start + timedelta(days=7)
    year_start = date(week_start.year, 1, 1)
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(week_start, time.min), tz)
    end = timezone.make_aware(datetime.combine(week_end, time.min), tz)
    cards = Schedule.objects.filter(followup__isnull=False, followup__pipeline_hidden=False).select_related('followup')

    rows = {}

    def add(schedule, from_stage, to_stage, moment, basis):
        key = (schedule.followup_id, to_stage)
        if key not in rows or moment < rows[key]['moment']:
            rows[key] = {
                'followup': schedule.followup, 'from_stage': from_stage, 'to_stage': to_stage,
                'moment': moment, 'basis': f'{basis} #{schedule.id}',
            }

    for schedule in cards.filter(
        activity_type='quote', status='cancelled', updated_at__gte=start, updated_at__lt=end,
        followup__pipeline_stage='lost',
    ):
        add(schedule, 'quote', 'lost', schedule.updated_at, '취소된 견적')

    in_week = cards.filter(visit_date__gte=week_start, visit_date__lt=week_end)
    earlier = cards.filter(visit_date__gte=year_start, visit_date__lt=week_start)

    won_candidates = in_week.filter(followup__pipeline_stage='won')
    delivered_ids = delivered_schedule_ids(won_candidates)
    delivered_before = set(
        Schedule.objects.filter(id__in=delivered_schedule_ids(earlier)).values_list('followup_id', flat=True)
    )
    quoted_this_year = set(
        cards.filter(activity_type='quote', visit_date__gte=year_start, visit_date__lt=week_end)
        .exclude(status='cancelled').values_list('followup_id', flat=True)
    )
    for schedule in won_candidates.filter(id__in=delivered_ids):
        if schedule.followup_id not in delivered_before:
            add(
                schedule, 'quote' if schedule.followup_id in quoted_this_year else 'contact', 'won',
                _noon(schedule.visit_date), '완료 납품',
            )

    quoted_before = set(
        earlier.filter(activity_type='quote', status='completed').values_list('followup_id', flat=True)
    )
    for schedule in in_week.filter(
        activity_type='quote', status='completed', followup__pipeline_stage__in=('quote', 'negotiation'),
    ):
        if schedule.followup_id not in quoted_before:
            add(schedule, 'contact', 'quote', _noon(schedule.visit_date), '완료 견적')

    existing = set(
        PipelineStageChange.objects.filter(
            source=PipelineStageChange.SOURCE_BACKFILL, changed_at__gte=start, changed_at__lt=end,
        ).values_list('followup_id', 'to_stage')
    )
    return [row for key, row in rows.items() if key not in existing]


class Command(BaseCommand):
    help = '기록 이전 한 주의 단계 변경을 일정 근거로 복원한다. --apply 없으면 미리보기만 한다.'

    def add_arguments(self, parser):
        parser.add_argument('--week', required=True, help='복원할 주의 월요일 (YYYY-MM-DD)')
        parser.add_argument('--apply', action='store_true', help='실제로 저장한다')

    def handle(self, *args, **options):
        try:
            week_start = date.fromisoformat(options['week'])
        except ValueError as exc:
            raise CommandError('--week 는 YYYY-MM-DD 형식이어야 합니다.') from exc
        if week_start.weekday() != 0:
            raise CommandError('--week 는 월요일이어야 합니다.')

        rows = sorted(collect_rows(week_start), key=lambda row: row['moment'])
        for row in rows:
            followup = row['followup']
            self.stdout.write(
                f"{timezone.localtime(row['moment']).date()} card={followup.id} {followup.user.username} "
                f"{followup.customer_name} {row['from_stage']}->{row['to_stage']} ({row['basis']})"
            )

        if not options['apply']:
            self.stdout.write(f'미리보기: {len(rows)}건 (저장하지 않음)')
            return

        with transaction.atomic():
            for row in rows:
                change = PipelineStageChange.objects.create(
                    followup=row['followup'], from_stage=row['from_stage'], to_stage=row['to_stage'],
                    source=PipelineStageChange.SOURCE_BACKFILL,
                )
                # changed_at 은 auto_now_add 라 생성 뒤에 실제 시점으로 맞춘다
                PipelineStageChange.objects.filter(pk=change.pk).update(changed_at=row['moment'])
        self.stdout.write(f'저장: {len(rows)}건')
