"""서비스 메뉴로 옮기기.

1. 아침회의에 적어 둔 서비스 기록(`MeetingServiceRecord`)을 서비스 케이스로 복사한다. 회의 화면은
   이제 서비스 케이스를 보여주므로, 복사하지 않으면 지난 회의 기록이 사라진다. 원본 행은 지우지 않는다.
   회의 기록은 지난 일을 보고한 것이라 '완료', 날짜는 그 주 월요일로 둔다.
2. 예전 장비 연결 케이스는 새 장비·기관 칸을 장비/고객 정보로 채운다(화면이 이 칸을 읽는다).
"""

from django.db import migrations


def forwards(apps, schema_editor):
    MeetingServiceRecord = apps.get_model('reporting', 'MeetingServiceRecord')
    ServiceCase = apps.get_model('reporting', 'ServiceCase')

    for record in MeetingServiceRecord.objects.order_by('week_start', 'position', 'id'):
        content = record.content or ''
        ServiceCase.objects.create(
            institution=record.institution[:100],
            title=content[:200],
            resolution=content if len(content) > 200 else '',
            case_type='service',
            status='completed',
            received_date=record.week_start,
            completed_date=record.week_start,
            assigned_to_id=record.owner_id,
            created_by_id=record.created_by_id or record.owner_id,
            meeting_position=record.position,
        )

    for case in ServiceCase.objects.select_related('asset', 'asset__company', 'followup', 'followup__company'):
        changed = []
        asset = case.asset
        if asset is not None:
            for field, value in (
                ('equipment_name', asset.asset_name),
                ('model_name', asset.model_name),
                ('serial_number', asset.serial_number),
            ):
                if not getattr(case, field) and value:
                    setattr(case, field, value[:case._meta.get_field(field).max_length])
                    changed.append(field)
        if not case.institution:
            company = (asset.company if asset is not None else None) or (case.followup.company if case.followup_id else None)
            if company is not None:
                case.institution = company.name[:100]
                changed.append('institution')
        if changed:
            case.save(update_fields=changed)


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0132_service_menu'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
