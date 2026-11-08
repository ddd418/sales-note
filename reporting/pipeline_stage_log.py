"""파이프라인 단계 변경 기록.

`FollowUp.pipeline_stage` 는 덮어쓰는 값이라 "지난주에 어느 단계였는지"가 남지 않는다.
아침회의의 "이번 주 움직임"을 보여주려면 변경 시점마다 한 줄씩 남겨야 한다.

기록 경로는 두 가지뿐이다.
- `FollowUp.save()` 를 거치는 변경: signals.py 의 pre/post_save 가 자동으로 잡는다.
- `QuerySet.update()` 로 바꾸는 카드 이동(funnel_pipeline_move): 시그널을 타지 않으므로
  그 뷰가 직접 `record_stage_change` 를 부른다.

연초 일괄 초기화(`_ensure_pipeline_year_reset`)는 일부러 기록하지 않는다. 영업 활동이
아니라 시스템 초기화라서, 1월 첫 회의의 움직임이 수백 건의 잡음으로 뒤덮이기 때문이다.
"""

import logging

from django.db import transaction

logger = logging.getLogger(__name__)


def record_stage_change(followup, from_stage, to_stage, *, actor=None):
    """단계가 실제로 바뀌었을 때만 한 줄 남긴다.

    기록 실패가 카드 이동이나 고객 저장을 막으면 안 되므로 예외는 로그만 남긴다.
    바깥 트랜잭션이 깨지지 않도록 savepoint 안에서 만든다.
    """
    from reporting.models import PipelineStageChange

    if from_stage == to_stage or not to_stage:
        return None
    try:
        with transaction.atomic():
            return PipelineStageChange.objects.create(
                followup=followup,
                from_stage=from_stage or '',
                to_stage=to_stage,
                changed_by=actor,
                source=(
                    PipelineStageChange.SOURCE_MANUAL if actor is not None
                    else PipelineStageChange.SOURCE_AUTO
                ),
            )
    except Exception:
        logger.exception('Failed to record pipeline stage change for followup %s', followup.pk)
        return None
