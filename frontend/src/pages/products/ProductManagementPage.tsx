import { useEffect, useMemo, useRef, useState, type ChangeEvent, type FormEvent } from 'react';
import {
    AlertTriangle,
    Archive,
    CheckCircle2,
    ChevronLeft,
    ChevronRight,
    Download,
    Loader2,
    Plus,
    RefreshCw,
    Search,
    Trash2,
    Upload,
    X
} from 'lucide-react';
import {
    ProductBulkDeleteResult,
    ProductBulkUpsertResult,
    ProductDeleteReference,
    ProductManagementData,
    ProductManagementItem,
    ProductMutationPayload,
    ProductOption,
    bulkDeleteProducts,
    bulkUpsertProducts,
    importProductsExcel,
    loadProducts,
    replaceProductReference,
    saveProduct
} from '../../api';
import { DashboardMetricCard } from '../../components/shared/DashboardMetricCard';
import { DashboardApiAlert, DashboardEmpty } from '../../components/shared/FeedbackStates';
import {
    formatDateLabel,
    formatDateTimeLabel,
    formatNumber,
    formatWon
} from '../../components/shared/formatters';
import { type PipelineData } from '../../pipelineTypes';
import { ProductSortField, ProductSortOrder, WorkspaceRoutePage, routeMeta, shouldOpenCreatePanel, useGuidedPanelFocus } from '../shared/appShared';


type ProductFormState = {
  description: string;
  isActive: boolean;
  productCode: string;
  specification: string;
  standardPrice: string;
  unit: string;
};

const makeEmptyProductForm = (): ProductFormState => ({
  description: '',
  isActive: true,
  productCode: '',
  specification: '',
  standardPrice: '',
  unit: 'EA',
});

const makeProductForm = (product: ProductManagementItem | null): ProductFormState => ({
  description: product?.description || '',
  isActive: product ? product.isActive : true,
  productCode: product?.productCode || '',
  specification: product?.specification || '',
  standardPrice: product ? String(product.standardPrice) : '',
  unit: product?.unit || 'EA',
});

const normalizeProductPriceInput = (value: string) => value.replace(/[,\s원]/g, '').trim();

const productFormToPayload = (form: ProductFormState): ProductMutationPayload => ({
  description: form.description.trim(),
  isActive: form.isActive,
  productCode: form.productCode.trim(),
  specification: form.specification.trim(),
  standardPrice: normalizeProductPriceInput(form.standardPrice) || '0',
  unit: form.unit.trim() || 'EA',
});

const splitProductPasteLine = (line: string) => {
  const trimmed = line.trim();
  if (!trimmed) return [];
  if (trimmed.includes('\t')) {
    return trimmed.split('\t').map((cell) => cell.trim());
  }
  return trimmed.split(/\s{2,}/).map((cell) => cell.trim());
};

const isProductPasteHeader = (cells: string[]) => {
  const normalizedCells = cells.map((cell) => cell.trim().toLowerCase());
  const headerText = normalizedCells.join(' ');
  return (
    normalizedCells.some((cell) => ['품번', '품목코드', '제품코드', '코드', 'code'].includes(cell)) ||
    headerText.includes('product code') ||
    headerText.includes('기준단가') ||
    headerText.includes('출고단가')
  );
};

const parseProductPasteRows = (text: string): ProductMutationPayload[] => {
  const rows: ProductMutationPayload[] = [];
  const seenCodes = new Set<string>();
  text.split(/\r?\n/).forEach((line) => {
    const cells = splitProductPasteLine(line);
    if (cells.length < 2 || isProductPasteHeader(cells)) {
      return;
    }

    const productCode = cells[0] || '';
    let description = '';
    let specification = '';
    let unit = 'EA';
    let price = '';

    if (cells.length >= 5) {
      description = cells[1] || '';
      specification = cells[2] || '';
      unit = cells[3] || 'EA';
      price = cells.slice(4).join('');
    } else if (cells.length >= 4) {
      specification = cells[1] || '';
      unit = cells[2] || 'EA';
      price = cells.slice(3).join('');
    } else {
      specification = cells[1] || '';
      price = cells[2] || '';
    }

    const normalizedCode = productCode.trim();
    if (!normalizedCode || seenCodes.has(normalizedCode)) {
      return;
    }
    seenCodes.add(normalizedCode);
    rows.push({
      description: description.trim(),
      isActive: true,
      productCode: normalizedCode,
      specification: specification.trim(),
      standardPrice: normalizeProductPriceInput(price) || '0',
      unit: unit.trim() || 'EA',
    });
  });
  return rows;
};

