import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from 'react';
import {
    AlertTriangle,
    ArrowRightLeft,
    ChevronDown,
    ChevronRight,
    FileText,
    MoveUpRight,
    Search,
    Users,
    X
} from 'lucide-react';
import {
    DemoRecordItem,
    NoteItem,
    ScheduleItem
} from '../../api';
import { type MainView } from '../../components/shared/CrmShell';
import { DashboardEmpty } from '../../components/shared/FeedbackStates';
import {
    formatDateLabel,
    formatDateTimeLabel,
    formatNumber,
    formatWon
} from '../../components/shared/formatters';
import { type Deal, type PipelineData } from '../../pipelineTypes';


export const scheduleCalendarUrl = '/schedules/calendar/';

export type RouteAction = {
  label: string;
  href: string;
  primary?: boolean;
};

export type NoteCreateFormState = {
  actionType: string;
  activityDate: string;
  content: string;
  departmentId: string;
  followupId: string;
  nextAction: string;
  nextActionDate: string;
  scheduleId: string;
};

export type ScheduleCreateFormState = {
  activityType: string;
  departmentId: string;
  expectedRevenue: string;
  followupId: string;
  location: string;
  notes: string;
  probability: string;
  visitDate: string;
  visitTime: string;
};

export type ProfileFormState = {
  username: string;
  firstName: string;
  lastName: string;
  email: string;
};

export type ProfilePasswordFormState = {
  oldPassword: string;
  newPassword1: string;
  newPassword2: string;
};

export type ProductSortField = 'code' | 'description' | 'specification' | 'unit' | 'price' | 'status' | 'quoteCount' | 'deliveryCount' | 'updatedAt';
export type ProductSortOrder = 'asc' | 'desc';

export type DemoRecordFormState = {
  departmentId: string;
  customerId: string;
  productId: string;
  productName: string;
  serialNumber: string;
  quantity: string;
  status: string;
  startDate: string;
  expectedReturnDate: string;
  returnedDate: string;
  ownerId: string;
  notes: string;
};

export type SearchableSelectOption = {
  value: string;
  label: string;
  meta?: string;
  searchText?: string;
};

export type CustomerSelectSource = {
  id: number;
  departmentId?: number | null;
  companyId?: number | null;
  label?: string;
  customer?: string;
  customerName?: string;
  company?: string;
  companyName?: string;
  department?: string;
  departmentName?: string;
  email?: string;
  ownerName?: string;
  priorityLabel?: string;
};

export const localDateInputValue = (date = new Date()) => {
  const localTime = date.getTime() - date.getTimezoneOffset() * 60_000;
  return new Date(localTime).toISOString().slice(0, 10);
};

export const parseLocalDate = (value: string) => {
  const [year, month, day] = value.split('-').map(Number);
  if (!year || !month || !day) {
    return new Date();
  }
  return new Date(year, month - 1, day);
};

export const getScheduleCalendarRange = (monthValue: string) => {
  const [year, month] = monthValue.split('-').map(Number);
  const start = new Date(year, month - 1, 1);
  const end = new Date(year, month, 0);
  return {
    start: localDateInputValue(start),
    end: localDateInputValue(end),
  };
};

export const shouldOpenCreatePanel = () => new URLSearchParams(window.location.search).get('create') === '1';

export const guidedPanelFocusableSelector = [
  'input:not([type="hidden"]):not(:disabled):not([readonly])',
  'select:not(:disabled)',
  'textarea:not(:disabled):not([readonly])',
  'button:not(:disabled)',
  'a[href]',
  '[tabindex]:not([tabindex="-1"])',
].join(',');

export type GuidedPanelFocusRef = {
  current: HTMLElement | null;
};

export type GuidedPanelFocusKey = string | number | boolean | null | undefined;

