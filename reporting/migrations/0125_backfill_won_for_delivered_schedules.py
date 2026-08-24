from django.db import migrations


def backfill_won_for_delivered_accounts(apps, schema_editor):
    """납품이 확인된 계정을 다시 '수주'로 맞춘다.

    0122 에서 한 번 백필했지만 그 뒤로 다시 어긋난 계정이 생겼다(운영 확인:
    접촉/미팅 단계에 565만원, 숨긴 협상 카드에 112만원어치 납품이 있었다).
    원인은 (1) 자동 전환 시그널이 History 저장에만 걸려 있어 **일정으로만**
    기록한 납품을 놓쳤고, (2) 카드를 수동으로 앞 단계로 옮기면 되돌릴 장치가
    없었기 때문이다. (1)은 Schedule 저장 시그널을 추가해 막았고, 이 마이그레이션은
    그동안 쌓인 잔여분을 정리한다.

    '견적' 일정에 품목을 넣고 납품노트를 달아 출고한 건도 납품으로 본다
    (운영 데이터에 실제로 있는 형태).
    """
    FollowUp = apps.get_model('reporting', 'FollowUp')
    Schedule = apps.get_model('reporting', 'Schedule')
    History = apps.get_model('reporting', 'History')

    delivered_followup_ids = set(
        Schedule.objects.filter(
            activity_type='delivery', status='completed', followup_id__isnull=False,
        ).values_list('followup_id', flat=True)
    )
    delivered_followup_ids |= set(
        History.objects.filter(
            action_type='delivery_schedule', followup_id__isnull=False,
        ).values_list('followup_id', flat=True)
    )

    delivered_department_ids = set(
        Schedule.objects.filter(
            activity_type='delivery', status='completed',
            followup_id__isnull=True, department_id__isnull=False,
        ).values_list('department_id', flat=True)
    )
    delivered_department_ids |= set(
        History.objects.filter(
            action_type='delivery_schedule',
            followup_id__isnull=True, department_id__isnull=False,
        ).values_list('department_id', flat=True)
    )
    if delivered_department_ids:
        delivered_followup_ids |= set(
            FollowUp.objects.filter(
                department_id__in=delivered_department_ids,
            ).values_list('id', flat=True)
        )

    delivered_followup_ids.discard(None)
    if not delivered_followup_ids:
        return

    FollowUp.objects.filter(
        id__in=delivered_followup_ids,
    ).exclude(pipeline_stage='won').update(
        pipeline_stage='won', pipeline_manually_set=False,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0124_followup_pipeline_probability_override'),
    ]

    operations = [
        migrations.RunPython(backfill_won_for_delivered_accounts, migrations.RunPython.noop),
    ]
