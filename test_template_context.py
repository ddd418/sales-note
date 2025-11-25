import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sales_project.settings')
django.setup()

from reporting.models import EmailLog
from django.template import Template, Context

email = EmailLog.objects.get(id=96)

# 템플릿 컨텍스트 테스트
print("=== 템플릿 컨텍스트 테스트 ===")
print(f"original_email.schedule: {email.schedule}")
print(f"original_email.schedule.followup: {email.schedule.followup if email.schedule else 'N/A'}")

if email.schedule and email.schedule.followup:
    print(f"original_email.schedule.followup.customer_name: {email.schedule.followup.customer_name}")
    print(f"original_email.schedule.followup.company.name: {email.schedule.followup.company.name if email.schedule.followup.company else 'N/A'}")

print(f"\noriginal_email.followup: {email.followup}")
if email.followup:
    print(f"original_email.followup.customer_name: {email.followup.customer_name}")
    print(f"original_email.followup.company.name: {email.followup.company.name if email.followup.company else 'N/A'}")

# Django 템플릿 렌더링 테스트
template_str = """
Customer Name (schedule.followup): {% if original_email.schedule.followup %}{{ original_email.schedule.followup.customer_name|default:"EMPTY" }}{% else %}NO_SCHEDULE_FOLLOWUP{% endif %}
Company Name (schedule.followup): {% if original_email.schedule.followup %}{{ original_email.schedule.followup.company.name|default:"EMPTY" }}{% else %}NO_SCHEDULE_FOLLOWUP{% endif %}

Customer Name (followup): {% if original_email.followup %}{{ original_email.followup.customer_name|default:"EMPTY" }}{% else %}NO_FOLLOWUP{% endif %}
Company Name (followup): {% if original_email.followup %}{{ original_email.followup.company.name|default:"EMPTY" }}{% else %}NO_FOLLOWUP{% endif %}
"""

template = Template(template_str)
context = Context({'original_email': email})
rendered = template.render(context)

print("\n=== 템플릿 렌더링 결과 ===")
print(rendered)
