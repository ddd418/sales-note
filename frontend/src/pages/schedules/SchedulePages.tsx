import { useEffect, useMemo, useRef, useState, type ChangeEvent, type FormEvent } from 'react';
import {
    AlertTriangle,
    Bell,
    CalendarDays,
    Check,
    CheckCircle2,
    ChevronDown,
    ChevronLeft,
    ChevronRight,
    CircleDollarSign,
    Clock,
    Copy,
    Download,
    Eye,
    FileSpreadsheet,
    FileText,
    Filter,
    Link2,
    ListChecks,
    Loader2,
    MessageSquareText,
    MoveUpRight,
    PanelRight,
    Pencil,
    Plus,
    RefreshCw,
    Search,
    Sparkles,
    Trash2,
    Users,
    X
} from 'lucide-react';
import {
    FollowupQuoteItem,
    FollowupQuoteItemsData,
    FollowupQuoteOption,
    NoteCreatePayload,
    PersonalScheduleDetailData,
    PersonalSchedulePayload,
    ProductOption,
    ScheduleCalendarData,
    ScheduleCreatePayload,
    ScheduleDeliveryItem,
    ScheduleDeliveryItemPayload,
    ScheduleDetailData,
    ScheduleDetailItem,
    ScheduleDocumentAction,
    ScheduleDocumentFormatAction,
    ScheduleDocumentPreviewData,
    ScheduleDocumentRequestOptions,
    ScheduleEditPayload,
    ScheduleFileItem,
    ScheduleGeneratedDocument,
    ScheduleItem,
    SchedulesData,
    createSchedule as createCustomerSchedule,
    createPersonalSchedule,
    createNote as createSalesNote,
    deleteGeneratedDocument,
    deleteSchedule,
    deleteScheduleFile,
    downloadScheduleDocument,
    loadFollowupQuoteItems,
    loadPersonalScheduleDetailData,
    loadProducts,
    loadScheduleDetailData,
    loadScheduleDocumentPreview,
    updateSchedule as updateCustomerSchedule,
    updatePersonalSchedule,
    updateScheduleDeliveryItems,
    uploadScheduleFiles
} from '../../api';
import type {
    AIWorkspaceActionEvidence,
    ScheduleAICoachResponse,
} from '../../api/ai';
import {
    generateScheduleAICoach,
} from '../../api/ai';
import type {
    PrepaymentOption,
    SchedulePrepaymentSelectionPayload
} from '../../api/prepayments';
import {
    loadPrepayments
} from '../../api/prepayments';
import { AttachmentManager, type AttachmentManagerFile } from '../../components/shared/AttachmentManager';
import { DashboardMetricCard } from '../../components/shared/DashboardMetricCard';
import { DashboardApiAlert, DashboardEmpty } from '../../components/shared/FeedbackStates';
import {
    formatDateLabel,
    formatDateTimeLabel,
    formatNumber,
    formatWon
} from '../../components/shared/formatters';
import { CustomerDetailNoteList, NoteCreateFormState, ScheduleCreateFormState, SchedulesCompactList, SearchableSelect, VatModeField, grossFromSubtotal, vatModeLabel, customersForDepartment, getCreateDateParam, getScheduleCalendarRange, isQuoteProbabilityRequired, localDateInputValue, makeCustomerSelectOption, makeDepartmentSelectOption, makeEmptyScheduleCreateForm, normalizeProbabilityInputValue, normalizeQuoteGroupKey, parseLocalDate, quoteGroupLabel, useGuidedPanelFocus } from '../shared/appShared';


type ScheduleEditFormState = ScheduleCreateFormState & {
  expectedCloseDate: string;
  purchaseConfirmed: boolean;
  status: string;
  usePrepayment: boolean;
};

type PersonalScheduleFormState = {
  title: string;
  content: string;
  scheduleDate: string;
  scheduleTime: string;
};

type SchedulePrepaymentEditRow = PrepaymentOption & {
  selected: boolean;
  amountInput: string;
};

type ScheduleDeliveryEditRow = {
  rowId: string;
  id?: number;
  productId: string;
  productQuery: string;
  itemName: string;
  quantity: string;
  unit: string;
  unitPrice: string;
  discountRate: string;
  discountUnitPrice: string;
  quoteGroup: string;
  notes: string;
  optionDescription: string;
  sourceQuoteScheduleId: string;
  sourceQuoteItemId: string;
};

type ScheduleDeliveryEditField = 'productId' | 'productQuery' | 'itemName' | 'quantity' | 'unit' | 'unitPrice' | 'discountRate' | 'discountUnitPrice' | 'quoteGroup' | 'notes' | 'optionDescription';

type ScheduleQuoteGroupNoteState = Record<string, string>;

const shiftScheduleCalendarMonth = (monthValue: string, offset: number) => {
  const [year, month] = monthValue.split('-').map(Number);
  const shifted = new Date(year, month - 1 + offset, 1);
  return localDateInputValue(shifted).slice(0, 7);
};

const getScheduleCalendarCreateParam = () => (
  new URLSearchParams(window.location.search).get('create') || ''
);

const getScheduleCalendarPersonalIdParam = () => {
  const value = new URLSearchParams(window.location.search).get('personal') || '';
  const id = Number(value);
  return Number.isFinite(id) && id > 0 ? id : 0;
};

const scheduleActivityToNoteActionType = (activityType: string) => {
  if (activityType === 'delivery') {
    return 'delivery_schedule';
  }
  if (activityType === 'quote') {
    return 'quote';
  }
  if (activityType === 'service') {
    return 'service';
  }
  return 'customer_meeting';
};

const scheduleNoteActionTypeOptions = [
  { value: 'customer_meeting', label: '고객 미팅' },
  { value: 'quote', label: '견적' },
  { value: 'delivery_schedule', label: '납품 일정' },
  { value: 'service', label: '메모' },
];

const makeScheduleNoteCreateForm = (schedule: ScheduleDetailItem | null): NoteCreateFormState => ({
  actionType: scheduleActivityToNoteActionType(schedule?.activityType || ''),
  activityDate: schedule?.date || localDateInputValue(),
  content: '',
  departmentId: schedule?.departmentId ? String(schedule.departmentId) : '',
  followupId: schedule?.followupId ? String(schedule.followupId) : '',
  nextAction: '',
  nextActionDate: '',
  scheduleId: schedule?.id ? String(schedule.id) : '',
});

const probabilityInputValueFromSchedule = (probability: number | null | undefined) => (
  probability === null || probability === undefined ? '' : String(probability)
);

const makeScheduleEditForm = (schedule: ScheduleDetailItem | null): ScheduleEditFormState => ({
  activityType: schedule?.activityType || 'customer_meeting',
  departmentId: schedule?.departmentId ? String(schedule.departmentId) : '',
  expectedCloseDate: schedule?.expectedCloseDate || '',
  expectedRevenue: schedule?.expectedRevenue ? String(schedule.expectedRevenue) : '',
  followupId: schedule?.followupId ? String(schedule.followupId) : '',
  location: schedule?.location || '',
  notes: schedule?.notesFull || schedule?.notes || '',
  probability: probabilityInputValueFromSchedule(schedule?.probability),
  vatMode: schedule?.vatMode || '',
  purchaseConfirmed: Boolean(schedule?.purchaseConfirmed),
  status: schedule?.status || 'scheduled',
  usePrepayment: Boolean(schedule?.usePrepayment),
  visitDate: schedule?.date || '',
  visitTime: schedule?.time || '09:00',
});

const makeEmptyPersonalScheduleForm = (scheduleDate = localDateInputValue()): PersonalScheduleFormState => ({
  title: '',
  content: '',
  scheduleDate,
  scheduleTime: '09:00',
});

const makePersonalScheduleEditForm = (schedule: ScheduleItem | null): PersonalScheduleFormState => ({
  title: schedule?.title || '',
  content: schedule?.notesFull || schedule?.notes || '',
  scheduleDate: schedule?.date || localDateInputValue(),
  scheduleTime: schedule?.time || '09:00',
});

const makeScheduleCalendarCreateForm = (data: ScheduleCalendarData | null, visitDate: string): ScheduleCreateFormState => {
  const form = makeEmptyScheduleCreateForm(visitDate);
  form.activityType = data?.create.activityTypes[0]?.value || form.activityType;
  const firstCustomer = data?.create.customers[0];
  const firstDepartmentId = firstCustomer?.departmentId ?? data?.create.departments[0]?.id;
  form.departmentId = firstDepartmentId ? String(firstDepartmentId) : '';
  form.followupId = firstCustomer?.id ? String(firstCustomer.id) : '';
  return form;
};

const scheduleCreateFormToPayload = (form: ScheduleCreateFormState): { payload?: ScheduleCreatePayload; error?: string } => {
  const followupId = Number(form.followupId);
  const departmentId = Number(form.departmentId);
  if (!followupId && !departmentId) {
    return { error: '고객 또는 부서/연구실을 선택하세요.' };
  }
  if (!form.activityType) {
    return { error: '일정 유형을 선택하세요.' };
  }
  if (!form.visitDate) {
    return { error: '일정 날짜를 선택하세요.' };
  }
  if (!form.visitTime) {
    return { error: '일정 시간을 선택하세요.' };
  }
  const probability = normalizeProbabilityInputValue(form.probability);
  if (isQuoteProbabilityRequired(form.activityType) && !probability) {
    return { error: '견적 성공 확률은 필수입니다.' };
  }

  return {
    payload: {
      activityType: form.activityType,
      departmentId: departmentId || undefined,
      expectedRevenue: form.expectedRevenue.trim() || undefined,
      vatMode: form.vatMode || undefined,
      followupId: followupId || undefined,
      location: form.location.trim() || undefined,
      notes: form.notes.trim() || undefined,
      probability: probability || undefined,
      visitDate: form.visitDate,
      visitTime: form.visitTime,
    },
  };
};

const personalScheduleFormToPayload = (form: PersonalScheduleFormState): { payload?: PersonalSchedulePayload; error?: string } => {
  if (!form.title.trim()) {
    return { error: '일정 제목을 입력하세요.' };
  }
  if (!form.scheduleDate) {
    return { error: '일정 날짜를 선택하세요.' };
  }
  if (!form.scheduleTime) {
    return { error: '일정 시간을 선택하세요.' };
  }

  return {
    payload: {
      title: form.title.trim(),
      content: form.content.trim() || undefined,
      scheduleDate: form.scheduleDate,
      scheduleTime: form.scheduleTime,
    },
  };
};

const scheduleEditFormToPayload = (form: ScheduleEditFormState): { payload?: ScheduleEditPayload; error?: string } => {
  const followupId = Number(form.followupId);
  if (!followupId) {
    return { error: '고객을 선택하세요.' };
  }
  if (!form.activityType) {
    return { error: '일정 유형을 선택하세요.' };
  }
  if (!form.status) {
    return { error: '일정 상태를 선택하세요.' };
  }
  if (!form.visitDate) {
    return { error: '일정 날짜를 선택하세요.' };
  }
  if (!form.visitTime) {
    return { error: '일정 시간을 선택하세요.' };
  }
  const probability = normalizeProbabilityInputValue(form.probability);
  if (isQuoteProbabilityRequired(form.activityType) && !probability) {
    return { error: '견적 성공 확률은 필수입니다.' };
  }

  return {
    payload: {
      activityType: form.activityType,
      expectedCloseDate: form.expectedCloseDate || undefined,
      expectedRevenue: form.expectedRevenue.trim() || undefined,
      vatMode: form.vatMode || undefined,
      followupId,
      location: form.location.trim() || undefined,
      notes: form.notes.trim() || undefined,
      probability: probability || undefined,
      purchaseConfirmed: form.purchaseConfirmed,
      status: form.status,
      visitDate: form.visitDate,
      visitTime: form.visitTime,
    },
  };
};

const makeSchedulePrepaymentRows = (options: PrepaymentOption[] = []): SchedulePrepaymentEditRow[] => (
  options.map((option) => ({
    ...option,
    selected: option.selectedAmount > 0,
    amountInput: option.selectedAmount > 0 ? String(option.selectedAmount) : '',
  }))
);

const makeScheduleDeliveryEditRow = (item?: ScheduleDeliveryItem, index = 0): ScheduleDeliveryEditRow => ({
  rowId: item ? `delivery-${item.id}` : `delivery-new-${Date.now()}-${index}`,
  id: item?.id,
  productId: item?.productId ? String(item.productId) : '',
  productQuery: item?.productCode || '',
  itemName: item?.itemName || '',
  quantity: item ? String(item.quantity) : '1',
  unit: item?.unit || 'EA',
  unitPrice: item && item.unitPrice !== undefined && item.unitPrice !== null ? String(item.unitPrice) : '',
  discountRate: item?.discountRate ? String(item.discountRate) : '',
  discountUnitPrice: item?.discountUnitPrice !== undefined && item.discountUnitPrice !== null ? String(item.discountUnitPrice) : '',
  quoteGroup: item?.quoteGroup || '',
  notes: item?.notes || '',
  optionDescription: item?.optionDescription || '',
  sourceQuoteScheduleId: item?.sourceQuoteScheduleId ? String(item.sourceQuoteScheduleId) : '',
  sourceQuoteItemId: item?.sourceQuoteItemId ? String(item.sourceQuoteItemId) : '',
});

const makeScheduleDeliveryEditRows = (items: ScheduleDeliveryItem[] = []): ScheduleDeliveryEditRow[] => (
  items.length > 0
    ? items.map((item, index) => makeScheduleDeliveryEditRow(item, index))
    : [makeScheduleDeliveryEditRow(undefined, 0)]
);

const quoteImportOptionTitle = (quote: FollowupQuoteOption) => {
  const label = quote.quoteGroupLabel || quoteGroupLabel(quote.quoteGroup);
  return label.includes('견적') ? label : `${label} 견적`;
};

const quoteImportItemSummary = (item: FollowupQuoteItem) => {
  const remaining = item.remainingQuantity || item.quantity || 0;
  const original = item.originalQuantity || remaining;
  const unit = item.unit || '';
  const numberLabel = (value: number) => new Intl.NumberFormat('ko-KR').format(value);
  const quantityLabel = original > remaining
    ? `${numberLabel(remaining)}/${numberLabel(original)}${unit}`
    : `${numberLabel(remaining)}${unit}`;
  return `${item.itemName || item.productCode || '품목'} ${quantityLabel}`;
};

const makeScheduleQuoteGroupNotes = (schedule: ScheduleDetailItem | null): ScheduleQuoteGroupNoteState => {
  const notes: ScheduleQuoteGroupNoteState = {};
  schedule?.quoteGroupNotes?.forEach((item) => {
    notes[normalizeQuoteGroupKey(item.quoteGroup)] = item.notes || '';
  });
  if (!notes[''] && schedule?.quoteExtraNotes) {
    notes[''] = schedule.quoteExtraNotes;
  }
  return notes;
};

const scheduleQuoteGroupsFromRows = (rows: ScheduleDeliveryEditRow[]): string[] => {
  const seen = new Set<string>();
  const groups: string[] = [];
  rows.forEach((row) => {
    const hasItemInput = Boolean(
      row.productId ||
      row.itemName.trim() ||
      row.quantity.trim() ||
      row.unitPrice.trim() ||
      row.discountRate.trim() ||
      row.discountUnitPrice.trim() ||
      row.notes.trim() ||
      row.optionDescription.trim(),
    );
    if (!hasItemInput && !row.quoteGroup.trim()) {
      return;
    }
    const group = normalizeQuoteGroupKey(row.quoteGroup);
    if (seen.has(group)) {
      return;
    }
    seen.add(group);
    groups.push(group);
  });
  return groups.length > 0 ? groups : [''];
};

const parsePositiveFormNumber = (value: string) => {
  const normalized = String(value ?? '').replace(/,/g, '').trim();
  if (!normalized) {
    return null;
  }
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : null;
};

const moneyInputValue = (value: number) => String(Math.round(value));

const rateInputValue = (value: number) => {
  if (!Number.isFinite(value)) return '';
  return String(Math.round(value * 100) / 100);
};

const discountUnitFromRate = (base: number, rate: number) => (
  Math.max(Math.round(base * (100 - rate) / 100), 0)
);

const discountRateFromUnit = (base: number, discountUnit: number) => (
  base > 0 ? Math.max(Math.min((1 - discountUnit / base) * 100, 100), 0) : 0
);

const scheduleDeliveryEditRowsTotal = (rows: ScheduleDeliveryEditRow[], vatMode?: string) => (
  rows.reduce((total, row) => {
    const quantity = Number(row.quantity);
    const unitPrice = parsePositiveFormNumber(row.unitPrice);
    const discountUnitPrice = parsePositiveFormNumber(row.discountUnitPrice);
    const discountRate = parsePositiveFormNumber(row.discountRate);
    if (!Number.isFinite(quantity) || quantity <= 0 || unitPrice === null || unitPrice < 0) {
      return total;
    }
    let effectiveUnitPrice = unitPrice;
    if (discountUnitPrice !== null) {
      effectiveUnitPrice = Math.max(discountUnitPrice, 0);
    } else if (discountRate !== null) {
      effectiveUnitPrice = discountUnitFromRate(unitPrice, Math.min(Math.max(discountRate, 0), 100));
    }
    return total + Math.round(grossFromSubtotal(quantity * effectiveUnitPrice, vatMode));
  }, 0)
);

const makeScheduleDeliveryEditRowFromQuoteItem = (
  item: FollowupQuoteItem,
  quote: FollowupQuoteOption,
  index: number,
): ScheduleDeliveryEditRow => {
  const quantity = item.quantity || 1;
  const itemTotal = item.totalPrice || item.remainingAmount || 0;
  const quoteSingleItemFallback = quote.items.length === 1 ? quote.remainingAmount || quote.expectedRevenue || 0 : 0;
  const totalFallback = itemTotal || quoteSingleItemFallback;
  const fallbackUnitPrice = totalFallback > 0 && quantity > 0
    ? Math.round(totalFallback / quantity / 1.1)
    : 0;
  const unitPrice = item.unitPrice > 0
    ? item.unitPrice
    : item.effectiveUnitPrice > 0
      ? item.effectiveUnitPrice
      : fallbackUnitPrice;
  const usesOriginalUnitPrice = item.unitPrice > 0;
  const hasExplicitDiscount = usesOriginalUnitPrice
    && item.discountUnitPrice !== undefined
    && item.discountUnitPrice !== null
    && (item.discountRate > 0 || item.discountUnitPrice < unitPrice);
  return {
    rowId: `quote-${quote.optionId}-${item.id ?? index}-${Date.now()}-${index}`,
    productId: item.productId ? String(item.productId) : '',
    productQuery: item.productCode || '',
    itemName: item.itemName || item.productCode || '',
    quantity: String(quantity),
    unit: item.unit || 'EA',
    unitPrice: unitPrice > 0 ? moneyInputValue(unitPrice) : '',
    discountRate: usesOriginalUnitPrice && item.discountRate ? rateInputValue(item.discountRate) : '',
    discountUnitPrice: hasExplicitDiscount ? moneyInputValue(item.discountUnitPrice ?? 0) : '',
    quoteGroup: item.quoteGroup || '',
    notes: item.notes || '',
    optionDescription: item.optionDescription || '',
    sourceQuoteScheduleId: item.sourceQuoteScheduleId ? String(item.sourceQuoteScheduleId) : String(quote.scheduleId || ''),
    sourceQuoteItemId: item.sourceQuoteItemId ? String(item.sourceQuoteItemId) : String(item.id || ''),
  };
};

const scheduleDeliveryRowsHaveUserInput = (rows: ScheduleDeliveryEditRow[]) => rows.some((row) => Boolean(
  row.id ||
  row.productId ||
  row.itemName.trim() ||
  row.unitPrice.trim() ||
  row.discountRate.trim() ||
  row.discountUnitPrice.trim() ||
  row.quoteGroup.trim() ||
  row.notes.trim() ||
  row.optionDescription.trim()
));

function getCreateTimeParam(): string {
  const value = new URLSearchParams(window.location.search).get('time') || '';
  return /^([01]\d|2[0-3]):[0-5]\d$/.test(value) ? value : '';
}

function appendDateQuery(href: string, dateValue: string): string {
  if (!dateValue) {
    return href;
  }
  const separator = href.includes('?') ? '&' : '?';
  return `${href}${separator}date=${encodeURIComponent(dateValue)}`;
}

function ScheduleStatusBadge({ schedule }: { schedule: ScheduleItem }) {
  return (
    <div className="customer-badge-row schedules-badge-row">
      <span className={`schedule-status ${schedule.status}`}>{schedule.statusLabel}</span>
      <span>{schedule.activityLabel}</span>
      {schedule.priorityLabel ? <span>{schedule.priorityLabel}</span> : null}
      {schedule.overdue ? <span className="schedule-overdue">지연</span> : null}
    </div>
  );
}

