import {
  AlertTriangle,
  Clock,
  Database,
  Download,
  FileArchive,
  FileSpreadsheet,
  FileText,
  Link2,
  Loader2,
  Lock,
  MoveUpRight,
  RefreshCw,
  Server,
} from 'lucide-react';
import { useMemo, useState } from 'react';
import type { DownloadRegistryItem, DownloadsData } from '../../api/downloads';
import { DashboardApiAlert, DashboardEmpty, DashboardLoading } from '../../components/shared/FeedbackStates';
import { formatDateTimeLabel, formatNumber } from '../../components/shared/formatters';

function fileIcon(fileType: string) {
  if (fileType.includes('xlsx') || fileType.includes('csv')) return FileSpreadsheet;
  if (fileType.includes('json')) return Database;
  if (fileType === 'original') return FileArchive;
  return FileText;
}

function downloadActionLabel(item: DownloadRegistryItem) {
  if (item.operation === 'export') {
    return 'Excel/파일 생성';
  }
  if (item.streaming) {
    return '파일 다운로드';
  }
  return '다운로드';
}

function DownloadRegistryCard({ item }: { item: DownloadRegistryItem }) {
  const Icon = fileIcon(item.fileType);
  return (
    <article className="download-registry-card">
      <div className="download-registry-title">
        <div className="download-registry-icon">
          <Icon size={19} />
        </div>
        <div>
          <strong>{item.label}</strong>
          <span>{item.description}</span>
        </div>
      </div>
      <dl className="download-registry-meta">
        <div>
          <dt>범위</dt>
          <dd>{item.scopeLabel}</dd>
        </div>
        <div>
          <dt>파일명</dt>
          <dd>{item.filenamePattern}</dd>
        </div>
        <div>
          <dt>URL</dt>
          <dd>{item.href || item.hrefTemplate}</dd>
        </div>
        <div>
          <dt>권한</dt>
          <dd>{item.permissionLabel}</dd>
        </div>
      </dl>
      <div className="download-registry-flags">
        <span><Lock size={13} />{item.authLabel}</span>
        <span><Server size={13} />{item.urlName}</span>
        {item.largeDownload ? <span><Clock size={13} />{formatNumber(item.timeoutSeconds)}초 검수</span> : null}
        {item.streaming ? <span><Download size={13} />스트리밍</span> : null}
      </div>
      <div className="download-registry-actions">
        {item.href ? (
          <a className="route-primary-action" href={item.href}>
            <Download size={15} />
            {downloadActionLabel(item)}
          </a>
        ) : (
          <button className="route-secondary-action" disabled type="button">
            <Link2 size={15} />
            대상 선택 필요
          </button>
        )}
        <a className="route-secondary-action" href={item.reactEntry}>
          <MoveUpRight size={15} />
          관련 화면
        </a>
      </div>
    </article>
  );
}

export function DownloadsPage({
  data,
  loading,
  onRefresh,
}: {
  data: DownloadsData | null;
  loading: boolean;
  onRefresh: () => void;
}) {
  const [activeGroup, setActiveGroup] = useState('all');
  const groups = data?.groups ?? [];
  const downloads = data?.downloads ?? [];
  const visibleDownloads = useMemo(() => (
    activeGroup === 'all' ? downloads : downloads.filter((item) => item.group === activeGroup)
  ), [activeGroup, downloads]);
  const generatedLabel = data?.generatedAt ? formatDateTimeLabel(data.generatedAt) : '';
  const largeDownloadCount = downloads.filter((item) => item.largeDownload).length;
  const streamingCount = downloads.filter((item) => item.streaming).length;

  if (loading && !data) {
    return <DashboardLoading label="파일/다운로드 목록을 불러오는 중입니다" />;
  }

  if (!data) {
    return null;
  }

  return (
    <section className="downloads-page">
      {data.source !== 'django' ? (
        <DashboardApiAlert
          actionHref="/reporting/login/"
          message={data.error === 'login_required' ? '로그인이 필요합니다.' : data.error || '다운로드 API에 연결되지 않았습니다.'}
          title="파일/다운로드 API에 연결되지 않았습니다"
        />
      ) : null}

      <div className="dashboard-summary-band downloads-summary-band">
        <div>
          <span className="eyebrow">Files & exports</span>
          <h2>파일/엑셀 다운로드</h2>
          <p>{formatNumber(downloads.length)}개 URL · 대용량 {formatNumber(largeDownloadCount)}개 · 스트리밍 {formatNumber(streamingCount)}개{generatedLabel ? ` · ${generatedLabel}` : ''}</p>
        </div>
        <div className="reports-actions">
          <a className="route-secondary-action" href="/reports/"><FileSpreadsheet size={15} />리포트</a>
          <a className="route-secondary-action" href="/documents/"><FileText size={15} />서류</a>
          <button className="icon-button" onClick={onRefresh} type="button" aria-label="다운로드 목록 새로고침">
            {loading ? <Loader2 className="spin-icon" size={17} /> : <RefreshCw size={17} />}
          </button>
        </div>
      </div>

      <section className="downloads-policy-panel">
        <div>
          <Lock size={18} />
          <strong>인증</strong>
          <span>{data.policy.authRequired ? '로그인 세션 기준' : '공개 없음'}</span>
        </div>
        <div>
          <Server size={18} />
          <strong>처리</strong>
          <span>{data.policy.handler}</span>
        </div>
        <div>
          <Clock size={18} />
          <strong>대용량</strong>
          <span>{formatNumber(data.policy.largeDownloadTimeoutSeconds)}초 기준</span>
        </div>
      </section>

      {data.policy.largeDownloadNote ? (
        <div className="dashboard-api-alert compact downloads-note">
          <AlertTriangle size={16} />
          <span>{data.policy.largeDownloadNote}</span>
        </div>
      ) : null}

      <div className="segmented-control downloads-group-tabs" role="tablist" aria-label="다운로드 그룹">
        <button className={activeGroup === 'all' ? 'active' : ''} onClick={() => setActiveGroup('all')} type="button">
          전체
        </button>
        {groups.map((group) => (
          <button className={activeGroup === group.id ? 'active' : ''} key={group.id} onClick={() => setActiveGroup(group.id)} type="button">
            {group.label}
            <span>{formatNumber(group.count)}</span>
          </button>
        ))}
      </div>

      {visibleDownloads.length ? (
        <div className="download-registry-grid">
          {visibleDownloads.map((item) => (
            <DownloadRegistryCard item={item} key={item.id} />
          ))}
        </div>
      ) : (
        <DashboardEmpty label="표시할 다운로드 URL이 없습니다" />
      )}
    </section>
  );
}
