import { useEffect, useRef, useState, type FormEvent } from 'react';
import {
    CheckCircle2,
    ListChecks,
    Loader2,
    Plus,
    Search,
    ShieldCheck,
    Users
} from 'lucide-react';
import {
    EmployeeManagementItem,
    EmployeeMutationPayload,
    EmployeesData,
    createEmployee,
    toggleEmployeeActive,
    updateEmployee
} from '../../api';
import { DashboardMetricCard } from '../../components/shared/DashboardMetricCard';
import { DashboardApiAlert, DashboardEmpty } from '../../components/shared/FeedbackStates';
import {
    formatDateTimeLabel,
    formatNumber
} from '../../components/shared/formatters';
import { useGuidedPanelFocus } from '../shared/appShared';


type EmployeeFormState = {
  username: string;
  firstName: string;
  lastName: string;
  email: string;
  role: string;
  companyId: string;
  companyName: string;
  password: string;
  passwordConfirm: string;
  canDownloadExcel: boolean;
  canUseAi: boolean;
  isActive: boolean;
};

const makeEmptyEmployeeForm = (data?: EmployeesData | null): EmployeeFormState => ({
  username: '',
  firstName: '',
  lastName: '',
  email: '',
  role: data?.scope.mode === 'admin' ? 'salesman' : 'salesman',
  companyId: data?.scope.mode === 'manager' && data.scope.companyId ? String(data.scope.companyId) : '',
  companyName: data?.scope.mode === 'manager' ? data.scope.companyName : '',
  password: '',
  passwordConfirm: '',
  canDownloadExcel: false,
  canUseAi: false,
  isActive: true,
});

const makeEmployeeEditForm = (employee: EmployeeManagementItem, data?: EmployeesData | null): EmployeeFormState => ({
  username: employee.username || '',
  firstName: employee.firstName || '',
  lastName: employee.lastName || '',
  email: employee.email || '',
  role: employee.role || 'salesman',
  companyId: employee.companyId ? String(employee.companyId) : '',
  companyName: employee.company || data?.scope.companyName || '',
  password: '',
  passwordConfirm: '',
  canDownloadExcel: Boolean(employee.canDownloadExcel),
  canUseAi: Boolean(employee.canUseAi),
  isActive: Boolean(employee.isActive),
});

const employeePayloadFromForm = (form: EmployeeFormState): EmployeeMutationPayload => ({
  username: form.username.trim(),
  firstName: form.firstName.trim(),
  lastName: form.lastName.trim(),
  email: form.email.trim(),
  role: form.role,
  companyId: form.companyId || undefined,
  companyName: form.companyName.trim() || undefined,
  password: form.password || undefined,
  passwordConfirm: form.passwordConfirm || undefined,
  canDownloadExcel: form.canDownloadExcel,
  canUseAi: form.canUseAi,
  isActive: form.isActive,
});

