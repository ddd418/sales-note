# Generated by Django 5.2.3 on 2025-06-20 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0014_history_meeting_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='history',
            name='action_type',
            field=models.CharField(choices=[('customer_meeting', '고객 미팅'), ('delivery_schedule', '납품 일정'), ('service', '서비스')], max_length=50, verbose_name='활동 유형'),
        ),
    ]
