# Quality Reporter

Quality Reporter는 검증 규칙의 품질을 정량적으로 평가하고 다양한 형식의 리포트를 생성하는 모듈입니다.

## 개요

Quality Reporter는 truthound의 품질 평가 시스템을 기반으로 검증 규칙의 정확도를 측정합니다. 혼동 행렬(Confusion Matrix) 기반의 F1 Score, Precision, Recall, Accuracy 메트릭을 계산하여 규칙의 품질 수준을 분류합니다.

### 품질 평가 메트릭

| 메트릭 | 정의 | 계산식 |
|--------|------|--------|
| **F1 Score** | Precision과 Recall의 조화 평균 | 2 × (Precision × Recall) / (Precision + Recall) |
| **Precision** | 예측된 양성 중 실제 양성의 비율 | TP / (TP + FP) |
| **Recall** | 실제 양성 중 예측된 양성의 비율 | TP / (TP + FN) |
| **Accuracy** | 전체 예측 중 정확한 예측의 비율 | (TP + TN) / (TP + TN + FP + FN) |

### 혼동 행렬

품질 메트릭은 혼동 행렬의 네 가지 요소로부터 계산됩니다:

| 요소 | 정의 |
|------|------|
| **TP (True Positive)** | 규칙이 정상 데이터를 정상으로 올바르게 판정 |
| **TN (True Negative)** | 규칙이 이상 데이터를 이상으로 올바르게 판정 |
| **FP (False Positive)** | 규칙이 정상 데이터를 이상으로 잘못 판정 (오탐) |
| **FN (False Negative)** | 규칙이 이상 데이터를 정상으로 잘못 판정 (미탐) |

## 품질 수준 분류

F1 Score를 기준으로 규칙의 품질 수준을 분류합니다:

| 수준 | F1 Score 범위 | 설명 |
|------|---------------|------|
| **Excellent** | ≥ 0.9 | 우수한 품질, 운영 환경에 적합 |
| **Good** | 0.7 ~ 0.9 | 양호한 품질, 대부분의 환경에 적합 |
| **Acceptable** | 0.5 ~ 0.7 | 허용 가능한 품질, 개선 권장 |
| **Poor** | 0.3 ~ 0.5 | 미흡한 품질, 규칙 재검토 필요 |
| **Unacceptable** | < 0.3 | 부적합, 즉시 수정 필요 |

### 품질 임계값 설정

기본 임계값은 사용자 정의가 가능합니다:

```json
{
  "thresholds": {
    "excellent": 0.9,
    "good": 0.7,
    "acceptable": 0.5,
    "poor": 0.3
  }
}
```

## 품질 점수 산정

### 점수 산정 설정

| 설정 | 설명 | 기본값 | 범위 |
|------|------|--------|------|
| **sample_size** | 평가에 사용할 데이터 샘플 크기 | 10,000 | 100 ~ 1,000,000 |
| **rule_names** | 평가할 특정 규칙 목록 (선택) | 전체 규칙 | - |

### 점수 산정 결과

점수 산정 후 다음 정보가 제공됩니다:

| 항목 | 내용 |
|------|------|
| **scores** | 개별 규칙의 품질 점수 목록 |
| **statistics** | 전체 통계 (평균, 최소, 최대 F1 등) |
| **level_distribution** | 품질 수준별 규칙 분포 |

## 리포트 생성

### 지원 형식

| 형식 | 확장자 | 용도 |
|------|--------|------|
| **Console** | .txt | 터미널 출력, 로깅 |
| **JSON** | .json | API 연동, 자동화 |
| **HTML** | .html | 대시보드, 문서화 |
| **Markdown** | .md | Git 저장소, 위키 |
| **JUnit** | .xml | CI/CD 파이프라인 |

### 리포트 설정

| 설정 | 설명 | 기본값 |
|------|------|--------|
| **title** | 리포트 제목 | - |
| **description** | 리포트 설명 | - |
| **include_metrics** | 상세 메트릭 포함 | true |
| **include_confusion_matrix** | 혼동 행렬 포함 | false |
| **include_recommendations** | 권장사항 포함 | true |
| **include_statistics** | 통계 섹션 포함 | true |
| **include_summary** | 요약 섹션 포함 | true |
| **include_charts** | 차트 포함 (HTML만 해당) | true |
| **sort_order** | 정렬 기준 | f1_desc |
| **max_scores** | 포함할 최대 점수 수 | 전체 |
| **theme** | HTML 테마 | professional |

### 정렬 옵션

| 옵션 | 설명 |
|------|------|
| **f1_desc** | F1 Score 내림차순 |
| **f1_asc** | F1 Score 오름차순 |
| **precision_desc** | Precision 내림차순 |
| **recall_desc** | Recall 내림차순 |
| **name_asc** | 규칙 이름 오름차순 |
| **name_desc** | 규칙 이름 내림차순 |

### HTML 테마

| 테마 | 설명 |
|------|------|
| **light** | 밝은 배경 테마 |
| **dark** | 어두운 배경 테마 |
| **professional** | 전문적인 비즈니스 테마 |

## 점수 필터링

