import { assertSuccessfulJsonPayload, fetchJson } from './shared';

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
    const { response, payload } = await fetchJson<Partial<DownloadsData>>(
      '/reporting/api/downloads/',
      {},
      'Downloads API unavailable',
    );
    assertSuccessfulJsonPayload(response, payload, 'Downloads API unavailable', { requireDjangoSource: true });
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
