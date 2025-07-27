from django.core.management.base import BaseCommand
from django.db import transaction
from reporting.models import Schedule, History


class Command(BaseCommand):
    help = 'Fix activity_type values: meeting -> customer_meeting, delivery_schedule -> delivery'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually making changes',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to make the changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        confirm = options['confirm']

        if not dry_run and not confirm:
            self.stdout.write(
                self.style.ERROR(
                    'You must use either --dry-run to preview changes or --confirm to apply them'
                )
            )
            return

        # Schedule 모델의 activity_type 수정
        self.stdout.write('\n=== Schedule 모델 activity_type 수정 ===')
        
        # meeting -> customer_meeting
        meeting_schedules = Schedule.objects.filter(activity_type='meeting')
        meeting_count = meeting_schedules.count()
        self.stdout.write(f'meeting -> customer_meeting: {meeting_count}개')
        
        if meeting_count > 0:
            for schedule in meeting_schedules:
                self.stdout.write(f'  - ID {schedule.id}: {schedule.followup.customer_name if schedule.followup else "No customer"} ({schedule.visit_date})')
        
        # delivery_schedule -> delivery  
        delivery_schedule_schedules = Schedule.objects.filter(activity_type='delivery_schedule')
        delivery_schedule_count = delivery_schedule_schedules.count()
        self.stdout.write(f'delivery_schedule -> delivery: {delivery_schedule_count}개')
        
        if delivery_schedule_count > 0:
            for schedule in delivery_schedule_schedules:
                self.stdout.write(f'  - ID {schedule.id}: {schedule.followup.customer_name if schedule.followup else "No customer"} ({schedule.visit_date})')

        # History 모델의 action_type 수정
        self.stdout.write('\n=== History 모델 action_type 수정 ===')
        
        # meeting -> customer_meeting
        meeting_histories = History.objects.filter(action_type='meeting')
        meeting_history_count = meeting_histories.count()
        self.stdout.write(f'meeting -> customer_meeting: {meeting_history_count}개')
        
        if meeting_history_count > 0:
            for history in meeting_histories[:10]:  # 처음 10개만 표시
                self.stdout.write(f'  - ID {history.id}: {history.followup.customer_name if history.followup else "No customer"} ({history.created_at.date()})')
            if meeting_history_count > 10:
                self.stdout.write(f'  ... 그 외 {meeting_history_count - 10}개 더')

        total_changes = meeting_count + delivery_schedule_count + meeting_history_count
        self.stdout.write(f'\n총 {total_changes}개의 레코드가 변경될 예정입니다.')

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\n[DRY RUN] 실제 변경은 하지 않았습니다. 실제 적용하려면 --confirm 옵션을 사용하세요.'
                )
            )
            return

        if not confirm:
            return

        # 실제 변경 작업
        self.stdout.write('\n실제 변경 작업을 시작합니다...')
        
        try:
            with transaction.atomic():
                # Schedule 모델 업데이트
                if meeting_count > 0:
                    meeting_schedules.update(activity_type='customer_meeting')
                    self.stdout.write(f'✓ Schedule: meeting -> customer_meeting ({meeting_count}개 완료)')
                
                if delivery_schedule_count > 0:
                    delivery_schedule_schedules.update(activity_type='delivery')
                    self.stdout.write(f'✓ Schedule: delivery_schedule -> delivery ({delivery_schedule_count}개 완료)')
                
                # History 모델 업데이트
                if meeting_history_count > 0:
                    meeting_histories.update(action_type='customer_meeting')
                    self.stdout.write(f'✓ History: meeting -> customer_meeting ({meeting_history_count}개 완료)')
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n모든 변경 작업이 완료되었습니다! 총 {total_changes}개 레코드가 업데이트되었습니다.'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'오류가 발생했습니다: {str(e)}'
                )
            )
            raise

        # 최종 확인
        self.stdout.write('\n=== 최종 확인 ===')
        final_meeting_schedules = Schedule.objects.filter(activity_type='meeting').count()
        final_meeting_histories = History.objects.filter(action_type='meeting').count()
        
        if final_meeting_schedules == 0 and final_meeting_histories == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    '✓ 모든 "meeting" 값이 "customer_meeting"으로 성공적으로 변경되었습니다!'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'아직 남은 meeting 값: Schedule {final_meeting_schedules}개, History {final_meeting_histories}개'
                )
            )

        # 현재 activity_type 분포 출력
        self.stdout.write('\n=== 현재 activity_type 분포 ===')
        schedule_types = Schedule.objects.values_list('activity_type', flat=True).distinct()
        history_types = History.objects.values_list('action_type', flat=True).distinct()
        
        self.stdout.write(f'Schedule activity_type: {list(schedule_types)}')
        self.stdout.write(f'History action_type: {list(history_types)}')
