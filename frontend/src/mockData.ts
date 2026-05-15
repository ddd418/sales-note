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

export type Deal = {
  id: number;
  company: string;
  contact: string;
  department?: string;
  owner: string;
  stage: PipelineStage;
  stageLabel?: string;
  value: number;
  probability: number;
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
  } | null;
  nextSchedule?: {
    id: number;
    type: string;
    date: string;
    time: string;
    location: string;
  } | null;
  detailUrl?: string;
  aiDepartment?: {
    departmentId: number | null;
    departmentName: string;
    companyName: string;
    canUseAi: boolean;
    canAnalyze: boolean;
    hasAnalysis: boolean;
    message: string;
    summary: string;
    updatedAt: string | null;
    meetingCount: number;
    quoteCount: number;
    deliveryCount: number;
    painpointCount: number;
    unverifiedPainpointCount: number;
    href: string;
    hubHref: string;
    runHref: string;
  };
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

export type PipelineData = {
  source: 'mock' | 'django' | 'unavailable';
  generatedAt?: string;
  stages: StageSummary[];
  deals: Deal[];
  metrics: PipelineMetrics;
  priorityTasks: PriorityTask[];
};

export const mockStages: StageSummary[] = [
  { id: 'potential', label: '잠재', caption: '관심 확인' },
  { id: 'contact', label: '접촉/미팅', caption: '요구사항 파악' },
  { id: 'quote', label: '견적 제출', caption: '금액/범위 협의' },
  { id: 'negotiation', label: '협상', caption: '의사결정 추적' },
  { id: 'won', label: '수주', caption: '납품 전환' },
  { id: 'lost', label: '실주', caption: '원인 정리' },
];

export const mockDeals: Deal[] = [
  {
    id: 1,
    company: '한빛바이오 연구소',
    contact: '김민석 책임',
    department: '분석화학팀',
    owner: '안재현',
    stage: 'quote',
    stageLabel: '견적 제출',
    value: 18400000,
    probability: 64,
    nextAction: '장비 구성 변경 견적 재전송',
    due: '오늘 15:00',
    risk: 'high',
    tags: ['견적 지연', '고액'],
    lastActivity: '견적 제출 후 5일 경과',
    recentActivities: [
      { type: '견적', date: '05/03', summary: '장비 구성 변경 견적 재전송 필요' },
      { type: '고객 미팅', date: '04/29', summary: '예산은 확보됐고 납기 조건 확인 요청' },
    ],
    latestQuote: {
      number: 'Q-2026-001',
      stage: '발송완료',
      amount: 18400000,
      probability: 64,
      validUntil: '2026-05-30',
    },
    nextSchedule: {
      id: 101,
      type: '견적 제출',
      date: '2026-05-08',
      time: '15:00',
      location: '전화',
    },
  },
  {
    id: 2,
    company: '세종메디컬',
    contact: '박서연 팀장',
    department: '진단검사실',
    owner: '안재현',
    stage: 'contact',
    value: 7200000,
    probability: 42,
    nextAction: '시약 보관 조건 확인',
    due: '내일 10:30',
    risk: 'medium',
    tags: ['미팅 예정'],
    lastActivity: '담당자 변경 요청',
  },
  {
    id: 3,
    company: '동아임상센터',
    contact: '정우진 과장',
    department: '임상연구부',
    owner: '이수진',
    stage: 'negotiation',
    value: 32600000,
    probability: 78,
    nextAction: '계약 조건 최종 확인',
    due: '금요일',
    risk: 'medium',
    tags: ['수주 유력', '관리자 확인'],
    lastActivity: '가격 조정안 공유',
  },
  {
    id: 4,
    company: '네오랩스',
    contact: '최하늘 매니저',
    department: 'R&D',
    owner: '안재현',
    stage: 'potential',
    value: 3800000,
    probability: 18,
    nextAction: '초기 상담 메일 발송',
    due: '이번 주',
    risk: 'low',
    tags: ['신규'],
    lastActivity: '웹 문의 유입',
    attentionScore: 33,
    attentionReason: '최근 활동',
  },
  {
    id: 5,
    company: '바른진단의학과',
    contact: '오지훈 원장',
    department: '검사실',
    owner: '김도윤',
    stage: 'quote',
    value: 12800000,
    probability: 56,
    nextAction: '납기 일정 확인 전화',
    due: '오늘',
    risk: 'medium',
    tags: ['납기 문의'],
    lastActivity: '견적서 열람 확인',
  },
  {
    id: 6,
    company: '유니온 R&D',
    contact: '문채원 선임',
    department: '소재분석팀',
    owner: '이수진',
    stage: 'won',
    value: 21400000,
    probability: 100,
    nextAction: '납품 일정 등록',
    due: '다음 주 월',
    risk: 'low',
    tags: ['수주'],
    lastActivity: '발주서 수신',
    latestQuote: {
      number: '납품 #6',
      stage: '완료됨',
      amount: 21400000,
      probability: 100,
      source: '실제 납품 매출',
      basisType: 'delivery',
    },
    quoteComparison: {
      quotedAmount: 22000000,
      actualAmount: 21400000,
      deltaAmount: -600000,
      deltaRate: -2.7,
      status: 'under',
      statusLabel: '실매출 미달',
      source: '수주 견적',
      number: 'Q-2026-006',
    },
  },
];

const totalPipelineValue = mockDeals.reduce((sum, deal) => sum + deal.value, 0);
const weightedPipelineValue = mockDeals.reduce(
  (sum, deal) => sum + deal.value * (deal.probability / 100),
  0,
);

export const mockPipelineData: PipelineData = {
  source: 'mock',
  stages: mockStages,
  deals: mockDeals,
  metrics: {
    totalPipelineValue,
    weightedPipelineValue,
    activeCount: mockDeals.length,
    overdueCount: mockDeals.filter((deal) => deal.risk === 'high').length,
    contactCount: mockDeals.filter((deal) => deal.stage === 'contact').length,
  },
  priorityTasks: [
    { title: '견적 후속 지연 고객', count: 7, tone: 'danger' },
    { title: '오늘 연락 필요', count: 12, tone: 'warning' },
    { title: '관리자 검토 요청', count: 3, tone: 'info' },
  ],
};

export const emptyPipelineData: PipelineData = {
  source: 'unavailable',
  stages: mockStages,
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
