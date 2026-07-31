from django.db import migrations


def backfill_won_stage_for_delivered_accounts(apps, schema_editor):
    """실제 납품 기록이 있는 계정을 '수주' 단계로 되돌린다.

    배경: 파이프라인 '수주' 합계가 올해 실제 매출보다 훨씬 낮았다. 원인 둘 —
    (1) 납품이 있어도 카드를 '수주'로 옮기는 유일한 방법이 수동 드래그/동기화
    버튼뿐이라 아무도 안 옮긴 계정이 있었고, (2) 계정당 최근 납품 1건만 집계하는
    계산 버그가 있었다(코드에서 같이 수정). 이 마이그레이션은 (1)의 기존 잔여분을
    바로잡는다. 이후로는 History/Schedule 저장 시 자동으로 '수주'를 반영한다.
    """
    FollowUp = apps.get_model('reporting', 'FollowUp')
    Schedule = apps.get_model('reporting', 'Schedule')
    History = apps.get_model('reporting', 'History')

    followup_ids = set(
        Schedule.objects.filter(
            activity_type='delivery', status='completed', followup_id__isnull=False,
        ).values_list('followup_id', flat=True)
    )
    followup_ids |= set(
        History.objects.filter(
            action_type='delivery_schedule', followup_id__isnull=False,
        ).values_list('followup_id', flat=True)
    )

    department_ids = set(
        Schedule.objects.filter(
            activity_type='delivery', status='completed',
            followup_id__isnull=True, department_id__isnull=False,
        ).values_list('department_id', flat=True)
    )
    department_ids |= set(
        History.objects.filter(
            action_type='delivery_schedule',
            followup_id__isnull=True, department_id__isnull=False,
        ).values_list('department_id', flat=True)
    )
    if department_ids:
        followup_ids |= set(
            FollowUp.objects.filter(department_id__in=department_ids).values_list('id', flat=True)
        )

    if followup_ids:
        FollowUp.objects.filter(id__in=followup_ids).exclude(pipeline_stage='won').update(
            pipeline_stage='won', pipeline_manually_set=False,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0121_reset_auto_contact_stage_to_potential'),
    ]

    operations = [
        migrations.RunPython(backfill_won_stage_for_delivered_accounts, migrations.RunPython.noop),
    ]
