import {
  AlertTriangle,
  ArrowLeft,
  Building2,
  FileText,
  Loader2,
  Mail,
  Pencil,
  Phone,
  Plus,
  Printer,
  Search,
  Trash2,
  Wrench,
  X,
} from 'lucide-react';
import { type FormEvent, type ReactNode, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  createService,
  deleteService,
  loadService,
  loadServiceForm,
  loadServices,
  searchServiceCustomers,
  updateService,
  type ServiceCustomer,
  type ServiceDetail,
  type ServiceFormOptions,
  type ServiceListData,
  type ServiceListFilters,
  type ServicePayload,
  type ServiceRequester,
} from '../../api/services';
import { formatDateLabel, formatNumber, formatWon } from '../../components/shared/formatters';
import { CRM_CLIENT_NAVIGATION_EVENT } from '../../navigationEvents';
import './services.css';

type Route =
  | { kind: 'list' }
  | { kind: 'new' }
  | { kind: 'detail'; id: number }
  | { kind: 'edit'; id: number };

function currentRoute(): Route {
  const path = window.location.pathname.replace(/\/+$/, '/');
  if (path === '/services/new/') return { kind: 'new' };
  const edit = path.match(/^\/services\/(\d+)\/edit\/$/);
  if (edit) return { kind: 'edit', id: Number(edit[1]) };
  const detail = path.match(/^\/services\/(\d+)\/$/);
  if (detail) return { kind: 'detail', id: Number(detail[1]) };
  return { kind: 'list' };
}

function go(href: string) {
  window.history.pushState(null, '', href);
  window.dispatchEvent(new Event(CRM_CLIENT_NAVIGATION_EVENT));
  window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
}

const errorText = (caught: unknown, fallback: string) => (caught instanceof Error ? caught.message : fallback);

const STATUS_TONE: Record<string, string> = {
  received: 'svc-tone-amber',
  in_progress: 'svc-tone-blue',
  waiting: 'svc-tone-amber',
  completed: 'svc-tone-green',
  cancelled: 'svc-tone-muted',
};

function StatusChip({ status, label }: { status: string; label: string }) {
  return <span className={`svc-chip ${STATUS_TONE[status] || 'svc-tone-muted'}`}>{label}</span>;
}

function ErrorBanner({ message }: { message: string }) {
  if (!message) return null;
  return (
    <div className="svc-error" role="alert">
      <AlertTriangle size={16} />
      <span>{message}</span>
    </div>
  );
}

export function ServicesPage() {
  const [route, setRoute] = useState<Route>(currentRoute);

  useEffect(() => {
    const refresh = () => setRoute(currentRoute());
    window.addEventListener('popstate', refresh);
    window.addEventListener(CRM_CLIENT_NAVIGATION_EVENT, refresh);
    return () => {
      window.removeEventListener('popstate', refresh);
      window.removeEventListener(CRM_CLIENT_NAVIGATION_EVENT, refresh);
    };
  }, []);

  if (route.kind === 'new') return <ServiceFormView key="new" />;
  if (route.kind === 'edit') return <ServiceFormView id={route.id} key={`edit-${route.id}`} />;
  if (route.kind === 'detail') return <ServiceDetailView id={route.id} key={`detail-${route.id}`} />;
  return <ServiceListView />;
}

// ------------------------------------------------------------------ 목록·현황

const STATUS_TABS = [
  { value: '', label: '전체' },
  { value: 'open', label: '진행 중' },
  { value: 'completed', label: '완료' },
];

