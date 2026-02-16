from django.db import migrations


def migrate_meeting_content_forward(apps, schema_editor):
    """기존 고객 미팅 히스토리의 content를 meeting_situation으로 복사"""
    History = apps.get_model('reporting', 'History')
    meetings = History.objects.filter(
        action_type='customer_meeting',
        meeting_situation__isnull=True,
    ).exclude(content__isnull=True).exclude(content='')
    
    for h in meetings:
        h.meeting_situation = h.content
        h.save(update_fields=['meeting_situation'])


def migrate_meeting_content_reverse(apps, schema_editor):
    """되돌리기: meeting_situation을 다시 content로"""
    History = apps.get_model('reporting', 'History')
    meetings = History.objects.filter(
        action_type='customer_meeting',
        meeting_situation__isnull=False,
    ).exclude(meeting_situation='')
    
    for h in meetings:
        if not h.content:
            h.content = h.meeting_situation
            h.save(update_fields=['content'])


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0084_add_structured_meeting_notes'),
    ]

    operations = [
        migrations.RunPython(
            migrate_meeting_content_forward,
            migrate_meeting_content_reverse,
        ),
    ]
