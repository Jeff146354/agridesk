import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { getErrorMessage } from '../utils/error';

export function useListData({
  fetcher,
  filterFn,
  initialSearch = '',
  initialFilters = {},
  fallbackError = 'Gagal memuat data',
}) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState(initialSearch);
  const [filters, setFilters] = useState(initialFilters);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await fetcher();
      if (!mountedRef.current) return null;
      const nextItems = Array.isArray(data) ? data : data || [];
      setItems(nextItems);
      return nextItems;
    } catch (err) {
      if (mountedRef.current) {
        setError(getErrorMessage(err, fallbackError));
      }
      return null;
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [fetcher, fallbackError]);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = useMemo(() => {
    if (!filterFn) return items;
    return filterFn(items, search, filters);
  }, [items, search, filters, filterFn]);

  return {
    items,
    filtered,
    loading,
    error,
    search,
    setSearch,
    filters,
    setFilters,
    reload: load,
  };
}