function ServiceListView() {
  const thisYear = new Date().getFullYear();
  const [filters, setFilters] = useState<ServiceListFilters>({ year: thisYear, status: '', type: '', q: '' });
  const [query, setQuery] = useState('');
  const [data, setData] = useState<ServiceListData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const timer = window.setTimeout(() => setFilters((current) => (current.q === query ? current : { ...current, q: query })), 250);
    return () => window.clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    loadServices(filters)
      .then((payload) => {
        if (!alive) return;
        setData(payload);
        setError('');
      })
      .catch((caught) => alive && setError(errorText(caught, '서비스 목록을 불러오지 못했습니다.')))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [filters]);

  const summary = data?.summary;
  const monthMax = Math.max(1, ...(summary?.byMonth ?? [0]));

  return (
    <section className="svc-page">
      <div className="svc-toolbar">
        <select
          aria-label="연도"
          className="svc-select"
          onChange={(event) => setFilters((current) => ({ ...current, year: Number(event.target.value) }))}
          value={filters.year}
        >
          {(data?.years ?? [thisYear]).map((year) => <option key={year} value={year}>{year}년</option>)}
        </select>
        <div className="svc-tabs">
          {STATUS_TABS.map((tab) => (
            <button
              className={`svc-tab${filters.status === tab.value ? ' active' : ''}`}
              key={tab.value}
              onClick={() => setFilters((current) => ({ ...current, status: tab.value }))}
              type="button"
            >
              {tab.label}
            </button>
          ))}
        </div>
        <select
          aria-label="유형"
          className="svc-select"
          onChange={(event) => setFilters((current) => ({ ...current, type: event.target.value }))}
          value={filters.type}
        >
          <option value="">모든 유형</option>
          {data?.form.types.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
        <label className="svc-search">
          <Search size={15} />
          <input
            onChange={(event) => setQuery(event.target.value)}
            placeholder="기관·고객·장비·시리얼·부품·증상 검색"
            value={query}
          />
        </label>
        {loading ? <Loader2 className="spin-icon" size={16} /> : null}
        <a className="svc-primary" href="/services/new/">
          <Plus size={15} />
          서비스 기록
        </a>
      </div>

      <ErrorBanner message={error} />

      {summary ? (
        <>
          <div className="svc-stats">
            <div><span>{summary.year}년 서비스</span><strong>{formatNumber(summary.total)}건</strong></div>
            <div><span>완료</span><strong>{formatNumber(summary.completed)}건</strong></div>
            <div><span>진행 중</span><strong>{formatNumber(summary.open)}건</strong></div>
            <div><span>유상 서비스</span><strong>{formatNumber(summary.paidCount)}건 · {formatWon(summary.paidAmount)}</strong></div>
            <div><span>교체 부품</span><strong>{formatNumber(summary.partsCount)}개</strong></div>
          </div>
          {summary.total > 0 ? (
            <div className="svc-insights">
              <section className="svc-card">
                <h3>월별 건수</h3>
                <div className="svc-months">
                  {summary.byMonth.map((count, index) => (
                    <div className="svc-month" key={index} title={`${index + 1}월 ${count}건`}>
                      <i style={{ height: `${Math.round((count / monthMax) * 100)}%` }} />
                      <b>{count || ''}</b>
                      <span>{index + 1}</span>
                    </div>
                  ))}
                </div>
              </section>
              <section className="svc-card">
                <h3>유형 · 많이 간 기관</h3>
                <ul className="svc-rank">
                  {summary.byType.map((row) => <li key={row.type}><span>{row.label}</span><b>{row.count}</b></li>)}
                </ul>
                <ul className="svc-rank">
                  {summary.topInstitutions.map((row) => <li key={row.name}><span>{row.name}</span><b>{row.count}</b></li>)}
                </ul>
              </section>
              <section className="svc-card">
                <h3>반복 서비스 장비</h3>
                {summary.repeatSerials.length ? (
                  <ul className="svc-rank">
                    {summary.repeatSerials.map((row) => (
                      <li key={row.serialNumber}>
                        <button className="svc-link" onClick={() => setQuery(row.serialNumber)} type="button">
                          {row.equipment || '장비'} · {row.serialNumber}
                        </button>
                        <b>{row.count}회</b>
                      </li>
                    ))}
                  </ul>
                ) : <p className="svc-muted">같은 시리얼로 두 번 이상 간 장비가 없습니다.</p>}
              </section>
            </div>
          ) : null}
        </>
      ) : null}

      <div className="svc-table-wrap">
        <table className="svc-table">
          <thead>
            <tr>
              <th>서비스일</th>
              <th>기관 · 사용자</th>
              <th>장비</th>
              <th>내용</th>
              <th>유형</th>
              <th>상태</th>
              <th>부품</th>
              <th>비용</th>
              <th>담당</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((item) => (
              <tr key={item.id} onClick={() => go(item.href)}>
                <td className="svc-nowrap">{formatDateLabel(item.date)}</td>
                <td>
                  <strong>{item.institution || '기관 미정'}</strong>
                  <small>
                    {item.customer ? item.customer.name : '고객 미연결'}
                    {item.requester ? ` · 의뢰 ${item.requester.name || item.requester.customer?.name || ''}` : ''}
                  </small>
                </td>
                <td>
                  {item.equipment || <span className="svc-muted">-</span>}
                  {item.serialNumbers.length ? <small>S/N {item.serialNumbers.join(', ')}</small> : null}
                </td>
                <td className="svc-title-cell">
                  <a href={item.href} onClick={(event) => event.stopPropagation()}>{item.title}</a>
                  {item.partNames.length ? <small>{item.partNames.join(', ')}</small> : null}
                </td>
                <td className="svc-nowrap">{item.typeLabel}</td>
                <td><StatusChip label={item.statusLabel} status={item.status} /></td>
                <td className="svc-num">{item.partsCount || ''}</td>
                <td className="svc-nowrap">{item.chargeType === 'paid' ? (item.chargeAmount !== null ? formatWon(item.chargeAmount) : '유상') : '무상'}</td>
                <td className="svc-nowrap">{item.owner}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {data && data.items.length === 0 ? (
          <p className="svc-empty">
            {filters.q || filters.status || filters.type ? '조건에 맞는 서비스 기록이 없습니다.' : `${filters.year}년 서비스 기록이 없습니다. 오른쪽 위 "서비스 기록"으로 시작하세요.`}
          </p>
        ) : null}
        {data?.truncated ? <p className="svc-muted svc-pad">최근 500건까지만 보여줍니다. 검색으로 좁혀 주세요.</p> : null}
      </div>
    </section>
  );
}

// ------------------------------------------------------------------ 상세

function ContactCard({ heading, customer, fallbackName, contact, icon }: {
  heading: string;
  customer: ServiceCustomer | null;
  fallbackName: string;
  contact?: string;
  icon: ReactNode;
}) {
  return (
    <section className="svc-card svc-contact">
      <h3>{icon}{heading}</h3>
      <strong>{customer ? customer.name : fallbackName || '연결된 고객 없음'}</strong>
      {customer ? <span>{[customer.company, customer.department].filter(Boolean).join(' · ')}</span> : null}
      {contact ? <span>{contact}</span> : null}
      <div className="svc-contact-actions">
        {customer?.phone ? <a className="svc-ghost" href={`tel:${customer.phone}`}><Phone size={14} />{customer.phone}</a> : null}
        {customer?.email ? <a className="svc-ghost" href={`mailto:${customer.email}`}><Mail size={14} />{customer.email}</a> : null}
        {customer ? <a className="svc-ghost" href={customer.href}>고객 상세</a> : null}
      </div>
      {customer && !customer.phone && !customer.email ? <small className="svc-muted">고객 정보에 연락처가 없습니다.</small> : null}
    </section>
  );
}

function requesterName(requester: ServiceRequester) {
  return requester.name || requester.customer?.company || requester.customer?.name || '';
}

const BASIS_LABEL: Record<string, string> = {
  serial: '같은 장비(시리얼)의 지난 서비스',
  customer: '같은 고객의 지난 서비스',
  institution: '같은 기관의 지난 서비스',
};

function ServiceDetailView({ id }: { id: number }) {
  const [item, setItem] = useState<ServiceDetail | null>(null);
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let alive = true;
    loadService(id)
      .then((payload) => alive && setItem(payload.item))
      .catch((caught) => alive && setError(errorText(caught, '서비스 기록을 불러오지 못했습니다.')));
    return () => {
      alive = false;
    };
  }, [id]);

  const remove = async () => {
    if (!item || !window.confirm('이 서비스 기록을 삭제할까요? 되돌릴 수 없습니다.')) return;
    setDeleting(true);
    try {
      await deleteService(item.id);
      go('/services/');
    } catch (caught) {
      setError(errorText(caught, '삭제하지 못했습니다.'));
      setDeleting(false);
    }
  };

  if (!item) {
    return (
      <section className="svc-page">
        <a className="svc-back" href="/services/"><ArrowLeft size={15} />서비스 목록</a>
        {error ? <ErrorBanner message={error} /> : <p className="svc-muted"><Loader2 className="spin-icon" size={15} /> 불러오는 중</p>}
      </section>
    );
  }

  const flow = [
    { label: '증상', text: item.symptom },
    { label: '판단', text: item.diagnosis },
    { label: '조치', text: item.resolution },
  ];

  return (
    <section className="svc-page">
      <a className="svc-back" href="/services/"><ArrowLeft size={15} />서비스 목록</a>
      <header className="svc-detail-head">
        <div>
          <div className="svc-chips">
            <span className="svc-chip svc-tone-muted">{item.typeLabel}</span>
            <StatusChip label={item.statusLabel} status={item.status} />
            <span className={`svc-chip ${item.chargeType === 'paid' ? 'svc-tone-blue' : 'svc-tone-muted'}`}>
              {item.chargeLabel}{item.chargeType === 'paid' && item.chargeAmount !== null ? ` ${formatWon(item.chargeAmount)}` : ''}
            </span>
          </div>
          <h2>{item.title}</h2>
          <p className="svc-muted">
            {item.institution || '기관 미정'} · {formatDateLabel(item.date)}
            {item.completedDate && item.completedDate !== item.date ? ` → 완료 ${formatDateLabel(item.completedDate)}` : ''}
            {item.owner ? ` · 담당 ${item.owner}` : ''}
          </p>
        </div>
        <div className="svc-head-actions">
          <a className="svc-secondary" href={`/services/${item.id}/report/`} rel="noreferrer" target="_blank">
            <Printer size={15} />수리완료보고서
          </a>
          {item.canEdit ? <a className="svc-secondary" href={`/services/${item.id}/edit/`}><Pencil size={15} />수정</a> : null}
          {item.canEdit ? (
            <button className="svc-danger" disabled={deleting} onClick={() => void remove()} type="button">
              <Trash2 size={15} />삭제
            </button>
          ) : null}
        </div>
      </header>

      <ErrorBanner message={error} />

      <div className="svc-detail-grid">
        <ContactCard customer={item.customer} fallbackName={item.institution} heading="사용자" icon={<Building2 size={15} />} />
        {item.requester ? (
          <ContactCard
            contact={item.requester.contact}
            customer={item.requester.customer}
            fallbackName={requesterName(item.requester)}
            heading="의뢰처"
            icon={<FileText size={15} />}
          />
        ) : null}
        <section className={`svc-card svc-equipment${item.equipments.length > 2 ? ' svc-span-all' : ''}`}>
          <h3><Wrench size={15} />장비{item.equipments.length > 1 ? ` ${item.equipments.length}대` : ''}</h3>
          {item.equipments.length ? (
            <ol className="svc-equip-list">
              {item.equipments.map((equipment, index) => (
                <li key={equipment.id ?? index}>
                  <strong>{[equipment.name, equipment.modelName].filter(Boolean).join(' · ') || '장비'}</strong>
                  {equipment.serialNumber ? <span>S/N {equipment.serialNumber}</span> : null}
                  {equipment.note ? <small>{equipment.note}</small> : null}
                </li>
              ))}
            </ol>
          ) : <p className="svc-muted">장비 기록 없음</p>}
        </section>
      </div>

      <div className="svc-flow">
        {flow.map((step, index) => (
          <section className="svc-card svc-step" key={step.label}>
            <h3><b>{index + 1}</b>{step.label}</h3>
            {step.text ? <p>{step.text}</p> : <p className="svc-muted">기록 없음</p>}
          </section>
        ))}
      </div>

      <section className="svc-card">
        <h3>교체 부품</h3>
        {item.parts.length ? (
          <table className="svc-parts">
            <thead><tr><th>부품명</th><th>품번</th><th>수량</th><th>단가</th><th>금액</th></tr></thead>
            <tbody>
              {item.parts.map((part) => (
                <tr key={part.id ?? part.name}>
                  <td>{part.name}</td>
                  <td>{part.partNumber || '-'}</td>
                  <td className="svc-num">{part.quantity}</td>
                  <td className="svc-num">{part.unitPrice !== null ? formatWon(part.unitPrice) : '-'}</td>
                  <td className="svc-num">{part.amount !== null && part.amount !== undefined ? formatWon(part.amount) : '-'}</td>
                </tr>
              ))}
            </tbody>
            {item.partsAmount ? (
              <tfoot><tr><td colSpan={4}>부품 합계</td><td className="svc-num">{formatWon(item.partsAmount)}</td></tr></tfoot>
            ) : null}
          </table>
        ) : <p className="svc-muted">교체한 부품이 없습니다.</p>}
      </section>

      <section className="svc-card">
        <h3>{BASIS_LABEL[item.related.basis] || '지난 서비스'}</h3>
        {item.related.items.length ? (
          <ul className="svc-history">
            {item.related.items.map((row) => (
              <li key={row.id}>
                <span className="svc-nowrap">{formatDateLabel(row.date)}</span>
                <a href={row.href}>{row.title}</a>
                <small>{row.typeLabel} · {row.statusLabel}{row.diagnosis ? ` · 판단: ${row.diagnosis}` : ''}</small>
              </li>
            ))}
          </ul>
        ) : <p className="svc-muted">이전 서비스 기록이 없습니다.</p>}
      </section>
    </section>
  );
}

