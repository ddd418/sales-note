from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

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

        with patch('ai_chat.views.analyze_department') as mocked_analyze:
            response = self.client.post(self.url, data={
                'department_id': str(department.id),
                'selected_goal': '견적 후속 연락 전략 작성',
                'custom_goal': '',
            })

        self.assertEqual(response.status_code, 200)
        mocked_analyze.assert_not_called()
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