export function EmployeesPage({
  data,
  loading,
  company,
  status,
  query,
  role,
  onCompanyChange,
  onQueryChange,
  onRoleChange,
  onStatusChange,
  onRefresh,
}: {
  data: EmployeesData | null;
  loading: boolean;
  company: string;
  status: string;
  query: string;
  role: string;
  onCompanyChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onRoleChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onRefresh: () => Promise<void>;
}) {
  const [formOpen, setFormOpen] = useState(() => new URLSearchParams(window.location.search).get('create') === '1');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<EmployeeFormState>(() => makeEmptyEmployeeForm(data));
  const [saving, setSaving] = useState(false);
  const [actioningId, setActioningId] = useState<number | null>(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const employeeFormPanelRef = useRef<HTMLElement | null>(null);

  useGuidedPanelFocus(formOpen, employeeFormPanelRef, `employee-${editingId || 'new'}`);

  useEffect(() => {
    if (!data) return;
    const params = new URLSearchParams(window.location.search);
    const requestedId = Number(params.get('employee') || 0);
    const shouldEdit = params.get('edit') === '1';
    if (requestedId && shouldEdit && editingId !== requestedId) {
      const employee = data.employees.find((item) => item.id === requestedId);
      if (employee?.canUpdate) {
        setEditingId(employee.id);
        setForm(makeEmployeeEditForm(employee, data));
        setFormOpen(true);
      }
    } else if (!editingId && !formOpen && data.scope.mode === 'manager') {
      setForm((previous) => ({
        ...previous,
        companyId: data.scope.companyId ? String(data.scope.companyId) : previous.companyId,
        companyName: data.scope.companyName || previous.companyName,
      }));
    }
  }, [data, editingId, formOpen]);

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>직원 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const isAdminMode = data.scope.mode === 'admin';
  const editingEmployee = editingId ? data.employees.find((employee) => employee.id === editingId) ?? null : null;
  const canSubmit = editingId ? Boolean(editingEmployee?.canUpdate) : data.scope.canCreate;
  const metrics = [
    { label: isAdminMode ? '전체 사용자' : '전체 직원', value: `${formatNumber(data.metrics.totalEmployees)}명`, detail: data.scope.companyName || '전체 회사', icon: Users, tone: 'blue' as const },
    { label: '활성 계정', value: `${formatNumber(data.metrics.activeEmployees)}명`, detail: `비활성 ${formatNumber(data.metrics.inactiveEmployees)}명`, icon: CheckCircle2, tone: 'green' as const },
    { label: 'Manager', value: `${formatNumber(data.metrics.managerCount)}명`, detail: '직원관리 가능', icon: ShieldCheck, tone: 'amber' as const },
    { label: 'SalesMan', value: `${formatNumber(data.metrics.salesmanCount)}명`, detail: '실무자 계정', icon: ListChecks, tone: 'teal' as const },
  ];

  const openCreateForm = () => {
    setEditingId(null);
    setForm(makeEmptyEmployeeForm(data));
    setFormOpen(true);
    setError('');
    setMessage('');
  };

  const openEditForm = (employee: EmployeeManagementItem) => {
    setEditingId(employee.id);
    setForm(makeEmployeeEditForm(employee, data));
    setFormOpen(true);
    setError('');
    setMessage('');
  };

  const handleFormChange = <K extends keyof EmployeeFormState>(field: K, value: EmployeeFormState[K]) => {
    setForm((previous) => ({ ...previous, [field]: value }));
    setError('');
    setMessage('');
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!canSubmit || saving) return;
    if (editingId && !editingEmployee) {
      setError('수정할 사용자 정보를 찾을 수 없습니다.');
      return;
    }
    if (!form.username.trim()) {
      setError('사용자 ID를 입력하세요.');
      return;
    }
    if (!editingEmployee && !form.password) {
      setError('새 사용자 비밀번호를 입력하세요.');
      return;
    }
    if (form.password || form.passwordConfirm) {
      if (form.password !== form.passwordConfirm) {
        setError('비밀번호가 일치하지 않습니다.');
        return;
      }
    }
    if (isAdminMode && form.role !== 'admin' && !form.companyName.trim()) {
      setError('소속 회사를 입력하세요.');
      return;
    }

    setSaving(true);
    setError('');
    setMessage('');
    try {
      const payload = employeePayloadFromForm(form);
      const result = editingEmployee
        ? await updateEmployee(editingEmployee.updateHref, payload)
        : await createEmployee(data.links.createApi, payload);
      setMessage(result.message || (editingEmployee ? '사용자 정보를 수정했습니다.' : '사용자를 생성했습니다.'));
      setFormOpen(false);
      setEditingId(null);
      setForm(makeEmptyEmployeeForm(data));
      await onRefresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : '사용자 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleActive = async (employee: EmployeeManagementItem) => {
    if (!employee.canToggleActive || !employee.toggleActiveHref || actioningId) return;
    const nextActive = !employee.isActive;
    const actionLabel = nextActive ? '활성화' : '비활성화';
    if (!window.confirm(`${employee.name || employee.username} 계정을 ${actionLabel}할까요?`)) {
      return;
    }
    setActioningId(employee.id);
    setError('');
    setMessage('');
    try {
      const result = await toggleEmployeeActive(employee.toggleActiveHref, nextActive);
      setMessage(result.message || `사용자를 ${actionLabel}했습니다.`);
      await onRefresh();
    } catch (toggleError) {
      setError(toggleError instanceof Error ? toggleError.message : '사용자 상태 변경에 실패했습니다.');
    } finally {
      setActioningId(null);
    }
  };

  return (
    <section className="employees-page">
      {data.source !== 'django' ? (
        <DashboardApiAlert message={data.error === 'management_required' ? 'Admin 또는 Manager 계정만 사용할 수 있습니다.' : data.message || data.error} title="직원관리 정보를 불러오지 못했습니다" />
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Employee management</span>
          <h2>{data.scope.label || (isAdminMode ? '사용자관리' : '직원관리')}</h2>
          <p>{isAdminMode ? '전체 사용자 계정, 회사, 권한, 활성 상태를 React에서 관리합니다.' : '같은 회사 직원 계정, 권한, 활성 상태를 React에서 관리합니다.'}</p>
        </div>
        <div className="schedules-summary-actions">
          {data.scope.canCreate ? (
            <button className="route-primary-action" type="button" onClick={openCreateForm}>
              {isAdminMode ? '사용자 추가' : '직원 추가'}
              <Plus size={16} />
            </button>
          ) : null}
        </div>
      </div>

      <section className="dashboard-metric-grid customers-metric-grid" aria-label="직원관리 지표">
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

      <div className="customers-filter-bar">
        <label className="customers-search">
          <Search size={17} />
          <input
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="이름, 사용자명, 이메일 검색"
            value={query}
          />
        </label>
        <select onChange={(event) => onRoleChange(event.target.value)} value={role}>
          {data.options.roles.map((option) => (
            <option key={option.value || 'all'} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onStatusChange(event.target.value)} value={status}>
          {(data.options.statuses ?? []).map((option) => (
            <option key={option.value || 'all'} value={option.value}>{option.label}</option>
          ))}
        </select>
        {isAdminMode ? (
          <select onChange={(event) => onCompanyChange(event.target.value)} value={company}>
            <option value="">회사 전체</option>
            {(data.options.companies ?? []).map((option) => (
              <option key={option.id} value={option.id}>{option.name}</option>
            ))}
          </select>
        ) : null}
      </div>

      {formOpen ? (
        <section className="dashboard-panel employee-form-panel" ref={employeeFormPanelRef}>
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">{editingEmployee ? 'Edit account' : 'Create account'}</span>
              <h2>{editingEmployee ? `${editingEmployee.name || editingEmployee.username} 수정` : isAdminMode ? '사용자 추가' : '직원 추가'}</h2>
            </div>
            <button className="route-secondary-action" type="button" onClick={() => {
              setFormOpen(false);
              setEditingId(null);
              setForm(makeEmptyEmployeeForm(data));
              setError('');
              setMessage('');
            }}>닫기</button>
          </div>
          <form className="employee-form-grid" onSubmit={handleSubmit}>
            <label>
              <span>사용자 ID</span>
              <input value={form.username} onChange={(event) => handleFormChange('username', event.target.value)} />
            </label>
            <label>
              <span>성</span>
              <input value={form.lastName} onChange={(event) => handleFormChange('lastName', event.target.value)} />
            </label>
            <label>
              <span>이름</span>
              <input value={form.firstName} onChange={(event) => handleFormChange('firstName', event.target.value)} />
            </label>
            <label>
              <span>이메일</span>
              <input type="email" value={form.email} onChange={(event) => handleFormChange('email', event.target.value)} />
            </label>
            <label>
              <span>권한</span>
              <select
                disabled={!isAdminMode || Boolean(editingEmployee && !editingEmployee.canChangeRole)}
                value={form.role}
                onChange={(event) => handleFormChange('role', event.target.value)}
              >
                {data.options.roles.filter((option) => option.value).map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>
            <label>
              <span>소속 회사</span>
              <input
                disabled={!isAdminMode || Boolean(editingEmployee && !editingEmployee.canChangeCompany)}
                list="employee-company-options"
                value={form.companyName}
                onChange={(event) => {
                  handleFormChange('companyName', event.target.value);
                  handleFormChange('companyId', '');
                }}
              />
              <datalist id="employee-company-options">
                {(data.options.companies ?? []).map((option) => (
                  <option key={option.id} value={option.name} />
                ))}
              </datalist>
            </label>
            <label>
              <span>{editingEmployee ? '새 비밀번호' : '비밀번호'}</span>
              <input type="password" value={form.password} onChange={(event) => handleFormChange('password', event.target.value)} />
            </label>
            <label>
              <span>비밀번호 확인</span>
              <input type="password" value={form.passwordConfirm} onChange={(event) => handleFormChange('passwordConfirm', event.target.value)} />
            </label>
            <div className="employee-permission-row">
              <label>
                <input
                  checked={form.canDownloadExcel}
                  type="checkbox"
                  onChange={(event) => handleFormChange('canDownloadExcel', event.target.checked)}
                />
                <span>엑셀 다운로드</span>
              </label>
              <label>
                <input
                  checked={form.canUseAi}
                  disabled={!isAdminMode || Boolean(editingEmployee && !editingEmployee.canChangeAi)}
                  type="checkbox"
                  onChange={(event) => handleFormChange('canUseAi', event.target.checked)}
                />
                <span>AI 사용</span>
              </label>
              {editingEmployee ? (
                <label>
                  <input
                    checked={form.isActive}
                    disabled={!editingEmployee.canToggleActive}
                    type="checkbox"
                    onChange={(event) => handleFormChange('isActive', event.target.checked)}
                  />
                  <span>활성 계정</span>
                </label>
              ) : null}
            </div>
            <div className="route-actions employee-form-actions">
              <button className="primary-button" type="submit" disabled={saving}>{saving ? '저장 중' : editingEmployee ? '수정 저장' : '계정 생성'}</button>
              <button className="route-secondary-action" type="button" onClick={() => {
                setFormOpen(false);
                setEditingId(null);
                setForm(makeEmptyEmployeeForm(data));
              }}>취소</button>
            </div>
          </form>
        </section>
      ) : null}

      {error ? <p className="form-error">{error}</p> : null}
      {message ? <p className="form-success">{message}</p> : null}

      <section className="dashboard-panel customers-main-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Employees</span>
            <h2>직원 목록</h2>
          </div>
          {loading ? <Loader2 className="spin-icon" size={18} /> : <Users size={18} />}
        </div>
        {data.employees.length ? (
          <div className="customers-table-wrap">
            <table className="customers-table">
              <thead>
                <tr>
                  <th>직원</th>
                  <th>권한</th>
                  <th>상태</th>
                  <th>권한 옵션</th>
                  {isAdminMode ? <th>회사</th> : null}
                  <th>최근 로그인</th>
                  <th>작업</th>
                </tr>
              </thead>
              <tbody>
                {data.employees.map((employee) => (
                  <tr key={employee.id}>
                    <td>
                      <strong>{employee.name || employee.username}</strong>
                      <small className="customer-muted-cell">{[employee.username, employee.email].filter(Boolean).join(' · ') || '-'}</small>
                    </td>
                    <td>{employee.roleLabel || employee.role}</td>
                    <td>
                      <span className={`product-status ${employee.isActive ? 'active' : 'inactive'}`}>
                        {employee.isActive ? '활성' : '비활성'}
                      </span>
                    </td>
                    <td>
                      {[
                        employee.canDownloadExcel ? '엑셀' : '',
                        employee.canUseAi ? 'AI' : '',
                      ].filter(Boolean).join(' · ') || '-'}
                    </td>
                    {isAdminMode ? <td>{employee.company || '-'}</td> : null}
                    <td>{employee.lastLogin ? formatDateTimeLabel(employee.lastLogin) : '-'}</td>
                    <td>
                      <div className="product-row-actions">
                        {employee.canUpdate ? (
                          <button className="route-secondary-action" type="button" onClick={() => openEditForm(employee)}>수정</button>
                        ) : (
                          <span className="customer-muted-cell">{employee.isCurrentUser ? '본인 계정' : '읽기 전용'}</span>
                        )}
                        {employee.canToggleActive ? (
                          <button
                            className={`route-secondary-action ${employee.isActive ? 'danger' : ''}`}
                            disabled={actioningId === employee.id}
                            type="button"
                            onClick={() => handleToggleActive(employee)}
                          >
                            {employee.isActive ? '비활성화' : '활성화'}
                          </button>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <DashboardEmpty label="조건에 맞는 직원이 없습니다" />
        )}
      </section>
    </section>
  );
}