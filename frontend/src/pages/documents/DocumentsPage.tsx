import { useRef, useState, type FormEvent } from 'react';
import {
    Check,
    Copy,
    Download,
    FileSpreadsheet,
    Plus,
    Star,
    X
} from 'lucide-react';
import {
    DocumentTemplateItem,
    DocumentTemplateMutationPayload,
    DocumentTemplatesData,
    createDocumentTemplate,
    deleteDocumentTemplate,
    toggleDocumentTemplateDefault,
    updateDocumentTemplate
} from '../../api';
import { DashboardApiAlert } from '../../components/shared/FeedbackStates';
import {
    formatDateLabel,
    formatDateTimeLabel,
    formatNumber
} from '../../components/shared/formatters';
import { type PipelineData } from '../../pipelineTypes';
import { WorkspaceRoutePage, shouldOpenCreatePanel, useGuidedPanelFocus } from '../shared/appShared';


type DocumentTemplateFormState = {
  companyId: string;
  description: string;
  documentType: string;
  isDefault: boolean;
  name: string;
};

const makeEmptyDocumentTemplateForm = (): DocumentTemplateFormState => ({
  companyId: '',
  description: '',
  documentType: 'quotation',
  isDefault: false,
  name: '',
});

const makeDocumentTemplateForm = (template: DocumentTemplateItem | null): DocumentTemplateFormState => ({
  companyId: template?.company?.id ? String(template.company.id) : '',
  description: template?.description || '',
  documentType: template?.documentType || 'quotation',
  isDefault: Boolean(template?.isDefault),
  name: template?.name || '',
});

