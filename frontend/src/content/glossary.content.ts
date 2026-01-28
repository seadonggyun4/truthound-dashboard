/**
 * Business glossary page translations.
 *
 * Contains translations for the glossary management page.
 */
import { t, type Dictionary } from 'intlayer'

const glossaryContent = {
  key: 'glossary',
  content: {
    // Page titles
    title: t({ en: 'Business Glossary', ko: '비즈니스 용어집' }),
    subtitle: t({
      en: 'Manage business terms and definitions',
      ko: '비즈니스 용어와 정의 관리',
    }),
    terms: t({ en: 'Terms', ko: '용어' }),
    categories: t({ en: 'Categories', ko: '카테고리' }),

    // Actions
    addTerm: t({ en: 'Add Term', ko: '용어 추가' }),
    editTerm: t({ en: 'Edit Term', ko: '용어 수정' }),
    deleteTerm: t({ en: 'Delete Term', ko: '용어 삭제' }),
    addCategory: t({ en: 'Add Category', ko: '카테고리 추가' }),

    // Form fields
    termName: t({ en: 'Term Name', ko: '용어명' }),
    definition: t({ en: 'Definition', ko: '정의' }),
    category: t({ en: 'Category', ko: '카테고리' }),
    owner: t({ en: 'Owner', ko: '담당자' }),
    selectCategory: t({ en: 'Select category', ko: '카테고리 선택' }),
    noCategory: t({ en: 'No category', ko: '카테고리 없음' }),

    // Relationships
    relationships: t({ en: 'Relationships', ko: '관계' }),
    synonyms: t({ en: 'Synonyms', ko: '동의어' }),
    relatedTerms: t({ en: 'Related Terms', ko: '관련 용어' }),
    addRelationship: t({ en: 'Add Relationship', ko: '관계 추가' }),
    selectTerm: t({ en: 'Select term', ko: '용어 선택' }),

    // History
    history: t({ en: 'History', ko: '변경 이력' }),
    noHistory: t({ en: 'No changes recorded', ko: '기록된 변경 이력 없음' }),
    changedBy: t({ en: 'Changed by', ko: '변경자' }),
    changedFrom: t({ en: 'From', ko: '이전' }),
    changedTo: t({ en: 'To', ko: '이후' }),

    // Status
    status: {
      label: t({ en: 'Status', ko: '상태' }),
      draft: t({ en: 'Draft', ko: '임시저장' }),
      approved: t({ en: 'Approved', ko: '승인됨' }),
      deprecated: t({ en: 'Deprecated', ko: '폐기됨' }),
    },

    // Relationship types
    relationshipTypes: {
      synonym: t({ en: 'Synonym', ko: '동의어' }),
      related: t({ en: 'Related', ko: '관련' }),
      parent: t({ en: 'Parent', ko: '상위' }),
      child: t({ en: 'Child', ko: '하위' }),
    },

    // Search & Filter
    searchTerms: t({ en: 'Search terms...', ko: '용어 검색...' }),
    filterByCategory: t({ en: 'Filter by category', ko: '카테고리 필터' }),
    filterByStatus: t({ en: 'Filter by status', ko: '상태 필터' }),
    allCategories: t({ en: 'All categories', ko: '모든 카테고리' }),
    allStatuses: t({ en: 'All statuses', ko: '모든 상태' }),

    // Empty states
    noTerms: t({ en: 'No terms found', ko: '용어가 없습니다' }),
    noTermsYet: t({ en: 'No terms yet', ko: '등록된 용어가 없습니다' }),
    noTermsDesc: t({
      en: 'Add your first business term to start building your glossary',
      ko: '첫 번째 비즈니스 용어를 추가하여 용어집을 구축하세요',
    }),
    addFirstTerm: t({ en: 'Add Your First Term', ko: '첫 번째 용어 추가' }),

    // Confirmation
    confirmDelete: t({
      en: 'Are you sure you want to delete this term? This action cannot be undone.',
      ko: '이 용어를 삭제하시겠습니까? 이 작업은 취소할 수 없습니다.',
    }),

    // Messages
    loadError: t({ en: 'Failed to load terms', ko: '용어를 불러오지 못했습니다' }),
    createSuccess: t({ en: 'Term created successfully', ko: '용어가 생성되었습니다' }),
    createError: t({ en: 'Failed to create term', ko: '용어 생성에 실패했습니다' }),
    updateSuccess: t({ en: 'Term updated successfully', ko: '용어가 수정되었습니다' }),
    updateError: t({ en: 'Failed to update term', ko: '용어 수정에 실패했습니다' }),
    deleteSuccess: t({ en: 'Term deleted successfully', ko: '용어가 삭제되었습니다' }),
    deleteError: t({ en: 'Failed to delete term', ko: '용어 삭제에 실패했습니다' }),

    // Tabs
    tabs: {
      overview: t({ en: 'Overview', ko: '개요' }),
      relationships: t({ en: 'Relationships', ko: '관계' }),
      history: t({ en: 'History', ko: '이력' }),
      comments: t({ en: 'Comments', ko: '댓글' }),
      terms: t({ en: 'Terms', ko: '용어' }),
      categories: t({ en: 'Categories', ko: '카테고리' }),
    },

    // Category management
    categoryManagement: {
      title: t({ en: 'Category Management', ko: '카테고리 관리' }),
      subtitle: t({ en: 'Organize terms with hierarchical categories', ko: '계층적 카테고리로 용어 정리' }),
      addCategory: t({ en: 'Add Category', ko: '카테고리 추가' }),
      editCategory: t({ en: 'Edit Category', ko: '카테고리 수정' }),
      deleteCategory: t({ en: 'Delete Category', ko: '카테고리 삭제' }),
      categoryName: t({ en: 'Category Name', ko: '카테고리 이름' }),
      parentCategory: t({ en: 'Parent Category', ko: '상위 카테고리' }),
      noParent: t({ en: 'No parent (root level)', ko: '상위 없음 (최상위)' }),
      confirmDeleteCategory: t({
        en: 'Are you sure you want to delete this category? Terms in this category will become uncategorized.',
        ko: '이 카테고리를 삭제하시겠습니까? 이 카테고리의 용어는 미분류 상태가 됩니다.',
      }),
      noCategories: t({ en: 'No categories yet', ko: '등록된 카테고리가 없습니다' }),
      noCategoriesDesc: t({
        en: 'Create categories to organize your business terms',
        ko: '비즈니스 용어를 정리할 카테고리를 생성하세요',
      }),
      createSuccess: t({ en: 'Category created successfully', ko: '카테고리가 생성되었습니다' }),
      createError: t({ en: 'Failed to create category', ko: '카테고리 생성에 실패했습니다' }),
      updateSuccess: t({ en: 'Category updated successfully', ko: '카테고리가 수정되었습니다' }),
      updateError: t({ en: 'Failed to update category', ko: '카테고리 수정에 실패했습니다' }),
      deleteSuccess: t({ en: 'Category deleted successfully', ko: '카테고리가 삭제되었습니다' }),
      deleteError: t({ en: 'Failed to delete category', ko: '카테고리 삭제에 실패했습니다' }),
      termCount: t({ en: 'terms', ko: '개 용어' }),
      subcategories: t({ en: 'Subcategories', ko: '하위 카테고리' }),
      expand: t({ en: 'Expand', ko: '펼치기' }),
      collapse: t({ en: 'Collapse', ko: '접기' }),
    },

    // Relationship management
    relationshipManagement: {
      title: t({ en: 'Term Relationships', ko: '용어 관계' }),
      addRelationship: t({ en: 'Add Relationship', ko: '관계 추가' }),
      removeRelationship: t({ en: 'Remove', ko: '제거' }),
      selectRelationType: t({ en: 'Select relationship type', ko: '관계 유형 선택' }),
      selectTargetTerm: t({ en: 'Select target term', ko: '대상 용어 선택' }),
      noRelationships: t({ en: 'No relationships defined', ko: '정의된 관계가 없습니다' }),
      createSuccess: t({ en: 'Relationship created successfully', ko: '관계가 생성되었습니다' }),
      createError: t({ en: 'Failed to create relationship', ko: '관계 생성에 실패했습니다' }),
      deleteSuccess: t({ en: 'Relationship removed successfully', ko: '관계가 제거되었습니다' }),
      deleteError: t({ en: 'Failed to remove relationship', ko: '관계 제거에 실패했습니다' }),
      duplicateError: t({ en: 'This relationship already exists', ko: '이 관계는 이미 존재합니다' }),
      selfReferenceError: t({ en: 'A term cannot have a relationship with itself', ko: '용어는 자기 자신과 관계를 가질 수 없습니다' }),
      parentTerms: t({ en: 'Parent Terms', ko: '상위 용어' }),
      childTerms: t({ en: 'Child Terms', ko: '하위 용어' }),
    },

    // Hierarchy
    hierarchy: {
      viewAsTree: t({ en: 'View as Tree', ko: '트리로 보기' }),
      viewAsList: t({ en: 'View as List', ko: '목록으로 보기' }),
      rootLevel: t({ en: 'Root Level', ko: '최상위' }),
      level: t({ en: 'Level', ko: '레벨' }),
      path: t({ en: 'Path', ko: '경로' }),
    },
  },
} satisfies Dictionary

export default glossaryContent