function SchedulesCountRows({ data }: { data: SchedulesData }) {
  const maxCount = Math.max(...data.statusCounts.map((item) => item.count), 1);
  return (
    <div className="notes-action-counts">
      {data.statusCounts.map((item) => (
        <div className="notes-action-count-row" key={item.value}>
          <div>
            <span>{item.label}</span>
            <strong>{formatNumber(item.count)}건</strong>
          </div>
          <div className="notes-count-bar">
            <div style={{ width: `${(item.count / maxCount) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function SchedulesTable({ schedules }: { schedules: ScheduleItem[] }) {
  if (schedules.length === 0) {
    return <DashboardEmpty label="조건에 맞는 일정이 없습니다" />;
  }

  return (
    <div className="customers-table-wrap schedules-table-wrap">
      <table className="customers-table schedules-table">
        <thead>
          <tr>
            <th>일정</th>
            <th>일시</th>
            <th>상태</th>
            <th>금액/보고</th>
            <th>담당자</th>
          </tr>
        </thead>
        <tbody>
          {schedules.map((schedule) => (
            <tr key={`${schedule.type}-${schedule.id}`}>
              <td>
                <a className="customer-name-link" href={schedule.href}>
                  <strong>{schedule.company || schedule.title || schedule.customer}</strong>
                  <span>{[schedule.customer, schedule.department, schedule.location].filter(Boolean).join(' · ')}</span>
                  {schedule.notes ? <small>{schedule.notes}</small> : null}
                </a>
              </td>
              <td>
                <span className={schedule.overdue ? 'customer-overdue-text' : ''}>
                  {schedule.date ? formatDateLabel(schedule.date) : '날짜 없음'}
                </span>
                {schedule.time ? <small>{schedule.time}</small> : null}
              </td>
              <td>
                <ScheduleStatusBadge schedule={schedule} />
              </td>
              <td>
                {schedule.expectedRevenue > 0 ? <span>{formatWon(schedule.expectedRevenue)}</span> : <span>예상 매출 없음</span>}
                <small>보고 {formatNumber(schedule.historyCount)}건</small>
                <div className="notes-row-actions">
                  {schedule.createHistoryHref ? <a className="customer-row-action" href={schedule.createHistoryHref}>보고</a> : null}
                  {schedule.customerHref ? <a className="customer-row-action" href={schedule.customerHref}>고객</a> : null}
                </div>
              </td>
              <td>
                <span>{schedule.owner}</span>
                <a className="customer-row-action" href={schedule.href}>상세</a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function buildScheduleCalendarDays(monthValue: string, schedules: ScheduleItem[]) {
  const [year, month] = monthValue.split('-').map(Number);
  const firstDay = new Date(year, month - 1, 1);
  const gridStart = new Date(firstDay);
  gridStart.setDate(firstDay.getDate() - ((firstDay.getDay() + 6) % 7));
  const todayValue = localDateInputValue();
  const schedulesByDate = new Map<string, ScheduleItem[]>();

  schedules.forEach((schedule) => {
    if (!schedule.date) {
      return;
    }
    const items = schedulesByDate.get(schedule.date) ?? [];
    items.push(schedule);
    schedulesByDate.set(schedule.date, items);
  });
  schedulesByDate.forEach((items) => {
    items.sort((a, b) => `${a.time} ${a.type}`.localeCompare(`${b.time} ${b.type}`));
  });

  return Array.from({ length: 42 }, (_item, index) => {
    const date = new Date(gridStart);
    date.setDate(gridStart.getDate() + index);
    const dateValue = localDateInputValue(date);
    return {
      date: dateValue,
      dayNumber: date.getDate(),
      inMonth: date.getMonth() === month - 1,
      isToday: dateValue === todayValue,
      schedules: schedulesByDate.get(dateValue) ?? [],
    };
  });
}

function getScheduleReportPreviewLines(report: NonNullable<ScheduleItem['reports']>[number]) {
  const lines = [
    report.content,
    report.deliveryItems ? `납품 품목: ${report.deliveryItems}` : '',
    report.deliveryAmount > 0 ? `납품 금액: ${formatWon(report.deliveryAmount)}` : '',
    report.nextAction ? `다음 액션: ${report.nextAction}` : '',
  ].filter(Boolean);

  if (lines.length > 0) {
    return lines;
  }
  return report.summary ? [report.summary] : [];
}

function ScheduleCalendarSelectedList({
  deletingKey,
  items,
  statusUpdatingKey,
  onDelete,
  onEdit,
  onStatusChange,
}: {
  deletingKey: string;
  items: ScheduleItem[];
  statusUpdatingKey: string;
  onDelete: (schedule: ScheduleItem) => void;
  onEdit: (schedule: ScheduleItem) => void;
  onStatusChange: (schedule: ScheduleItem, status: string) => void;
}) {
  if (items.length === 0) {
    return <DashboardEmpty label="선택한 날짜의 일정이 없습니다" />;
  }

  return (
    <div className="schedule-calendar-selected-list">
      {items.map((item) => {
        const itemKey = `${item.type}-${item.id}`;
        const statusOptions = item.statusOptions ?? [];
        const reports = item.reports ?? [];
        const canChangeStatus = item.type === 'customer' && Boolean(item.canEdit && item.statusUpdateHref && statusOptions.length);
        const canManage = Boolean(item.canEdit);
        const isUpdating = statusUpdatingKey === itemKey;
        const isDeleting = deletingKey === itemKey;
        return (
          <article className={`schedule-calendar-selected-card ${item.overdue ? 'urgent' : ''}`} key={itemKey}>
            <div className="schedule-calendar-selected-main">
              <div>
                <strong>{item.company || item.title || item.customer}</strong>
                <span>{[item.customer, item.department, item.activityLabel, item.owner].filter(Boolean).join(' · ')}</span>
                {item.notes ? <small>{item.notes}</small> : null}
              </div>
              <time>
                {item.time || '시간 없음'}
              </time>
            </div>
            <ScheduleStatusBadge schedule={item} />
            {reports.length > 0 ? (
              <div className="schedule-calendar-report-list">
                <div className="schedule-calendar-report-heading">
                  <span>보고 내용</span>
                  <small>{reports.length}건</small>
                </div>
                {reports.map((report) => {
                  const previewLines = getScheduleReportPreviewLines(report);
                  return (
                    <div className="schedule-calendar-report-item" key={report.id}>
                      <div className="schedule-calendar-report-meta">
                        <strong>{report.actionLabel}</strong>
                        <span>{report.activityDate ? formatDateLabel(report.activityDate) : formatDateTimeLabel(report.createdAt)}</span>
                      </div>
                      {previewLines.length > 0 ? (
                        <div className="schedule-calendar-report-body">
                          {previewLines.map((line, index) => <p key={`${report.id}-${index}`}>{line}</p>)}
                        </div>
                      ) : (
                        <p className="schedule-calendar-report-empty">보고 내용이 비어 있습니다.</p>
                      )}
                      <a href={report.href}>보고 상세</a>
                    </div>
                  );
                })}
              </div>
            ) : null}
            <div className="schedule-calendar-selected-actions">
              {canManage ? (
                <button onClick={() => onEdit(item)} type="button">
                  <Pencil size={13} />
                  수정
                </button>
              ) : null}
              {canManage ? (
                <button className="danger" disabled={isDeleting} onClick={() => onDelete(item)} type="button">
                  {isDeleting ? <Loader2 className="spin-icon" size={13} /> : <Trash2 size={13} />}
                  삭제
                </button>
              ) : null}
              <a href={item.href}>상세</a>
              {item.customerHref ? <a href={item.customerHref}>고객</a> : null}
              {item.createHistoryHref ? <a href={item.createHistoryHref}>보고</a> : null}
            </div>
            {canChangeStatus ? (
              <div className="schedule-calendar-status-actions" aria-label={`${item.customer || item.title} 상태 변경`}>
                {statusOptions.map((option) => (
                  <button
                    className={option.value === item.status ? 'active' : ''}
                    disabled={isUpdating || option.value === item.status}
                    key={option.value}
                    onClick={() => onStatusChange(item, option.value)}
                    type="button"
                  >
                    {isUpdating && option.value !== item.status ? <Loader2 className="spin-icon" size={13} /> : null}
                    {option.label}
                  </button>
                ))}
              </div>
            ) : null}
          </article>
        );
      })}
    </div>
  );
}

export function ScheduleCalendarPage({
  data,
  dataFilter,
  filterUser,
  loading,
  month,
  statusError,
  statusMessage,
  statusUpdatingKey,
  onDataFilterChange,
  onFilterUserChange,
  onMonthChange,
  onRefresh,
  onStatusChange,
}: {
  data: ScheduleCalendarData | null;
  dataFilter: string;
  filterUser: string;
  loading: boolean;
  month: string;
  statusError: string;
  statusMessage: string;
  statusUpdatingKey: string;
  onDataFilterChange: (value: string) => void;
  onFilterUserChange: (value: string) => void;
  onMonthChange: (value: string) => void;
  onRefresh: () => Promise<ScheduleCalendarData | null>;
  onStatusChange: (schedule: ScheduleItem, status: string) => void;
}) {
  const range = useMemo(() => getScheduleCalendarRange(month), [month]);
  const initialIntentRef = useRef({
    create: getScheduleCalendarCreateParam(),
    date: getCreateDateParam(),
    time: getCreateTimeParam(),
    personalId: getScheduleCalendarPersonalIdParam(),
    createHandled: false,
    personalHandled: false,
  });
  const [selectedDate, setSelectedDate] = useState(() => {
    const intentDate = initialIntentRef.current.date;
    if (intentDate) {
      return intentDate;
    }
    const today = localDateInputValue();
    return today >= range.start && today <= range.end ? today : range.start;
  });
  const [calendarCreateOpen, setCalendarCreateOpen] = useState(false);
  const [calendarCreateForm, setCalendarCreateForm] = useState<ScheduleCreateFormState>(() => makeEmptyScheduleCreateForm());
  const [calendarCreating, setCalendarCreating] = useState(false);
  const [calendarCreateError, setCalendarCreateError] = useState('');
  const [calendarCreateMessage, setCalendarCreateMessage] = useState('');
  const [calendarCreatedDetailHref, setCalendarCreatedDetailHref] = useState('');
  const [personalCreateOpen, setPersonalCreateOpen] = useState(false);
  const [personalCreateForm, setPersonalCreateForm] = useState<PersonalScheduleFormState>(() => makeEmptyPersonalScheduleForm());
  const [personalCreating, setPersonalCreating] = useState(false);
  const [personalCreateError, setPersonalCreateError] = useState('');
  const [personalCreateMessage, setPersonalCreateMessage] = useState('');
  const [personalCreatedDetailHref, setPersonalCreatedDetailHref] = useState('');
  const [calendarEditOpen, setCalendarEditOpen] = useState(false);
  const [calendarEditLoading, setCalendarEditLoading] = useState(false);
  const [calendarEditData, setCalendarEditData] = useState<ScheduleDetailData | null>(null);
  const [calendarEditForm, setCalendarEditForm] = useState<ScheduleEditFormState>(() => makeScheduleEditForm(null));
  const [calendarEditSaving, setCalendarEditSaving] = useState(false);
  const [calendarEditError, setCalendarEditError] = useState('');
  const [calendarEditMessage, setCalendarEditMessage] = useState('');
  const [personalEditOpen, setPersonalEditOpen] = useState(false);
  const [personalEditLoading, setPersonalEditLoading] = useState(false);
  const [personalEditData, setPersonalEditData] = useState<PersonalScheduleDetailData | null>(null);
  const [personalEditForm, setPersonalEditForm] = useState<PersonalScheduleFormState>(() => makeEmptyPersonalScheduleForm());
  const [personalEditSaving, setPersonalEditSaving] = useState(false);
  const [personalEditError, setPersonalEditError] = useState('');
  const [personalEditMessage, setPersonalEditMessage] = useState('');
  const [calendarDeletingKey, setCalendarDeletingKey] = useState('');
  const [calendarActionError, setCalendarActionError] = useState('');
  const [calendarActionMessage, setCalendarActionMessage] = useState('');
  const calendarCreatePanelRef = useRef<HTMLDivElement | null>(null);
  const personalCreatePanelRef = useRef<HTMLDivElement | null>(null);
  const calendarEditPanelRef = useRef<HTMLDivElement | null>(null);
  const personalEditPanelRef = useRef<HTMLDivElement | null>(null);
  const schedules = data?.schedules ?? [];
  const personalDeleteRequested = new URLSearchParams(window.location.search).get('delete') === '1';
  const days = useMemo(() => buildScheduleCalendarDays(month, schedules), [month, schedules]);
  const selectedDayItems = useMemo(
    () => schedules.filter((schedule) => schedule.date === selectedDate).sort((a, b) => `${a.time} ${a.type}`.localeCompare(`${b.time} ${b.type}`)),
    [schedules, selectedDate],
  );
  const monthLabel = new Intl.DateTimeFormat('ko-KR', { year: 'numeric', month: 'long' }).format(parseLocalDate(`${month}-01`));
  const todayMonth = localDateInputValue().slice(0, 7);
  const showUserFilter = dataFilter === 'user';

  useGuidedPanelFocus(calendarCreateOpen, calendarCreatePanelRef, `calendar-create-${selectedDate}`);
  useGuidedPanelFocus(personalCreateOpen, personalCreatePanelRef, `personal-create-${selectedDate}`);
  useGuidedPanelFocus(calendarEditOpen, calendarEditPanelRef, `calendar-edit-${calendarEditData?.schedule?.id || 'loading'}`);
  useGuidedPanelFocus(personalEditOpen, personalEditPanelRef, `personal-edit-${personalEditData?.schedule?.id || 'loading'}`);

  useEffect(() => {
    setSelectedDate((previous) => {
      if (previous >= range.start && previous <= range.end) {
        return previous;
      }
      const firstScheduledDate = schedules.find((schedule) => schedule.date && schedule.date >= range.start && schedule.date <= range.end)?.date;
      const today = localDateInputValue();
      return firstScheduledDate || (today >= range.start && today <= range.end ? today : range.start);
    });
  }, [range.end, range.start, schedules]);

  useEffect(() => {
    setCalendarActionError('');
    setCalendarActionMessage('');
    setCalendarCreateError('');
    setCalendarCreateMessage('');
    setCalendarEditError('');
    setCalendarEditMessage('');
    setPersonalCreateError('');
    setPersonalCreateMessage('');
    setPersonalEditError('');
    setPersonalEditMessage('');
  }, [dataFilter, filterUser, month]);

  useEffect(() => {
    if (!data) {
      return;
    }
    const intent = initialIntentRef.current;
    if (intent.createHandled || (intent.create !== '1' && intent.create !== 'personal')) {
      return;
    }
    intent.createHandled = true;

    const intentDate = intent.date || selectedDate;
    if (intent.date && intent.date.slice(0, 7) !== month) {
      onMonthChange(intent.date.slice(0, 7));
    }
    setSelectedDate(intentDate);
    setCalendarActionError('');
    setCalendarActionMessage('');

    if (intent.create === 'personal') {
      setCalendarCreateOpen(false);
      setCalendarEditOpen(false);
      setPersonalEditOpen(false);
      setPersonalCreateOpen(true);
      setPersonalCreateError('');
      setPersonalCreateMessage('');
      setPersonalCreatedDetailHref('');
      setPersonalCreateForm({
        ...makeEmptyPersonalScheduleForm(intentDate),
        scheduleTime: intent.time || '09:00',
      });
      return;
    }

    setCalendarCreateOpen(true);
    setCalendarEditOpen(false);
    setPersonalCreateOpen(false);
    setPersonalEditOpen(false);
    setCalendarCreateError('');
    setCalendarCreateMessage('');
    setCalendarCreatedDetailHref('');
    setCalendarCreateForm(makeScheduleCalendarCreateForm(data, intentDate));
  }, [data, month, onMonthChange, selectedDate]);

  useEffect(() => {
    const intent = initialIntentRef.current;
    if (!intent.personalId || intent.personalHandled) {
      return;
    }
    intent.personalHandled = true;

    let alive = true;
    setCalendarCreateOpen(false);
    setCalendarEditOpen(false);
    setPersonalCreateOpen(false);
    setPersonalEditOpen(true);
    setPersonalEditLoading(true);
    setPersonalEditData(null);
    setPersonalEditError('');
    setPersonalEditMessage('');
    setCalendarActionError('');
    setCalendarActionMessage('');

    loadPersonalScheduleDetailData(intent.personalId).then((detail) => {
      if (!alive) {
        return;
      }
      if (detail.source !== 'django' || !detail.schedule) {
        throw new Error(detail.error || detail.message || '개인 일정 상세를 불러오지 못했습니다.');
      }
      const detailDate = detail.schedule.date || '';
      if (detailDate) {
        setSelectedDate(detailDate);
        if (detailDate.slice(0, 7) !== month) {
          onMonthChange(detailDate.slice(0, 7));
        }
      }
      setPersonalEditData(detail);
      setPersonalEditForm(makePersonalScheduleEditForm(detail.schedule));
      if (!detail.edit.canEdit) {
        setPersonalEditMessage('읽기 전용으로 개인 일정을 확인 중입니다.');
      } else if (personalDeleteRequested) {
        setPersonalEditMessage('삭제 요청으로 들어왔습니다. 아래 삭제 버튼으로 확정하세요.');
      }
    }).catch((error_) => {
      if (!alive) {
        return;
      }
      setPersonalEditData(null);
      setPersonalEditError(error_ instanceof Error ? error_.message : '개인 일정 상세를 불러오지 못했습니다.');
    }).finally(() => {
      if (alive) {
        setPersonalEditLoading(false);
      }
    });

    return () => {
      alive = false;
    };
  }, [month, onMonthChange, personalDeleteRequested]);

  const openCalendarCreatePanel = () => {
    if (!data) {
      return;
    }
    setCalendarCreateForm(makeScheduleCalendarCreateForm(data, selectedDate));
    setCalendarCreateOpen(true);
    setCalendarEditOpen(false);
    setPersonalCreateOpen(false);
    setPersonalEditOpen(false);
    setCalendarCreateError('');
    setCalendarCreateMessage('');
    setCalendarCreatedDetailHref('');
    setCalendarActionError('');
    setCalendarActionMessage('');
  };

  const openPersonalCreatePanel = () => {
    if (!data) {
      return;
    }
    setPersonalCreateForm(makeEmptyPersonalScheduleForm(selectedDate));
    setPersonalCreateOpen(true);
    setCalendarCreateOpen(false);
    setCalendarEditOpen(false);
    setPersonalEditOpen(false);
    setPersonalCreateError('');
    setPersonalCreateMessage('');
    setPersonalCreatedDetailHref('');
    setCalendarActionError('');
    setCalendarActionMessage('');
  };

  const handleCalendarCreateFieldChange = (field: keyof ScheduleCreateFormState, value: string) => {
    setCalendarCreateForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setCalendarCreateError('');
    setCalendarCreateMessage('');
  };

  const calendarCreateCustomers = data?.create.customers ?? [];
  const calendarCreateDepartments = data?.create.departments ?? [];
  const filteredCalendarCreateCustomers = customersForDepartment(calendarCreateCustomers, calendarCreateForm.departmentId);
  const calendarDepartmentHasCustomers = filteredCalendarCreateCustomers.length > 0;
  const handleCalendarDepartmentChange = (value: string) => {
    const nextCustomers = customersForDepartment(calendarCreateCustomers, value);
    handleCalendarCreateFieldChange('departmentId', value);
    handleCalendarCreateFieldChange('followupId', nextCustomers[0]?.id ? String(nextCustomers[0].id) : '');
  };
  const handleCalendarCustomerChange = (value: string) => {
    const nextCustomer = calendarCreateCustomers.find((customer) => String(customer.id) === value);
    if (nextCustomer?.departmentId) {
      handleCalendarCreateFieldChange('departmentId', String(nextCustomer.departmentId));
    }
    handleCalendarCreateFieldChange('followupId', value);
  };

  const handlePersonalCreateFieldChange = (field: keyof PersonalScheduleFormState, value: string) => {
    setPersonalCreateForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setPersonalCreateError('');
    setPersonalCreateMessage('');
  };

  const handleCalendarCreateSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data || calendarCreating) {
      return;
    }
    if (!data.create.canCreate) {
      setCalendarCreateError(data.create.message || '일정 등록 권한이 없습니다.');
      return;
    }
    const { payload, error } = scheduleCreateFormToPayload(calendarCreateForm);
    if (!payload) {
      setCalendarCreateError(error || '일정 등록 정보를 확인하세요.');
      return;
    }

    setCalendarCreating(true);
    setCalendarCreateError('');
    setCalendarCreateMessage('');
    setCalendarCreatedDetailHref('');
    try {
      const created = await createCustomerSchedule(payload, data.create.submitUrl);
      await onRefresh();
      setCalendarCreateMessage(created.message || '일정을 등록했습니다.');
      setCalendarCreatedDetailHref(created.href || '');
      setCalendarCreateForm(makeScheduleCalendarCreateForm(data, calendarCreateForm.visitDate || selectedDate));
    } catch (error_) {
      setCalendarCreateError(error_ instanceof Error ? error_.message : '일정 등록에 실패했습니다.');
    } finally {
      setCalendarCreating(false);
    }
  };

  const handlePersonalCreateSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data || personalCreating) {
      return;
    }
    const createConfig = data.create.personalSchedule;
    if (!createConfig?.canCreate) {
      setPersonalCreateError(createConfig?.message || '개인 일정 등록 권한이 없습니다.');
      return;
    }
    const { payload, error } = personalScheduleFormToPayload(personalCreateForm);
    if (!payload) {
      setPersonalCreateError(error || '개인 일정 등록 정보를 확인하세요.');
      return;
    }

    setPersonalCreating(true);
    setPersonalCreateError('');
    setPersonalCreateMessage('');
    setPersonalCreatedDetailHref('');
    try {
      const created = await createPersonalSchedule(payload, createConfig.submitUrl);
      await onRefresh();
      setPersonalCreateMessage(created.message || '개인 일정을 등록했습니다.');
      setPersonalCreatedDetailHref(created.href || created.schedule?.href || '');
      setPersonalCreateForm(makeEmptyPersonalScheduleForm(personalCreateForm.scheduleDate || selectedDate));
    } catch (error_) {
      setPersonalCreateError(error_ instanceof Error ? error_.message : '개인 일정 등록에 실패했습니다.');
    } finally {
      setPersonalCreating(false);
    }
  };

  const handleCalendarEditFieldChange = (field: keyof ScheduleEditFormState, value: string | boolean) => {
    setCalendarEditForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setCalendarEditError('');
    setCalendarEditMessage('');
  };

  const handlePersonalEditFieldChange = (field: keyof PersonalScheduleFormState, value: string) => {
    setPersonalEditForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setPersonalEditError('');
    setPersonalEditMessage('');
  };

  const handleCalendarEditOpen = async (schedule: ScheduleItem) => {
    if (calendarEditLoading || calendarEditSaving || personalEditLoading || personalEditSaving) {
      return;
    }
    if (schedule.type === 'personal') {
      if (!schedule.canEdit) {
        setCalendarActionError('이 개인 일정의 수정 권한이 없습니다.');
        setCalendarActionMessage('');
        return;
      }

      setCalendarCreateOpen(false);
      setCalendarEditOpen(false);
      setPersonalCreateOpen(false);
      setPersonalEditOpen(true);
      setPersonalEditLoading(true);
      setPersonalEditData(null);
      setPersonalEditError('');
      setPersonalEditMessage('');
      setCalendarActionError('');
      setCalendarActionMessage('');
      try {
        const detail = await loadPersonalScheduleDetailData(schedule.id);
        if (detail.source !== 'django' || !detail.schedule) {
          throw new Error(detail.error || detail.message || '개인 일정 상세를 불러오지 못했습니다.');
        }
        if (!detail.edit.canEdit) {
          throw new Error(detail.edit.message || '수정 권한이 없습니다.');
        }
        setPersonalEditData(detail);
        setPersonalEditForm(makePersonalScheduleEditForm(detail.schedule));
      } catch (error_) {
        setPersonalEditData(null);
        setPersonalEditError(error_ instanceof Error ? error_.message : '개인 일정 상세를 불러오지 못했습니다.');
      } finally {
        setPersonalEditLoading(false);
      }
      return;
    }
    if (schedule.type !== 'customer' || !schedule.canEdit) {
      setCalendarActionError('이 일정의 수정 권한이 없습니다.');
      setCalendarActionMessage('');
      return;
    }

    setCalendarCreateOpen(false);
    setPersonalCreateOpen(false);
    setPersonalEditOpen(false);
    setCalendarEditOpen(true);
    setCalendarEditLoading(true);
    setCalendarEditData(null);
    setCalendarEditError('');
    setCalendarEditMessage('');
    setCalendarActionError('');
    setCalendarActionMessage('');
    try {
      const detail = await loadScheduleDetailData(schedule.id);
      if (detail.source !== 'django' || !detail.schedule) {
        throw new Error(detail.error || detail.message || '일정 상세를 불러오지 못했습니다.');
      }
      if (!detail.edit.canEdit) {
        throw new Error(detail.edit.message || '수정 권한이 없습니다.');
      }
      setCalendarEditData(detail);
      setCalendarEditForm(makeScheduleEditForm(detail.schedule));
    } catch (error_) {
      setCalendarEditData(null);
      setCalendarEditError(error_ instanceof Error ? error_.message : '일정 상세를 불러오지 못했습니다.');
    } finally {
      setCalendarEditLoading(false);
    }
  };

  const handleCalendarEditSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!calendarEditData?.edit || calendarEditSaving) {
      return;
    }
    if (!calendarEditData.edit.canEdit || !calendarEditData.edit.submitUrl) {
      setCalendarEditError(calendarEditData.edit.message || '수정 권한이 없습니다.');
      return;
    }
    const { payload, error } = scheduleEditFormToPayload(calendarEditForm);
    if (!payload) {
      setCalendarEditError(error || '일정 수정 정보를 확인하세요.');
      return;
    }

    setCalendarEditSaving(true);
    setCalendarEditError('');
    setCalendarEditMessage('');
    try {
      const updated = await updateCustomerSchedule(payload, calendarEditData.edit.submitUrl);
      await onRefresh();
      setCalendarEditData(updated);
      setCalendarEditForm(makeScheduleEditForm(updated.schedule));
      setCalendarEditMessage(updated.message || '일정을 수정했습니다.');
      setCalendarEditOpen(false);
    } catch (error_) {
      setCalendarEditError(error_ instanceof Error ? error_.message : '일정 수정에 실패했습니다.');
    } finally {
      setCalendarEditSaving(false);
    }
  };

  const handlePersonalEditSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!personalEditData?.edit || personalEditSaving) {
      return;
    }
    if (!personalEditData.edit.canEdit || !personalEditData.edit.submitUrl) {
      setPersonalEditError(personalEditData.edit.message || '수정 권한이 없습니다.');
      return;
    }
    const { payload, error } = personalScheduleFormToPayload(personalEditForm);
    if (!payload) {
      setPersonalEditError(error || '개인 일정 수정 정보를 확인하세요.');
      return;
    }

    setPersonalEditSaving(true);
    setPersonalEditError('');
    setPersonalEditMessage('');
    try {
      const updated = await updatePersonalSchedule(payload, personalEditData.edit.submitUrl);
      await onRefresh();
      setPersonalEditData(updated);
      setPersonalEditForm(makePersonalScheduleEditForm(updated.schedule));
      setPersonalEditMessage(updated.message || '개인 일정을 수정했습니다.');
      setPersonalEditOpen(false);
    } catch (error_) {
      setPersonalEditError(error_ instanceof Error ? error_.message : '개인 일정 수정에 실패했습니다.');
    } finally {
      setPersonalEditSaving(false);
    }
  };

  const handleCalendarDelete = async (schedule: ScheduleItem) => {
    if (calendarDeletingKey) {
      return;
    }
    if (!schedule.canEdit || !schedule.deleteHref) {
      setCalendarActionError('이 일정의 삭제 권한이 없습니다.');
      setCalendarActionMessage('');
      return;
    }
    const confirmMessage = schedule.type === 'personal'
      ? [
        '이 개인 일정을 삭제할까요?',
        '',
        `제목: ${schedule.title || '제목 없음'}`,
        `날짜: ${schedule.date ? formatDateLabel(schedule.date) : '날짜 없음'}`,
        '',
        '관련 메모도 함께 삭제되며 복구할 수 없습니다.',
      ].join('\n')
      : [
        '이 일정을 삭제할까요?',
        '',
        `고객: ${schedule.customer || '고객명 미정'}`,
        `날짜: ${schedule.date ? formatDateLabel(schedule.date) : '날짜 없음'}`,
        '',
        '관련 활동 기록도 함께 삭제되며 복구할 수 없습니다.',
      ].join('\n');
    if (!window.confirm(confirmMessage)) {
      return;
    }

    const itemKey = `${schedule.type}-${schedule.id}`;
    setCalendarDeletingKey(itemKey);
    setCalendarActionError('');
    setCalendarActionMessage('');
    try {
      const result = await deleteSchedule(schedule.deleteHref);
      await onRefresh();
      if (schedule.type === 'customer' && calendarEditData?.schedule?.id === schedule.id) {
        setCalendarEditOpen(false);
        setCalendarEditData(null);
      }
      if (schedule.type === 'personal' && personalEditData?.schedule?.id === schedule.id) {
        setPersonalEditOpen(false);
        setPersonalEditData(null);
      }
      if (schedule.type === 'personal') {
        setPersonalCreateOpen(false);
        setPersonalCreateMessage('');
        setPersonalCreatedDetailHref('');
        setPersonalEditOpen(false);
        setPersonalEditData(null);
        setPersonalEditError('');
        setPersonalEditMessage('');
      }
      setCalendarActionMessage(result.message || '일정을 삭제했습니다.');
    } catch (error_) {
      setCalendarActionError(error_ instanceof Error ? error_.message : '일정 삭제에 실패했습니다.');
    } finally {
      setCalendarDeletingKey('');
    }
  };

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>일정 캘린더를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const metrics = [
    { label: '월간 일정', value: `${formatNumber(data.metrics.totalSchedules)}건`, detail: data.scope.label || '범위', icon: CalendarDays, tone: 'blue' as const },
    { label: '고객 일정', value: `${formatNumber(data.metrics.customerSchedules)}건`, detail: '방문/견적/납품', icon: Users, tone: 'green' as const },
    { label: '개인 일정', value: `${formatNumber(data.metrics.personalSchedules)}건`, detail: '일반 업무', icon: Clock, tone: 'teal' as const },
    { label: '완료', value: `${formatNumber(data.metrics.completedSchedules)}건`, detail: '고객 일정 기준', icon: CheckCircle2, tone: 'amber' as const },
    { label: '지연', value: `${formatNumber(data.metrics.overdueSchedules)}건`, detail: '예정일 경과', icon: AlertTriangle, tone: 'red' as const },
  ];
  const personalScheduleCreateConfig = data.create.personalSchedule;

  return (
    <section className="schedules-page schedule-calendar-page">
      {data.source !== 'django' ? (
        <DashboardApiAlert message={data.error} title="일정 캘린더 정보를 불러오지 못했습니다" />
      ) : null}

      <div className="dashboard-summary-band schedule-calendar-summary">
        <div>
          <span className="eyebrow">Schedule Calendar</span>
          <h2>{monthLabel}</h2>
          <p>{data.scope.label || '내 일정'} 기준으로 고객 일정과 개인 일정을 월간 캘린더에서 확인합니다.</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href={data.links.schedules}>
            목록
          </a>
          <button
            className={data.create.canCreate ? 'route-primary-action' : 'route-secondary-action'}
            onClick={openCalendarCreatePanel}
            type="button"
          >
            {data.create.canCreate ? '일정 등록' : '등록 권한 없음'}
            <Plus size={16} />
          </button>
        </div>
      </div>

      <section className="dashboard-metric-grid" aria-label="월간 일정 지표">
        {metrics.map((metric) => (
          <DashboardMetricCard
            detail={metric.detail}
            icon={metric.icon}
            key={metric.label}
            label={metric.label}
            tone={metric.tone}
            value={metric.value}
          />
        ))}
      </section>

      <div className="schedule-calendar-toolbar">
        <div className="schedule-calendar-month-controls">
          <button aria-label="이전 달" onClick={() => onMonthChange(shiftScheduleCalendarMonth(month, -1))} type="button">
            <ChevronLeft size={17} />
          </button>
          <button onClick={() => onMonthChange(todayMonth)} type="button">오늘</button>
          <button aria-label="다음 달" onClick={() => onMonthChange(shiftScheduleCalendarMonth(month, 1))} type="button">
            <ChevronRight size={17} />
          </button>
          <strong>{monthLabel}</strong>
          {loading ? <Loader2 className="spin-icon" size={16} /> : null}
        </div>
        <div className="schedule-calendar-filters">
          <select onChange={(event) => onDataFilterChange(event.target.value)} value={dataFilter}>
            {data.options.dataFilters.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          {showUserFilter ? (
            <select onChange={(event) => onFilterUserChange(event.target.value)} value={filterUser}>
              <option value="">직원 선택</option>
              {data.options.users.map((user) => (
                <option key={user.id} value={user.id}>{user.name}{user.isCurrent ? ' (나)' : ''}</option>
              ))}
            </select>
          ) : null}
        </div>
      </div>

      <div className="schedule-calendar-layout">
        <section className="dashboard-panel schedule-calendar-grid-panel">
          <div className="schedule-calendar-weekdays" aria-hidden="true">
            {['월', '화', '수', '목', '금', '토', '일'].map((day) => <span key={day}>{day}</span>)}
          </div>
          <div className="schedule-calendar-grid" role="grid" aria-label={`${monthLabel} 일정 캘린더`}>
            {days.map((day) => (
              <button
                className={[
                  'schedule-calendar-day',
                  day.inMonth ? '' : 'muted',
                  day.isToday ? 'today' : '',
                  selectedDate === day.date ? 'selected' : '',
                ].filter(Boolean).join(' ')}
                key={day.date}
                onClick={() => setSelectedDate(day.date)}
                type="button"
              >
                <span className="schedule-calendar-date-number">{day.dayNumber}</span>
                <div className="schedule-calendar-events">
                  {day.schedules.slice(0, 4).map((schedule) => (
                    <span className={`schedule-calendar-event ${schedule.type} ${schedule.status}`} key={`${schedule.type}-${schedule.id}`}>
                      {schedule.time ? `${schedule.time} ` : ''}{schedule.company || schedule.title || schedule.customer}
                    </span>
                  ))}
                  {day.schedules.length > 4 ? <span className="schedule-calendar-more">+{day.schedules.length - 4}</span> : null}
                </div>
              </button>
            ))}
          </div>
        </section>

        <aside className="dashboard-panel schedule-calendar-day-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Selected day</span>
              <h2>{formatDateLabel(selectedDate)}</h2>
            </div>
            <CalendarDays size={18} />
          </div>
          {statusError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{statusError}</span></div> : null}
          {statusMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{statusMessage}</span></div> : null}
          {calendarActionError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{calendarActionError}</span></div> : null}
          {calendarActionMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{calendarActionMessage}</span></div> : null}
          <ScheduleCalendarSelectedList
            deletingKey={calendarDeletingKey}
            items={selectedDayItems}
            onDelete={handleCalendarDelete}
            onEdit={handleCalendarEditOpen}
            onStatusChange={onStatusChange}
            statusUpdatingKey={statusUpdatingKey}
          />
          <div className="dashboard-panel-heading schedules-side-heading">
            <div>
              <span className="eyebrow">Actions</span>
              <h2>일정 작업</h2>
            </div>
            <Plus size={18} />
          </div>
          <div className="customers-side-actions">
            <button onClick={openCalendarCreatePanel} type="button">고객 일정 등록</button>
            {personalScheduleCreateConfig?.canCreate ? (
              <button onClick={openPersonalCreatePanel} type="button">
                개인 일정 등록
              </button>
            ) : null}
            <a href={data.links.schedules}>일정 목록</a>
          </div>

          {calendarCreateOpen || calendarCreateError || calendarCreateMessage ? (
            <div className="schedule-calendar-inline-editor" ref={calendarCreatePanelRef}>
              <div className="schedule-calendar-editor-heading">
                <div>
                  <span className="eyebrow">Quick schedule</span>
                  <h3>고객 일정 등록</h3>
                </div>
                <button aria-label="등록 패널 닫기" onClick={() => setCalendarCreateOpen(false)} type="button">
                  <X size={16} />
                </button>
              </div>
              {calendarCreateError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{calendarCreateError}</span></div> : null}
              {calendarCreateMessage ? (
                <div className="dashboard-api-alert compact success">
                  <CheckCircle2 size={16} />
                  <span>{calendarCreateMessage}</span>
                  {calendarCreatedDetailHref ? <a href={calendarCreatedDetailHref}>상세</a> : null}
                </div>
              ) : null}
              {!data.create.canCreate ? (
                <DashboardEmpty label={data.create.message || '일정 등록 권한이 없습니다'} />
              ) : (data.create.departments ?? []).length === 0 && data.create.customers.length === 0 ? (
                <DashboardEmpty label="등록 가능한 부서/연구실이 없습니다" />
              ) : data.create.activityTypes.length === 0 ? (
                <DashboardEmpty label="등록 가능한 일정 유형이 없습니다" />
              ) : calendarCreateOpen ? (
                <form className="notes-create-form schedule-calendar-form" onSubmit={handleCalendarCreateSubmit}>
                  <div className="notes-create-grid schedules-create-grid">
                    <div className="form-field">
                      <span>부서/연구실</span>
                      <SearchableSelect
                        ariaLabel="부서/연구실 선택"
                        onChange={handleCalendarDepartmentChange}
                        options={calendarCreateDepartments.map(makeDepartmentSelectOption)}
                        placeholder="회사, 부서/연구실, 담당자 검색"
                        value={calendarCreateForm.departmentId}
                      />
                    </div>
                    <div className="form-field">
                      <span>고객</span>
                      <SearchableSelect
                        allowEmpty={!calendarDepartmentHasCustomers}
                        ariaLabel="고객 선택"
                        disabled={!calendarDepartmentHasCustomers}
                        emptyLabel="부서에만 연결"
                        onChange={handleCalendarCustomerChange}
                        options={filteredCalendarCreateCustomers.map(makeCustomerSelectOption)}
                        placeholder="고객, 회사, 부서 검색"
                        value={calendarCreateForm.followupId}
                      />
                    </div>
                    <label>
                      <span>일정 유형</span>
                      <select
                        onChange={(event) => handleCalendarCreateFieldChange('activityType', event.target.value)}
                        required
                        value={calendarCreateForm.activityType}
                      >
                        {data.create.activityTypes.map((option) => (
                          <option key={option.value} value={option.value}>{option.label}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      <span>일정 날짜</span>
                      <input
                        onChange={(event) => handleCalendarCreateFieldChange('visitDate', event.target.value)}
                        required
                        type="date"
                        value={calendarCreateForm.visitDate}
                      />
                    </label>
                    <label>
                      <span>일정 시간</span>
                      <input
                        onChange={(event) => handleCalendarCreateFieldChange('visitTime', event.target.value)}
                        required
                        type="time"
                        value={calendarCreateForm.visitTime}
                      />
                    </label>
                    <label>
                      <span>장소</span>
                      <input
                        onChange={(event) => handleCalendarCreateFieldChange('location', event.target.value)}
                        placeholder="방문 장소"
                        value={calendarCreateForm.location}
                      />
                    </label>
                    <label>
                      <span>예상 매출</span>
                      <input
                        inputMode="numeric"
                        min="0"
                        onChange={(event) => handleCalendarCreateFieldChange('expectedRevenue', event.target.value)}
                        placeholder="원"
                        type="number"
                        value={calendarCreateForm.expectedRevenue}
                      />
                    </label>
                    <VatModeField onChange={(value) => handleCalendarCreateFieldChange('vatMode', value)} value={calendarCreateForm.vatMode} />
                    <label>
                      <span>성공 확률</span>
                      <input
                        inputMode="numeric"
                        max="100"
                        min="0"
                        step="5"
                        required={isQuoteProbabilityRequired(calendarCreateForm.activityType)}
                        onBlur={(event) => handleCalendarCreateFieldChange('probability', normalizeProbabilityInputValue(event.target.value))}
                        onChange={(event) => handleCalendarCreateFieldChange('probability', event.target.value)}
                        placeholder="0-100, 5% 단위"
                        type="number"
                        value={calendarCreateForm.probability}
                      />
                    </label>
                  </div>
                  <label>
                    <span>일정 내용</span>
                    <textarea
                      onChange={(event) => handleCalendarCreateFieldChange('notes', event.target.value)}
                      rows={3}
                      value={calendarCreateForm.notes}
                    />
                  </label>
                  <div className="notes-create-actions">
                    <a className="route-secondary-action" href={appendDateQuery(data.links.createSchedule, calendarCreateForm.visitDate || selectedDate)}>
                      상세 등록
                      <MoveUpRight size={15} />
                    </a>
                    <button className="route-primary-action" disabled={calendarCreating} type="submit">
                      {calendarCreating ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                      저장
                    </button>
                  </div>
                </form>
              ) : null}
            </div>
          ) : null}

          {personalCreateOpen || personalCreateError || personalCreateMessage ? (
            <div className="schedule-calendar-inline-editor" ref={personalCreatePanelRef}>
              <div className="schedule-calendar-editor-heading">
                <div>
                  <span className="eyebrow">Personal schedule</span>
                  <h3>개인 일정 등록</h3>
                </div>
                <button aria-label="개인 일정 등록 패널 닫기" onClick={() => setPersonalCreateOpen(false)} type="button">
                  <X size={16} />
                </button>
              </div>
              {personalCreateError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{personalCreateError}</span></div> : null}
              {personalCreateMessage ? (
                <div className="dashboard-api-alert compact success">
                  <CheckCircle2 size={16} />
                  <span>{personalCreateMessage}</span>
                  {personalCreatedDetailHref ? <a href={personalCreatedDetailHref}>상세</a> : null}
                </div>
              ) : null}
              {!personalScheduleCreateConfig?.canCreate ? (
                <DashboardEmpty label={personalScheduleCreateConfig?.message || '개인 일정 등록 권한이 없습니다'} />
              ) : personalCreateOpen ? (
                <form className="notes-create-form schedule-calendar-form" onSubmit={handlePersonalCreateSubmit}>
                  <label>
                    <span>일정 제목</span>
                    <input
                      onChange={(event) => handlePersonalCreateFieldChange('title', event.target.value)}
                      required
                      value={personalCreateForm.title}
                    />
                  </label>
                  <div className="notes-create-grid schedules-create-grid">
                    <label>
                      <span>날짜</span>
                      <input
                        onChange={(event) => handlePersonalCreateFieldChange('scheduleDate', event.target.value)}
                        required
                        type="date"
                        value={personalCreateForm.scheduleDate}
                      />
                    </label>
                    <label>
                      <span>시간</span>
                      <input
                        onChange={(event) => handlePersonalCreateFieldChange('scheduleTime', event.target.value)}
                        required
                        type="time"
                        value={personalCreateForm.scheduleTime}
                      />
                    </label>
                  </div>
                  <label>
                    <span>내용</span>
                    <textarea
                      onChange={(event) => handlePersonalCreateFieldChange('content', event.target.value)}
                      rows={3}
                      value={personalCreateForm.content}
                    />
                  </label>
                  <div className="notes-create-actions">
                    <button className="route-primary-action" disabled={personalCreating} type="submit">
                      {personalCreating ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                      저장
                    </button>
                  </div>
                </form>
              ) : null}
            </div>
          ) : null}

          {calendarEditOpen || calendarEditError || calendarEditMessage ? (
            <div className="schedule-calendar-inline-editor" ref={calendarEditPanelRef}>
              <div className="schedule-calendar-editor-heading">
                <div>
                  <span className="eyebrow">Edit schedule</span>
                  <h3>일정 수정</h3>
                </div>
                <button aria-label="수정 패널 닫기" onClick={() => setCalendarEditOpen(false)} type="button">
                  <X size={16} />
                </button>
              </div>
              {calendarEditError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{calendarEditError}</span></div> : null}
              {calendarEditMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{calendarEditMessage}</span></div> : null}
              {calendarEditLoading ? (
                <div className="schedule-calendar-editor-loading">
                  <Loader2 className="spin-icon" size={16} />
                  <span>일정 상세를 불러오는 중입니다</span>
                </div>
              ) : calendarEditOpen && calendarEditData?.schedule && calendarEditData.edit.canEdit ? (
                <form className="notes-create-form schedule-calendar-form" onSubmit={handleCalendarEditSubmit}>
                  <div className="notes-create-grid schedules-create-grid">
                    <div className="form-field">
                      <span>고객</span>
                      <SearchableSelect
                        ariaLabel="고객 선택"
                        onChange={(nextValue) => handleCalendarEditFieldChange('followupId', nextValue)}
                        options={calendarEditData.edit.customers.map(makeCustomerSelectOption)}
                        placeholder="고객, 회사, 부서 검색"
                        value={calendarEditForm.followupId}
                      />
                    </div>
                    <label>
                      <span>일정 유형</span>
                      <select
                        onChange={(event) => handleCalendarEditFieldChange('activityType', event.target.value)}
                        required
                        value={calendarEditForm.activityType}
                      >
                        {calendarEditData.edit.activityTypes.map((option) => (
                          <option key={option.value} value={option.value}>{option.label}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      <span>상태</span>
                      <select
                        onChange={(event) => handleCalendarEditFieldChange('status', event.target.value)}
                        required
                        value={calendarEditForm.status}
                      >
                        {calendarEditData.edit.statuses.map((option) => (
                          <option key={option.value} value={option.value}>{option.label}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      <span>일정 날짜</span>
                      <input
                        onChange={(event) => handleCalendarEditFieldChange('visitDate', event.target.value)}
                        required
                        type="date"
                        value={calendarEditForm.visitDate}
                      />
                    </label>
                    <label>
                      <span>일정 시간</span>
                      <input
                        onChange={(event) => handleCalendarEditFieldChange('visitTime', event.target.value)}
                        required
                        type="time"
                        value={calendarEditForm.visitTime}
                      />
                    </label>
                    <label>
                      <span>장소</span>
                      <input
                        onChange={(event) => handleCalendarEditFieldChange('location', event.target.value)}
                        value={calendarEditForm.location}
                      />
                    </label>
                    <label>
                      <span>예상 매출</span>
                      <input
                        inputMode="numeric"
                        min="0"
                        onChange={(event) => handleCalendarEditFieldChange('expectedRevenue', event.target.value)}
                        type="number"
                        value={calendarEditForm.expectedRevenue}
                      />
                    </label>
                    <VatModeField onChange={(value) => handleCalendarEditFieldChange('vatMode', value)} value={calendarEditForm.vatMode} />
                    <label>
                      <span>성공 확률</span>
                      <input
                        inputMode="numeric"
                        max="100"
                        min="0"
                        step="5"
                        required={isQuoteProbabilityRequired(calendarEditForm.activityType)}
                        onBlur={(event) => handleCalendarEditFieldChange('probability', normalizeProbabilityInputValue(event.target.value))}
                        onChange={(event) => handleCalendarEditFieldChange('probability', event.target.value)}
                        type="number"
                        value={calendarEditForm.probability}
                      />
                    </label>
                    <label>
                      <span>예상 종료일</span>
                      <input
                        onChange={(event) => handleCalendarEditFieldChange('expectedCloseDate', event.target.value)}
                        type="date"
                        value={calendarEditForm.expectedCloseDate}
                      />
                    </label>
                  </div>
                  <label className="schedule-edit-inline-check">
                    <input
                      checked={calendarEditForm.purchaseConfirmed}
                      onChange={(event) => handleCalendarEditFieldChange('purchaseConfirmed', event.target.checked)}
                      type="checkbox"
                    />
                    <span>구매 확정</span>
                  </label>
                  <label>
                    <span>일정 내용</span>
                    <textarea
                      onChange={(event) => handleCalendarEditFieldChange('notes', event.target.value)}
                      rows={3}
                      value={calendarEditForm.notes}
                    />
                  </label>
                  <div className="notes-create-actions">
                    <a className="route-secondary-action" href={calendarEditData.schedule.href}>
                      상세
                    </a>
                    <button className="route-primary-action" disabled={calendarEditSaving} type="submit">
                      {calendarEditSaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                      저장
                    </button>
                  </div>
                </form>
              ) : null}
            </div>
          ) : null}

          {personalEditOpen || personalEditError || personalEditMessage ? (
            <div className="schedule-calendar-inline-editor" ref={personalEditPanelRef}>
              <div className="schedule-calendar-editor-heading">
                <div>
                  <span className="eyebrow">Edit personal</span>
                  <h3>개인 일정 수정</h3>
                </div>
                <button aria-label="개인 일정 수정 패널 닫기" onClick={() => setPersonalEditOpen(false)} type="button">
                  <X size={16} />
                </button>
              </div>
              {personalEditError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{personalEditError}</span></div> : null}
              {personalEditMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{personalEditMessage}</span></div> : null}
              {personalEditLoading ? (
                <div className="schedule-calendar-editor-loading">
                  <Loader2 className="spin-icon" size={16} />
                  <span>개인 일정 상세를 불러오는 중입니다</span>
                </div>
              ) : personalEditOpen && personalEditData?.schedule && personalEditData.edit.canEdit ? (
                <form className="notes-create-form schedule-calendar-form" onSubmit={handlePersonalEditSubmit}>
                  <label>
                    <span>일정 제목</span>
                    <input
                      onChange={(event) => handlePersonalEditFieldChange('title', event.target.value)}
                      required
                      value={personalEditForm.title}
                    />
                  </label>
                  <div className="notes-create-grid schedules-create-grid">
                    <label>
                      <span>날짜</span>
                      <input
                        onChange={(event) => handlePersonalEditFieldChange('scheduleDate', event.target.value)}
                        required
                        type="date"
                        value={personalEditForm.scheduleDate}
                      />
                    </label>
                    <label>
                      <span>시간</span>
                      <input
                        onChange={(event) => handlePersonalEditFieldChange('scheduleTime', event.target.value)}
                        required
                        type="time"
                        value={personalEditForm.scheduleTime}
                      />
                    </label>
                  </div>
                  <label>
                    <span>내용</span>
                    <textarea
                      onChange={(event) => handlePersonalEditFieldChange('content', event.target.value)}
                      rows={3}
                      value={personalEditForm.content}
                    />
                  </label>
                  <div className="notes-create-actions">
                    <a className="route-secondary-action" href={personalEditData.schedule.href}>
                      상세
                    </a>
                    {personalEditData.links.deleteSchedule ? (
                      <button
                        className="route-secondary-action danger"
                        disabled={calendarDeletingKey === `personal-${personalEditData.schedule.id}`}
                        onClick={() => personalEditData.schedule && handleCalendarDelete(personalEditData.schedule)}
                        type="button"
                      >
                        {calendarDeletingKey === `personal-${personalEditData.schedule.id}` ? <Loader2 className="spin-icon" size={15} /> : <Trash2 size={15} />}
                        삭제
                      </button>
                    ) : null}
                    <button className="route-primary-action" disabled={personalEditSaving} type="submit">
                      {personalEditSaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                      저장
                    </button>
                  </div>
                </form>
              ) : personalEditOpen && personalEditData?.schedule ? (
                <div className="schedule-calendar-readonly-detail">
                  <dl>
                    <div>
                      <dt>제목</dt>
                      <dd>{personalEditData.schedule.title || '제목 없음'}</dd>
                    </div>
                    <div>
                      <dt>담당자</dt>
                      <dd>{personalEditData.schedule.owner || '-'}</dd>
                    </div>
                    <div>
                      <dt>날짜</dt>
                      <dd>{personalEditData.schedule.date ? formatDateLabel(personalEditData.schedule.date) : '-'}</dd>
                    </div>
                    <div>
                      <dt>시간</dt>
                      <dd>{personalEditData.schedule.time || '-'}</dd>
                    </div>
                  </dl>
                  <p>{personalEditData.schedule.notesFull || personalEditData.schedule.notes || '내용이 없습니다.'}</p>
                  <div className="notes-create-actions">
                    <a className="route-secondary-action" href={personalEditData.links.calendar || '/schedules/calendar/'}>
                      캘린더
                    </a>
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}
        </aside>
      </div>
    </section>
  );
}

const scheduleDocumentVariableBuckets: Array<{ label: string; keys: string[] }> = [
  { label: '기본 정보', keys: ['년', '월', '일', '거래번호', '일정날짜', '날짜', '발행일'] },
  { label: '고객 정보', keys: ['고객명', '업체명', '학교명', '부서명', '연구실', '담당자', '이메일', '담당자이메일', '연락처', '전화번호'] },
  { label: '영업 담당', keys: ['실무자', '영업담당자', '담당영업', '영업담당자이메일'] },
  { label: '견적 정보', keys: ['견적번호', '메모', '기타사항', '견적기타사항'] },
  { label: '회사 정보', keys: ['회사명'] },
  { label: '금액', keys: ['공급가액', '소계', '부가세액', '부가세', '총액', '합계', '총액한글', '한글금액'] },
];

const isScheduleDocumentEmptyValue = (value: ScheduleDocumentPreviewData['variables'][string]) => (
  value === null || value === undefined || String(value).trim() === ''
);

const formatScheduleDocumentValue = (value: ScheduleDocumentPreviewData['variables'][string]) => {
  if (isScheduleDocumentEmptyValue(value)) {
    return '미입력';
  }
  return typeof value === 'number' ? formatNumber(value) : String(value);
};

function buildScheduleDocumentVariableGroups(variables: ScheduleDocumentPreviewData['variables']) {
  const usedKeys = new Set<string>();
  const groups = scheduleDocumentVariableBuckets.map((bucket) => {
    const entries = bucket.keys
      .filter((key) => Object.prototype.hasOwnProperty.call(variables, key))
      .map((key) => {
        usedKeys.add(key);
        return [key, variables[key]] as const;
      });
    return { label: bucket.label, entries };
  }).filter((group) => group.entries.length > 0);

  const itemEntries: Array<readonly [string, ScheduleDocumentPreviewData['variables'][string]]> = [];
  const otherEntries: Array<readonly [string, ScheduleDocumentPreviewData['variables'][string]]> = [];
  Object.entries(variables).forEach(([key, value]) => {
    if (usedKeys.has(key)) {
      return;
    }
    if (/^품목\d+_/.test(key)) {
      itemEntries.push([key, value]);
    } else {
      otherEntries.push([key, value]);
    }
  });

  if (itemEntries.length > 0) {
    groups.push({ label: '품목 변수', entries: itemEntries });
  }
  if (otherEntries.length > 0) {
    groups.push({ label: '기타 변수', entries: otherEntries });
  }
  return groups;
}

function saveDownloadedBlob(blob: Blob, filename: string) {
  const objectUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(objectUrl);
}

function scheduleDocumentDownloadKey(
  action: ScheduleDocumentAction,
  formatAction: ScheduleDocumentFormatAction,
  options?: ScheduleDocumentRequestOptions,
) {
  return [
    action.type,
    formatAction.format,
    formatAction.href,
    options?.hideBaseUnitPrice ? 'hide-base-unit-price' : 'show-base-unit-price',
  ].join('-');
}

function commercialCheckStatusClass(status?: string) {
  if (status === 'warning' || status === 'error') return 'warning';
  if (status === 'ok') return 'ok';
  return 'info';
}

function ScheduleCommercialChecksPanel({ checks }: { checks?: ScheduleDetailData['commercialChecks'] }) {
  if (!checks?.applies) {
    return null;
  }

  const statusClass = commercialCheckStatusClass(checks.status);
  const isQuote = checks.kind === 'quote';
  const isDelivery = checks.kind === 'delivery';
  const autoAttachLabel = isDelivery
    ? checks.delivery.autoAttachLabel || checks.documents.autoAttachLabel
    : checks.summary.autoAttachReady
      ? checks.documents.autoAttachLabel
      : '메일 자동첨부 후보 없음';
  const metrics = isQuote
    ? [
      { label: '견적 품목', value: `${formatNumber(checks.summary.quoteItemCount)}개` },
      { label: '견적 금액', value: formatWon(checks.summary.quoteAmount) },
      { label: '납품 반영', value: formatWon(checks.summary.deliveredAmount) },
      { label: '미납 잔액', value: formatWon(checks.summary.remainingAmount) },
    ]
    : [
      { label: '납품 품목', value: `${formatNumber(checks.summary.deliveryItemCount)}개` },
      { label: '납품 금액', value: formatWon(checks.summary.deliveryAmount) },
      { label: '원본 견적', value: `${formatNumber(checks.delivery.sourceQuoteCount)}건` },
      { label: '등록 서류', value: `${formatNumber(checks.summary.registeredDocumentCount)}개` },
    ];

  return (
    <section className={`schedule-commercial-panel ${statusClass}`} aria-label="견적 납품 정합성">
      <div className="schedule-commercial-heading">
        <div>
          <span className="eyebrow">Commercial check</span>
          <h3 className="customer-detail-section-heading">견적/납품 정합성</h3>
        </div>
        <span className={`schedule-commercial-status ${statusClass}`}>
          {statusClass === 'warning' ? <AlertTriangle size={14} /> : <CheckCircle2 size={14} />}
          {checks.statusLabel}
        </span>
      </div>

      <div className="schedule-commercial-metrics">
        {metrics.map((metric) => (
          <div key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </div>
        ))}
      </div>

      {autoAttachLabel ? (
        <div className={`schedule-commercial-auto ${checks.summary.autoAttachReady ? 'ok' : 'warning'}`}>
          <FileText size={15} />
          <span>{autoAttachLabel}</span>
        </div>
      ) : null}

      {isQuote && checks.quoteGroups.length > 0 ? (
        <div className="schedule-commercial-group-list">
          {checks.quoteGroups.map((group) => (
            <div className={`schedule-commercial-group ${commercialCheckStatusClass(group.status)}`} key={group.quoteGroup || 'default'}>
              <div>
                <strong>{group.quoteGroupLabel}</strong>
                <span>{[
                  `${formatNumber(group.itemCount)}개 품목`,
                  group.fulfillmentLabel,
                  group.autoAttachLabel,
                ].filter(Boolean).join(' · ')}</span>
              </div>
              <dl>
                <div>
                  <dt>견적</dt>
                  <dd>{formatWon(group.quoteAmount)}</dd>
                </div>
                <div>
                  <dt>납품</dt>
                  <dd>{formatWon(group.deliveredAmount)}</dd>
                </div>
                <div>
                  <dt>잔여</dt>
                  <dd>{formatWon(group.remainingAmount)}</dd>
                </div>
                <div>
                  <dt>등록</dt>
                  <dd>{formatNumber(group.registeredQuotationCount)}개</dd>
                </div>
              </dl>
            </div>
          ))}
        </div>
      ) : null}

      {isDelivery && checks.delivery.sourceQuotes.length > 0 ? (
        <div className="schedule-commercial-source-list">
          <h4>연결된 원본 견적</h4>
          {checks.delivery.sourceQuotes.map((source) => (
            <div key={`${source.sourceQuoteScheduleId}-${source.quoteGroup}`}>
              <span>{[
                `일정 #${source.sourceQuoteScheduleId}`,
                source.quoteGroupLabel,
                `${formatNumber(source.itemCount)}개 품목`,
              ].filter(Boolean).join(' · ')}</span>
              <strong>{formatWon(source.amount)}</strong>
            </div>
          ))}
        </div>
      ) : null}

      {checks.delivery.historyAmountMismatches.length > 0 ? (
        <div className="schedule-commercial-source-list warning">
          <h4>납품 노트 금액</h4>
          {checks.delivery.historyAmountMismatches.slice(0, 3).map((mismatch) => (
            <div key={mismatch.historyId}>
              <span>{mismatch.createdAt ? formatDateTimeLabel(mismatch.createdAt) : `보고 #${mismatch.historyId}`}</span>
              <strong>{formatWon(mismatch.noteAmount)} / {formatWon(mismatch.itemAmount)}</strong>
            </div>
          ))}
        </div>
      ) : null}

      {checks.warnings.length > 0 ? (
        <div className="schedule-commercial-warning-list">
          {checks.warnings.map((warning, index) => (
            <div key={`${warning.code}-${index}`}>
              <AlertTriangle size={14} />
              <span>{warning.message}</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="schedule-commercial-auto ok">
          <CheckCircle2 size={15} />
          <span>현재 확인된 정합성 경고가 없습니다.</span>
        </div>
      )}
    </section>
  );
}

function ScheduleDocumentsPanel({
  documents,
  deletingDocumentKey,
  downloadingKey,
  previewAction,
  previewData,
  previewError,
  previewLoading,
  onClosePreview,
  onDelete,
  onDownload,
  onPreview,
}: {
  documents: ScheduleDetailData['documents'];
  deletingDocumentKey: string;
  downloadingKey: string;
  previewAction: ScheduleDocumentAction | null;
  previewData: ScheduleDocumentPreviewData | null;
  previewError: string;
  previewLoading: boolean;
  onClosePreview: () => void;
  onDelete: (document: ScheduleGeneratedDocument) => void;
  onDownload: (action: ScheduleDocumentAction, formatAction: ScheduleDocumentFormatAction, options?: ScheduleDocumentRequestOptions) => void;
  onPreview: (action: ScheduleDocumentAction, options?: ScheduleDocumentRequestOptions) => void;
}) {
  const [hideBaseUnitPriceByAction, setHideBaseUnitPriceByAction] = useState<Record<string, boolean>>({});
  const registeredDocuments = documents.registeredDocuments.length > 0
    ? documents.registeredDocuments
    : documents.registeredQuotations;

  if (!documents.items.length && !registeredDocuments.length) {
    return null;
  }

  const variableGroups = previewData ? buildScheduleDocumentVariableGroups(previewData.variables) : [];

  return (
    <section className="schedule-documents-panel" aria-label="서류 다운로드">
      <div className="schedule-file-heading schedule-document-heading">
        <h3 className="customer-detail-section-heading">서류 다운로드</h3>
        <a className="customer-row-action schedule-document-template-link" href={documents.templateManagerHref}>
          <FileText size={14} />
          <span>템플릿</span>
        </a>
      </div>
      <div className="schedule-document-list">
        {documents.items.map((action) => {
          const hasTemplate = action.templateCount > 0;
          const actionListKey = `${action.type}-${action.quoteGroup ?? ''}-${action.previewHref}`;
          const supportsHideBaseUnitPrice = action.type === 'quotation';
          const hideBaseUnitPrice = supportsHideBaseUnitPrice && Boolean(hideBaseUnitPriceByAction[actionListKey]);
          const documentOptions = hideBaseUnitPrice ? { hideBaseUnitPrice: true } : undefined;
          return (
            <div className="schedule-document-card" key={actionListKey}>
              <div className="schedule-document-card-main">
                <div>
                  <strong>{action.label}</strong>
                  <span>{action.description}</span>
                </div>
                <span className={hasTemplate ? 'schedule-document-template-count' : 'schedule-document-template-count empty'}>
                  {hasTemplate ? `${formatNumber(action.templateCount)}개 템플릿` : '템플릿 없음'}
                </span>
              </div>
              {supportsHideBaseUnitPrice ? (
                <label className="schedule-document-option-check">
                  <input
                    checked={hideBaseUnitPrice}
                    onChange={(event) => setHideBaseUnitPriceByAction((previous) => ({
                      ...previous,
                      [actionListKey]: event.target.checked,
                    }))}
                    type="checkbox"
                  />
                  <span>기준단가 가리기</span>
                </label>
              ) : null}
              <div className="schedule-document-actions">
                <button
                  className="customer-row-action schedule-document-action-button"
                  disabled={!hasTemplate || previewLoading}
                  onClick={() => onPreview(action, documentOptions)}
                  type="button"
                >
                  {previewLoading && previewAction?.previewHref === action.previewHref ? <Loader2 className="spin-icon" size={14} /> : <Eye size={14} />}
                  <span>미리보기</span>
                </button>
                {action.formats.map((formatAction) => {
                  const actionKey = scheduleDocumentDownloadKey(action, formatAction, documentOptions);
                  const downloading = downloadingKey === actionKey;
                  return (
                    <button
                      className="customer-row-action schedule-document-action-button"
                      disabled={!hasTemplate || Boolean(downloadingKey)}
                      key={formatAction.format}
                      onClick={() => onDownload(action, formatAction, documentOptions)}
                      type="button"
                    >
                      {downloading ? (
                        <Loader2 className="spin-icon" size={14} />
                      ) : formatAction.format === 'xlsx' ? (
                        <FileSpreadsheet size={14} />
                      ) : (
                        <Download size={14} />
                      )}
                      <span>{formatAction.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {documents.autoAttachLabel ? (
        <div className="dashboard-api-alert compact success">
          <FileText size={16} />
          <span>{documents.autoAttachLabel}</span>
        </div>
      ) : null}

      {registeredDocuments.length > 0 ? (
        <div className="schedule-quote-document-list">
          <h4>등록된 서류</h4>
          {registeredDocuments.map((document) => (
            <div className="schedule-quote-document-row" key={document.id}>
              <a href={document.downloadHref}>
                <FileText size={14} />
                <span>
                  {[
                    document.documentTypeLabel,
                    document.quoteGroupLabel && document.documentType === 'quotation' ? document.quoteGroupLabel : '',
                    document.filename || document.transactionNumber,
                  ].filter(Boolean).join(' · ')}
                </span>
                <small>{[document.size, document.createdAt ? formatDateTimeLabel(document.createdAt) : ''].filter(Boolean).join(' · ')}</small>
              </a>
              {document.canDelete && document.deleteHref ? (
                <button
                  aria-label={`${document.filename || document.transactionNumber} 삭제`}
                  className="schedule-quote-document-delete"
                  disabled={Boolean(deletingDocumentKey)}
                  onClick={() => onDelete(document)}
                  type="button"
                >
                  {deletingDocumentKey === String(document.id) ? <Loader2 className="spin-icon" size={13} /> : <Trash2 size={13} />}
                </button>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}

      {previewError ? (
        <div className="dashboard-api-alert compact">
          <AlertTriangle size={16} />
          <span>{previewError}</span>
        </div>
      ) : null}

      {previewAction ? (
        <div className="schedule-document-preview">
          <div className="schedule-document-preview-heading">
            <div>
              <span className="eyebrow">Preview</span>
              <h4>{previewAction.label} 변수</h4>
            </div>
            <button className="customer-row-action schedule-document-close-button" onClick={onClosePreview} type="button">
              <X size={13} />
              <span>닫기</span>
            </button>
          </div>
          {previewLoading ? (
            <div className="schedule-document-preview-loading">
              <Loader2 className="spin-icon" size={15} />
              <span>변수 데이터를 불러오는 중입니다</span>
            </div>
          ) : previewData ? (
            <>
              <div className="schedule-document-preview-meta">
                <span>{previewData.fileInfo.docName || previewAction.label}</span>
                <span>{previewData.templateFilename || '템플릿 파일명 없음'}</span>
                {previewData.fileInfo.quoteGroupLabel ? <span>{previewData.fileInfo.quoteGroupLabel}</span> : null}
                <span>품목 {formatNumber(previewData.itemCount)}개</span>
              </div>
              {variableGroups.length > 0 ? (
                <div className="schedule-document-variable-groups">
                  {variableGroups.map((group) => (
                    <div className="schedule-document-variable-group" key={group.label}>
                      <h5>{group.label}</h5>
                      <div className="schedule-document-variable-grid">
                        {group.entries.map(([key, value]) => (
                          <div className={isScheduleDocumentEmptyValue(value) ? 'schedule-document-variable-row empty' : 'schedule-document-variable-row'} key={key}>
                            <span>{key}</span>
                            <strong>{formatScheduleDocumentValue(value)}</strong>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <DashboardEmpty label="표시할 서류 변수가 없습니다" />
              )}
              {previewData.items.length > 0 ? (
                <div className="schedule-document-item-list">
                  {previewData.items.map((item) => (
                    <div key={item.index}>
                      <strong>{item.quoteGroupLabel ? `[${item.quoteGroupLabel}] ${item.name || `품목 ${item.index}`}` : item.name || `품목 ${item.index}`}</strong>
                      <span>{[
                        `${formatNumber(item.quantity)}${item.unit || ''}`,
                        !item.baseUnitPriceHidden && item.discountUnitPrice !== null ? `기준 ${formatWon(item.baseUnitPrice)}` : '',
                        item.discountUnitPrice !== null ? `할인 ${formatWon(item.discountUnitPrice)}` : formatWon(item.unitPrice),
                        formatWon(item.subtotal),
                        item.notes,
                      ].filter(Boolean).join(' · ')}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <DashboardEmpty label="서류에 들어갈 품목이 없습니다" />
              )}
            </>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function AIEvidenceList({
  className = '',
  items,
  limit = 6,
}: {
  className?: string;
  items: AIWorkspaceActionEvidence[];
  limit?: number;
}) {
  const rows = items.slice(0, limit).filter((item) => item.label || item.value);
  if (!rows.length) {
    return null;
  }
  return (
    <div className={['ai-evidence-list', className].filter(Boolean).join(' ')}>
      {rows.map((item, index) => (
        <span className="ai-evidence-row" key={`${item.label}-${item.value}-${item.href || index}`}>
          <b>{item.label}</b>
          {item.value}
          {item.href ? (
            <a className="ai-evidence-link" href={item.href}>
              <Link2 size={12} />
              {item.linkLabel || '열기'}
            </a>
          ) : null}
        </span>
      ))}
    </div>
  );
}

function ScheduleAICoachPanel({
  canUseAi,
  error,
  loading,
  message,
  permissionMessage,
  onGenerate,
  result,
}: {
  canUseAi: boolean;
  error: string;
  loading: boolean;
  message: string;
  permissionMessage: string;
  onGenerate: () => void;
  result: ScheduleAICoachResponse | null;
}) {
  const coach = result?.coach ?? null;
  const risks = coach?.risks ?? [];
  const evidence = coach?.evidence ?? [];

  return (
    <section className="schedule-ai-coach-panel" aria-label="일정 AI 브리핑">
      <div className="schedule-ai-coach-heading">
        <div>
          <span className="eyebrow">Schedule brief</span>
          <h3>일정 브리핑</h3>
        </div>
        <button className="customer-row-action schedule-ai-coach-run" disabled={!canUseAi || loading} onClick={onGenerate} type="button">
          {loading ? <Loader2 className="spin-icon" size={14} /> : <Sparkles size={14} />}
          <span>{loading ? '분석 중' : coach ? '다시 보기' : '브리핑 보기'}</span>
        </button>
      </div>
      {!canUseAi ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{permissionMessage || 'AI 기능 사용 권한이 없습니다.'}</span></div> : null}
      {error ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{error}</span></div> : null}
      {message ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{message}</span></div> : null}
      {coach ? (
        <div className="schedule-ai-coach-body">
          <div className="schedule-ai-coach-summary">
            <p>{coach.summary}</p>
            <span>{result?.source === 'openai' ? `${result.modelLabel || 'AI'} 브리핑` : 'CRM 기반 브리핑'} · {coach.confidence}</span>
          </div>
          {coach.recommendedNextAction ? (
            <div className="schedule-ai-coach-next">
              <span>확인 필요</span>
              <strong>{coach.recommendedNextAction}</strong>
            </div>
          ) : null}
          {coach.talkTrack.length > 0 ? (
            <div className="schedule-ai-coach-list">
              <h4>브리핑 메모</h4>
              {coach.talkTrack.map((item) => <p key={item}>{item}</p>)}
            </div>
          ) : null}
          {coach.checklist.length > 0 ? (
            <div className="schedule-ai-coach-checklist">
              {coach.checklist.map((item) => (
                <span key={item}><CheckCircle2 size={13} />{item}</span>
              ))}
            </div>
          ) : null}
          {risks.length > 0 ? (
            <div className="schedule-ai-coach-risk-list">
              {risks.map((risk) => (
                <div className={risk.level || 'medium'} key={`${risk.label}-${risk.value}`}>
                  <AlertTriangle size={14} />
                  <span><strong>{risk.label}</strong>{risk.value}</span>
                </div>
              ))}
            </div>
          ) : null}
          {evidence.length > 0 ? (
            <AIEvidenceList className="schedule-ai-coach-evidence" items={evidence} limit={5} />
          ) : null}
        </div>
      ) : (
        <DashboardEmpty label="현재 일정 기준 브리핑을 확인하세요" />
      )}
    </section>
  );
}

export function ScheduleDetailPage({
  data,
  loading,
  onRefresh,
}: {
  data: ScheduleDetailData | null;
  loading: boolean;
  onRefresh: () => Promise<ScheduleDetailData | null>;
}) {
  const currentSchedule = data?.schedule ?? null;
  const [editOpen, setEditOpen] = useState(false);
  const [editForm, setEditForm] = useState<ScheduleEditFormState>(() => makeScheduleEditForm(currentSchedule));
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState('');
  const [editMessage, setEditMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [fileUploading, setFileUploading] = useState(false);
  const [fileDeletingId, setFileDeletingId] = useState<number | null>(null);
  const [fileError, setFileError] = useState('');
  const [fileMessage, setFileMessage] = useState('');
  const [deliveryEditOpen, setDeliveryEditOpen] = useState(false);
  const [deliveryRows, setDeliveryRows] = useState<ScheduleDeliveryEditRow[]>(() => makeScheduleDeliveryEditRows(data?.deliveryItems ?? []));
  const [quoteGroupNotes, setQuoteGroupNotes] = useState<ScheduleQuoteGroupNoteState>(() => makeScheduleQuoteGroupNotes(currentSchedule));
  const [deliverySaving, setDeliverySaving] = useState(false);
  const [deliveryError, setDeliveryError] = useState('');
  const [deliveryMessage, setDeliveryMessage] = useState('');
  const [deliveryUsePrepayment, setDeliveryUsePrepayment] = useState(Boolean(currentSchedule?.activityType === 'delivery' && currentSchedule.usePrepayment));
  const [deliveryPrepaymentRows, setDeliveryPrepaymentRows] = useState<SchedulePrepaymentEditRow[]>([]);
  const [deliveryPrepaymentsLoading, setDeliveryPrepaymentsLoading] = useState(false);
  const [deliveryPrepaymentsError, setDeliveryPrepaymentsError] = useState('');
  const [quoteImportData, setQuoteImportData] = useState<FollowupQuoteItemsData | null>(null);
  const [quoteImportOpen, setQuoteImportOpen] = useState(false);
  const [quoteImportLoading, setQuoteImportLoading] = useState(false);
  const [quoteImportError, setQuoteImportError] = useState('');
  const [selectedQuoteImportIds, setSelectedQuoteImportIds] = useState<string[]>([]);
  const [productOptions, setProductOptions] = useState<ProductOption[]>([]);
  const [productsLoaded, setProductsLoaded] = useState(false);
  const [productsLoading, setProductsLoading] = useState(false);
  const [productError, setProductError] = useState('');
  const [scheduleDeleting, setScheduleDeleting] = useState(false);
  const [scheduleDeleteError, setScheduleDeleteError] = useState('');
  const [prepaymentRows, setPrepaymentRows] = useState<SchedulePrepaymentEditRow[]>([]);
  const [prepaymentsLoading, setPrepaymentsLoading] = useState(false);
  const [prepaymentsError, setPrepaymentsError] = useState('');
  const [documentDownloadingKey, setDocumentDownloadingKey] = useState('');
  const [documentDeletingKey, setDocumentDeletingKey] = useState('');
  const [documentPreviewAction, setDocumentPreviewAction] = useState<ScheduleDocumentAction | null>(null);
  const [documentPreviewData, setDocumentPreviewData] = useState<ScheduleDocumentPreviewData | null>(null);
  const [documentPreviewLoading, setDocumentPreviewLoading] = useState(false);
  const [documentPreviewError, setDocumentPreviewError] = useState('');
  const [scheduleNoteOpen, setScheduleNoteOpen] = useState(false);
  const [scheduleNoteForm, setScheduleNoteForm] = useState<NoteCreateFormState>(() => makeScheduleNoteCreateForm(currentSchedule));
  const [scheduleNoteSaving, setScheduleNoteSaving] = useState(false);
  const [scheduleNoteError, setScheduleNoteError] = useState('');
  const [scheduleNoteMessage, setScheduleNoteMessage] = useState('');
  const [scheduleNoteHref, setScheduleNoteHref] = useState('');
  const [scheduleCoachLoading, setScheduleCoachLoading] = useState(false);
  const [scheduleCoachError, setScheduleCoachError] = useState('');
  const [scheduleCoachMessage, setScheduleCoachMessage] = useState('');
  const [scheduleCoachResult, setScheduleCoachResult] = useState<ScheduleAICoachResponse | null>(null);
  const scheduleNotePanelRef = useRef<HTMLElement | null>(null);
  const scheduleEditPanelRef = useRef<HTMLElement | null>(null);
  const quoteImportPanelRef = useRef<HTMLDivElement | null>(null);
  const deliveryEditPanelRef = useRef<HTMLFormElement | null>(null);

  useGuidedPanelFocus(scheduleNoteOpen, scheduleNotePanelRef, `schedule-note-${currentSchedule?.id || 'new'}`);
  useGuidedPanelFocus(editOpen, scheduleEditPanelRef, `schedule-edit-${currentSchedule?.id || 'new'}`);
  useGuidedPanelFocus(quoteImportOpen, quoteImportPanelRef, `quote-import-${currentSchedule?.id || 'new'}`, { focusFirst: false });
  useGuidedPanelFocus(deliveryEditOpen, deliveryEditPanelRef, `delivery-edit-${currentSchedule?.id || 'new'}`);

  useEffect(() => {
    setEditForm(makeScheduleEditForm(currentSchedule));
    setEditError('');
    setEditMessage('');
    setEditOpen(false);
    setFileError('');
    setFileMessage('');
    setFileUploading(false);
    setFileDeletingId(null);
    setDeliveryEditOpen(false);
    setDeliveryRows(makeScheduleDeliveryEditRows(data?.deliveryItems ?? []));
    setQuoteGroupNotes(makeScheduleQuoteGroupNotes(data?.schedule ?? null));
    setDeliverySaving(false);
    setDeliveryError('');
    setDeliveryMessage('');
    setDeliveryUsePrepayment(Boolean(data?.schedule?.activityType === 'delivery' && data.schedule.usePrepayment));
    setDeliveryPrepaymentRows([]);
    setDeliveryPrepaymentsLoading(false);
    setDeliveryPrepaymentsError('');
    setQuoteImportData(null);
    setQuoteImportOpen(false);
    setQuoteImportLoading(false);
    setQuoteImportError('');
    setSelectedQuoteImportIds([]);
    setProductError('');
    setScheduleDeleting(false);
    setScheduleDeleteError('');
    setPrepaymentRows([]);
    setPrepaymentsLoading(false);
    setPrepaymentsError('');
    setDocumentDownloadingKey('');
    setDocumentDeletingKey('');
    setDocumentPreviewAction(null);
    setDocumentPreviewData(null);
    setDocumentPreviewLoading(false);
    setDocumentPreviewError('');
    setScheduleNoteOpen(false);
    setScheduleNoteForm(makeScheduleNoteCreateForm(data?.schedule ?? null));
    setScheduleNoteSaving(false);
    setScheduleNoteError('');
    setScheduleNoteMessage('');
    setScheduleNoteHref('');
    setScheduleCoachLoading(false);
    setScheduleCoachError('');
    setScheduleCoachMessage('');
    setScheduleCoachResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [currentSchedule?.id]);

  useEffect(() => {
    if (
      !editOpen ||
      !currentSchedule?.canEdit ||
      editForm.activityType !== 'delivery' ||
      !editForm.followupId
    ) {
      setPrepaymentRows([]);
      setPrepaymentsLoading(false);
      setPrepaymentsError('');
      return undefined;
    }

    const followupId = Number(editForm.followupId);
    if (!followupId) {
      setPrepaymentRows([]);
      return undefined;
    }

    let active = true;
    setPrepaymentsLoading(true);
    setPrepaymentsError('');
    loadPrepayments(followupId, currentSchedule.id)
      .then((options) => {
        if (active) {
          setPrepaymentRows(makeSchedulePrepaymentRows(options));
        }
      })
      .catch((error) => {
        if (active) {
          setPrepaymentRows([]);
          setPrepaymentsError(error instanceof Error ? error.message : '선결제 목록을 불러오지 못했습니다.');
        }
      })
      .finally(() => {
        if (active) {
          setPrepaymentsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [editOpen, editForm.activityType, editForm.followupId, currentSchedule?.canEdit, currentSchedule?.id]);

  useEffect(() => {
    if (
      !deliveryEditOpen ||
      !currentSchedule?.canEdit ||
      currentSchedule.activityType !== 'delivery' ||
      !currentSchedule.followupId
    ) {
      setDeliveryPrepaymentRows([]);
      setDeliveryPrepaymentsLoading(false);
      setDeliveryPrepaymentsError('');
      return undefined;
    }

    let active = true;
    setDeliveryPrepaymentsLoading(true);
    setDeliveryPrepaymentsError('');
    loadPrepayments(currentSchedule.followupId, currentSchedule.id)
      .then((options) => {
        if (active) {
          setDeliveryPrepaymentRows(makeSchedulePrepaymentRows(options));
        }
      })
      .catch((error) => {
        if (active) {
          setDeliveryPrepaymentRows([]);
          setDeliveryPrepaymentsError(error instanceof Error ? error.message : '선결제 목록을 불러오지 못했습니다.');
        }
      })
      .finally(() => {
        if (active) {
          setDeliveryPrepaymentsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [deliveryEditOpen, currentSchedule?.activityType, currentSchedule?.canEdit, currentSchedule?.followupId, currentSchedule?.id]);

  const handleEditFieldChange = (field: keyof ScheduleEditFormState, value: string | boolean) => {
    setEditForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setEditError('');
    setEditMessage('');
  };

  const handlePrepaymentRowToggle = (id: number, selected: boolean) => {
    setPrepaymentRows((rows) => rows.map((row) => (
      row.id === id
        ? {
          ...row,
          selected,
          amountInput: selected && !row.amountInput && row.selectedAmount > 0 ? String(row.selectedAmount) : row.amountInput,
        }
        : row
    )));
    setEditError('');
    setEditMessage('');
  };

  const handlePrepaymentAmountChange = (id: number, amountInput: string) => {
    setPrepaymentRows((rows) => rows.map((row) => (
      row.id === id ? { ...row, amountInput } : row
    )));
    setEditError('');
    setEditMessage('');
  };

  const handleScheduleNoteFieldChange = (field: keyof NoteCreateFormState, value: string) => {
    setScheduleNoteForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setScheduleNoteError('');
    setScheduleNoteMessage('');
    setScheduleNoteHref('');
  };

  const handleScheduleNoteToggle = () => {
    if (!currentSchedule?.canEdit) {
      setScheduleNoteError('영업노트 작성 권한이 없습니다.');
      return;
    }
    setScheduleNoteForm((previous) => ({
      ...makeScheduleNoteCreateForm(currentSchedule),
      content: previous.content,
      nextAction: previous.nextAction,
      nextActionDate: previous.nextActionDate,
    }));
    setScheduleNoteOpen((open) => !open);
    setScheduleNoteError('');
    setScheduleNoteMessage('');
    setScheduleNoteHref('');
  };

  const handleScheduleNoteSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!currentSchedule || scheduleNoteSaving) {
      return;
    }
    if (!currentSchedule.canEdit) {
      setScheduleNoteError('영업노트 작성 권한이 없습니다.');
      return;
    }
    const followupId = Number(scheduleNoteForm.followupId);
    const departmentId = Number(scheduleNoteForm.departmentId);
    const scheduleId = Number(scheduleNoteForm.scheduleId);
    if ((!followupId && !departmentId) || !scheduleId) {
      setScheduleNoteError('연결할 고객 또는 부서/연구실과 일정 정보가 없습니다.');
      return;
    }
    if (!scheduleNoteForm.actionType) {
      setScheduleNoteError('활동 유형을 선택하세요.');
      return;
    }
    if (!scheduleNoteForm.content.trim()) {
      setScheduleNoteError('활동 내용을 입력하세요.');
      return;
    }

    const payload: NoteCreatePayload = {
      actionType: scheduleNoteForm.actionType,
      activityDate: scheduleNoteForm.activityDate || undefined,
      content: scheduleNoteForm.content.trim(),
      departmentId: departmentId || undefined,
      followupId: followupId || undefined,
      nextAction: scheduleNoteForm.nextAction.trim() || undefined,
      nextActionDate: scheduleNoteForm.nextActionDate || undefined,
      scheduleId,
    };

    setScheduleNoteSaving(true);
    setScheduleNoteError('');
    setScheduleNoteMessage('');
    setScheduleNoteHref('');
    try {
      const result = await createSalesNote(payload);
      await onRefresh();
      setScheduleNoteMessage(result.message || '일정에 영업노트를 연결했습니다.');
      setScheduleNoteHref(result.reactHref || (result.historyId ? `/notes/${result.historyId}/` : ''));
      setScheduleNoteForm(makeScheduleNoteCreateForm(currentSchedule));
      setScheduleNoteOpen(false);
    } catch (error) {
      setScheduleNoteError(error instanceof Error ? error.message : '영업노트 저장에 실패했습니다.');
    } finally {
      setScheduleNoteSaving(false);
    }
  };

  const handleScheduleCoachRun = async () => {
    if (!currentSchedule || scheduleCoachLoading) {
      return;
    }
    setScheduleCoachLoading(true);
    setScheduleCoachError('');
    setScheduleCoachMessage('');
    try {
      const result = await generateScheduleAICoach(currentSchedule.id);
      setScheduleCoachResult(result);
      setScheduleCoachMessage(result.context?.stored === false ? '브리핑은 저장되지 않았습니다.' : '');
    } catch (error) {
      setScheduleCoachResult(null);
      setScheduleCoachError(error instanceof Error ? error.message : '일정 AI 브리핑 생성에 실패했습니다.');
    } finally {
      setScheduleCoachLoading(false);
    }
  };

  const handleDeliveryPrepaymentToggle = (selected: boolean) => {
    if (selected && scheduleDeliveryEditRowsTotal(deliveryRows) <= 0) {
      setDeliveryUsePrepayment(true);
      setDeliveryError('선결제를 차감하려면 먼저 견적 품목을 불러오거나 납품 품목 금액을 입력하세요.');
      setDeliveryMessage('');
      return;
    }
    setDeliveryUsePrepayment(selected);
    setDeliveryError('');
    setDeliveryMessage('');
  };

  const handleDeliveryPrepaymentRowToggle = (id: number, selected: boolean) => {
    if (selected && scheduleDeliveryEditRowsTotal(deliveryRows) <= 0) {
      setDeliveryError('선결제를 차감하려면 먼저 견적 품목을 불러오거나 납품 품목 금액을 입력하세요.');
      setDeliveryMessage('');
      return;
    }
    setDeliveryPrepaymentRows((rows) => rows.map((row) => (
      row.id === id
        ? {
          ...row,
          selected,
          amountInput: selected && !row.amountInput && row.selectedAmount > 0 ? String(row.selectedAmount) : row.amountInput,
        }
        : row
    )));
    setDeliveryError('');
    setDeliveryMessage('');
  };

  const handleDeliveryPrepaymentAmountChange = (id: number, amountInput: string) => {
    setDeliveryPrepaymentRows((rows) => rows.map((row) => (
      row.id === id ? { ...row, amountInput } : row
    )));
    setDeliveryError('');
    setDeliveryMessage('');
  };

  const handleDeliveryPrepaymentFillMax = (id: number, maxAmount: number) => {
    setDeliveryPrepaymentRows((rows) => rows.map((row) => (
      row.id === id ? { ...row, amountInput: String(Math.max(Math.round(maxAmount), 0)) } : row
    )));
    setDeliveryError('');
    setDeliveryMessage('');
  };

  const handleEditSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!currentSchedule || !data?.edit || editSaving) {
      return;
    }
    if (!data.edit.canEdit) {
      setEditError(data.edit.message || '수정 권한이 없습니다.');
      return;
    }
    const followupId = Number(editForm.followupId);
    if (!followupId) {
      setEditError('고객을 선택하세요.');
      return;
    }
    if (!editForm.activityType) {
      setEditError('일정 유형을 선택하세요.');
      return;
    }
    if (!editForm.status) {
      setEditError('일정 상태를 선택하세요.');
      return;
    }
    if (!editForm.visitDate) {
      setEditError('일정 날짜를 선택하세요.');
      return;
    }
    if (!editForm.visitTime) {
      setEditError('일정 시간을 선택하세요.');
      return;
    }
    const probability = normalizeProbabilityInputValue(editForm.probability);
    if (isQuoteProbabilityRequired(editForm.activityType) && !probability) {
      setEditError('견적 성공 확률은 필수입니다.');
      return;
    }

    const prepaymentSelections = prepaymentRows.filter((row) => row.selected);
    const usePrepayment = editForm.activityType === 'delivery' && editForm.usePrepayment;
    if (usePrepayment) {
      if (prepaymentsLoading) {
        setEditError('선결제 목록을 불러오는 중입니다.');
        return;
      }
      if (prepaymentsError) {
        setEditError(prepaymentsError);
        return;
      }
      if (!prepaymentSelections.length) {
        setEditError('사용할 선결제를 선택하세요.');
        return;
      }
      for (const [index, row] of prepaymentSelections.entries()) {
        const amount = Number(row.amountInput);
        if (!Number.isFinite(amount) || amount <= 0) {
          setEditError(`${index + 1}번째 선결제 차감 금액을 입력하세요.`);
          return;
        }
        if (amount > row.availableBalance) {
          setEditError(`${row.payerName} 선결제 잔액이 부족합니다.`);
          return;
        }
      }
    }

    const payload: ScheduleEditPayload = {
      activityType: editForm.activityType,
      expectedCloseDate: editForm.expectedCloseDate || undefined,
      expectedRevenue: editForm.expectedRevenue.trim() || undefined,
      vatMode: editForm.vatMode || undefined,
      followupId,
      location: editForm.location.trim() || undefined,
      notes: editForm.notes.trim() || undefined,
      probability: probability || undefined,
      prepayments: usePrepayment
        ? prepaymentSelections.map((row) => ({ id: row.id, amount: row.amountInput.trim() }))
        : [],
      purchaseConfirmed: editForm.purchaseConfirmed,
      status: editForm.status,
      usePrepayment,
      visitDate: editForm.visitDate,
      visitTime: editForm.visitTime,
    };

    setEditSaving(true);
    setEditError('');
    setEditMessage('');
    try {
      const updated = await updateCustomerSchedule(payload, data.edit.submitUrl);
      await onRefresh();
      setEditMessage(updated.message || '일정을 수정했습니다.');
      setEditOpen(false);
    } catch (error) {
      setEditError(error instanceof Error ? error.message : '일정 수정에 실패했습니다.');
    } finally {
      setEditSaving(false);
    }
  };

  const handleScheduleFileUploadClick = () => {
    if (!currentSchedule?.canEdit || !data?.links.uploadFiles) {
      setFileError('첨부파일 업로드 권한이 없습니다.');
      setFileMessage('');
      return;
    }
    fileInputRef.current?.click();
  };

  const handleScheduleFilesSelected = async (event: ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files ?? []);
    if (!selectedFiles.length) {
      return;
    }

    if (!currentSchedule?.canEdit || !data?.links.uploadFiles) {
      setFileError('첨부파일 업로드 권한이 없습니다.');
      setFileMessage('');
      event.target.value = '';
      return;
    }

    if (currentSchedule.files.length + selectedFiles.length > 5) {
      setFileError(`첨부파일은 최대 5개까지 등록할 수 있습니다. 현재 ${currentSchedule.files.length}개가 등록되어 있습니다.`);
      setFileMessage('');
      event.target.value = '';
      return;
    }

    setFileUploading(true);
    setFileError('');
    setFileMessage('');
    try {
      const result = await uploadScheduleFiles(data.links.uploadFiles, selectedFiles);
      await onRefresh();
      setFileMessage(result.message || `${selectedFiles.length}개 파일을 업로드했습니다.`);
    } catch (error) {
      setFileError(error instanceof Error ? error.message : '첨부파일 업로드에 실패했습니다.');
    } finally {
      setFileUploading(false);
      event.target.value = '';
    }
  };

  const handleScheduleFileDelete = async (file: ScheduleFileItem | AttachmentManagerFile) => {
    if (fileDeletingId !== null) {
      return;
    }
    if (!currentSchedule?.canEdit || !file.canDelete || !file.deleteHref) {
      setFileError('첨부파일 삭제 권한이 없습니다.');
      setFileMessage('');
      return;
    }
    if (!window.confirm(`"${file.filename}" 파일을 삭제할까요?`)) {
      return;
    }

    setFileDeletingId(Number(file.id));
    setFileError('');
    setFileMessage('');
    try {
      const result = await deleteScheduleFile(file.deleteHref);
      await onRefresh();
      setFileMessage(result.message || '첨부파일을 삭제했습니다.');
    } catch (error) {
      setFileError(error instanceof Error ? error.message : '첨부파일 삭제에 실패했습니다.');
    } finally {
      setFileDeletingId(null);
    }
  };

  const ensureProductsLoaded = async () => {
    if (productsLoaded || productsLoading) {
      return;
    }
    setProductsLoading(true);
    setProductError('');
    try {
      const products = await loadProducts();
      setProductOptions(products);
      setProductsLoaded(true);
    } catch (error) {
      setProductError(error instanceof Error ? error.message : '제품 목록을 불러오지 못했습니다.');
    } finally {
      setProductsLoading(false);
    }
  };

  const getDeliveryProductMatches = (query: string) => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) {
      return [];
    }
    return productOptions.filter((product) => (
      product.productCode.toLowerCase().includes(normalizedQuery) ||
      product.name.toLowerCase().includes(normalizedQuery) ||
      product.description.toLowerCase().includes(normalizedQuery) ||
      product.specification.toLowerCase().includes(normalizedQuery)
    )).slice(0, 6);
  };

  const handleDeliveryEditToggle = () => {
    if (!currentSchedule?.canEdit || !data?.links.updateDeliveryItems) {
      setDeliveryError('납품 품목 수정 권한이 없습니다.');
      setDeliveryMessage('');
      return;
    }
    const willOpen = !deliveryEditOpen;
    setDeliveryRows(makeScheduleDeliveryEditRows(data.deliveryItems));
    setDeliveryUsePrepayment(Boolean(willOpen && currentSchedule.activityType === 'delivery' && currentSchedule.usePrepayment));
    setDeliveryError('');
    setDeliveryMessage('');
    setProductError('');
    setDeliveryEditOpen((open) => !open);
    if (willOpen) {
      void ensureProductsLoaded();
    }
  };

  const loadQuoteImports = async () => {
    if (!currentSchedule?.followupId) {
      setQuoteImportError('연결된 고객 정보가 없어 견적을 불러올 수 없습니다.');
      return;
    }
    if (quoteImportLoading) {
      return;
    }
    setQuoteImportLoading(true);
    setQuoteImportError('');
    try {
      const quotes = await loadFollowupQuoteItems(currentSchedule.followupId);
      setQuoteImportData(quotes);
      const availableQuoteIds = new Set(quotes.quotes.map((quote) => quote.optionId));
      setSelectedQuoteImportIds((previous) => previous.filter((optionId) => availableQuoteIds.has(optionId)));
      if (!quotes.quotes.length) {
        setQuoteImportError('불러올 수 있는 견적 품목이 없습니다.');
      }
    } catch (error) {
      setQuoteImportData(null);
      setQuoteImportError(error instanceof Error ? error.message : '견적 품목을 불러오지 못했습니다.');
    } finally {
      setQuoteImportLoading(false);
    }
  };

  const handleQuoteImportToggle = () => {
    if (!currentSchedule?.canEdit || !data?.links.updateDeliveryItems) {
      setDeliveryError('납품 품목 수정 권한이 없습니다.');
      setDeliveryMessage('');
      return;
    }
    if (currentSchedule.activityType !== 'delivery') {
      setDeliveryError('견적 품목 불러오기는 납품 일정에서만 사용할 수 있습니다.');
      setDeliveryMessage('');
      return;
    }
    if (quoteImportOpen) {
      setQuoteImportOpen(false);
      setQuoteImportError('');
      setSelectedQuoteImportIds([]);
      return;
    }
    setDeliveryEditOpen(true);
    setDeliveryUsePrepayment((previous) => previous || Boolean(currentSchedule.usePrepayment));
    setDeliveryError('');
    setDeliveryMessage('');
    setQuoteImportOpen(true);
    setSelectedQuoteImportIds([]);
    void ensureProductsLoaded();
    void loadQuoteImports();
  };

  const handleQuoteImportOpenFromPrepayment = () => {
    if (quoteImportOpen) {
      void loadQuoteImports();
      return;
    }
    handleQuoteImportToggle();
  };

  const handleQuoteImportSelectionChange = (optionId: string, selected: boolean) => {
    setSelectedQuoteImportIds((previous) => {
      if (selected) {
        return previous.includes(optionId) ? previous : [...previous, optionId];
      }
      return previous.filter((id) => id !== optionId);
    });
    setQuoteImportError('');
  };

  const handleQuoteImportApply = (quotes: FollowupQuoteOption | FollowupQuoteOption[]) => {
    const quoteList = (Array.isArray(quotes) ? quotes : [quotes]).filter((quote) => quote.items.length > 0);
    if (!quoteList.length) {
      setQuoteImportError('선택한 견적에 품목이 없습니다.');
      return;
    }
    if (
      scheduleDeliveryRowsHaveUserInput(deliveryRows) &&
      !window.confirm('현재 입력된 납품 품목을 선택한 견적 품목으로 바꿀까요?')
    ) {
      return;
    }
    const importedRows = quoteList.flatMap((quote, quoteIndex) => (
      quote.items.map((item, itemIndex) => makeScheduleDeliveryEditRowFromQuoteItem(
        item,
        quote,
        quoteIndex * 1000 + itemIndex,
      ))
    ));
    setDeliveryRows(importedRows.length > 0 ? importedRows : [makeScheduleDeliveryEditRow(undefined, 0)]);
    setDeliveryEditOpen(true);
    setQuoteImportOpen(false);
    setSelectedQuoteImportIds([]);
    setQuoteImportError('');
    setDeliveryError('');
    const quoteLabel = quoteList.length === 1 ? quoteImportOptionTitle(quoteList[0]) : `${quoteList.length}개 견적`;
    setDeliveryMessage(`${quoteLabel} 품목 ${importedRows.length}개를 불러왔습니다. 저장을 눌러 납품 일정에 반영하세요.`);
  };

  const handleSelectedQuoteImportApply = () => {
    const selectedQuotes = quoteImportData?.quotes.filter((quote) => selectedQuoteImportIds.includes(quote.optionId)) ?? [];
    handleQuoteImportApply(selectedQuotes);
  };

  const handleDeliveryFieldChange = (rowId: string, field: ScheduleDeliveryEditField, value: string | boolean) => {
    setDeliveryRows((rows) => rows.map((row) => (
      row.rowId === rowId ? (() => {
        const nextRow = { ...row, [field]: value } as ScheduleDeliveryEditRow;
        const basePrice = parsePositiveFormNumber(String(field === 'unitPrice' ? value : nextRow.unitPrice));
        if (field === 'discountRate') {
          const rate = parsePositiveFormNumber(String(value));
          nextRow.discountUnitPrice = basePrice !== null && rate !== null ? moneyInputValue(discountUnitFromRate(basePrice, rate)) : '';
        } else if (field === 'discountUnitPrice') {
          const discountUnit = parsePositiveFormNumber(String(value));
          nextRow.discountRate = basePrice !== null && discountUnit !== null ? rateInputValue(discountRateFromUnit(basePrice, discountUnit)) : '';
        } else if (field === 'unitPrice') {
          const rate = parsePositiveFormNumber(nextRow.discountRate);
          const discountUnit = parsePositiveFormNumber(nextRow.discountUnitPrice);
          if (basePrice !== null && rate !== null && nextRow.discountRate.trim()) {
            nextRow.discountUnitPrice = moneyInputValue(discountUnitFromRate(basePrice, rate));
          } else if (basePrice !== null && discountUnit !== null && nextRow.discountUnitPrice.trim()) {
            nextRow.discountRate = rateInputValue(discountRateFromUnit(basePrice, discountUnit));
          }
        }
        return nextRow;
      })() : row
    )));
    setDeliveryError('');
    setDeliveryMessage('');
  };

  const handleDeliveryProductQueryChange = (rowId: string, value: string) => {
    setDeliveryRows((rows) => rows.map((row) => (
      row.rowId === rowId ? { ...row, productId: '', productQuery: value } : row
    )));
    setDeliveryError('');
    setDeliveryMessage('');
    setProductError('');
  };

  const handleDeliveryProductSelect = (rowId: string, product: ProductOption) => {
    const unitPrice = product.currentPrice || product.standardPrice || '';
    setDeliveryRows((rows) => rows.map((row) => (
      row.rowId === rowId ? {
        ...row,
        productId: String(product.id),
        productQuery: product.productCode,
        itemName: product.productCode,
        unit: product.unit || 'EA',
        unitPrice: unitPrice === '' ? '' : String(unitPrice),
        discountRate: '',
        discountUnitPrice: '',
      } : row
    )));
    setDeliveryError('');
    setDeliveryMessage('');
    setProductError('');
  };

  const handleDeliveryProductClear = (rowId: string) => {
    setDeliveryRows((rows) => rows.map((row) => (
      row.rowId === rowId ? { ...row, productId: '', productQuery: '' } : row
    )));
    setDeliveryError('');
    setDeliveryMessage('');
    setProductError('');
  };

  const handleDeliveryAddRow = () => {
    setDeliveryRows((rows) => [...rows, makeScheduleDeliveryEditRow(undefined, rows.length)]);
    setDeliveryError('');
    setDeliveryMessage('');
  };

  const handleDeliveryRemoveRow = (rowId: string) => {
    setDeliveryRows((rows) => {
      const nextRows = rows.filter((row) => row.rowId !== rowId);
      return nextRows.length > 0 ? nextRows : [makeScheduleDeliveryEditRow(undefined, 0)];
    });
    setDeliveryError('');
    setDeliveryMessage('');
  };

  const handleDeliverySubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!currentSchedule || deliverySaving) {
      return;
    }
    if (!currentSchedule.canEdit || !data?.links.updateDeliveryItems) {
      setDeliveryError('납품 품목 수정 권한이 없습니다.');
      setDeliveryMessage('');
      return;
    }

    const rowsWithInput = deliveryRows.filter((row) => (
      row.productId
      || row.itemName.trim()
      || row.quantity.trim()
      || row.unitPrice.trim()
      || row.discountRate.trim()
      || row.discountUnitPrice.trim()
      || row.quoteGroup.trim()
      || row.notes.trim()
      || row.optionDescription.trim()
    ));
    if (!rowsWithInput.length) {
      setDeliveryError('품목명과 수량이 있는 납품 품목을 하나 이상 입력하세요.');
      return;
    }

    const payloadItems: ScheduleDeliveryItemPayload[] = [];
    for (const [index, row] of rowsWithInput.entries()) {
      const itemName = row.itemName.trim();
      if (!itemName) {
        setDeliveryError(`${index + 1}번째 품목명을 입력하세요.`);
        return;
      }
      const quantity = Number(row.quantity);
      if (!Number.isInteger(quantity) || quantity <= 0) {
        setDeliveryError(`${index + 1}번째 수량은 1 이상의 숫자로 입력하세요.`);
        return;
      }
      const unitPrice = row.unitPrice.trim();
      if (unitPrice && Number.isNaN(Number(unitPrice))) {
        setDeliveryError(`${index + 1}번째 단가는 숫자로 입력하세요.`);
        return;
      }
      if (unitPrice && Number(unitPrice) < 0) {
        setDeliveryError(`${index + 1}번째 단가는 0 이상이어야 합니다.`);
        return;
      }
      const discountRate = row.discountRate.trim();
      if (discountRate && Number.isNaN(Number(discountRate))) {
        setDeliveryError(`${index + 1}번째 할인율은 숫자로 입력하세요.`);
        return;
      }
      if (discountRate && (Number(discountRate) < 0 || Number(discountRate) > 100)) {
        setDeliveryError(`${index + 1}번째 할인율은 0부터 100 사이여야 합니다.`);
        return;
      }
      const discountUnitPrice = row.discountUnitPrice.trim();
      if (discountUnitPrice && Number.isNaN(Number(discountUnitPrice))) {
        setDeliveryError(`${index + 1}번째 할인단가는 숫자로 입력하세요.`);
        return;
      }
      if (discountUnitPrice && Number(discountUnitPrice) < 0) {
        setDeliveryError(`${index + 1}번째 할인단가는 0 이상이어야 합니다.`);
        return;
      }
      if (unitPrice && discountUnitPrice && Number(discountUnitPrice) > Number(unitPrice)) {
        setDeliveryError(`${index + 1}번째 할인단가는 기준단가보다 클 수 없습니다.`);
        return;
      }
      payloadItems.push({
        id: row.id,
        productId: row.productId ? Number(row.productId) : null,
        itemName,
        quantity,
        unit: row.unit.trim() || 'EA',
        unitPrice: unitPrice || null,
        discountRate: discountRate || null,
        discountUnitPrice: discountUnitPrice || null,
        quoteGroup: row.quoteGroup.trim(),
        notes: row.notes.trim(),
        optionDescription: row.optionDescription.trim(),
        sourceQuoteScheduleId: row.sourceQuoteScheduleId ? Number(row.sourceQuoteScheduleId) : null,
        sourceQuoteItemId: row.sourceQuoteItemId ? Number(row.sourceQuoteItemId) : null,
      });
    }
    const sourceQuoteScheduleIds = Array.from(new Set(
      rowsWithInput
        .map((row) => Number(row.sourceQuoteScheduleId))
        .filter((sourceId) => Number.isInteger(sourceId) && sourceId > 0),
    ));
    const checkedQuoteScheduleIds = Array.from(new Set(
      (quoteImportData?.quotes ?? [])
        .filter((quote) => selectedQuoteImportIds.includes(quote.optionId))
        .map((quote) => Number(quote.scheduleId))
        .filter((sourceId) => Number.isInteger(sourceId) && sourceId > 0),
    ));
    const quoteGroupNotesPayload = scheduleQuoteGroupsFromRows(rowsWithInput).reduce<ScheduleQuoteGroupNoteState>((acc, group) => {
      acc[group] = (quoteGroupNotes[group] || '').trim();
      return acc;
    }, {});
    const deliveryPrepaymentSelections = deliveryPrepaymentRows.filter((row) => row.selected);
    const useDeliveryPrepayment = currentSchedule.activityType === 'delivery' && deliveryUsePrepayment;
    if (useDeliveryPrepayment) {
      if (deliveryPrepaymentBaseAmount <= 0) {
        setDeliveryError('선결제를 차감하려면 먼저 견적 품목을 불러오거나 납품 품목 금액을 입력하세요.');
        return;
      }
      if (deliveryPrepaymentsLoading) {
        setDeliveryError('선결제 목록을 불러오는 중입니다.');
        return;
      }
      if (deliveryPrepaymentsError) {
        setDeliveryError(deliveryPrepaymentsError);
        return;
      }
      if (!deliveryPrepaymentSelections.length) {
        setDeliveryError('차감할 선결제를 선택하세요.');
        return;
      }
      for (const [index, row] of deliveryPrepaymentSelections.entries()) {
        const amount = Number(row.amountInput);
        if (!Number.isFinite(amount) || amount <= 0) {
          setDeliveryError(`${index + 1}번째 선결제 차감 금액을 입력하세요.`);
          return;
        }
        if (amount > row.availableBalance) {
          setDeliveryError(`${row.payerName} 선결제 잔액이 부족합니다.`);
          return;
        }
        const otherSelectedAmount = deliveryPrepaymentSelections.reduce((total, otherRow) => {
          if (otherRow.id === row.id) {
            return total;
          }
          const otherAmount = Number(otherRow.amountInput);
          return Number.isFinite(otherAmount) && otherAmount > 0 ? total + otherAmount : total;
        }, 0);
        const rowMaxAmount = Math.min(
          row.availableBalance,
          Math.max(deliveryPrepaymentBaseAmount - otherSelectedAmount, 0),
        );
        if (amount > rowMaxAmount) {
          setDeliveryError(`${row.payerName} 차감 금액은 ${formatWon(rowMaxAmount)}까지 입력할 수 있습니다.`);
          return;
        }
      }
    }
    const prepaymentOptions = currentSchedule.activityType === 'delivery'
      ? {
        usePrepayment: useDeliveryPrepayment,
        prepayments: useDeliveryPrepayment
          ? deliveryPrepaymentSelections.map<SchedulePrepaymentSelectionPayload>((row) => ({ id: row.id, amount: row.amountInput.trim() }))
          : [],
        checkedQuoteScheduleIds,
      }
      : checkedQuoteScheduleIds.length
        ? { checkedQuoteScheduleIds }
        : undefined;

    setDeliverySaving(true);
    setDeliveryError('');
    setDeliveryMessage('');
    try {
      const updated = await updateScheduleDeliveryItems(
        data.links.updateDeliveryItems,
        payloadItems,
        quoteGroupNotesPayload,
        sourceQuoteScheduleIds,
        prepaymentOptions,
      );
      const refreshed = await onRefresh();
      setDeliveryRows(makeScheduleDeliveryEditRows(refreshed?.deliveryItems ?? updated.deliveryItems ?? []));
      setQuoteGroupNotes(makeScheduleQuoteGroupNotes(refreshed?.schedule ?? updated.schedule ?? null));
      setDeliveryMessage(updated.message || '납품 품목을 저장했습니다.');
      setDeliveryEditOpen(false);
    } catch (error) {
      setDeliveryError(error instanceof Error ? error.message : '납품 품목 저장에 실패했습니다.');
    } finally {
      setDeliverySaving(false);
    }
  };

  const handleDocumentPreview = async (action: ScheduleDocumentAction, options?: ScheduleDocumentRequestOptions) => {
    if (documentPreviewLoading) {
      return;
    }
    setDocumentPreviewAction(action);
    setDocumentPreviewData(null);
    setDocumentPreviewLoading(true);
    setDocumentPreviewError('');
    try {
      const preview = await loadScheduleDocumentPreview(action.previewHref, options);
      setDocumentPreviewData(preview);
    } catch (error) {
      setDocumentPreviewError(error instanceof Error ? error.message : '서류 변수 미리보기에 실패했습니다.');
    } finally {
      setDocumentPreviewLoading(false);
    }
  };

  const handleDocumentDownload = async (
    action: ScheduleDocumentAction,
    formatAction: ScheduleDocumentFormatAction,
    options?: ScheduleDocumentRequestOptions,
  ) => {
    if (documentDownloadingKey) {
      return;
    }
    const actionKey = scheduleDocumentDownloadKey(action, formatAction, options);
    setDocumentDownloadingKey(actionKey);
    setDocumentPreviewError('');
    try {
      const result = await downloadScheduleDocument(formatAction.href, options);
      saveDownloadedBlob(result.blob, result.filename);
    } catch (error) {
      setDocumentPreviewError(error instanceof Error ? error.message : `${action.label} 다운로드에 실패했습니다.`);
    } finally {
      setDocumentDownloadingKey('');
    }
  };

  const handleGeneratedDocumentDelete = async (document: ScheduleGeneratedDocument) => {
    if (documentDeletingKey) {
      return;
    }
    if (!currentSchedule?.canEdit || !document.canDelete || !document.deleteHref) {
      setDocumentPreviewError('등록 서류 삭제 권한이 없습니다.');
      return;
    }
    const filename = document.filename || document.transactionNumber || document.documentTypeLabel;
    if (!window.confirm(`"${filename}" 등록 서류를 삭제할까요?`)) {
      return;
    }

    setDocumentDeletingKey(String(document.id));
    setDocumentPreviewError('');
    try {
      await deleteGeneratedDocument(document.deleteHref);
      await onRefresh();
    } catch (error) {
      setDocumentPreviewError(error instanceof Error ? error.message : '등록 서류 삭제에 실패했습니다.');
    } finally {
      setDocumentDeletingKey('');
    }
  };

  const handleScheduleDelete = async () => {
    if (scheduleDeleting) {
      return;
    }
    if (!currentSchedule?.canEdit || !data?.links.deleteSchedule) {
      setScheduleDeleteError('일정 삭제 권한이 없습니다.');
      return;
    }
    const confirmMessage = [
      '이 일정을 삭제할까요?',
      '',
      `고객: ${currentSchedule.customer || '고객명 미정'}`,
      `날짜: ${currentSchedule.date ? formatDateLabel(currentSchedule.date) : '날짜 없음'}`,
      '',
      '관련 활동 기록도 함께 삭제되며 복구할 수 없습니다.',
    ].join('\n');
    if (!window.confirm(confirmMessage)) {
      return;
    }

    setScheduleDeleting(true);
    setScheduleDeleteError('');
    try {
      await deleteSchedule(data.links.deleteSchedule);
      window.location.assign(data.links.schedules || '/schedules/');
    } catch (error) {
      setScheduleDeleteError(error instanceof Error ? error.message : '일정 삭제에 실패했습니다.');
    } finally {
      setScheduleDeleting(false);
    }
  };

  const handleDocumentPreviewClose = () => {
    setDocumentPreviewAction(null);
    setDocumentPreviewData(null);
    setDocumentPreviewLoading(false);
    setDocumentPreviewError('');
  };

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>일정 상세 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data || !data.schedule) {
    return (
      <section className="schedules-page">
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>일정 상세를 불러오지 못했습니다</strong>
            <span>{data?.error || '일정 상세 정보를 불러오지 못했습니다.'}</span>
          </div>
          <a href="/schedules/">목록</a>
        </div>
      </section>
    );
  }

  const schedule = data.schedule;
  const deliveryItems = data.deliveryItems;
  const isQuoteSchedule = schedule.activityType === 'quote';
  const itemPanelLabel = isQuoteSchedule ? '견적 품목' : '납품 품목';
  const taxInvoice = data.taxInvoice;
  const editableQuoteGroups = scheduleQuoteGroupsFromRows(deliveryRows);
  const savedQuoteGroupNotes = schedule.quoteGroupNotes?.filter((item) => item.notes.trim()) ?? [];
  const prepaymentUsages = schedule.prepaymentUsages ?? [];
  const deliveryTotalAmount = deliveryItems.reduce((total, item) => total + (item.totalPrice || 0), 0);
  const prepaymentBaseAmount = deliveryTotalAmount > 0 ? deliveryTotalAmount : schedule.expectedRevenue;
  const selectedPrepaymentAmount = prepaymentRows.reduce((total, row) => {
    const amount = Number(row.amountInput);
    return row.selected && Number.isFinite(amount) && amount > 0 ? total + amount : total;
  }, 0);
  const payableAfterPrepayment = Math.max(prepaymentBaseAmount - selectedPrepaymentAmount, 0);
  const deliveryEditTotalAmount = scheduleDeliveryEditRowsTotal(deliveryRows, schedule.vatMode);
  const deliveryPrepaymentBaseAmount = deliveryEditOpen
    ? deliveryEditTotalAmount
    : prepaymentBaseAmount;
  const deliveryPrepaymentNeedsItems = deliveryUsePrepayment && deliveryPrepaymentBaseAmount <= 0;
  const selectedDeliveryPrepaymentAmount = deliveryPrepaymentRows.reduce((total, row) => {
    const amount = Number(row.amountInput);
    return !deliveryPrepaymentNeedsItems && row.selected && Number.isFinite(amount) && amount > 0 ? total + amount : total;
  }, 0);
  const deliveryPayableAfterPrepayment = Math.max(deliveryPrepaymentBaseAmount - selectedDeliveryPrepaymentAmount, 0);
  const deleteRequested = new URLSearchParams(window.location.search).get('delete') === '1';
  const metrics = [
    { label: '일정 상태', value: schedule.statusLabel, detail: schedule.activityLabel, icon: CalendarDays, tone: schedule.overdue ? 'red' as const : 'blue' as const },
    { label: '방문 일시', value: schedule.date ? formatDateLabel(schedule.date) : '날짜 없음', detail: schedule.time || '시간 없음', icon: Clock, tone: 'green' as const },
    { label: '예상 매출', value: schedule.expectedRevenue > 0 ? formatWon(schedule.expectedRevenue) : '없음', detail: schedule.probability === null || schedule.probability === undefined ? '확률 미입력' : `${schedule.probability}%`, icon: CircleDollarSign, tone: 'amber' as const },
    { label: '보고/파일', value: `${formatNumber(schedule.historyCount)} / ${formatNumber(schedule.fileCount)}`, detail: '보고 / 첨부', icon: MessageSquareText, tone: 'teal' as const },
  ];
  const scheduleNoteActionOptions = schedule.activityType === 'service'
    ? scheduleNoteActionTypeOptions
    : scheduleNoteActionTypeOptions.filter((option) => option.value !== 'service');

  return (
    <section className="schedules-page schedule-detail-page">
      {data.source !== 'django' ? (
        <DashboardApiAlert message={data.error} title="일정 상세 정보를 불러오지 못했습니다" />
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Schedule detail</span>
          <h2>{schedule.company || schedule.customer || schedule.activityLabel}</h2>
          <p>{[schedule.customer, schedule.department, schedule.activityLabel, schedule.owner].filter(Boolean).join(' · ')}</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href="/schedules/">목록</a>
          {data.links.customer ? <a className="route-secondary-action" href={data.links.customer}>고객</a> : null}
          {schedule.canEdit ? (
            <button className="route-secondary-action" onClick={handleScheduleNoteToggle} type="button">
              {scheduleNoteOpen ? '작성 닫기' : '영업노트 작성'}
              <FileText size={16} />
            </button>
          ) : null}
          {data.edit.canEdit ? (
            <button className="route-primary-action" onClick={() => setEditOpen((open) => !open)} type="button">
              수정
              <Check size={16} />
            </button>
          ) : null}
          {schedule.canEdit && data.links.deleteSchedule ? (
            <button
              className="route-secondary-action danger schedule-delete-action"
              disabled={scheduleDeleting}
              onClick={handleScheduleDelete}
              type="button"
            >
              {scheduleDeleting ? <Loader2 className="spin-icon" size={16} /> : <Trash2 size={16} />}
              삭제
            </button>
          ) : null}
        </div>
      </div>

      {scheduleDeleteError ? (
        <div className="dashboard-api-alert compact">
          <AlertTriangle size={16} />
          <span>{scheduleDeleteError}</span>
        </div>
      ) : null}
      {deleteRequested && schedule.canEdit ? (
        <div className="dashboard-api-alert compact">
          <AlertTriangle size={16} />
          <span>삭제 요청으로 들어왔습니다. 상단의 삭제 버튼으로 확정하세요.</span>
        </div>
      ) : null}

      <section className="dashboard-metric-grid" aria-label="일정 상세 지표">
        {metrics.map((metric) => (
          <DashboardMetricCard
            detail={metric.detail}
            icon={metric.icon}
            key={metric.label}
            label={metric.label}
            tone={metric.tone}
            value={metric.value}
          />
        ))}
      </section>

      {data.relatedNotes.length > 0 ? (
        <section className="dashboard-panel note-related-panel schedule-linked-notes-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Linked notes</span>
              <h2>연결된 영업노트</h2>
            </div>
            <MessageSquareText size={18} />
          </div>
          <CustomerDetailNoteList emptyLabel="이 일정에 연결된 영업노트가 없습니다" notes={data.relatedNotes} />
        </section>
      ) : null}

      {scheduleNoteOpen || scheduleNoteMessage || scheduleNoteError ? (
        <section className="dashboard-panel notes-create-panel schedule-note-create-panel" ref={scheduleNotePanelRef}>
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Sales note</span>
              <h2>일정 영업노트 작성</h2>
            </div>
            {scheduleNoteSaving ? <Loader2 className="spin-icon" size={18} /> : <FileText size={18} />}
          </div>
          {scheduleNoteError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{scheduleNoteError}</span></div> : null}
          {scheduleNoteMessage ? (
            <div className="dashboard-api-alert compact success">
              <CheckCircle2 size={16} />
              <span>{scheduleNoteMessage}</span>
              {scheduleNoteHref ? <a href={scheduleNoteHref}>노트 보기</a> : null}
            </div>
          ) : null}
          {scheduleNoteOpen ? (
            <form className="notes-create-form schedule-note-create-form" onSubmit={handleScheduleNoteSubmit}>
              <div className="notes-create-grid">
                <label>
                  <span>고객</span>
                  <input
                    readOnly
                    value={[schedule.company, schedule.department, schedule.customer].filter(Boolean).join(' · ') || '고객 없음'}
                  />
                </label>
                <label>
                  <span>활동 유형</span>
                  <select
                    onChange={(event) => handleScheduleNoteFieldChange('actionType', event.target.value)}
                    required
                    value={scheduleNoteForm.actionType}
                  >
                    {scheduleNoteActionOptions.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>활동일</span>
                  <input
                    onChange={(event) => handleScheduleNoteFieldChange('activityDate', event.target.value)}
                    type="date"
                    value={scheduleNoteForm.activityDate}
                  />
                </label>
                <label>
                  <span>다음 예정일</span>
                  <input
                    onChange={(event) => handleScheduleNoteFieldChange('nextActionDate', event.target.value)}
                    type="date"
                    value={scheduleNoteForm.nextActionDate}
                  />
                </label>
              </div>
              <label>
                <span>활동 내용</span>
                <textarea
                  onChange={(event) => handleScheduleNoteFieldChange('content', event.target.value)}
                  required
                  rows={4}
                  value={scheduleNoteForm.content}
                />
              </label>
              <label>
                <span>다음 액션</span>
                <textarea
                  onChange={(event) => handleScheduleNoteFieldChange('nextAction', event.target.value)}
                  rows={2}
                  value={scheduleNoteForm.nextAction}
                />
              </label>
              <div className="notes-create-actions">
                {data.links.djangoCreateNote ? (
                  <a className="route-secondary-action" href={data.links.djangoCreateNote}>
                    노트 페이지
                    <MoveUpRight size={15} />
                  </a>
                ) : null}
                <button className="route-primary-action" disabled={scheduleNoteSaving} type="submit">
                  {scheduleNoteSaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                  저장
                </button>
              </div>
            </form>
          ) : null}
        </section>
      ) : null}

      {editOpen || editMessage || editError ? (
        <section className="dashboard-panel notes-create-panel schedule-edit-panel" ref={scheduleEditPanelRef}>
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Edit schedule</span>
              <h2>일정 수정</h2>
            </div>
            {editSaving ? <Loader2 className="spin-icon" size={18} /> : <CalendarDays size={18} />}
          </div>
          {editError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{editError}</span></div> : null}
          {editMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{editMessage}</span></div> : null}
          {editOpen ? (
            <form className="notes-create-form schedule-edit-form" onSubmit={handleEditSubmit}>
              <div className="notes-create-grid schedules-create-grid">
                <div className="form-field">
                  <span>고객</span>
                  <SearchableSelect
                    ariaLabel="고객 선택"
                    onChange={(nextValue) => handleEditFieldChange('followupId', nextValue)}
                    options={data.edit.customers.map(makeCustomerSelectOption)}
                    placeholder="고객, 회사, 부서 검색"
                    value={editForm.followupId}
                  />
                </div>
                <label>
                  <span>일정 유형</span>
                  <select
                    onChange={(event) => handleEditFieldChange('activityType', event.target.value)}
                    required
                    value={editForm.activityType}
                  >
                    {data.edit.activityTypes.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>상태</span>
                  <select
                    onChange={(event) => handleEditFieldChange('status', event.target.value)}
                    required
                    value={editForm.status}
                  >
                    {data.edit.statuses.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>일정 날짜</span>
                  <input
                    onChange={(event) => handleEditFieldChange('visitDate', event.target.value)}
                    required
                    type="date"
                    value={editForm.visitDate}
                  />
                </label>
                <label>
                  <span>일정 시간</span>
                  <input
                    onChange={(event) => handleEditFieldChange('visitTime', event.target.value)}
                    required
                    type="time"
                    value={editForm.visitTime}
                  />
                </label>
                <label>
                  <span>장소</span>
                  <input
                    onChange={(event) => handleEditFieldChange('location', event.target.value)}
                    value={editForm.location}
                  />
                </label>
                <label>
                  <span>예상 매출</span>
                  <input
                    inputMode="numeric"
                    min="0"
                    onChange={(event) => handleEditFieldChange('expectedRevenue', event.target.value)}
                    type="number"
                    value={editForm.expectedRevenue}
                  />
                </label>
                <VatModeField onChange={(value) => handleEditFieldChange('vatMode', value)} value={editForm.vatMode} />
                <label>
                  <span>성공 확률</span>
                  <input
                    inputMode="numeric"
                    max="100"
                    min="0"
                    step="5"
                    required={isQuoteProbabilityRequired(editForm.activityType)}
                    onBlur={(event) => handleEditFieldChange('probability', normalizeProbabilityInputValue(event.target.value))}
                    onChange={(event) => handleEditFieldChange('probability', event.target.value)}
                    type="number"
                    value={editForm.probability}
                  />
                </label>
                <label>
                  <span>예상 종료일</span>
                  <input
                    onChange={(event) => handleEditFieldChange('expectedCloseDate', event.target.value)}
                    type="date"
                    value={editForm.expectedCloseDate}
                  />
                </label>
              </div>
              <label className="schedule-edit-inline-check">
                <input
                  checked={editForm.purchaseConfirmed}
                  onChange={(event) => handleEditFieldChange('purchaseConfirmed', event.target.checked)}
                  type="checkbox"
                />
                <span>구매 확정</span>
              </label>
              {editForm.activityType === 'delivery' ? (
                <div className="schedule-prepayment-editor">
                  <label className="schedule-edit-inline-check">
                    <input
                      checked={editForm.usePrepayment}
                      onChange={(event) => handleEditFieldChange('usePrepayment', event.target.checked)}
                      type="checkbox"
                    />
                    <span>선결제 사용</span>
                  </label>
                  {editForm.usePrepayment ? (
                    <div className="schedule-prepayment-body">
                      {prepaymentsError ? (
                        <div className="dashboard-api-alert compact">
                          <AlertTriangle size={16} />
                          <span>{prepaymentsError}</span>
                        </div>
                      ) : null}
                      {prepaymentsLoading ? (
                        <div className="schedule-prepayment-loading">
                          <Loader2 className="spin-icon" size={15} />
                          <span>선결제 조회 중</span>
                        </div>
                      ) : prepaymentRows.length > 0 ? (
                        <div className="schedule-prepayment-list">
                          {prepaymentRows.map((row) => (
                            <div className={row.selected ? 'schedule-prepayment-row selected' : 'schedule-prepayment-row'} key={row.id}>
                              <label className="schedule-prepayment-check">
                                <input
                                  checked={row.selected}
                                  onChange={(event) => handlePrepaymentRowToggle(row.id, event.target.checked)}
                                  type="checkbox"
                                />
                                <span>
                                  <strong>{[row.paymentDate ? formatDateLabel(row.paymentDate) : '입금일 없음', row.payerName].filter(Boolean).join(' · ')}</strong>
                                  <small>{[row.customerName, `잔액 ${formatWon(row.balance)}`, `사용 가능 ${formatWon(row.availableBalance)}`].filter(Boolean).join(' · ')}</small>
                                </span>
                              </label>
                              <label className="schedule-prepayment-amount">
                                <span>차감</span>
                                <input
                                  disabled={!row.selected}
                                  inputMode="numeric"
                                  min="0"
                                  onChange={(event) => handlePrepaymentAmountChange(row.id, event.target.value)}
                                  type="number"
                                  value={row.amountInput}
                                />
                              </label>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <DashboardEmpty label="사용 가능한 선결제가 없습니다" />
                      )}
                      <div className="schedule-prepayment-totals">
                        <span>납품 합계 <strong>{formatWon(prepaymentBaseAmount)}</strong> <small>{vatModeLabel(schedule.vatMode)} 기준</small></span>
                        <span>차감 <strong>{formatWon(selectedPrepaymentAmount)}</strong></span>
                        <span>실결제 <strong>{formatWon(payableAfterPrepayment)}</strong></span>
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
              <label>
                <span>일정 내용</span>
                <textarea
                  onChange={(event) => handleEditFieldChange('notes', event.target.value)}
                  rows={4}
                  value={editForm.notes}
                />
              </label>
              <div className="notes-create-actions">
                <button className="route-primary-action" disabled={editSaving} type="submit">
                  {editSaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                  저장
                </button>
              </div>
            </form>
          ) : null}
        </section>
      ) : null}

      <div className="note-detail-layout schedule-detail-layout">
        <section className="dashboard-panel note-detail-main schedule-detail-main">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Schedule</span>
              <h2>일정 내용</h2>
            </div>
            <ScheduleStatusBadge schedule={schedule} />
          </div>
          <div className="note-detail-content schedule-detail-content">
            {schedule.notesFull || schedule.notes ? <p>{schedule.notesFull || schedule.notes}</p> : <DashboardEmpty label="일정 내용이 없습니다" />}
          </div>
          <div className="note-detail-field-grid">
            <div className="note-detail-field">
              <span>장소</span>
              <p>{schedule.location || '장소 없음'}</p>
            </div>
            <div className="note-detail-field">
              <span>예상 종료일</span>
              <p>{schedule.expectedCloseDate ? formatDateLabel(schedule.expectedCloseDate) : '없음'}</p>
            </div>
            <div className="note-detail-field">
              <span>구매 확정</span>
              <p>{schedule.purchaseConfirmed ? '확정' : '미확정'}</p>
            </div>
            <div className="note-detail-field">
              <span>이메일 스레드</span>
              <p>{formatNumber(schedule.emailThreadCount)}건</p>
            </div>
          </div>
        </section>

        <aside className="dashboard-panel note-detail-side schedule-detail-side">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Related</span>
              <h2>연결 정보</h2>
            </div>
            <PanelRight size={18} />
          </div>
          <div className="customer-detail-summary">
            <dl>
              <div>
                <dt>고객</dt>
                <dd>{[schedule.company, schedule.department, schedule.customer].filter(Boolean).join(' · ') || '고객 없음'}</dd>
              </div>
              <div>
                <dt>담당자</dt>
                <dd>{schedule.owner}</dd>
              </div>
              <div>
                <dt>일정일</dt>
                <dd className={schedule.overdue ? 'customer-overdue-text' : ''}>
                  {[schedule.date ? formatDateLabel(schedule.date) : '', schedule.time].filter(Boolean).join(' ') || '일정 없음'}
                </dd>
              </div>
              <div>
                <dt>선결제</dt>
                <dd>{schedule.usePrepayment ? formatWon(schedule.prepaymentAmount) : '미사용'}</dd>
              </div>
            </dl>
            {prepaymentUsages.length > 0 ? (
              <div className="schedule-prepayment-usage-list">
                {prepaymentUsages.map((usage) => (
                  <div key={usage.id}>
                    <span>{[usage.paymentDate ? formatDateLabel(usage.paymentDate) : '', usage.payerName].filter(Boolean).join(' · ') || '선결제'}</span>
                    <strong>{formatWon(usage.amount)}</strong>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
          <div className="customers-side-actions note-detail-actions">
            {data.links.customer ? <a href={data.links.customer}>고객 상세</a> : null}
            {data.links.createNote ? <a href={data.links.createNote}>보고 작성</a> : null}
            <a href={data.links.calendar}>일정 캘린더</a>
          </div>
          <ScheduleAICoachPanel
            canUseAi={data.ai.canUseAi}
            error={scheduleCoachError}
            loading={scheduleCoachLoading}
            message={scheduleCoachMessage}
            permissionMessage={data.ai.message}
            onGenerate={handleScheduleCoachRun}
            result={scheduleCoachResult}
          />
          <ScheduleCommercialChecksPanel checks={data.commercialChecks} />
          <ScheduleDocumentsPanel
            documents={data.documents}
            deletingDocumentKey={documentDeletingKey}
            downloadingKey={documentDownloadingKey}
            onClosePreview={handleDocumentPreviewClose}
            onDelete={handleGeneratedDocumentDelete}
            onDownload={handleDocumentDownload}
            onPreview={handleDocumentPreview}
            previewAction={documentPreviewAction}
            previewData={documentPreviewData}
            previewError={documentPreviewError}
            previewLoading={documentPreviewLoading}
          />
          <div className="schedule-file-heading schedule-delivery-heading">
            <h3 className="customer-detail-section-heading">{itemPanelLabel}</h3>
            {schedule.canEdit && data.links.updateDeliveryItems ? (
              <div className="schedule-heading-actions">
                {!isQuoteSchedule ? (
                  <button
                    className="customer-row-action schedule-delivery-edit-toggle"
                    disabled={deliverySaving || quoteImportLoading}
                    onClick={handleQuoteImportToggle}
                    type="button"
                  >
                    {quoteImportLoading ? <Loader2 className="spin-icon" size={14} /> : <Copy size={14} />}
                    <span>{quoteImportOpen ? '불러오기 닫기' : '견적 불러오기'}</span>
                  </button>
                ) : null}
                <button
                  className="customer-row-action schedule-delivery-edit-toggle"
                  disabled={deliverySaving}
                  onClick={handleDeliveryEditToggle}
                  type="button"
                >
                  {deliveryEditOpen ? <ChevronDown size={14} /> : <ListChecks size={14} />}
                  <span>{deliveryEditOpen ? '닫기' : '편집'}</span>
                </button>
              </div>
            ) : null}
          </div>
          {deliveryError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{deliveryError}</span></div> : null}
          {deliveryMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{deliveryMessage}</span></div> : null}
          {!isQuoteSchedule && taxInvoice.applies ? (
            <div className={`schedule-tax-invoice-panel ${taxInvoice.status}`}>
              <div>
                <FileText size={15} />
                <span>
                  <strong>외상 {taxInvoice.statusLabel}</strong>
                  <small>{[
                    taxInvoice.message,
                    taxInvoice.totalCount ? `총 ${formatNumber(taxInvoice.totalCount)}개 품목` : '',
                  ].filter(Boolean).join(' · ')}</small>
                </span>
              </div>
              <a className="customer-row-action schedule-tax-invoice-toggle" href="/receivables/">
                <CircleDollarSign size={14} />
                <span>외상고객</span>
              </a>
            </div>
          ) : null}
          {!isQuoteSchedule && quoteImportOpen ? (
            <div className="schedule-quote-import-panel" ref={quoteImportPanelRef}>
              <div className="schedule-quote-import-heading">
                <div>
                  <strong>견적 품목 불러오기</strong>
                  <span>같은 부서의 본인 견적 일정에서 하나 이상 선택해 한 번에 가져옵니다.</span>
                </div>
                <div className="schedule-quote-import-actions">
                  <span>{selectedQuoteImportIds.length ? `${formatNumber(selectedQuoteImportIds.length)}개 선택` : '선택 대기'}</span>
                  <button
                    className="route-secondary-action"
                    disabled={deliverySaving || quoteImportLoading || selectedQuoteImportIds.length === 0}
                    onClick={handleSelectedQuoteImportApply}
                    type="button"
                  >
                    선택 적용
                  </button>
                  <button
                    className="customer-row-action schedule-delivery-edit-toggle"
                    disabled={quoteImportLoading}
                    onClick={() => void loadQuoteImports()}
                    type="button"
                  >
                    {quoteImportLoading ? <Loader2 className="spin-icon" size={14} /> : <RefreshCw size={14} />}
                    <span>새로고침</span>
                  </button>
                </div>
              </div>
              {quoteImportError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{quoteImportError}</span></div> : null}
              {quoteImportLoading ? (
                <div className="schedule-quote-import-loading">
                  <Loader2 className="spin-icon" size={16} />
                  <span>견적을 불러오는 중입니다</span>
                </div>
              ) : quoteImportData?.quotes.length ? (
                <div className="schedule-quote-import-list">
                  {quoteImportData.quotes.map((quote) => {
                    const selected = selectedQuoteImportIds.includes(quote.optionId);
                    return (
                      <div className={selected ? 'schedule-quote-import-card selected' : 'schedule-quote-import-card'} key={quote.optionId}>
                        <label className="schedule-quote-import-select">
                          <input
                            checked={selected}
                            disabled={deliverySaving}
                            onChange={(event) => handleQuoteImportSelectionChange(quote.optionId, event.target.checked)}
                            type="checkbox"
                          />
                          <span className="schedule-quote-import-main">
                            <strong>{quoteImportOptionTitle(quote)}</strong>
                            <span>{[
                              quote.customerName || '고객명 미정',
                              quote.companyName,
                              quote.departmentName,
                              quote.quoteDate ? formatDateLabel(quote.quoteDate) : '',
                              `일정 #${quote.scheduleId}`,
                              `남은 품목 ${formatNumber(quote.items.length)}개`,
                              quote.remainingAmount ? `잔여 ${formatWon(quote.remainingAmount)}` : '',
                            ].filter(Boolean).join(' · ')}</span>
                            <span className="schedule-quote-import-badges">
                              <span className={quote.hasPartialDelivery ? 'partial' : 'pending'}>
                                {quote.deliveryStatusLabel}
                              </span>
                              {quote.deliveredAmount > 0 ? <span>납품 반영 {formatWon(quote.deliveredAmount)}</span> : null}
                              {quote.quotedAmount > 0 ? <span>원 견적 {formatWon(quote.quotedAmount)}</span> : null}
                            </span>
                            <p>{quote.items.map(quoteImportItemSummary).slice(0, 6).join(', ')}</p>
                          </span>
                        </label>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <DashboardEmpty label="불러올 수 있는 견적이 없습니다" />
              )}
            </div>
          ) : null}
          {deliveryEditOpen ? (
            <form className="schedule-delivery-edit-form" onSubmit={handleDeliverySubmit} ref={deliveryEditPanelRef}>
              {productError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{productError}</span></div> : null}
              <div className="schedule-delivery-edit-list">
                {deliveryRows.map((row, index) => {
                  const productMatches = getDeliveryProductMatches(row.productQuery);
                  return (
                    <div className="schedule-delivery-edit-row" key={row.rowId}>
                      <label className="schedule-delivery-product-field">
                        <span>제품 검색</span>
                        <div className="schedule-delivery-product-control">
                          <Search size={14} />
                          <input
                            onChange={(event) => handleDeliveryProductQueryChange(row.rowId, event.target.value)}
                            onFocus={() => void ensureProductsLoaded()}
                            placeholder="품번/설명 검색"
                            value={row.productQuery}
                          />
                          {row.productId ? (
                            <button
                              aria-label={`${index + 1}번째 ${itemPanelLabel} 제품 선택 해제`}
                              className="schedule-delivery-product-clear"
                              disabled={deliverySaving}
                              onClick={() => handleDeliveryProductClear(row.rowId)}
                              type="button"
                            >
                              <X size={13} />
                            </button>
                          ) : null}
                        </div>
                        {row.productId ? <small>제품 마스터 연결됨</small> : null}
                        {row.productQuery.trim() && !row.productId ? (
                          <div className="schedule-delivery-product-results">
                            {productsLoading ? (
                              <span><Loader2 className="spin-icon" size={13} /> 제품 검색 중</span>
                            ) : productMatches.length > 0 ? (
                              productMatches.map((product) => (
                                <button
                                  key={product.id}
                                  onClick={() => handleDeliveryProductSelect(row.rowId, product)}
                                  type="button"
                                >
                                  <strong>{product.productCode}</strong>
                                  <span>{[product.description, product.specification, product.unit, formatWon(product.currentPrice)].filter(Boolean).join(' · ')}</span>
                                </button>
                              ))
                            ) : productsLoaded ? (
                              <span>검색 결과 없음</span>
                            ) : null}
                          </div>
                        ) : null}
                      </label>
                      <label className="schedule-delivery-name-field">
                        <span>품목명</span>
                        <input
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'itemName', event.target.value)}
                          required
                          value={row.itemName}
                        />
                      </label>
                      {isQuoteSchedule ? (
                        <label>
                          <span>견적서 구분</span>
                          <input
                            onChange={(event) => handleDeliveryFieldChange(row.rowId, 'quoteGroup', event.target.value)}
                            placeholder="예: 보상판매, 수리"
                            value={row.quoteGroup}
                          />
                        </label>
                      ) : null}
                      <label>
                        <span>수량</span>
                        <input
                          inputMode="numeric"
                          min="1"
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'quantity', event.target.value)}
                          required
                          type="number"
                          value={row.quantity}
                        />
                      </label>
                      <label>
                        <span>단위</span>
                        <input
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'unit', event.target.value)}
                          value={row.unit}
                        />
                      </label>
                      <label>
                        <span>기준단가</span>
                        <input
                          inputMode="numeric"
                          min="0"
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'unitPrice', event.target.value)}
                          type="number"
                          value={row.unitPrice}
                        />
                      </label>
                      <label>
                        <span>할인율(%)</span>
                        <input
                          inputMode="decimal"
                          max="100"
                          min="0"
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'discountRate', event.target.value)}
                          step="0.01"
                          type="number"
                          value={row.discountRate}
                        />
                      </label>
                      <label>
                        <span>할인단가</span>
                        <input
                          inputMode="numeric"
                          min="0"
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'discountUnitPrice', event.target.value)}
                          type="number"
                          value={row.discountUnitPrice}
                        />
                      </label>
                      <label className="schedule-delivery-notes-field">
                        <span>적요</span>
                        <input
                          onChange={(event) => handleDeliveryFieldChange(row.rowId, 'notes', event.target.value)}
                          value={row.notes}
                        />
                      </label>
                      {isQuoteSchedule ? (
                        <label className="schedule-delivery-notes-field">
                          <span>옵션/설명</span>
                          <textarea
                            onChange={(event) => handleDeliveryFieldChange(row.rowId, 'optionDescription', event.target.value)}
                            placeholder="예: 구성 옵션, 설치 조건, 별도 안내 문구"
                            rows={2}
                            value={row.optionDescription}
                          />
                        </label>
                      ) : null}
                      <button
                        aria-label={`${index + 1}번째 ${itemPanelLabel} 삭제`}
                        className="customer-row-action schedule-delivery-remove-button"
                        disabled={deliveryRows.length <= 1 || deliverySaving}
                        onClick={() => handleDeliveryRemoveRow(row.rowId)}
                        type="button"
                      >
                        <Trash2 size={14} />
                        <span>삭제</span>
                      </button>
                    </div>
                  );
                })}
              </div>
              {isQuoteSchedule ? (
                <div className="schedule-quote-group-notes-grid">
                  {editableQuoteGroups.map((group) => (
                    <label className="schedule-quote-extra-notes-field" key={group || 'default'}>
                      <span>{quoteGroupLabel(group)} 기타사항</span>
                      <textarea
                        onChange={(event) => {
                          setQuoteGroupNotes((previous) => ({
                            ...previous,
                            [group]: event.target.value,
                          }));
                          setDeliveryError('');
                          setDeliveryMessage('');
                        }}
                        rows={3}
                        value={quoteGroupNotes[group] || ''}
                      />
                    </label>
                  ))}
                </div>
              ) : null}
              {!isQuoteSchedule ? (
                <div className="schedule-prepayment-editor schedule-delivery-prepayment-editor">
                  <label className="schedule-edit-inline-check">
                    <input
                      checked={deliveryUsePrepayment}
                      onChange={(event) => handleDeliveryPrepaymentToggle(event.target.checked)}
                      type="checkbox"
                    />
                    <span>납품 저장 시 선결제 차감</span>
                  </label>
                  {deliveryUsePrepayment ? (
                    <div className="schedule-prepayment-body">
                      {deliveryPrepaymentsError ? (
                        <div className="dashboard-api-alert compact">
                          <AlertTriangle size={16} />
                          <span>{deliveryPrepaymentsError}</span>
                        </div>
                      ) : null}
                      {deliveryPrepaymentsLoading ? (
                        <div className="schedule-prepayment-loading">
                          <Loader2 className="spin-icon" size={15} />
                          <span>선결제 조회 중</span>
                        </div>
                      ) : deliveryPrepaymentRows.length > 0 ? (
                        <>
                          {deliveryPrepaymentNeedsItems ? (
                            <div className="dashboard-api-alert compact schedule-prepayment-item-required">
                              <AlertTriangle size={16} />
                              <span>차감할 납품 품목 합계가 없습니다. 먼저 견적 품목을 불러오거나 납품 품목 금액을 입력하세요.</span>
                              {currentSchedule?.canEdit && data?.links.updateDeliveryItems ? (
                                <button
                                  className="customer-row-action"
                                  disabled={quoteImportLoading}
                                  onClick={handleQuoteImportOpenFromPrepayment}
                                  type="button"
                                >
                                  {quoteImportLoading ? <Loader2 className="spin-icon" size={14} /> : <FileText size={14} />}
                                  <span>견적 품목 불러오기</span>
                                </button>
                              ) : null}
                            </div>
                          ) : null}
                          <div className="schedule-prepayment-list">
                            {deliveryPrepaymentRows.map((row) => {
                              const rowAmount = Number(row.amountInput);
                              const safeRowAmount = !deliveryPrepaymentNeedsItems && row.selected && Number.isFinite(rowAmount) && rowAmount > 0 ? rowAmount : 0;
                              const otherSelectedAmount = selectedDeliveryPrepaymentAmount - safeRowAmount;
                              const itemRemainingBeforeRow = Math.max(deliveryPrepaymentBaseAmount - otherSelectedAmount, 0);
                              const rowMaxAmount = deliveryPrepaymentNeedsItems ? 0 : Math.min(row.availableBalance, itemRemainingBeforeRow);
                              const itemRemainingAfterRow = Math.max(itemRemainingBeforeRow - safeRowAmount, 0);
                              const isOverRowMax = row.selected && safeRowAmount > rowMaxAmount;
                              return (
                                <div className={!deliveryPrepaymentNeedsItems && row.selected ? 'schedule-prepayment-row selected' : 'schedule-prepayment-row'} key={row.id}>
                                  <label className="schedule-prepayment-check">
                                    <input
                                      checked={!deliveryPrepaymentNeedsItems && row.selected}
                                      disabled={deliveryPrepaymentNeedsItems}
                                      onChange={(event) => handleDeliveryPrepaymentRowToggle(row.id, event.target.checked)}
                                      type="checkbox"
                                    />
                                    <span>
                                      <strong>{[row.paymentDate ? formatDateLabel(row.paymentDate) : '입금일 없음', row.payerName].filter(Boolean).join(' · ')}</strong>
                                      <small>{[row.customerName, `잔액 ${formatWon(row.balance)}`, `사용 가능 ${formatWon(row.availableBalance)}`].filter(Boolean).join(' · ')}</small>
                                      {!deliveryPrepaymentNeedsItems && row.selected ? (
                                        <small className={isOverRowMax ? 'schedule-prepayment-limit over' : 'schedule-prepayment-limit'}>
                                          품목 상한 {formatWon(itemRemainingBeforeRow)} · 최대 차감 {formatWon(rowMaxAmount)} · 입력 후 남은 납품금액 {formatWon(itemRemainingAfterRow)}
                                        </small>
                                      ) : null}
                                    </span>
                                  </label>
                                  <div className="schedule-prepayment-amount">
                                    <label>
                                      <span>차감</span>
                                      <input
                                        disabled={deliveryPrepaymentNeedsItems || !row.selected}
                                        inputMode="numeric"
                                        max={row.selected ? rowMaxAmount : undefined}
                                        min="0"
                                        onChange={(event) => handleDeliveryPrepaymentAmountChange(row.id, event.target.value)}
                                        type="number"
                                        value={deliveryPrepaymentNeedsItems ? '' : row.amountInput}
                                      />
                                    </label>
                                    <button
                                      className="schedule-prepayment-fill-button"
                                      disabled={deliveryPrepaymentNeedsItems || !row.selected || rowMaxAmount <= 0}
                                      onClick={() => handleDeliveryPrepaymentFillMax(row.id, rowMaxAmount)}
                                      type="button"
                                    >
                                      전체 차감
                                    </button>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </>
                      ) : (
                        <DashboardEmpty label="사용 가능한 선결제가 없습니다" />
                      )}
                      <div className="schedule-prepayment-totals">
                        <span>납품 합계 <strong>{formatWon(deliveryPrepaymentBaseAmount)}</strong> <small>{vatModeLabel(schedule.vatMode)} 기준</small></span>
                        <span>차감 <strong>{formatWon(selectedDeliveryPrepaymentAmount)}</strong></span>
                        <span>실결제 <strong>{formatWon(deliveryPayableAfterPrepayment)}</strong></span>
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
              <div className="notes-create-actions schedule-delivery-edit-actions">
                <button className="route-secondary-action" disabled={deliverySaving} onClick={handleDeliveryAddRow} type="button">
                  <Plus size={15} />
                  {itemPanelLabel} 추가
                </button>
                <button className="route-primary-action" disabled={deliverySaving} type="submit">
                  {deliverySaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                  저장
                </button>
              </div>
            </form>
          ) : deliveryItems.length === 0 ? (
            <DashboardEmpty label={`등록된 ${itemPanelLabel}이 없습니다`} />
          ) : (
            <div className="schedule-delivery-list">
              {deliveryItems.map((item) => (
                <div key={item.id}>
                  <strong>{isQuoteSchedule && item.quoteGroupLabel ? `[${item.quoteGroupLabel}] ${item.itemName}` : item.itemName}</strong>
                  <span>{[
                    `${formatNumber(item.quantity)}${item.unit}`,
                    item.discountUnitPrice !== null ? `할인단가 ${formatWon(item.discountUnitPrice)}` : '',
                    item.totalPrice ? formatWon(item.totalPrice) : '',
                    item.cardPaymentReceived ? '카드결제' : item.receivableSettled ? '수금완료' : '외상 진행중',
                  ].filter(Boolean).join(' · ')}</span>
                  {item.notes ? <p>{isQuoteSchedule ? `적요: ${item.notes}` : item.notes}</p> : null}
                  {isQuoteSchedule && item.optionDescription ? <p>옵션/설명: {item.optionDescription}</p> : null}
                </div>
              ))}
              {isQuoteSchedule && savedQuoteGroupNotes.length > 0 ? (
                <div className="schedule-quote-group-notes-list">
                  {savedQuoteGroupNotes.map((note) => (
                    <div className="schedule-quote-extra-notes" key={note.quoteGroup || 'default'}>
                      <span>{note.quoteGroupLabel || quoteGroupLabel(note.quoteGroup)} 기타사항</span>
                      <p>{note.notes}</p>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          )}
          {fileError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{fileError}</span></div> : null}
          {fileMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{fileMessage}</span></div> : null}
          <AttachmentManager
            canUpload={schedule.canEdit && Boolean(data.links.uploadFiles)}
            deletingId={fileDeletingId}
            emptyLabel="첨부파일이 없습니다"
            files={schedule.files}
            inputRef={fileInputRef}
            title="첨부파일"
            uploadAriaLabel="일정 첨부파일 선택"
            uploading={fileUploading}
            onDelete={handleScheduleFileDelete}
            onFilesSelected={handleScheduleFilesSelected}
            onUploadClick={handleScheduleFileUploadClick}
          />
        </aside>
      </div>

    </section>
  );
}

export function SchedulesPage({
  activityType,
  createError,
  createForm,
  createdDetailHref,
  createMessage,
  createOpen,
  creating,
  data,
  loading,
  owner,
  query,
  range,
  status,
  onActivityTypeChange,
  onCreateFormChange,
  onCreateOpenChange,
  onCreateSubmit,
  onOwnerChange,
  onQueryChange,
  onRangeChange,
  onStatusChange,
}: {
  activityType: string;
  createError: string;
  createForm: ScheduleCreateFormState;
  createdDetailHref: string;
  createMessage: string;
  createOpen: boolean;
  creating: boolean;
  data: SchedulesData | null;
  loading: boolean;
  owner: string;
  query: string;
  range: string;
  status: string;
  onActivityTypeChange: (value: string) => void;
  onCreateFormChange: (field: keyof ScheduleCreateFormState, value: string) => void;
  onCreateOpenChange: (open: boolean) => void;
  onCreateSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onOwnerChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onRangeChange: (value: string) => void;
  onStatusChange: (value: string) => void;
}) {
  const createPanelRef = useRef<HTMLElement | null>(null);
  useGuidedPanelFocus(createOpen, createPanelRef, 'schedule-create');

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>일정 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const metrics = [
    { label: '전체 일정', value: `${formatNumber(data.metrics.totalSchedules)}건`, detail: data.scope.label, icon: CalendarDays, tone: 'blue' as const },
    { label: '오늘 일정', value: `${formatNumber(data.metrics.todaySchedules)}건`, detail: '금일 업무', icon: Clock, tone: 'green' as const },
    { label: '7일 이내', value: `${formatNumber(data.metrics.weekSchedules)}건`, detail: '다가오는 일정', icon: Bell, tone: 'teal' as const },
    { label: '지연 일정', value: `${formatNumber(data.metrics.overdueSchedules)}건`, detail: '예정일 경과', icon: AlertTriangle, tone: 'red' as const },
    { label: '완료 일정', value: `${formatNumber(data.metrics.completedSchedules)}건`, detail: '고객 일정 기준', icon: CheckCircle2, tone: 'amber' as const },
  ];
  const createConfig = data.create;
  const canCreateSchedules = createConfig.canCreate;
  const createCustomers = createConfig.customers;
  const createDepartments = createConfig.departments ?? [];
  const createActivityTypes = createConfig.activityTypes;
  const filteredCreateCustomers = customersForDepartment(createCustomers, createForm.departmentId);
  const selectedDepartmentHasCustomers = filteredCreateCustomers.length > 0;
  const handleCreateDepartmentChange = (nextValue: string) => {
    const nextCustomers = customersForDepartment(createCustomers, nextValue);
    onCreateFormChange('departmentId', nextValue);
    onCreateFormChange('followupId', nextCustomers[0]?.id ? String(nextCustomers[0].id) : '');
  };
  const handleCreateCustomerChange = (nextValue: string) => {
    const nextCustomer = createCustomers.find((customer) => String(customer.id) === nextValue);
    if (nextCustomer?.departmentId) {
      onCreateFormChange('departmentId', String(nextCustomer.departmentId));
    }
    onCreateFormChange('followupId', nextValue);
  };

  return (
    <section className="schedules-page">
      {data.source !== 'django' ? (
        <DashboardApiAlert message={data.error} title="일정 정보를 불러오지 못했습니다" />
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Schedules</span>
          <h2>{data.scope.label || '일정'}</h2>
          <p>고객 일정과 개인 일정을 함께 보고 후속 보고 작성으로 연결합니다.</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href={data.links.createPersonalSchedule}>
            개인 일정
          </a>
          <button
            className={canCreateSchedules ? 'route-primary-action' : 'route-secondary-action'}
            onClick={() => onCreateOpenChange(!createOpen)}
            type="button"
          >
            {canCreateSchedules ? '일정 등록' : '등록 권한 없음'}
            <Plus size={16} />
          </button>
        </div>
      </div>

      {createOpen ? (
        <section className="dashboard-panel notes-create-panel schedules-create-panel" ref={createPanelRef}>
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Quick schedule</span>
              <h2>고객 일정 빠른 등록</h2>
            </div>
            {creating ? <Loader2 className="spin-icon" size={18} /> : <CalendarDays size={18} />}
          </div>
          {createMessage ? (
            <div className="notes-action-feedback success">
              <span>{createMessage}</span>
              {createdDetailHref ? <a href={createdDetailHref}>상세 열기</a> : null}
            </div>
          ) : null}
          {createError ? <div className="notes-action-feedback error">{createError}</div> : null}
          {!canCreateSchedules ? (
            <DashboardEmpty label={createConfig.message || '일정 등록 권한이 없습니다'} />
          ) : createDepartments.length === 0 && createCustomers.length === 0 ? (
            <DashboardEmpty label="등록 가능한 부서/연구실이 없습니다" />
          ) : createActivityTypes.length === 0 ? (
            <DashboardEmpty label="등록 가능한 일정 유형이 없습니다" />
          ) : (
            <form className="notes-create-form" onSubmit={onCreateSubmit}>
              <div className="notes-create-grid schedules-create-grid">
                <div className="form-field">
                  <span>부서/연구실</span>
                  <SearchableSelect
                    ariaLabel="부서/연구실 선택"
                    onChange={handleCreateDepartmentChange}
                    options={createDepartments.map(makeDepartmentSelectOption)}
                    placeholder="회사, 부서/연구실, 담당자 검색"
                    value={createForm.departmentId}
                  />
                </div>
                <div className="form-field">
                  <span>고객</span>
                  <SearchableSelect
                    allowEmpty={!selectedDepartmentHasCustomers}
                    ariaLabel="고객 선택"
                    disabled={!selectedDepartmentHasCustomers}
                    emptyLabel="부서에만 연결"
                    onChange={handleCreateCustomerChange}
                    options={filteredCreateCustomers.map(makeCustomerSelectOption)}
                    placeholder="고객, 회사, 부서 검색"
                    value={createForm.followupId}
                  />
                </div>
                <label>
                  <span>일정 유형</span>
                  <select
                    onChange={(event) => onCreateFormChange('activityType', event.target.value)}
                    required
                    value={createForm.activityType}
                  >
                    {createActivityTypes.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>일정 날짜</span>
                  <input
                    onChange={(event) => onCreateFormChange('visitDate', event.target.value)}
                    required
                    type="date"
                    value={createForm.visitDate}
                  />
                </label>
                <label>
                  <span>일정 시간</span>
                  <input
                    onChange={(event) => onCreateFormChange('visitTime', event.target.value)}
                    required
                    type="time"
                    value={createForm.visitTime}
                  />
                </label>
                <label>
                  <span>장소</span>
                  <input
                    onChange={(event) => onCreateFormChange('location', event.target.value)}
                    placeholder="방문 장소"
                    value={createForm.location}
                  />
                </label>
                <label>
                  <span>예상 매출</span>
                  <input
                    inputMode="numeric"
                    min="0"
                    onChange={(event) => onCreateFormChange('expectedRevenue', event.target.value)}
                    placeholder="원"
                    type="number"
                    value={createForm.expectedRevenue}
                  />
                </label>
                <VatModeField onChange={(value) => onCreateFormChange('vatMode', value)} value={createForm.vatMode} />
                <label>
                  <span>성공 확률</span>
                  <input
                    inputMode="numeric"
                    max="100"
                    min="0"
                    step="5"
                    required={isQuoteProbabilityRequired(createForm.activityType)}
                    onBlur={(event) => onCreateFormChange('probability', normalizeProbabilityInputValue(event.target.value))}
                    onChange={(event) => onCreateFormChange('probability', event.target.value)}
                    placeholder="0-100, 5% 단위"
                    type="number"
                    value={createForm.probability}
                  />
                </label>
              </div>
              <label>
                <span>일정 내용</span>
                <textarea
                  onChange={(event) => onCreateFormChange('notes', event.target.value)}
                  placeholder="일정 내용, 준비사항, 후속 확인 사항"
                  rows={3}
                  value={createForm.notes}
                />
              </label>
              <div className="notes-create-actions">
                <a className="route-secondary-action" href={data.links.createSchedule}>
                  상세 등록
                  <MoveUpRight size={15} />
                </a>
                <button className="route-primary-action" disabled={creating} type="submit">
                  {creating ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                  저장
                </button>
              </div>
            </form>
          )}
        </section>
      ) : null}

      <section className="dashboard-metric-grid" aria-label="일정 핵심 지표">
        {metrics.map((metric) => (
          <DashboardMetricCard
            detail={metric.detail}
            icon={metric.icon}
            key={metric.label}
            label={metric.label}
            tone={metric.tone}
            value={metric.value}
          />
        ))}
      </section>

      <div className="schedules-filter-bar">
        <label className="customers-search">
          <Search size={17} />
          <input
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="고객, 회사, 장소, 일정 내용 검색"
            value={query}
          />
        </label>
        <select onChange={(event) => onOwnerChange(event.target.value)} value={owner}>
          <option value="">담당자 전체</option>
          {data.options.owners.map((option) => (
            <option key={option.id} value={option.id}>{option.name}</option>
          ))}
        </select>
        <select onChange={(event) => onStatusChange(event.target.value)} value={status}>
          <option value="">상태 전체</option>
          {data.options.statuses.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onActivityTypeChange(event.target.value)} value={activityType}>
          <option value="">일정 유형 전체</option>
          {data.options.activityTypes.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onRangeChange(event.target.value)} value={range}>
          <option value="">기간 전체</option>
          {data.options.ranges.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      </div>

      <div className="schedules-layout">
        <section className="dashboard-panel schedules-main-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Schedule list</span>
              <h2>일정 목록</h2>
            </div>
            {loading ? <Loader2 className="spin-icon" size={18} /> : <CalendarDays size={18} />}
          </div>
          <SchedulesTable schedules={data.schedules} />
        </section>

        <aside className="dashboard-panel schedules-side-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Today</span>
              <h2>오늘 일정</h2>
            </div>
            <Clock size={18} />
          </div>
          <SchedulesCompactList emptyLabel="오늘 일정이 없습니다" items={data.today} />
          <div className="dashboard-panel-heading schedules-side-heading">
            <div>
              <span className="eyebrow">Overdue</span>
              <h2>지연 일정</h2>
            </div>
            <AlertTriangle size={18} />
          </div>
          <SchedulesCompactList emptyLabel="지연 일정이 없습니다" items={data.overdue} urgent />
          <div className="dashboard-panel-heading schedules-side-heading">
            <div>
              <span className="eyebrow">Status</span>
              <h2>상태별 현황</h2>
            </div>
            <Filter size={18} />
          </div>
          <SchedulesCountRows data={data} />
          <div className="customers-side-actions">
            <a href={data.links.calendar}>일정 캘린더</a>
            <a href={data.links.schedules}>일정 목록</a>
          </div>
        </aside>
      </div>
    </section>
  );
}