// ------------------------------------------------------------------ 입력·수정

function CustomerPicker({ label, value, onChange, placeholder }: {
  label: string;
  value: ServiceCustomer | null;
  onChange: (customer: ServiceCustomer | null) => void;
  placeholder: string;
}) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<ServiceCustomer[]>([]);
  const [open, setOpen] = useState(false);
  const [searching, setSearching] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const term = query.trim();
    if (!term) {
      setResults([]);
      return undefined;
    }
    let alive = true;
    const timer = window.setTimeout(() => {
      setSearching(true);
      searchServiceCustomers(term)
        .then((rows) => alive && setResults(rows))
        .catch(() => alive && setResults([]))
        .finally(() => alive && setSearching(false));
    }, 250);
    return () => {
      alive = false;
      window.clearTimeout(timer);
    };
  }, [query]);

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  if (value) {
    return (
      <div className="svc-field">
        <span>{label}</span>
        <div className="svc-picked">
          <strong>{value.name}</strong>
          <small>{[value.company, value.department].filter(Boolean).join(' · ')}</small>
          <button aria-label={`${label} 연결 해제`} className="svc-icon" onClick={() => onChange(null)} type="button"><X size={14} /></button>
        </div>
      </div>
    );
  }

  return (
    <div className="svc-field svc-picker" ref={boxRef}>
      <span>{label}</span>
      <input
        aria-label={`${label} 검색`}
        onChange={(event) => {
          setQuery(event.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        placeholder={placeholder}
        value={query}
      />
      {open && query.trim() ? (
        <ul className="svc-picker-list">
          {searching && !results.length ? <li className="svc-muted">찾는 중…</li> : null}
          {!searching && !results.length ? <li className="svc-muted">맞는 고객이 없습니다.</li> : null}
          {results.map((row) => (
            <li key={row.id}>
              <button
                onClick={() => {
                  onChange(row);
                  setQuery('');
                  setOpen(false);
                }}
                type="button"
              >
                <strong>{row.name}</strong>
                <small>{[row.company, row.department].filter(Boolean).join(' · ')}</small>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

type PartRow = { key: number; name: string; partNumber: string; quantity: string; unitPrice: string };
type EquipmentRow = { key: number; name: string; modelName: string; serialNumber: string; note: string };

type FormState = {
  customer: ServiceCustomer | null;
  institution: string;
  hasRequester: boolean;
  requester: ServiceCustomer | null;
  requesterName: string;
  requesterContact: string;
  type: string;
  status: string;
  date: string;
  completedDate: string;
  ownerId: string;
  title: string;
  symptom: string;
  diagnosis: string;
  resolution: string;
  equipments: EquipmentRow[];
  chargeType: string;
  chargeAmount: string;
  parts: PartRow[];
};

const today = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
};

let partKey = 0;
const emptyPart = (): PartRow => ({ key: ++partKey, name: '', partNumber: '', quantity: '1', unitPrice: '' });
const emptyEquipment = (): EquipmentRow => ({ key: ++partKey, name: '', modelName: '', serialNumber: '', note: '' });

const emptyForm = (): FormState => ({
  customer: null,
  institution: '',
  hasRequester: false,
  requester: null,
  requesterName: '',
  requesterContact: '',
  type: 'repair',
  status: 'completed',
  date: today(),
  completedDate: '',
  ownerId: '',
  title: '',
  symptom: '',
  diagnosis: '',
  resolution: '',
  equipments: [emptyEquipment()],
  chargeType: 'free',
  chargeAmount: '',
  parts: [],
});

function formFromDetail(item: ServiceDetail): FormState {
  return {
    customer: item.customer,
    institution: item.institution,
    hasRequester: Boolean(item.requester),
    requester: item.requester?.customer ?? null,
    requesterName: item.requester?.name ?? '',
    requesterContact: item.requester?.contact ?? '',
    type: item.type,
    status: item.status,
    date: item.date ?? today(),
    completedDate: item.completedDate ?? '',
    ownerId: item.ownerId ? String(item.ownerId) : '',
    title: item.rawTitle,
    symptom: item.symptom,
    diagnosis: item.diagnosis,
    resolution: item.resolution,
    equipments: item.equipments.length
      ? item.equipments.map((equipment) => ({
        key: ++partKey,
        name: equipment.name,
        modelName: equipment.modelName,
        serialNumber: equipment.serialNumber,
        note: equipment.note,
      }))
      : [emptyEquipment()],
    chargeType: item.chargeType,
    chargeAmount: item.chargeAmount !== null ? String(item.chargeAmount) : '',
    parts: item.parts.map((part) => ({
      key: ++partKey,
      name: part.name,
      partNumber: part.partNumber,
      quantity: String(part.quantity),
      unitPrice: part.unitPrice !== null ? String(part.unitPrice) : '',
    })),
  };
}

function toPayload(form: FormState): ServicePayload {
  return {
    customerId: form.customer?.id ?? null,
    institution: form.institution.trim(),
    requesterId: form.hasRequester ? form.requester?.id ?? null : null,
    requesterName: form.hasRequester ? form.requesterName.trim() : '',
    requesterContact: form.hasRequester ? form.requesterContact.trim() : '',
    type: form.type,
    status: form.status,
    date: form.date,
    completedDate: form.status === 'completed' ? form.completedDate : '',
    ownerId: form.ownerId ? Number(form.ownerId) : null,
    title: form.title,
    symptom: form.symptom,
    diagnosis: form.diagnosis,
    resolution: form.resolution,
    equipments: form.equipments
      .map((row) => ({ name: row.name.trim(), modelName: row.modelName.trim(), serialNumber: row.serialNumber.trim(), note: row.note.trim() }))
      .filter((row) => row.name || row.modelName || row.serialNumber || row.note),
    chargeType: form.chargeType,
    chargeAmount: form.chargeType === 'paid' ? form.chargeAmount : '',
    parts: form.parts
      .filter((part) => part.name.trim())
      .map((part) => ({ name: part.name.trim(), partNumber: part.partNumber.trim(), quantity: Number(part.quantity) || 1, unitPrice: part.unitPrice })),
  };
}

function ServiceFormView({ id }: { id?: number }) {
  const editing = id !== undefined;
  const [form, setForm] = useState<FormState>(emptyForm);
  const [options, setOptions] = useState<ServiceFormOptions | null>(null);
  const [loaded, setLoaded] = useState(!editing);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let alive = true;
    if (id !== undefined) {
      loadService(id)
        .then((payload) => {
          if (!alive) return;
          setOptions(payload.form);
          setForm(formFromDetail(payload.item));
          setLoaded(true);
        })
        .catch((caught) => alive && setError(errorText(caught, '서비스 기록을 불러오지 못했습니다.')));
    } else {
      loadServiceForm()
        .then((payload) => {
          if (!alive) return;
          setOptions(payload.form);
          setForm((current) => ({ ...current, ownerId: current.ownerId || String(payload.viewerId) }));
        })
        .catch((caught) => alive && setError(errorText(caught, '입력 항목을 불러오지 못했습니다.')));
    }
    return () => {
      alive = false;
    };
  }, [editing, id]);

  const set = useCallback(<K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((current) => ({ ...current, [key]: value }));
  }, []);

  const setEquipment = (key: number, field: keyof Omit<EquipmentRow, 'key'>, value: string) => {
    setForm((current) => ({ ...current, equipments: current.equipments.map((row) => (row.key === key ? { ...row, [field]: value } : row)) }));
  };

  const setPart = (key: number, field: keyof Omit<PartRow, 'key'>, value: string) => {
    setForm((current) => ({ ...current, parts: current.parts.map((part) => (part.key === key ? { ...part, [field]: value } : part)) }));
  };

  const partsTotal = useMemo(() => form.parts.reduce((sum, part) => {
    const price = Number(part.unitPrice.replace(/,/g, ''));
    return Number.isFinite(price) && part.unitPrice ? sum + price * (Number(part.quantity) || 1) : sum;
  }, 0), [form.parts]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!form.customer && !form.institution.trim()) {
      setError('기관을 입력하거나 고객을 연결하세요.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const saved = id !== undefined ? await updateService(id, toPayload(form)) : await createService(toPayload(form));
      go(`/services/${saved.id}/`);
    } catch (caught) {
      setError(errorText(caught, '저장하지 못했습니다.'));
      setSaving(false);
    }
  };

  const ownerSelectable = (options?.owners.length ?? 0) > 1;

  return (
    <section className="svc-page">
      <a className="svc-back" href={editing ? `/services/${id}/` : '/services/'}><ArrowLeft size={15} />{editing ? '돌아가기' : '서비스 목록'}</a>
      <h2 className="svc-form-title">{editing ? '서비스 기록 수정' : '새 서비스 기록'}</h2>
      <ErrorBanner message={error} />
      {!loaded ? <p className="svc-muted"><Loader2 className="spin-icon" size={15} /> 불러오는 중</p> : (
        <form className="svc-form" onSubmit={(event) => void submit(event)}>
          <section className="svc-card">
            <h3>고객</h3>
            <div className="svc-grid-2">
              <CustomerPicker
                label="사용자(엔드유저)"
                onChange={(customer) => {
                  set('customer', customer);
                  if (customer && !form.institution.trim()) set('institution', customer.company);
                }}
                placeholder="고객명·기관·부서로 검색"
                value={form.customer}
              />
              <label className="svc-field">
                <span>기관</span>
                <input maxLength={100} onChange={(event) => set('institution', event.target.value)} placeholder="고객을 고르면 자동으로 채워집니다" value={form.institution} />
              </label>
            </div>
            <label className="svc-check">
              <input checked={form.hasRequester} onChange={(event) => set('hasRequester', event.target.checked)} type="checkbox" />
              업체(대리점 등)에서 맡긴 건 — 의뢰처가 사용자와 다름
            </label>
            {form.hasRequester ? (
              <div className="svc-grid-3">
                <CustomerPicker
                  label="의뢰처 고객"
                  onChange={(customer) => {
                    set('requester', customer);
                    if (customer && !form.requesterName.trim()) set('requesterName', customer.company);
                  }}
                  placeholder="CRM 에 있는 업체 고객 검색(선택)"
                  value={form.requester}
                />
                <label className="svc-field">
                  <span>의뢰 업체명</span>
                  <input maxLength={200} onChange={(event) => set('requesterName', event.target.value)} placeholder="예: ○○상사" value={form.requesterName} />
                </label>
                <label className="svc-field">
                  <span>의뢰처 담당자 / 연락처</span>
                  <input maxLength={200} onChange={(event) => set('requesterContact', event.target.value)} placeholder="예: 박대리 02-123-4567" value={form.requesterContact} />
                </label>
              </div>
            ) : null}
          </section>

          <section className="svc-card">
            <h3>기본</h3>
            <div className="svc-grid-4">
              <label className="svc-field">
                <span>유형</span>
                <select onChange={(event) => set('type', event.target.value)} value={form.type}>
                  {options?.types.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                </select>
              </label>
              <label className="svc-field">
                <span>상태</span>
                <select onChange={(event) => set('status', event.target.value)} value={form.status}>
                  {options?.statuses.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                </select>
              </label>
              <label className="svc-field">
                <span>서비스일</span>
                <input onChange={(event) => set('date', event.target.value)} required type="date" value={form.date} />
              </label>
              {form.status === 'completed' ? (
                <label className="svc-field">
                  <span>완료일</span>
                  <input min={form.date} onChange={(event) => set('completedDate', event.target.value)} type="date" value={form.completedDate} />
                  <small>비우면 서비스일과 같게 저장됩니다</small>
                </label>
              ) : null}
              {ownerSelectable ? (
                <label className="svc-field">
                  <span>담당</span>
                  <select onChange={(event) => set('ownerId', event.target.value)} value={form.ownerId}>
                    {options?.owners.map((owner) => <option key={owner.id} value={owner.id}>{owner.name}</option>)}
                  </select>
                </label>
              ) : null}
            </div>
          </section>

          <section className="svc-card">
            <h3>장비{form.equipments.length > 1 ? ` ${form.equipments.length}대` : ''}</h3>
            <div className="svc-equip-head" aria-hidden="true">
              <span>장비명</span><span>모델</span><span>시리얼</span><span>장비별 메모</span><span />
            </div>
            <div className="svc-part-rows">
              {form.equipments.map((row, index) => (
                <div className="svc-equip-row" key={row.key}>
                  <input aria-label={`장비명 ${index + 1}`} maxLength={200} onChange={(event) => setEquipment(row.key, 'name', event.target.value)} placeholder="장비명" value={row.name} />
                  <input aria-label={`모델 ${index + 1}`} maxLength={200} onChange={(event) => setEquipment(row.key, 'modelName', event.target.value)} placeholder="모델" value={row.modelName} />
                  <input aria-label={`시리얼 ${index + 1}`} maxLength={120} onChange={(event) => setEquipment(row.key, 'serialNumber', event.target.value)} placeholder="시리얼" value={row.serialNumber} />
                  <input aria-label={`장비별 메모 ${index + 1}`} maxLength={300} onChange={(event) => setEquipment(row.key, 'note', event.target.value)} placeholder="이 장비만 해당하는 내용(선택)" value={row.note} />
                  <button
                    aria-label={`장비 ${index + 1} 삭제`}
                    className="svc-icon"
                    onClick={() => set('equipments', form.equipments.length > 1 ? form.equipments.filter((item) => item.key !== row.key) : [emptyEquipment()])}
                    type="button"
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
            <div className="svc-part-foot">
              <button className="svc-ghost" onClick={() => set('equipments', [...form.equipments, emptyEquipment()])} type="button"><Plus size={14} />장비 추가</button>
              <span className="svc-muted">한 번 방문에 여러 대를 봤으면 장비를 추가하세요. 증상·판단·조치는 아래에 함께 적습니다.</span>
            </div>
          </section>

          <section className="svc-card">
            <h3>내용</h3>
            <label className="svc-field">
              <span>한 줄 요약</span>
              <input maxLength={200} onChange={(event) => set('title', event.target.value)} placeholder="목록·아침회의에 보이는 문장 (비우면 증상 첫 줄)" value={form.title} />
            </label>
            <div className="svc-grid-3">
              <label className="svc-field"><span>증상</span><textarea onChange={(event) => set('symptom', event.target.value)} placeholder="고객이 말한 증상·요청" rows={5} value={form.symptom} /></label>
              <label className="svc-field"><span>판단</span><textarea onChange={(event) => set('diagnosis', event.target.value)} placeholder="점검해 보고 내린 판단·원인" rows={5} value={form.diagnosis} /></label>
              <label className="svc-field"><span>조치</span><textarea onChange={(event) => set('resolution', event.target.value)} placeholder="한 일·결과·고객 안내" rows={5} value={form.resolution} /></label>
            </div>
          </section>

          <section className="svc-card">
            <h3>교체 부품</h3>
            {form.parts.length ? (
              <div className="svc-part-rows">
                {form.parts.map((part) => (
                  <div className="svc-part-row" key={part.key}>
                    <input aria-label="부품명" onChange={(event) => setPart(part.key, 'name', event.target.value)} placeholder="부품명" value={part.name} />
                    <input aria-label="품번" onChange={(event) => setPart(part.key, 'partNumber', event.target.value)} placeholder="품번" value={part.partNumber} />
                    <input aria-label="수량" inputMode="numeric" min={1} onChange={(event) => setPart(part.key, 'quantity', event.target.value)} type="number" value={part.quantity} />
                    <input aria-label="단가" inputMode="numeric" onChange={(event) => setPart(part.key, 'unitPrice', event.target.value)} placeholder="단가(선택)" value={part.unitPrice} />
                    <button aria-label="부품 삭제" className="svc-icon" onClick={() => set('parts', form.parts.filter((row) => row.key !== part.key))} type="button"><X size={14} /></button>
                  </div>
                ))}
              </div>
            ) : null}
            <div className="svc-part-foot">
              <button className="svc-ghost" onClick={() => set('parts', [...form.parts, emptyPart()])} type="button"><Plus size={14} />부품 추가</button>
              {partsTotal ? <span className="svc-muted">부품 합계 {formatWon(partsTotal)}</span> : null}
            </div>
          </section>

          <section className="svc-card">
            <h3>비용</h3>
            <div className="svc-grid-4">
              <div className="svc-field">
                <span>유상/무상</span>
                <div className="svc-tabs">
                  {(options?.charges ?? []).map((option) => (
                    <button
                      className={`svc-tab${form.chargeType === option.value ? ' active' : ''}`}
                      key={option.value}
                      onClick={() => set('chargeType', option.value)}
                      type="button"
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>
              {form.chargeType === 'paid' ? (
                <label className="svc-field">
                  <span>청구 금액 (원)</span>
                  <input inputMode="numeric" onChange={(event) => set('chargeAmount', event.target.value)} placeholder={partsTotal ? String(partsTotal) : ''} value={form.chargeAmount} />
                  <small>서비스 현황용 — 매출에는 들어가지 않습니다</small>
                </label>
              ) : null}
            </div>
          </section>

          <div className="svc-form-actions">
            <a className="svc-secondary" href={editing ? `/services/${id}/` : '/services/'}>취소</a>
            <button className="svc-primary" disabled={saving} type="submit">
              {saving ? <Loader2 className="spin-icon" size={15} /> : null}
              저장
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