export const requestGuidedPanelFocus = (
  targetRef: GuidedPanelFocusRef,
  options: { focusFirst?: boolean } = {},
) => {
  window.requestAnimationFrame(() => {
    window.requestAnimationFrame(() => {
      const section = targetRef.current;
      if (!section) {
        return;
      }
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
      section.classList.remove('guided-panel-focus');
      void section.offsetWidth;
      section.classList.add('guided-panel-focus');
      window.setTimeout(() => section.classList.remove('guided-panel-focus'), 1800);
      if (options.focusFirst === false) {
        return;
      }
      window.setTimeout(() => {
        const focusTarget = section.querySelector<HTMLElement>(guidedPanelFocusableSelector);
        focusTarget?.focus({ preventScroll: true });
      }, 280);
    });
  });
};

export function useGuidedPanelFocus(
  isOpen: boolean,
  targetRef: GuidedPanelFocusRef,
  focusKey: GuidedPanelFocusKey = 'open',
  options: { focusFirst?: boolean } = {},
) {
  const lastFocusKeyRef = useRef('');

  useEffect(() => {
    const normalizedKey = isOpen ? String(focusKey ?? 'open') : '';
    if (isOpen && normalizedKey && lastFocusKeyRef.current !== normalizedKey) {
      requestGuidedPanelFocus(targetRef, options);
    }
    lastFocusKeyRef.current = normalizedKey;
  }, [focusKey, isOpen, targetRef, options.focusFirst]);
}

export const isNoteActionAllowed = (actionTypes: Array<{ value: string }>, actionType: string) => (
  Boolean(actionType && actionTypes.some((option) => option.value === actionType))
);

export const makeEmptyScheduleCreateForm = (visitDate = localDateInputValue()): ScheduleCreateFormState => ({
  activityType: 'customer_meeting',
  departmentId: '',
  expectedRevenue: '',
  followupId: '',
  location: '',
  notes: '',
  probability: '',
  visitDate,
  visitTime: '09:00',
});

export const normalizeProbabilityInputValue = (value: string) => {
  const trimmed = value.trim();
  if (!trimmed) {
    return '';
  }
  const parsed = Number(trimmed);
  if (!Number.isFinite(parsed)) {
    return trimmed;
  }
  const normalized = Math.min(100, Math.max(0, Math.round(parsed / 5) * 5));
  return String(normalized);
};

export const isQuoteProbabilityRequired = (activityType: string) => activityType === 'quote';

export const normalizeQuoteGroupKey = (value: string) => value.trim().slice(0, 100);

export const quoteGroupLabel = (value: string) => normalizeQuoteGroupKey(value) || '기본 견적서';

export const routeMeta: Record<
  MainView,
  {
    eyebrow: string;
    title: string;
    summary: string;
    primaryHref: string;
    primaryLabel: string;
    actions: RouteAction[];
  }
