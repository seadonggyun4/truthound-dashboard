import { useMemo, useState } from 'react'

type FilterFn<T> = (item: T, search: string) => boolean

interface UseClientFilterOptions<T> {
  /** 검색 대상 필드를 지정하는 함수 */
  searchFn?: FilterFn<T>
  /** 추가 필터 조건 */
  filters?: Record<string, (item: T, value: string) => boolean>
}

interface UseClientFilterReturn<T> {
  /** 필터링된 결과 */
  filtered: T[]
  /** 검색어 */
  search: string
  /** 검색어 변경 */
  setSearch: (value: string) => void
  /** 필터 값들 */
  filterValues: Record<string, string>
  /** 특정 필터 값 변경 */
  setFilter: (key: string, value: string) => void
  /** 모든 필터 초기화 */
  resetFilters: () => void
}

/**
 * 클라이언트 사이드 필터링 훅
 *
 * @example
 * ```tsx
 * const { filtered, search, setSearch, setFilter } = useClientFilter(terms, {
 *   searchFn: (item, search) =>
 *     item.name.toLowerCase().includes(search) ||
 *     item.definition.toLowerCase().includes(search),
 *   filters: {
 *     category: (item, value) => item.category_id === value,
 *     status: (item, value) => item.status === value,
 *   }
 * })
 * ```
 */
export function useClientFilter<T>(
  items: T[],
  options: UseClientFilterOptions<T> = {}
): UseClientFilterReturn<T> {
  const { searchFn, filters = {} } = options

  const [search, setSearch] = useState('')
  const [filterValues, setFilterValues] = useState<Record<string, string>>({})

  const filtered = useMemo(() => {
    let result = items

    // 검색어 필터링
    if (search && searchFn) {
      const lowerSearch = search.toLowerCase()
      result = result.filter(item => searchFn(item, lowerSearch))
    }

    // 추가 필터 적용
    for (const [key, filterFn] of Object.entries(filters)) {
      const value = filterValues[key]
      if (value) {
        result = result.filter(item => filterFn(item, value))
      }
    }

    return result
  }, [items, search, searchFn, filters, filterValues])

  const setFilter = (key: string, value: string) => {
    setFilterValues(prev => ({ ...prev, [key]: value }))
  }

  const resetFilters = () => {
    setSearch('')
    setFilterValues({})
  }

  return {
    filtered,
    search,
    setSearch,
    filterValues,
    setFilter,
    resetFilters,
  }
}
