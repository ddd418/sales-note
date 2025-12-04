-- 일정 544를 새 OpportunityTracking 233에 연결
UPDATE reporting_schedule SET opportunity_id = 233 WHERE id = 544;

-- 일정 545에 새 OpportunityTracking 생성 (closing 단계)
INSERT INTO reporting_opportunitytracking (followup_id, current_stage, stage_entry_date, expected_revenue, weighted_revenue, probability, expected_close_date, created_at, updated_at, stage_history, total_quotes_sent, total_meetings, backlog_amount)
VALUES (156, 'closing', '2025-12-04', 6222458, 4977966, 80, '2026-01-05', NOW(), NOW(), '[{"stage": "closing", "entered": "2025-12-04", "exited": null, "note": "delivery scheduled"}]'::jsonb, 0, 0, 0)
RETURNING id;
