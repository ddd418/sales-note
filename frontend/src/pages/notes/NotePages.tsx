import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from 'react';
import {
    AlertTriangle,
    Check,
    CheckCircle2,
    Clock,
    FileText,
    Filter,
    Loader2,
    MessageSquareText,
    MoveUpRight,
    PanelRight,
    Plus,
    Search,
    Trash2
} from 'lucide-react';
import {
    NoteDetailData,
    NoteDetailItem,
    NoteEditPayload,
    NoteFileItem,
    NoteItem,
    NoteReplyItem,
    NotesData,
    addNoteReply,
    deleteNoteFile,
    deleteNoteReply,
    deleteNote as deleteSalesNote,
    toggleNoteReviewed,
    updateNote as updateSalesNote,
    uploadNoteFiles
} from '../../api';
import { AttachmentManager, type AttachmentManagerFile } from '../../components/shared/AttachmentManager';
import { DashboardMetricCard } from '../../components/shared/DashboardMetricCard';
import { DashboardApiAlert, DashboardEmpty } from '../../components/shared/FeedbackStates';
import {
    formatDateLabel,
    formatDateTimeLabel,
    formatNumber,
    formatWon
} from '../../components/shared/formatters';
import { CustomerDetailNoteList, NoteCreateFormState, SearchableSelect, customersForDepartment, isNoteActionAllowed, makeCustomerSelectOption, makeDepartmentSelectOption, noteNextActionLabel, useGuidedPanelFocus } from '../shared/appShared';


type NoteEditFormState = NoteCreateFormState & {
  deliveryAmount: string;
  deliveryItems: string;
};

const makeNoteEditForm = (note: NoteDetailItem | null): NoteEditFormState => ({
  actionType: note?.actionType || 'customer_meeting',
  activityDate: note?.meetingDate || note?.deliveryDate || note?.activityDate || '',
  content: note?.content || '',
  departmentId: note?.departmentId ? String(note.departmentId) : '',
  deliveryAmount: note?.deliveryAmount ? String(note.deliveryAmount) : '',
  deliveryItems: note?.deliveryItems || '',
  followupId: note?.followupId ? String(note.followupId) : '',
  nextAction: note?.nextAction || '',
  nextActionDate: note?.nextActionDate || '',
  scheduleId: note?.scheduleId ? String(note.scheduleId) : '',
});

function NoteStatusBadge({ note }: { note: NoteItem }) {
  const reviewLabel = note.reviewed ? '검토 완료' : note.reviewRequired ? '미검토' : '검토 불필요';
  return (
    <div className="customer-badge-row notes-badge-row">
      <span className={`note-action ${note.actionType}`}>{note.actionLabel}</span>
      <span className={note.reviewed ? 'note-reviewed' : note.reviewRequired ? 'note-unreviewed' : ''}>
        {reviewLabel}
      </span>
      {note.overdue ? <span className="note-overdue">지연</span> : null}
      {note.serviceStatusLabel ? <span>{note.serviceStatusLabel}</span> : null}
    </div>
  );
}