> = {
  dashboard: {
    eyebrow: 'Sales CRM / Dashboard',
    title: '대시보드',
    summary: '영업 현황과 이번 주 접촉을 한 화면에서 확인합니다.',
    primaryHref: '/dashboard/',
    primaryLabel: '프론트 대시보드 보기',
    actions: [
      { label: '영업노트 작성', href: '/notes/?create=1', primary: true },
      { label: '미검토 노트', href: '/notes/?review=unreviewed' },
      { label: '일정 캘린더', href: scheduleCalendarUrl },
    ],
  },
  customers: {
    eyebrow: 'Sales CRM / Customers',
    title: '고객',
    summary: '고객, 업체, 부서, 팔로우업을 하나의 고객 업무 흐름으로 묶습니다.',
    primaryHref: '/customers/',
    primaryLabel: '프론트 고객 보기',
    actions: [
      { label: '파이프라인', href: '/pipeline/', primary: true },
    ],
  },
  companies: {
    eyebrow: 'Sales CRM / Companies',
    title: '업체/부서',
    summary: '업체와 부서/연구실 계정을 React에서 검색, 생성, 수정, 삭제 검토합니다.',
    primaryHref: '/companies/',
    primaryLabel: '업체/부서 관리 열기',
    actions: [
      { label: '업체/부서 관리', href: '/companies/', primary: true },
      { label: '고객 목록', href: '/customers/' },
    ],
  },
  demos: {
    eyebrow: 'Sales CRM / Demos',
    title: '데모관리',
    summary: '고객/계정별 데모 제품, 상태, 반납 예정일을 한 화면에서 관리합니다.',
    primaryHref: '/demos/?create=1',
    primaryLabel: '데모 등록',
    actions: [
      { label: '데모 등록', href: '/demos/?create=1', primary: true },
      { label: '고객 목록', href: '/customers/' },
      { label: '제품관리', href: '/products/' },
    ],
  },
  pipeline: {
    eyebrow: 'Sales CRM / Pipeline',
    title: '파이프라인 관리',
    summary: '견적, 협상, 수주 가능성을 중심으로 이번 주 우선 영업 건을 관리합니다.',
    primaryHref: '/pipeline/',
    primaryLabel: '파이프라인 보기',
    actions: [
      { label: '고객 목록', href: '/customers/' },
      { label: '영업노트', href: '/notes/' },
      { label: '일정 캘린더', href: scheduleCalendarUrl },
    ],
  },
  pipelineSheet: {
    eyebrow: 'Sales CRM / Pipeline Sheet',
    title: '파이프라인 시트',
    summary: '계정별 주간 활동과 이번 주 견적·납품 금액을 한 장에서 보고, 다음 주 계획을 세웁니다.',
    primaryHref: '/pipeline-sheet/',
    primaryLabel: '시트 보기',
    actions: [
      { label: '파이프라인', href: '/pipeline/' },
    ],
  },
  revenue: {
    eyebrow: 'Sales CRM / Revenue',
    title: '매출 내역',
    summary: '완료된 납품과 선결제만 모아 대시보드 매출 숫자의 실제 근거를 보여줍니다.',
    primaryHref: '/revenue/',
    primaryLabel: '매출 내역 보기',
    actions: [
      { label: '대시보드', href: '/dashboard/' },
    ],
  },
  notes: {
    eyebrow: 'Sales CRM / Notes',
    title: '영업노트',
    summary: '영업 활동 기록, 검토 상태, 고객별 히스토리를 빠르게 확인합니다.',
    primaryHref: '/notes/',
    primaryLabel: '프론트 영업노트 보기',
    actions: [
      { label: '노트 작성', href: '/notes/?create=1', primary: true },
      { label: '미검토 노트', href: '/notes/' },
    ],
  },
  schedules: {
    eyebrow: 'Sales CRM / Schedule',
    title: '일정',
    summary: '미팅, 견적, 납품 일정을 캘린더 중심으로 관리합니다.',
    primaryHref: scheduleCalendarUrl,
    primaryLabel: '일정 캘린더 열기',
    actions: [
      { label: '일정 캘린더', href: scheduleCalendarUrl, primary: true },
      { label: '새 일정 등록', href: '/schedules/?create=1' },
    ],
  },
  employees: {
    eyebrow: 'Sales CRM / Employees',
    title: '사용자/직원관리',
    summary: 'Admin은 전체 사용자, Manager는 같은 회사 직원을 React CRM에서 관리합니다.',
    primaryHref: '/employees/',
    primaryLabel: '사용자/직원관리 열기',
    actions: [
      { label: '사용자/직원관리', href: '/employees/', primary: true },
    ],
  },
  documents: {
    eyebrow: 'Sales CRM / Documents',
    title: '서류',
    summary: '견적서, 거래명세서, 납품서 템플릿을 관리하고 일정 서류 생성 흐름과 연결합니다.',
    primaryHref: '/documents/',
    primaryLabel: '서류 템플릿 관리',
    actions: [
      { label: '서류 등록', href: '/documents/?create=1', primary: true },
      { label: '일정', href: '/schedules/' },
      { label: '일정 캘린더', href: scheduleCalendarUrl },
    ],
  },
  products: {
    eyebrow: 'Sales CRM / Products',
    title: '제품',
    summary: '제품 기준단가, 규격, 단위, Ecount 반영 데이터를 React CRM에서 관리합니다.',
    primaryHref: '/products/',
    primaryLabel: '제품관리 열기',
    actions: [
      { label: '제품 등록', href: '/products/?create=1', primary: true },
      { label: '엑셀 다운로드', href: '/reporting/api/products/export.xlsx' },
      { label: '일정', href: '/schedules/' },
    ],
  },
  receivables: {
    eyebrow: 'Sales CRM / Receivables',
    title: '외상고객',
    summary: '납품 품목별 외상, 카드결제, 수금완료 상태를 한 곳에서 처리합니다.',
    primaryHref: '/receivables/',
    primaryLabel: '외상고객 열기',
    actions: [
      { label: '외상고객', href: '/receivables/', primary: true },
      { label: '납품 일정', href: '/schedules/' },
      { label: '고객 목록', href: '/customers/' },
    ],
  },
  prepayments: {
    eyebrow: 'Sales CRM / Prepayments',
    title: '선결제',
    summary: '고객별 선결제 입금, 잔액, 사용 현황을 React CRM에서 빠르게 확인합니다.',
    primaryHref: '/prepayments/',
    primaryLabel: '프론트 선결제 보기',
    actions: [
      { label: '선결제 등록', href: '/prepayments/new/', primary: true },
      { label: '고객 목록', href: '/customers/' },
      { label: '일정', href: '/schedules/' },
    ],
  },
  profile: {
    eyebrow: 'Sales CRM / Profile',
    title: '프로필',
    summary: '내 계정과 권한을 확인합니다.',
    primaryHref: '/profile/',
    primaryLabel: '프로필 열기',
    actions: [
      { label: '프로필 보기', href: '/profile/', primary: true },
    ],
  },
  notFound: {
    eyebrow: 'Sales CRM',
    title: '페이지를 찾을 수 없습니다',
    summary: '요청한 화면은 현재 CRM 메뉴에서 제공하지 않습니다.',
    primaryHref: '/dashboard/',
    primaryLabel: '대시보드로 이동',
    actions: [
      { label: '대시보드', href: '/dashboard/', primary: true },
      { label: '고객', href: '/customers/' },
    ],
  },
};

