import { useEffect, useState, type FormEvent } from 'react';
import {
    Activity,
    AlertTriangle,
    ArrowRightLeft,
    Check,
    CheckCircle2,
    CircleDollarSign,
    ListChecks,
    Loader2,
    Plus,
    Search,
    Trash2,
    Users,
    X
} from 'lucide-react';
import type {
    PrepaymentCreateData,
    PrepaymentCustomerData,
    PrepaymentDetailData,
    PrepaymentFormPayload,
    PrepaymentsData
} from '../../api/prepayments';
import {
    cancelPrepayment as cancelCustomerPrepayment,
    createPrepayment as createCustomerPrepayment,
    deletePrepayment as deleteCustomerPrepayment,
    transferPrepayment as transferCustomerPrepayment,
    updatePrepayment as updateCustomerPrepayment
} from '../../api/prepayments';
import { DashboardMetricCard } from '../../components/shared/DashboardMetricCard';
import { DashboardApiAlert, DashboardEmpty } from '../../components/shared/FeedbackStates';
import {
    formatDateLabel,
    formatDateTimeLabel,
    formatNumber,
    formatWon
} from '../../components/shared/formatters';
import { PrepaymentStatusBadge, SearchableSelect, joinOptionParts, localDateInputValue, makeCustomerSelectOption } from '../shared/appShared';


type PrepaymentFormState = {
  amount: string;
  balance: string;
  customerId: string;
  departmentId: string;
  memo: string;
  payerName: string;
  paymentDate: string;
  paymentMethod: string;
  status: string;
};

const makeEmptyPrepaymentForm = (): PrepaymentFormState => ({
  amount: '',
  balance: '',
  customerId: '',
  departmentId: '',
  memo: '',
  payerName: '',
  paymentDate: localDateInputValue(),
  paymentMethod: 'transfer',
  status: 'active',
});

const makePrepaymentEditForm = (prepayment: PrepaymentDetailData['prepayment'] | null): PrepaymentFormState => ({
  amount: prepayment ? String(prepayment.amount) : '',
  balance: prepayment ? String(prepayment.balance) : '',
  customerId: prepayment?.customerId ? String(prepayment.customerId) : '',
  departmentId: prepayment?.departmentId ? String(prepayment.departmentId) : '',
  memo: prepayment?.memo || '',
  payerName: prepayment?.payerName || '',
  paymentDate: prepayment?.paymentDate || localDateInputValue(),
  paymentMethod: prepayment?.paymentMethod || 'transfer',
  status: prepayment?.status || 'active',
});

