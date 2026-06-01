from django.db import migrations


def normalize_probability(value):
    if value is None:
        return None
    value = int(value)
    value = max(0, min(100, value))
    return max(0, min(100, ((value + 2) // 5) * 5))


def normalize_meeting_probability_values(apps, schema_editor):
    Schedule = apps.get_model('reporting', 'Schedule')

    schedules = []
    for schedule in Schedule.objects.filter(
        activity_type='customer_meeting',
    ).exclude(
        probability__isnull=True,
    ).only('id', 'probability'):
        normalized = normalize_probability(schedule.probability)
        if normalized != schedule.probability:
            schedule.probability = normalized
            schedules.append(schedule)

    if schedules:
        Schedule.objects.bulk_update(schedules, ['probability'])


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0116_normalize_probability_to_five_percent'),
    ]

    operations = [
        migrations.RunPython(normalize_meeting_probability_values, migrations.RunPython.noop),
    ]
