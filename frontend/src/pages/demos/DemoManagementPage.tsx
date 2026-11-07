import { type FormEvent } from 'react';
import {
    Activity,
    AlertTriangle,
    Archive,
    Check,
    CheckCircle2,
    Loader2,
    Plus,
    Search,
    ShieldCheck,
    X
} from 'lucide-react';
import {
    DemoAccountOption,
    DemoRecordItem,
    DemoRecordsData,
    ProductOption
} from '../../api';
import { DashboardMetricCard } from '../../components/shared/DashboardMetricCard';
import { DashboardEmpty } from '../../components/shared/FeedbackStates';
import {
    formatDateLabel,
    formatNumber
} from '../../components/shared/formatters';
import { DemoRecordFormState, DemoStatusBadge, SearchableSelect, SearchableSelectOption, joinOptionParts } from '../shared/appShared';


function makeDemoAccountSelectOption(account: DemoAccountOption): SearchableSelectOption {
  const contactNames = account.contacts.map((contact) => contact.name).filter(Boolean).slice(0, 4).join(', ');
  return {
    value: String(account.departmentId),
    label: account.label || joinOptionParts([account.companyName, account.departmentName]),
    meta: joinOptionParts([`${account.contactCount}명`, contactNames]),
    searchText: [account.searchText, account.companyName, account.departmentName, contactNames].filter(Boolean).join(' '),
  };
}

function makeProductSelectOption(product: ProductOption): SearchableSelectOption {
  const meta = joinOptionParts([product.specification, product.unit, product.description]);
  return {
    value: String(product.id),
    label: product.productCode || product.name || `제품 #${product.id}`,
    meta,
    searchText: [product.productCode, product.name, product.specification, product.description].filter(Boolean).join(' '),
  };
}

