import { redirectIfLoginRequired } from './shared';

export type DownloadRegistryItem = {
  id: string;
  group: string;
  groupLabel: string;
  label: string;
  description: string;
  urlName: string;
  method: 'GET' | string;
  operation: 'download' | 'export' | string;
  href: string;
  hrefTemplate: string;
  fileType: string;
  filenamePattern: string;
  scopeLabel: string;
  reactEntry: string;
  authLabel: string;
  permissionLabel: string;
  streaming: boolean;
  largeDownload: boolean;
  timeoutSeconds: number;
  queryParameters: string[];
};

export type DownloadRegistryGroup = {
  id: string;
  label: string;
  count: number;
};

export type DownloadsData = {
  success?: boolean;
  source: 'django' | 'unavailable';
  generatedAt?: string;
  error?: string;
  message?: string;
  links: {
    react: string;
    legacy: string;
    login: string;
  };
  policy: {
    authRequired: boolean;
    handler: string;
    largeDownloadTimeoutSeconds: number;
    largeDownloadNote: string;
  };
  groups: DownloadRegistryGroup[];
  downloads: DownloadRegistryItem[];
};

const emptyDownloadsData: DownloadsData = {
  success: false,
  source: 'unavailable',
  generatedAt: new Date().toISOString(),
  links: {
    react: '/downloads/',
    legacy: '/reporting/downloads/',
    login: '/reporting/login/',
  },
  policy: {
    authRequired: true,
    handler: 'Django API',
    largeDownloadTimeoutSeconds: 120,
    largeDownloadNote: '',
  },
  groups: [],
  downloads: [],
};

export async function loadDownloadsData(): Promise<DownloadsData> {
  try {
    const response = await fetch('/reporting/api/downloads/', {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });
    redirectIfLoginRequired(response);
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      throw new Error(`Downloads API unavailable: ${response.status}`);
    }
    const payload = (await response.json()) as Partial<DownloadsData>;
    redirectIfLoginRequired(response, payload);
    if (!response.ok || payload.success === false || payload.source !== 'django') {
      throw new Error(payload.error || payload.message || `Downloads API unavailable: ${response.status}`);
    }
    return {
      ...emptyDownloadsData,
      ...payload,
      links: {
        ...emptyDownloadsData.links,
        ...(payload.links ?? {}),
      },
      policy: {
        ...emptyDownloadsData.policy,
        ...(payload.policy ?? {}),
      },
      groups: payload.groups ?? [],
      downloads: payload.downloads ?? [],
    };
  } catch (error) {
    return {
      ...emptyDownloadsData,
      generatedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Downloads API unavailable',
    };
  }
}