### 필터 옵션

| 필터 | 설명 | 예시 |
|------|------|------|
| **min_level** | 최소 품질 수준 | good |
| **max_level** | 최대 품질 수준 | excellent |
| **min_f1** | 최소 F1 Score | 0.7 |
| **max_f1** | 최대 F1 Score | 0.95 |
| **min_confidence** | 최소 신뢰도 | 0.8 |
| **should_use_only** | 사용 권장 규칙만 | true |
| **include_columns** | 포함할 컬럼 | ["email", "phone"] |
| **exclude_columns** | 제외할 컬럼 | ["internal_id"] |
| **rule_types** | 규칙 유형 | ["not_null", "unique"] |

## 점수 비교

여러 소스의 품질 점수를 비교할 수 있습니다:

| 설정 | 설명 |
|------|------|
| **source_ids** | 비교할 소스 ID 목록 |
| **sort_by** | 정렬 기준 (f1_score, precision, recall, confidence) |
| **descending** | 내림차순 정렬 여부 |
| **group_by** | 그룹화 기준 (column, level, rule_type) |
| **max_results** | 최대 결과 수 |

## API 참조

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/quality/formats` | GET | 사용 가능한 형식 및 옵션 조회 |
| `/quality/sources/{id}/score` | POST | 품질 점수 산정 |
| `/quality/sources/{id}/report` | POST | 리포트 생성 |
| `/quality/sources/{id}/report/download` | GET | 리포트 다운로드 |
| `/quality/sources/{id}/report/preview` | GET | 리포트 미리보기 |
| `/quality/sources/{id}/summary` | GET | 품질 요약 조회 |
| `/quality/compare` | POST | 소스간 점수 비교 |
| `/quality/filter` | POST | 점수 필터링 |

### 요청 예시

#### 품질 점수 산정

```json
POST /api/v1/quality/sources/{source_id}/score
{
  "sample_size": 10000,
  "rule_names": ["not_null_email", "unique_id"],
  "thresholds": {
    "excellent": 0.95,
    "good": 0.8,
    "acceptable": 0.6,
    "poor": 0.4
  }
}
```

#### 리포트 생성

```json
POST /api/v1/quality/sources/{source_id}/report
{
  "format": "html",
  "config": {
    "title": "Data Quality Report",
    "include_metrics": true,
    "include_statistics": true,
    "include_charts": true,
    "theme": "professional",
    "sort_order": "f1_desc",
    "max_scores": 50
  }
}
```

#### 점수 필터링

```json
POST /api/v1/quality/filter?source_id={source_id}
{
  "min_level": "good",
  "min_f1": 0.7,
  "should_use_only": true,
  "include_columns": ["email", "phone"]
}
```

## 권장 사용 지침

### 품질 수준별 권장 조치

| 품질 수준 | 권장 조치 |
|-----------|----------|
| **Excellent** | 운영 환경에 배포 가능 |
| **Good** | 대부분의 환경에 사용 가능, 모니터링 권장 |
| **Acceptable** | 개발/테스트 환경에서 사용, 개선 계획 수립 |
| **Poor** | 규칙 로직 재검토 필요 |
| **Unacceptable** | 즉시 수정 또는 비활성화 |

### 리포트 형식별 권장 대상

| 대상 | 권장 형식 |
|------|----------|
| **경영진** | HTML (요약 포함) |
| **데이터 엔지니어** | JSON (자동화용) |
| **QA 팀** | Markdown |
| **CI/CD 시스템** | JUnit XML |

### 샘플 크기 가이드라인

| 데이터셋 크기 | 권장 샘플 크기 | 비고 |
|--------------|---------------|------|
| < 10,000 rows | 전체 데이터 | 샘플링 불필요 |
| 10,000 ~ 100,000 rows | 10,000 | 기본값 적합 |
| 100,000 ~ 1M rows | 50,000 | 통계적 유의성 확보 |
| > 1M rows | 100,000+ | 대표성 확보 필요 |

## 문제 해결

| 문제 | 원인 | 해결 방법 |
|------|------|----------|
| 점수가 반환되지 않음 | 검증 결과 없음 | 먼저 검증 실행 필요 |
| F1 점수가 낮음 | 규칙이 너무 엄격/느슨함 | 규칙 임계값 조정 |
| 리포트 생성 실패 | 잘못된 형식 지정 | format 파라미터 확인 |
| 빈 리포트 | 필터 조건에 맞는 점수 없음 | 필터 조건 완화 |

## 제한 사항

현재 버전에서 다음 기능은 지원되지 않습니다:

| 기능 | 상태 | 비고 |
|------|------|------|
| Cross-validation folds 설정 | 미지원 | truthound 기본 scorer 사용 |
| Chart type 커스터마이징 | 미지원 | HTML 기본 차트만 제공 |
| Display mode 설정 | 미지원 | 기본 모드만 제공 |
| Confidence interval 표시 | 미지원 | 메트릭만 표시 |
| Trend analysis | 미지원 | 현재 스냅샷만 제공 |

향후 truthound 라이브러리 업데이트에 따라 지원 범위가 확대될 수 있습니다.
