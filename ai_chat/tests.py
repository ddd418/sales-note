from datetime import date, timedelta
import json
import sys
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from reporting.models import Company, Department, FollowUp, UserProfile

from .models import AIDepartmentAnalysis, PainPointCard
from .department_prompt import (
    build_prompt_from_department_analysis,
    suggest_goals,
    suggest_goals_from_department_analysis,
)


def make_ai_user(username, can_use_ai):
    user = User.objects.create_user(username=username, password='TestPass123!')
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.can_use_ai = can_use_ai
    profile.role = 'salesman'
    profile.save(update_fields=['can_use_ai', 'role'])
    return user


def make_department_with_followup(user, company_name='테스트 고객사', department_name='영업팀'):
    company = Company.objects.create(name=company_name, created_by=user)
    department = Department.objects.create(company=company, name=department_name, created_by=user)
    FollowUp.objects.create(
        user=user,
        company=company,
        department=department,
        customer_name='테스트 고객',
    )
    return company, department


def make_department_analysis(user, department):
    analysis = AIDepartmentAnalysis.objects.create(
        user=user,
        department=department,
        analysis_data={
            'department_summary': '최근 견적 문의가 늘었지만 후속 연락이 지연되고 있습니다.',
            'meeting_insights': [
                {
                    'theme': '후속 일정 증가',
                    'details': '최근 미팅에서 후속 확인 요청이 반복되었습니다.',
                    'frequency': '3건',
                }
            ],
            'quote_delivery_insights': {
                'conversion_analysis': '견적 후 납품 전환율이 낮아 확인 연락이 필요합니다.',
                'stalled_quotes': [
                    {
                        'quote_info': '미전환 견적',
                        'possible_reason': '고객 의사결정 일정 확인 필요',
                        'suggestion': '견적 후속 연락을 우선 진행',
                    }
                ],
            },
            'next_actions': [
                {
                    'action': '견적 대기 고객에게 후속 연락',
                    'priority': 'high',
                    'reason': '전환되지 않은 견적이 있기 때문입니다.',
                }
            ],
            'missing_info': {
                'items': ['의사결정 예정일'],
                'questions': ['구매 결정 기준은 무엇인가요?'],
            },
        },
        quote_delivery_data={
            'total_quotes': 4,
            'converted_quotes': 1,
            'conversion_rate': 25.0,
            'total_deliveries': 1,
            'avg_delivery_interval_days': 45,
            'product_stats': {
                'TEST-PRODUCT': {
                    'quoted': 2,
                    'delivered': 1,
                    'quote_amount': 1000000,
                    'delivery_amount': 500000,
                }
            },
        },
        meeting_count=3,
        quote_count=4,
        delivery_count=1,
        analysis_period_start=date(2026, 4, 1),
        analysis_period_end=date(2026, 5, 1),
    )
    PainPointCard.objects.create(
        analysis=analysis,
        category='delivery',
        hypothesis='견적 대기 고객의 후속 연락 지연이 핵심 문제입니다.',
        confidence='high',
        confidence_score=82,
        evidence=[],
        attribution='lab',
        verification_question='견적 검토 일정은 언제인가요?',
        action_if_yes='후속 연락 전략을 세웁니다.',
        action_if_no='다음 의사결정 기준을 확인합니다.',
    )
    return analysis


