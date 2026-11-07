export type PipelineStage = 'potential' | 'contact' | 'quote' | 'negotiation' | 'won' | 'lost';

export type StageSummary = {
  id: PipelineStage;
  label: string;
  caption: string;
  color?: string;
  count?: number;
  totalValue?: number;
  overdueCount?: number;
};

export type QuoteLineItem = {
  id: string;
  itemName: string;
  productCode?: string;
  quantity: number;
  unit: string;
  unitPrice?: number | null;
  totalPrice?: number;
  quoteGroup?: string;
  quoteGroupLabel?: string;
  source?: string;
  notes?: string;
};

export type Deal = {
  id: number;
  company: string;
  contact: string;
  department?: string;
  owner: string;
  stage: PipelineStage;
  stageLabel?: string;
  value: number;
  probability: number | null;
  probabilityOverridden?: boolean;
  nextAction: string;
  due: string;
  risk: 'low' | 'medium' | 'high';
  tags: string[];
  lastActivity: string;
  attentionScore?: number;
  attentionReason?: string;
  isPotentialOverflow?: boolean;
  recentActivities?: Array<{
    type: string;
    date: string;
    summary: string;
  }>;
  latestQuote?: {
    number: string;
    stage: string;
    amount: number;
    probability: number;
    validUntil?: string | null;
    source?: string;
    basisType?: string;
    basisDate?: string | null;
    quoteDate?: string | null;
    items?: QuoteLineItem[];
  } | null;
  quoteComparison?: {
    quotedAmount: number;
    actualAmount: number;
    deltaAmount: number;
    deltaRate: number;
    status: 'over' | 'under' | 'match';
    statusLabel: string;
    source: string;
    number: string;
    items?: QuoteLineItem[];
  } | null;
  nextSchedule?: {
    id: number;
    type: string;
    date: string;
    time: string;
    location: string;
  } | null;
  detailUrl?: string;
};

export type PipelineMetrics = {
  totalPipelineValue: number;
  weightedPipelineValue: number;
  activeCount: number;
  overdueCount: number;
  contactCount: number;
};

export type PriorityTask = {
  title: string;
  count: number;
  tone: 'danger' | 'warning' | 'info';
};

export type HiddenDeal = {
  id: number;
  company: string;
  department: string;
  contact: string;
  owner: string;
};

export type PipelineData = {
  source: 'mock' | 'django' | 'unavailable';
  generatedAt?: string;
  stages: StageSummary[];
  deals: Deal[];
  hiddenDeals?: HiddenDeal[];
  metrics: PipelineMetrics;
  priorityTasks: PriorityTask[];
};

// 단계 정의. 서버 응답이 오기 전/실패 시 빈 보드의 칸 제목으로 쓴다.
const PIPELINE_STAGE_DEFINITIONS: StageSummary[] = [
  { id: 'potential', label: '잠재', caption: '관심 확인' },
  { id: 'contact', label: '접촉/미팅', caption: '요구사항 파악' },
  { id: 'quote', label: '견적 제출', caption: '금액/범위 협의' },
  { id: 'negotiation', label: '협상', caption: '의사결정 추적' },
  { id: 'won', label: '수주', caption: '납품 전환' },
  { id: 'lost', label: '실주', caption: '원인 정리' },
];

export const emptyPipelineData: PipelineData = {
  source: 'unavailable',
  stages: PIPELINE_STAGE_DEFINITIONS,
  deals: [],
  metrics: {
    totalPipelineValue: 0,
    weightedPipelineValue: 0,
    activeCount: 0,
    overdueCount: 0,
    contactCount: 0,
  },
  priorityTasks: [],
};
