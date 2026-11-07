import { useEffect, useRef, useState, type FormEvent } from 'react';
import {
    AlertTriangle,
    Archive,
    Building2,
    CalendarDays,
    Check,
    CheckCircle2,
    ChevronLeft,
    ChevronRight,
    CircleDollarSign,
    Clock,
    Download,
    FileSpreadsheet,
    FileText,
    ListChecks,
    Loader2,
    MoveUpRight,
    Pencil,
    Plus,
    Search,
    ShieldCheck,
    Target,
    Trash2,
    Upload,
    Users
} from 'lucide-react';
import {
    ScheduleDeliveryItem
} from '../../api';
import type {
    AccountContactPayload,
    AccountInfoUpdatePayload,
    CustomerAccountContact,
    CustomerAttachmentItem,
    CustomerDeliveryRecord,
    CustomerDetailData,
    CustomerEditPayload,
    CustomerItem,
    CustomerQuoteRecord,
    CustomerRowMode,
    CustomerServiceRecord,
    CustomersData,
} from '../../api/accounts';
import {
    deleteCustomer as deleteCustomerRecord,
    saveAccountContact,
    updateAccountInfo,
    updateCustomer as updateCustomerRecord
} from '../../api/accounts';
import type {
    PrepaymentListItem
} from '../../api/prepayments';
import { AttachmentManager } from '../../components/shared/AttachmentManager';
import { DashboardMetricCard } from '../../components/shared/DashboardMetricCard';
import { DashboardApiAlert, DashboardEmpty } from '../../components/shared/FeedbackStates';
import {
    formatDateLabel,
    formatDateTimeLabel,
    formatNumber,
    formatWon
} from '../../components/shared/formatters';
import { CustomerDetailNoteList, DemoStatusBadge, PrepaymentStatusBadge, SchedulesCompactList, SearchableSelect, SearchableSelectOption, makeDepartmentSelectOption, useGuidedPanelFocus } from '../shared/appShared';


type CustomerDetailMode = 'customer' | 'account';



type CustomerEditFormState = {
  address: string;
  companyId: string;
  customerName: string;
  departmentId: string;
  email: string;
  manager: string;
  notes: string;
  phoneNumber: string;
  pipelineStage: string;
  status: string;
};

type AccountInfoFormState = {
  address: string;
  companyId: string;
  departmentName: string;
  notes: string;
};

type AccountContactFormState = {
  address: string;
  contactRole: string;
  customerName: string;
  departmentId: string;
  email: string;
  isActive: boolean;
  manager: string;
  notes: string;
  phoneNumber: string;
  pipelineStage: string;
  status: string;
};

type AccountContactEditorMode = '' | 'create' | 'edit';


const makeCustomerEditForm = (customer: CustomerItem | null): CustomerEditFormState => ({
  address: customer?.address || '',
  companyId: customer?.companyId ? String(customer.companyId) : '',
  customerName: customer?.customer || '',
  departmentId: customer?.departmentId ? String(customer.departmentId) : '',
  email: customer?.email || '',
  manager: customer?.manager || '',
  notes: customer?.notesFull || customer?.notes || '',
  phoneNumber: customer?.phone || '',
  pipelineStage: customer?.pipelineStage || 'potential',
  status: customer?.status || 'active',
});

const makeAccountInfoForm = (data?: CustomerDetailData | null): AccountInfoFormState => ({
  address: data?.account.address || '',
  companyId: data?.account.companyId ? String(data.account.companyId) : '',
  departmentName: data?.account.departmentName || data?.account.name || '',
  notes: data?.account.notes || '',
});

const makeAccountContactForm = (
  data?: CustomerDetailData | null,
  contact?: CustomerAccountContact | null,
): AccountContactFormState => {
  const management = data?.account.management;
  return {
    address: contact?.address || '',
    contactRole: contact?.contactRole || management?.contactRoles[0]?.value || 'practitioner',
    customerName: contact?.name || '',
    departmentId: String(data?.account.departmentId || ''),
    email: contact?.email || '',
    isActive: contact?.isActive ?? true,
    manager: contact?.manager || '',
    notes: contact?.notesFull || contact?.notes || '',
    phoneNumber: contact?.phone || '',
    pipelineStage: contact?.pipelineStage || management?.stages[0]?.value || 'potential',
    status: contact?.status || management?.statuses[0]?.value || 'active',
  };
};

const accountInfoFormToPayload = (form: AccountInfoFormState): { payload: AccountInfoUpdatePayload | null; error: string } => {
  const companyId = Number(form.companyId);
  if (!companyId) {
    return { payload: null, error: '업체/학교를 선택하세요.' };
  }
  if (!form.departmentName.trim()) {
    return { payload: null, error: '부서/연구실명을 입력하세요.' };
  }
  return {
    payload: {
      address: form.address.trim() || undefined,
      companyId,
      departmentName: form.departmentName.trim(),
      notes: form.notes.trim() || undefined,
    },
    error: '',
  };
};

const accountContactFormToPayload = (form: AccountContactFormState): { payload: AccountContactPayload | null; error: string } => {
  const departmentId = Number(form.departmentId);
  if (!departmentId) {
    return { payload: null, error: '부서/연구실을 선택하세요.' };
  }
  if (!form.customerName.trim()) {
    return { payload: null, error: '담당자명을 입력하세요.' };
  }
  return {
    payload: {
      address: form.address.trim() || undefined,
      contactRole: form.contactRole || 'practitioner',
      customerName: form.customerName.trim(),
      departmentId,
      email: form.email.trim() || undefined,
      isActive: form.isActive,
      manager: form.manager.trim() || undefined,
      notes: form.notes.trim() || undefined,
      phoneNumber: form.phoneNumber.trim() || undefined,
      pipelineStage: form.pipelineStage || 'potential',
      status: form.status || 'active',
    },
    error: '',
  };
};

function makeCompanySelectOption(company: { id: number; name: string }): SearchableSelectOption {
  return {
    value: String(company.id),
    label: company.name,
    searchText: company.name,
  };
}

function CustomerStatusBadge({ customer }: { customer: CustomerItem }) {
  return (
    <div className="customer-badge-row">
      <span>{customer.pipelineLabel}</span>
      {customer.grade ? <span>{customer.grade}</span> : null}
    </div>
  );
}

