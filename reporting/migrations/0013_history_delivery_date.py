# Generated by Django 5.2.3 on 2025-06-18 02:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0012_history_delivery_items'),
    ]

    operations = [
        migrations.AddField(
            model_name='history',
            name='delivery_date',
            field=models.DateField(blank=True, help_text='납품 일정인 경우 실제 납품 날짜를 입력하세요', null=True, verbose_name='납품 날짜'),
        ),
    ]
