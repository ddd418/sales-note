# Generated manually for performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0054_update_funnel_stages'),
    ]

    operations = [
        # UserProfile 최적화 인덱스
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['company'], name='userprofile_company_idx'),
        ),
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['role'], name='userprofile_role_idx'),
        ),
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['company', 'role'], name='userprofile_company_role_idx'),
        ),
        
        # UserCompany 최적화 인덱스
        migrations.AddIndex(
            model_name='usercompany',
            index=models.Index(fields=['name'], name='usercompany_name_idx'),
        ),
        
        # Company (고객사) 최적화 인덱스
        migrations.AddIndex(
            model_name='company',
            index=models.Index(fields=['name'], name='company_name_idx'),
        ),
        migrations.AddIndex(
            model_name='company',
            index=models.Index(fields=['created_by'], name='company_created_by_idx'),
        ),
        
        # Department 최적화 인덱스
        migrations.AddIndex(
            model_name='department',
            index=models.Index(fields=['company', 'name'], name='department_company_name_idx'),
        ),
        
        # FollowUp 최적화 인덱스
        migrations.AddIndex(
            model_name='followup',
            index=models.Index(fields=['user', 'status'], name='followup_user_status_idx'),
        ),
        migrations.AddIndex(
            model_name='followup',
            index=models.Index(fields=['user_company'], name='followup_user_company_idx'),
        ),
        migrations.AddIndex(
            model_name='followup',
            index=models.Index(fields=['company'], name='followup_company_idx'),
        ),
        migrations.AddIndex(
            model_name='followup',
            index=models.Index(fields=['created_at'], name='followup_created_at_idx'),
        ),
        
        # Schedule 최적화 인덱스 (가장 중요!)
        migrations.AddIndex(
            model_name='schedule',
            index=models.Index(fields=['visit_date', 'status'], name='schedule_date_status_idx'),
        ),
        migrations.AddIndex(
            model_name='schedule',
            index=models.Index(fields=['user', 'visit_date'], name='schedule_user_date_idx'),
        ),
        migrations.AddIndex(
            model_name='schedule',
            index=models.Index(fields=['activity_type', 'status'], name='schedule_type_status_idx'),
        ),
        migrations.AddIndex(
            model_name='schedule',
            index=models.Index(fields=['company'], name='schedule_company_idx'),
        ),
        
        # History 최적화 인덱스
        migrations.AddIndex(
            model_name='history',
            index=models.Index(fields=['user', 'created_at'], name='history_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='history',
            index=models.Index(fields=['action_type', 'created_at'], name='history_type_created_idx'),
        ),
        migrations.AddIndex(
            model_name='history',
            index=models.Index(fields=['company'], name='history_company_idx'),
        ),
        
        # DeliveryItem 최적화 인덱스
        migrations.AddIndex(
            model_name='deliveryitem',
            index=models.Index(fields=['schedule'], name='deliveryitem_schedule_idx'),
        ),
        migrations.AddIndex(
            model_name='deliveryitem',
            index=models.Index(fields=['history'], name='deliveryitem_history_idx'),
        ),
        migrations.AddIndex(
            model_name='deliveryitem',
            index=models.Index(fields=['product'], name='deliveryitem_product_idx'),
        ),
        
        # OpportunityTracking 최적화 인덱스
        migrations.AddIndex(
            model_name='opportunitytracking',
            index=models.Index(fields=['followup', 'current_stage'], name='opportunity_followup_stage_idx'),
        ),
        migrations.AddIndex(
            model_name='opportunitytracking',
            index=models.Index(fields=['current_stage'], name='opportunity_stage_idx'),
        ),
    ]
