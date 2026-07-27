"""AI workspace JSON APIs.

The AI API implementation is still exported from the legacy view module for
compatibility while URL routing and future changes use this domain module.
"""

from reporting.views import (  # noqa: F401
    schedule_ai_coach_api,
)

