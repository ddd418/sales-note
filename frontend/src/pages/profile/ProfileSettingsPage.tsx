import { type FormEvent } from 'react';
import {
    Building2,
    Check,
    Loader2,
    ShieldCheck,
    Target,
    Users
} from 'lucide-react';
import {
    ProfileData
} from '../../api';
import { DashboardApiAlert } from '../../components/shared/FeedbackStates';
import {
    formatDateLabel,
    formatDateTimeLabel
} from '../../components/shared/formatters';
import { ProfileFormState, ProfilePasswordFormState } from '../shared/appShared';


export function ProfileSettingsPage({
  data,
  error,
  form,
  loading,
  message,
  passwordForm,
  passwordSaving,
  saving,
  onFormChange,
  onPasswordFormChange,
  onPasswordSubmit,
  onSubmit,
}: {
  data: ProfileData | null;
  error: string;
  form: ProfileFormState;
  loading: boolean;
  message: string;
  passwordForm: ProfilePasswordFormState;
  passwordSaving: boolean;
  saving: boolean;
  onFormChange: (field: keyof ProfileFormState, value: string) => void;
  onPasswordFormChange: (field: keyof ProfilePasswordFormState, value: string) => void;
  onPasswordSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  if (loading && !data) {
    return (
      <section className="dashboard-loading">
        <Loader2 className="spin-icon" size={24} />
        <span>프로필 데이터를 불러오는 중입니다</span>
      </section>
    );
  }
  if (!data) return null;
  const permissionItems = [
    { label: 'AI 사용', enabled: data.profile.canUseAi },
    { label: '엑셀 다운로드', enabled: data.profile.canDownloadExcel },
  ];

  return (
    <section className="profile-page">
      {data.source !== 'django' ? (
        <DashboardApiAlert message={data.error} title="프로필 정보를 불러오지 못했습니다" />
      ) : null}
      {message ? <div className="form-success-message">{message}</div> : null}
      {error ? <div className="form-error-message">{error}</div> : null}

      <div className="dashboard-summary-band">
        <div>
          <span className="eyebrow">Profile</span>
          <h2>{data.user.fullName || data.user.username || '프로필'}</h2>
          <p>{[data.profile.roleLabel, data.profile.company].filter(Boolean).join(' · ') || '계정 정보'}</p>
        </div>
        <a className="route-secondary-action" href={data.links.dashboard}>대시보드</a>
      </div>

      <div className="profile-overview-strip">
        <div>
          <Users size={18} />
          <span>계정</span>
          <strong>{data.user.username || '-'}</strong>
        </div>
        <div>
          <Building2 size={18} />
          <span>소속</span>
          <strong>{data.profile.company || '-'}</strong>
        </div>
        <div>
          <ShieldCheck size={18} />
          <span>권한</span>
          <strong>{permissionItems.filter((item) => item.enabled).length} / {permissionItems.length}</strong>
        </div>
      </div>

      <div className="profile-layout">
        <section className="dashboard-panel profile-info-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Account</span>
              <h2>기본 정보</h2>
            </div>
            <Users size={18} />
          </div>
          <form className="profile-form" onSubmit={onSubmit}>
            <label className="profile-form-wide">사용자명<input value={form.username} onChange={(event) => onFormChange('username', event.target.value)} required /></label>
            <label>성<input value={form.firstName} onChange={(event) => onFormChange('firstName', event.target.value)} /></label>
            <label>이름<input value={form.lastName} onChange={(event) => onFormChange('lastName', event.target.value)} /></label>
            <label className="profile-form-wide">이메일<input type="email" value={form.email} onChange={(event) => onFormChange('email', event.target.value)} /></label>
            <div className="profile-readonly-grid">
              <div><span>권한</span><strong>{data.profile.roleLabel || '-'}</strong></div>
              <div><span>소속</span><strong>{data.profile.company || '-'}</strong></div>
              <div><span>가입일</span><strong>{data.user.dateJoined ? formatDateLabel(data.user.dateJoined) : '-'}</strong></div>
              <div><span>최종 로그인</span><strong>{data.user.lastLogin ? formatDateTimeLabel(data.user.lastLogin) : '-'}</strong></div>
            </div>
            <div className="profile-permission-row">
              {permissionItems.map((item) => (
                <span className={item.enabled ? 'status-pill done' : 'status-pill neutral'} key={item.label}>
                  {item.label}
                </span>
              ))}
            </div>
            <button className="primary-button" disabled={saving} type="submit">
              {saving ? <Loader2 className="spin-icon" size={16} /> : <Check size={16} />}
              기본 정보 저장
            </button>
          </form>
        </section>

        <section className="dashboard-panel profile-password-panel">
          <div className="dashboard-panel-heading">
            <div>
              <span className="eyebrow">Password</span>
              <h2>비밀번호 변경</h2>
            </div>
            <Target size={18} />
          </div>
          <form className="profile-form profile-password-form" onSubmit={onPasswordSubmit}>
            <label>현재 비밀번호<input type="password" value={passwordForm.oldPassword} onChange={(event) => onPasswordFormChange('oldPassword', event.target.value)} required /></label>
            <label>새 비밀번호<input type="password" value={passwordForm.newPassword1} onChange={(event) => onPasswordFormChange('newPassword1', event.target.value)} required /></label>
            <label>새 비밀번호 확인<input type="password" value={passwordForm.newPassword2} onChange={(event) => onPasswordFormChange('newPassword2', event.target.value)} required /></label>
            <button className="primary-button" disabled={passwordSaving} type="submit">
              {passwordSaving ? <Loader2 className="spin-icon" size={16} /> : <Check size={16} />}
              비밀번호 변경
            </button>
          </form>
        </section>
      </div>
    </section>
  );
}