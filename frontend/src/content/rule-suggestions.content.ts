/**
 * Rule Suggestions translations
 *
 * This file contains translations for profile-based
 * validation rule suggestions feature.
 */
import { t, type Dictionary } from 'intlayer'

const ruleSuggestionsContent = {
  key: 'ruleSuggestions',
  content: {
    // Dialog title and description
    title: t({ en: 'Suggested Validation Rules', ko: '제안된 검증 규칙' }),
    description: t({
      en: 'Based on profile analysis, we suggest the following validation rules.',
      ko: '프로파일 분석을 기반으로 다음 검증 규칙을 제안합니다.',
    }),
    selectRulesDesc: t({
      en: 'Select the rules you want to apply.',
      ko: '적용할 규칙을 선택하세요.',
    }),

    // Stats
    suggestions: t({ en: 'suggestions', ko: '제안' }),
    highConfidence: t({ en: 'high confidence', ko: '높은 신뢰도' }),

    // Selection
    selectAll: t({ en: 'Select All', ko: '전체 선택' }),
    deselectAll: t({ en: 'Deselect All', ko: '전체 해제' }),
    selected: t({ en: 'selected', ko: '선택됨' }),

    // Actions
    generateRules: t({ en: 'Generate Rules', ko: '규칙 생성' }),
    applyRules: t({ en: 'Apply Rules', ko: '규칙 적용' }),
    applying: t({ en: 'Applying...', ko: '적용 중...' }),
    analyzingProfile: t({
      en: 'Analyzing profile data...',
      ko: '프로파일 데이터 분석 중...',
    }),

    // Filter and search
    searchSuggestions: t({ en: 'Search suggestions...', ko: '제안 검색...' }),
    allCategories: t({ en: 'All Categories', ko: '모든 카테고리' }),
    noSuggestionsMatch: t({
      en: 'No suggestions match your filters.',
      ko: '필터에 맞는 제안이 없습니다.',
    }),

    // Empty state
    noSuggestionsAvailable: t({
      en: 'No suggestions available. Run profiling first.',
      ko: '제안이 없습니다. 먼저 프로파일링을 실행하세요.',
    }),

    // Confidence levels
    confidence: t({ en: 'Confidence', ko: '신뢰도' }),
    highConfidenceLabel: t({ en: 'High confidence', ko: '높은 신뢰도' }),
    mediumConfidenceLabel: t({ en: 'Medium confidence', ko: '중간 신뢰도' }),
    lowConfidenceLabel: t({ en: 'Low confidence', ko: '낮은 신뢰도' }),

    // Categories
    completeness: t({ en: 'Completeness', ko: '완전성' }),
    uniqueness: t({ en: 'Uniqueness', ko: '고유성' }),
    distribution: t({ en: 'Distribution', ko: '분포' }),
    string: t({ en: 'String', ko: '문자열' }),
    datetime: t({ en: 'Datetime', ko: '날짜/시간' }),

    // Status messages
    rulesApplied: t({
      en: 'Rules applied successfully',
      ko: '규칙이 성공적으로 적용되었습니다',
    }),
    appliedCount: t({ en: 'rules applied', ko: '개의 규칙 적용됨' }),

    // Validation reasons
    lowNulls: t({
      en: 'Column has less than 1% null values',
      ko: '컬럼의 null 값이 1% 미만입니다',
    }),
    noNulls: t({
      en: 'Column has 0% null values',
      ko: '컬럼에 null 값이 없습니다',
    }),
    highUniqueness: t({
      en: 'Column has 100% unique values',
      ko: '컬럼의 모든 값이 고유합니다',
    }),
    lowCardinality: t({
      en: 'Column has low cardinality with limited distinct values',
      ko: '컬럼의 카디널리티가 낮습니다',
    }),
    numericRange: t({
      en: 'Column values fall within a defined numeric range',
      ko: '컬럼 값이 정의된 숫자 범위 내에 있습니다',
    }),
    emailPattern: t({
      en: 'Column name suggests email format',
      ko: '컬럼 이름이 이메일 형식을 암시합니다',
    }),
    phonePattern: t({
      en: 'Column name suggests phone number format',
      ko: '컬럼 이름이 전화번호 형식을 암시합니다',
    }),
  },
} satisfies Dictionary

export default ruleSuggestionsContent
