# Privacy & PII Management

The Privacy module provides capabilities for detecting Personally Identifiable Information (PII) within data sources and applying masking strategies to protect sensitive data while maintaining analytical utility.

## Overview

Privacy management is essential for regulatory compliance and data protection. This module implements PII detection through pattern recognition and classification, followed by configurable masking strategies that transform sensitive data for safe downstream use.

## Privacy Interface

### Source Selection

The Privacy interface begins with source selection:

1. Select a data source from the dropdown
2. Sources display PII column count badges indicating previously detected sensitive columns
3. Upon selection, the interface displays source-specific privacy information

### Statistics Dashboard

The interface displays aggregate privacy metrics:

| Metric | Description |
|--------|-------------|
| **Total Scans** | Count of PII scans executed across all sources |
| **Total PII Findings** | Aggregate count of PII instances detected |
| **Columns Protected** | Count of columns that have been masked |
| **Compliance Score** | Overall compliance assessment percentage |

## PII Scan Tab

### Executing a PII Scan

1. Select the target data source
2. Configure scan parameters:
   - **Regulations**: Compliance frameworks to check against
   - **Minimum Confidence**: Threshold for PII classification confidence
3. Click **Run PII Scan**
4. Review results upon completion

### Regulation Selection

The system supports multiple regulatory frameworks:

| Regulation | Description | PII Categories |
|------------|-------------|----------------|
| **GDPR** | EU General Data Protection Regulation | Name, email, address, phone, IP, financial, health |
| **CCPA** | California Consumer Privacy Act | Personal identifiers, commercial information, biometric |
| **LGPD** | Brazil's Lei Geral de Proteção de Dados | Similar to GDPR with Brazil-specific requirements |
| **HIPAA** | Health Insurance Portability and Accountability Act | Protected health information (PHI) |

### Confidence Threshold

Configure the minimum confidence level for PII classification:

| Threshold | Description |
|-----------|-------------|
| **High (0.9+)** | Only high-confidence detections reported |
| **Medium (0.7-0.9)** | Balanced precision and recall |
| **Low (0.5-0.7)** | Broader detection with potential false positives |

### Scan Results

Upon completion, scan results display:

#### Column-Level Findings

| Attribute | Description |
|-----------|-------------|
| **Column Name** | The column containing PII |
| **PII Type** | Classification of detected PII (email, phone, SSN, etc.) |
| **Confidence** | Detection confidence score (0-1) |
| **Sample Matches** | Example values that triggered detection |
| **Regulations** | Applicable regulatory frameworks |

#### PII Type Classifications

| PII Type | Description | Examples |
|----------|-------------|----------|
| **Email** | Email addresses | john.doe@example.com |
| **Phone** | Phone numbers | +1-555-123-4567 |
| **SSN** | Social Security Numbers | 123-45-6789 |
| **Credit Card** | Payment card numbers | 4111-1111-1111-1111 |
| **Name** | Personal names | John Doe |
| **Address** | Physical addresses | 123 Main St, City, ST 12345 |
| **IP Address** | IP addresses | 192.168.1.1 |
| **Date of Birth** | Birth dates | 1990-01-15 |

## Data Mask Tab

### Executing Data Masking

1. Select the target data source
2. Select columns to mask (typically columns identified in PII scan)
3. Choose masking strategy
4. Select output format
5. Click **Run Mask**
6. Download masked data file

### Masking Strategy Selection

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **Redact** | Replace with fixed placeholder (e.g., `[REDACTED]`) | Complete removal of sensitive values |
| **Hash** | Apply cryptographic hash transformation | Referential integrity preservation |
| **Fake** | Replace with realistic synthetic data | Testing and development environments |

#### Strategy Details

**Redact**:
- Replaces all values with a consistent placeholder
- Completely removes original information
- Suitable when original values are not needed

**Hash**:
- Applies SHA-256 hash transformation
- Same input produces same output (deterministic)
- Preserves referential integrity across tables
- Original value cannot be recovered

**Fake**:
- Generates synthetic data matching original pattern
- Maintains statistical properties
- Produces realistic-looking but fictional values
- Suitable for development and testing

### Output Format Selection

| Format | Description | Use Case |
|--------|-------------|----------|
| **CSV** | Comma-separated values | Universal compatibility |
| **Parquet** | Columnar storage format | Big data processing |
| **JSON** | JavaScript Object Notation | API integration |
| **Excel** | Microsoft Excel format | Business user consumption |

### Download Masked Data

Upon completion:

1. Masking operation generates output file
2. Download link becomes available
3. Click to download masked dataset
4. Original data remains unchanged

## History Tab

### Scan History

View historical PII scans:

| Attribute | Description |
|-----------|-------------|
| **Timestamp** | When the scan was executed |
| **Source** | Data source that was scanned |
| **Regulations** | Compliance frameworks checked |
| **Findings Count** | Number of PII instances detected |
| **Status** | Scan completion status |

### Mask History

View historical masking operations:

| Attribute | Description |
|-----------|-------------|
| **Timestamp** | When masking was executed |
| **Source** | Data source that was masked |
| **Columns** | Columns that were masked |
| **Strategy** | Masking strategy applied |
| **Output Format** | Format of generated file |

## Compliance Workflow

### Recommended Process

1. **Discovery**: Execute PII scan across data sources
2. **Classification**: Review and validate PII findings
3. **Assessment**: Evaluate compliance requirements
4. **Protection**: Apply appropriate masking strategies
5. **Verification**: Confirm masked data meets requirements
6. **Documentation**: Generate compliance reports
7. **Monitoring**: Periodic rescanning for new PII

### Regulatory Mapping

#### GDPR Compliance

| GDPR Requirement | Feature Support |
|-----------------|-----------------|
| Data minimization | PII detection and masking |
| Purpose limitation | Column-level access control |
| Accuracy | Data profiling validation |
| Storage limitation | Retention policies |

#### CCPA Compliance

| CCPA Requirement | Feature Support |
|-----------------|-----------------|
| Know what personal info is collected | PII scanning |
| Delete personal info | Data masking/redaction |
| Opt-out of sale | Data masking for shared data |

## Integration with Other Modules

### Data Catalog Integration

- PII findings can be linked to catalog asset columns
- Sensitivity levels can be updated based on scan results
- Column metadata enriched with PII classification

### Notification Integration

- Configure alerts for new PII detection
- Notify stakeholders when sensitive data is found
- Automate compliance reporting workflows

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sources/{id}/scan` | POST | Execute PII scan |
| `/sources/{id}/pii-scans` | GET | List PII scan history |
| `/sources/{id}/mask` | POST | Execute data masking |
| `/sources/{id}/masks` | GET | List masking history |
