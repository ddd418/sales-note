# 장비 "모델" 칸을 "브랜드"로 바꾼다(사용자 요청). 이미 적은 값은 그대로 옮긴다.
# "판단" 칸 이름도 "점검 결과"로(표시 이름만, DB 변화 없음).
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0135_service_part_product'),
    ]

    operations = [
        migrations.RenameField(model_name='servicecase', old_name='model_name', new_name='brand'),
        migrations.AlterField(
            model_name='servicecase',
            name='brand',
            field=models.CharField(blank=True, max_length=200, verbose_name='브랜드'),
        ),
        migrations.RenameField(model_name='serviceequipment', old_name='model_name', new_name='brand'),
        migrations.AlterField(
            model_name='serviceequipment',
            name='brand',
            field=models.CharField(blank=True, max_length=200, verbose_name='브랜드'),
        ),
        migrations.AlterField(
            model_name='servicecase',
            name='diagnosis',
            field=models.TextField(blank=True, verbose_name='점검 결과'),
        ),
    ]
