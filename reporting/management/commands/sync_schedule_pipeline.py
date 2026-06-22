import json

from django.core.management.base import BaseCommand

from reporting.models import Schedule
from reporting.views import _schedule_pipeline_target_stage


class Command(BaseCommand):
    help = 'Synchronize existing schedule states into linked followup pipeline stages.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Persist pipeline stage changes. Without this, the command is a dry-run.',
        )
        parser.add_argument(
            '--schedule-id',
            type=int,
            action='append',
            dest='schedule_ids',
            help='Limit synchronization to one schedule id. Can be passed more than once.',
        )
        parser.add_argument(
            '--followup-id',
            type=int,
            action='append',
            dest='followup_ids',
            help='Limit synchronization to one followup id. Can be passed more than once.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=500,
            help='Maximum number of schedule rows to inspect. Defaults to 500.',
        )
        parser.add_argument(
            '--json',
            action='store_true',
            dest='json_output',
            help='Print a JSON summary instead of human-readable lines.',
        )

    def handle(self, *args, **options):
        apply_changes = bool(options['apply'])
        limit = max(1, int(options['limit'] or 500))

        queryset = (
            Schedule.objects.select_related('followup')
            .filter(
                followup__isnull=False,
                activity_type__in=['customer_meeting', 'quote', 'delivery'],
            )
            .order_by('followup_id', '-updated_at', '-visit_date', '-id')
        )

        if options['schedule_ids']:
            queryset = queryset.filter(id__in=options['schedule_ids'])
        if options['followup_ids']:
            queryset = queryset.filter(followup_id__in=options['followup_ids'])

        inspected = 0
        selected_by_followup = {}
        skipped = []

        for schedule in queryset[:limit]:
            inspected += 1
            if schedule.followup_id in selected_by_followup:
                continue

            target_stage = _schedule_pipeline_target_stage(schedule)
            if not target_stage:
                skipped.append(self._schedule_payload(schedule, 'no_pipeline_target'))
                continue

            selected_by_followup[schedule.followup_id] = (schedule, target_stage)

        changes = []
        already_synced = []

        for followup_id, (schedule, target_stage) in selected_by_followup.items():
            followup = schedule.followup
            current_stage = followup.pipeline_stage or 'potential'
            if current_stage == target_stage and not followup.pipeline_manually_set:
                already_synced.append(self._change_payload(schedule, target_stage, current_stage, applied=False))
                continue

            changes.append(self._change_payload(schedule, target_stage, current_stage, applied=apply_changes))
            if apply_changes:
                followup.pipeline_stage = target_stage
                followup.pipeline_manually_set = False
                followup.save(update_fields=['pipeline_stage', 'pipeline_manually_set'])

        summary = {
            'mode': 'apply' if apply_changes else 'dry_run',
            'inspectedSchedules': inspected,
            'selectedFollowups': len(selected_by_followup),
            'changed': len(changes),
            'alreadySynced': len(already_synced),
            'skipped': len(skipped),
            'changes': changes,
            'alreadySyncedItems': already_synced,
            'skippedItems': skipped,
        }

        if options['json_output']:
            self.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2))
            return

        self.stdout.write(self.style.WARNING(f"Mode: {summary['mode']}"))
        self.stdout.write(
            f"Inspected schedules: {inspected}, selected followups: {len(selected_by_followup)}, "
            f"changes: {len(changes)}, already synced: {len(already_synced)}, skipped: {len(skipped)}"
        )
        for change in changes:
            label = 'applied' if change['applied'] else 'would apply'
            self.stdout.write(
                f"- {label}: schedule #{change['scheduleId']} followup #{change['followupId']} "
                f"{change['fromStage']} -> {change['toStage']}"
            )

    def _schedule_payload(self, schedule, reason):
        return {
            'scheduleId': schedule.id,
            'followupId': schedule.followup_id,
            'activityType': schedule.activity_type,
            'status': schedule.status,
            'reason': reason,
        }

    def _change_payload(self, schedule, target_stage, current_stage, applied):
        return {
            'scheduleId': schedule.id,
            'followupId': schedule.followup_id,
            'activityType': schedule.activity_type,
            'status': schedule.status,
            'fromStage': current_stage,
            'toStage': target_stage,
            'manualFlagWasSet': bool(schedule.followup.pipeline_manually_set),
            'applied': bool(applied),
        }