class AIDepartmentPromptLogicTests(TestCase):
    def test_suggest_goals_uses_department_defaults(self):
        goals = suggest_goals('마케팅팀')

        self.assertIn('캠페인 아이디어 도출', goals)
        self.assertIn('경쟁사 비교 자료 작성', goals)

    def test_suggest_goals_prioritizes_keywords(self):
        goals = suggest_goals('영업팀', situation='견적 요청 후 후속 연락이 지연됨')

        self.assertEqual(goals[0], '견적 후속 전략 작성')
        self.assertIn('후속 연락 스크립트 작성', goals[:3])

    def test_department_analysis_goal_cards_use_painpoint_first(self):
        user = make_ai_user('analysis_goal_user', can_use_ai=True)
        _, department = make_department_with_followup(user)
        analysis = make_department_analysis(user, department)

        goals = suggest_goals_from_department_analysis(analysis)

        self.assertEqual(goals[0]['title'], '견적 후속 연락 전략 작성')
        self.assertIn('추천 이유', f"추천 이유: {goals[0]['reason']}")

    def test_build_prompt_from_department_analysis_uses_custom_goal_and_sanitizes(self):
        user = make_ai_user('analysis_prompt_user', can_use_ai=True)
        _, department = make_department_with_followup(user)
        analysis = make_department_analysis(user, department)
        analysis.analysis_data['department_summary'] = '담당자 test@example.com, 010-1234-5678, 1,000,000원 확인 필요'
        analysis.save(update_fields=['analysis_data'])

        prompt = build_prompt_from_department_analysis(
            analysis,
            selected_goal='고객 우선순위 정리',
            custom_goal='이번 주 팀장 보고용 요약을 만들고 싶다',
        )

        self.assertIn('이번 주 팀장 보고용 요약을 만들고 싶다', prompt)
        self.assertIn('보고서 목차', prompt)
        self.assertIn('[이메일 제거]', prompt)
        self.assertIn('[연락처 제거]', prompt)
        self.assertIn('[금액 제거]', prompt)


