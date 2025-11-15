"""
연말 OpportunityTracking 정리 명령어
- 수주(won) 및 견적실패(quote_lost) 단계의 OpportunityTracking 삭제
- 매년 1월 1일에 실행하여 새해 시작
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from reporting.models import OpportunityTracking


class Command(BaseCommand):
    help = '연말에 수주 및 견적실패 OpportunityTracking 삭제'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제로 삭제하지 않고 삭제될 항목만 표시',
        )
        parser.add_argument(
            '--year',
            type=int,
            help='특정 연도의 데이터만 삭제 (기본값: 작년)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        target_year = options.get('year')
        
        if not target_year:
            # 기본값: 작년
            target_year = datetime.now().year - 1
        
        self.stdout.write(self.style.WARNING(f'\n{"="*60}'))
        self.stdout.write(self.style.WARNING(f'연말 OpportunityTracking 정리 ({target_year}년)'))
        self.stdout.write(self.style.WARNING(f'{"="*60}\n'))
        
        if dry_run:
            self.stdout.write(self.style.NOTICE('[DRY RUN 모드] 실제로 삭제하지 않습니다.\n'))
        
        # 수주(won) 및 견적실패(quote_lost) 단계 조회
        won_opportunities = OpportunityTracking.objects.filter(
            current_stage='won',
            won_date__year=target_year
        )
        
        quote_lost_opportunities = OpportunityTracking.objects.filter(
            current_stage='quote_lost',
            lost_date__year=target_year
        )
        
        won_count = won_opportunities.count()
        quote_lost_count = quote_lost_opportunities.count()
        total_count = won_count + quote_lost_count
        
        self.stdout.write(f'🔍 삭제 대상:')
        self.stdout.write(f'  - 수주(won): {won_count}건')
        self.stdout.write(f'  - 견적실패(quote_lost): {quote_lost_count}건')
        self.stdout.write(f'  - 총계: {total_count}건\n')
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('삭제할 항목이 없습니다.'))
            return
        
        # 삭제 대상 상세 표시
        if won_count > 0:
            self.stdout.write(self.style.WARNING('\n📋 수주(won) 삭제 대상:'))
            for opp in won_opportunities[:10]:  # 최대 10개만 표시
                self.stdout.write(f'  - {opp.followup.customer_name} ({opp.followup.company}): {opp.won_date}')
            if won_count > 10:
                self.stdout.write(f'  ... 외 {won_count - 10}건')
        
        if quote_lost_count > 0:
            self.stdout.write(self.style.WARNING('\n📋 견적실패(quote_lost) 삭제 대상:'))
            for opp in quote_lost_opportunities[:10]:
                self.stdout.write(f'  - {opp.followup.customer_name} ({opp.followup.company}): {opp.lost_date}')
            if quote_lost_count > 10:
                self.stdout.write(f'  ... 외 {quote_lost_count - 10}건')
        
        # 삭제 실행
        if not dry_run:
            self.stdout.write(self.style.WARNING('\n🗑️  삭제 중...'))
            won_deleted, _ = won_opportunities.delete()
            quote_lost_deleted, _ = quote_lost_opportunities.delete()
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ 완료!'))
            self.stdout.write(f'  - 수주: {won_deleted}건 삭제')
            self.stdout.write(f'  - 견적실패: {quote_lost_deleted}건 삭제')
            self.stdout.write(f'  - 총계: {won_deleted + quote_lost_deleted}건 삭제\n')
        else:
            self.stdout.write(self.style.NOTICE('\n✋ DRY RUN 모드: 삭제하지 않았습니다.'))
            self.stdout.write(self.style.NOTICE('실제 삭제하려면 --dry-run 옵션을 제거하세요.\n'))