function DemoRecordFormPanel({
  data,
  editingId,
  form,
  open,
  saving,
  onClose,
  onFormChange,
  onSubmit,
}: {
  data: DemoRecordsData;
  editingId: number | null;
  form: DemoRecordFormState;
  open: boolean;
  saving: boolean;
  onClose: () => void;
  onFormChange: (updater: (form: DemoRecordFormState) => DemoRecordFormState) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  if (!open) {
    return null;
  }

  const selectedAccount = data.options.accounts.find((account) => String(account.departmentId) === form.departmentId) || null;
  const contactOptions = selectedAccount?.contacts ?? [];

  return (
    <section className="dashboard-panel demo-form-panel">
      <div className="dashboard-panel-heading">
        <div>
          <span className="eyebrow">Demo form</span>
          <h2>{editingId ? '데모 기록 수정' : '데모 등록'}</h2>
        </div>
        <button className="route-secondary-action icon-only" onClick={onClose} type="button" aria-label="닫기">
          <X size={16} />
        </button>
      </div>
      <form className="notes-create-form demo-record-form" onSubmit={onSubmit}>
        <div className="notes-create-grid demo-form-grid">
          <div className="form-field demo-field-account">
            <span>부서/연구실</span>
            <SearchableSelect
              ariaLabel="데모 계정 선택"
              onChange={(value) => onFormChange((current) => ({
                ...current,
                departmentId: value,
                customerId: '',
              }))}
              options={data.options.accounts.map(makeDemoAccountSelectOption)}
              placeholder="업체, 부서, 연구원 이름으로 검색"
              value={form.departmentId}
            />
          </div>
          <label>
            <span>고객</span>
            <select
              disabled={!selectedAccount || contactOptions.length === 0}
              onChange={(event) => onFormChange((current) => ({ ...current, customerId: event.target.value }))}
              value={form.customerId}
            >
              <option value="">부서에만 연결</option>
              {contactOptions.map((contact) => (
                <option key={contact.id} value={contact.id}>{contact.name} · {contact.ownerName}</option>
              ))}
            </select>
          </label>
          <label>
            <span>제품</span>
            <SearchableSelect
              ariaLabel="데모 제품 선택"
              onChange={(value) => onFormChange((current) => ({ ...current, productId: value, productName: '' }))}
              options={data.options.products.map(makeProductSelectOption)}
              placeholder="제품 코드/규격 검색"
              value={form.productId}
            />
          </label>
          <label>
            <span>수량</span>
            <input
              min="1"
              onChange={(event) => onFormChange((current) => ({ ...current, quantity: event.target.value }))}
              type="number"
              value={form.quantity}
            />
          </label>
          <label>
            <span>상태</span>
            <select
              onChange={(event) => onFormChange((current) => ({ ...current, status: event.target.value }))}
              value={form.status}
            >
              {data.options.statuses.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>
          <label>
            <span>시작일</span>
            <input
              onChange={(event) => onFormChange((current) => ({ ...current, startDate: event.target.value }))}
              type="date"
              value={form.startDate}
            />
          </label>
          <label>
            <span>반납 예정일</span>
            <input
              onChange={(event) => onFormChange((current) => ({ ...current, expectedReturnDate: event.target.value }))}
              type="date"
              value={form.expectedReturnDate}
            />
          </label>
          <label>
            <span>회수일</span>
            <input
              onChange={(event) => onFormChange((current) => ({ ...current, returnedDate: event.target.value }))}
              type="date"
              value={form.returnedDate}
            />
          </label>
          <label>
            <span>담당자</span>
            <select
              onChange={(event) => onFormChange((current) => ({ ...current, ownerId: event.target.value }))}
              value={form.ownerId}
            >
              <option value="">현재 사용자</option>
              {data.options.owners.map((owner) => (
                <option key={owner.id} value={owner.id}>{owner.name}</option>
              ))}
            </select>
          </label>
          <label>
            <span>시리얼/식별번호</span>
            <input
              onChange={(event) => onFormChange((current) => ({ ...current, serialNumber: event.target.value }))}
              placeholder="선택 입력"
              value={form.serialNumber}
            />
          </label>
          <label className="demo-field-wide">
            <span>메모</span>
            <textarea
              onChange={(event) => onFormChange((current) => ({ ...current, notes: event.target.value }))}
              placeholder="데모 조건, 설치 위치, 회수 메모"
              rows={3}
              value={form.notes}
            />
          </label>
        </div>
        <div className="notes-create-actions demo-form-actions">
          <button className="route-secondary-action" onClick={onClose} type="button">취소</button>
          <button className="route-primary-action" disabled={saving} type="submit">
            {saving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
            저장
          </button>
        </div>
      </form>
    </section>
  );
}

function DemoRecordsTable({
  demos,
  order,
  sort,
  saving,
  onDelete,
  onEdit,
  onSort,
}: {
  demos: DemoRecordItem[];
  order: string;
  sort: string;
  saving: boolean;
  onDelete: (record: DemoRecordItem) => void;
  onEdit: (record: DemoRecordItem) => void;
  onSort: (key: string) => void;
}) {
  if (demos.length === 0) {
    return <DashboardEmpty label="조건에 맞는 데모 기록이 없습니다" />;
  }

  const sortLabel = (key: string) => (sort === key ? (order === 'asc' ? '↑' : '↓') : '');
  return (
    <div className="customers-table-wrap service-cases-table-wrap">
      <table className="customers-table service-cases-table demos-table">
        <thead>
          <tr>
            <th><button className={`product-sort-button ${sort === 'account' ? 'active' : ''}`.trim()} onClick={() => onSort('account')} type="button">고객/계정 {sortLabel('account')}</button></th>
            <th><button className={`product-sort-button ${sort === 'product' ? 'active' : ''}`.trim()} onClick={() => onSort('product')} type="button">제품 {sortLabel('product')}</button></th>
            <th><button className={`product-sort-button ${sort === 'status' ? 'active' : ''}`.trim()} onClick={() => onSort('status')} type="button">상태 {sortLabel('status')}</button></th>
            <th><button className={`product-sort-button ${sort === 'expectedReturnDate' ? 'active' : ''}`.trim()} onClick={() => onSort('expectedReturnDate')} type="button">기간 {sortLabel('expectedReturnDate')}</button></th>
            <th>담당/메모</th>
            <th>관리</th>
          </tr>
        </thead>
        <tbody>
          {demos.map((record) => (
            <tr key={record.id}>
              <td>
                <a className="customer-name-link" href={record.customerHref || record.accountHref || '/customers/'}>
                  <strong>{record.customerName || '담당자 없음'}</strong>
                  <span>{[record.companyName, record.departmentName].filter(Boolean).join(' · ')}</span>
                </a>
                <div className="notes-row-actions">
                  {record.accountHref ? <a className="customer-row-action" href={record.accountHref}>계정</a> : null}
                  {record.customerHref ? <a className="customer-row-action" href={record.customerHref}>고객</a> : null}
                </div>
              </td>
              <td>
                <strong>{record.productName}</strong>
                <small>{record.quantity ? `${formatNumber(record.quantity)}개` : ''}</small>
                {record.serialNumber ? <small>{record.serialNumber}</small> : null}
              </td>
              <td>
                <DemoStatusBadge record={record} />
              </td>
              <td>
                <span>{record.startDate ? `시작 ${formatDateLabel(record.startDate)}` : '시작일 없음'}</span>
                {record.expectedReturnDate ? <small>예정 {formatDateLabel(record.expectedReturnDate)}</small> : null}
                {record.returnedDate ? <small>회수 {formatDateLabel(record.returnedDate)}</small> : null}
              </td>
              <td>
                <span>{record.ownerName || record.createdByName || '담당자 없음'}</span>
                {record.notes ? <small>{record.notes}</small> : null}
              </td>
              <td>
                <div className="notes-row-actions">
                  <button className="customer-row-action" disabled={!record.canManage || saving} onClick={() => onEdit(record)} type="button">수정</button>
                  <button className="customer-row-action danger" disabled={!record.canManage || saving} onClick={() => onDelete(record)} type="button">삭제</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function DemoManagementPage({
  data,
  error,
  form,
  loading,
  message,
  open,
  owner,
  product,
  query,
  saving,
  sort,
  order,
  status,
  editingId,
  onCloseForm,
  onDelete,
  onEdit,
  onFormChange,
  onOpenCreate,
  onOwnerChange,
  onProductChange,
  onQueryChange,
  onSort,
  onStatusChange,
  onSubmit,
}: {
  data: DemoRecordsData | null;
  error: string;
  form: DemoRecordFormState;
  loading: boolean;
  message: string;
  open: boolean;
  owner: string;
  product: string;
  query: string;
  saving: boolean;
  sort: string;
  order: string;
  status: string;
  editingId: number | null;
  onCloseForm: () => void;
  onDelete: (record: DemoRecordItem) => void;
  onEdit: (record: DemoRecordItem) => void;
  onFormChange: (updater: (form: DemoRecordFormState) => DemoRecordFormState) => void;
  onOpenCreate: () => void;
  onOwnerChange: (value: string) => void;
  onProductChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onSort: (key: string) => void;
  onStatusChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>데모 기록을 불러오는 중입니다</span>
      </section>
    );
  }
  if (!data) {
    return null;
  }

  const metrics = [
    { label: '전체 데모', value: `${formatNumber(data.summary.total)}건`, detail: data.scope.label, icon: Archive, tone: 'blue' as const },
    { label: '진행중', value: `${formatNumber(data.summary.active)}건`, detail: '현재 대여/설치', icon: Activity, tone: 'teal' as const },
    { label: '반납 지연', value: `${formatNumber(data.summary.overdue)}건`, detail: '예정일 경과', icon: AlertTriangle, tone: data.summary.overdue > 0 ? 'red' as const : 'green' as const },
    { label: '구매전환', value: `${formatNumber(data.summary.converted)}건`, detail: '데모 후 구매', icon: CheckCircle2, tone: 'green' as const },
  ];

  return (
    <section className="customers-page demos-page">
      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Demo management</span>
          <h2>{data.scope.label || '데모관리'}</h2>
          <p>고객/계정별 데모 제품과 반납 상태를 제품 원장과 연결해 확인합니다.</p>
        </div>
        <div className="schedules-summary-actions">
          {data.permissions.canCreate ? (
            <button className="route-primary-action" onClick={onOpenCreate} type="button">
              <Plus size={15} />
              데모 등록
            </button>
          ) : null}
          <a className="route-secondary-action" href="/products/">제품관리</a>
        </div>
      </div>

      {error ? <div className="form-status error">{error}</div> : null}
      {message ? <div className="form-status success">{message}</div> : null}
      {!data.permissions.canCreate && data.permissions.readOnlyMessage ? (
        <div className="dashboard-api-alert compact">
          <ShieldCheck size={16} />
          <span>{data.permissions.readOnlyMessage}</span>
        </div>
      ) : null}

      <DemoRecordFormPanel
        data={data}
        editingId={editingId}
        form={form}
        open={open}
        saving={saving}
        onClose={onCloseForm}
        onFormChange={onFormChange}
        onSubmit={onSubmit}
      />

      <section className="dashboard-metric-grid customers-metric-grid" aria-label="데모 핵심 지표">
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

      <div className="customers-filter-bar demos-filter-bar">
        <label className="customers-search">
          <Search size={17} />
          <input
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="고객, 부서, 제품, 시리얼 검색"
            value={query}
          />
        </label>
        <select onChange={(event) => onStatusChange(event.target.value)} value={status}>
          <option value="all">상태 전체</option>
          {data.options.statuses.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onProductChange(event.target.value)} value={product}>
          <option value="">제품 전체</option>
          {data.options.products.map((item) => (
            <option key={item.id} value={item.id}>{item.productCode}</option>
          ))}
        </select>
        <select onChange={(event) => onOwnerChange(event.target.value)} value={owner}>
          <option value="">담당자 전체</option>
          {data.options.owners.map((item) => (
            <option key={item.id} value={item.id}>{item.name}</option>
          ))}
        </select>
      </div>

      <section className="dashboard-panel services-main-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Demo list</span>
            <h2>데모 현황</h2>
          </div>
          {loading ? <Loader2 className="spin-icon" size={18} /> : <Archive size={18} />}
        </div>
        <DemoRecordsTable
          demos={data.demos}
          order={order}
          saving={saving}
          sort={sort}
          onDelete={onDelete}
          onEdit={onEdit}
          onSort={onSort}
        />
      </section>
    </section>
  );
}