export function getCreateDateParam(): string {
  const value = new URLSearchParams(window.location.search).get('date') || '';
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return '';
  }
  return localDateInputValue(parseLocalDate(value)) === value ? value : '';
}



export const noteNextActionLabel = (note: Pick<NoteItem, 'nextAction' | 'nextActionDate'> & { nextActionDisplay?: string }) => (
  note.nextActionDisplay || note.nextAction || (note.nextActionDate ? '후속 예정' : '')
);


export const riskLabel: Record<Deal['risk'], string> = {
  low: '정상',
  medium: '확인',
  high: '지연',
};

export const searchableOptionLimit = 80;

export const joinOptionParts = (parts: Array<string | undefined>) => parts.filter(Boolean).join(' · ');

export const koreanAdministrativeAliasPairs: Array<[string, string]> = [
  ['서울특별시', '서울시'],
  ['부산광역시', '부산시'],
  ['대구광역시', '대구시'],
  ['인천광역시', '인천시'],
  ['광주광역시', '광주시'],
  ['대전광역시', '대전시'],
  ['울산광역시', '울산시'],
  ['세종특별자치시', '세종시'],
  ['제주특별자치도', '제주도'],
];

export function normalizeOptionText(value: string): string {
  return value.trim().toLocaleLowerCase('ko-KR').replace(/\s+/g, '');
}

export function searchableTextVariants(value: string): string[] {
  const normalized = normalizeOptionText(value);
  const variants = new Set([normalized]);
  koreanAdministrativeAliasPairs.forEach(([formal, short]) => {
    const formalText = normalizeOptionText(formal);
    const shortText = normalizeOptionText(short);
    if (normalized.includes(formalText)) {
      variants.add(normalized.split(formalText).join(shortText));
    }
    if (normalized.includes(shortText)) {
      variants.add(normalized.split(shortText).join(formalText));
    }
  });
  return Array.from(variants).filter(Boolean);
}

