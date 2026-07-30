from django.db import migrations


def reset_contact_stage_to_potential(apps, schema_editor):
    """'접촉/미팅' 자동 채움을 중단하면서, 자동으로 채워졌던 카드를 원상복구한다.

    사용자 확인: 수동으로 옮겼던 카드(pipeline_manually_set=True)를 포함해
    현재 '접촉/미팅' 단계에 있는 카드 전부를 '잠재'로 되돌린다.
    """
    FollowUp = apps.get_model('reporting', 'FollowUp')
    FollowUp.objects.filter(pipeline_stage='contact').update(
        pipeline_stage='potential', pipeline_manually_set=False,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0120_followup_pipeline_hidden'),
    ]

    operations = [
        migrations.RunPython(reset_contact_stage_to_potential, migrations.RunPython.noop),
    ]
