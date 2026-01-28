# Enterprise Sampling

Enterprise-scale sampling capabilities for datasets from 100M to billions of rows, powered by truthound 1.2.10.

## Overview

When working with massive datasets (100M+ rows), full data scans become impractical due to time and memory constraints. Enterprise Sampling provides intelligent sampling strategies that maintain statistical validity while dramatically reducing processing time.

## Scale Categories

The system automatically classifies datasets by scale and recommends appropriate strategies:

| Category | Row Count | Recommended Strategy | Description |
|----------|-----------|---------------------|-------------|
| Small | < 1M | None | No sampling needed |
| Medium | 1M - 10M | Column-Aware | Type-weighted adaptive sampling |
| Large | 10M - 100M | Block | Parallel block-based sampling |
| XLarge | 100M - 1B | Multi-Stage | Hierarchical multi-pass sampling |
| XXLarge | > 1B | Multi-Stage + Sketches | Probabilistic data structures |

## Sampling Strategies

### Block Sampling

Best for: **10M - 100M rows**

Divides data into fixed-size blocks and samples proportionally from each block. Ensures even coverage across the dataset.

**Configuration:**
```json
{
  "strategy": "block",
  "block_config": {
    "block_size": 0,
    "sample_per_block": null,
    "parallel": {
      "max_workers": 4,
      "enable_work_stealing": true,
      "scheduling_policy": "adaptive"
    }
  }
}
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| block_size | 0 (auto) | Rows per block. Auto-detect aims for ~100 blocks |
| sample_per_block | null | Samples per block. null = proportional |
| max_workers | 4 | Parallel workers (1-32) |

### Multi-Stage Sampling

Best for: **100M - 1B rows**

Progressively reduces data in multiple stages. Each stage reduces by factor `(total_rows / target)^(1/stages)`.

**Configuration:**
```json
{
  "strategy": "multi_stage",
  "multi_stage_config": {
    "num_stages": 3,
    "stage_reduction_factor": null,
    "early_stop_enabled": true
  }
}
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| num_stages | 3 | Number of sampling stages (2-5) |
| stage_reduction_factor | null | Reduction per stage (null = auto) |
| early_stop_enabled | true | Stop early on convergence |

### Column-Aware Sampling

Best for: **Mixed column types**

Adjusts sample size based on column type complexity:
- **Strings**: 2x multiplier (high cardinality)
- **Categoricals**: 0.5x multiplier (low cardinality)
- **Complex types**: 3x multiplier (List/Struct)
- **Numeric**: 1x baseline

**Configuration:**
```json
{
  "strategy": "column_aware",
  "column_aware_config": {
    "string_multiplier": 2.0,
    "categorical_multiplier": 0.5,
    "complex_multiplier": 3.0,
    "numeric_multiplier": 1.0
  }
}
```

### Progressive Sampling

Best for: **Exploratory analysis, early stopping**

Iteratively increases sample size until estimates converge within threshold.

**Configuration:**
```json
{
  "strategy": "progressive",
  "progressive_config": {
    "convergence_threshold": 0.01,
    "max_stages": 5,
    "initial_sample_ratio": 0.01,
    "growth_factor": 2.0
  }
}
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| convergence_threshold | 0.01 | Stop when change < threshold |
| max_stages | 5 | Maximum progressive stages |
| initial_sample_ratio | 0.01 | Start with 1% of data |
| growth_factor | 2.0 | Double sample size per stage |

## Quality Presets

Pre-configured quality levels for common use cases:

| Preset | Target Rows | Confidence | Margin of Error | Use Case |
|--------|-------------|------------|-----------------|----------|
| Sketch | 10K | 80% | 10% | Fast approximation |
| Quick | 50K | 90% | 5% | Quick estimates |
| Standard | 100K | 95% | 5% | Balanced (default) |
| High | 500K | 99% | 3% | High accuracy |
| Exact | Full | 100% | 0% | Full scan |

## Probabilistic Data Structures

For datasets exceeding 10B rows, probabilistic data structures provide O(1) memory aggregations.

### Truthound Integration

The dashboard leverages truthound's native probabilistic data structure implementations from `truthound.profiler.sketches`:

| Sketch Type | Truthound Module | Purpose |
|-------------|------------------|---------|
| HyperLogLog | `truthound.profiler.sketches.HyperLogLog` | Cardinality estimation |
| Count-Min Sketch | `truthound.profiler.sketches.CountMinSketch` | Frequency estimation |
| Bloom Filter | `truthound.profiler.sketches.BloomFilter` | Membership testing |

These implementations provide:
- **O(1) Memory**: Constant memory regardless of data size
- **Mergeable**: Results can be combined across distributed partitions
- **Configurable Precision**: Trade-off between accuracy and memory usage

### HyperLogLog

Cardinality estimation (distinct count) with configurable precision. Higher precision yields lower error but uses more memory.

| Precision | Memory | Standard Error |
|-----------|--------|----------------|
| 10 | ~1KB | ±1.04% |
| 12 | ~4KB | ±0.65% |
| 14 (default) | ~16KB | ±0.41% |
| 16 | ~64KB | ±0.26% |
| 18 | ~256KB | ±0.16% |

```json
{
  "sketch_type": "hyperloglog",
  "sketch_config": {
    "hll_precision": 14
  }
}
```

### Count-Min Sketch

Frequency estimation for heavy hitters detection. Width and depth parameters control the trade-off between accuracy and memory.

| Parameter | Effect |
|-----------|--------|
| Width | Larger = fewer collisions, more memory |
| Depth | More = higher confidence, more computation |

```json
{
  "sketch_type": "countmin",
  "sketch_config": {
    "cms_width": 2000,
    "cms_depth": 5
  }
}
```

### Bloom Filter

Probabilistic membership testing with configurable false positive rate. No false negatives - if the filter says an item is not present, it is definitively not present.

```json
{
  "sketch_type": "bloom",
  "sketch_config": {
    "bloom_capacity": 10000000,
    "bloom_error_rate": 0.01
  }
}
```

## API Endpoints

### Run Enterprise Sampling

```http
POST /api/v1/sampling/enterprise
Content-Type: application/json