class AIDepartmentQuoteDeliveryCollectionTests(TestCase):
    def test_department_analysis_collects_schedule_quote_and_delivery_items(self):
        from datetime import time
        from decimal import Decimal
        from reporting.models import DeliveryItem, History, Schedule
        from .services import gather_quote_delivery_data

        user = make_ai_user('ai_qd_schedule_user', can_use_ai=True)
        _company, department = make_department_with_followup(user)
        followup = FollowUp.objects.get(user=user, department=department)

        quote_schedule = Schedule.objects.create(
            user=user,
            followup=followup,
            visit_date=date(2026, 5, 11),
            visit_time=time(10, 0),
            activity_type='quote',
            status='completed',
            notes='견적서 전달 완료',
        )
        DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='견적용 피펫',
            quantity=2,
            unit_price=Decimal('100000'),
        )
        delivery_schedule = Schedule.objects.create(
            user=user,
            followup=followup,
            visit_date=date(2026, 5, 12),
            visit_time=time(11, 0),
            activity_type='delivery',
            status='completed',
            notes='납품 완료',
        )
        DeliveryItem.objects.create(
            schedule=delivery_schedule,
            item_name='납품용 팁',
            quantity=3,
            unit_price=Decimal('50000'),
        )
        History.objects.create(
            user=user,
            followup=followup,
            schedule=delivery_schedule,
            action_type='delivery_schedule',
            content='납품 히스토리 동기화',
        )

        data = gather_quote_delivery_data(department, user)

        self.assertEqual(data['summary']['total_quotes'], 1)
        self.assertEqual(data['summary']['total_deliveries'], 1)
        self.assertEqual(data['quotes'][0]['source'], '견적 일정')
        self.assertEqual(data['quotes'][0]['total_amount'], 220000)
        self.assertEqual(data['quotes'][0]['items'][0]['product'], '견적용 피펫')
        self.assertEqual(data['deliveries'][0]['source'], '납품 활동')
        self.assertEqual(data['deliveries'][0]['amount'], 165000)
        self.assertEqual(data['deliveries'][0]['items'][0]['product'], '납품용 팁')
        self.assertEqual(data['summary']['product_stats']['견적용 피펫']['quote_amount'], 220000)
        self.assertEqual(data['summary']['product_stats']['납품용 팁']['delivery_amount'], 165000)

    def test_department_analysis_meetings_include_all_department_followups(self):
        from reporting.models import History
        from .services import analyze_department, gather_meeting_data

        user = make_ai_user('ai_department_all_meetings_user', can_use_ai=True)
        company, department = make_department_with_followup(user)
        own_followup = FollowUp.objects.get(user=user, department=department)
        coworker = make_ai_user('ai_department_coworker_user', can_use_ai=True)
        coworker_followup = FollowUp.objects.create(
            user=coworker,
            company=company,
            department=department,
            customer_name='동료 담당 고객',
        )
        History.objects.create(
            user=user,
            followup=own_followup,
            action_type='customer_meeting',
            content='내 담당 미팅 내용',
        )
        History.objects.create(
            user=coworker,
            followup=coworker_followup,
            action_type='customer_meeting',
            content='동료 담당 미팅 내용',
        )

        meetings = gather_meeting_data(department, user)

        self.assertEqual(len(meetings), 2)
        self.assertEqual(
            {meeting['customer'] for meeting in meetings},
            {'테스트 고객', '동료 담당 고객'},
        )
        self.assertIn('ai_department_coworker_user', {meeting.get('owner') for meeting in meetings})

        analysis = AIDepartmentAnalysis.objects.create(user=user, department=department)
        captured = {}

        class FakeCompletions:
            def create(self, **kwargs):
                captured.update(kwargs)

                class Usage:
                    total_tokens = 13

                class Message:
                    content = json.dumps({
                        'department_summary': '부서 전체 미팅을 반영했습니다.',
                        'painpoint_cards': [],
                    })

                class Choice:
                    message = Message()

                class Response:
                    choices = [Choice()]
                    usage = Usage()

                return Response()

        class FakeChat:
            completions = FakeCompletions()

        class FakeClient:
            chat = FakeChat()

        with patch('ai_chat.services.get_openai_client', return_value=FakeClient()):
            analyze_department(analysis, department, user)

        prompt = captured['messages'][1]['content']
        self.assertIn('미팅 기록 (2건)', prompt)
        self.assertIn('내 담당 미팅 내용', prompt)
        self.assertIn('동료 담당 미팅 내용', prompt)
        self.assertIn('담당자: ai_department_coworker_user', prompt)

    def test_department_analysis_prompt_includes_schedule_quote_and_delivery_context(self):
        from datetime import time
        from decimal import Decimal
        from reporting.models import DeliveryItem, Schedule
        from .services import analyze_department

        user = make_ai_user('ai_qd_prompt_user', can_use_ai=True)
        _company, department = make_department_with_followup(user)
        followup = FollowUp.objects.get(user=user, department=department)
        analysis = AIDepartmentAnalysis.objects.create(user=user, department=department)

        quote_schedule = Schedule.objects.create(
            user=user,
            followup=followup,
            visit_date=date(2026, 5, 13),
            visit_time=time(10, 0),
            activity_type='quote',
            status='completed',
            notes='고객에게 견적 제출함',
        )
        DeliveryItem.objects.create(
            schedule=quote_schedule,
            item_name='AI 견적 품목',
            quantity=1,
            unit_price=Decimal('300000'),
        )
        delivery_schedule = Schedule.objects.create(
            user=user,
            followup=followup,
            visit_date=date(2026, 5, 14),
            visit_time=time(11, 0),
            activity_type='delivery',
            status='completed',
            notes='일부 납품 완료',
        )
        DeliveryItem.objects.create(
            schedule=delivery_schedule,
            item_name='AI 납품 품목',
            quantity=2,
            unit_price=Decimal('40000'),
        )

        captured = {}

        class FakeCompletions:
            def create(self, **kwargs):
                captured.update(kwargs)

                class Usage:
                    total_tokens = 11

                class Message:
                    content = json.dumps({
                        'department_summary': '견적과 납품을 반영했습니다.',
                        'painpoint_cards': [],
                    })

                class Choice:
                    message = Message()

                class Response:
                    choices = [Choice()]
                    usage = Usage()

                return Response()

        class FakeChat:
            completions = FakeCompletions()

        class FakeClient:
            chat = FakeChat()

        with patch('ai_chat.services.get_openai_client', return_value=FakeClient()):
            result, qd_data, _token_usage = analyze_department(analysis, department, user)

        prompt = captured['messages'][1]['content']
        self.assertIn('견적 데이터 (1건)', prompt)
        self.assertIn('AI 견적 품목', prompt)
        self.assertIn('330,000원', prompt)
        self.assertIn('견적 일정', prompt)
        self.assertIn('납품 데이터 (1건)', prompt)
        self.assertIn('AI 납품 품목', prompt)
        self.assertIn('88,000원', prompt)
        self.assertIn('납품 일정', prompt)
        self.assertEqual(qd_data['summary']['total_quotes'], 1)
        self.assertEqual(qd_data['summary']['total_deliveries'], 1)
        self.assertEqual(result['department_summary'], '견적과 납품을 반영했습니다.')


