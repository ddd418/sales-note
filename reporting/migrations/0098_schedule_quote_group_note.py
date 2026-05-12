from django.db import migrations, models
import django.db.models.deletion


def copy_legacy_quote_extra_notes(apps, schema_editor):
    Schedule = apps.get_model('reporting', 'Schedule')
    ScheduleQuoteGroupNote = apps.get_model('reporting', 'ScheduleQuoteGroupNote')
    schedules = Schedule.objects.exclude(quote_extra_notes__isnull=True).exclude(quote_extra_notes='')
    for schedule in schedules.iterator():
        ScheduleQuoteGroupNote.objects.get_or_create(
            schedule_id=schedule.id,
            quote_group='',
            defaults={'notes': schedule.quote_extra_notes},
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0097_quote_document_groups'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduleQuoteGroupNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quote_group', models.CharField(blank=True, default='', max_length=100, verbose_name='견적서 구분')),
                ('notes', models.TextField(blank=True, default='', verbose_name='견적 기타사항')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='수정일')),
                ('schedule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quote_group_notes', to='reporting.schedule', verbose_name='일정')),
            ],
            options={
                'verbose_name': '견적서 구분별 기타사항',
                'verbose_name_plural': '견적서 구분별 기타사항',
                'unique_together': {('schedule', 'quote_group')},
            },
        ),
        migrations.AddIndex(
            model_name='schedulequotegroupnote',
            index=models.Index(fields=['schedule', 'quote_group'], name='schedule_quote_note_idx'),
        ),
        migrations.RunPython(copy_legacy_quote_extra_notes, noop_reverse),
    ]