function PrepaymentsTable({ data }: { data: PrepaymentsData }) {
  if (data.prepayments.length === 0) {
    return <DashboardEmpty label="표시할 선결제가 없습니다" />;
  }

  return (
    <div className="customers-table-wrap prepayments-table-wrap">
      <table className="customers-table prepayments-table">
        <thead>
          <tr>
            <th>고객</th>
            <th>입금 정보</th>
            <th>금액</th>
            <th>잔액</th>
            <th>상태</th>
            <th>담당</th>
            <th>작업</th>
          </tr>
        </thead>
        <tbody>
          {data.prepayments.map((prepayment) => (
            <tr key={prepayment.id}>
              <td>
                <a className="customer-name-link" href={prepayment.customerHref || prepayment.customerPrepaymentHref || '/customers/'}>
                  <strong>{prepayment.companyName || prepayment.customerName || '고객 미지정'}</strong>
                  <span>{[prepayment.departmentName, prepayment.customerName].filter(Boolean).join(' · ')}</span>
                </a>
                {prepayment.memo ? <small className="customer-muted-cell">{prepayment.memo}</small> : null}
              </td>
              <td>
                <div className="prepayment-info-cell">
                  <strong>{prepayment.paymentDate ? formatDateLabel(prepayment.paymentDate) : '입금일 없음'}</strong>
                  <span>{[prepayment.payerName || '입금자 미지정', prepayment.paymentMethodLabel].filter(Boolean).join(' · ')}</span>
                  {prepayment.usageCount > 0 ? <small>사용 {formatNumber(prepayment.usageCount)}건</small> : null}
                </div>
              </td>
              <td>
                <strong>{formatWon(prepayment.amount)}</strong>
                <small className="customer-muted-cell">사용 {formatWon(prepayment.usedAmount)}</small>
              </td>
              <td>
                <strong className={prepayment.balance > 0 ? 'prepayment-balance-active' : 'customer-muted-cell'}>
                  {formatWon(prepayment.balance)}
                </strong>
              </td>
              <td>
                <PrepaymentStatusBadge label={prepayment.statusLabel} status={prepayment.status} />
              </td>
              <td>
                <span className="customer-muted-cell">{prepayment.ownerName}</span>
              </td>
              <td>
                <div className="customer-row-actions">
                  <a className="customer-row-action" href={`/prepayments/${prepayment.id}/`}>상세</a>
                  {prepayment.canManage ? <a className="customer-row-action" href={`/prepayments/${prepayment.id}/edit/`}>수정</a> : null}
                  {prepayment.customerPrepaymentHref ? (
                    <a className="customer-row-action" href={prepayment.customerPrepaymentHref}>계정별</a>
                  ) : null}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function PrepaymentsPage({
  data,
  dataFilter,
  filterUser,
  loading,
  query,
  status,
  onDataFilterChange,
  onFilterUserChange,
  onQueryChange,
  onStatusChange,
}: {
  data: PrepaymentsData | null;
  dataFilter: string;
  filterUser: string;
  loading: boolean;
  query: string;
  status: string;
  onDataFilterChange: (value: string) => void;
  onFilterUserChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onStatusChange: (value: string) => void;
}) {
  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>선결제 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const metrics = [
    { label: '총 선결제', value: formatWon(data.metrics.totalAmount), detail: `${formatNumber(data.metrics.filteredPrepayments)}건`, icon: CircleDollarSign, tone: 'blue' as const },
    { label: '남은 잔액', value: formatWon(data.metrics.totalBalance), detail: '사용 가능 잔액', icon: CheckCircle2, tone: 'green' as const },
    { label: '사용 금액', value: formatWon(data.metrics.totalUsed), detail: '차감 누적', icon: Activity, tone: 'amber' as const },
    { label: '사용 가능', value: `${formatNumber(data.metrics.activeCount)}건`, detail: `소진 ${formatNumber(data.metrics.depletedCount)}건`, icon: CircleDollarSign, tone: 'teal' as const },
  ];
  const selectedDataFilter = dataFilter || data.filters.dataFilter || 'me';
  const selectedFilterUser = filterUser || data.filters.filterUser || '';
  const showOwnerSelect = selectedDataFilter === 'user';

  return (
    <section className="prepayments-page">
      {data.source !== 'django' ? (
        <DashboardApiAlert message={data.error} title="선결제 정보를 불러오지 못했습니다" />
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Prepayments</span>
          <h2>{data.scope.label || '선결제 현황'}</h2>
          <p>입금액, 사용액, 잔액을 계정 단위로 확인하고 납품 일정 차감 흐름과 연결합니다.</p>
        </div>
        <div className="schedules-summary-actions">
          {data.links.create ? (
            <a className="route-primary-action" href="/prepayments/new/">
              선결제 등록
              <Plus size={16} />
            </a>
          ) : null}
          <a className="route-secondary-action" href={data.links.excel}>엑셀</a>
        </div>
      </div>

      <section className="dashboard-metric-grid customers-metric-grid" aria-label="선결제 핵심 지표">
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

      <div className="customers-filter-bar prepayments-filter-bar">
        <label className="customers-search">
          <Search size={17} />
          <input
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="고객, 업체, 부서, 입금자 검색"
            value={query}
          />
        </label>
        <select onChange={(event) => onStatusChange(event.target.value)} value={status}>
          <option value="">상태 전체</option>
          {data.options.statuses.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onDataFilterChange(event.target.value)} value={selectedDataFilter}>
          {data.options.dataFilters.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select disabled={!showOwnerSelect} onChange={(event) => onFilterUserChange(event.target.value)} value={selectedFilterUser}>
          <option value="">직원 선택</option>
          {data.options.owners.map((option) => (
            <option key={option.id} value={option.id}>{option.name}</option>
          ))}
        </select>
      </div>

      {data.metrics.truncated ? (
        <div className="dashboard-api-alert compact">
          <AlertTriangle size={16} />
          <span>결과가 많아 최근 {formatNumber(data.metrics.returnedCount)}건만 표시합니다. 검색이나 상태 필터를 좁혀 확인하세요.</span>
        </div>
      ) : null}

      <section className="dashboard-panel prepayments-main-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Prepayment list</span>
            <h2>선결제 목록</h2>
          </div>
          {loading ? <Loader2 className="spin-icon" size={18} /> : <CircleDollarSign size={18} />}
        </div>
        <PrepaymentsTable data={data} />
      </section>
    </section>
  );
}

export function PrepaymentCustomerPage({
  data,
  loading,
  selectedUser,
  onSelectedUserChange,
}: {
  data: PrepaymentCustomerData | null;
  loading: boolean;
  selectedUser: string;
  onSelectedUserChange: (value: string) => void;
}) {
  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>계정 선결제 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const isAccountScope = data.scope.mode === 'department';
  const metrics = [
    { label: '총 선결제', value: formatWon(data.metrics.totalAmount), detail: `${formatNumber(data.metrics.totalCount)}건`, icon: CircleDollarSign, tone: 'blue' as const },
    { label: '남은 잔액', value: formatWon(data.metrics.totalBalance), detail: `${data.scope.targetUserName || '담당'} 기준`, icon: CheckCircle2, tone: 'green' as const },
    { label: '사용 금액', value: formatWon(data.metrics.totalUsed), detail: '차감 누적', icon: Activity, tone: 'amber' as const },
    { label: '사용 가능', value: `${formatNumber(data.metrics.activeCount)}건`, detail: `소진 ${formatNumber(data.metrics.depletedCount)}건 · 취소 ${formatNumber(data.metrics.cancelledCount)}건`, icon: ListChecks, tone: 'teal' as const },
  ];

  return (
    <section className="prepayments-page prepayment-customer-page">
      {data.source !== 'django' ? (
        <DashboardApiAlert message={data.error} title="계정 선결제 정보를 불러오지 못했습니다" />
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">{isAccountScope ? 'Account prepayments' : 'Customer prepayments'}</span>
          <h2>{data.scope.name || data.customer.customerName || (isAccountScope ? '계정 선결제' : '고객별 선결제')}</h2>
          <p>
            {[
              isAccountScope ? '부서/연구실 계정 기준' : '고객 기준',
              data.scope.targetUserName ? `${data.scope.targetUserName} 등록분` : '',
            ].filter(Boolean).join(' · ')}
          </p>
        </div>
        <div className="schedules-summary-actions">
          {data.links.accountDetail ? <a className="route-secondary-action" href={data.links.accountDetail}>계정 상세</a> : null}
          <a className="route-secondary-action" href={data.links.prepayments}>선결제 목록</a>
          <a className="route-secondary-action" href={data.links.accountExcel || data.links.djangoExcel}>엑셀</a>
        </div>
      </div>

      <section className="dashboard-metric-grid customers-metric-grid" aria-label="고객별 선결제 지표">
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

      <div className="prepayment-customer-layout">
        <section className="dashboard-panel prepayments-main-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">{isAccountScope ? 'Account scope' : 'Customer scope'}</span>
              <h2>선결제 내역</h2>
            </div>
            {loading ? <Loader2 className="spin-icon" size={18} /> : <CircleDollarSign size={18} />}
          </div>
          {data.scope.canSelectUser ? (
            <div className="prepayment-customer-filter">
              <label>
                <span>조회 사용자</span>
                <select onChange={(event) => onSelectedUserChange(event.target.value)} value={selectedUser || (data.scope.targetUserId ? String(data.scope.targetUserId) : '')}>
                  <option value="">{data.scope.targetUserName || '회사 전체'}</option>
                  {data.options.owners.map((owner) => (
                    <option key={owner.id} value={owner.id}>{owner.name}</option>
                  ))}
                </select>
              </label>
            </div>
          ) : null}

          {data.prepayments.length === 0 ? (
            <DashboardEmpty label="표시할 선결제 내역이 없습니다" />
          ) : (
            <div className="customers-table-wrap prepayments-table-wrap">
              <table className="customers-table prepayments-table prepayment-customer-table">
                <thead>
                  <tr>
                    <th>고객</th>
                    <th>입금 정보</th>
                    <th>금액</th>
                    <th>잔액</th>
                    <th>상태</th>
                    <th>작업</th>
                  </tr>
                </thead>
                <tbody>
                  {data.prepayments.map((prepayment) => (
                    <tr key={prepayment.id}>
                      <td>
                        <a className="customer-name-link" href={prepayment.customerHref || '/customers/'}>
                          <strong>{prepayment.customerName || data.customer.customerName || '고객 미정'}</strong>
                          <span>{[prepayment.companyName, prepayment.departmentName].filter(Boolean).join(' · ')}</span>
                        </a>
                      </td>
                      <td>
                        <div className="prepayment-info-cell">
                          <strong>{prepayment.paymentDate ? formatDateLabel(prepayment.paymentDate) : '입금일 없음'}</strong>
                          <span>{[prepayment.payerName || '입금자 미지정', prepayment.paymentMethodLabel].filter(Boolean).join(' · ')}</span>
                          {prepayment.usageCount > 0 ? <small>사용 {formatNumber(prepayment.usageCount)}건</small> : null}
                        </div>
                      </td>
                      <td>
                        <strong>{formatWon(prepayment.amount)}</strong>
                        <small className="customer-muted-cell">사용 {formatWon(prepayment.usedAmount)}</small>
                      </td>
                      <td>
                        <strong className={prepayment.balance > 0 ? 'prepayment-balance-active' : 'customer-muted-cell'}>
                          {formatWon(prepayment.balance)}
                        </strong>
                      </td>
                      <td>
                        <PrepaymentStatusBadge label={prepayment.statusLabel} status={prepayment.status} />
                      </td>
                      <td>
                        <div className="customer-row-actions">
                          <a className="customer-row-action" href={`/prepayments/${prepayment.id}/`}>상세</a>
                          {prepayment.canManage ? <a className="customer-row-action" href={`/prepayments/${prepayment.id}/edit/`}>수정</a> : null}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <aside className="dashboard-panel prepayment-customer-side">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Customers</span>
              <h2>{isAccountScope ? '계정 담당자' : '기준 고객'}</h2>
            </div>
            <Users size={18} />
          </div>
          <div className="prepayment-customer-list">
            {data.departmentCustomers.map((customer) => (
              <a className={customer.id === data.customer.id ? 'active' : ''} href={`/prepayments/customer/${customer.id}/`} key={customer.id}>
                <strong>{customer.customerName}</strong>
                <span>{customer.ownerName}</span>
              </a>
            ))}
          </div>
          <div className="customers-side-actions">
            <a href={data.links.accountDetail || data.links.customerDetail || '/prepayments/'}>{isAccountScope ? '계정 상세' : '고객 상세'}</a>
          </div>
        </aside>
      </div>

      <div className="prepayment-drilldown-grid">
        <section className="dashboard-panel prepayment-usage-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Balance drilldown</span>
              <h2>계정 잔액</h2>
            </div>
            <CheckCircle2 size={18} />
          </div>
          {data.balanceRows.length === 0 ? (
            <DashboardEmpty label="표시할 잔액이 없습니다" />
          ) : (
            <div className="prepayment-usage-list">
              {data.balanceRows.map((row) => (
                <article className="prepayment-usage-row" key={row.id}>
                  <div>
                    <strong>{row.payerName || row.customerName || '입금자 미지정'}</strong>
                    <span>{[row.paymentDate ? formatDateLabel(row.paymentDate) : '', row.customerName, row.statusLabel].filter(Boolean).join(' · ')}</span>
                    {row.memo ? <small>{row.memo}</small> : null}
                  </div>
                  <div className="prepayment-usage-amount">
                    <strong>{formatWon(row.balance)}</strong>
                    <span>원금 {formatWon(row.amount)} · 사용 {formatWon(row.usedAmount)}</span>
                    <a href={`/prepayments/${row.id}/`}>상세</a>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="dashboard-panel prepayment-usage-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Delivery deductions</span>
              <h2>납품 차감 내역</h2>
            </div>
            <ListChecks size={18} />
          </div>
          {data.deductionRows.length === 0 ? (
            <DashboardEmpty label="납품 차감 내역이 없습니다" />
          ) : (
            <div className="prepayment-usage-list">
              {data.deductionRows.map((usage) => (
                <article className="prepayment-usage-row" key={usage.id}>
                  <div>
                    <strong>{usage.productName || '납품 차감'}</strong>
                    <span>{[usage.usedAt ? formatDateTimeLabel(usage.usedAt) : '', usage.scheduleDate ? `납품 ${formatDateLabel(usage.scheduleDate)}` : '', usage.payerName].filter(Boolean).join(' · ')}</span>
                    {usage.deliveryItems.length > 0 ? (
                      <small>{usage.deliveryItems.map((item) => `${item.itemName} ${formatNumber(item.quantity)}${item.unit || ''}`).join(', ')}</small>
                    ) : usage.memo ? <small>{usage.memo}</small> : null}
                  </div>
                  <div className="prepayment-usage-amount">
                    <strong>-{formatWon(usage.amount)}</strong>
                    <span>잔액 {formatWon(usage.remainingBalance)}</span>
                    {usage.scheduleHref ? <a href={usage.scheduleHref}>일정</a> : null}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="dashboard-panel prepayment-usage-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Ledger</span>
              <h2>조정/이관/취소 기록</h2>
            </div>
            <Activity size={18} />
          </div>
          {data.ledgerEntries.length === 0 ? (
            <DashboardEmpty label="원장 기록이 없습니다" />
          ) : (
            <div className="prepayment-usage-list">
              {data.ledgerEntries.map((entry) => (
                <article className="prepayment-usage-row" key={entry.id}>
                  <div>
                    <strong>{entry.entryTypeLabel}</strong>
                    <span>{[entry.createdAt ? formatDateTimeLabel(entry.createdAt) : '', entry.actorName, entry.targetUserName ? `대상 ${entry.targetUserName}` : ''].filter(Boolean).join(' · ')}</span>
                    {entry.memo ? <small>{entry.memo}</small> : null}
                  </div>
                  <div className="prepayment-usage-amount">
                    <strong>{entry.amount < 0 ? '-' : ''}{formatWon(Math.abs(entry.amount))}</strong>
                    <span>잔액 {formatWon(entry.balanceAfter)}</span>
                    {entry.prepaymentHref ? <a href={entry.prepaymentHref}>선결제</a> : null}
                    {entry.scheduleHref ? <a href={entry.scheduleHref}>일정</a> : null}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </section>
  );
}

function PrepaymentFormFields({
  form,
  options,
  saving,
  showStatus,
  submitLabel,
  onChange,
  onSubmit,
  secondaryActions,
}: {
  form: PrepaymentFormState;
  options: {
    accounts: PrepaymentCreateData['create']['accounts'];
    customers: PrepaymentCreateData['create']['customers'];
    paymentMethods: PrepaymentCreateData['create']['paymentMethods'];
    statuses: PrepaymentCreateData['create']['statuses'];
  };
  saving: boolean;
  showStatus: boolean;
  submitLabel: string;
  onChange: (field: keyof PrepaymentFormState, value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  secondaryActions?: React.ReactNode;
}) {
  const accountOptions = options.accounts.map((account) => ({
    value: String(account.id),
    label: account.label || joinOptionParts([account.companyName, account.departmentName || account.name]),
    meta: `${formatNumber(account.customerCount)}명`,
    searchText: [account.label, account.companyName, account.departmentName, account.name].filter(Boolean).join(' '),
  }));
  const filteredCustomers = form.departmentId
    ? options.customers.filter((customer) => String(customer.departmentId ?? '') === form.departmentId)
    : options.customers;
  return (
    <form className="notes-create-form prepayment-form" onSubmit={onSubmit}>
      <div className="notes-create-grid prepayment-form-grid">
        <div className="form-field">
          <span>계정</span>
          <SearchableSelect
            ariaLabel="계정 선택"
            onChange={(nextValue) => onChange('departmentId', nextValue)}
            options={accountOptions}
            placeholder="업체, 부서/연구실 검색"
            value={form.departmentId}
          />
        </div>
        <div className="form-field">
          <span>담당자 보조 정보</span>
          <SearchableSelect
            ariaLabel="담당자 선택"
            allowEmpty
            disabled={!form.departmentId}
            emptyLabel="담당자 미지정"
            onChange={(nextValue) => onChange('customerId', nextValue)}
            options={filteredCustomers.map(makeCustomerSelectOption)}
            placeholder={form.departmentId ? '담당자 검색' : '계정 선택 후 검색'}
            value={form.customerId}
          />
        </div>
        <label>
          <span>입금일</span>
          <input
            onChange={(event) => onChange('paymentDate', event.target.value)}
            required
            type="date"
            value={form.paymentDate}
          />
        </label>
        <label>
          <span>선결제 금액</span>
          <input
            inputMode="numeric"
            min="1"
            onChange={(event) => onChange('amount', event.target.value)}
            placeholder="예: 250000"
            required
            type="number"
            value={form.amount}
          />
        </label>
        {showStatus ? (
          <label>
            <span>잔액</span>
            <input
              inputMode="numeric"
              min="0"
              onChange={(event) => onChange('balance', event.target.value)}
              required
              type="number"
              value={form.balance}
            />
          </label>
        ) : null}
        <label>
          <span>입금 방법</span>
          <select
            onChange={(event) => onChange('paymentMethod', event.target.value)}
            required
            value={form.paymentMethod}
          >
            {options.paymentMethods.map((method) => (
              <option key={method.value} value={method.value}>{method.label}</option>
            ))}
          </select>
        </label>
        <label>
          <span>입금자명</span>
          <input
            onChange={(event) => onChange('payerName', event.target.value)}
            placeholder="실제 입금자"
            value={form.payerName}
          />
        </label>
        {showStatus ? (
          <label>
            <span>상태</span>
            <select
              onChange={(event) => onChange('status', event.target.value)}
              required
              value={form.status}
            >
              {options.statuses.map((statusOption) => (
                <option key={statusOption.value} value={statusOption.value}>{statusOption.label}</option>
              ))}
            </select>
          </label>
        ) : null}
      </div>
      <label>
        <span>메모</span>
        <textarea
          onChange={(event) => onChange('memo', event.target.value)}
          rows={4}
          value={form.memo}
        />
      </label>
      <div className="notes-create-actions">
        {secondaryActions}
        <button className="route-primary-action" disabled={saving} type="submit">
          {saving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
          {submitLabel}
        </button>
      </div>
    </form>
  );
}

export function PrepaymentCreatePage({
  data,
  loading,
}: {
  data: PrepaymentCreateData | null;
  loading: boolean;
}) {
  const [form, setForm] = useState<PrepaymentFormState>(() => makeEmptyPrepaymentForm());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [createdHref, setCreatedHref] = useState('');

  const handleChange = (field: keyof PrepaymentFormState, value: string) => {
    if (field === 'departmentId') {
      setForm((previous) => ({
        ...previous,
        departmentId: value,
        customerId: '',
      }));
      setError('');
      setMessage('');
      setCreatedHref('');
      return;
    }
    setForm((previous) => ({
      ...previous,
      [field]: value,
      ...(field === 'amount' && !previous.balance ? { balance: value } : {}),
    }));
    setError('');
    setMessage('');
    setCreatedHref('');
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data || saving) {
      return;
    }
    if (!data.create.canCreate) {
      setError(data.create.message || '등록 권한이 없습니다.');
      return;
    }
    const departmentId = Number(form.departmentId);
    const customerId = Number(form.customerId);
    if (!departmentId) {
      setError('계정을 선택하세요.');
      return;
    }
    if (!form.amount || Number(form.amount) <= 0) {
      setError('선결제 금액을 입력하세요.');
      return;
    }
    if (!form.paymentDate) {
      setError('입금일을 선택하세요.');
      return;
    }

    const payload: PrepaymentFormPayload = {
      amount: form.amount,
      departmentId,
      customerId: customerId || null,
      memo: form.memo.trim() || undefined,
      payerName: form.payerName.trim() || undefined,
      paymentDate: form.paymentDate,
      paymentMethod: form.paymentMethod,
    };

    setSaving(true);
    setError('');
    setMessage('');
    setCreatedHref('');
    try {
      const created = await createCustomerPrepayment(payload, data.create.submitUrl);
      setMessage(created.message || '선결제를 등록했습니다.');
      setCreatedHref(created.href || (created.prepaymentId ? `/prepayments/${created.prepaymentId}/` : ''));
      setForm((previous) => ({
        ...makeEmptyPrepaymentForm(),
        departmentId: previous.departmentId,
        customerId: previous.customerId,
      }));
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : '선결제 등록에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>선결제 등록 정보를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const formOptions = {
    accounts: data.create.accounts,
    customers: data.create.customers,
    paymentMethods: data.create.paymentMethods,
    statuses: data.create.statuses,
  };

  return (
    <section className="prepayments-page prepayment-detail-page">
      {data.source !== 'django' ? (
        <DashboardApiAlert message={data.error} title="선결제 등록 정보를 불러오지 못했습니다" />
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">New prepayment</span>
          <h2>선결제 등록</h2>
          <p>계정을 먼저 선택하고 담당자는 보조 정보로 연결해 납품 차감 잔액을 관리합니다.</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href="/prepayments/">목록</a>
        </div>
      </div>

      <section className="dashboard-panel notes-create-panel prepayment-editor-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Prepayment form</span>
            <h2>입금 정보</h2>
          </div>
          {saving ? <Loader2 className="spin-icon" size={18} /> : <CircleDollarSign size={18} />}
        </div>
        {message ? (
          <div className="notes-action-feedback success">
            <span>{message}</span>
            {createdHref ? <a href={createdHref}>상세 열기</a> : null}
          </div>
        ) : null}
        {error ? <div className="notes-action-feedback error">{error}</div> : null}
        {!data.create.canCreate ? (
          <DashboardEmpty label={data.create.message || '선결제 등록 권한이 없습니다'} />
        ) : (
          <PrepaymentFormFields
            form={form}
            options={formOptions}
            saving={saving}
            showStatus={false}
            submitLabel="등록"
            onChange={handleChange}
            onSubmit={handleSubmit}
          />
        )}
      </section>
    </section>
  );
}

export function PrepaymentDetailPage({
  data,
  editRoute,
  loading,
  onRefresh,
}: {
  data: PrepaymentDetailData | null;
  editRoute: boolean;
  loading: boolean;
  onRefresh: () => Promise<PrepaymentDetailData | null>;
}) {
  const prepayment = data?.prepayment ?? null;
  const [form, setForm] = useState<PrepaymentFormState>(() => makePrepaymentEditForm(prepayment));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [cancelReason, setCancelReason] = useState('');
  const [transferUserId, setTransferUserId] = useState('');
  const [transferReason, setTransferReason] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState('');
  const [actionBusy, setActionBusy] = useState<'cancel' | 'delete' | 'transfer' | ''>('');
  const [actionError, setActionError] = useState('');
  const [actionMessage, setActionMessage] = useState('');
  const transferUserIdsKey = data?.actions.transferUsers.map((user) => user.id).join(',') ?? '';

  useEffect(() => {
    setForm(makePrepaymentEditForm(prepayment));
    setError('');
    setMessage('');
    setSaving(false);
    setCancelReason('');
    setTransferReason('');
    setDeleteConfirm('');
    setActionBusy('');
    setActionError('');
    setActionMessage('');
  }, [prepayment?.id]);

  useEffect(() => {
    const transferUsers = data?.actions.transferUsers ?? [];
    const firstTransferUserId = transferUsers[0] ? String(transferUsers[0].id) : '';
    setTransferUserId((current) => {
      if (current && transferUsers.some((user) => String(user.id) === current)) {
        return current;
      }
      return firstTransferUserId;
    });
  }, [prepayment?.id, transferUserIdsKey]);

  const handleChange = (field: keyof PrepaymentFormState, value: string) => {
    if (field === 'departmentId') {
      setForm((previous) => ({
        ...previous,
        departmentId: value,
        customerId: '',
      }));
      setError('');
      setMessage('');
      return;
    }
    setForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setError('');
    setMessage('');
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data || !prepayment || saving) {
      return;
    }
    if (!data.edit.canEdit || !data.edit.submitUrl) {
      setError(data.edit.message || '수정 권한이 없습니다.');
      return;
    }
    const departmentId = Number(form.departmentId);
    const customerId = Number(form.customerId);
    const amount = Number(form.amount);
    const balance = Number(form.balance);
    if (!departmentId) {
      setError('계정을 선택하세요.');
      return;
    }
    if (!Number.isFinite(amount) || amount <= 0) {
      setError('선결제 금액을 입력하세요.');
      return;
    }
    if (!Number.isFinite(balance) || balance < 0) {
      setError('잔액은 0원 이상이어야 합니다.');
      return;
    }
    if (balance > amount) {
      setError('잔액은 선결제 금액보다 클 수 없습니다.');
      return;
    }

    const payload: PrepaymentFormPayload = {
      amount: form.amount,
      balance: form.balance,
      departmentId,
      customerId: customerId || null,
      memo: form.memo.trim() || undefined,
      payerName: form.payerName.trim() || undefined,
      paymentDate: form.paymentDate,
      paymentMethod: form.paymentMethod,
      status: form.status,
    };

    setSaving(true);
    setError('');
    setMessage('');
    try {
      const updated = await updateCustomerPrepayment(payload, data.edit.submitUrl);
      await onRefresh();
      setMessage(updated.message || '선결제 정보를 수정했습니다.');
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : '선결제 수정에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data || !prepayment || actionBusy) {
      return;
    }
    if (!data.actions.canCancel || !data.actions.cancelUrl) {
      setActionError('취소 권한이 없거나 이미 취소된 선결제입니다.');
      return;
    }

    setActionBusy('cancel');
    setActionError('');
    setActionMessage('');
    try {
      const cancelled = await cancelCustomerPrepayment(data.actions.cancelUrl, cancelReason);
      await onRefresh();
      setCancelReason('');
      setActionMessage(cancelled.message || '선결제를 취소했습니다.');
    } catch (cancelError) {
      setActionError(cancelError instanceof Error ? cancelError.message : '선결제 취소에 실패했습니다.');
    } finally {
      setActionBusy('');
    }
  };

  const handleTransfer = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data || !prepayment || actionBusy) {
      return;
    }
    if (!data.actions.canTransfer || !data.actions.transferUrl) {
      setActionError('이관 권한이 없습니다.');
      return;
    }
    const targetUserId = Number(transferUserId);
    if (!Number.isFinite(targetUserId) || targetUserId <= 0) {
      setActionError('이관 대상을 선택하세요.');
      return;
    }

    setActionBusy('transfer');
    setActionError('');
    setActionMessage('');
    try {
      const transferred = await transferCustomerPrepayment(data.actions.transferUrl, targetUserId, transferReason);
      await onRefresh();
      setTransferReason('');
      setActionMessage(transferred.message || '선결제를 이관했습니다.');
    } catch (transferError) {
      setActionError(transferError instanceof Error ? transferError.message : '선결제 이관에 실패했습니다.');
    } finally {
      setActionBusy('');
    }
  };

  const handleDelete = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data || !prepayment || actionBusy) {
      return;
    }
    if (!data.actions.canDelete || !data.actions.deleteUrl) {
      setActionError(data.actions.deleteMessage || '삭제할 수 없는 선결제입니다.');
      return;
    }
    if (deleteConfirm.trim() !== '삭제') {
      setActionError('확인 문구를 입력하세요.');
      return;
    }

    setActionBusy('delete');
    setActionError('');
    setActionMessage('');
    try {
      const deleted = await deleteCustomerPrepayment(data.actions.deleteUrl);
      window.location.href = deleted.href || '/prepayments/';
    } catch (deleteError) {
      setActionError(deleteError instanceof Error ? deleteError.message : '선결제 삭제에 실패했습니다.');
      setActionBusy('');
    }
  };

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>선결제 상세 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data || !prepayment) {
    return (
      <section className="prepayments-page">
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>선결제 상세를 불러오지 못했습니다</strong>
            <span>{data?.error || '선결제 상세 정보를 불러오지 못했습니다.'}</span>
          </div>
          <a href="/prepayments/">목록</a>
        </div>
      </section>
    );
  }

  const metrics = [
    { label: '선결제 금액', value: formatWon(data.metrics.amount), detail: prepayment.paymentDate ? formatDateLabel(prepayment.paymentDate) : '입금일 없음', icon: CircleDollarSign, tone: 'blue' as const },
    { label: '남은 잔액', value: formatWon(data.metrics.balance), detail: `${data.metrics.balancePercent}% 남음`, icon: CheckCircle2, tone: 'green' as const },
    { label: '사용 금액', value: formatWon(data.metrics.usedAmount), detail: `${data.metrics.usagePercent}% 사용`, icon: Activity, tone: 'amber' as const },
    { label: '사용 내역', value: `${formatNumber(data.metrics.usageCount)}건`, detail: prepayment.statusLabel, icon: ListChecks, tone: 'teal' as const },
  ];
  const formOptions = {
    accounts: data.edit.accounts,
    customers: data.edit.customers,
    paymentMethods: data.edit.paymentMethods,
    statuses: data.edit.statuses,
  };
  const deleteConfirmed = deleteConfirm.trim() === '삭제';
  const actionDisabled = Boolean(actionBusy);

  return (
    <section className="prepayments-page prepayment-detail-page">
      {data.source !== 'django' ? (
        <DashboardApiAlert message={data.error} title="선결제 상세 정보를 불러오지 못했습니다" />
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Prepayment detail</span>
          <h2>{prepayment.companyName || prepayment.customerName || '선결제 상세'}</h2>
          <p>{[prepayment.departmentName, prepayment.customerName, prepayment.payerName || '입금자 미지정'].filter(Boolean).join(' · ')}</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href="/prepayments/">목록</a>
          {data.links.reactEdit && !editRoute ? <a className="route-primary-action" href={data.links.reactEdit}>수정</a> : null}
        </div>
      </div>

      <section className="dashboard-metric-grid customers-metric-grid" aria-label="선결제 상세 지표">
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

      {editRoute ? (
        <section className="dashboard-panel notes-create-panel prepayment-editor-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Edit prepayment</span>
              <h2>선결제 수정</h2>
            </div>
            {saving ? <Loader2 className="spin-icon" size={18} /> : <CircleDollarSign size={18} />}
          </div>
          {message ? <div className="notes-action-feedback success">{message}</div> : null}
          {error ? <div className="notes-action-feedback error">{error}</div> : null}
          {!data.edit.canEdit ? (
            <DashboardEmpty label={data.edit.message || '수정 권한이 없습니다'} />
          ) : (
            <PrepaymentFormFields
              form={form}
              options={formOptions}
              saving={saving}
              showStatus
              submitLabel="저장"
              onChange={handleChange}
              onSubmit={handleSubmit}
            />
          )}
        </section>
      ) : null}

      <div className="prepayment-detail-layout">
        <section className="dashboard-panel prepayment-usage-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Usage history</span>
              <h2>사용 내역</h2>
            </div>
            <ListChecks size={18} />
          </div>
          {data.usages.length === 0 ? (
            <DashboardEmpty label="아직 사용 내역이 없습니다" />
          ) : (
            <div className="prepayment-usage-list">
              {data.usages.map((usage) => (
                <article className="prepayment-usage-row" key={usage.id}>
                  <div>
                    <strong>{usage.productName || '사용 내역'}</strong>
                    <span>
                      {[usage.usedAt ? formatDateTimeLabel(usage.usedAt) : '', usage.scheduleDate ? `납품 ${formatDateLabel(usage.scheduleDate)}` : ''].filter(Boolean).join(' · ')}
                    </span>
                    {usage.deliveryItems.length > 0 ? (
                      <small>{usage.deliveryItems.map((item) => `${item.itemName} ${formatNumber(item.quantity)}${item.unit || ''}`).join(', ')}</small>
                    ) : usage.memo ? <small>{usage.memo}</small> : null}
                  </div>
                  <div className="prepayment-usage-amount">
                    <strong>-{formatWon(usage.amount)}</strong>
                    <span>잔액 {formatWon(usage.remainingBalance)}</span>
                    {usage.scheduleHref ? <a href={usage.scheduleHref}>일정</a> : null}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <aside className="dashboard-panel prepayment-detail-side">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Summary</span>
              <h2>기본 정보</h2>
            </div>
            <CircleDollarSign size={18} />
          </div>
          <PrepaymentStatusBadge label={prepayment.statusLabel} status={prepayment.status} />
          <dl className="prepayment-detail-list">
            <div>
              <dt>입금 방법</dt>
              <dd>{prepayment.paymentMethodLabel || '-'}</dd>
            </div>
            <div>
              <dt>등록자</dt>
              <dd>{prepayment.ownerName}</dd>
            </div>
            <div>
              <dt>등록일</dt>
              <dd>{prepayment.createdAt ? formatDateTimeLabel(prepayment.createdAt) : '-'}</dd>
            </div>
            <div>
              <dt>메모</dt>
              <dd>{prepayment.memo || '메모 없음'}</dd>
            </div>
          </dl>
          {actionMessage ? <div className="notes-action-feedback success">{actionMessage}</div> : null}
          {actionError ? <div className="notes-action-feedback error">{actionError}</div> : null}
          {!data.scope.canManage ? (
            <DashboardEmpty label="등록자만 취소/삭제/이관할 수 있습니다" />
          ) : (
            <div className="prepayment-action-panel">
              <form className="prepayment-action-block" onSubmit={handleCancel}>
                <div className="prepayment-action-heading">
                  <X size={15} />
                  <strong>취소</strong>
                </div>
                <textarea
                  disabled={!data.actions.canCancel || actionDisabled}
                  onChange={(event) => {
                    setCancelReason(event.target.value);
                    setActionError('');
                    setActionMessage('');
                  }}
                  placeholder="취소 사유"
                  value={cancelReason}
                />
                <button className="route-secondary-action" disabled={!data.actions.canCancel || actionDisabled} type="submit">
                  {actionBusy === 'cancel' ? <Loader2 className="spin-icon" size={15} /> : <X size={15} />}
                  취소 처리
                </button>
              </form>

              <form className="prepayment-action-block" onSubmit={handleTransfer}>
                <div className="prepayment-action-heading">
                  <ArrowRightLeft size={15} />
                  <strong>이관</strong>
                </div>
                <select
                  disabled={!data.actions.canTransfer || actionDisabled || data.actions.transferUsers.length === 0}
                  onChange={(event) => {
                    setTransferUserId(event.target.value);
                    setActionError('');
                    setActionMessage('');
                  }}
                  value={transferUserId}
                >
                  {data.actions.transferUsers.length === 0 ? (
                    <option value="">대상 없음</option>
                  ) : (
                    data.actions.transferUsers.map((user) => (
                      <option key={user.id} value={user.id}>{user.name}</option>
                    ))
                  )}
                </select>
                <textarea
                  disabled={!data.actions.canTransfer || actionDisabled || data.actions.transferUsers.length === 0}
                  onChange={(event) => {
                    setTransferReason(event.target.value);
                    setActionError('');
                    setActionMessage('');
                  }}
                  placeholder="이관 사유"
                  value={transferReason}
                />
                <button
                  className="route-secondary-action"
                  disabled={!data.actions.canTransfer || !transferUserId || data.actions.transferUsers.length === 0 || actionDisabled}
                  type="submit"
                >
                  {actionBusy === 'transfer' ? <Loader2 className="spin-icon" size={15} /> : <ArrowRightLeft size={15} />}
                  이관
                </button>
              </form>

              <form className="prepayment-action-block danger" onSubmit={handleDelete}>
                <div className="prepayment-action-heading">
                  <Trash2 size={15} />
                  <strong>삭제</strong>
                </div>
                {data.actions.deleteMessage ? <small>{data.actions.deleteMessage}</small> : null}
                <input
                  disabled={!data.actions.canDelete || actionDisabled}
                  onChange={(event) => {
                    setDeleteConfirm(event.target.value);
                    setActionError('');
                    setActionMessage('');
                  }}
                  placeholder="삭제"
                  value={deleteConfirm}
                />
                <button className="prepayment-danger-button" disabled={!data.actions.canDelete || !deleteConfirmed || actionDisabled} type="submit">
                  {actionBusy === 'delete' ? <Loader2 className="spin-icon" size={15} /> : <Trash2 size={15} />}
                  삭제
                </button>
              </form>
            </div>
          )}
          <div className="customers-side-actions">
            {prepayment.customerHref ? <a href={prepayment.customerHref}>고객 상세</a> : null}
            {prepayment.customerPrepaymentHref ? <a href={prepayment.customerPrepaymentHref}>계정별 선결제</a> : null}
          </div>
        </aside>
      </div>
    </section>
  );
}