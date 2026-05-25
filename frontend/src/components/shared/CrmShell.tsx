import {
  Activity,
  Archive,
  ArrowRightLeft,
  Bell,
  Building2,
  CalendarDays,
  CheckCircle2,
  CircleDollarSign,
  Columns3,
  Download,
  FileSpreadsheet,
  FileText,
  ImagePlus,
  LayoutDashboard,
  ListChecks,
  LogOut,
  Mail,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  Users,
  Wrench,
  type LucideIcon,
} from 'lucide-react';
import { type ReactNode, useEffect, useState } from 'react';
import { loadNavigationData, type NavigationData, type NavigationItem } from '../../api/dashboard';
import { getCookie } from '../../api/shared';

export type MainView =
  | 'dashboard'
  | 'analytics'
  | 'dataCleanup'
  | 'downloads'
  | 'customers'
  | 'companies'
  | 'assets'
  | 'services'
  | 'pipeline'
  | 'notes'
  | 'schedules'
  | 'tasks'
  | 'employees'
  | 'mail'
  | 'businessCards'
  | 'weeklyReports'
  | 'documents'
  | 'products'
  | 'prepayments'
  | 'profile'
  | 'ai';

type ShellNavigationItem = NavigationItem & { icon?: LucideIcon };

const fallbackNavItems: ShellNavigationItem[] = [
  { id: 'dashboard', label: '대시보드', icon: LayoutDashboard, href: '/dashboard/' },
  { id: 'analytics', label: '현황', icon: Activity, href: '/reports/' },
  { id: 'dataCleanup', label: '데이터정리', icon: ArrowRightLeft, href: '/data-cleanup/' },
  { id: 'downloads', label: '파일/다운로드', icon: Download, href: '/downloads/' },
  { id: 'customers', label: '고객', icon: Users, href: '/customers/' },
  { id: 'companies', label: '업체/부서', icon: Building2, href: '/companies/' },
  { id: 'assets', label: '장비', icon: Wrench, href: '/assets/' },
  { id: 'services', label: '서비스', icon: Wrench, href: '/services/' },
  { id: 'pipeline', label: '파이프라인', icon: Columns3, href: '/pipeline/' },
  { id: 'notes', label: '영업노트', icon: FileText, href: '/notes/' },
  { id: 'schedules', label: '일정', icon: CalendarDays, href: '/schedules/calendar/' },
  { id: 'tasks', label: '업무', icon: CheckCircle2, href: '/tasks/' },
  { id: 'mail', label: '메일', icon: Mail, href: '/mailbox/' },
  { id: 'businessCards', label: '명함', icon: ImagePlus, href: '/mailbox/business-cards/' },
  { id: 'weeklyReports', label: '주간보고', icon: ListChecks, href: '/weekly-reports/' },
  { id: 'documents', label: '서류', icon: FileSpreadsheet, href: '/documents/' },
  { id: 'products', label: '제품', icon: Archive, href: '/products/' },
  { id: 'prepayments', label: '선결제', icon: CircleDollarSign, href: '/prepayments/' },
  { id: 'profile', label: '프로필', icon: Users, href: '/profile/' },
  { id: 'ai', label: 'AI', icon: Sparkles, href: '/ai-workspace/' },
];

const navIconMap: Record<string, LucideIcon> = {
  dashboard: LayoutDashboard,
  analytics: Activity,
  dataCleanup: ArrowRightLeft,
  downloads: Download,
  customers: Users,
  companies: Building2,
  assets: Wrench,
  services: Wrench,
  pipeline: Columns3,
  notes: FileText,
  schedules: CalendarDays,
  tasks: CheckCircle2,
  tasksManager: Users,
  employees: ShieldCheck,
  userAdmin: ShieldCheck,
  mail: Mail,
  businessCards: ImagePlus,
  weeklyReports: ListChecks,
  documents: FileSpreadsheet,
  products: Archive,
  prepayments: CircleDollarSign,
  profile: Users,
  ai: Sparkles,
};

