import {
  AlertTriangle,
  Building2,
  Check,
  ChevronRight,
  Loader2,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Trash2,
  Users,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import {
  CompanyManagementCompany,
  CompanyManagementData,
  CompanyManagementDepartment,
  createCompany as createCompanyRecord,
  createDepartment as createDepartmentRecord,
  deleteCompanyRecord,
  deleteDepartmentRecord,
  loadCompanyManagementData,
  updateCompany as updateCompanyRecord,
  updateDepartment as updateDepartmentRecord,
} from '../../api/accounts';
import { DashboardEmpty } from '../../components/shared/FeedbackStates';

const formatNumber = (value: number | null | undefined) => new Intl.NumberFormat('ko-KR').format(value ?? 0);

const initialSearch = () => new URLSearchParams(window.location.search).get('q') || new URLSearchParams(window.location.search).get('search') || '';
const initialCompanyId = () => new URLSearchParams(window.location.search).get('company_id') || '';
const initialDepartmentId = () => new URLSearchParams(window.location.search).get('department_id') || '';

function BlockerBadges({ blockers }: { blockers: Array<{ label: string; count: number }> }) {
  if (!blockers.length) {
    return <span className="company-management-clear">삭제 가능</span>;
  }
  return (
    <div className="company-management-blockers">
      {blockers.map((blocker) => (
        <span key={blocker.label}>{blocker.label} {formatNumber(blocker.count)}</span>
      ))}
    </div>
  );
}

function CompanyRow({
  company,
  editName,
  editing,
  saving,
  selected,
  onDelete,
  onEditCancel,
  onEditNameChange,
  onEditStart,
  onEditSubmit,
  onSelect,
}: {
  company: CompanyManagementCompany;
  editName: string;
  editing: boolean;
  saving: boolean;
  selected: boolean;
  onDelete: (company: CompanyManagementCompany) => void;
  onEditCancel: () => void;
  onEditNameChange: (value: string) => void;
  onEditStart: (company: CompanyManagementCompany) => void;
  onEditSubmit: (company: CompanyManagementCompany) => void;
  onSelect: (companyId: number) => void;
}) {
  return (
    <article className={`company-management-row ${selected ? 'selected' : ''}`.trim()}>
      {editing ? (
        <div className="company-management-row-main">
          <Building2 size={17} />
          <span>
            <input
              aria-label="업체/학교명 수정"
              onChange={(event) => onEditNameChange(event.target.value)}
              value={editName}
            />
            <small>{company.createdByName || '생성자 없음'} · 부서 {formatNumber(company.departmentCount)} · 담당자 {formatNumber(company.followupCount)}</small>
          </span>
        </div>
      ) : (
        <button className="company-management-row-main" onClick={() => onSelect(company.id)} type="button">
          <Building2 size={17} />
          <span>
            <strong>{company.name}</strong>
            <small>{company.createdByName || '생성자 없음'} · 부서 {formatNumber(company.departmentCount)} · 담당자 {formatNumber(company.followupCount)}</small>
          </span>
        </button>
      )}
      <BlockerBadges blockers={company.deleteBlockers ?? []} />
      {company.salesmen.length ? (
        <div className="company-management-salesmen">
          {company.salesmen.slice(0, 3).map((salesman) => (
            <span key={salesman.id}>{salesman.name} {formatNumber(salesman.contactCount)}</span>
          ))}
        </div>
      ) : null}
      {company.deleteGuidance ? <p className="company-management-guidance">{company.deleteGuidance}</p> : null}
      <div className="company-management-actions">
        {editing ? (
          <>
            <button className="route-secondary-action" disabled={saving || !editName.trim()} onClick={() => onEditSubmit(company)} type="button">
              {saving ? <Loader2 className="spin-icon" size={14} /> : <Check size={14} />}
              저장
            </button>
            <button className="route-secondary-action" onClick={onEditCancel} type="button">취소</button>
          </>
        ) : (
          <>
            <button className="route-secondary-action" disabled={!company.canManage} onClick={() => onEditStart(company)} title={company.manageMessage || ''} type="button">
              <Pencil size={14} />
              수정
            </button>
            <button className="route-secondary-action danger" disabled={saving || !company.canDelete} onClick={() => onDelete(company)} title={company.deleteMessage || company.manageMessage || ''} type="button">
              {saving ? <Loader2 className="spin-icon" size={14} /> : <Trash2 size={14} />}
              삭제
            </button>
          </>
        )}
      </div>
    </article>
  );
}

function DepartmentRow({
  department,
  editName,
  editing,
  saving,
  onDelete,
  onEditCancel,
  onEditNameChange,
  onEditStart,
  onEditSubmit,
}: {
  department: CompanyManagementDepartment;
  editName: string;
  editing: boolean;
  saving: boolean;
  onDelete: (department: CompanyManagementDepartment) => void;
  onEditCancel: () => void;
  onEditNameChange: (value: string) => void;
  onEditStart: (department: CompanyManagementDepartment) => void;
  onEditSubmit: (department: CompanyManagementDepartment) => void;
}) {
  return (
    <article className="company-management-department-row">
      <div className="company-management-department-main">
        <Building2 size={16} />
        <span>
          {editing ? (
            <input
              aria-label="부서/연구실명 수정"
              onChange={(event) => onEditNameChange(event.target.value)}
              value={editName}
            />
          ) : (
            <strong>{department.name}</strong>
          )}
          <small>{department.createdByName || '생성자 없음'} · 담당자 {formatNumber(department.followupCount)} · 장비 {formatNumber(department.assetCount)}</small>
        </span>
      </div>
      <BlockerBadges blockers={department.deleteBlockers ?? []} />
      {department.deleteGuidance ? <p className="company-management-guidance">{department.deleteGuidance}</p> : null}
      <div className="company-management-actions">
        <a className="route-secondary-action" href={department.href}>계정<ChevronRight size={14} /></a>
        {department.cleanupPreviewHref ? <a className="route-secondary-action" href={department.cleanupPreviewHref}>정리 영향</a> : null}
        {editing ? (
          <>
            <button className="route-secondary-action" disabled={saving || !editName.trim()} onClick={() => onEditSubmit(department)} type="button">
              {saving ? <Loader2 className="spin-icon" size={14} /> : <Check size={14} />}
              저장
            </button>
            <button className="route-secondary-action" onClick={onEditCancel} type="button">취소</button>
          </>
        ) : (
          <>
            <button className="route-secondary-action" disabled={!department.canManage} onClick={() => onEditStart(department)} title={department.manageMessage || ''} type="button">
              <Pencil size={14} />
              수정
            </button>
            <button className="route-secondary-action danger" disabled={saving || !department.canDelete} onClick={() => onDelete(department)} title={department.deleteMessage || department.manageMessage || ''} type="button">
              {saving ? <Loader2 className="spin-icon" size={14} /> : <Trash2 size={14} />}
              삭제
            </button>
          </>
        )}
      </div>
    </article>
  );
}

export function CompanyManagementPage() {
  const [data, setData] = useState<CompanyManagementData | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState(initialSearch);
  const [selectedCompanyId, setSelectedCompanyId] = useState(initialCompanyId);
  const [departmentQuery, setDepartmentQuery] = useState('');
  const [companyCreateName, setCompanyCreateName] = useState('');
  const [departmentCreateName, setDepartmentCreateName] = useState('');
  const [companyEditId, setCompanyEditId] = useState<number | null>(null);
  const [companyEditName, setCompanyEditName] = useState('');
  const [departmentEditId, setDepartmentEditId] = useState<number | null>(null);
  const [departmentEditName, setDepartmentEditName] = useState('');
  const [savingKey, setSavingKey] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const departmentIdParam = useMemo(initialDepartmentId, []);

  const refreshData = async () => {
    setLoading(true);
    const nextData = await loadCompanyManagementData({
      q: query,
      companyId: selectedCompanyId,
      departmentId: departmentIdParam,
    });
    setData(nextData);
    setLoading(false);
  };

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      void refreshData();
    }, 200);
    return () => window.clearTimeout(timeout);
  }, [query]);

  useEffect(() => {
    if (!data || selectedCompanyId) {
      return;
    }
    const departmentMatch = departmentIdParam
      ? data.departments.find((department) => String(department.id) === departmentIdParam)
      : null;
    const firstCompanyId = departmentMatch?.companyId ?? data.companies[0]?.id;
    if (firstCompanyId) {
      setSelectedCompanyId(String(firstCompanyId));
    }
  }, [data, departmentIdParam, selectedCompanyId]);

  const selectedCompany = data?.companies.find((company) => String(company.id) === selectedCompanyId) ?? data?.companies[0] ?? null;
  const visibleDepartments = (selectedCompany?.departments ?? []).filter((department) => {
    const term = departmentQuery.trim().toLowerCase();
    if (!term) return true;
    return [department.name, department.companyName, department.createdByName].join(' ').toLowerCase().includes(term);
  });

  const resetFeedback = () => {
    setMessage('');
    setError('');
  };

  const runAction = async (key: string, action: () => Promise<void>) => {
    if (savingKey) return;
    setSavingKey(key);
    resetFeedback();
    try {
      await action();
      await refreshData();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : '작업에 실패했습니다.');
    } finally {
      setSavingKey('');
    }
  };

  const handleCreateCompany = () => {
    const name = companyCreateName.trim();
    if (!name || !data?.permissions.canCreateCompany) return;
    void runAction('company-create', async () => {
      const result = await createCompanyRecord(name, data.links.createCompany);
      setCompanyCreateName('');
      if (result.company?.id) {
        setSelectedCompanyId(String(result.company.id));
      }
      setMessage(result.message || '업체/학교를 추가했습니다.');
    });
  };

  const handleCreateDepartment = () => {
    const name = departmentCreateName.trim();
    const companyId = Number(selectedCompany?.id);
    if (!name || !companyId || !data?.permissions.canCreateDepartment) return;
    void runAction('department-create', async () => {
      const result = await createDepartmentRecord(companyId, name, data.links.createDepartment);
      setDepartmentCreateName('');
      setMessage(result.message || '부서/연구실을 추가했습니다.');
    });
  };

  const handleCompanyEditStart = (company: CompanyManagementCompany) => {
    setCompanyEditId(company.id);
    setCompanyEditName(company.name);
    setDepartmentEditId(null);
    resetFeedback();
  };

  const handleDepartmentEditStart = (department: CompanyManagementDepartment) => {
    setDepartmentEditId(department.id);
    setDepartmentEditName(department.name);
    setCompanyEditId(null);
    resetFeedback();
  };

  const handleCompanyEditSubmit = (company: CompanyManagementCompany) => {
    const name = companyEditName.trim();
    if (!name || !company.canManage) return;
    void runAction(`company-${company.id}`, async () => {
      const result = await updateCompanyRecord(company.id, name, company.updateUrl);
      setCompanyEditId(null);
      setCompanyEditName('');
      setMessage(result.message || '업체/학교 정보가 수정되었습니다.');
    });
  };

  const handleDepartmentEditSubmit = (department: CompanyManagementDepartment) => {
    const name = departmentEditName.trim();
    if (!name || !department.canManage) return;
    void runAction(`department-${department.id}`, async () => {
      const result = await updateDepartmentRecord(department.id, name, department.updateUrl);
      setDepartmentEditId(null);
      setDepartmentEditName('');
      setMessage(result.message || '부서/연구실 정보가 수정되었습니다.');
    });
  };

  const handleCompanyDelete = (company: CompanyManagementCompany) => {
    if (!company.canDelete) {
      setError(company.deleteMessage || company.manageMessage || '삭제할 수 없습니다.');
      return;
    }
    if (!window.confirm(`"${company.name}" 업체/학교를 삭제할까요?`)) return;
    void runAction(`company-${company.id}`, async () => {
      const result = await deleteCompanyRecord(company.id, company.deleteUrl);
      if (String(company.id) === selectedCompanyId) {
        setSelectedCompanyId('');
      }
      setMessage(result.message || '업체/학교가 삭제되었습니다.');
    });
  };

  const handleDepartmentDelete = (department: CompanyManagementDepartment) => {
    if (!department.canDelete) {
      setError(department.deleteMessage || department.manageMessage || '삭제할 수 없습니다.');
      return;
    }
    if (!window.confirm(`"${department.companyName} - ${department.name}" 부서/연구실을 삭제할까요?`)) return;
    void runAction(`department-${department.id}`, async () => {
      const result = await deleteDepartmentRecord(department.id, department.deleteUrl);
      setMessage(result.message || '부서/연구실이 삭제되었습니다.');
    });
  };

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>업체/부서 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const readOnly = data.permissions.readOnly;

  return (
    <section className="companies-page">
      {data.source !== 'django' ? (
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>업체/부서 API에 연결되지 않았습니다</strong>
            <span>{data.error === 'login_required' ? '로그인이 필요합니다.' : data.error}</span>
          </div>
          <a href="/reporting/login/">로그인</a>
        </div>
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Company accounts</span>
          <h2>업체/부서 관리</h2>
          <p>{data.scope.label || '업체/부서 현황'} · {data.scope.roleLabel || '권한 확인'}</p>
        </div>
        <div className="schedules-summary-actions">
          <button className="route-secondary-action" disabled={loading} onClick={() => { void refreshData(); }} type="button">
            {loading ? <Loader2 className="spin-icon" size={15} /> : <RefreshCw size={15} />}
            새로고침
          </button>
          <a className="route-secondary-action" href={data.links.customers}>고객 목록</a>
        </div>
      </div>

      <div className="dashboard-metric-grid">
        <article className="metric-card tone-blue">
          <Building2 size={19} />
          <span>업체</span>
          <strong>{formatNumber(data.metrics.filteredCompanies)}개</strong>
          <small>전체 {formatNumber(data.metrics.totalCompanies)}개</small>
        </article>
        <article className="metric-card tone-teal">
          <Users size={19} />
          <span>부서/연구실</span>
          <strong>{formatNumber(data.metrics.filteredDepartments)}개</strong>
          <small>전체 {formatNumber(data.metrics.totalDepartments)}개</small>
        </article>
        <article className="metric-card tone-amber">
          <AlertTriangle size={19} />
          <span>삭제 차단</span>
          <strong>{formatNumber(data.metrics.blockedCompanies + data.metrics.blockedDepartments)}건</strong>
          <small>이관/정리 필요</small>
        </article>
      </div>

      {readOnly && data.permissions.readOnlyMessage ? (
        <div className="dashboard-api-alert compact">
          <ShieldCheck size={16} />
          <span>{data.permissions.readOnlyMessage}</span>
        </div>
      ) : null}
      {message ? <div className="notes-action-feedback success">{message}</div> : null}
      {error ? <div className="notes-action-feedback error">{error}</div> : null}

      <section className="dashboard-panel company-management-toolbar">
        <label className="search-box company-management-search">
          <Search size={17} />
          <input onChange={(event) => setQuery(event.target.value)} placeholder="업체, 부서, 담당자 검색" value={query} />
        </label>
        {!readOnly ? (
          <div className="company-management-create">
            <input onChange={(event) => setCompanyCreateName(event.target.value)} placeholder="새 업체/학교명" value={companyCreateName} />
            <button className="route-secondary-action" disabled={savingKey === 'company-create' || !companyCreateName.trim()} onClick={handleCreateCompany} type="button">
              {savingKey === 'company-create' ? <Loader2 className="spin-icon" size={14} /> : <Plus size={14} />}
              업체 추가
            </button>
          </div>
        ) : null}
      </section>

      <div className="company-management-layout">
        <section className="dashboard-panel company-management-list-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Companies</span>
              <h2>업체/학교</h2>
            </div>
            <span className="customer-manage-count">{formatNumber(data.companies.length)}개</span>
          </div>
          {data.companies.length === 0 ? (
            <DashboardEmpty label="조건에 맞는 업체/학교가 없습니다" />
          ) : (
            <div className="company-management-list">
              {data.companies.map((company) => (
                <CompanyRow
                  company={company}
                  editName={companyEditName}
                  editing={companyEditId === company.id}
                  key={company.id}
                  saving={savingKey === `company-${company.id}`}
                  selected={selectedCompany?.id === company.id}
                  onDelete={handleCompanyDelete}
                  onEditCancel={() => { setCompanyEditId(null); setCompanyEditName(''); }}
                  onEditNameChange={setCompanyEditName}
                  onEditStart={handleCompanyEditStart}
                  onEditSubmit={handleCompanyEditSubmit}
                  onSelect={(companyId) => setSelectedCompanyId(String(companyId))}
                />
              ))}
            </div>
          )}
        </section>

        <section className="dashboard-panel company-management-detail-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Departments</span>
              <h2>{selectedCompany?.name || '부서/연구실'}</h2>
            </div>
            {selectedCompany ? <a className="route-secondary-action" href={selectedCompany.href}>선택 고정</a> : null}
          </div>
          {selectedCompany ? (
            <>
              <div className="company-management-department-tools">
                <label className="search-box">
                  <Search size={16} />
                  <input onChange={(event) => setDepartmentQuery(event.target.value)} placeholder="부서/연구실 검색" value={departmentQuery} />
                </label>
                {!readOnly ? (
                  <div className="company-management-create">
                    <input onChange={(event) => setDepartmentCreateName(event.target.value)} placeholder="새 부서/연구실명" value={departmentCreateName} />
                    <button className="route-secondary-action" disabled={savingKey === 'department-create' || !departmentCreateName.trim()} onClick={handleCreateDepartment} type="button">
                      {savingKey === 'department-create' ? <Loader2 className="spin-icon" size={14} /> : <Plus size={14} />}
                      부서 추가
                    </button>
                  </div>
                ) : null}
              </div>
              {visibleDepartments.length === 0 ? (
                <DashboardEmpty label="조건에 맞는 부서/연구실이 없습니다" />
              ) : (
                <div className="company-management-department-list">
                  {visibleDepartments.map((department) => (
                    <DepartmentRow
                      department={department}
                      editName={departmentEditName}
                      editing={departmentEditId === department.id}
                      key={department.id}
                      saving={savingKey === `department-${department.id}`}
                      onDelete={handleDepartmentDelete}
                      onEditCancel={() => { setDepartmentEditId(null); setDepartmentEditName(''); }}
                      onEditNameChange={setDepartmentEditName}
                      onEditStart={handleDepartmentEditStart}
                      onEditSubmit={handleDepartmentEditSubmit}
                    />
                  ))}
                </div>
              )}
            </>
          ) : (
            <DashboardEmpty label="업체/학교를 선택하세요" />
          )}
        </section>
      </div>
    </section>
  );
}