function NotesActionCounts({ data }: { data: NotesData }) {
  const maxCount = Math.max(...data.actionCounts.map((item) => item.count), 1);
  return (
    <div className="notes-action-counts">
      {data.actionCounts.map((item) => (
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

function NotesTable({
  canReview,
  notes,
  onToggleReview,
  reviewingNoteId,
}: {
  canReview: boolean;
  notes: NoteItem[];
  onToggleReview: (note: NoteItem) => void;
  reviewingNoteId: number | null;
}) {
  if (notes.length === 0) {
    return <DashboardEmpty label="조건에 맞는 영업노트가 없습니다" />;
  }

  return (
    <div className="customers-table-wrap notes-table-wrap">
      <table className="customers-table notes-table">
        <thead>
          <tr>
            <th>영업노트</th>
            <th>다음 액션</th>
            <th>상태</th>
            <th>연결</th>
            <th>담당자</th>
          </tr>
        </thead>
        <tbody>
          {notes.map((note) => (
            <tr key={note.id}>
              <td>
                <a className="customer-name-link" href={note.href}>
                  <strong>{note.company || note.customer}</strong>
                  <span>{[note.customer, note.department, note.actionLabel].filter(Boolean).join(' · ')}</span>
                  {note.summary ? <small>{note.summary}</small> : null}
                  {note.fileCount > 0 || note.replyCount > 0 ? (
                    <div className="note-meta-row">
                      {note.fileCount > 0 ? <span>첨부 {formatNumber(note.fileCount)}</span> : null}
                      {note.replyCount > 0 ? <span>댓글 {formatNumber(note.replyCount)}</span> : null}
                    </div>
                  ) : null}
                </a>
              </td>
              <td>
                <span className={note.overdue ? 'customer-overdue-text' : ''}>
                  {noteNextActionLabel(note) || '다음 액션 없음'}
                </span>
                {note.nextActionDate ? <small>{formatDateLabel(note.nextActionDate)}</small> : null}
              </td>
              <td>
                <NoteStatusBadge note={note} />
                {note.reviewedAt ? (
                  <small>{[note.reviewer, formatDateTimeLabel(note.reviewedAt)].filter(Boolean).join(' · ')}</small>
                ) : null}
              </td>
              <td>
                <div className="notes-row-actions">
                  <a className="customer-row-action" href={note.href}>상세</a>
                  {note.customerHref ? <a className="customer-row-action" href={note.customerHref}>고객</a> : null}
                  {note.scheduleHref ? <a className="customer-row-action" href={note.scheduleHref}>일정</a> : null}
                  {canReview && note.canReview && note.reviewToggleHref ? (
                    <button
                      className="customer-row-action note-review-action"
                      disabled={reviewingNoteId === note.id}
                      onClick={() => onToggleReview(note)}
                      type="button"
                    >
                      {reviewingNoteId === note.id ? <Loader2 className="spin-icon" size={12} /> : <CheckCircle2 size={12} />}
                      {note.reviewed ? '검토 해제' : '검토 완료'}
                    </button>
                  ) : null}
                </div>
              </td>
              <td>
                <span>{note.owner}</span>
                <small>{note.activityDate ? formatDateLabel(note.activityDate) : formatDateTimeLabel(note.createdAt)}</small>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function NoteDetailPage({
  data,
  loading,
  onRefresh,
}: {
  data: NoteDetailData | null;
  loading: boolean;
  onRefresh: () => Promise<NoteDetailData | null>;
}) {
  const currentNote = data?.note ?? null;
  const [editOpen, setEditOpen] = useState(false);
  const [editForm, setEditForm] = useState<NoteEditFormState>(() => makeNoteEditForm(currentNote));
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState('');
  const [editMessage, setEditMessage] = useState('');
  const [reviewing, setReviewing] = useState(false);
  const noteFileInputRef = useRef<HTMLInputElement | null>(null);
  const [noteFileUploading, setNoteFileUploading] = useState(false);
  const [noteFileDeletingId, setNoteFileDeletingId] = useState<number | null>(null);
  const [noteFileError, setNoteFileError] = useState('');
  const [noteFileMessage, setNoteFileMessage] = useState('');
  const [replyText, setReplyText] = useState('');
  const [replySaving, setReplySaving] = useState(false);
  const [replyDeletingId, setReplyDeletingId] = useState<number | null>(null);
  const [replyError, setReplyError] = useState('');
  const [replyMessage, setReplyMessage] = useState('');
  const [noteDeleting, setNoteDeleting] = useState(false);
  const [noteDeleteError, setNoteDeleteError] = useState('');
  const [noteDeleteMessage, setNoteDeleteMessage] = useState('');
  const noteEditPanelRef = useRef<HTMLElement | null>(null);

  useGuidedPanelFocus(editOpen, noteEditPanelRef, `note-edit-${currentNote?.id || 'new'}`);

  useEffect(() => {
    setEditForm(makeNoteEditForm(currentNote));
    setEditError('');
    setEditMessage('');
    setEditOpen(false);
    setNoteFileError('');
    setNoteFileMessage('');
    setNoteFileUploading(false);
    setNoteFileDeletingId(null);
    setReplyText('');
    setReplyError('');
    setReplyMessage('');
    setReplySaving(false);
    setReplyDeletingId(null);
    setNoteDeleting(false);
    setNoteDeleteError('');
    setNoteDeleteMessage('');
    if (noteFileInputRef.current) {
      noteFileInputRef.current.value = '';
    }
  }, [currentNote?.id]);

  const editConfig = data?.edit;
  const activityDateVisible = editForm.actionType === 'customer_meeting' || editForm.actionType === 'delivery_schedule';
  const editCustomers = editConfig?.customers ?? [];
  const editDepartments = editConfig?.departments ?? [];
  const filteredEditCustomers = customersForDepartment(editCustomers, editForm.departmentId);
  const selectedEditDepartmentHasCustomers = filteredEditCustomers.length > 0;
  const editCustomerCanBeEmpty = Boolean(editForm.departmentId) && (
    !selectedEditDepartmentHasCustomers || !currentNote?.followupId
  );

  const handleEditFieldChange = (field: keyof NoteEditFormState, value: string) => {
    setEditForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setEditError('');
    setEditMessage('');
  };

  const handleEditDepartmentChange = (nextValue: string) => {
    const nextCustomers = customersForDepartment(editCustomers, nextValue);
    const currentCustomerStillAvailable = nextCustomers.some((customer) => String(customer.id) === editForm.followupId);
    setEditForm((previous) => ({
      ...previous,
      departmentId: nextValue,
      followupId: currentCustomerStillAvailable ? previous.followupId : '',
    }));
    setEditError('');
    setEditMessage('');
  };

  const handleEditCustomerChange = (nextValue: string) => {
    const nextCustomer = editCustomers.find((customer) => String(customer.id) === nextValue);
    setEditForm((previous) => ({
      ...previous,
      departmentId: nextCustomer?.departmentId ? String(nextCustomer.departmentId) : previous.departmentId,
      followupId: nextValue,
    }));
    setEditError('');
    setEditMessage('');
  };

  const handleEditSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!currentNote || !editConfig || editSaving) {
      return;
    }
    if (!editConfig.canEdit) {
      setEditError(editConfig.message || '수정 권한이 없습니다.');
      return;
    }
    const followupId = Number(editForm.followupId);
    const departmentId = Number(editForm.departmentId);
    if (!followupId && !departmentId) {
      setEditError('고객 또는 부서/연구실을 선택하세요.');
      return;
    }
    if (!editForm.actionType) {
      setEditError('활동 유형을 선택하세요.');
      return;
    }
    if (!editForm.content.trim()) {
      setEditError('활동 내용을 입력하세요.');
      return;
    }
    const payload: NoteEditPayload = {
      actionType: editForm.actionType,
      activityDate: activityDateVisible ? editForm.activityDate || undefined : undefined,
      content: editForm.content.trim(),
      departmentId: departmentId || undefined,
      deliveryAmount: editForm.deliveryAmount.trim() || undefined,
      deliveryItems: editForm.deliveryItems.trim() || undefined,
      followupId: followupId || undefined,
      nextAction: editForm.nextAction.trim() || undefined,
      nextActionDate: editForm.nextActionDate || undefined,
    };

    setEditSaving(true);
    setEditError('');
    setEditMessage('');
    try {
      const updated = await updateSalesNote(payload, editConfig.submitUrl);
      await onRefresh();
      setEditMessage(updated.message || '영업노트를 수정했습니다.');
      setEditOpen(false);
    } catch (error) {
      setEditError(error instanceof Error ? error.message : '영업노트 수정에 실패했습니다.');
    } finally {
      setEditSaving(false);
    }
  };

  const handleToggleReview = async () => {
    if (!currentNote?.reviewToggleHref || reviewing) {
      return;
    }
    setReviewing(true);
    setEditError('');
    setEditMessage('');
    try {
      await toggleNoteReviewed(currentNote.reviewToggleHref);
      await onRefresh();
      setEditMessage(currentNote.reviewed ? '검토 상태를 해제했습니다.' : '검토 완료로 처리했습니다.');
    } catch (error) {
      setEditError(error instanceof Error ? error.message : '검토 상태 변경에 실패했습니다.');
    } finally {
      setReviewing(false);
    }
  };

  const handleDeleteNote = async () => {
    if (!currentNote?.canDelete || !currentNote.deleteHref || noteDeleting) {
      setNoteDeleteError('삭제 권한이 없습니다.');
      setNoteDeleteMessage('');
      return;
    }
    if (!window.confirm('이 영업노트를 삭제할까요? 첨부파일과 댓글도 함께 정리됩니다.')) {
      return;
    }

    setNoteDeleting(true);
    setNoteDeleteError('');
    setNoteDeleteMessage('');
    try {
      const result = await deleteSalesNote(currentNote.deleteHref);
      setNoteDeleteMessage(result.message || '영업노트를 삭제했습니다.');
      window.location.assign(result.redirect || '/notes/');
    } catch (error) {
      setNoteDeleteError(error instanceof Error ? error.message : '영업노트 삭제에 실패했습니다.');
    } finally {
      setNoteDeleting(false);
    }
  };

  const handleNoteFileUploadClick = () => {
    if (!currentNote?.canEdit || !data?.links.uploadFiles) {
      setNoteFileError('첨부파일 업로드 권한이 없습니다.');
      setNoteFileMessage('');
      return;
    }
    noteFileInputRef.current?.click();
  };

  const handleNoteFilesSelected = async (event: ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files ?? []);
    if (!selectedFiles.length) {
      return;
    }

    if (!currentNote?.canEdit || !data?.links.uploadFiles) {
      setNoteFileError('첨부파일 업로드 권한이 없습니다.');
      setNoteFileMessage('');
      event.target.value = '';
      return;
    }

    if (currentNote.files.length + selectedFiles.length > 5) {
      setNoteFileError(`첨부파일은 최대 5개까지 등록할 수 있습니다. 현재 ${currentNote.files.length}개가 등록되어 있습니다.`);
      setNoteFileMessage('');
      event.target.value = '';
      return;
    }

    setNoteFileUploading(true);
    setNoteFileError('');
    setNoteFileMessage('');
    try {
      const result = await uploadNoteFiles(data.links.uploadFiles, selectedFiles);
      await onRefresh();
      setNoteFileMessage(result.message || `${selectedFiles.length}개 파일을 업로드했습니다.`);
    } catch (error) {
      setNoteFileError(error instanceof Error ? error.message : '첨부파일 업로드에 실패했습니다.');
    } finally {
      setNoteFileUploading(false);
      event.target.value = '';
    }
  };

  const handleNoteFileDelete = async (file: NoteFileItem | AttachmentManagerFile) => {
    if (noteFileDeletingId !== null) {
      return;
    }
    if (!currentNote?.canEdit || !file.canDelete || !file.deleteHref) {
      setNoteFileError('첨부파일 삭제 권한이 없습니다.');
      setNoteFileMessage('');
      return;
    }
    if (!window.confirm(`"${file.filename}" 파일을 삭제할까요?`)) {
      return;
    }

    setNoteFileDeletingId(Number(file.id));
    setNoteFileError('');
    setNoteFileMessage('');
    try {
      const result = await deleteNoteFile(file.deleteHref);
      await onRefresh();
      setNoteFileMessage(result.message || '첨부파일을 삭제했습니다.');
    } catch (error) {
      setNoteFileError(error instanceof Error ? error.message : '첨부파일 삭제에 실패했습니다.');
    } finally {
      setNoteFileDeletingId(null);
    }
  };

  const handleReplySubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const memo = replyText.trim();
    if (!memo) {
      setReplyError('댓글 내용을 입력하세요.');
      setReplyMessage('');
      return;
    }
    if (!data?.comments.canCreate || !data.comments.submitUrl || replySaving) {
      setReplyError(data?.comments.message || '댓글 작성 권한이 없습니다.');
      setReplyMessage('');
      return;
    }

    setReplySaving(true);
    setReplyError('');
    setReplyMessage('');
    try {
      const result = await addNoteReply(data.comments.submitUrl, memo);
      await onRefresh();
      setReplyText('');
      setReplyMessage(result.message || '댓글을 추가했습니다.');
    } catch (error) {
      setReplyError(error instanceof Error ? error.message : '댓글 작성에 실패했습니다.');
    } finally {
      setReplySaving(false);
    }
  };

  const handleReplyDelete = async (reply: NoteReplyItem) => {
    if (replyDeletingId !== null) {
      return;
    }
    if (!reply.canDelete || !reply.deleteHref) {
      setReplyError('댓글 삭제 권한이 없습니다.');
      setReplyMessage('');
      return;
    }
    if (!window.confirm('이 댓글을 삭제할까요?')) {
      return;
    }

    setReplyDeletingId(reply.id);
    setReplyError('');
    setReplyMessage('');
    try {
      const result = await deleteNoteReply(reply.deleteHref);
      await onRefresh();
      setReplyMessage(result.message || '댓글을 삭제했습니다.');
    } catch (error) {
      setReplyError(error instanceof Error ? error.message : '댓글 삭제에 실패했습니다.');
    } finally {
      setReplyDeletingId(null);
    }
  };

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>영업노트 상세 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data || !data.note) {
    return (
      <section className="notes-page">
        <div className="dashboard-api-alert">
          <AlertTriangle size={18} />
          <div>
            <strong>영업노트 상세를 불러오지 못했습니다</strong>
            <span>{data?.error || '영업노트 상세 정보를 불러오지 못했습니다.'}</span>
          </div>
          <a href="/notes/">목록</a>
        </div>
      </section>
    );
  }

  const note = data.note;
  const deleteRequested = new URLSearchParams(window.location.search).get('delete') === '1';
  const metrics = [
    { label: '활동 유형', value: note.actionLabel, detail: note.owner, icon: FileText, tone: 'blue' as const },
    { label: '검토 상태', value: note.reviewed ? '완료' : note.reviewRequired ? '미검토' : '불필요', detail: note.reviewer || data.scope.label, icon: CheckCircle2, tone: note.reviewed ? 'green' as const : 'amber' as const },
    { label: '다음 예정일', value: note.nextActionDate ? formatDateLabel(note.nextActionDate) : '없음', detail: note.overdue ? '지연' : '후속 액션', icon: Clock, tone: note.overdue ? 'red' as const : 'teal' as const },
    { label: '첨부/댓글', value: `${formatNumber(note.fileCount)} / ${formatNumber(note.replyCount)}`, detail: '파일 / 댓글', icon: MessageSquareText, tone: 'green' as const },
  ];

  return (
    <section className="notes-page note-detail-page">
      {data.source !== 'django' ? (
        <DashboardApiAlert message={data.error} title="영업노트 상세 정보를 불러오지 못했습니다" />
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Note detail</span>
          <h2>{note.company || note.customer || note.actionLabel}</h2>
          <p>{[note.customer, note.department, note.actionLabel, note.owner].filter(Boolean).join(' · ')}</p>
        </div>
        <div className="schedules-summary-actions">
          <a className="route-secondary-action" href="/notes/">목록</a>
          {data.links.customer ? <a className="route-secondary-action" href={data.links.customer}>고객</a> : null}
          {note.canReview && note.reviewToggleHref ? (
            <button className="route-secondary-action" disabled={reviewing} onClick={handleToggleReview} type="button">
              {reviewing ? <Loader2 className="spin-icon" size={15} /> : <CheckCircle2 size={15} />}
              {note.reviewed ? '검토 해제' : '검토 완료'}
            </button>
          ) : null}
          {data.edit.canEdit ? (
            <button className="route-primary-action" onClick={() => setEditOpen((open) => !open)} type="button">
              수정
              <Check size={16} />
            </button>
          ) : null}
          {note.canDelete && note.deleteHref ? (
            <button className="route-secondary-action danger" disabled={noteDeleting} onClick={handleDeleteNote} type="button">
              {noteDeleting ? <Loader2 className="spin-icon" size={15} /> : <Trash2 size={15} />}
              삭제
            </button>
          ) : null}
        </div>
      </div>

      {deleteRequested && note.canDelete ? (
        <div className="dashboard-api-alert compact">
          <AlertTriangle size={16} />
          <span>삭제 요청으로 들어왔습니다. 상단의 삭제 버튼으로 확정하세요.</span>
        </div>
      ) : null}
      {noteDeleteError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{noteDeleteError}</span></div> : null}
      {noteDeleteMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{noteDeleteMessage}</span></div> : null}

      <section className="dashboard-metric-grid" aria-label="영업노트 상세 지표">
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

      {editOpen || editMessage || editError ? (
        <section className="dashboard-panel notes-create-panel note-edit-panel" ref={noteEditPanelRef}>
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Edit note</span>
              <h2>영업노트 수정</h2>
            </div>
            {editSaving ? <Loader2 className="spin-icon" size={18} /> : <FileText size={18} />}
          </div>
          {editError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{editError}</span></div> : null}
          {editMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{editMessage}</span></div> : null}
          {editOpen ? (
            <form className="notes-create-form note-edit-form" onSubmit={handleEditSubmit}>
              <div className="notes-create-grid">
                <div className="form-field">
                  <span>부서/연구실</span>
                  <SearchableSelect
                    ariaLabel="부서/연구실 선택"
                    onChange={handleEditDepartmentChange}
                    options={editDepartments.map(makeDepartmentSelectOption)}
                    placeholder="회사, 부서/연구실, 담당자 검색"
                    value={editForm.departmentId}
                  />
                </div>
                <div className="form-field">
                  <span>고객</span>
                  <SearchableSelect
                    allowEmpty={editCustomerCanBeEmpty}
                    ariaLabel="고객 선택"
                    disabled={Boolean(editForm.departmentId) && !selectedEditDepartmentHasCustomers}
                    emptyLabel="부서에만 연결"
                    onChange={handleEditCustomerChange}
                    options={filteredEditCustomers.map(makeCustomerSelectOption)}
                    placeholder="고객, 회사, 부서 검색"
                    value={editForm.followupId}
                  />
                </div>
                <label>
                  <span>활동 유형</span>
                  <select
                    onChange={(event) => handleEditFieldChange('actionType', event.target.value)}
                    required
                    value={editForm.actionType}
                  >
                    {data.edit.actionTypes.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                {activityDateVisible ? (
                  <label>
                    <span>{editForm.actionType === 'delivery_schedule' ? '납품일' : '미팅일'}</span>
                    <input
                      onChange={(event) => handleEditFieldChange('activityDate', event.target.value)}
                      type="date"
                      value={editForm.activityDate}
                    />
                  </label>
                ) : null}
                <label>
                  <span>다음 예정일</span>
                  <input
                    onChange={(event) => handleEditFieldChange('nextActionDate', event.target.value)}
                    type="date"
                    value={editForm.nextActionDate}
                  />
                </label>
                {editForm.actionType === 'delivery_schedule' ? (
                  <label>
                    <span>납품 금액</span>
                    <input
                      min="0"
                      onChange={(event) => handleEditFieldChange('deliveryAmount', event.target.value)}
                      type="number"
                      value={editForm.deliveryAmount}
                    />
                  </label>
                ) : null}
              </div>
              <label>
                <span>활동 내용</span>
                <textarea
                  onChange={(event) => handleEditFieldChange('content', event.target.value)}
                  required
                  rows={4}
                  value={editForm.content}
                />
              </label>
              {editForm.actionType === 'delivery_schedule' ? (
                <label>
                  <span>납품 품목</span>
                  <textarea
                    onChange={(event) => handleEditFieldChange('deliveryItems', event.target.value)}
                    rows={3}
                    value={editForm.deliveryItems}
                  />
                </label>
              ) : null}
              <label>
                <span>다음 액션</span>
                <textarea
                  onChange={(event) => handleEditFieldChange('nextAction', event.target.value)}
                  rows={2}
                  value={editForm.nextAction}
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

      <div className="note-detail-layout">
        <section className="dashboard-panel note-detail-main">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Activity</span>
              <h2>활동 내용</h2>
            </div>
            <NoteStatusBadge note={note} />
          </div>
          <div className="note-detail-content">
            {note.content ? <p>{note.content}</p> : <DashboardEmpty label="활동 내용이 없습니다" />}
          </div>
          <div className="note-detail-next-action">
            <span>다음 액션</span>
            <p className={note.overdue ? 'customer-overdue-text' : ''}>{noteNextActionLabel(note) || '다음 액션 없음'}</p>
            {note.nextActionDate ? <small>{formatDateLabel(note.nextActionDate)}</small> : null}
          </div>
          {note.actionType === 'delivery_schedule' ? (
            <div className="note-detail-field-grid">
              <div className="note-detail-field">
                <span>납품 금액</span>
                <p>{formatWon(note.deliveryAmount)}</p>
              </div>
              {note.deliveryItems ? (
                <div className="note-detail-field">
                  <span>납품 품목</span>
                  <p>{note.deliveryItems}</p>
                </div>
              ) : null}
            </div>
          ) : null}
        </section>

        <aside className="dashboard-panel note-detail-side">
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
                <dd>{[note.company, note.department, note.customer].filter(Boolean).join(' · ') || '고객 없음'}</dd>
              </div>
              <div>
                <dt>담당자</dt>
                <dd>{note.owner}</dd>
              </div>
              <div>
                <dt>활동일</dt>
                <dd>{note.activityDate ? formatDateLabel(note.activityDate) : formatDateTimeLabel(note.createdAt)}</dd>
              </div>
              <div>
                <dt>다음 액션</dt>
                <dd className={note.overdue ? 'customer-overdue-text' : ''}>{noteNextActionLabel(note) || '다음 액션 없음'}</dd>
              </div>
            </dl>
          </div>
          <div className="customers-side-actions note-detail-actions">
            {data.links.customer ? <a href={data.links.customer}>고객 상세</a> : null}
            {data.links.schedule ? <a href={data.links.schedule}>연결 일정</a> : null}
            <a href={data.links.createNote}>새 노트 작성</a>
          </div>
          {noteFileError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{noteFileError}</span></div> : null}
          {noteFileMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{noteFileMessage}</span></div> : null}
          <AttachmentManager
            canUpload={note.canEdit && Boolean(data.links.uploadFiles)}
            deletingId={noteFileDeletingId}
            emptyLabel="첨부파일이 없습니다"
            files={note.files}
            inputRef={noteFileInputRef}
            title="첨부파일"
            uploadAriaLabel="영업노트 첨부파일 선택"
            uploading={noteFileUploading}
            onDelete={handleNoteFileDelete}
            onFilesSelected={handleNoteFilesSelected}
            onUploadClick={handleNoteFileUploadClick}
          />
          <h3 className="customer-detail-section-heading">댓글</h3>
          {data.comments.canCreate ? (
            <form className="note-reply-compose" onSubmit={handleReplySubmit}>
              <textarea
                aria-label="댓글 내용"
                onChange={(event) => {
                  setReplyText(event.target.value);
                  setReplyError('');
                  setReplyMessage('');
                }}
                rows={3}
                value={replyText}
              />
              <button className="customer-row-action note-reply-submit-button" disabled={replySaving} type="submit">
                {replySaving ? <Loader2 className="spin-icon" size={14} /> : <MessageSquareText size={14} />}
                <span>추가</span>
              </button>
            </form>
          ) : null}
          {replyError ? <div className="dashboard-api-alert compact"><AlertTriangle size={16} /><span>{replyError}</span></div> : null}
          {replyMessage ? <div className="dashboard-api-alert compact success"><CheckCircle2 size={16} /><span>{replyMessage}</span></div> : null}
          {note.replies.length === 0 ? (
            <DashboardEmpty label="댓글이 없습니다" />
          ) : (
            <div className="note-reply-list">
              {note.replies.map((reply) => (
                <div className="note-reply-row" key={reply.id}>
                  <div className="note-reply-content">
                    <strong>{reply.author}</strong>
                    <span>{[reply.authorRole, reply.createdAt ? formatDateTimeLabel(reply.createdAt) : ''].filter(Boolean).join(' · ')}</span>
                    <p>{reply.content}</p>
                  </div>
                  {reply.canDelete && reply.deleteHref ? (
                    <button
                      aria-label={`${reply.author} 댓글 삭제`}
                      className="customer-row-action note-reply-delete-button"
                      disabled={replyDeletingId === reply.id}
                      onClick={() => handleReplyDelete(reply)}
                      type="button"
                    >
                      {replyDeletingId === reply.id ? <Loader2 className="spin-icon" size={14} /> : <Trash2 size={14} />}
                      <span>삭제</span>
                    </button>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </aside>
      </div>

      <section className="dashboard-panel note-related-panel">
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">Related notes</span>
            <h2>같은 고객의 최근 노트</h2>
          </div>
          <MessageSquareText size={18} />
        </div>
        <CustomerDetailNoteList emptyLabel="같은 고객의 다른 영업노트가 없습니다" notes={data.relatedNotes} />
      </section>
    </section>
  );
}

export function NotesPage({
  actionType,
  createError,
  createForm,
  createMessage,
  createOpen,
  creating,
  data,
  dateFrom,
  dateTo,
  loading,
  nextAction,
  owner,
  query,
  reviewError,
  reviewMessage,
  reviewingNoteId,
  review,
  onActionTypeChange,
  onCreateFormChange,
  onCreateOpenChange,
  onCreateSubmit,
  onDateFromChange,
  onDateToChange,
  onNextActionChange,
  onOwnerChange,
  onQueryChange,
  onReviewChange,
  onToggleReview,
}: {
  actionType: string;
  createError: string;
  createForm: NoteCreateFormState;
  createMessage: string;
  createOpen: boolean;
  creating: boolean;
  data: NotesData | null;
  dateFrom: string;
  dateTo: string;
  loading: boolean;
  nextAction: string;
  owner: string;
  query: string;
  reviewError: string;
  reviewMessage: string;
  reviewingNoteId: number | null;
  review: string;
  onActionTypeChange: (value: string) => void;
  onCreateFormChange: (field: keyof NoteCreateFormState, value: string) => void;
  onCreateOpenChange: (open: boolean) => void;
  onCreateSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
  onNextActionChange: (value: string) => void;
  onOwnerChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onReviewChange: (value: string) => void;
  onToggleReview: (note: NoteItem) => void;
}) {
  const createPanelRef = useRef<HTMLElement | null>(null);
  useGuidedPanelFocus(createOpen, createPanelRef, 'note-create');

  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>영업노트 데이터를 불러오는 중입니다</span>
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const metrics = [
    { label: '전체 노트', value: `${formatNumber(data.metrics.totalNotes)}건`, detail: data.scope.label, icon: FileText, tone: 'blue' as const },
    { label: '검색 결과', value: `${formatNumber(data.metrics.filteredNotes)}건`, detail: '현재 필터', icon: Search, tone: 'teal' as const },
    { label: '미검토', value: `${formatNumber(data.metrics.unreviewedNotes)}건`, detail: '검토 필요', icon: CheckCircle2, tone: 'amber' as const },
    { label: '7일 이내', value: `${formatNumber(data.metrics.upcomingActions)}건`, detail: '다가오는 액션', icon: Clock, tone: 'green' as const },
  ];
  const createConfig = data.create;
  const canCreateNotes = createConfig.canCreate;
  const createCustomers = createConfig.customers;
  const createDepartments = createConfig.departments ?? [];
  const createActionTypes = createConfig.actionTypes;
  const createSchedules = createConfig.schedules ?? [];
  const filteredCreateCustomers = customersForDepartment(createCustomers, createForm.departmentId);
  const availableCreateSchedules = createSchedules.filter((schedule) => (
    createForm.followupId
      ? String(schedule.followupId) === createForm.followupId
      : !createForm.departmentId || String(schedule.departmentId || '') === createForm.departmentId
  ));
  const selectedCreateSchedule = createSchedules.find((schedule) => String(schedule.id) === createForm.scheduleId) ?? null;
  const selectedDepartmentHasCustomers = filteredCreateCustomers.length > 0;
  const handleCreateDepartmentChange = (nextValue: string) => {
    const nextCustomers = customersForDepartment(createCustomers, nextValue);
    const nextCustomerId = nextCustomers[0]?.id ? String(nextCustomers[0].id) : '';
    onCreateFormChange('departmentId', nextValue);
    onCreateFormChange('followupId', nextCustomerId);
    onCreateFormChange('scheduleId', '');
  };
  const handleCreateCustomerChange = (nextValue: string) => {
    const nextCustomer = createCustomers.find((customer) => String(customer.id) === nextValue);
    const selectedScheduleBelongsToCustomer = selectedCreateSchedule && String(selectedCreateSchedule.followupId) === nextValue;
    if (nextCustomer?.departmentId) {
      onCreateFormChange('departmentId', String(nextCustomer.departmentId));
    }
    onCreateFormChange('followupId', nextValue);
    if (!selectedScheduleBelongsToCustomer) {
      onCreateFormChange('scheduleId', '');
    }
  };
  const handleCreateScheduleChange = (nextValue: string) => {
    const nextSchedule = createSchedules.find((schedule) => String(schedule.id) === nextValue);
    onCreateFormChange('scheduleId', nextValue);
    if (!nextSchedule) {
      return;
    }
    if (String(nextSchedule.followupId) !== createForm.followupId) {
      onCreateFormChange('followupId', nextSchedule.followupId ? String(nextSchedule.followupId) : '');
    }
    if (nextSchedule.departmentId && String(nextSchedule.departmentId) !== createForm.departmentId) {
      onCreateFormChange('departmentId', String(nextSchedule.departmentId));
    }
    if (nextSchedule.date) {
      onCreateFormChange('activityDate', nextSchedule.date);
    }
    if (isNoteActionAllowed(createActionTypes, nextSchedule.suggestedActionType)) {
      onCreateFormChange('actionType', nextSchedule.suggestedActionType);
    }
  };

  return (
    <section className="notes-page">
      {data.source !== 'django' ? (
        <DashboardApiAlert message={data.error} title="영업노트 정보를 불러오지 못했습니다" />
      ) : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Notes</span>
          <h2>{data.scope.label || '영업노트'}</h2>
          <p>활동 기록, 검토 상태, 다음 액션을 같은 목록에서 확인합니다.</p>
        </div>
        <button
          className={canCreateNotes ? 'route-primary-action' : 'route-secondary-action'}
          onClick={() => onCreateOpenChange(!createOpen)}
          type="button"
        >
          {canCreateNotes ? '노트 작성' : '작성 권한 없음'}
          <Plus size={16} />
        </button>
      </div>

      <section className="dashboard-metric-grid" aria-label="영업노트 핵심 지표">
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

      {createOpen ? (
        <section className="dashboard-panel notes-create-panel" ref={createPanelRef}>
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Quick note</span>
              <h2>영업노트 빠른 작성</h2>
            </div>
            {creating ? <Loader2 className="spin-icon" size={18} /> : <MessageSquareText size={18} />}
          </div>
          {createMessage ? <div className="notes-action-feedback success">{createMessage}</div> : null}
          {createError ? <div className="notes-action-feedback error">{createError}</div> : null}
          {!canCreateNotes ? (
            <DashboardEmpty label={createConfig.message || '작성 권한이 없습니다'} />
          ) : createDepartments.length === 0 && createCustomers.length === 0 ? (
            <DashboardEmpty label="작성 가능한 부서/연구실이 없습니다" />
          ) : createActionTypes.length === 0 ? (
            <DashboardEmpty label="작성 가능한 활동 유형이 없습니다" />
          ) : (
            <form className="notes-create-form" onSubmit={onCreateSubmit}>
              <div className="notes-create-grid">
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
                  <span>연결 일정/납품</span>
                  <select
                    onChange={(event) => handleCreateScheduleChange(event.target.value)}
                    value={createForm.scheduleId}
                  >
                    <option value="">연결 없음</option>
                    {availableCreateSchedules.map((schedule) => (
                      <option key={schedule.id} value={schedule.id}>
                        {schedule.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>활동 유형</span>
                  <select
                    onChange={(event) => onCreateFormChange('actionType', event.target.value)}
                    required
                    value={createForm.actionType}
                  >
                    {createActionTypes.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>활동일</span>
                  <input
                    onChange={(event) => onCreateFormChange('activityDate', event.target.value)}
                    type="date"
                    value={createForm.activityDate}
                  />
                </label>
                <label>
                  <span>다음 예정일</span>
                  <input
                    onChange={(event) => onCreateFormChange('nextActionDate', event.target.value)}
                    type="date"
                    value={createForm.nextActionDate}
                  />
                </label>
              </div>
              {selectedCreateSchedule ? (
                <div className="note-linked-schedule-card">
                  <div>
                    <strong>{selectedCreateSchedule.activityLabel}</strong>
                    <span>
                      {[
                        selectedCreateSchedule.date ? formatDateLabel(selectedCreateSchedule.date) : '',
                        selectedCreateSchedule.time,
                        selectedCreateSchedule.statusLabel,
                      ].filter(Boolean).join(' · ')}
                    </span>
                    {selectedCreateSchedule.deliveryItems ? <p>{selectedCreateSchedule.deliveryItems}</p> : null}
                  </div>
                  <div>
                    {selectedCreateSchedule.deliveryAmount > 0 ? <strong>{formatWon(selectedCreateSchedule.deliveryAmount)}</strong> : null}
                    <a className="customer-row-action" href={selectedCreateSchedule.href}>일정 상세</a>
                  </div>
                </div>
              ) : null}
              <label>
                <span>활동 내용</span>
                <textarea
                  onChange={(event) => onCreateFormChange('content', event.target.value)}
                  placeholder="방문/통화/견적 진행 내용"
                  required
                  rows={4}
                  value={createForm.content}
                />
              </label>
              <label>
                <span>다음 액션</span>
                <textarea
                  onChange={(event) => onCreateFormChange('nextAction', event.target.value)}
                  placeholder="후속 연락, 견적 발송, 샘플 준비 등"
                  rows={2}
                  value={createForm.nextAction}
                />
              </label>
              <div className="notes-create-actions">
                <a className="route-secondary-action" href="/notes/?create=1">
                  상세 작성
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

      <div className="notes-filter-bar">
        <label className="customers-search">
          <Search size={17} />
          <input
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="이름, 고객, 회사, 노트 내용, 다음 액션 검색"
            value={query}
          />
        </label>
        <label className="notes-date-filter">
          <span>시작</span>
          <input
            aria-label="영업노트 시작일"
            onChange={(event) => onDateFromChange(event.target.value)}
            type="date"
            value={dateFrom}
          />
        </label>
        <label className="notes-date-filter">
          <span>종료</span>
          <input
            aria-label="영업노트 종료일"
            onChange={(event) => onDateToChange(event.target.value)}
            type="date"
            value={dateTo}
          />
        </label>
        <select onChange={(event) => onOwnerChange(event.target.value)} value={owner}>
          <option value="">담당자 전체</option>
          {data.options.owners.map((option) => (
            <option key={option.id} value={option.id}>{option.name}</option>
          ))}
        </select>
        <select onChange={(event) => onActionTypeChange(event.target.value)} value={actionType}>
          <option value="">활동 유형 전체</option>
          {data.options.actionTypes.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onReviewChange(event.target.value)} value={review}>
          <option value="">검토 상태 전체</option>
          {data.options.reviewStates.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select onChange={(event) => onNextActionChange(event.target.value)} value={nextAction}>
          <option value="">다음 액션 전체</option>
          {data.options.nextActionStates.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      </div>

      <div className="notes-layout">
        <section className="dashboard-panel notes-main-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Note list</span>
              <h2>영업노트 목록</h2>
            </div>
            {loading ? <Loader2 className="spin-icon" size={18} /> : <MessageSquareText size={18} />}
          </div>
          {reviewMessage ? <div className="notes-action-feedback success">{reviewMessage}</div> : null}
          {reviewError ? <div className="notes-action-feedback error">{reviewError}</div> : null}
          <NotesTable
            canReview={data.scope.canReview}
            notes={data.notes}
            onToggleReview={onToggleReview}
            reviewingNoteId={reviewingNoteId}
          />
        </section>

        <aside className="dashboard-panel notes-side-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Activity type</span>
              <h2>유형별 현황</h2>
            </div>
            <Filter size={18} />
          </div>
          <NotesActionCounts data={data} />
          <div className="customers-side-actions">
            <a href={data.links.notes}>전체 노트</a>
            <a href={data.links.unreviewed}>미검토 노트</a>
          </div>
        </aside>
      </div>
    </section>
  );
}