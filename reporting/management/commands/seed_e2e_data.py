import json
import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from reporting.models import (
    Company,
    Department,
    FollowUp,
    PrepaymentLedgerEntry,
    UserCompany,
    UserProfile,
)
from reporting.services.test_fixtures import create_account_ledger_fixture


E2E_PASSWORD = 'E2ePass123!'
E2E_USERNAMES = ('e2e_salesman', 'e2e_manager', 'e2e_admin')
E2E_ORG_NAME = 'E2E Sales Org'
E2E_COMPANY_NAME = 'E2E 서울대병원'
E2E_SOURCE_DEPARTMENT_NAME = 'E2E 원장 연구실'
E2E_TARGET_DEPARTMENT_NAME = 'E2E 원장 Lab'
DEFAULT_OUTPUT = Path('output/e2e/seed.json')


class Command(BaseCommand):
    help = 'Create deterministic browser E2E users and CRM ledger data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            default=str(DEFAULT_OUTPUT),
            help='Path for the JSON file consumed by Playwright tests.',
        )
        parser.add_argument(
            '--allow-production',
            action='store_true',
            help='Allow seeding when production-like environment variables are present.',
        )

    def handle(self, *args, **options):
        if self._looks_like_production() and not options['allow_production']:
            raise CommandError(
                'Refusing to seed E2E data in a production-like environment. '
                'Pass --allow-production only for an explicitly isolated test database.'
            )

        output_path = Path(options['output'])
        payload = self._seed()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(f'E2E seed data written to {output_path}'))

    def _looks_like_production(self):
        if getattr(settings, 'DEBUG', False):
            return False
        return bool(
            os.environ.get('RAILWAY_ENVIRONMENT')
            or os.environ.get('RAILWAY_PROJECT_ID')
            or os.environ.get('RAILWAY_SERVICE_ID')
            or os.environ.get('DATABASE_URL')
        )

    @transaction.atomic
    def _seed(self):
        self._delete_existing_seed()

        User = get_user_model()
        user_company = UserCompany.objects.create(name=E2E_ORG_NAME)
        salesman = self._create_user(
            User,
            user_company,
            username='e2e_salesman',
            role='salesman',
            first_name='E2E',
            last_name='Salesman',
            can_download_excel=False,
        )
        manager = self._create_user(
            User,
            user_company,
            username='e2e_manager',
            role='manager',
            first_name='E2E',
            last_name='Manager',
            can_download_excel=True,
        )
        admin = self._create_user(
            User,
            user_company,
            username='e2e_admin',
            role='admin',
            first_name='E2E',
            last_name='Admin',
            can_download_excel=True,
            is_staff=True,
            is_superuser=True,
        )

        company = Company.objects.create(name=E2E_COMPANY_NAME, created_by=salesman)
        source_department = Department.objects.create(
            company=company,
            name=E2E_SOURCE_DEPARTMENT_NAME,
            address='E2E 테스트시 서울 연구동 101호',
            notes='E2E 계정 상세 회귀 검수용 원장 계정',
            created_by=salesman,
        )
        fixture = create_account_ledger_fixture(
            salesman,
            user_company=user_company,
            company=company,
            department=source_department,
            today=timezone.localdate(),
            prefix='e2eledger',
        )
        self._create_prepayment_ledger_entries(fixture, salesman)

        target_department = Department.objects.create(
            company=company,
            name=E2E_TARGET_DEPARTMENT_NAME,
            address='E2E 테스트시 서울 연구동 102호',
            notes='E2E 데이터 정리 후보 계정',
            created_by=salesman,
        )
        target_contact = FollowUp.objects.create(
            user=salesman,
            user_company=user_company,
            company=company,
            department=target_department,
            customer_name='e2eledger 담당자 C',
            manager='e2eledger 매니저 C',
            contact_role=FollowUp.CONTACT_ROLE_PI,
            priority='followup',
            status='active',
            pipeline_stage='contact',
            email='e2e-contact-c@example.test',
        )

        unassigned_company = Company.objects.create(name='E2E 업체 미지정', created_by=salesman)
        unassigned_department = Department.objects.create(
            company=unassigned_company,
            name='미지정',
            created_by=salesman,
        )
        unassigned_contact = FollowUp.objects.create(
            user=salesman,
            user_company=user_company,
            company=unassigned_company,
            department=unassigned_department,
            customer_name='E2E 미지정 담당자',
            manager='E2E 미지정 PI',
            priority='scheduled',
            status='active',
        )

        return {
            'basePassword': E2E_PASSWORD,
            'users': {
                'salesman': self._user_payload(salesman),
                'manager': self._user_payload(manager),
                'admin': self._user_payload(admin),
            },
            'ids': {
                'customerId': fixture['primary'].id,
                'siblingCustomerId': fixture['sibling'].id,
                'companyId': company.id,
                'departmentId': source_department.id,
                'targetDepartmentId': target_department.id,
                'targetCustomerId': target_contact.id,
                'unassignedCustomerId': unassigned_contact.id,
                'prepaymentId': fixture['prepayment'].id,
                'prepaidDeliveryId': fixture['prepaid_delivery'].id,
            },
            'paths': {
                'customerDetail': f"/customers/{fixture['primary'].id}/",
                'accountDetail': f"/accounts/{source_department.id}/",
                'reports': '/reports/',
                'accountPrepayments': f"/prepayments/account/{source_department.id}/",
                'reportsExcel': '/reporting/api/reports/customer-operations.xlsx',
            },
            'labels': {
                'company': company.name,
                'sourceDepartment': source_department.name,
                'targetDepartment': target_department.name,
                'primaryContact': fixture['primary'].customer_name,
                'siblingContact': fixture['sibling'].customer_name,
                'prepaymentPayer': fixture['prepayment'].payer_name,
                'prepaymentItem': fixture['prepaid_item'].item_name,
            },
        }

    def _delete_existing_seed(self):
        User = get_user_model()
        PrepaymentLedgerEntry.objects.filter(
            Q(metadata__e2e=True) | Q(memo__startswith='E2E seed')
        ).delete()
        User.objects.filter(username__in=E2E_USERNAMES).delete()
        Company.objects.filter(name__startswith='E2E ').delete()
        UserCompany.objects.filter(name=E2E_ORG_NAME).delete()

    def _create_user(
        self,
        User,
        user_company,
        *,
        username,
        role,
        first_name,
        last_name,
        can_download_excel,
        is_staff=False,
        is_superuser=False,
    ):
        user = User.objects.create_user(
            username=username,
            password=E2E_PASSWORD,
            email=f'{username}@example.test',
            first_name=first_name,
            last_name=last_name,
        )
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.save(update_fields=['is_staff', 'is_superuser'])
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                'company': user_company,
                'role': role,
                'can_download_excel': can_download_excel,
                'can_use_ai': role in {'admin', 'manager'},
            },
        )
        return user

    def _create_prepayment_ledger_entries(self, fixture, actor):
        prepayment = fixture['prepayment']
        PrepaymentLedgerEntry.objects.create(
            prepayment=prepayment,
            department=fixture['department'],
            customer=fixture['primary'],
            entry_type=PrepaymentLedgerEntry.ENTRY_DEPOSIT,
            amount=prepayment.amount,
            balance_before=0,
            balance_after=prepayment.amount,
            actor=actor,
            target_user=actor,
            memo='E2E seed deposit',
            metadata={'e2e': True},
        )
        PrepaymentLedgerEntry.objects.create(
            prepayment=prepayment,
            department=fixture['department'],
            customer=fixture['sibling'],
            schedule=fixture['prepaid_delivery'],
            usage=fixture['usage'],
            entry_type=PrepaymentLedgerEntry.ENTRY_DELIVERY_DEDUCTION,
            amount=fixture['usage'].amount,
            balance_before=prepayment.amount,
            balance_after=prepayment.balance,
            actor=actor,
            target_user=actor,
            memo='E2E seed delivery deduction',
            metadata={'e2e': True},
        )

    def _user_payload(self, user):
        return {
            'username': user.username,
            'password': E2E_PASSWORD,
            'id': user.id,
            'displayName': user.get_full_name() or user.username,
        }
