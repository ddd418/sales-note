from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import models
from reporting.models import FollowUp, Schedule, History
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = '테스트용 샘플 데이터를 생성합니다'

    def handle(self, *args, **options):
        # 슈퍼유저 가져오기
        admin = User.objects.get(username='admin')
        
        # 기존 데이터 삭제 (테스트 환경에서만)
        if self.confirm_action("기존 데이터를 삭제하고 새로운 테스트 데이터를 생성하시겠습니까?"):
            History.objects.all().delete()
            Schedule.objects.all().delete()
            FollowUp.objects.all().delete()
            self.stdout.write(self.style.WARNING('기존 데이터가 삭제되었습니다.'))        # 팔로우업 생성
        followups_data = [
            {'customer_name': '김철수', 'company': 'ABC 대학교', 'department': '컴퓨터공학과', 'phone_number': '010-1234-5678', 'priority': 'high'},
            {'customer_name': '이영희', 'company': 'XYZ 기업', 'department': '연구개발팀', 'phone_number': '010-2345-6789', 'priority': 'medium'},
            {'customer_name': '박민수', 'company': '테크놀로지 회사', 'department': 'IT사업부', 'phone_number': '010-3456-7890', 'priority': 'low'},
            {'customer_name': '최수진', 'company': '제조업체', 'department': '품질관리팀', 'phone_number': '010-4567-8901', 'priority': 'high'},
            {'customer_name': '정우성', 'company': '스타트업', 'department': '개발팀', 'phone_number': '010-5678-9012', 'priority': 'medium'},
        ]
        
        
        followups = []
        for data in followups_data:
            followup = FollowUp.objects.create(
                user=admin,
                customer_name=data['customer_name'],
                company=data['company'],
                department=data['department'],
                phone_number=data['phone_number'],
                address=f"{data['company']} 주소",
                notes=f"{data['customer_name']} 고객 관련 상세 내용",
                priority=data['priority']
            )
            followups.append(followup)
            self.stdout.write(f'팔로우업 생성: {followup.customer_name} ({followup.company})')

        # 일정 생성
        base_date = datetime.now().date()
        for i, followup in enumerate(followups):
            for j in range(random.randint(1, 3)):  # 각 팔로우업당 1-3개 일정
                visit_date = base_date + timedelta(days=random.randint(-30, 30))
                schedule = Schedule.objects.create(
                    user=admin,
                    followup=followup,
                    visit_date=visit_date,
                    visit_time=datetime.now().time(),
                    location=f"{followup.company} 사무실",
                    status=random.choice(['scheduled', 'completed', 'cancelled']),
                    notes=f"{followup.customer_name}님과의 미팅"
                )
                self.stdout.write(f'일정 생성: {schedule.visit_date} - {followup.customer_name}')

        # 히스토리 생성 (다양한 활동 유형과 납품 금액 포함)
        activities = [
            {'type': 'customer_meeting', 'content': '제품 데모 및 요구사항 논의', 'amount': None},
            {'type': 'customer_meeting', 'content': '계약 조건 협상', 'amount': None},
            {'type': 'delivery_schedule', 'content': '1차 납품 완료', 'amount': 5000000},
            {'type': 'delivery_schedule', 'content': '추가 장비 납품', 'amount': 3000000},
            {'type': 'customer_meeting', 'content': '프로젝트 진행 상황 보고', 'amount': None},
            {'type': 'delivery_schedule', 'content': '최종 납품 및 설치', 'amount': 8000000},
            {'type': 'customer_meeting', 'content': '향후 협력 방안 논의', 'amount': None},
            {'type': 'delivery_schedule', 'content': '유지보수 장비 납품', 'amount': 1500000},
        ]

        for i, followup in enumerate(followups):
            # 각 팔로우업마다 2-4개의 히스토리 생성
            num_histories = random.randint(2, 4)
            selected_activities = random.sample(activities, num_histories)
            
            for j, activity in enumerate(selected_activities):
                created_date = datetime.now() - timedelta(days=random.randint(1, 60))
                
                history = History.objects.create(
                    user=admin,
                    followup=followup,
                    action_type=activity['type'],
                    content=activity['content'],
                    delivery_amount=activity['amount'],
                    created_at=created_date
                )
                
                action_display = '고객 미팅' if activity['type'] == 'customer_meeting' else '납품 일정'
                amount_text = f" (금액: {activity['amount']:,}원)" if activity['amount'] else ""
                self.stdout.write(f'히스토리 생성: {followup.customer_name} - {action_display}{amount_text}')

        self.stdout.write(self.style.SUCCESS('테스트 데이터 생성이 완료되었습니다!'))
        self.stdout.write(f'팔로우업: {FollowUp.objects.count()}개')
        self.stdout.write(f'일정: {Schedule.objects.count()}개')
        self.stdout.write(f'히스토리: {History.objects.count()}개')
        
        # 통계 요약
        meeting_count = History.objects.filter(action_type='customer_meeting').count()
        delivery_count = History.objects.filter(action_type='delivery_schedule').count()
        total_amount = History.objects.filter(
            action_type='delivery_schedule', 
            delivery_amount__isnull=False
        ).aggregate(total=models.Sum('delivery_amount'))['total'] or 0
        
        self.stdout.write(self.style.SUCCESS(f'고객 미팅: {meeting_count}건'))
        self.stdout.write(self.style.SUCCESS(f'납품 일정: {delivery_count}건'))
        self.stdout.write(self.style.SUCCESS(f'총 납품 금액: {total_amount:,}원'))

    def confirm_action(self, message):
        """사용자 확인을 위한 헬퍼 메서드"""
        return True  # 테스트 환경에서는 자동으로 진행
