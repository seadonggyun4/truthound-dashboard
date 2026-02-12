# Privacy and PII Management

The Privacy module implements systematic capabilities for detecting Personally Identifiable Information (PII) within data sources and applying masking strategies to safeguard sensitive data while preserving analytical utility.

## Overview

Privacy management is regarded as a fundamental requirement for achieving regulatory compliance and ensuring comprehensive data protection. This module facilitates PII detection through pattern recognition and classification methodologies, followed by the application of configurable masking strategies through which sensitive data is transformed for safe downstream consumption.

## Privacy Interface Specifications

### Source Selection

The Privacy interface is initiated through a source selection procedure:

1. A data source is selected from the dropdown control
2. PII column count badges are displayed for each source, indicating previously detected sensitive columns
3. Upon selection, source-specific privacy information is rendered within the interface

### Statistics Dashboard

Aggregate privacy metrics are presented through the following statistical indicators:

| Metric | Description |
|--------|-------------|
| **Total Scans** | Count of PII scans executed across all sources |
| **Total PII Findings** | Aggregate count of PII instances detected |
| **Columns Protected** | Count of columns that have been masked |
| **Compliance Score** | Overall compliance assessment percentage |

## PII Scan Tab

### Executing a PII Scan

The following procedure is employed to initiate a PII scan:

1. The target data source is selected
2. The **Run PII Scan** action is invoked
3. Results are reviewed upon completion of the scanning process

> **Note**: It should be observed that truthound's `th.scan()` does not accept configuration parameters.
> The scan is executed automatically across all columns with default settings, whereby
> all supported PII types are detected across all applicable regulatory frameworks.

### Supported Regulatory Frameworks

Compliance is assessed automatically against multiple regulatory frameworks, as enumerated below:

| Regulation | Description | PII Categories |
|------------|-------------|----------------|
| **GDPR** | EU General Data Protection Regulation | Name, email, address, phone, IP, financial, health |
| **CCPA** | California Consumer Privacy Act | Personal identifiers, commercial information, biometric |
| **LGPD** | Brazil's Lei Geral de Protecao de Dados | Similar to GDPR with Brazil-specific requirements |
| **HIPAA** | Health Insurance Portability and Accountability Act | Protected health information (PHI) |

### Scan Results

Upon completion of the scanning process, the following result categories are presented:

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

The data masking procedure is conducted through the following sequential steps:

1. The target data source is selected
2. Columns to be masked are designated (typically those identified during the PII scan)
3. An appropriate masking strategy is chosen
4. The **Run Mask** operation is executed
5. The masked data file is downloaded (CSV format)

> **Note**: It is noted that truthound's `th.mask()` does not support output format selection.
> The output is invariably generated in CSV format.

### Masking Strategy Selection

Three masking strategies are provided, each suited to distinct operational requirements:

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **Redact** | Replace with fixed placeholder (e.g., `[REDACTED]`) | Complete removal of sensitive values |
| **Hash** | Apply cryptographic hash transformation | Referential integrity preservation |
| **Fake** | Replace with realistic synthetic data | Testing and development environments |

#### Strategy Details

**Redact**:
- All values are replaced with a consistent placeholder string
- Original information is completely removed from the output
- This strategy is deemed suitable when original values are not required for downstream processing

**Hash**:
- A SHA-256 hash transformation is applied to each value
- Identical inputs produce identical outputs (deterministic behavior is guaranteed)
- Referential integrity across tables is preserved through consistent hashing
- The original value cannot be recovered from the hash output

**Fake**:
- Synthetic data is generated to match the pattern of the original values
- Statistical properties of the original distribution are maintained
- Realistic but entirely fictional values are produced
- This strategy is considered appropriate for development and testing environments

### Download Masked Data

Upon completion of the masking operation, the following workflow is observed:

1. The masking operation generates an output file
2. A download link is made available to the user
3. The masked dataset is obtained via the download mechanism
4. The original data source remains unmodified throughout the process

## History Tab

### Scan History

Historical PII scan records are maintained and may be reviewed through the following attributes:

| Attribute | Description |
|-----------|-------------|
| **Timestamp** | When the scan was executed |
| **Source** | Data source that was scanned |
| **Findings Count** | Number of PII instances detected |
| **Status** | Scan completion status |

### Mask History

Historical masking operation records are similarly maintained and may be examined:

| Attribute | Description |
|-----------|-------------|
| **Timestamp** | When masking was executed |
| **Source** | Data source that was masked |
| **Columns** | Columns that were masked |
| **Strategy** | Masking strategy applied |

## Compliance Workflow Methodology

### Recommended Process

A systematic compliance workflow is recommended, consisting of the following ordered phases:

1. **Discovery**: PII scans are executed across all relevant data sources
2. **Classification**: PII findings are reviewed and validated by designated personnel
3. **Assessment**: Applicable compliance requirements are evaluated against findings
4. **Protection**: Appropriate masking strategies are applied to identified PII columns
5. **Verification**: Masked data is confirmed to satisfy stated requirements
6. **Documentation**: Compliance reports are generated for audit and record-keeping purposes
7. **Monitoring**: Periodic rescanning is conducted to detect newly introduced PII

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

## Cross-Module Integration Architecture

### Data Catalog Integration

- PII findings may be linked to corresponding catalog asset columns
- Sensitivity levels are updated based on scan results as they become available
- Column metadata is enriched with PII classification information derived from scan outputs

### Notification Integration

- Alerts may be configured for the detection of new PII instances
- Relevant stakeholders are notified when sensitive data is identified
- Compliance reporting workflows may be automated through the notification subsystem

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sources/{id}/scan` | POST | Execute PII scan |
| `/sources/{id}/pii-scans` | GET | List PII scan history |
| `/sources/{id}/mask` | POST | Execute data masking |
| `/sources/{id}/masks` | GET | List masking history |
