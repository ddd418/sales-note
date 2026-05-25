import { CalendarDays, Download, FileText, Loader2, Trash2, Upload } from 'lucide-react';
import type { ChangeEvent, RefObject } from 'react';
import { DashboardEmpty } from './FeedbackStates';
import { formatDateTimeLabel } from './formatters';

export type AttachmentManagerFile = {
  id: number | string;
  filename: string;
  size?: string;
  fileSize?: number;
  uploadedAt?: string | null;
  uploadedBy?: string | { name?: string; username?: string } | null;
  downloadHref: string;
  deleteHref?: string;
  canDelete?: boolean;
  sourceHref?: string;
  sourceLabel?: string;
  sourceDetail?: string;
  sourceOwner?: string;
  sourceDate?: string | null;
  fileType?: string;
  fileTypeLabel?: string;
};

function formatFileSize(size?: number) {
  if (!size && size !== 0) return '';
  if (size >= 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  if (size >= 1024) return `${Math.round(size / 1024)} KB`;
  return `${size} B`;
}

function uploadedByLabel(file: AttachmentManagerFile) {
  if (!file.uploadedBy) return '';
  if (typeof file.uploadedBy === 'string') return file.uploadedBy;
  return file.uploadedBy.name || file.uploadedBy.username || '';
}

function fileMeta(file: AttachmentManagerFile) {
  return [
    file.size || formatFileSize(file.fileSize),
    file.fileTypeLabel,
    uploadedByLabel(file),
    file.uploadedAt ? formatDateTimeLabel(file.uploadedAt) : '',
  ].filter(Boolean).join(' · ');
}

function sourceMeta(file: AttachmentManagerFile) {
  return [
    file.sourceLabel,
    file.sourceOwner,
    file.sourceDate ? formatDateTimeLabel(file.sourceDate) : '',
    file.sourceDetail,
  ].filter(Boolean).join(' · ');
}

export function AttachmentManager({
  canUpload = false,
  className = '',
  deletingId = null,
  emptyLabel = '첨부파일이 없습니다',
  files,
  inputRef,
  title = '첨부파일',
  uploadAriaLabel = '첨부파일 선택',
  uploadLabel = '업로드',
  uploading = false,
  onDelete,
  onFilesSelected,
  onUploadClick,
}: {
  canUpload?: boolean;
  className?: string;
  deletingId?: number | string | null;
  emptyLabel?: string;
  files: AttachmentManagerFile[];
  inputRef?: RefObject<HTMLInputElement>;
  title?: string;
  uploadAriaLabel?: string;
  uploadLabel?: string;
  uploading?: boolean;
  onDelete?: (file: AttachmentManagerFile) => void;
  onFilesSelected?: (event: ChangeEvent<HTMLInputElement>) => void;
  onUploadClick?: () => void;
}) {
  return (
    <section className={`attachment-manager ${className}`.trim()}>
      <div className="attachment-manager-heading">
        <h3 className="customer-detail-section-heading">{title}</h3>
        {canUpload ? (
          <>
            <input
              aria-label={uploadAriaLabel}
              className="attachment-manager-input"
              multiple
              onChange={onFilesSelected}
              ref={inputRef}
              type="file"
            />
            <button
              className="customer-row-action attachment-upload-button"
              disabled={uploading}
              onClick={onUploadClick}
              type="button"
            >
              {uploading ? <Loader2 className="spin-icon" size={14} /> : <Upload size={14} />}
              <span>{uploading ? '업로드 중' : uploadLabel}</span>
            </button>
          </>
        ) : null}
      </div>
      {files.length === 0 ? (
        <DashboardEmpty label={emptyLabel} />
      ) : (
        <div className="attachment-manager-list">
          {files.map((file) => {
            const canDelete = Boolean(file.canDelete && file.deleteHref && onDelete);
            const SourceIcon = file.fileType === 'schedule' ? CalendarDays : FileText;
            return (
              <article className="attachment-manager-row" key={`${file.fileType || 'file'}-${file.id}`}>
                <a className="attachment-manager-download" href={file.downloadHref}>
                  <SourceIcon size={17} />
                  <span>
                    <strong>{file.filename}</strong>
                    <small>{fileMeta(file)}</small>
                    {sourceMeta(file) ? <em>{sourceMeta(file)}</em> : null}
                  </span>
                  <Download size={15} />
                </a>
                <div className="attachment-manager-actions">
                  {file.sourceHref ? (
                    <a className="customer-row-action" href={file.sourceHref}>
                      원문
                    </a>
                  ) : null}
                  {canDelete ? (
                    <button
                      aria-label={`${file.filename} 삭제`}
                      className="customer-row-action schedule-file-delete-button"
                      disabled={deletingId === file.id}
                      onClick={() => onDelete?.(file)}
                      type="button"
                    >
                      {deletingId === file.id ? <Loader2 className="spin-icon" size={14} /> : <Trash2 size={14} />}
                      <span>삭제</span>
                    </button>
                  ) : null}
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
