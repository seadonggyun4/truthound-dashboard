"""Business rule validators.

Validators for domain-specific business rules including checksums,
financial identifiers (IBAN, VAT), and credit card validation.

Import path in truthound: `from truthound.validators.business_rule import *`
"""

from .base import (
    ParameterDefinition,
    ParameterType,
    ValidatorCategory,
    ValidatorDefinition,
)

BUSINESS_RULE_VALIDATORS: list[ValidatorDefinition] = [
    ValidatorDefinition(
        name="Checksum",
        display_name="Generic Checksum",
        category=ValidatorCategory.BUSINESS_RULE,
        description="Validates values using a generic checksum algorithm.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
                description="Column containing values to validate",
            ),
            ParameterDefinition(
                name="algorithm",
                label="Checksum Algorithm",
                type=ParameterType.SELECT,
                options=[
                    {"value": "luhn", "label": "Luhn (Mod 10)"},
                    {"value": "mod11", "label": "Modulo 11"},
                    {"value": "verhoeff", "label": "Verhoeff"},
                    {"value": "damm", "label": "Damm"},
                ],
                default="luhn",
                description="Checksum algorithm to use",
            ),
        ],
        tags=["business_rule", "checksum", "validation", "integrity"],
        severity_default="high",
    ),
    ValidatorDefinition(
        name="Luhn",
        display_name="Luhn Algorithm (Mod 10)",
        category=ValidatorCategory.BUSINESS_RULE,
        description="Validates values using the Luhn algorithm (credit cards, IMEI, etc.).",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
                description="Column containing numeric strings to validate",
            ),
        ],
        tags=["business_rule", "luhn", "mod10", "credit_card"],
        severity_default="high",
    ),
    ValidatorDefinition(
        name="ISBN",
        display_name="ISBN Validation",
        category=ValidatorCategory.BUSINESS_RULE,
        description="Validates ISBN-10 or ISBN-13 book identifiers.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
                description="Column containing ISBN values",
            ),
            ParameterDefinition(
                name="format",
                label="ISBN Format",
                type=ParameterType.SELECT,
                options=[
                    {"value": "any", "label": "Any (ISBN-10 or ISBN-13)"},
                    {"value": "isbn10", "label": "ISBN-10 Only"},
                    {"value": "isbn13", "label": "ISBN-13 Only"},
                ],
                default="any",
                description="Expected ISBN format",
            ),
        ],
        tags=["business_rule", "isbn", "book", "identifier"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="CreditCard",
        display_name="Credit Card Number",
        category=ValidatorCategory.BUSINESS_RULE,
        description="Validates credit card numbers using Luhn algorithm and format checks.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
                description="Column containing credit card numbers",
            ),
            ParameterDefinition(
                name="card_type",
                label="Card Type",
                type=ParameterType.MULTI_SELECT,
                options=[
                    {"value": "visa", "label": "Visa"},
                    {"value": "mastercard", "label": "MasterCard"},
                    {"value": "amex", "label": "American Express"},
                    {"value": "discover", "label": "Discover"},
                    {"value": "jcb", "label": "JCB"},
                    {"value": "diners", "label": "Diners Club"},
                ],
                description="Accepted card types (empty = any)",
            ),
        ],
        tags=["business_rule", "credit_card", "payment", "financial"],
        severity_default="critical",
    ),
    ValidatorDefinition(
        name="IBAN",
        display_name="International Bank Account Number",
        category=ValidatorCategory.BUSINESS_RULE,
        description="Validates International Bank Account Numbers (IBAN).",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
                description="Column containing IBAN values",
            ),
            ParameterDefinition(
                name="country_codes",
                label="Allowed Country Codes",
                type=ParameterType.STRING_LIST,
                description="Allowed country codes (e.g., DE, FR, GB). Empty = any.",
                placeholder="DE, FR, GB",
            ),
        ],
        tags=["business_rule", "iban", "bank", "financial"],
        severity_default="high",
    ),
    ValidatorDefinition(
        name="VAT",
        display_name="VAT Number Validation",
        category=ValidatorCategory.BUSINESS_RULE,
        description="Validates Value Added Tax (VAT) identification numbers.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
                description="Column containing VAT numbers",
            ),
            ParameterDefinition(
                name="country",
                label="Country",
                type=ParameterType.SELECT,
                options=[
                    {"value": "auto", "label": "Auto-detect"},
                    {"value": "DE", "label": "Germany"},
                    {"value": "FR", "label": "France"},
                    {"value": "GB", "label": "United Kingdom"},
                    {"value": "IT", "label": "Italy"},
                    {"value": "ES", "label": "Spain"},
                    {"value": "NL", "label": "Netherlands"},
                    {"value": "BE", "label": "Belgium"},
                    {"value": "AT", "label": "Austria"},
                    {"value": "PL", "label": "Poland"},
                ],
                default="auto",
                description="VAT number country format",
            ),
        ],
        tags=["business_rule", "vat", "tax", "eu"],
        severity_default="high",
    ),
    ValidatorDefinition(
        name="SWIFT",
        display_name="SWIFT/BIC Code Validation",
        category=ValidatorCategory.BUSINESS_RULE,
        description="Validates SWIFT/BIC bank identification codes.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
                description="Column containing SWIFT/BIC codes",
            ),
            ParameterDefinition(
                name="format",
                label="Code Format",
                type=ParameterType.SELECT,
                options=[
                    {"value": "any", "label": "Any (8 or 11 characters)"},
                    {"value": "bic8", "label": "BIC8 (8 characters)"},
                    {"value": "bic11", "label": "BIC11 (11 characters)"},
                ],
                default="any",
                description="Expected SWIFT/BIC format",
            ),
        ],
        tags=["business_rule", "swift", "bic", "bank", "financial"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="EAN",
        display_name="EAN/UPC Barcode Validation",
        category=ValidatorCategory.BUSINESS_RULE,
        description="Validates EAN-8, EAN-13, UPC-A, or UPC-E barcodes.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
                description="Column containing barcode values",
            ),
            ParameterDefinition(
                name="format",
                label="Barcode Format",
                type=ParameterType.SELECT,
                options=[
                    {"value": "any", "label": "Any (EAN/UPC)"},
                    {"value": "ean8", "label": "EAN-8"},
                    {"value": "ean13", "label": "EAN-13"},
                    {"value": "upca", "label": "UPC-A"},
                    {"value": "upce", "label": "UPC-E"},
                ],
                default="any",
                description="Expected barcode format",
            ),
        ],
        tags=["business_rule", "ean", "upc", "barcode", "product"],
        severity_default="medium",
    ),
]
