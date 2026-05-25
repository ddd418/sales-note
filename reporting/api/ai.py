"""AI workspace JSON APIs.

The AI API implementation is still exported from the legacy view module for
compatibility while URL routing and future changes use this domain module.
"""

from reporting.views import (  # noqa: F401
    ai_workspace_action_draft_api,
    ai_workspace_action_feedback_api,
    ai_workspace_department_question_api,
    ai_workspace_memories_api,
    ai_workspace_memory_create_api,
    ai_workspace_memory_toggle_active_api,
    ai_workspace_memory_update_api,
    ai_workspace_question_feedback_api,
    ai_workspace_question_log_delete_api,
    ai_workspace_question_log_detail_api,
    ai_workspace_summary_api,
    schedule_ai_coach_api,
)