export function makeDepartmentSelectOption(department: { id: number; name: string; companyName?: string; searchText?: string }): SearchableSelectOption {
  const label = joinOptionParts([department.companyName, department.name]) || department.name;
  return {
    value: String(department.id),
    label,
    searchText: [label, department.searchText || ''].filter(Boolean).join(' '),
  };
}

export function makeCustomerSelectOption(customer: CustomerSelectSource): SearchableSelectOption {
  const label = customer.label || joinOptionParts([
    customer.company || customer.companyName,
    customer.department || customer.departmentName,
    customer.customer || customer.customerName,
  ]) || `고객 #${customer.id}`;
  const meta = joinOptionParts([customer.email, customer.ownerName, customer.priorityLabel]);
  return {
    value: String(customer.id),
    label,
    meta,
    searchText: [
      label,
      customer.company,
      customer.companyName,
      customer.department,
      customer.departmentName,
      customer.customer,
      customer.customerName,
      customer.email,
      customer.ownerName,
      customer.priorityLabel,
    ].filter(Boolean).join(' '),
  };
}

export function customerDepartmentValue(customer: CustomerSelectSource): string {
  return customer.departmentId ? String(customer.departmentId) : '';
}

export function customersForDepartment<T extends CustomerSelectSource>(customers: T[], departmentId: string): T[] {
  if (!departmentId) {
    return customers;
  }
  return customers.filter((customer) => customerDepartmentValue(customer) === departmentId);
}

export function SearchableSelect({
  allowEmpty = false,
  ariaLabel,
  className = '',
  disabled = false,
  emptyLabel = '선택 없음',
  onChange,
  onSearchChange,
  options,
  placeholder = '검색해서 선택',
  value,
}: {
  allowEmpty?: boolean;
  ariaLabel: string;
  className?: string;
  disabled?: boolean;
  emptyLabel?: string;
  onChange: (value: string) => void;
  onSearchChange?: (query: string) => void;
  options: SearchableSelectOption[];
  placeholder?: string;
  value: string;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const selectedOption = options.find((option) => option.value === value);
  useEffect(() => {
    onSearchChange?.(query);
  }, [onSearchChange, query]);
  const allOptions = useMemo(
    () => (allowEmpty ? [{ value: '', label: emptyLabel, searchText: emptyLabel }, ...options] : options),
    [allowEmpty, emptyLabel, options],
  );
  const filteredOptions = useMemo(() => {
    const normalizedQuery = normalizeOptionText(query);
    const queryVariants = searchableTextVariants(query);
    const matches = normalizedQuery
      ? allOptions.filter((option) => {
        const optionVariants = searchableTextVariants(`${option.label} ${option.meta || ''} ${option.searchText || ''}`);
        return queryVariants.some((queryVariant) => (
          optionVariants.some((optionVariant) => optionVariant.includes(queryVariant))
        ));
      })
      : allOptions;
    return matches.slice(0, searchableOptionLimit);
  }, [allOptions, query]);
  const inputValue = open ? query : selectedOption?.label || (!value && allowEmpty ? emptyLabel : '');

  useEffect(() => {
    setActiveIndex(0);
  }, [query, filteredOptions.length]);

  useEffect(() => {
    const handlePointerDown = (event: PointerEvent) => {
      if (!containerRef.current || containerRef.current.contains(event.target as Node)) {
        return;
      }
      setOpen(false);
      setQuery('');
    };
    document.addEventListener('pointerdown', handlePointerDown);
    return () => document.removeEventListener('pointerdown', handlePointerDown);
  }, []);

  const handleSelect = (nextValue: string) => {
    onChange(nextValue);
    setOpen(false);
    setQuery('');
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((index) => Math.min(index + 1, Math.max(filteredOptions.length - 1, 0)));
      return;
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((index) => Math.max(index - 1, 0));
      return;
    }
    if (event.key === 'Enter' && open) {
      event.preventDefault();
      const activeOption = filteredOptions[activeIndex];
      if (activeOption) {
        handleSelect(activeOption.value);
      }
      return;
    }
    if (event.key === 'Escape') {
      setOpen(false);
      setQuery('');
    }
  };

  return (
    <div
      className={`searchable-select ${open ? 'open' : ''} ${disabled ? 'disabled' : ''} ${className}`.trim()}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
          setOpen(false);
          setQuery('');
        }
      }}
      ref={containerRef}
    >
      <div aria-expanded={open} aria-haspopup="listbox" className="searchable-select-control" role="combobox">
        <Search size={15} />
        <input
          aria-autocomplete="list"
          aria-label={ariaLabel}
          className="searchable-select-input"
          disabled={disabled}
          onChange={(event) => {
            setQuery(event.target.value);
            setOpen(true);
          }}
          onFocus={() => {
            setQuery('');
            setOpen(true);
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          value={inputValue}
        />
        {allowEmpty && value ? (
          <button
            aria-label={`${ariaLabel} 선택 해제`}
            className="searchable-select-clear"
            disabled={disabled}
            onMouseDown={(event) => {
              event.preventDefault();
              handleSelect('');
            }}
            type="button"
          >
            <X size={14} />
          </button>
        ) : null}
        <button
          aria-label={`${ariaLabel} 목록 열기`}
          className="searchable-select-toggle"
          disabled={disabled}
          onMouseDown={(event) => {
            event.preventDefault();
            setOpen((current) => !current);
            setQuery('');
          }}
          type="button"
        >
          <ChevronDown size={15} />
        </button>
      </div>
      {open && !disabled ? (
        <div className="searchable-select-menu" role="listbox">
          {filteredOptions.length > 0 ? (
            filteredOptions.map((option, index) => (
              <button
                aria-selected={option.value === value}
                className={`searchable-select-option ${index === activeIndex ? 'active' : ''} ${option.value === value ? 'selected' : ''}`.trim()}
                key={`${option.value}-${option.label}`}
                onMouseDown={(event) => {
                  event.preventDefault();
                  handleSelect(option.value);
                }}
                onMouseEnter={() => setActiveIndex(index)}
                role="option"
                type="button"
              >
                <span>{option.label}</span>
                {option.meta ? <small>{option.meta}</small> : null}
              </button>
            ))
          ) : (
            <div className="searchable-select-empty">검색 결과 없음</div>
          )}
        </div>
      ) : null}
    </div>
  );
}

