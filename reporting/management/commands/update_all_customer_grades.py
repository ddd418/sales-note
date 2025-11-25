"""
전체 고객의 AI 등급을 일괄 업데이트하는 management command

사용법:
    python manage.py update_all_customer_grades
    python manage.py update_all_customer_grades --limit 50
    python manage.py update_all_customer_grades --grade A+,A
    python manage.py update_all_customer_grades --dry-run
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import timedelta
from decimal import Decimal
import time

from reporting.models import (
    FollowUp, Schedule, EmailLog, DeliveryItem, History,
    OpportunityTracking, Prepayment
)
from reporting.ai_utils import update_customer_grade_with_ai


class Command(BaseCommand):
    help = 'AI를 사용하여 전체 고객의 등급을 일괄 업데이트합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='업데이트할 최대 고객 수 (기본: 전체)'
        )
        parser.add_argument(
            '--grade',
            type=str,
            default=None,
            help='특정 등급의 고객만 업데이트 (예: A+,A,B)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제로 업데이트하지 않고 결과만 출력'
        )
        parser.add_argument(
            '--min-activity',
            type=int,
            default=1,
            help='최소 활동 횟수 (미팅+견적+납품, 기본: 1)'
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        grade_filter = options.get('grade')
        dry_run = options.get('dry_run')
        min_activity = options.get('min_activity', 1)

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('AI 기반 전체 고객 등급 업데이트 시작'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # 고객 쿼리셋 준비
        queryset = FollowUp.objects.all()

        # 등급 필터 적용
        if grade_filter:
            grades = [g.strip() for g in grade_filter.split(',')]
            queryset = queryset.filter(customer_grade__in=grades)
            self.stdout.write(f"등급 필터: {', '.join(grades)}")

        # 활동이 있는 고객만 (일정, 이메일, 히스토리, 선결제 중 하나라도 있으면)
        if min_activity > 0:
            queryset = queryset.annotate(
                schedule_count=Count('schedules', distinct=True),
                email_count=Count('emails', distinct=True),
                history_count=Count('histories', distinct=True),
                prepayment_count=Count('prepayments', distinct=True)
            ).filter(
                Q(schedule_count__gte=1) | 
                Q(email_count__gte=1) | 
                Q(history_count__gte=1) |
                Q(prepayment_count__gte=1)
            )
            self.stdout.write(f"최소 활동: 일정/이메일/히스토리/선결제 중 1개 이상")

        # 정렬: 최근 수정 순
        queryset = queryset.order_by('-updated_at')

        # 제한 적용
        if limit:
            queryset = queryset[:limit]
            self.stdout.write(f"업데이트 대상: 최대 {limit}명")

        total_count = queryset.count()
        
        if total_count == 0:
            self.stdout.write(self.style.WARNING('업데이트할 고객이 없습니다.'))
            return

        self.stdout.write(f"\n총 {total_count}명의 고객을 처리합니다.")
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  DRY RUN 모드: 실제로 업데이트하지 않습니다.\n'))

        # 통계 변수
        success_count = 0
        error_count = 0
        grade_changes = []
        start_time = time.time()

        # 각 고객 처리
        for index, followup in enumerate(queryset, 1):
            try:
                # 진행 표시
                progress = f"[{index}/{total_count}]"
                self.stdout.write(f"\n{progress} 처리 중: {followup.customer_name or '고객명 없음'} ({followup.company or '업체명 없음'})")

                # 고객 데이터 수집
                customer_data = self._collect_customer_data(followup)
                
                # 변경사항 확인: 마지막 등급 업데이트 이후 새로운 활동이 있는지 체크
                has_changes = self._check_for_changes(followup)
                
                old_grade = followup.customer_grade or '없음'
                
                # 변경사항이 없으면 스킵 (토큰 절약)
                if not has_changes and followup.ai_grade_score is not None:
                    self.stdout.write(
                        f"  ⏭️  변경사항 없음 - 스킵 (기존 등급: {old_grade}, "
                        f"점수: {followup.ai_grade_score}/100)"
                    )
                    continue
                
                # AI로 등급 분석 (변경사항이 있을 때만)
                result = update_customer_grade_with_ai(customer_data, user=None)
                new_grade = result.get('grade')
                score = result.get('score')
                reasoning = result.get('reasoning', '')

                # 등급 변경 여부 확인
                grade_changed = old_grade != new_grade
                change_symbol = '🔄' if grade_changed else '✓'
                
                self.stdout.write(
                    f"  {change_symbol} 등급: {old_grade} → {new_grade} "
                    f"(점수: {score}/100)"
                )
                self.stdout.write(f"  📝 근거: {reasoning[:80]}{'...' if len(reasoning) > 80 else ''}")

                # 실제 업데이트 (dry-run이 아닐 때만)
                if not dry_run:
                    followup.customer_grade = new_grade
                    followup.ai_grade_score = score
                    followup.ai_grade_reasoning = reasoning
                    followup.ai_grade_updated_at = timezone.now()
                    followup.save(update_fields=[
                        'customer_grade', 
                        'ai_grade_score', 
                        'ai_grade_reasoning',
                        'ai_grade_updated_at'
                    ])

                # 통계 업데이트
                success_count += 1
                if grade_changed:
                    grade_changes.append({
                        'name': followup.customer_name or '고객명 없음',
                        'old': old_grade,
                        'new': new_grade,
                        'score': score
                    })

                # API 속도 제한 고려 (OpenAI)
                if index < total_count:
                    time.sleep(0.5)  # 0.5초 대기

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"  ❌ 오류 발생: {str(e)}")
                )
                continue

        # 최종 결과 출력
        elapsed_time = time.time() - start_time
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('업데이트 완료'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        self.stdout.write(f"\n총 처리: {total_count}명")
        self.stdout.write(self.style.SUCCESS(f"✓ 성공: {success_count}명"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"✗ 실패: {error_count}명"))
        self.stdout.write(f"🔄 등급 변경: {len(grade_changes)}명")
        self.stdout.write(f"⏱️  소요 시간: {elapsed_time:.1f}초")
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  DRY RUN 모드였으므로 실제 변경사항 없음'))

        # 등급 변경 상세 내역
        if grade_changes:
            self.stdout.write(f"\n{'=' * 70}")
            self.stdout.write("등급 변경 상세:")
            self.stdout.write('=' * 70)
            
            for change in grade_changes[:20]:  # 최대 20개만 출력
                self.stdout.write(
                    f"  • {change['name']}: "
                    f"{change['old']} → {change['new']} "
                    f"({change['score']}점)"
                )
            
            if len(grade_changes) > 20:
                self.stdout.write(f"  ... 외 {len(grade_changes) - 20}건")

        # 등급별 분포 (실제 업데이트된 경우만)
        if not dry_run and success_count > 0:
            self.stdout.write(f"\n{'=' * 70}")
            self.stdout.write("업데이트 후 등급 분포:")
            self.stdout.write('=' * 70)
            
            grade_dist = FollowUp.objects.values('customer_grade').annotate(
                count=Count('id')
            ).order_by('-customer_grade')
            
            for item in grade_dist:
                grade = item['customer_grade'] or '미지정'
                count = item['count']
                self.stdout.write(f"  {grade}: {count}명")

    def _check_for_changes(self, followup):
        """
        마지막 AI 등급 업데이트 이후 새로운 활동이 있는지 확인
        """
        # 한번도 등급 업데이트를 안했으면 무조건 업데이트 필요
        if not followup.ai_grade_updated_at:
            return True
        
        last_updated = followup.ai_grade_updated_at
        
        # 마지막 업데이트 이후 새로운 활동 확인
        new_schedules = Schedule.objects.filter(
            followup=followup,
            created_at__gt=last_updated
        ).exists()
        
        new_emails = EmailLog.objects.filter(
            followup=followup,
            sent_at__gt=last_updated
        ).exists()
        
        # DeliveryItem의 경우 관련 Schedule을 통해 확인
        new_deliveries = DeliveryItem.objects.filter(
            schedule__followup=followup,
            schedule__created_at__gt=last_updated
        ).exists()
        
        # 선결제 추가 확인
        new_prepayments = Prepayment.objects.filter(
            customer=followup,
            created_at__gt=last_updated
        ).exists()
        
        # 30일 이상 지났으면 재평가 (데이터가 오래됨)
        days_since_update = (timezone.now() - last_updated).days
        if days_since_update > 30:
            return True
        
        return new_schedules or new_emails or new_deliveries or new_prepayments
    
    def _collect_customer_data(self, followup):
        """
        고객의 활동 데이터 수집
        """
        # 기간 설정 (최근 6개월)
        six_months_ago = timezone.now() - timedelta(days=180)

        # 미팅 횟수
        meeting_count = Schedule.objects.filter(
            followup=followup,
            activity_type='meeting',
            created_at__gte=six_months_ago
        ).count()

        # 이메일 횟수
        email_count = EmailLog.objects.filter(
            followup=followup,
            sent_at__gte=six_months_ago
        ).count()

        # 견적 횟수
        quote_count = Schedule.objects.filter(
            followup=followup,
            activity_type='quote',
            created_at__gte=six_months_ago
        ).count()

        # 구매 횟수 및 금액 (모든 구매 내역 - 기간 제한 없음)
        all_deliveries = DeliveryItem.objects.filter(
            schedule__followup=followup
        )
        
        # 최근 6개월 구매
        recent_deliveries = all_deliveries.filter(
            schedule__created_at__gte=six_months_ago
        )
        
        purchase_count = all_deliveries.values('schedule').distinct().count()
        recent_purchase_count = recent_deliveries.values('schedule').distinct().count()
        
        total_purchase = all_deliveries.aggregate(
            total=Sum('total_price')
        )['total'] or Decimal('0')
        
        recent_total_purchase = recent_deliveries.aggregate(
            total=Sum('total_price')
        )['total'] or Decimal('0')
        
        # 선결제 정보
        prepayments = Prepayment.objects.filter(
            customer=followup
        )
        prepayment_count = prepayments.count()
        total_prepayment = prepayments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        # 마지막 연락일 (최근 일정 기준)
        last_schedule = Schedule.objects.filter(followup=followup).order_by('-visit_date').first()
        last_contact = last_schedule.visit_date.strftime('%Y-%m-%d') if last_schedule else '없음'

        # 미팅 요약
        recent_meetings = Schedule.objects.filter(
            followup=followup,
            activity_type='meeting',
            notes__isnull=False
        ).order_by('-visit_date')[:3]
        
        meeting_summary = []
        for meeting in recent_meetings:
            if meeting.notes:
                meeting_summary.append(f"[{meeting.visit_date.strftime('%Y-%m-%d')}] {meeting.notes[:100]}")

        # 진행 중인 기회
        opportunities = []
        active_opps = OpportunityTracking.objects.filter(
            followup=followup,
            current_stage__in=['lead', 'contact', 'quote', 'closing']
        )[:5]
        for opp in active_opps:
            opportunities.append({
                'stage': opp.get_current_stage_display(),
                'content': opp.title or '영업 기회'
            })

        return {
            'name': followup.customer_name or '고객명 미정',
            'company': followup.company or '업체명 미정',
            'meeting_count': meeting_count,
            'email_count': email_count,
            'quote_count': quote_count,
            'purchase_count': purchase_count,
            'recent_purchase_count': recent_purchase_count,
            'total_purchase': float(total_purchase),
            'recent_total_purchase': float(recent_total_purchase),
            'prepayment_count': prepayment_count,
            'total_prepayment': float(total_prepayment),
            'last_contact': last_contact,
            'avg_response_time': '알 수 없음',
            'email_sentiment': '중립',
            'meeting_summary': meeting_summary,
            'opportunities': opportunities,
        }