class AIEmailAndStageActionContextTests(TestCase):
    def _fake_client(self, captured, payload):
        class FakeCompletions:
            def create(self, **kwargs):
                captured.update(kwargs)

                class Usage:
                    total_tokens = 29

                class Message:
                    content = json.dumps(payload)

                class Choice:
                    message = Message()

                class Response:
                    choices = [Choice()]
                    usage = Usage()

                return Response()

        class FakeChat:
            completions = FakeCompletions()

        class FakeClient:
            chat = FakeChat()

        return FakeClient()

    def test_department_analysis_uses_customer_emails_and_stage_actions(self):
        from reporting.models import EmailLog, History
        from .services import analyze_department

        user = make_ai_user('ai_email_stage_user', can_use_ai=True)
        company, department = make_department_with_followup(user)
        quote_followup = FollowUp.objects.get(user=user, department=department)
        quote_followup.customer_name = '견적고객'
        quote_followup.pipeline_stage = 'quote'
        quote_followup.save(update_fields=['customer_name', 'pipeline_stage'])
        won_followup = FollowUp.objects.create(
            user=user,
            company=company,
            department=department,
            customer_name='락인고객',
            pipeline_stage='won',
        )
        meeting_followup = FollowUp.objects.create(
            user=user,
            company=company,
            department=department,
            customer_name='미팅고객',
            pipeline_stage='contact',
        )
        History.objects.create(
            user=user,
            followup=meeting_followup,
            action_type='customer_meeting',
            content='자료 전달 요청',
            meeting_researcher_quote='다음 미팅 전에 제품 자료를 보내주세요.',
        )
        now = timezone.now()
        EmailLog.objects.create(
            user=user,
            sender=user,
            followup=quote_followup,
            email_type='sent',
            is_sent=True,
            status='sent',
            from_email='sales@example.com',
            to_email='customer@example.com',
            sender_email='sales@example.com',
            recipient_email='customer@example.com',
            subject='견적 조건 안내',
            body='먼저 보낸 견적 조건 안내입니다.',
            thread_id='thread-quote',
            sent_at=now - timedelta(minutes=2),
        )
        EmailLog.objects.create(
            user=user,
            sender=user,
            followup=meeting_followup,
            email_type='sent',
            is_sent=True,
            status='sent',
            from_email='sales@example.com',
            to_email='meeting@example.com',
            sender_email='sales@example.com',
            recipient_email='meeting@example.com',
            subject='비교표 전달',
            body='최근 보낸 제품 비교표입니다.',
            thread_id='thread-meeting-outbound',
            sent_at=now - timedelta(minutes=3),
        )
        EmailLog.objects.create(
            user=user,
            sender=user,
            followup=meeting_followup,
            email_type='sent',
            is_sent=True,
            status='sent',
            from_email='sales@example.com',
            to_email='meeting@example.com',
            sender_email='sales@example.com',
            recipient_email='meeting@example.com',
            subject='제외될 세 번째 발신',
            body='세 번째 발신은 AI 컨텍스트에서 제외되어야 합니다.',
            thread_id='thread-old-outbound',
            sent_at=now - timedelta(minutes=4),
        )
        EmailLog.objects.create(
            user=user,
            followup=quote_followup,
            email_type='received',
            is_sent=False,
            status='received',
            from_email='customer@example.com',
            to_email='sales@example.com',
            sender_email='customer@example.com',
            recipient_email='sales@example.com',
            subject='견적 검토 회신',
            body='가격 조정 가능 여부와 5월 말 납기 가능 여부를 확인 부탁드립니다.',
            thread_id='thread-quote',
            received_at=now,
        )
        EmailLog.objects.create(
            user=user,
            followup=meeting_followup,
            email_type='received',
            is_sent=False,
            status='received',
            from_email='meeting@example.com',
            to_email='sales@example.com',
            subject='미팅 후 자료 요청',
            body='미팅에서 설명한 제품 비교표와 다음 미팅 가능 일정을 보내주세요.',
            received_at=now - timedelta(minutes=1),
        )
        analysis = AIDepartmentAnalysis.objects.create(user=user, department=department)
        captured = {}

        with patch(
            'ai_chat.services.get_openai_client',
            return_value=self._fake_client(captured, {
                'department_summary': '메일과 고객 단계를 반영합니다.',
                'painpoint_cards': [],
                'next_actions': [],
            }),
        ):
            result, _qd_data, _token_usage = analyze_department(analysis, department, user)

        prompt = captured['messages'][1]['content']
        self.assertIn('고객 메일/답장 컨텍스트', prompt)
        self.assertIn('고객→영업', prompt)
        self.assertIn('가격 조정 가능 여부와 5월 말 납기 가능 여부', prompt)
        self.assertIn('관련 발신 메일', prompt)
        self.assertIn('먼저 보낸 견적 조건 안내입니다.', prompt)
        self.assertIn('최근 보낸 제품 비교표입니다.', prompt)
        self.assertNotIn('세 번째 발신은 AI 컨텍스트에서 제외', prompt)
        self.assertIn('고객 단계별 다음 액션 기준', prompt)
        self.assertIn('락인/수주 고객', prompt)
        self.assertIn('견적 고객', prompt)
        self.assertIn('미팅만 진행 고객', prompt)
        self.assertEqual(result['email_context']['summary']['inbound_count'], 2)
        self.assertEqual(result['email_context']['summary']['outbound_count'], 2)
        context_types = {
            item['context_type']
            for item in result['customer_stage_context']
        }
        self.assertIn('won_locked', context_types)
        self.assertIn('quote', context_types)
        self.assertIn('meeting_only', context_types)
        actions = ' '.join(action['action'] for action in result['next_actions'])
        self.assertIn('수주/락인', actions)
        self.assertIn('견적', actions)
        self.assertIn('미팅', actions)

    def test_followup_analysis_uses_email_reply_and_quote_stage_action(self):
        from reporting.models import EmailLog
        from .services import analyze_followup

        user = make_ai_user('ai_followup_email_user', can_use_ai=True)
        _company, department = make_department_with_followup(user)
        followup = FollowUp.objects.get(user=user, department=department)
        followup.pipeline_stage = 'quote'
        followup.save(update_fields=['pipeline_stage'])
        EmailLog.objects.create(
            user=user,
            followup=followup,
            email_type='received',
            is_sent=False,
            status='received',
            from_email='buyer@example.com',
            to_email='sales@example.com',
            subject='견적 답장',
            body='예산은 가능하지만 결제 조건과 납기 일정을 다시 받고 싶습니다.',
            received_at=timezone.now(),
        )
        analysis = AIDepartmentAnalysis.objects.create(user=user, department=department)
        captured = {}

        with patch(
            'ai_chat.services.get_openai_client',
            return_value=self._fake_client(captured, {
                'deal_probability': 50,
                'next_best_actions': [],
            }),
        ):
            result, _meeting_count, _token_usage = analyze_followup(analysis, followup, user)

        prompt = captured['messages'][1]['content']
        self.assertIn('고객 메일/답장 컨텍스트', prompt)
        self.assertIn('현재 고객 분석 기준', prompt)
        self.assertIn('견적 고객', prompt)
        self.assertIn('결제 조건과 납기 일정을 다시 받고 싶습니다', prompt)
        self.assertEqual(result['email_context']['summary']['inbound_count'], 1)
        self.assertEqual(result['stage_action_guidance']['context_type'], 'quote')
        self.assertTrue(any(
            '견적 내용, 미팅 이슈, 고객 메일 답장' in action['action']
            for action in result['next_best_actions']
        ))


class AIDepartmentPromptHubViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('ai_chat:department_list')

    def test_ai_main_requires_ai_permission(self):
        user = make_ai_user('no_ai_main_user', can_use_ai=False)
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_ai_main_lists_departments_for_ai_user(self):
        user = make_ai_user('ai_main_user', can_use_ai=True)
        _, department = make_department_with_followup(user, department_name='마케팅팀')
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI 업무 프롬프트 생성')
        self.assertContains(response, department.name)
        self.assertNotContains(response, '수동 프롬프트 생성기')
        self.assertNotContains(response, '/ai/prompt-builder/')

    def test_ai_main_only_marks_ai_sidebar_item_active(self):
        user = make_ai_user('ai_sidebar_user', can_use_ai=True)
        make_department_with_followup(user)
        self.client.force_login(user)

        response = self.client.get(self.url)
        html = response.content.decode('utf-8')

        self.assertRegex(
            html,
            r'href="/ai/" class="nav-link\s+active"',
        )
        self.assertNotRegex(
            html,
            r'href="/reporting/companies/" class="nav-link\s+active"',
        )

    def test_ai_main_shows_empty_analysis_state(self):
        user = make_ai_user('ai_empty_analysis_user', can_use_ai=True)
        _, department = make_department_with_followup(user)
        self.client.force_login(user)

        response = self.client.get(f'{self.url}?department={department.id}')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '아직 이 부서의 AI 분석 결과가 없습니다.')
        self.assertContains(response, 'AI 분석 실행')

    def test_ai_main_shows_analysis_summary_and_goal_cards(self):
        user = make_ai_user('ai_analysis_summary_user', can_use_ai=True)
        _, department = make_department_with_followup(user)
        make_department_analysis(user, department)
        self.client.force_login(user)

        response = self.client.get(f'{self.url}?department={department.id}')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '최근 견적 문의가 늘었지만 후속 연락이 지연되고 있습니다.')
        self.assertContains(response, '견적 후속 연락 전략 작성')
        self.assertContains(response, '참고 조건')

    def test_ai_main_post_builds_prompt_without_openai_call(self):
        user = make_ai_user('ai_main_post_user', can_use_ai=True)
        _, department = make_department_with_followup(user)
        make_department_analysis(user, department)
        self.client.force_login(user)

        previous_services_module = sys.modules.pop('ai_chat.services', None)
        try:
            response = self.client.post(self.url, data={
                'department_id': str(department.id),
                'selected_goal': '견적 후속 연락 전략 작성',
                'custom_goal': '',
            })
            services_imported_during_request = 'ai_chat.services' in sys.modules
        finally:
            if previous_services_module is not None:
                sys.modules['ai_chat.services'] = previous_services_module

        self.assertEqual(response.status_code, 200)
        self.assertFalse(services_imported_during_request)
        self.assertContains(response, '# 역할')
        self.assertContains(response, '견적 후속 연락 전략 작성')
        self.assertIn('견적 후속 연락 전략 작성', response.context['generated_prompt'])

    def test_ai_main_post_custom_goal_overrides_selected_goal(self):
        user = make_ai_user('ai_main_custom_goal_user', can_use_ai=True)
        _, department = make_department_with_followup(user)
        make_department_analysis(user, department)
        self.client.force_login(user)

        response = self.client.post(self.url, data={
            'department_id': str(department.id),
            'selected_goal': '고객 우선순위 정리',
            'custom_goal': '이번 주 팀장 보고용 요약을 만들고 싶다',
        })

        self.assertEqual(response.status_code, 200)
        prompt = response.context['generated_prompt']
        self.assertIn('이번 주 팀장 보고용 요약을 만들고 싶다', prompt)
        self.assertIn('보고서 목차', prompt)

    def test_manual_prompt_builder_url_is_removed(self):
        user = make_ai_user('removed_manual_prompt_user', can_use_ai=True)
        self.client.force_login(user)

        response = self.client.get('/ai/prompt-builder/')

        self.assertEqual(response.status_code, 404)


class AIDepartmentAnalysisMemoryTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _create_verified_card(self, analysis, status='confirmed', note='검증 메모'):
        return PainPointCard.objects.create(
            analysis=analysis,
            category='purchase_process',
            hypothesis='결재 승인자가 불명확해서 구매가 지연됩니다.',
            confidence='high',
            confidence_score=88,
            evidence=[],
            attribution='lab',
            verification_question='결재 승인자는 누구인가요?',
            action_if_yes='승인자 기준으로 제안서를 보냅니다.',
            action_if_no='구매 루트를 다시 확인합니다.',
            verification_status=status,
            verification_note=note,
            verified_at=timezone.now(),
        )

    def test_analyze_department_includes_verification_memory_in_prompt(self):
        from .services import analyze_department

        user = make_ai_user('ai_memory_prompt_user', can_use_ai=True)
        _, department = make_department_with_followup(user)
        analysis = AIDepartmentAnalysis.objects.create(user=user, department=department)
        self._create_verified_card(
            analysis,
            status='confirmed',
            note='김박사가 최종 승인자라고 5월 미팅에서 확인함',
        )
        captured = {}

        class FakeCompletions:
            def create(self, **kwargs):
                captured.update(kwargs)

                class Usage:
                    total_tokens = 37

                class Message:
                    content = json.dumps({
                        'department_summary': '검증 메모리를 반영했습니다.',
                        'painpoint_cards': [],
                    })

                class Choice:
                    message = Message()

                class Response:
                    choices = [Choice()]
                    usage = Usage()

                return Response()

        class FakeChat:
            completions = FakeCompletions()

        class FakeClient:
            chat = FakeChat()

        with patch('ai_chat.services.get_openai_client', return_value=FakeClient()):
            result, _qd_data, token_usage = analyze_department(analysis, department, user)

        prompt = captured['messages'][1]['content']
        self.assertIn('기존 PainPoint 검증 메모리', prompt)
        self.assertIn('김박사가 최종 승인자라고 5월 미팅에서 확인함', prompt)
        self.assertIn('미팅 기록과 동급의 분석 근거', prompt)
        self.assertIn('요약, 미팅 인사이트, PainPoint, 다음 액션, missing_info', prompt)
        self.assertIn('승인 일정/예산/필요 서류', prompt)
        self.assertIn('상태값으로 의미를 고정하지 말고', prompt)
        self.assertIn('같은 질문을 그대로 반복하지 않는다', prompt)
        self.assertEqual(token_usage, 37)
        self.assertEqual(result['verification_memory'][0]['verification_status'], 'checked')
        self.assertEqual(result['verification_memory'][0]['verification_status_label'], '검증 메모')
        self.assertIn('김박사가 최종 승인자라고 5월 미팅에서 확인함', result['department_summary'])
        self.assertEqual(result['verification_insights'][0]['status'], 'checked')
        self.assertIn('김박사가 최종 승인자라고 5월 미팅에서 확인함', result['verification_insights'][0]['impact'])
        self.assertTrue(any(
            '김박사가 최종 승인자라고 5월 미팅에서 확인함' in action['reason']
            for action in result['next_actions']
        ))
        self.assertTrue(any(
            '다음 단계 확인 질문' in question
            for question in result['missing_info']['questions']
        ))

    def test_run_analysis_preserves_verified_cards_and_skips_memory_duplicates(self):
        user = make_ai_user('ai_memory_run_user', can_use_ai=True)
        _, department = make_department_with_followup(user)
        followup = FollowUp.objects.get(user=user, department=department)
        followup.priority = 'long_term'
        followup.save(update_fields=['priority'])
        analysis = AIDepartmentAnalysis.objects.create(user=user, department=department)
        verified = self._create_verified_card(
            analysis,
            status='denied',
            note='구매 지연 원인은 결재가 아니라 기존 재고 소진 대기였음',
        )
        stale_unverified = PainPointCard.objects.create(
            analysis=analysis,
            category='delivery',
            hypothesis='납기 일정이 불명확합니다.',
            confidence='med',
            confidence_score=55,
            evidence=[],
            attribution='lab',
            verification_question='납기 기준일은 언제인가요?',
            action_if_yes='납기 일정을 맞춥니다.',
            action_if_no='다른 장애물을 확인합니다.',
        )
        analysis_result = {
            'department_summary': '재분석 결과',
            'followup_priority_recommendations': [
                {
                    'customer': '테스트 고객',
                    'priority': 'urgent',
                    'reason': '고객 답장과 견적 검토 일정 확인이 필요합니다.',
                },
            ],
            'recommended_goals': [
                {
                    'customer': '테스트 고객',
                    'title': '테스트 고객 견적 후속 실행계획 작성',
                    'description': '긴급 고객의 후속 액션을 정리합니다.',
                    'reason': 'AI가 긴급 후속 대상으로 판단했습니다.',
                    'priority': 'urgent',
                },
            ],
            'painpoint_cards': [
                {
                    'category': verified.category,
                    'hypothesis': verified.hypothesis,
                    'confidence': 'high',
                    'confidence_score': 90,
                    'evidence': [],
                    'attribution': verified.attribution,
                    'verification_question': verified.verification_question,
                    'action_if_yes': '중복 카드',
                    'action_if_no': '중복 카드',
                    'caution': '',
                },
                {
                    'category': 'budget',
                    'hypothesis': '예산 집행 시점 확인이 필요합니다.',
                    'confidence': 'med',
                    'confidence_score': 62,
                    'evidence': [],
                    'attribution': 'lab',
                    'verification_question': '이번 분기 예산 집행 가능 시점은 언제인가요?',
                    'action_if_yes': '분기 예산 일정에 맞춰 견적을 보냅니다.',
                    'action_if_no': '다음 예산 주기를 확인합니다.',
                    'caution': '',
                },
            ],
        }
        qd_data = {
            'summary': {
                'total_quotes': 0,
                'total_deliveries': 0,
            },
        }
        self.client.force_login(user)

        with patch('ai_chat.services.analyze_department', return_value=(analysis_result, qd_data, 41)), \
                patch('ai_chat.services.gather_meeting_data', return_value=[]):
            response = self.client.post(reverse('ai_chat:run_analysis', args=[department.id]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['cards_created'], 1)
        self.assertEqual(payload['cards_preserved'], 1)
        self.assertEqual(payload['priority_updates'], 1)
        self.assertEqual(payload['priority_recommendations'], 1)
        self.assertTrue(PainPointCard.objects.filter(id=verified.id).exists())
        self.assertFalse(PainPointCard.objects.filter(id=stale_unverified.id).exists())
        self.assertEqual(
            PainPointCard.objects.filter(
                analysis=analysis,
                category='purchase_process',
                verification_status='unverified',
            ).count(),
            0,
        )
        self.assertTrue(PainPointCard.objects.filter(
            analysis=analysis,
            category='budget',
            hypothesis='예산 집행 시점 확인이 필요합니다.',
        ).exists())
        analysis.refresh_from_db()
        memory_notes = [
            item['verification_note']
            for item in analysis.analysis_data.get('verification_memory', [])
        ]
        self.assertIn('구매 지연 원인은 결재가 아니라 기존 재고 소진 대기였음', memory_notes)
        self.assertIn(
            '구매 지연 원인은 결재가 아니라 기존 재고 소진 대기였음',
            analysis.analysis_data['verification_insights'][0]['impact'],
        )
        self.assertIn(
            '구매 지연 원인은 결재가 아니라 기존 재고 소진 대기였음',
            analysis.analysis_data['department_summary'],
        )
        self.assertIn('검증 메모', analysis.analysis_data['department_summary'])
        self.assertNotIn('부정된 가설', analysis.analysis_data['department_summary'])
        self.assertTrue(any(
            '검증 메모리 반영' in action['reason']
            for action in analysis.analysis_data['next_actions']
        ))
        followup.refresh_from_db()
        self.assertEqual(followup.priority, 'urgent')
        self.assertEqual(
            analysis.analysis_data['followup_priority_recommendations'][0]['customer'],
            '테스트 고객',
        )
        self.assertEqual(
            analysis.analysis_data['followup_priority_recommendations'][0]['priority'],
            'urgent',
        )
        self.assertIn(
            '테스트 고객',
            analysis.analysis_data['recommended_goals'][0]['title'],
        )

    def test_verify_card_uses_confirm_only_and_saves_note_for_ai_judgment(self):
        user = make_ai_user('ai_verify_confirm_only_user', can_use_ai=True)
        _, department = make_department_with_followup(user)
        analysis = AIDepartmentAnalysis.objects.create(user=user, department=department)
        card = PainPointCard.objects.create(
            analysis=analysis,
            category='budget',
            hypothesis='예산 지연 가능성이 있습니다.',
            confidence='med',
            confidence_score=60,
            evidence=[],
            attribution='lab',
            verification_question='예산 집행일은 언제인가요?',
            action_if_yes='예산 일정에 맞춰 견적을 보냅니다.',
            action_if_no='다음 예산 주기를 확인합니다.',
        )
        self.client.force_login(user)

        denied_response = self.client.post(
            reverse('ai_chat:verify_card', args=[card.id]),
            {'status': 'denied', 'note': '단순 거절 버튼은 더 이상 사용하지 않습니다.'},
        )
        self.assertEqual(denied_response.status_code, 400)

        response = self.client.post(
            reverse('ai_chat:verify_card', args=[card.id]),
            {'note': '예산은 있으나 집행 시점을 고객이 아직 못 정했습니다.'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], '검증 메모')
        card.refresh_from_db()
        self.assertEqual(card.verification_status, 'confirmed')
        self.assertEqual(card.verification_note, '예산은 있으나 집행 시점을 고객이 아직 못 정했습니다.')