export function WorkspaceRoutePage({
  actions,
  data,
  view,
}: {
  actions?: typeof routeMeta[MainView]['actions'];
  data: PipelineData;
  view: MainView;
}) {
  const meta = routeMeta[view];
  const routeActions = actions ?? meta.actions;
  const urgentDeals = data.deals
    .filter((deal) => deal.risk === 'high' || deal.stage === 'quote' || deal.stage === 'negotiation')
    .slice(0, 5);
  const routeStats = [
    {
      label: '활성 고객',
      value: `${data.metrics.activeCount}건`,
      detail: '파이프라인 기준',
    },
    {
      label: '예상 매출',
      value: formatWon(data.metrics.weightedPipelineValue),
      detail: '확률 가중',
    },
  ];

  return (
    <section className="workspace-route-page">
      <div className="route-hero">
        <div>
          <span className="eyebrow">{meta.eyebrow}</span>
          <h2>{meta.title}</h2>
          <p>{meta.summary}</p>
        </div>
        <a className="route-primary-action" href={meta.primaryHref}>
          {meta.primaryLabel}
          <MoveUpRight size={16} />
        </a>
      </div>

      <div className="route-stat-grid">
        {routeStats.map((stat) => (
          <article className="route-stat-card" key={stat.label}>
            <span>{stat.label}</span>
            <strong>{stat.value}</strong>
            <small>{stat.detail}</small>
          </article>
        ))}
      </div>

      <div className="route-content-grid">
        <article className="route-card">
          <div className="panel-heading">
            <span>주요 작업</span>
            <ArrowRightLeft size={15} />
          </div>
          <div className="route-action-list">
            {routeActions.map((action) => (
              <a className={action.primary ? 'primary' : ''} href={action.href} key={action.label}>
                {action.label}
                <ChevronRight size={15} />
              </a>
            ))}
          </div>
        </article>

        <article className="route-card">
          <div className="panel-heading">
            <span>우선 확인 고객</span>
            <Users size={15} />
          </div>
          <div className="route-deal-list">
            {urgentDeals.map((deal) => (
              <a href={deal.detailUrl || `/customers/${deal.id}/`} key={deal.id}>
                <div>
                  <strong>{deal.company}</strong>
                  <span>{deal.contact} · {deal.owner}</span>
                </div>
                <small className={`risk-badge ${deal.risk}`}>{riskLabel[deal.risk]}</small>
              </a>
            ))}
          </div>
        </article>
      </div>
    </section>
  );
}