function CustomersTable({ customers, emptyLabel = '조건에 맞는 계정이 없습니다' }: { customers: CustomerItem[]; emptyLabel?: string }) {
  if (customers.length === 0) {
    return <DashboardEmpty label={emptyLabel} />;
  }

  return (
    <div className="customers-table-wrap">
      <table className="customers-table">
        <thead>
          <tr>
            <th>계정</th>
            <th>상태</th>
            <th>후속</th>
            <th>예정 일정</th>
            <th>활동</th>
            <th>영업/담당자</th>
          </tr>
        </thead>
        <tbody>
          {customers.map((customer) => (
            <tr key={`${customer.accountType || 'customer'}-${customer.id}`}>
              <td>
                <a className="customer-name-link" href={customer.href}>
                  <strong>{customer.company || customer.customer}</strong>
                  <span>{[
                    customer.department || customer.customer,
                    customer.contactCount ? `담당자 ${formatNumber(customer.contactCount)}명` : '',
                  ].filter(Boolean).join(' · ')}</span>
                  {customer.contactSummary ? <small className="customer-contact-line">{customer.contactSummary}</small> : null}
                  {!customer.contactSummary && customer.notes ? <small className="customer-contact-line">{customer.notes}</small> : null}
                </a>
              </td>
              <td>
                <CustomerStatusBadge customer={customer} />
              </td>
              <td>
                <span className={customer.overdue ? 'customer-overdue-text' : ''}>
                  {customer.nextAction || '다음 액션 없음'}
                </span>
                {customer.nextActionDate ? <small>{formatDateLabel(customer.nextActionDate)}</small> : null}
              </td>
              <td>
                {customer.upcomingSchedule ? (
                  <a className="customer-schedule-link" href={customer.upcomingSchedule.href}>
                    <strong>
                      {formatDateLabel(customer.upcomingSchedule.date)}
                      {customer.upcomingSchedule.time ? ` ${customer.upcomingSchedule.time}` : ''}
                    </strong>
                    <span>
                      {[customer.upcomingSchedule.activityLabel, customer.upcomingSchedule.location].filter(Boolean).join(' · ')}
                    </span>
                  </a>
                ) : (
                  <span className="customer-muted-cell">예정 일정 없음</span>
                )}
              </td>
              <td>
                <div className="customer-count-grid">
                  <span>활동 <strong>{formatNumber(customer.activityCount)}</strong></span>
                  <span>일정 <strong>{formatNumber(customer.scheduleCount)}</strong></span>
                </div>
                <small>{customer.lastActivityLabel || '최근 활동 없음'}</small>
                {customer.lastActivityAt ? <small>{formatDateTimeLabel(customer.lastActivityAt)}</small> : null}
              </td>
              <td>
                <span>{customer.owner}</span>
                <div className="customer-row-actions">
                  <a className="customer-row-action" href={customer.createScheduleHref}>일정</a>
                  {customer.upcomingSchedule ? (
                    <a className="customer-row-action" href={customer.upcomingSchedule.createHistoryHref}>보고</a>
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

function CustomerAttachmentList({ files }: { files: CustomerAttachmentItem[] }) {
  return (
    <AttachmentManager
      className="customer-attachment-manager"
      emptyLabel="첨부된 파일이 없습니다"
      files={files}
      title="첨부파일"
    />
  );
}

function CustomerRecordItems({ items }: { items: ScheduleDeliveryItem[] }) {
  if (!items.length) {
    return <span className="customer-record-empty-line">품목 정보 없음</span>;
  }

  const visibleItems = items.slice(0, 3);
  const hiddenCount = Math.max(items.length - visibleItems.length, 0);

  return (
    <div className="customer-record-item-list">
      {visibleItems.map((item) => (
        <span key={`${item.id}-${item.itemName}`}>
          <strong>{item.itemName}</strong>
          <small>
            {formatNumber(item.quantity)}{item.unit || 'EA'}
            {item.totalPrice ? ` · ${formatWon(item.totalPrice)}` : ''}
          </small>
        </span>
      ))}
      {hiddenCount > 0 ? <span className="customer-record-more">외 {formatNumber(hiddenCount)}개</span> : null}
    </div>
  );
}

function CustomerDeliveryRecords({ records }: { records: CustomerDeliveryRecord[] }) {
  if (!records.length) {
    return <DashboardEmpty label="납품 기록이 없습니다" />;
  }

  return (
    <div className="customer-record-list delivery-record-list">
      {records.slice(0, 8).map((record) => (
        <article className="customer-record-row" key={record.id}>
          <div className="customer-record-main">
            <div className="customer-record-title-line">
              <span className={`customer-delivery-source ${record.paymentSource}`}>
                {record.paymentTypeLabel || record.paymentSourceLabel || '일반 납품'}
              </span>
              {record.paymentStatusLabel && record.paymentStatusLabel !== (record.paymentTypeLabel || record.paymentSourceLabel) ? (
                <span className={`customer-delivery-status ${record.paymentStatus}`}>
                  {record.paymentStatusLabel}
                </span>
              ) : null}
              <strong>{record.date ? formatDateLabel(record.date) : '납품일 없음'}</strong>
              <span>{record.statusLabel}</span>
            </div>
            <CustomerRecordItems items={record.items ?? []} />
            <small className="customer-record-context">
              {[record.customerName ? `담당자 ${record.customerName}` : '', record.ownerName ? `영업 ${record.ownerName}` : ''].filter(Boolean).join(' · ')}
            </small>
            {record.notes ? <p>{record.notes}</p> : null}
            <small>{record.paymentEvidence}</small>
          </div>
          <div className="customer-record-side">
            <strong>{formatWon(record.totalAmount || 0)}</strong>
            {record.paymentSource === 'prepayment' ? (
              <span>차감 {formatWon(record.prepaymentAmount || 0)}</span>
            ) : (
              <span>선결제 차감 없음</span>
            )}
            {record.href ? <a href={record.href}>일정</a> : null}
          </div>
        </article>
      ))}
    </div>
  );
}

function CustomerQuoteRecords({ records }: { records: CustomerQuoteRecord[] }) {
  if (!records.length) {
    return <DashboardEmpty label="견적 기록이 없습니다" />;
  }

  return (
    <div className="customer-record-list">
      {records.slice(0, 8).map((record) => (
        <article className="customer-record-row" key={`${record.recordType}-${record.id}`}>
          <div className="customer-record-main">
            <div className="customer-record-title-line">
              <strong>{record.quoteNumber || '견적 일정'}</strong>
              <span>{record.date ? formatDateLabel(record.date) : '견적일 없음'}</span>
              <span>{record.statusLabel}</span>
            </div>
            <CustomerRecordItems items={record.items ?? []} />
            <small className="customer-record-context">
              {[record.customerName ? `담당자 ${record.customerName}` : '', record.ownerName ? `영업 ${record.ownerName}` : ''].filter(Boolean).join(' · ')}
            </small>
            {record.notes ? <p>{record.notes}</p> : null}
          </div>
          <div className="customer-record-side">
            <strong>{formatWon(record.totalAmount || 0)}</strong>
            {record.validUntil ? <span>유효 {formatDateLabel(record.validUntil)}</span> : null}
            {record.href ? <a href={record.href}>일정</a> : null}
          </div>
        </article>
      ))}
    </div>
  );
}

function CustomerServiceRecords({ records }: { records: CustomerServiceRecord[] }) {
  if (!records.length) {
    return <DashboardEmpty label="서비스 기록이 없습니다" />;
  }

  return (
    <div className="customer-record-list">
      {records.slice(0, 8).map((record) => (
        <article className="customer-record-row compact" key={`${record.recordType}-${record.id}`}>
          <div className="customer-record-main">
            <div className="customer-record-title-line">
              <strong>{record.assetName || record.caseTypeLabel || '서비스 기록'}</strong>
              <span>{record.date ? formatDateLabel(record.date) : '일자 없음'}</span>
              <span>{record.statusLabel}</span>
            </div>
            <small className="customer-record-context">
              {[record.customerName ? `담당자 ${record.customerName}` : '', record.ownerName ? `접수 ${record.ownerName}` : '', record.assignedTo ? `배정 ${record.assignedTo}` : ''].filter(Boolean).join(' · ')}
            </small>
            <p>{record.summary || record.detail || '상세 내용 없음'}</p>
            <small>{[record.caseTypeLabel, record.priorityLabel, record.assignedTo || record.ownerName].filter(Boolean).join(' · ')}</small>
          </div>
          <div className="customer-record-side">
            {record.dueDate ? <span>처리기한 {formatDateLabel(record.dueDate)}</span> : null}
            {record.completedDate ? <span>완료 {formatDateLabel(record.completedDate)}</span> : null}
            {record.href ? <a href={record.href}>열기</a> : null}
          </div>
        </article>
      ))}
    </div>
  );
}

function CustomerPrepaymentRecords({ records }: { records: PrepaymentListItem[] }) {
  if (!records.length) {
    return <DashboardEmpty label="선결제 기록이 없습니다" />;
  }

  return (
    <div className="customer-record-list prepayment-record-list">
      {records.slice(0, 8).map((record) => (
        <article className="customer-record-row compact" key={record.id}>
          <div className="customer-record-main">
            <div className="customer-record-title-line">
              <strong>{record.paymentDate ? formatDateLabel(record.paymentDate) : '입금일 없음'}</strong>
              <span>{record.payerName || '입금자 미지정'}</span>
              <PrepaymentStatusBadge label={record.statusLabel} status={record.status} />
            </div>
            <small className="customer-record-context">
              {[record.customerName ? `담당자 ${record.customerName}` : '', record.ownerName ? `등록 ${record.ownerName}` : '', record.departmentName].filter(Boolean).join(' · ')}
            </small>
            {record.memo ? <p>{record.memo}</p> : null}
            <small>사용 {formatWon(record.usedAmount || 0)} · 사용내역 {formatNumber(record.usageCount || 0)}건</small>
          </div>
          <div className="customer-record-side">
            <strong>{formatWon(record.amount || 0)}</strong>
            <span>잔액 {formatWon(record.balance || 0)}</span>
            <a href={`/prepayments/${record.id}/`}>상세</a>
          </div>
        </article>
      ))}
    </div>
  );
}

export function CustomerDetailPage({
  data,
  detailMode = 'customer',
  loading,
  onRefresh,
}: {
  data: CustomerDetailData | null;
  detailMode?: CustomerDetailMode;
  loading: boolean;
  onRefresh: () => Promise<CustomerDetailData | null>;
}) {
  const customer = data?.customer ?? null;
  const [editOpen, setEditOpen] = useState(false);
  const [editForm, setEditForm] = useState<CustomerEditFormState>(() => makeCustomerEditForm(customer));
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState('');
  const [editMessage, setEditMessage] = useState('');
  const [deleteSaving, setDeleteSaving] = useState(false);
  const [deleteError, setDeleteError] = useState('');
  const [deleteMessage, setDeleteMessage] = useState('');
  const [accountInfoOpen, setAccountInfoOpen] = useState(false);
  const [accountInfoForm, setAccountInfoForm] = useState<AccountInfoFormState>(() => makeAccountInfoForm(data));
  const [accountInfoSaving, setAccountInfoSaving] = useState(false);
  const [accountInfoError, setAccountInfoError] = useState('');
  const [accountInfoMessage, setAccountInfoMessage] = useState('');
  const [accountContactEditor, setAccountContactEditor] = useState<AccountContactEditorMode>('');
  const [accountContactForm, setAccountContactForm] = useState<AccountContactFormState>(() => makeAccountContactForm(data));
  const [editingAccountContactId, setEditingAccountContactId] = useState<number | null>(null);
  const [accountContactSaving, setAccountContactSaving] = useState(false);
  const [accountContactError, setAccountContactError] = useState('');
  const [accountContactMessage, setAccountContactMessage] = useState('');
  const accountInfoPanelRef = useRef<HTMLFormElement | null>(null);
  const accountContactPanelRef = useRef<HTMLFormElement | null>(null);
  const customerEditPanelRef = useRef<HTMLElement | null>(null);

  useGuidedPanelFocus(accountInfoOpen, accountInfoPanelRef, `account-info-${data?.account.id || customer?.id || 'new'}`);
  useGuidedPanelFocus(
    Boolean(accountContactEditor),
    accountContactPanelRef,
    `${accountContactEditor || 'closed'}-${editingAccountContactId || 'new'}`,
  );
  useGuidedPanelFocus(editOpen, customerEditPanelRef, `customer-edit-${customer?.id || 'new'}`);

  useEffect(() => {
    setEditForm(makeCustomerEditForm(customer));
    setEditError('');
    setEditMessage('');
    setEditOpen(false);
    setDeleteSaving(false);
    setDeleteError('');
    setDeleteMessage('');
    setAccountInfoOpen(false);
    setAccountInfoForm(makeAccountInfoForm(data));
    setAccountInfoSaving(false);
    setAccountInfoError('');
    setAccountInfoMessage('');
    setAccountContactEditor('');
    setAccountContactForm(makeAccountContactForm(data));
    setEditingAccountContactId(null);
    setAccountContactSaving(false);
    setAccountContactError('');
    setAccountContactMessage('');
  }, [customer?.id, data?.account.id]);

  const editConfig = data?.edit;
  const editCompanies = editConfig?.companies ?? [];
  const editDepartments = editForm.companyId
    ? (editConfig?.departments ?? []).filter((department) => String(department.companyId) === editForm.companyId)
    : editConfig?.departments ?? [];
  const accountManagement = data?.account.management;
  const accountInfoCompanies = accountManagement?.companies ?? [];
  const accountInfoDepartments = accountInfoForm.companyId
    ? (accountManagement?.departments ?? []).filter((department) => String(department.companyId) === accountInfoForm.companyId)
    : accountManagement?.departments ?? [];
  const contactTargetDepartments = accountManagement?.departments ?? [];

  const handleEditFieldChange = (field: keyof CustomerEditFormState, value: string) => {
    setEditForm((previous) => {
      const next = {
        ...previous,
        [field]: value,
      };
      if (field === 'companyId') {
        const firstDepartment = (editConfig?.departments ?? []).find(
          (department) => String(department.companyId) === value,
        );
        next.departmentId = firstDepartment ? String(firstDepartment.id) : '';
      }
      return next;
    });
    setEditError('');
    setEditMessage('');
  };

  const handleEditSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!customer || !editConfig || editSaving) {
      return;
    }
    if (!editConfig.canEdit) {
      setEditError(editConfig.message || '수정 권한이 없습니다.');
      return;
    }
    const companyId = Number(editForm.companyId);
    const departmentId = Number(editForm.departmentId);
    if (!companyId) {
      setEditError('업체/학교를 선택하세요.');
      return;
    }
    if (!departmentId) {
      setEditError('부서/연구실을 선택하세요.');
      return;
    }
    if (!editForm.customerName.trim()) {
      setEditError('고객명을 입력하세요.');
      return;
    }
    const payload: CustomerEditPayload = {
      address: editForm.address.trim() || undefined,
      companyId,
      customerName: editForm.customerName.trim(),
      departmentId,
      email: editForm.email.trim() || undefined,
      manager: editForm.manager.trim() || undefined,
      notes: editForm.notes.trim() || undefined,
      phoneNumber: editForm.phoneNumber.trim() || undefined,
      pipelineStage: editForm.pipelineStage,
      status: editForm.status,
    };

    setEditSaving(true);
    setEditError('');
    setEditMessage('');
    try {
      const updated = await updateCustomerRecord(payload, editConfig.submitUrl);
      await onRefresh();
      setEditMessage(updated.message || '고객 정보를 수정했습니다.');
      setEditOpen(false);
    } catch (error) {
      setEditError(error instanceof Error ? error.message : '고객 정보 수정에 실패했습니다.');
    } finally {
      setEditSaving(false);
    }
  };

  const handleCustomerDelete = async () => {
    if (!customer || !editConfig || deleteSaving) {
      return;
    }
    if (!editConfig.canDelete || !editConfig.deleteUrl) {
      setDeleteError(editConfig.message || '삭제 권한이 없습니다.');
      setDeleteMessage('');
      return;
    }
    const label = customer.customer || '고객';
    if (!window.confirm(`"${label}" 고객 정보를 삭제할까요?\n연결된 일정, 영업노트, 파일 기록도 함께 삭제될 수 있습니다.`)) {
      return;
    }

    setDeleteSaving(true);
    setDeleteError('');
    setDeleteMessage('');
    try {
      const result = await deleteCustomerRecord(editConfig.deleteUrl);
      setDeleteMessage(result.message || '고객 정보를 삭제했습니다.');
      window.location.href = result.href || data?.links.customers || '/customers/';
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : '고객 삭제에 실패했습니다.');
    } finally {
      setDeleteSaving(false);
    }
  };

  const handleAccountInfoFieldChange = (field: keyof AccountInfoFormState, value: string) => {
    setAccountInfoForm((previous) => {
      return {
        ...previous,
        [field]: value,
      };
    });
    setAccountInfoError('');
    setAccountInfoMessage('');
  };

  const handleAccountInfoSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!accountManagement?.canManage || accountInfoSaving) {
      setAccountInfoError(accountManagement?.message || '계정 관리 권한이 없습니다.');
      return;
    }
    if (!accountManagement.accountSubmitUrl) {
      setAccountInfoError('계정 저장 API가 준비되지 않았습니다.');
      return;
    }
    const { payload, error } = accountInfoFormToPayload(accountInfoForm);
    if (!payload || error) {
      setAccountInfoError(error || '계정 정보를 확인하세요.');
      return;
    }

    setAccountInfoSaving(true);
    setAccountInfoError('');
    setAccountInfoMessage('');
    try {
      const result = await updateAccountInfo(payload, accountManagement.accountSubmitUrl);
      await onRefresh();
      setAccountInfoMessage(result.message || '계정 정보를 저장했습니다.');
      setAccountInfoOpen(false);
    } catch (error) {
      setAccountInfoError(error instanceof Error ? error.message : '계정 정보 저장에 실패했습니다.');
    } finally {
      setAccountInfoSaving(false);
    }
  };

  const resetAccountContactFeedback = () => {
    setAccountContactError('');
    setAccountContactMessage('');
  };

  const handleAccountContactFieldChange = (field: keyof AccountContactFormState, value: string | boolean) => {
    setAccountContactForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    resetAccountContactFeedback();
  };

  const openAccountContactCreate = () => {
    setEditingAccountContactId(null);
    setAccountContactForm(makeAccountContactForm(data));
    setAccountContactEditor('create');
    resetAccountContactFeedback();
  };

  const openAccountContactEdit = (contact: CustomerAccountContact) => {
    if (!contact.canManage) {
      setAccountContactError(contact.manageMessage || '이 담당자 수정 권한이 없습니다.');
      setAccountContactMessage('');
      return;
    }
    setEditingAccountContactId(contact.id);
    setAccountContactForm(makeAccountContactForm(data, contact));
    setAccountContactEditor('edit');
    resetAccountContactFeedback();
  };

  const handleAccountContactSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!accountManagement?.canManage || accountContactSaving) {
      setAccountContactError(accountManagement?.message || '담당자 관리 권한이 없습니다.');
      return;
    }
    const editingContact = data?.account.contacts.find((contact) => contact.id === editingAccountContactId) ?? null;
    const submitUrl = editingContact ? editingContact.updateUrl : accountManagement.contactCreateUrl;
    if (!submitUrl) {
      setAccountContactError('담당자 저장 API가 준비되지 않았습니다.');
      return;
    }
    const { payload, error } = accountContactFormToPayload(accountContactForm);
    if (!payload || error) {
      setAccountContactError(error || '담당자 정보를 확인하세요.');
      return;
    }

    setAccountContactSaving(true);
    resetAccountContactFeedback();
    try {
      const result = await saveAccountContact(payload, submitUrl);
      await onRefresh();
      setAccountContactMessage(result.message || '담당자 정보를 저장했습니다.');
      setAccountContactEditor('');
      setEditingAccountContactId(null);
    } catch (error) {
      setAccountContactError(error instanceof Error ? error.message : '담당자 저장에 실패했습니다.');
    } finally {
      setAccountContactSaving(false);
    }
  };

  const toggleAccountContactActive = async (contact: CustomerAccountContact, isActive: boolean) => {
    if (!contact.canManage || !contact.updateUrl || accountContactSaving) {
      setAccountContactError(contact.manageMessage || '이 담당자 수정 권한이 없습니다.');
      setAccountContactMessage('');
      return;
    }
    const payload = accountContactFormToPayload({
      ...makeAccountContactForm(data, contact),
      isActive,
    }).payload;
    if (!payload) {
      setAccountContactError('담당자 정보를 확인하세요.');
      setAccountContactMessage('');
      return;
    }
    setAccountContactSaving(true);
    resetAccountContactFeedback();
    try {
      const result = await saveAccountContact(payload, contact.updateUrl);
      await onRefresh();
      setAccountContactMessage(result.message || (isActive ? '담당자를 활성화했습니다.' : '담당자를 비활성화했습니다.'));
    } catch (error) {
      setAccountContactError(error instanceof Error ? error.message : '담당자 상태 변경에 실패했습니다.');
    } finally {
      setAccountContactSaving(false);
    }
  };

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>고객 상세 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data || !data.customer) {
    return (
      <section className="customers-page">
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>고객 상세를 불러오지 못했습니다</strong>
            <span>{data?.error || '고객 상세 정보를 불러오지 못했습니다.'}</span>
          </div>
          <a href="/customers/">목록</a>
        </div>
      </section>
    );
  }

  const customerDetail = data.customer;
  const prepaymentSummary = data.prepaymentSummary;
  const operationalRecords = data.operationalRecords;
  const demoSummary = data.demoSummary;
  const attachments = data.attachments;
  const account = data.account;
  const isAccountDetail = detailMode === 'account';
  const canCreateNote = data.permissions.canCreateNote && Boolean(data.links.createNote);
  const canCreateSchedule = data.permissions.canCreateSchedule && Boolean(data.links.createSchedule);
  const canEditRepresentative = data.permissions.canEditRepresentative && data.edit.canEdit && !isAccountDetail;
  const canDeleteRepresentative = data.permissions.canDeleteRepresentative && data.edit.canDelete && !isAccountDetail;
  const accountContacts = account.contacts ?? [];
  const ledgerScopeLabel = account.ledgerScopeLabel || (
    account.type === 'department' ? '부서/연구실 계정 공유 원장' : '담당자 단일 원장'
  );
  const ledgerScopeDescription = account.ledgerScopeDescription || (
    account.type === 'department'
      ? '같은 업체/부서/연구실 담당자의 납품, 견적, 선결제, 서비스 기록을 함께 집계합니다.'
      : '부서/연구실 연결이 없어 이 담당자에게 연결된 기록만 집계합니다.'
  );
  const prepaymentScopeHref = prepaymentSummary.links.accountPrepayments
    || prepaymentSummary.links.customerPrepayments
    || prepaymentSummary.links.djangoCustomerPrepayments;
  const prepaymentScopeLabel = account.type === 'department' ? '계정 선결제' : '고객별 선결제';
  const accountContactPreview = accountContacts
    .map((contact) => contact.name)
    .filter(Boolean)
    .slice(0, 4)
    .join(', ');
  const accountAddress = account.address || customerDetail.address || '';
  const accountNotes = account.notes || customerDetail.notesFull || customerDetail.notes || '';
  const metrics = [
    { label: '최근 노트', value: `${formatNumber(data.metrics.recentNotes)}건`, detail: data.scope.label, icon: FileText, tone: 'blue' as const },
    { label: '예정 일정', value: `${formatNumber(data.metrics.upcomingSchedules)}건`, detail: '진행 예정', icon: CalendarDays, tone: 'green' as const },
    { label: '14일 내 후속', value: `${formatNumber(data.metrics.upcomingActions)}건`, detail: '예정 액션', icon: Clock, tone: 'teal' as const },
  ];
  const demoMetrics = [
    { label: '전체 데모', value: `${formatNumber(demoSummary.metrics.total)}건` },
    { label: '진행중', value: `${formatNumber(demoSummary.metrics.active)}건` },
    { label: '반납 지연', value: `${formatNumber(demoSummary.metrics.overdue)}건` },
    { label: '구매전환', value: `${formatNumber(demoSummary.metrics.converted)}건` },
  ];
  const operationalMetrics = [
    { label: '납품', value: `${formatNumber(operationalRecords.metrics.deliveryRecords)}건` },
    { label: '선결제 차감 납품', value: `${formatNumber(operationalRecords.metrics.prepaymentDeliveryRecords)}건` },
    { label: '일반 납품', value: `${formatNumber(operationalRecords.metrics.normalDeliveryRecords)}건` },
    { label: '견적', value: `${formatNumber(operationalRecords.metrics.quoteRecords)}건` },
    { label: '선결제 기록', value: `${formatNumber(operationalRecords.metrics.prepaymentRecords)}건` },
    { label: '서비스', value: `${formatNumber(operationalRecords.metrics.serviceRecords)}건` },
  ];
  const ledgerCards = [
    {
      label: '원장 범위',
      value: ledgerScopeLabel,
      detail: ledgerScopeDescription,
    },
    {
      label: '공유 담당자',
      value: `${formatNumber(account.contactCount || accountContacts.length)}명`,
      detail: accountContactPreview || '담당자 없음',
    },
    {
      label: '납품 구분',
      value: `선결제 ${formatNumber(operationalRecords.metrics.prepaymentDeliveryRecords)}건 / 일반 ${formatNumber(operationalRecords.metrics.normalDeliveryRecords)}건`,
      detail: '구조화 선결제 사용 기록 기준',
    },
  ];
  const customerProfileFields = [
    { label: '업체/학교', value: account.companyName || customerDetail.company },
    { label: '부서/연구실', value: account.departmentName || customerDetail.department },
    { label: 'PI', value: account.piContactName || '-' },
    { label: '대표 담당자', value: account.representativeName || customerDetail.customer },
    { label: '계정 담당자 수', value: account.contactCount ? `${formatNumber(account.contactCount)}명` : '' },
    { label: '활성/비활성', value: `${formatNumber(account.activeContactCount || account.contactCount)}명 / ${formatNumber(account.inactiveContactCount)}명` },
    { label: '영업 담당자', value: customerDetail.owner },
    { label: '책임자', value: customerDetail.manager },
    { label: '전화번호', value: customerDetail.phone },
    { label: '이메일', value: customerDetail.email },
    { label: '파이프라인', value: customerDetail.pipelineLabel },
  ];
  const customerDetailNotes = accountNotes;

  return (
    <section className="customers-page customer-detail-page">
      {data.source !== 'django' ? (
        <DashboardApiAlert message={data.error} title="고객 상세 정보를 불러오지 못했습니다" />
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Department account</span>
          <h2>{[account.companyName || customerDetail.company, account.departmentName || customerDetail.department].filter(Boolean).join(' · ') || account.name || customerDetail.customer}</h2>
          <p>{[account.representativeName || customerDetail.customer, account.contactCount ? `담당자 ${formatNumber(account.contactCount)}명` : '', data.scope.label].filter(Boolean).join(' · ')}</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href="/customers/">{isAccountDetail ? '계정 목록' : '목록'}</a>
          {!isAccountDetail && data.links.accountDetail ? (
            <a className="route-secondary-action" href={data.links.accountDetail}>계정 링크</a>
          ) : null}
          {data.links.pipeline ? (
            <a className="route-secondary-action" href={data.links.pipeline}>
              <Target size={15} />
              파이프라인
            </a>
          ) : null}
          {accountManagement?.canManage ? (
            <>
              <button className="route-secondary-action" onClick={() => setAccountInfoOpen((open) => !open)} type="button">
                <Pencil size={15} />
                계정 관리
              </button>
              <button className="route-secondary-action" onClick={openAccountContactCreate} type="button">
                <Plus size={15} />
                담당자 추가
              </button>
            </>
          ) : null}
          {canEditRepresentative ? (
            <button className="route-secondary-action" onClick={() => setEditOpen((open) => !open)} type="button">
              담당자 수정
            </button>
          ) : null}
          {canDeleteRepresentative && data.edit.deleteUrl ? (
            <button className="route-secondary-action danger" disabled={deleteSaving} onClick={handleCustomerDelete} type="button">
              {deleteSaving ? <Loader2 className="spin-icon" size={15} /> : <Trash2 size={15} />}
              담당자 삭제
            </button>
          ) : null}
          {canCreateNote ? (
            <a className="route-secondary-action" href={data.links.createNote}>
              노트 작성
              <FileText size={16} />
            </a>
          ) : null}
          {canCreateSchedule ? (
            <a className="route-primary-action" href={data.links.createSchedule}>
              일정 등록
              <Plus size={16} />
            </a>
          ) : null}
        </div>
      </div>

      {isAccountDetail && data.permissions.readOnlyMessage && !accountManagement?.canManage ? (
        <div className="dashboard-api-alert compact">
          <ShieldCheck size={16} />
          <span>{data.permissions.readOnlyMessage}</span>
        </div>
      ) : null}

      {deleteError ? (
        <div className="dashboard-api-alert compact">
          <AlertTriangle size={16} />
          <span>{deleteError}</span>
        </div>
      ) : null}
      {deleteMessage ? (
        <div className="dashboard-api-alert compact success">
          <CheckCircle2 size={16} />
          <span>{deleteMessage}</span>
        </div>
      ) : null}

      <div className="customer-account-ledger-strip">
        {ledgerCards.map((item) => (
          <div key={item.label}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
            <small>{item.detail}</small>
          </div>
        ))}
      </div>

      <section className="dashboard-metric-grid customers-metric-grid" aria-label="고객 상세 지표">
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

      <section className="dashboard-panel customer-profile-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Customer profile</span>
            <h2>부서/연구실 계정 정보</h2>
          </div>
          <Building2 size={18} />
        </div>
        <dl className="customer-profile-grid">
          {customerProfileFields.map((field) => (
            <div key={field.label}>
              <dt>{field.label}</dt>
              <dd>{field.value || '-'}</dd>
            </div>
          ))}
        </dl>
        <div className="customer-profile-text-grid">
          <article className={`customer-profile-text ${accountAddress ? '' : 'empty'}`}>
            <span>계정 주소</span>
            <p>{accountAddress || '등록된 주소 없음'}</p>
          </article>
          <article className={`customer-profile-text ${customerDetailNotes ? '' : 'empty'}`}>
            <span>계정 메모</span>
            <p>{customerDetailNotes || '등록된 상세 내용 없음'}</p>
          </article>
        </div>
        {accountManagement && !accountManagement.canManage && accountManagement.message ? (
          <div className="dashboard-api-alert compact">
            <AlertTriangle size={16} />
            <span>{accountManagement.message}</span>
          </div>
        ) : null}
        {accountInfoOpen || accountInfoError || accountInfoMessage ? (
          <form className="notes-create-form account-info-form" onSubmit={handleAccountInfoSubmit} ref={accountInfoPanelRef}>
            {accountInfoError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{accountInfoError}</span></div> : null}
            {accountInfoMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{accountInfoMessage}</span></div> : null}
            {accountInfoOpen ? (
              <>
                <div className="notes-create-grid">
                  <div className="form-field">
                    <span>업체/학교</span>
                    <SearchableSelect
                      ariaLabel="계정 업체/학교 선택"
                      onChange={(nextValue) => handleAccountInfoFieldChange('companyId', nextValue)}
                      options={accountInfoCompanies.map(makeCompanySelectOption)}
                      placeholder="업체/학교 검색"
                      value={accountInfoForm.companyId}
                    />
                  </div>
                  <label>
                    <span>부서/연구실명</span>
                    <input
                      onChange={(event) => handleAccountInfoFieldChange('departmentName', event.target.value)}
                      required
                      value={accountInfoForm.departmentName}
                    />
                  </label>
                  <div className="form-field account-info-reference">
                    <span>같은 업체 부서 참고</span>
                    <SearchableSelect
                      allowEmpty
                      ariaLabel="부서/연구실 참고 선택"
                      disabled={!accountInfoForm.companyId}
                      emptyLabel="직접 입력 유지"
                      onChange={(nextValue) => {
                        const selected = accountInfoDepartments.find((department) => String(department.id) === nextValue);
                        if (selected) {
                          handleAccountInfoFieldChange('departmentName', selected.name);
                        }
                      }}
                      options={accountInfoDepartments.map(makeDepartmentSelectOption)}
                      placeholder={accountInfoForm.companyId ? '기존 부서 검색' : '업체를 먼저 선택'}
                      value=""
                    />
                  </div>
                  <label>
                    <span>계정 주소</span>
                    <input
                      onChange={(event) => handleAccountInfoFieldChange('address', event.target.value)}
                      value={accountInfoForm.address}
                    />
                  </label>
                </div>
                <label>
                  <span>계정 메모</span>
                  <textarea
                    onChange={(event) => handleAccountInfoFieldChange('notes', event.target.value)}
                    rows={3}
                    value={accountInfoForm.notes}
                  />
                </label>
                <div className="notes-create-actions">
                  <button className="route-secondary-action" onClick={() => setAccountInfoOpen(false)} type="button">
                    취소
                  </button>
                  <button className="route-primary-action" disabled={accountInfoSaving} type="submit">
                    {accountInfoSaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                    저장
                  </button>
                </div>
              </>
            ) : null}
          </form>
        ) : null}
      </section>

      <section className="dashboard-panel customer-account-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Account contacts</span>
            <h2>계정 담당자</h2>
          </div>
          <div className="customer-account-heading-actions">
            {accountManagement?.canManage ? (
              <button className="route-secondary-action" onClick={openAccountContactCreate} type="button">
                <Plus size={15} />
                담당자 추가
              </button>
            ) : null}
            <Users size={18} />
          </div>
        </div>
        {accountContactError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{accountContactError}</span></div> : null}
        {accountContactMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{accountContactMessage}</span></div> : null}
        {accountContacts.length > 0 ? (
          <div className="customer-account-contact-list">
            {accountContacts.map((contact) => (
              <article className={`customer-account-contact-card ${contact.isActive ? '' : 'inactive'}`} key={contact.id}>
                <div>
                  <div className="customer-account-contact-title">
                    <strong>{contact.name}</strong>
                    <span className="customer-contact-role-badge">{contact.contactRoleLabel || '실무자'}</span>
                    {!contact.isActive ? <span className="customer-contact-role-badge inactive">비활성</span> : null}
                  </div>
                  <span>{[contact.manager, contact.ownerName].filter(Boolean).join(' · ') || '담당자 정보 없음'}</span>
                </div>
                <dl>
                  <div>
                    <dt>연락처</dt>
                    <dd>{contact.contactSummary || '연락처 없음'}</dd>
                  </div>
                  <div>
                    <dt>주소</dt>
                    <dd>{contact.address || '주소 없음'}</dd>
                  </div>
                  <div>
                    <dt>상세</dt>
                    <dd>{contact.notes || '상세 내용 없음'}</dd>
                  </div>
                </dl>
                <div className="customer-account-contact-actions">
                  <a className="customer-row-action" href={contact.href}>
                    상세 <MoveUpRight size={13} />
                  </a>
                  {contact.canManage ? (
                    <>
                      <button className="customer-row-action" onClick={() => openAccountContactEdit(contact)} type="button">
                        수정/이동
                      </button>
                      <button
                        className="customer-row-action"
                        disabled={accountContactSaving}
                        onClick={() => toggleAccountContactActive(contact, !contact.isActive)}
                        type="button"
                      >
                        {contact.isActive ? '비활성화' : '활성화'}
                      </button>
                    </>
                  ) : null}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <DashboardEmpty label="이 계정에 표시할 담당자가 없습니다" />
        )}
        {accountContactEditor ? (
          <form className="notes-create-form account-contact-form" onSubmit={handleAccountContactSubmit} ref={accountContactPanelRef}>
            <div className="dashboard-panel-heading customer-asset-editor-heading">
              <div>
                <span className="eyebrow">{accountContactEditor === 'create' ? 'New contact' : 'Edit contact'}</span>
                <h3>{accountContactEditor === 'create' ? '담당자 추가' : '담당자 수정/이동'}</h3>
              </div>
            </div>
            <div className="notes-create-grid">
              <label>
                <span>담당자명</span>
                <input
                  onChange={(event) => handleAccountContactFieldChange('customerName', event.target.value)}
                  required
                  value={accountContactForm.customerName}
                />
              </label>
              <label>
                <span>역할</span>
                <select
                  onChange={(event) => handleAccountContactFieldChange('contactRole', event.target.value)}
                  required
                  value={accountContactForm.contactRole}
                >
                  {(accountManagement?.contactRoles ?? []).map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
              <div className="form-field">
                <span>소속 계정</span>
                <SearchableSelect
                  ariaLabel="담당자 이동 대상 부서/연구실"
                  onChange={(nextValue) => handleAccountContactFieldChange('departmentId', nextValue)}
                  options={contactTargetDepartments.map(makeDepartmentSelectOption)}
                  placeholder="부서/연구실 검색"
                  value={accountContactForm.departmentId}
                />
              </div>
              <label>
                <span>활성 여부</span>
                <select
                  onChange={(event) => handleAccountContactFieldChange('isActive', event.target.value === 'true')}
                  value={accountContactForm.isActive ? 'true' : 'false'}
                >
                  <option value="true">활성</option>
                  <option value="false">비활성</option>
                </select>
              </label>
              <label>
                <span>PI/책임자</span>
                <input
                  onChange={(event) => handleAccountContactFieldChange('manager', event.target.value)}
                  value={accountContactForm.manager}
                />
              </label>
              <label>
                <span>연락처</span>
                <input
                  onChange={(event) => handleAccountContactFieldChange('phoneNumber', event.target.value)}
                  value={accountContactForm.phoneNumber}
                />
              </label>
              <label>
                <span>이메일</span>
                <input
                  onChange={(event) => handleAccountContactFieldChange('email', event.target.value)}
                  type="email"
                  value={accountContactForm.email}
                />
              </label>
              <label>
                <span>주소</span>
                <input
                  onChange={(event) => handleAccountContactFieldChange('address', event.target.value)}
                  value={accountContactForm.address}
                />
              </label>
              <label>
                <span>파이프라인</span>
                <select
                  onChange={(event) => handleAccountContactFieldChange('pipelineStage', event.target.value)}
                  required
                  value={accountContactForm.pipelineStage}
                >
                  {(accountManagement?.stages ?? []).map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
            </div>
            <label>
              <span>담당자 메모</span>
              <textarea
                onChange={(event) => handleAccountContactFieldChange('notes', event.target.value)}
                rows={3}
                value={accountContactForm.notes}
              />
            </label>
            <div className="notes-create-actions">
              <button className="route-secondary-action" onClick={() => setAccountContactEditor('')} type="button">
                취소
              </button>
              <button className="route-primary-action" disabled={accountContactSaving} type="submit">
                {accountContactSaving ? <Loader2 className="spin-icon" size={15} /> : <Check size={15} />}
                저장
              </button>
            </div>
          </form>
        ) : null}
      </section>

      <section className="dashboard-panel customer-records-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Operational records</span>
            <h2>고객 운영 기록</h2>
          </div>
          <ListChecks size={18} />
        </div>
        <div className="customer-record-metrics">
          {operationalMetrics.map((metric) => (
            <span key={metric.label}>
              {metric.label}
              <strong>{metric.value}</strong>
            </span>
          ))}
        </div>
        <div className="customer-record-ledger-note">
          <span>납품 합계 {formatWon(operationalRecords.metrics.deliveryAmount)}</span>
          <span>선결제 차감 납품 {formatWon(operationalRecords.metrics.prepaymentDeliveryAmount)}</span>
          <span>일반 납품 {formatWon(operationalRecords.metrics.normalDeliveryAmount)}</span>
          <span>선결제 차감액 {formatWon(operationalRecords.metrics.prepaymentUsedAmount)}</span>
        </div>
        <div className="customer-record-sections">
          <section className="customer-record-section">
            <div className="customer-record-section-heading">
              <div>
                <h3>납품 기록</h3>
                <span>부서/연구실 계정 기준 · 명시 결제구분 표시</span>
              </div>
              {(data.links.accountDeliveryRecordsXlsx || data.links.deliveryRecordsXlsx) ? (
                <a className="route-secondary-action" href={data.links.accountDeliveryRecordsXlsx || data.links.deliveryRecordsXlsx}>
                  <Download size={15} />
                  납품 엑셀
                </a>
              ) : null}
            </div>
            <CustomerDeliveryRecords records={operationalRecords.deliveryRecords} />
          </section>
          <section className="customer-record-section">
            <div className="customer-record-section-heading">
              <h3>견적 기록</h3>
              <span>같은 부서 견적서/견적 일정 기준</span>
            </div>
            <CustomerQuoteRecords records={operationalRecords.quoteRecords} />
          </section>
          <section className="customer-record-section">
            <div className="customer-record-section-heading">
              <h3>서비스 기록</h3>
              <span>A/S, 수리, 서비스 일정</span>
            </div>
            <CustomerServiceRecords records={operationalRecords.serviceRecords} />
          </section>
          <section className="customer-record-section">
            <div className="customer-record-section-heading">
              <h3>선결제 기록</h3>
              <span>같은 부서 입금, 잔액, 사용내역</span>
            </div>
            <CustomerPrepaymentRecords records={operationalRecords.prepaymentRecords} />
          </section>
        </div>
      </section>

      <section className="dashboard-panel customer-demo-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Demos</span>
            <h2>데모 현황</h2>
          </div>
          <Archive size={18} />
        </div>
        <div className="customer-assets-metrics">
          {demoMetrics.map((metric) => (
            <span key={metric.label}>
              {metric.label}
              <strong>{metric.value}</strong>
            </span>
          ))}
        </div>
        {!demoSummary.canManage && demoSummary.message ? (
          <div className="dashboard-api-alert compact">
            <ShieldCheck size={16} />
            <span>{demoSummary.message}</span>
          </div>
        ) : null}
        <div className="customer-assets-actions">
          {demoSummary.canManage && demoSummary.links.createDemo ? (
            <a className="route-secondary-action" href={demoSummary.links.createDemo}>
              <Plus size={15} />
              데모 등록
            </a>
          ) : null}
          <a className="route-secondary-action" href={demoSummary.links.demos || '/demos/'}>
            데모관리
            <MoveUpRight size={15} />
          </a>
        </div>
        {demoSummary.demos.length > 0 ? (
          <div className="customer-asset-list demo-summary-list">
            {demoSummary.demos.map((record) => (
              <article className="customer-asset-card" key={record.id}>
                <div>
                  <strong>{record.productName}</strong>
                  <span>{[record.customerName || '부서 연결', record.serialNumber, `${formatNumber(record.quantity)}개`].filter(Boolean).join(' · ')}</span>
                </div>
                <DemoStatusBadge record={record} />
                <div className="customer-asset-meta">
                  {record.startDate ? <span>시작 {formatDateLabel(record.startDate)}</span> : null}
                  {record.expectedReturnDate ? <span>예정 {formatDateLabel(record.expectedReturnDate)}</span> : null}
                  {record.returnedDate ? <span>회수 {formatDateLabel(record.returnedDate)}</span> : null}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <DashboardEmpty label="등록된 데모 기록이 없습니다" />
        )}
      </section>

      {editOpen || editMessage || editError ? (
        <section className="dashboard-panel notes-create-panel customer-edit-panel" ref={customerEditPanelRef}>
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Edit customer</span>
              <h2>고객 정보 수정</h2>
            </div>
            <Users size={18} />
          </div>
          {editError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{editError}</span></div> : null}
          {editMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{editMessage}</span></div> : null}
          {editOpen ? (
            <form className="notes-create-form customer-edit-form" onSubmit={handleEditSubmit}>
              <div className="notes-create-grid">
                <div className="form-field">
                  <span>업체/학교</span>
                  <SearchableSelect
                    ariaLabel="업체/학교 선택"
                    onChange={(nextValue) => handleEditFieldChange('companyId', nextValue)}
                    options={editCompanies.map(makeCompanySelectOption)}
                    placeholder="업체/학교 검색"
                    value={editForm.companyId}
                  />
                </div>
                <div className="form-field">
                  <span>부서/연구실</span>
                  <SearchableSelect
                    ariaLabel="부서/연구실 선택"
                    disabled={!editForm.companyId}
                    onChange={(nextValue) => handleEditFieldChange('departmentId', nextValue)}
                    options={editDepartments.map(makeDepartmentSelectOption)}
                    placeholder={editForm.companyId ? '부서/연구실 검색' : '업체를 먼저 선택'}
                    value={editForm.departmentId}
                  />
                </div>
                <label>
                  <span>고객명</span>
                  <input
                    onChange={(event) => handleEditFieldChange('customerName', event.target.value)}
                    required
                    value={editForm.customerName}
                  />
                </label>
                <label>
                  <span>책임자</span>
                  <input
                    onChange={(event) => handleEditFieldChange('manager', event.target.value)}
                    value={editForm.manager}
                  />
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
                  <span>파이프라인</span>
                  <select
                    onChange={(event) => handleEditFieldChange('pipelineStage', event.target.value)}
                    required
                    value={editForm.pipelineStage}
                  >
                    {data.edit.stages.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>연락처</span>
                  <input
                    onChange={(event) => handleEditFieldChange('phoneNumber', event.target.value)}
                    value={editForm.phoneNumber}
                  />
                </label>
                <label>
                  <span>이메일</span>
                  <input
                    onChange={(event) => handleEditFieldChange('email', event.target.value)}
                    type="email"
                    value={editForm.email}
                  />
                </label>
                <label>
                  <span>상세주소</span>
                  <input
                    onChange={(event) => handleEditFieldChange('address', event.target.value)}
                    value={editForm.address}
                  />
                </label>
              </div>
              <label>
                <span>상세 내용</span>
                <textarea
                  onChange={(event) => handleEditFieldChange('notes', event.target.value)}
                  rows={3}
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

      <div className="customer-detail-layout">
        <div className="customer-detail-main-stack">
          <section className="dashboard-panel customer-detail-main">
            <div className="dashboard-panel-heading">
              <div>
                <span className="eyebrow">Recent notes</span>
                <h2>최근 영업노트</h2>
              </div>
              <FileText size={18} />
            </div>
            <CustomerDetailNoteList emptyLabel="최근 영업노트가 없습니다" notes={data.recentNotes} />
          </section>

          <section className="dashboard-panel customer-detail-main">
            <div className="dashboard-panel-heading">
              <div>
                <span className="eyebrow">Schedule history</span>
                <h2>최근 일정</h2>
              </div>
              <CalendarDays size={18} />
            </div>
            <SchedulesCompactList emptyLabel="최근 일정이 없습니다" items={data.recentSchedules} />
          </section>

          <section className="dashboard-panel customer-detail-main customer-attachments-panel">
            <div className="dashboard-panel-heading">
              <div>
                <span className="eyebrow">Files</span>
                <h2>첨부 파일</h2>
              </div>
              <Upload size={18} />
            </div>
            <div className="customer-attachment-metrics">
              <span>전체 <strong>{formatNumber(attachments.metrics.totalFiles)}개</strong></span>
              <span>영업노트 <strong>{formatNumber(attachments.metrics.noteFiles)}개</strong></span>
              <span>일정 <strong>{formatNumber(attachments.metrics.scheduleFiles)}개</strong></span>
            </div>
            <div className="customer-attachment-links">
              <a className="route-secondary-action" href={attachments.links.notes}>
                노트 파일
                <MoveUpRight size={14} />
              </a>
              <a className="route-secondary-action" href={attachments.links.schedules}>
                일정 파일
                <MoveUpRight size={14} />
              </a>
            </div>
            <CustomerAttachmentList files={attachments.recentFiles} />
          </section>
        </div>

        <aside className="dashboard-panel customer-detail-side">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Customer</span>
              <h2>고객 요약</h2>
            </div>
            <Users size={18} />
          </div>
          <div className="customer-detail-summary">
            <CustomerStatusBadge customer={customerDetail} />
            <dl>
              <div>
                <dt>연락처</dt>
                <dd>{customerDetail.contactSummary || '연락처 없음'}</dd>
              </div>
              <div>
                <dt>다음 액션</dt>
                <dd className={customerDetail.overdue ? 'customer-overdue-text' : ''}>{customerDetail.nextAction || '다음 액션 없음'}</dd>
              </div>
              <div>
                <dt>최근 활동</dt>
                <dd>{customerDetail.lastActivityLabel || '최근 활동 없음'}</dd>
              </div>
            </dl>
          </div>

          <div className="customer-prepayment-card">
            <div className="customer-prepayment-heading">
              <div>
                <span className="eyebrow">Prepayment</span>
                <h3>선결제 요약</h3>
              </div>
              <CircleDollarSign size={18} />
            </div>
            <div className="customer-prepayment-metrics">
              <span>
                총액
                <strong>{formatWon(prepaymentSummary.metrics.totalAmount)}</strong>
              </span>
              <span>
                잔액
                <strong>{formatWon(prepaymentSummary.metrics.totalBalance)}</strong>
              </span>
              <span>
                사용
                <strong>{formatWon(prepaymentSummary.metrics.totalUsed)}</strong>
              </span>
              <span>
                건수
                <strong>{formatNumber(prepaymentSummary.metrics.totalCount)}건</strong>
              </span>
            </div>
            <div className="customer-prepayment-state">
              <span>활성 {formatNumber(prepaymentSummary.metrics.activeCount)}</span>
              <span>소진 {formatNumber(prepaymentSummary.metrics.depletedCount)}</span>
              <span>취소 {formatNumber(prepaymentSummary.metrics.cancelledCount)}</span>
            </div>
            {prepaymentSummary.recentPrepayments.length > 0 ? (
              <div className="customer-prepayment-list">
                {prepaymentSummary.recentPrepayments.map((prepayment) => (
                  <article key={prepayment.id}>
                    <div>
                      <strong>{prepayment.paymentDate ? formatDateLabel(prepayment.paymentDate) : '입금일 없음'}</strong>
                      <small>{[prepayment.payerName || '입금자 미지정', prepayment.ownerName].filter(Boolean).join(' · ')}</small>
                    </div>
                    <div>
                      <strong className={prepayment.balance > 0 ? 'prepayment-balance-active' : 'customer-muted-cell'}>
                        {formatWon(prepayment.balance)}
                      </strong>
                      <PrepaymentStatusBadge label={prepayment.statusLabel} status={prepayment.status} />
                    </div>
                    <a href={`/prepayments/${prepayment.id}/`}>상세</a>
                  </article>
                ))}
              </div>
            ) : (
              <DashboardEmpty label="이 고객의 선결제가 없습니다" />
            )}
            <div className="customer-prepayment-actions">
              <a className="route-secondary-action" href={prepaymentScopeHref}>
                {prepaymentScopeLabel}
                <MoveUpRight size={15} />
              </a>
              <a className="route-secondary-action" href={prepaymentSummary.links.prepayments}>
                선결제 목록
                <MoveUpRight size={15} />
              </a>
            </div>
          </div>

          <div className="dashboard-panel-heading customer-detail-section-heading">
            <div>
              <span className="eyebrow">Upcoming</span>
              <h2>예정 일정</h2>
            </div>
            <CalendarDays size={18} />
          </div>
          <SchedulesCompactList emptyLabel="예정 일정이 없습니다" items={data.upcomingSchedules} />
        </aside>
      </div>
    </section>
  );
}

export function CustomersPage({
  data,
  detailData,
  detailLoading,
  loading,
  company,
  grade,
  level,
  owner,
  page,
  query,
  rowMode,
  selectedCustomerId,
  selectedDetailMode,
  stage,
  onDetailRefresh,
  onCompanyFilterChange,
  onGradeChange,
  onLevelChange,
  onOwnerChange,
  onPageChange,
  onQueryChange,
  onRowModeChange,
  onStageChange,
}: {
  data: CustomersData | null;
  detailData: CustomerDetailData | null;
  detailLoading: boolean;
  loading: boolean;
  company: string;
  grade: string;
  level: string;
  owner: string;
  page: number;
  query: string;
  rowMode: CustomerRowMode;
  selectedCustomerId: number | null;
  selectedDetailMode: CustomerDetailMode;
  stage: string;
  onDetailRefresh: () => Promise<CustomerDetailData | null>;
  onCompanyFilterChange: (value: string) => void;
  onGradeChange: (value: string) => void;
  onLevelChange: (value: string) => void;
  onOwnerChange: (value: string) => void;
  onPageChange: (value: number) => void;
  onQueryChange: (value: string) => void;
  onRowModeChange: (value: CustomerRowMode) => void;
  onStageChange: (value: string) => void;
}) {
  if (selectedCustomerId) {
    return (
      <CustomerDetailPage
        data={detailData}
        detailMode={selectedDetailMode}
        loading={detailLoading}
        onRefresh={onDetailRefresh}
      />
    );
  }

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>고객 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const listRows = rowMode === 'contact' ? data.customers : (data.accounts.length > 0 ? data.accounts : data.customers);
  const totalAccountCount = data.metrics.totalAccounts || data.metrics.totalCustomers;
  const filteredAccountCount = data.metrics.filteredAccounts || data.metrics.filteredCustomers;
  const rowModeLabel = rowMode === 'contact' ? '담당자 목록' : '계정 목록';
  const rowModeDetail = rowMode === 'contact'
    ? `${formatNumber(data.pagination.contactRows || data.metrics.filteredCustomers)}명`
    : `${formatNumber(data.pagination.accountRows || filteredAccountCount)}개 계정`;
  const pagination = data.pagination;
  const currentPage = pagination.page || page || 1;
  const metrics = [
    { label: '계정', value: `${formatNumber(totalAccountCount)}개`, detail: data.scope.label, icon: Users, tone: 'blue' as const },
    { label: '검색 결과', value: `${formatNumber(filteredAccountCount)}개`, detail: '부서/연구실 계정', icon: Search, tone: 'teal' as const },
    { label: '담당자', value: `${formatNumber(data.metrics.totalCustomers)}명`, detail: rowModeDetail, icon: Building2, tone: 'amber' as const },
    { label: '예정 일정 고객', value: `${formatNumber(data.metrics.scheduledCustomers)}건`, detail: '미래 일정 보유', icon: CalendarDays, tone: 'green' as const },
  ];
  return (
    <section className="customers-page">
      {data.source !== 'django' ? (
        <DashboardApiAlert message={data.error} title="고객 정보를 불러오지 못했습니다" />
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Customers</span>
          <h2>{data.scope.label || '계정 관리'}</h2>
          <p>부서/연구실 계정 기준으로 담당자, 일정, 활동, 후속조치를 확인합니다.</p>
        </div>
      </div>

      <section className="dashboard-metric-grid customers-metric-grid" aria-label="고객 핵심 지표">
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

      <div className="customers-filter-tools">
        <div className="customer-row-mode" role="tablist" aria-label="고객 목록 표시 기준">
          {(data.options.rowModes.length > 0 ? data.options.rowModes : [
            { value: 'account' as CustomerRowMode, label: '계정 기준' },
            { value: 'contact' as CustomerRowMode, label: '담당자 기준' },
          ]).map((option) => (
            <button
              aria-selected={rowMode === option.value}
              className={rowMode === option.value ? 'active' : ''}
              key={option.value}
              onClick={() => onRowModeChange(option.value)}
              role="tab"
              type="button"
            >
              {option.label}
            </button>
          ))}
        </div>
        <div className="customer-export-actions">
          {data.export.canDownload ? (
            <>
              <a className="route-secondary-action" href={data.export.basicUrl}>
                <Download size={15} />
                기본 엑셀
              </a>
              <a className="route-secondary-action" href={data.export.fullUrl}>
                <FileSpreadsheet size={15} />
                전체 엑셀
              </a>
            </>
          ) : (
            <span>{data.export.message || '엑셀 권한 없음'}</span>
          )}
        </div>
      </div>

      <div className="customers-filter-bar">
        <label className="customers-search">
          <Search size={17} />
          <input
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="계정, 담당자, 회사, 연구실, 연락처 검색"
            value={query}
          />
        </label>
        <select onChange={(event) => onCompanyFilterChange(event.target.value)} value={company}>
          <option value="">업체 전체</option>
          {data.options.companies.map((option) => (
            <option key={option.id} value={option.id}>
              {option.name} ({formatNumber(option.count)})
            </option>
          ))}
        </select>
        <select onChange={(event) => onOwnerChange(event.target.value)} value={owner}>
          <option value="">담당자 전체</option>
          {data.options.owners.map((option) => (
            <option key={option.id} value={option.id}>{option.name}</option>
          ))}
        </select>
        <select onChange={(event) => onStageChange(event.target.value)} value={stage}>
          <option value="">파이프라인 전체</option>
          {data.options.stages.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onGradeChange(event.target.value)} value={grade}>
          <option value="">고객등급 전체</option>
          {data.options.grades.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onLevelChange(event.target.value)} value={level}>
          <option value="">종합점수 전체</option>
          {data.options.scoreLevels.map((option) => (
            <option key={option.value} value={option.value}>
              {option.description ? `${option.label} (${option.description})` : option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="customers-layout">
        <section className="dashboard-panel customers-main-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Customer list</span>
              <h2>{rowModeLabel}</h2>
            </div>
            {loading ? <Loader2 className="spin-icon" size={18} /> : <Users size={18} />}
          </div>
          <CustomersTable customers={listRows} emptyLabel={rowMode === 'contact' ? '조건에 맞는 담당자가 없습니다' : '조건에 맞는 계정이 없습니다'} />
          <div className="customers-pagination">
            <button
              className="route-secondary-action"
              disabled={!pagination.hasPrevious || loading}
              onClick={() => onPageChange(Math.max(1, currentPage - 1))}
              type="button"
            >
              <ChevronLeft size={15} />
              이전
            </button>
            <span>
              {formatNumber(currentPage)} / {formatNumber(pagination.totalPages || 1)}
              {' · '}
              {formatNumber(pagination.totalRows)}건
            </span>
            <button
              className="route-secondary-action"
              disabled={!pagination.hasNext || loading}
              onClick={() => onPageChange(currentPage + 1)}
              type="button"
            >
              다음
              <ChevronRight size={15} />
            </button>
          </div>
        </section>

      </div>
    </section>
  );
}