{
  "source_id": "src_123",
  "target_rows": 100000,
  "quality": "standard",
  "strategy": "adaptive",
  "confidence_level": 0.95,
  "margin_of_error": 0.05,
  "memory_budget": {
    "max_memory_mb": 1024,
    "backpressure_enabled": true
  }
}
```

**Response:**
```json
{
  "source_id": "src_123",
  "job_id": "job_abc123",
  "status": "completed",
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:00:05Z",
  "metrics": {
    "original_rows": 50000000,
    "sampled_rows": 100000,
    "sampling_ratio": 0.002,
    "strategy_used": "block",
    "scale_category": "large",
    "sampling_time_ms": 5234,
    "throughput_rows_per_sec": 9552861,
    "speedup_factor": 500,
    "peak_memory_mb": 256,
    "workers_used": 4,
    "blocks_processed": 100
  }
}
```

### Estimate Sample Size

```http
POST /api/v1/sampling/estimate-size
Content-Type: application/json

{
  "population_size": 100000000,
  "confidence_level": 0.95,
  "margin_of_error": 0.05,
  "quality": "standard"
}
```

**Response:**
```json
{
  "population_size": 100000000,
  "scale_category": "large",
  "recommended_size": 100000,
  "min_size": 50000,
  "max_size": 1000000,
  "estimated_time_seconds": 5.0,
  "estimated_memory_mb": 256,
  "speedup_factor": 1000,
  "recommended_strategy": "block",
  "strategy_rationale": "Block sampling ensures even coverage across the dataset with parallel processing."
}
```

### Run Sketch Estimation

```http
POST /api/v1/sampling/sketch
Content-Type: application/json

{
  "source_id": "src_123",
  "columns": ["user_id", "product_id"],
  "sketch_type": "hyperloglog",
  "sketch_config": {
    "hll_precision": 14
  }
}
```

### List Sampling Jobs

```http
GET /api/v1/sampling/jobs?status_filter=running&limit=10
```

### Get Job Status

```http
GET /api/v1/sampling/jobs/{job_id}
```

### Cancel Job

```http
POST /api/v1/sampling/jobs/{job_id}/cancel
```

### List Strategies

```http
GET /api/v1/sampling/strategies
```

### List Quality Presets

```http
GET /api/v1/sampling/quality-presets
```

### List Scale Categories

```http
GET /api/v1/sampling/scale-categories
```

## Memory Budget Configuration

Control memory usage during sampling operations:

```json
{
  "memory_budget": {
    "max_memory_mb": 1024,
    "reserved_memory_mb": 256,
    "gc_threshold_mb": null,
    "backpressure_enabled": true
  }
}
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| max_memory_mb | 1024 | Maximum memory (128-65536 MB) |
| reserved_memory_mb | 256 | Reserved for system operations |
| gc_threshold_mb | null | GC trigger (default: 75% of max) |
| backpressure_enabled | true | Slow down when memory high |

## Sample Size Formula

Sample size is calculated using Cochran's formula with finite population correction:

```
n₀ = (Z² × p × (1-p)) / e²
n = n₀ / (1 + (n₀ - 1) / N)
```

Where:
- **Z** = Z-score for confidence level (1.96 for 95%)
- **p** = Expected proportion (0.5 for maximum variability)
- **e** = Margin of error (0.05 for 5%)
- **N** = Population size

## UI Components

The Enterprise Sampling configuration UI provides:

1. **Basic Tab**
   - Quality preset selection
   - Target rows configuration
   - Confidence level selection
   - Margin of error slider

2. **Strategy Tab**
   - Strategy selection with recommendations
   - Strategy-specific settings (block size, stages, multipliers)

3. **Advanced Tab**
   - Memory budget configuration
   - Backpressure toggle
   - Random seed for reproducibility

## Best Practices

1. **Start with Adaptive**: Let the system auto-select the best strategy
2. **Use Quality Presets**: Start with Standard, adjust as needed
3. **Enable Backpressure**: Prevents OOM errors on constrained systems
4. **Set Reproducible Seeds**: Use fixed seeds for reproducible results
5. **Monitor Job Progress**: Check job status for long-running operations

## Performance Benchmarks

Typical performance characteristics (varies by hardware):

| Dataset Size | Strategy | Time | Speedup |
|-------------|----------|------|---------|
| 10M rows | Column-Aware | 2s | 50x |
| 100M rows | Block | 5s | 200x |
| 1B rows | Multi-Stage | 15s | 1000x |
| 10B rows | Sketches | 30s | 5000x |

## Related Documentation

- [Drift Monitoring](./drift-monitoring.md) - Uses sampling for large datasets
- [Quality Reporter](./quality-reporter.md) - Quality scoring with sampling
- [Architecture](../architecture.md) - System design overview