export function CustomerDetailNoteList({
  emptyLabel,
  notes,
  urgent,
}: {
  emptyLabel: string;
  notes: NoteItem[];
  urgent?: boolean;
}) {
  if (notes.length === 0) {
    return <DashboardEmpty label={emptyLabel} />;
  }

  return (
    <div className="dashboard-list customer-detail-note-list">
      {notes.map((note) => (
        <a className={`dashboard-list-row ${urgent || note.overdue ? 'urgent' : ''}`} href={note.href} key={note.id}>
          <div className="dashboard-row-icon">
            {urgent || note.overdue ? <AlertTriangle size={17} /> : <FileText size={17} />}
          </div>
          <div className="dashboard-row-main">
            <strong>{note.actionLabel}</strong>
            <span>{[note.owner, note.serviceStatusLabel].filter(Boolean).join(' · ')}</span>
            <small>{noteNextActionLabel(note) || note.summary || '내용 없음'}</small>
            {note.fileCount || note.replyCount ? (
              <small className="customer-note-submeta">
                {[note.fileCount ? `첨부 ${formatNumber(note.fileCount)}` : '', note.replyCount ? `댓글 ${formatNumber(note.replyCount)}` : ''].filter(Boolean).join(' · ')}
              </small>
            ) : null}
          </div>
          <time>{note.nextActionDate ? formatDateLabel(note.nextActionDate) : formatDateTimeLabel(note.createdAt)}</time>
        </a>
      ))}
    </div>
  );
}

export function DemoStatusBadge({ record }: { record: DemoRecordItem }) {
  const overdue = record.expectedReturnDate
    && ['scheduled', 'active'].includes(record.status)
    && record.expectedReturnDate < localDateInputValue();
  return (
    <div className="customer-badge-row service-badge-row">
      <span className={`service-case-status ${record.status}`}>{record.statusLabel}</span>
      {overdue ? <span className="schedule-overdue">반납 지연</span> : null}
    </div>
  );
}

export function SchedulesCompactList({
  emptyLabel,
  items,
  urgent,
}: {
  emptyLabel: string;
  items: ScheduleItem[];
  urgent?: boolean;
}) {
  if (items.length === 0) {
    return <DashboardEmpty label={emptyLabel} />;
  }

  return (
    <div className="schedules-compact-list">
      {items.map((item) => (
        <a className={`schedules-compact-row ${urgent || item.overdue ? 'urgent' : ''}`} href={item.href} key={`${item.type}-${item.id}`}>
          <div>
            <strong>{item.company || item.title || item.customer}</strong>
            <span>{[item.customer, item.activityLabel, item.owner].filter(Boolean).join(' · ')}</span>
            {item.notes ? <small>{item.notes}</small> : null}
          </div>
          <time>
            {item.date ? formatDateLabel(item.date) : ''}
            {item.time ? ` ${item.time}` : ''}
          </time>
        </a>
      ))}
    </div>
  );
}

export function PrepaymentStatusBadge({ status, label }: { status: string; label: string }) {
  return <span className={`prepayment-status ${status || 'unknown'}`}>{label || status || '상태 없음'}</span>;
}