export function DocumentsPage({
  data,
  loading,
  onReload,
  onTypeChange,
  routeData,
  selectedType,
}: {
  data: DocumentTemplatesData | null;
  loading: boolean;
  onReload: () => Promise<DocumentTemplatesData>;
  onTypeChange: (value: string) => void;
  routeData: PipelineData;
  selectedType: string;
}) {
  const [formOpen, setFormOpen] = useState(() => shouldOpenCreatePanel());
  const [editingTemplate, setEditingTemplate] = useState<DocumentTemplateItem | null>(null);
  const [form, setForm] = useState<DocumentTemplateFormState>(() => makeEmptyDocumentTemplateForm());
  const [file, setFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [actionId, setActionId] = useState<number | null>(null);
  const [formError, setFormError] = useState('');
  const [formMessage, setFormMessage] = useState('');
  const [copiedVariableToken, setCopiedVariableToken] = useState('');
  const documentFormPanelRef = useRef<HTMLFormElement | null>(null);

  useGuidedPanelFocus(formOpen, documentFormPanelRef, `document-${editingTemplate?.id || 'new'}`);

  const canCreate = Boolean(data?.create.canCreate);
  const documentTypes = data?.documentTypes ?? [];
  const recentGenerations = data?.recentGenerations ?? [];
  const templateVariableGroups = data?.templateVariableGroups ?? [];

  const openCreate = () => {
    setEditingTemplate(null);
    setForm(makeEmptyDocumentTemplateForm());
    setFile(null);
    setFormOpen(true);
    setFormError('');
    setFormMessage('');
  };

  const openEdit = (template: DocumentTemplateItem) => {
    setEditingTemplate(template);
    setForm(makeDocumentTemplateForm(template));
    setFile(null);
    setFormOpen(true);
    setFormError('');
    setFormMessage('');
  };

  const closeForm = () => {
    setFormOpen(false);
    setEditingTemplate(null);
    setFile(null);
    setFormError('');
  };

  const handleFormChange = (field: keyof DocumentTemplateFormState, value: string | boolean) => {
    setForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setFormError('');
  };

  const handleVariableCopy = async (token: string) => {
    try {
      await navigator.clipboard.writeText(token);
      setCopiedVariableToken(token);
      window.setTimeout(() => setCopiedVariableToken(''), 1400);
    } catch {
      setCopiedVariableToken('');
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!data || saving) return;
    if (!form.name.trim()) {
      setFormError('서류명을 입력하세요.');
      return;
    }
    if (!form.documentType) {
      setFormError('서류 종류를 선택하세요.');
      return;
    }
    if (!editingTemplate && !file) {
      setFormError('엑셀 템플릿 파일을 선택하세요.');
      return;
    }

    const payload: DocumentTemplateMutationPayload = {
      companyId: form.companyId,
      description: form.description,
      documentType: form.documentType,
      file,
      isDefault: form.isDefault,
      name: form.name.trim(),
    };

    setSaving(true);
    setFormError('');
    setFormMessage('');
    try {
      const result = editingTemplate
        ? await updateDocumentTemplate(editingTemplate.updateUrl, payload)
        : await createDocumentTemplate(data.create.submitUrl, payload);
      setFormMessage(result.message || '저장했습니다.');
      setFormOpen(false);
      setEditingTemplate(null);
      setFile(null);
      await onReload();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : '서류 템플릿 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleDefault = async (template: DocumentTemplateItem) => {
    if (actionId) return;
    setActionId(template.id);
    setFormError('');
    setFormMessage('');
    try {
      await toggleDocumentTemplateDefault(template.toggleDefaultUrl);
      await onReload();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : '기본 설정 변경에 실패했습니다.');
    } finally {
      setActionId(null);
    }
  };

  const handleDelete = async (template: DocumentTemplateItem) => {
    if (actionId || !window.confirm(`"${template.name}" 서류 템플릿을 삭제할까요?`)) return;
    setActionId(template.id);
    setFormError('');
    setFormMessage('');
    try {
      const result = await deleteDocumentTemplate(template.deleteUrl);
      setFormMessage(result.message || '삭제했습니다.');
      await onReload();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : '삭제에 실패했습니다.');
    } finally {
      setActionId(null);
    }
  };

  if (loading && !data) {
    return <div className="documents-page"><div className="empty-state">서류 템플릿을 불러오는 중입니다.</div></div>;
  }

  return (
    <section className="documents-page">
      <WorkspaceRoutePage data={routeData} view="documents" />
      {data?.source !== 'django' ? (
        <DashboardApiAlert message={data?.error} title="서류 정보를 불러오지 못했습니다" />
      ) : null}

      <div className="documents-layout">
        <section className="documents-main">
          <div className="section-heading-row">
            <div>
              <p className="eyebrow">Templates</p>
              <h2>서류 템플릿</h2>
            </div>
            <div className="schedules-summary-actions">
              {canCreate ? (
                <button type="button" className="route-secondary-action primary" onClick={openCreate}>
                  <Plus size={16} />
                  등록
                </button>
              ) : null}
            </div>
          </div>

          <div className="documents-filter-bar">
            <button className={!selectedType ? 'active' : ''} type="button" onClick={() => onTypeChange('')}>전체</button>
            {documentTypes.map((type) => (
              <button
                className={selectedType === type.value ? 'active' : ''}
                key={type.value}
                type="button"
                onClick={() => onTypeChange(type.value)}
              >
                {type.label}
              </button>
            ))}
          </div>

          {formError ? <p className="form-error">{formError}</p> : null}
          {formMessage ? <p className="form-success">{formMessage}</p> : null}

          {data?.templates.length ? (
            <div className="document-template-grid">
              {data.templates.map((template) => (
                <article className={`document-template-card ${template.isDefault ? 'default' : ''}`} key={template.id}>
                  <div className="document-template-card-head">
                    <div className="document-template-icon">
                      <FileSpreadsheet size={20} />
                    </div>
                    <div>
                      <h3>{template.name}</h3>
                      <span>{template.documentTypeLabel} · {template.company.name}</span>
                    </div>
                    {template.isDefault ? <strong className="status-pill done">기본</strong> : null}
                  </div>
                  {template.description ? <p>{template.description}</p> : <p className="muted-text">설명이 없습니다.</p>}
                  <dl className="document-template-meta">
                    <div>
                      <dt>파일</dt>
                      <dd>{template.fileName || template.fileType}</dd>
                    </div>
                    <div>
                      <dt>등록</dt>
                      <dd>{template.createdBy || '-'} · {formatDateTimeLabel(template.createdAt)}</dd>
                    </div>
                    <div>
                      <dt>수정</dt>
                      <dd>{formatDateTimeLabel(template.updatedAt) || '-'}</dd>
                    </div>
                  </dl>
                  <div className="document-template-actions">
                    <a className="icon-button" aria-label="다운로드" href={template.downloadHref}>
                      <Download size={17} />
                    </a>
                    {template.canToggleDefault ? (
                      <button
                        aria-label={template.isDefault ? '기본 해제' : '기본 설정'}
                        className="icon-button"
                        disabled={actionId === template.id}
                        onClick={() => handleToggleDefault(template)}
                        type="button"
                      >
                        <Star size={17} />
                      </button>
                    ) : null}
                    {template.canManage ? (
                      <>
                        <button className="route-secondary-action" onClick={() => openEdit(template)} type="button">수정</button>
                        <button
                          className="route-secondary-action danger"
                          disabled={actionId === template.id}
                          onClick={() => handleDelete(template)}
                          type="button"
                        >
                          삭제
                        </button>
                      </>
                    ) : null}
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-state compact">조건에 맞는 서류 템플릿이 없습니다.</div>
          )}
        </section>

        <aside className="documents-side">
          <div className="document-summary-panel">
            <h3>요약</h3>
            <div className="document-summary-metrics">
              <div>
                <span>전체</span>
                <strong>{formatNumber(data?.summary.totalTemplates ?? 0)}</strong>
              </div>
              <div>
                <span>기본</span>
                <strong>{formatNumber(data?.summary.defaultTemplates ?? 0)}</strong>
              </div>
              <div>
                <span>오늘 생성</span>
                <strong>{formatNumber(data?.summary.generatedToday ?? 0)}</strong>
              </div>
              <div>
                <span>최근 이력</span>
                <strong>{formatNumber(data?.summary.recentGenerationCount ?? 0)}</strong>
              </div>
            </div>
            <div className="document-type-summary">
              {(data?.summary.byType ?? []).map((item) => (
                <div key={item.type}>
                  <span>{item.label}</span>
                  <strong>{formatNumber(item.count)}</strong>
                  <small>기본 {formatNumber(item.defaultCount)}</small>
                </div>
              ))}
            </div>
          </div>

          {formOpen ? (
            <form className="document-template-form" onSubmit={handleSubmit} ref={documentFormPanelRef}>
              <div className="section-heading-row compact">
                <div>
                  <p className="eyebrow">{editingTemplate ? 'Edit' : 'Create'}</p>
                  <h3>{editingTemplate ? '서류 수정' : '서류 등록'}</h3>
                </div>
                <button className="icon-button" aria-label="닫기" onClick={closeForm} type="button">
                  <X size={17} />
                </button>
              </div>
              {data?.currentUser.isSuperuser && data.create.companies.length ? (
                <label>
                  <span>회사</span>
                  <select value={form.companyId} onChange={(event) => handleFormChange('companyId', event.target.value)} disabled={Boolean(editingTemplate)}>
                    <option value="">선택</option>
                    {data.create.companies.map((company) => (
                      <option key={company.id} value={company.id}>{company.name}</option>
                    ))}
                  </select>
                </label>
              ) : null}
              <label>
                <span>서류 종류</span>
                <select value={form.documentType} onChange={(event) => handleFormChange('documentType', event.target.value)}>
                  {documentTypes.map((type) => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>서류명</span>
                <input value={form.name} onChange={(event) => handleFormChange('name', event.target.value)} />
              </label>
              <label>
                <span>설명</span>
                <textarea value={form.description} onChange={(event) => handleFormChange('description', event.target.value)} rows={4} />
              </label>
              <label>
                <span>{editingTemplate ? '파일 교체' : '파일'}</span>
                <input accept=".xlsx,.xls" onChange={(event) => setFile(event.target.files?.[0] ?? null)} type="file" />
              </label>
              {editingTemplate?.fileName ? <small>현재 파일: {editingTemplate.fileName}</small> : null}
              {templateVariableGroups.length > 0 ? (
                <div className="document-variable-panel">
                  <div className="section-heading-row compact">
                    <div>
                      <p className="eyebrow">Variables</p>
                      <h3>사용 가능한 템플릿 변수</h3>
                    </div>
                  </div>
                  <div className="document-variable-groups">
                    {templateVariableGroups.map((group) => (
                      <div className="document-variable-group" key={group.label}>
                        <h4>{group.label}</h4>
                        <div className="document-variable-chip-list">
                          {group.variables.map((variable) => (
                            <button
                              className={copiedVariableToken === variable.token ? 'copied' : ''}
                              key={variable.token}
                              onClick={() => handleVariableCopy(variable.token)}
                              type="button"
                            >
                              {copiedVariableToken === variable.token ? <Check size={13} /> : <Copy size={13} />}
                              <span>{variable.display || variable.token}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
              <label className="checkbox-row">
                <input checked={form.isDefault} onChange={(event) => handleFormChange('isDefault', event.target.checked)} type="checkbox" />
                <span>기본 템플릿으로 설정</span>
              </label>
              <button className="primary-button" disabled={saving || !canCreate && !editingTemplate} type="submit">
                {saving ? '저장 중' : '저장'}
              </button>
              {!canCreate && !editingTemplate ? <p className="form-error">{data?.create.message}</p> : null}
            </form>
          ) : (
            <div className="document-summary-panel">
              <h3>연결 화면</h3>
              <div className="button-stack">
                <a className="route-secondary-action" href={data?.links.scheduleList || '/schedules/'}>일정 목록</a>
                <a className="route-secondary-action" href={data?.links.scheduleCalendar || '/schedules/calendar/'}>일정 캘린더</a>
              </div>
            </div>
          )}

          <div className="document-summary-panel document-generation-panel">
            <h3>최근 생성 이력</h3>
            {recentGenerations.length ? (
              <div className="document-generation-list">
                {recentGenerations.map((generation) => {
                  const customerLine = [
                    generation.customerCompany,
                    generation.departmentName,
                    generation.customerName,
                  ].filter(Boolean).join(' · ');
                  const cardBody = (
                    <>
                      <div className="document-generation-card-head">
                        <span>{generation.quoteGroupLabel ? `${generation.quoteGroupLabel} ${generation.documentTypeLabel}` : generation.documentTypeLabel}</span>
                        <strong>{generation.transactionNumber}</strong>
                      </div>
                      <div className="document-generation-card-meta">
                        <span>{generation.outputFormatLabel}</span>
                        <span>{formatDateTimeLabel(generation.createdAt)}</span>
                      </div>
                      <p>{customerLine || '연결된 고객 정보가 없습니다.'}</p>
                      <small>
                        {[generation.createdBy, generation.schedule.visitDate ? `일정 ${formatDateLabel(generation.schedule.visitDate)}` : ''].filter(Boolean).join(' · ')}
                      </small>
                    </>
                  );
                  return generation.schedule.href ? (
                    <a className="document-generation-card" href={generation.schedule.href} key={generation.id}>
                      {cardBody}
                    </a>
                  ) : (
                    <div className="document-generation-card" key={generation.id}>
                      {cardBody}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="empty-state compact">최근 생성된 서류가 없습니다.</div>
            )}
          </div>
        </aside>
      </div>
    </section>
  );
}