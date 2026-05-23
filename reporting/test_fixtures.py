from datetime import time, timedelta
from decimal import Decimal

from django.utils import timezone

from .models import (
    Company,
    DeliveryItem,
    Department,
    FollowUp,
    Prepayment,
    PrepaymentUsage,
    Quote,
    Schedule,
    UserCompany,
)


def create_account_ledger_fixture(owner, *, user_company=None, company=None, department=None, today=None, prefix='ledger'):
    """Create a compact department-account ledger fixture shared by API/AI tests."""
    today = today or timezone.localdate()
    user_company = user_company or UserCompany.objects.create(name=f'{prefix} 소속')
    company = company or Company.objects.create(name=f'{prefix} 업체', created_by=owner)
    department = department or Department.objects.create(name=f'{prefix} 연구실', company=company, created_by=owner)
    primary = FollowUp.objects.create(
        user=owner,
        company=company,
        department=department,
        customer_name=f'{prefix} 담당자 A',
        manager=f'{prefix} 매니저 A',
    )
    sibling = FollowUp.objects.create(
        user=owner,
        company=company,
        department=department,
        customer_name=f'{prefix} 담당자 B',
        manager=f'{prefix} 매니저 B',
    )

    quote_schedule = Schedule.objects.create(
        user=owner,
        company=user_company,
        followup=primary,
        visit_date=today - timedelta(days=12),
        visit_time=time(9, 30),
        activity_type='quote',
        status='completed',
        expected_revenue=Decimal('110000'),
    )
    quote_number = f'{prefix.upper()}-{owner.id}-{Quote.objects.count() + 1}'
    quote = Quote.objects.create(
        quote_number=quote_number,
        schedule=quote_schedule,
        followup=primary,
        user=owner,
        valid_until=today + timedelta(days=30),
        stage='sent',
        subtotal=Decimal('100000'),
        total_amount=Decimal('110000'),
    )

    normal_delivery = Schedule.objects.create(
        user=owner,
        company=user_company,
        followup=primary,
        visit_date=today - timedelta(days=5),
        visit_time=time(10, 0),
        activity_type='delivery',
        status='completed',
        delivery_payment_type=Schedule.DELIVERY_PAYMENT_TYPE_NORMAL,
        delivery_payment_status=Schedule.DELIVERY_PAYMENT_STATUS_NORMAL,
    )
    normal_item = DeliveryItem.objects.create(
        schedule=normal_delivery,
        item_name=f'{prefix} 일반Kit',
        quantity=1,
        unit='EA',
        total_price=Decimal('30000'),
    )

    prepayment = Prepayment.objects.create(
        department=department,
        customer=primary,
        company=company,
        amount=Decimal('100000'),
        balance=Decimal('40000'),
        payment_date=today - timedelta(days=20),
        payer_name=f'{prefix} 입금자',
        created_by=owner,
    )
    prepaid_delivery = Schedule.objects.create(
        user=owner,
        company=user_company,
        followup=sibling,
        visit_date=today - timedelta(days=2),
        visit_time=time(11, 0),
        activity_type='delivery',
        status='completed',
        use_prepayment=True,
        prepayment=prepayment,
        prepayment_amount=Decimal('60000'),
        delivery_payment_type=Schedule.DELIVERY_PAYMENT_TYPE_PREPAYMENT,
        delivery_payment_status=Schedule.DELIVERY_PAYMENT_STATUS_PREPAYMENT,
    )
    prepaid_item = DeliveryItem.objects.create(
        schedule=prepaid_delivery,
        item_name=f'{prefix} 선결제Kit',
        quantity=1,
        unit='EA',
        total_price=Decimal('60000'),
    )
    usage = PrepaymentUsage.objects.create(
        prepayment=prepayment,
        schedule=prepaid_delivery,
        schedule_item=prepaid_item,
        product_name=prepaid_item.item_name,
        quantity=1,
        amount=Decimal('60000'),
        remaining_balance=Decimal('40000'),
        memo='fixture deduction',
    )

    return {
        'user_company': user_company,
        'company': company,
        'department': department,
        'primary': primary,
        'sibling': sibling,
        'quote_schedule': quote_schedule,
        'quote': quote,
        'normal_delivery': normal_delivery,
        'normal_item': normal_item,
        'prepayment': prepayment,
        'prepaid_delivery': prepaid_delivery,
        'prepaid_item': prepaid_item,
        'usage': usage,
    }