const routeShellMeta: Record<MainView, { eyebrow: string; title: string }> = {
  dashboard: { eyebrow: 'Sales CRM / Dashboard', title: '대시보드' },
  analytics: { eyebrow: 'Sales CRM / Reports', title: '분석' },
  dataCleanup: { eyebrow: 'Sales CRM / Data Cleanup', title: '데이터정리' },
  downloads: { eyebrow: 'Sales CRM / Downloads', title: '파일/다운로드' },
  customers: { eyebrow: 'Sales CRM / Customers', title: '고객' },
  companies: { eyebrow: 'Sales CRM / Companies', title: '업체/부서' },
  assets: { eyebrow: 'Sales CRM / Assets', title: '장비' },
  services: { eyebrow: 'Sales CRM / Services', title: '서비스' },
  pipeline: { eyebrow: 'Sales CRM / Pipeline', title: '파이프라인' },
  notes: { eyebrow: 'Sales CRM / Notes', title: '영업노트' },
  schedules: { eyebrow: 'Sales CRM / Schedule', title: '일정' },
  tasks: { eyebrow: 'Sales CRM / Tasks', title: '업무' },
  employees: { eyebrow: 'Sales CRM / Employees', title: '직원관리' },
  mail: { eyebrow: 'Sales CRM / Mail', title: '메일' },
  businessCards: { eyebrow: 'Sales CRM / Signature', title: '명함' },
  weeklyReports: { eyebrow: 'Sales CRM / Weekly', title: '주간보고' },
  documents: { eyebrow: 'Sales CRM / Documents', title: '서류' },
  products: { eyebrow: 'Sales CRM / Products', title: '제품' },
  prepayments: { eyebrow: 'Sales CRM / Prepayment', title: '선결제' },
  profile: { eyebrow: 'Sales CRM / Profile', title: '프로필' },
  ai: { eyebrow: 'Sales CRM / AI', title: 'AI 업무도구' },
};

async function handleLogout() {
  const csrfToken = getCookie('csrftoken');
  try {
    await fetch('/reporting/logout/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
      },
    });
  } catch (error) {
    console.error('Logout request failed', error);
  } finally {
    window.location.href = '/reporting/login/';
  }
}

function isActiveNavItem(item: NavigationItem, activeView: MainView, pathname: string, hasTaskManagerItem: boolean) {
  if (activeView !== 'tasks') {
    return item.id === activeView;
  }
  if (pathname.startsWith('/tasks/manager/')) {
    return item.id === (hasTaskManagerItem ? 'tasksManager' : 'tasks');
  }
  return item.id === 'tasks';
}

export function AppShell({ activeView, children }: { activeView: MainView; children: ReactNode }) {
  const [navigation, setNavigation] = useState<NavigationData | null>(null);

  useEffect(() => {
    let mounted = true;
    loadNavigationData().then((data) => {
      if (mounted) setNavigation(data);
    });
    return () => {
      mounted = false;
    };
  }, []);

  const items = navigation?.items?.length
    ? navigation.items.map((item) => ({ ...item, icon: navIconMap[item.id] || LayoutDashboard }))
    : fallbackNavItems;
  const pathname = window.location.pathname;
  const hasTaskManagerItem = items.some((item) => item.id === 'tasksManager');

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">SN</div>
          <div>
            <strong>영업 보고 시스템</strong>
            <span>CRM Workspace</span>
          </div>
        </div>
        <nav className="nav-list" aria-label="CRM navigation">
          {items.map((item) => {
            const Icon = item.icon || navIconMap[item.id] || LayoutDashboard;
            return (
              <a className={`nav-item ${isActiveNavItem(item, activeView, pathname, hasTaskManagerItem) ? 'active' : ''}`} href={item.href} key={`${item.id}-${item.href}`}>
                <Icon size={18} />
                <span>{item.label}</span>
              </a>
            );
          })}
        </nav>
        <div className="sidebar-note">
          <span>{navigation?.currentUser.roleLabel || '운영 기준'}</span>
          <strong>{navigation?.currentUser.name || '프론트가 메인 화면'}</strong>
          <p>{navigation?.currentUser.company || '조회와 이동은 React CRM에서 시작합니다.'}</p>
        </div>
      </aside>
      <main className="workspace">{children}</main>
    </div>
  );
}

export function TopBar({
  activeView,
  searchQuery = '',
  onSearchChange,
}: {
  activeView: MainView;
  searchQuery?: string;
  onSearchChange?: (value: string) => void;
}) {
  const meta = routeShellMeta[activeView];
  const showSearch = activeView === 'pipeline' && Boolean(onSearchChange);
  return (
    <header className="topbar">
      <div>
        <div className="eyebrow">{meta.eyebrow}</div>
        <h1>{meta.title}</h1>
      </div>
      <div className="topbar-actions">
        {showSearch ? (
          <label className="search-box">
            <Search size={17} />
            <input
              onChange={(event) => onSearchChange?.(event.target.value)}
              placeholder="고객, 담당자, 품목, 다음 액션 검색"
              value={searchQuery}
            />
          </label>
        ) : null}
        <a className="icon-button" aria-label="영업노트" href="/notes/">
          <Bell size={18} />
        </a>
        <a className="primary-button" href="/notes/?create=1">
          <Plus size={17} />
          새 영업노트
        </a>
        <button className="logout-button" onClick={handleLogout} type="button">
          <LogOut size={17} />
          로그아웃
        </button>
      </div>
    </header>
  );
}
