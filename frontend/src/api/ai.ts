// Schedule AI coach API surface (AI 워크스페이스 메뉴 제거와 무관한 별도 기능, 보존).

export type {
  AIWorkspaceActionEvidence,
  ScheduleAICoach,
  ScheduleAICoachResponse,
} from './legacy';

export {
  generateScheduleAICoach,
} from './legacy';
