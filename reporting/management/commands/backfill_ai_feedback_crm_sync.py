import json

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from reporting.models import AIWorkspaceActionFeedback
from reporting.views import (
    _ai_workspace_apply_crm_state_sync,
    _ai_workspace_empty_crm_sync,
    _ai_workspace_feedback_fallback,
    _ai_workspace_feedback_status_from_result,
    _ai_workspace_normalize_feedback_result,
    get_user_profile,
)


class Command(BaseCommand):
    help = (
        "Backfill CRM state synchronization for legacy AI workspace feedback "
        "records that were created before ai_result.intent/crmSync existed."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Persist CRM state changes and ai_result.crmSync. Without this, the command is a dry-run.',
        )
        parser.add_argument(
            '--feedback-id',
            type=int,
            action='append',
            dest='feedback_ids',
            help='Limit processing to one feedback id. Can be passed more than once.',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            action='append',
            dest='user_ids',
            help='Limit processing to one user id. Can be passed more than once.',
        )
        parser.add_argument(
            '--status',
            action='append',
            dest='statuses',
            choices=['answered', 'next_action', 'resolved', 'dismissed'],
            help='Limit processing to a feedback status. Defaults to answered, next_action, resolved.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=200,
            help='Maximum number of candidate feedback rows to inspect. Defaults to 200.',
        )
        parser.add_argument(
            '--include-synced',
            action='store_true',
            help='Also inspect rows that already have both intent and crmSync.',
        )
        parser.add_argument(
            '--json',
            action='store_true',
            dest='json_output',
            help='Print a JSON summary instead of human-readable lines.',
        )

    def handle(self, *args, **options):
        apply_changes = options['apply']
        limit = max(1, int(options['limit'] or 200))
        statuses = options['statuses'] or ['answered', 'next_action', 'resolved']

        queryset = AIWorkspaceActionFeedback.objects.select_related(
            'user',
            'followup',
            'history',
            'followup__company',
            'followup__department',
        ).filter(status__in=statuses).order_by('created_at', 'id')

        if options['feedback_ids']:
            queryset = queryset.filter(id__in=options['feedback_ids'])
        if options['user_ids']:
            queryset = queryset.filter(user_id__in=options['user_ids'])

        inspected = 0
        processed = []
        skipped = []

        for feedback in queryset[:limit]:
            inspected += 1
            result = feedback.ai_result or {}
            if (
                not options['include_synced']
                and result.get('intent')
                and result.get('crmSync')
            ):
                skipped.append(self._skip_payload(feedback, 'already_synced'))
                continue

            action = self._action_from_feedback(feedback)
            if not action.get('followupId'):
                skipped.append(self._skip_payload(feedback, 'missing_followup'))
                continue

            normalized = self._normalized_result(feedback, action)
            if normalized.get('intent') == 'needs_human_review':
                crm_sync = _ai_workspace_empty_crm_sync(normalized.get('intent'))
                crm_sync['message'] = '검토 필요로 분류되어 CRM 상태는 자동 변경하지 않았습니다.'
                processed.append(self._processed_payload(feedback, normalized, crm_sync, apply_changes))
                if apply_changes:
                    self._save_feedback_result(feedback, normalized, crm_sync)
                continue

            if apply_changes:
                with transaction.atomic():
                    crm_sync = _ai_workspace_apply_crm_state_sync(
                        feedback.user,
                        get_user_profile(feedback.user),
                        action,
                        feedback.feedback,
                        normalized,
                    )
                    self._save_feedback_result(feedback, normalized, crm_sync)
            else:
                with transaction.atomic():
                    crm_sync = _ai_workspace_apply_crm_state_sync(
                        feedback.user,
                        get_user_profile(feedback.user),
                        action,
                        feedback.feedback,
                        normalized,
                    )
                    transaction.set_rollback(True)

            processed.append(self._processed_payload(feedback, normalized, crm_sync, apply_changes))

        summary = {
            'mode': 'apply' if apply_changes else 'dry_run',
            'inspected': inspected,
            'processed': len(processed),
            'skipped': len(skipped),
            'processedItems': processed,
            'skippedItems': skipped,
        }

        if options['json_output']:
            self.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2))
            return

        self.stdout.write(self.style.WARNING(f"Mode: {summary['mode']}"))
        self.stdout.write(f"Inspected: {inspected}, processed: {len(processed)}, skipped: {len(skipped)}")
        for item in processed:
            self.stdout.write(
                f"- feedback #{item['feedbackId']} {item['actionId']} "
                f"intent={item['intent']} status={item['status']} "
                f"applied={item['crmSync'].get('applied')} changes={len(item['crmSync'].get('changes', []))}"
            )
            message = item['crmSync'].get('message')
            if message:
                self.stdout.write(f"  message: {message}")
            for change in item['crmSync'].get('changes', [])[:8]:
                self.stdout.write(
                    f"  * {change.get('label')} "
                    f"{change.get('objectType')}#{change.get('objectId')} "
                    f"{change.get('detail') or ''}"
                )
        for item in skipped:
            self.stdout.write(f"- skipped feedback #{item['feedbackId']} {item['actionId']}: {item['reason']}")

    def _action_from_feedback(self, feedback):
        action = dict(feedback.action_snapshot or {})
        followup = feedback.followup
        action_id = action.get('id') or feedback.action_id

        action['id'] = action_id
        action['kind'] = action.get('kind') or feedback.action_kind or ''
        action['kindLabel'] = action.get('kindLabel') or feedback.action_kind or 'AI 추천 액션'
        action['followupId'] = action.get('followupId') or feedback.followup_id

        if followup:
            customer = followup.customer_name or followup.manager or '고객'
            company = followup.company.name if followup.company_id else ''
            department = followup.department.name if followup.department_id else ''
            action['customer'] = action.get('customer') or customer
            action['company'] = action.get('company') or company
            action['department'] = action.get('department') or department
            action['title'] = action.get('title') or f"{customer} AI 추천 실행"

        action['recommendedAction'] = action.get('recommendedAction') or ''
        action['hrefs'] = action.get('hrefs') or {}
        action['evidence'] = action.get('evidence') or []
        action['feedback'] = action.get('feedback') or None
        return action

    def _normalized_result(self, feedback, action):
        existing = dict(feedback.ai_result or {})
        fallback = _ai_workspace_feedback_fallback(action, feedback.feedback)
        status_hint = existing.get('recommendedStatus') or existing.get('status') or feedback.status
        normalized = _ai_workspace_normalize_feedback_result(
            {
                **existing,
                'status': status_hint,
                'recommendedStatus': status_hint,
            },
            fallback,
        )
        return {
            **existing,
            **normalized,
            'source': existing.get('source') or 'legacy_backfill',
        }

    def _save_feedback_result(self, feedback, normalized, crm_sync):
        next_result = {
            **(feedback.ai_result or {}),
            **normalized,
            'crmSync': crm_sync,
            'backfilledAt': timezone.now().isoformat(),
            'backfillCommand': 'backfill_ai_feedback_crm_sync',
        }
        next_status = _ai_workspace_feedback_status_from_result(next_result)
        feedback.ai_result = next_result
        feedback.status = next_status
        if next_status in {'resolved', 'dismissed'} and not feedback.resolved_at:
            feedback.resolved_at = timezone.now()
        feedback.save(update_fields=['ai_result', 'status', 'resolved_at', 'updated_at'])

    def _processed_payload(self, feedback, normalized, crm_sync, applied):
        return {
            'feedbackId': feedback.id,
            'actionId': feedback.action_id,
            'followupId': feedback.followup_id,
            'historyId': feedback.history_id,
            'status': _ai_workspace_feedback_status_from_result(normalized),
            'intent': normalized.get('intent'),
            'appliedMode': applied,
            'crmSync': crm_sync,
        }

    def _skip_payload(self, feedback, reason):
        return {
            'feedbackId': feedback.id,
            'actionId': feedback.action_id,
            'followupId': feedback.followup_id,
            'historyId': feedback.history_id,
            'reason': reason,
        }