const parseProductDeleteCodes = (text: string): string[] => {
  const codes: string[] = [];
  text.split(/\r?\n/).forEach((line) => {
    const [firstCell] = line.split(/\t|,|\s{2,}/).map((cell) => cell.trim());
    if (!firstCell || isProductPasteHeader([firstCell]) || codes.includes(firstCell)) {
      return;
    }
    codes.push(firstCell);
  });
  return codes;
};

const mergeProductOptions = (current: ProductOption[], incoming: ProductOption[]) => {
  const optionsById = new Map<number, ProductOption>();
  current.forEach((option) => optionsById.set(option.id, option));
  incoming.forEach((option) => optionsById.set(option.id, option));
  return Array.from(optionsById.values()).sort((a, b) => a.productCode.localeCompare(b.productCode));
};

export function ProductManagementPage({
  data,
  loading,
  onOrderChange,
  onPageChange,
  onQueryChange,
  onReload,
  onSortChange,
  onStatusChange,
  order,
  page,
  query,
  routeData,
  sort,
  status,
}: {
  data: ProductManagementData | null;
  loading: boolean;
  onOrderChange: (value: ProductSortOrder) => void;
  onPageChange: (value: number) => void;
  onQueryChange: (value: string) => void;
  onReload: () => Promise<ProductManagementData | null>;
  onSortChange: (value: ProductSortField) => void;
  onStatusChange: (value: string) => void;
  order: ProductSortOrder;
  page: number;
  query: string;
  routeData: PipelineData;
  sort: ProductSortField;
  status: string;
}) {
  const [formOpen, setFormOpen] = useState(() => shouldOpenCreatePanel());
  const [editingProduct, setEditingProduct] = useState<ProductManagementItem | null>(null);
  const [form, setForm] = useState<ProductFormState>(() => makeEmptyProductForm());
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');
  const [formMessage, setFormMessage] = useState('');
  const [bulkText, setBulkText] = useState('');
  const [bulkSaving, setBulkSaving] = useState(false);
  const [bulkResult, setBulkResult] = useState<ProductBulkUpsertResult | null>(null);
  const [bulkError, setBulkError] = useState('');
  const [importSaving, setImportSaving] = useState(false);
  const [importResult, setImportResult] = useState<ProductBulkUpsertResult | null>(null);
  const [importError, setImportError] = useState('');
  const [deleteText, setDeleteText] = useState('');
  const [deleteSaving, setDeleteSaving] = useState(false);
  const [deleteResult, setDeleteResult] = useState<ProductBulkDeleteResult | null>(null);
  const [deleteError, setDeleteError] = useState('');
  const [deleteReferenceReplacements, setDeleteReferenceReplacements] = useState<Record<string, string>>({});
  const [deleteReplacementOptions, setDeleteReplacementOptions] = useState<ProductOption[]>([]);
  const [deleteReplacementLoading, setDeleteReplacementLoading] = useState(false);
  const [deleteReplacementError, setDeleteReplacementError] = useState('');
  const [deleteReplacementSearch, setDeleteReplacementSearch] = useState('');
  const [deleteReplacementMessage, setDeleteReplacementMessage] = useState('');
  const [replacingReferenceKey, setReplacingReferenceKey] = useState('');
  const [handledProductAction, setHandledProductAction] = useState('');
  const productImportInputRef = useRef<HTMLInputElement | null>(null);
  const productFormPanelRef = useRef<HTMLFormElement | null>(null);

  const products = data?.products ?? [];
  const pagination = data?.pagination;
  const canManage = Boolean(data?.scope.canManage);
  const productRouteActions = data && !canManage
    ? routeMeta.products.actions.filter((action) => action.href !== '/products/?create=1')
    : routeMeta.products.actions;
  const pastedProducts = useMemo(() => parseProductPasteRows(bulkText), [bulkText]);
  const deleteCodes = useMemo(() => parseProductDeleteCodes(deleteText), [deleteText]);
  const replaceableDeleteRows = useMemo(() => (
    (deleteResult?.results ?? []).filter((row) => row.status === 'blocked' && row.canReplace)
  ), [deleteResult]);

  useGuidedPanelFocus(formOpen, productFormPanelRef, `product-${editingProduct?.id || 'new'}`);

  useEffect(() => {
    if (!data || canManage || !formOpen) {
      return;
    }
    setFormOpen(false);
    setEditingProduct(null);
    setFormError('');
    setFormMessage('');
  }, [canManage, data, formOpen]);

  useEffect(() => {
    if (!data || !canManage || !products.length) {
      return;
    }
    const params = new URLSearchParams(window.location.search);
    const productId = Number(params.get('product') || 0);
    const action = params.get('edit') === '1' ? 'edit' : params.get('delete') === '1' ? 'delete' : '';
    const signature = productId && action ? `${productId}:${action}` : '';
    if (!signature || handledProductAction === signature) {
      return;
    }
    const product = products.find((item) => item.id === productId);
    if (!product) {
      return;
    }
    setHandledProductAction(signature);
    if (action === 'edit') {
      openEdit(product);
    } else if (action === 'delete') {
      setDeleteText(product.productCode);
      setDeleteResult(null);
      setDeleteError('');
    }
    ['product', 'edit', 'delete'].forEach((key) => params.delete(key));
    const queryString = params.toString();
    window.history.replaceState(null, '', `/products/${queryString ? `?${queryString}` : ''}`);
  }, [canManage, data, handledProductAction, products]);

  useEffect(() => {
    if (!replaceableDeleteRows.length || deleteReplacementOptions.length) {
      return;
    }

    let active = true;
    setDeleteReplacementLoading(true);
    setDeleteReplacementError('');
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 15000);
    loadProducts('', { limit: 80, signal: controller.signal })
      .then((options) => {
        if (active) {
          setDeleteReplacementOptions((previous) => mergeProductOptions(previous, options));
          if (!options.length) {
            setDeleteReplacementError('선택 가능한 활성 제품이 없습니다. 제품을 먼저 등록하거나 활성화하세요.');
          } else {
            setDeleteReplacementMessage(`최근 품번 기준 ${formatNumber(options.length)}건을 불러왔습니다. 필요한 제품이 없으면 검색하세요.`);
          }
        }
      })
      .catch((error) => {
        if (active) {
          setDeleteReplacementError(error instanceof Error && error.name === 'AbortError'
            ? '대체 제품 목록 조회가 지연되었습니다. 품번/제품명으로 검색하세요.'
            : error instanceof Error ? error.message : '대체 제품 목록을 불러오지 못했습니다.');
        }
      })
      .finally(() => {
        window.clearTimeout(timeout);
        if (active) {
          setDeleteReplacementLoading(false);
        }
      });

    return () => {
      active = false;
      controller.abort();
      window.clearTimeout(timeout);
    };
  }, [deleteReplacementOptions.length, replaceableDeleteRows.length]);

  const handleDeleteReplacementSearch = async () => {
    const search = deleteReplacementSearch.trim();
    if (deleteReplacementLoading) return;
    if (search.length < 2) {
      setDeleteReplacementError('품번, 제품설명, 규격 중 2글자 이상 입력하세요.');
      setDeleteReplacementMessage('');
      return;
    }

    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 15000);
    setDeleteReplacementLoading(true);
    setDeleteReplacementError('');
    setDeleteReplacementMessage('');
    try {
      const options = await loadProducts(search, { limit: 80, signal: controller.signal });
      setDeleteReplacementOptions((previous) => mergeProductOptions(previous, options));
      setDeleteReplacementMessage(options.length
        ? `"${search}" 검색 결과 ${formatNumber(options.length)}건을 선택지에 추가했습니다.`
        : `"${search}" 검색 결과가 없습니다.`);
    } catch (error) {
      setDeleteReplacementError(error instanceof Error && error.name === 'AbortError'
        ? '제품 검색이 지연되었습니다. 더 구체적인 품번으로 다시 검색하세요.'
        : error instanceof Error ? error.message : '제품 검색에 실패했습니다.');
    } finally {
      window.clearTimeout(timeout);
      setDeleteReplacementLoading(false);
    }
  };

  const openCreate = () => {
    setEditingProduct(null);
    setForm(makeEmptyProductForm());
    setFormOpen(true);
    setFormError('');
    setFormMessage('');
  };

  const openEdit = (product: ProductManagementItem) => {
    setEditingProduct(product);
    setForm(makeProductForm(product));
    setFormOpen(true);
    setFormError('');
    setFormMessage('');
  };

  const closeForm = () => {
    setFormOpen(false);
    setEditingProduct(null);
    setFormError('');
  };

  const handleFormChange = (field: keyof ProductFormState, value: string | boolean) => {
    setForm((previous) => ({
      ...previous,
      [field]: value,
    }));
    setFormError('');
  };

  const handleSort = (field: ProductSortField) => {
    if (sort === field) {
      onOrderChange(order === 'asc' ? 'desc' : 'asc');
    } else {
      onSortChange(field);
      onOrderChange(field === 'updatedAt' || field === 'price' ? 'desc' : 'asc');
    }
    onPageChange(1);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (saving) return;
    const payload = productFormToPayload(form);
    const price = Number(payload.standardPrice);
    if (!payload.productCode) {
      setFormError('품번을 입력하세요.');
      return;
    }
    if (!Number.isFinite(price) || price < 0) {
      setFormError('기준단가는 0 이상 숫자로 입력하세요.');
      return;
    }

    setSaving(true);
    setFormError('');
    setFormMessage('');
    try {
      const result = await saveProduct(payload, editingProduct?.id);
      setFormMessage(result.message || '제품을 저장했습니다.');
      setForm(makeEmptyProductForm());
      setEditingProduct(null);
      setFormOpen(false);
      await onReload();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : '제품 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleBulkUpsert = async () => {
    if (bulkSaving) return;
    if (!pastedProducts.length) {
      setBulkError('붙여넣은 제품 데이터가 없습니다.');
      return;
    }
    setBulkSaving(true);
    setBulkError('');
    setBulkResult(null);
    try {
      const result = await bulkUpsertProducts(pastedProducts);
      setBulkResult(result);
      if (result.errorCount > 0) {
        setBulkError(result.message);
      }
      await onReload();
    } catch (error) {
      setBulkError(error instanceof Error ? error.message : '일괄 반영에 실패했습니다.');
    } finally {
      setBulkSaving(false);
    }
  };

  const handleProductExcelImport = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    event.target.value = '';
    if (!file || importSaving) return;
    setImportSaving(true);
    setImportError('');
    setImportResult(null);
    try {
      const result = await importProductsExcel(file, data?.links.excelImport || '/reporting/api/products/import.xlsx');
      setImportResult(result);
      if (result.errorCount > 0) {
        setImportError(result.message);
      }
      await onReload();
    } catch (error) {
      setImportError(error instanceof Error ? error.message : '엑셀 업로드에 실패했습니다.');
    } finally {
      setImportSaving(false);
    }
  };

  const handleBulkDelete = async () => {
    if (deleteSaving) return;
    if (!deleteCodes.length) {
      setDeleteError('삭제할 품번을 붙여넣으세요.');
      return;
    }
    if (!window.confirm(`${deleteCodes.length}개 품번을 삭제 처리할까요? 이미 사용된 제품은 삭제되지 않습니다.`)) {
      return;
    }
    setDeleteSaving(true);
    setDeleteError('');
    setDeleteReplacementError('');
    setDeleteReplacementMessage('');
    setDeleteReferenceReplacements({});
    setDeleteResult(null);
    try {
      const result = await bulkDeleteProducts(deleteCodes);
      setDeleteResult(result);
      await onReload();
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : '일괄 삭제에 실패했습니다.');
    } finally {
      setDeleteSaving(false);
    }
  };

  const productDeleteReferenceKey = (productCode: string, reference: ProductDeleteReference) => (
    `${productCode}:${reference.referenceType}:${reference.referenceId}`
  );

  const handleDeleteReferenceReplacementChange = (
    productCode: string,
    reference: ProductDeleteReference,
    replacementProductId: string,
  ) => {
    const referenceKey = productDeleteReferenceKey(productCode, reference);
    setDeleteReferenceReplacements((previous) => ({
      ...previous,
      [referenceKey]: replacementProductId,
    }));
    setDeleteError('');
    setDeleteReplacementError('');
  };

  const handleReplaceProductReference = async (productCode: string, reference: ProductDeleteReference) => {
    if (deleteSaving || replacingReferenceKey) return;
    const referenceKey = productDeleteReferenceKey(productCode, reference);
    const replacementId = Number(deleteReferenceReplacements[referenceKey] || 0);
    if (!replacementId) {
      setDeleteError(`${productCode}의 ${reference.itemName || '품목'} 대체 제품을 선택하세요.`);
      return;
    }
    const replacement = deleteReplacementOptions.find((option) => option.id === replacementId);
    if (!replacement) {
      setDeleteError('대체 제품을 찾을 수 없습니다.');
      return;
    }
    if (replacement.productCode === productCode) {
      setDeleteError(`${productCode} 자신은 대체 제품으로 사용할 수 없습니다.`);
      return;
    }

    setReplacingReferenceKey(referenceKey);
    setDeleteError('');
    try {
      const result = await replaceProductReference({
        productCode,
        referenceType: reference.referenceType,
        referenceId: reference.referenceId,
        replacementProductId: replacementId,
      });
      setDeleteResult((previous) => {
        const previousResults = previous?.results ?? [];
        const hasExistingRow = previousResults.some((row) => row.productCode === result.productCode);
        const nextResults = hasExistingRow
          ? previousResults.map((row) => (row.productCode === result.productCode ? result.result : row))
          : [result.result, ...previousResults];
        return {
          success: true,
          deletedCount: nextResults.filter((row) => row.status === 'deleted').length,
          blockedCount: nextResults.filter((row) => row.status === 'blocked').length,
          missingCount: nextResults.filter((row) => row.status === 'missing').length,
          replacedCount: (previous?.replacedCount ?? 0) + 1,
          results: nextResults,
          message: result.message,
        };
      });
      setDeleteReferenceReplacements((previous) => {
        const next = { ...previous };
        delete next[referenceKey];
        return next;
      });
      if (result.deletedOriginal) {
        await onReload();
      }
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : '품목 대체에 실패했습니다.');
    } finally {
      setReplacingReferenceKey('');
    }
  };

  const renderSortButton = (field: ProductSortField, label: string) => (
    <button
      className={`product-sort-button ${sort === field ? 'active' : ''}`.trim()}
      onClick={() => handleSort(field)}
      type="button"
    >
      {label}
      {sort === field ? <span>{order === 'asc' ? '↑' : '↓'}</span> : null}
    </button>
  );

  return (
    <section className="products-page">
      <WorkspaceRoutePage actions={productRouteActions} data={routeData} view="products" />
      {data?.source === 'unavailable' ? (
        <DashboardApiAlert message={data.error} title="제품관리 정보를 불러오지 못했습니다" />
      ) : null}

      <div className="dashboard-metric-grid customers-metric-grid">
        <DashboardMetricCard label="전체 제품" value={`${formatNumber(data?.metrics.totalProducts ?? 0)}건`} detail={data?.scope.label || '제품 기준'} icon={Archive} tone="blue" />
        <DashboardMetricCard label="활성" value={`${formatNumber(data?.metrics.activeProducts ?? 0)}건`} detail="견적/납품 선택 가능" icon={CheckCircle2} tone="green" />
        <DashboardMetricCard label="비활성" value={`${formatNumber(data?.metrics.inactiveProducts ?? 0)}건`} detail="목록 보존" icon={AlertTriangle} tone="amber" />
        <DashboardMetricCard label="검색 결과" value={`${formatNumber(data?.metrics.filteredProducts ?? 0)}건`} detail="현재 필터" icon={Search} tone="teal" />
      </div>

      <div className="products-toolbar customers-filter-bar">
        <label className="customers-search">
          <Search size={16} />
          <input
            onChange={(event) => {
              onQueryChange(event.target.value);
              onPageChange(1);
            }}
            placeholder="품번, 제품설명, 규격 검색"
            value={query}
          />
        </label>
        <select
          value={status}
          onChange={(event) => {
            onStatusChange(event.target.value);
            onPageChange(1);
          }}
        >
          <option value="">전체 상태</option>
          <option value="active">활성</option>
          <option value="inactive">비활성</option>
        </select>
        <button className="route-secondary-action" onClick={() => void onReload()} type="button">
          <RefreshCw size={16} />
          새로고침
        </button>
        <a className="route-secondary-action" href={data?.links.excelDownload || '/reporting/api/products/export.xlsx'}>
          <Download size={16} />
          엑셀
        </a>
        {canManage ? (
          <button className="route-primary-action" onClick={openCreate} type="button">
            <Plus size={16} />
            제품 등록
          </button>
        ) : null}
      </div>

      {formOpen ? (
        <form className="dashboard-panel notes-create-form product-editor-panel" onSubmit={handleSubmit} ref={productFormPanelRef}>
          <div className="dashboard-panel-heading">
            <div>
              <p className="eyebrow">{editingProduct ? 'Edit' : 'Create'}</p>
              <h2>{editingProduct ? '제품 수정' : '제품 등록'}</h2>
            </div>
            <button aria-label="닫기" className="icon-button" onClick={closeForm} type="button">
              <X size={17} />
            </button>
          </div>
          <div className="notes-create-grid product-form-grid">
            <label>
              <span>품번</span>
              <input value={form.productCode} onChange={(event) => handleFormChange('productCode', event.target.value)} />
            </label>
            <label>
              <span>제품설명</span>
              <input value={form.description} onChange={(event) => handleFormChange('description', event.target.value)} />
            </label>
            <label>
              <span>규격</span>
              <input value={form.specification} onChange={(event) => handleFormChange('specification', event.target.value)} />
            </label>
            <label>
              <span>단위</span>
              <input value={form.unit} onChange={(event) => handleFormChange('unit', event.target.value)} />
            </label>
            <label>
              <span>기준단가</span>
              <input inputMode="numeric" value={form.standardPrice} onChange={(event) => handleFormChange('standardPrice', event.target.value)} />
            </label>
            <label className="checkbox-row product-active-row">
              <input checked={form.isActive} onChange={(event) => handleFormChange('isActive', event.target.checked)} type="checkbox" />
              <span>활성 제품</span>
            </label>
          </div>
          {formError ? <p className="form-error">{formError}</p> : null}
          {formMessage ? <p className="form-success">{formMessage}</p> : null}
          <div className="notes-create-actions">
            <button className="route-secondary-action" onClick={closeForm} type="button">취소</button>
            <button className="route-primary-action" disabled={saving} type="submit">
              {saving ? '저장 중' : '저장'}
            </button>
          </div>
        </form>
      ) : null}

      <div className={`products-layout ${canManage ? '' : 'readonly'}`.trim()}>
        <section className="dashboard-panel products-main-panel">
          <div className="dashboard-panel-heading">
            <div>
              <h2>제품 목록</h2>
              <span>{loading ? '불러오는 중' : `현재 ${formatNumber(products.length)}건 표시`}</span>
            </div>
          </div>

          {loading && !data ? (
            <DashboardEmpty label="제품 데이터를 불러오는 중입니다" />
          ) : products.length ? (
            <>
              <div className="customers-table-wrap products-table-wrap">
                <table className="customers-table products-table">
                  <thead>
                    <tr>
                      <th>{renderSortButton('code', '품번')}</th>
                      <th>{renderSortButton('description', '제품설명')}</th>
                      <th>{renderSortButton('specification', '규격')}</th>
                      <th>{renderSortButton('unit', '단위')}</th>
                      <th>{renderSortButton('price', '기준단가')}</th>
                      <th>{renderSortButton('status', '상태')}</th>
                      <th>{renderSortButton('quoteCount', '견적')}</th>
                      <th>{renderSortButton('deliveryCount', '판매')}</th>
                      <th>{renderSortButton('updatedAt', '수정일')}</th>
                      <th>작업</th>
                    </tr>
                  </thead>
                  <tbody>
                    {products.map((product) => (
                      <tr key={product.id}>
                        <td>
                          <strong>{product.productCode}</strong>
                          <small className="customer-muted-cell">{product.createdBy}</small>
                        </td>
                        <td>{product.description || '-'}</td>
                        <td>{product.specification || '-'}</td>
                        <td>{product.unit || 'EA'}</td>
                        <td>{formatWon(product.standardPrice)}</td>
                        <td>
                          <span className={`product-status ${product.isActive ? 'active' : 'inactive'}`}>{product.isActive ? '활성' : '비활성'}</span>
                        </td>
                        <td>{formatNumber(product.quoteCount)}</td>
                        <td>{formatNumber(product.deliveryCount)}</td>
                        <td>{product.updatedAt ? formatDateTimeLabel(product.updatedAt) : '-'}</td>
                        <td>
                          <div className="product-row-actions">
                            {canManage ? (
                              <>
                                <button className="route-secondary-action" onClick={() => openEdit(product)} type="button">수정</button>
                              </>
                            ) : (
                              <span className="customer-muted-cell">읽기 전용</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="products-pagination">
                <button className="route-secondary-action" disabled={!pagination?.hasPrevious} onClick={() => onPageChange(Math.max(page - 1, 1))} type="button">
                  <ChevronLeft size={16} />
                  이전
                </button>
                <span>{formatNumber(pagination?.page ?? page)} / {formatNumber(pagination?.totalPages ?? 1)} 페이지</span>
                <button className="route-secondary-action" disabled={!pagination?.hasNext} onClick={() => onPageChange(page + 1)} type="button">
                  다음
                  <ChevronRight size={16} />
                </button>
              </div>
            </>
          ) : (
            <DashboardEmpty label="조건에 맞는 제품이 없습니다" />
          )}
        </section>

        {canManage ? (
        <aside className="products-side">
          <section className="dashboard-panel product-bulk-panel">
            <div className="dashboard-panel-heading">
              <div>
                <p className="eyebrow">Ecount / Excel</p>
                <h2>붙여넣기 반영</h2>
              </div>
              <div className="product-import-actions">
                <input
                  accept=".xlsx"
                  hidden
                  onChange={handleProductExcelImport}
                  ref={productImportInputRef}
                  type="file"
                />
                <button
                  className="icon-button"
                  disabled={importSaving}
                  onClick={() => productImportInputRef.current?.click()}
                  title="엑셀 업로드"
                  type="button"
                >
                  {importSaving ? <Loader2 className="spin-icon" size={16} /> : <Upload size={16} />}
                </button>
              </div>
            </div>
            <textarea
              onChange={(event) => {
                setBulkText(event.target.value);
                setBulkError('');
              }}
              placeholder={'품번\t제품설명\t규격\t단위\t출고단가'}
              rows={8}
              value={bulkText}
            />
            <div className="product-bulk-summary">
              <span>인식 {formatNumber(pastedProducts.length)}건</span>
              {pastedProducts.slice(0, 3).map((item) => (
                <small key={item.productCode}>{item.productCode} · {item.unit} · {formatWon(Number(item.standardPrice) || 0)}</small>
              ))}
            </div>
            {importError ? <p className="form-error">{importError}</p> : null}
            {importResult && !importError ? <p className="form-success">{importResult.message}</p> : null}
            {bulkError ? <p className="form-error">{bulkError}</p> : null}
            {bulkResult && !bulkError ? <p className="form-success">{bulkResult.message}</p> : null}
            <button className="route-primary-action" disabled={bulkSaving || !pastedProducts.length} onClick={handleBulkUpsert} type="button">
              {bulkSaving ? '반영 중' : '등록/갱신'}
            </button>
          </section>

          <section className="dashboard-panel product-bulk-panel">
            <div className="dashboard-panel-heading">
              <div>
                <p className="eyebrow">Bulk Delete</p>
                <h2>품번 일괄 삭제</h2>
              </div>
              <Trash2 size={18} />
            </div>
            <textarea
              onChange={(event) => {
                setDeleteText(event.target.value);
                setDeleteError('');
              }}
              placeholder={'삭제할 품번을 한 줄에 하나씩 붙여넣기'}
              rows={7}
              value={deleteText}
            />
            <div className="product-bulk-summary">
              <span>삭제 대상 {formatNumber(deleteCodes.length)}건</span>
              {deleteCodes.slice(0, 4).map((code) => <small key={code}>{code}</small>)}
            </div>
            {deleteError ? <p className="form-error">{deleteError}</p> : null}
            {deleteResult ? <p className="form-success">{deleteResult.message}</p> : null}
            {replaceableDeleteRows.length > 0 ? (
              <div className="product-delete-replacement-panel">
                <div>
                  <strong>차단 품목 개별 대체</strong>
                  <span>견적/납품에 사용된 품목마다 대체 제품을 선택하고 한 건씩 이동합니다. 마지막 품목이 이동되면 원제품이 삭제됩니다.</span>
                </div>
                {deleteReplacementError ? <p className="form-error">{deleteReplacementError}</p> : null}
                {deleteReplacementMessage ? <p className="form-success">{deleteReplacementMessage}</p> : null}
                <div className="product-delete-replacement-search">
                  <input
                    onChange={(event) => {
                      setDeleteReplacementSearch(event.target.value);
                      setDeleteReplacementError('');
                    }}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') {
                        event.preventDefault();
                        void handleDeleteReplacementSearch();
                      }
                    }}
                    placeholder="대체 제품 품번, 설명, 규격 검색"
                    value={deleteReplacementSearch}
                  />
                  <button
                    className="route-secondary-action"
                    disabled={deleteReplacementLoading}
                    onClick={() => void handleDeleteReplacementSearch()}
                    type="button"
                  >
                    검색
                  </button>
                </div>
                {deleteReplacementLoading ? (
                  <div className="product-delete-replacement-loading">
                    <Loader2 className="spin-icon" size={15} />
                    <span>대체 제품 목록을 불러오는 중입니다. 오래 걸리면 품번으로 검색하세요.</span>
                  </div>
                ) : (
                  <div className="product-delete-replacement-list">
                    {replaceableDeleteRows.map((row) => {
                      const replacementOptions = deleteReplacementOptions.filter((option) => (
                        option.productCode !== row.productCode &&
                        !deleteCodes.includes(option.productCode)
                      ));
                      return (
                        <div className="product-delete-reference-group" key={row.productCode}>
                          <div className="product-delete-reference-heading">
                            <strong>{row.productCode}</strong>
                            <span>납품/견적 품목 {formatNumber(row.deliveryItemCount ?? 0)}건 · 레거시 견적 {formatNumber(row.quoteItemCount ?? 0)}건</span>
                          </div>
                          {row.hasMoreReferences ? <small>표시된 품목 외 추가 참조가 있습니다. 표시된 항목부터 대체한 뒤 다시 확인하세요.</small> : null}
                          {(row.references ?? []).length ? (
                            (row.references ?? []).map((reference) => {
                              const referenceKey = productDeleteReferenceKey(row.productCode, reference);
                              const selectedReplacement = deleteReferenceReplacements[referenceKey] || '';
                              const isReplacing = replacingReferenceKey === referenceKey;
                              return (
                                <div className="product-delete-reference-row" key={referenceKey}>
                                  <div>
                                    <strong>{reference.itemName || row.productCode}</strong>
                                    <span>{[
                                      reference.scheduleTypeLabel || (reference.referenceType === 'quoteItem' ? '레거시 견적' : '품목'),
                                      reference.scheduleId ? `일정 #${reference.scheduleId}` : '',
                                      reference.historyId && !reference.scheduleId ? `영업노트 #${reference.historyId}` : '',
                                      reference.quoteNumber ? `견적 ${reference.quoteNumber}` : '',
                                      reference.customerName,
                                      reference.companyName,
                                      reference.departmentName,
                                      reference.scheduleDate ? formatDateLabel(reference.scheduleDate) : '',
                                      reference.quoteGroupLabel,
                                      `수량 ${formatNumber(reference.quantity)}${reference.unit ? reference.unit : ''}`,
                                    ].filter(Boolean).join(' · ')}</span>
                                  </div>
                                  <select
                                    disabled={Boolean(replacingReferenceKey)}
                                    onChange={(event) => handleDeleteReferenceReplacementChange(row.productCode, reference, event.target.value)}
                                    value={selectedReplacement}
                                  >
                                    <option value="">대체 제품 선택</option>
                                    {replacementOptions.map((option) => (
                                      <option key={option.id} value={option.id}>
                                        {option.productCode} · {option.description || option.specification || option.unit}
                                      </option>
                                    ))}
                                  </select>
                                  <button
                                    className="route-secondary-action"
                                    disabled={deleteSaving || Boolean(replacingReferenceKey) || !selectedReplacement}
                                    onClick={() => handleReplaceProductReference(row.productCode, reference)}
                                    type="button"
                                  >
                                    {isReplacing ? '처리 중' : '이 품목 대체'}
                                  </button>
                                </div>
                              );
                            })
                          ) : (
                            <small>표시할 품목 참조가 없습니다. 다시 삭제 실행으로 상태를 확인하세요.</small>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            ) : null}
            <button className="route-secondary-action danger" disabled={deleteSaving || !deleteCodes.length} onClick={handleBulkDelete} type="button">
              {deleteSaving ? '삭제 중' : '삭제 실행'}
            </button>
          </section>
        </aside>
        ) : null}
      </div>
    </section>
  );
}