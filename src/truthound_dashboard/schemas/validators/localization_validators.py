"""Localization validators.

Validators for regional identifier formats including Korean, Japanese,
and Chinese specific formats.

Import path in truthound: `from truthound.validators.localization import *`
"""

from .base import (
    ParameterDefinition,
    ParameterType,
    ValidatorCategory,
    ValidatorDefinition,
)

LOCALIZATION_VALIDATORS: list[ValidatorDefinition] = [
    # Korean validators
    ValidatorDefinition(
        name="KoreanBusinessNumber",
        display_name="Korean Business Registration Number",
        category=ValidatorCategory.LOCALIZATION,
        description="Validates Korean business registration numbers (사업자등록번호, 10 digits).",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
                description="Column containing business registration numbers",
            ),
            ParameterDefinition(
                name="allow_hyphen",
                label="Allow Hyphens",
                type=ParameterType.BOOLEAN,
                default=True,
                description="Accept numbers with hyphens (123-45-67890)",
            ),
        ],
        tags=["localization", "korean", "business", "registration"],
        severity_default="high",
    ),
    ValidatorDefinition(
        name="KoreanRRN",
        display_name="Korean Resident Registration Number",
        category=ValidatorCategory.LOCALIZATION,
        description="Validates Korean Resident Registration Numbers (주민등록번호, 13 digits).",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
                description="Column containing RRN values",
            ),
            ParameterDefinition(
                name="masked",
                label="Masked Format",
                type=ParameterType.BOOLEAN,
                default=True,
                description="Accept partially masked numbers (123456-1******)",
            ),
        ],
        tags=["localization", "korean", "rrn", "pii", "identity"],
        severity_default="critical",
    ),
    ValidatorDefinition(
        name="KoreanPhone",
        display_name="Korean Phone Number",
        category=ValidatorCategory.LOCALIZATION,
        description="Validates Korean phone number formats (mobile and landline).",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
                description="Column containing phone numbers",
            ),
            ParameterDefinition(
                name="type",
                label="Phone Type",
                type=ParameterType.SELECT,
                options=[
                    {"value": "any", "label": "Any (Mobile or Landline)"},
                    {"value": "mobile", "label": "Mobile (010/011/016/017/018/019)"},
                    {"value": "landline", "label": "Landline (02/031-064)"},
                ],
                default="any",
                description="Accepted phone number types",
            ),
        ],
        tags=["localization", "korean", "phone", "contact"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="KoreanBankAccount",
        display_name="Korean Bank Account Number",
        category=ValidatorCategory.LOCALIZATION,
        description="Validates Korean bank account number formats by bank.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
                description="Column containing bank account numbers",
            ),
            ParameterDefinition(
                name="bank",
                label="Bank",
                type=ParameterType.SELECT,
                options=[
                    {"value": "any", "label": "Any Bank"},
                    {"value": "kb", "label": "KB Kookmin Bank"},
                    {"value": "shinhan", "label": "Shinhan Bank"},
                    {"value": "woori", "label": "Woori Bank"},
                    {"value": "hana", "label": "Hana Bank"},
                    {"value": "nh", "label": "NH Bank"},
                    {"value": "ibk", "label": "IBK"},
                    {"value": "kakao", "label": "Kakao Bank"},
                    {"value": "toss", "label": "Toss Bank"},
                ],
                default="any",
                description="Bank for format validation",
            ),
        ],
        tags=["localization", "korean", "bank", "financial"],
        severity_default="high",
    ),
    # Japanese validators
    ValidatorDefinition(
        name="JapanesePostalCode",
        display_name="Japanese Postal Code",
        category=ValidatorCategory.LOCALIZATION,
        description="Validates Japanese postal codes (〒xxx-xxxx format).",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
                description="Column containing postal codes",
            ),
            ParameterDefinition(
                name="allow_symbol",
                label="Allow 〒 Symbol",
                type=ParameterType.BOOLEAN,
                default=True,
                description="Accept codes with 〒 prefix",
            ),
        ],
        tags=["localization", "japanese", "postal", "address"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="JapaneseMyNumber",
        display_name="Japanese My Number",
        category=ValidatorCategory.LOCALIZATION,
        description="Validates Japanese Individual Number (マイナンバー, 12 digits).",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
                description="Column containing My Number values",
            ),
        ],
        tags=["localization", "japanese", "mynumber", "pii", "identity"],
        severity_default="critical",
    ),
    ValidatorDefinition(
        name="JapanesePhone",
        display_name="Japanese Phone Number",
        category=ValidatorCategory.LOCALIZATION,
        description="Validates Japanese phone number formats.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
                description="Column containing phone numbers",
            ),
            ParameterDefinition(
                name="type",
                label="Phone Type",
                type=ParameterType.SELECT,
                options=[
                    {"value": "any", "label": "Any"},
                    {"value": "mobile", "label": "Mobile (070/080/090)"},
                    {"value": "landline", "label": "Landline"},
                    {"value": "toll_free", "label": "Toll Free (0120/0800)"},
                ],
                default="any",
                description="Accepted phone number types",
            ),
        ],
        tags=["localization", "japanese", "phone", "contact"],
        severity_default="medium",
    ),
    # Chinese validators
    ValidatorDefinition(
        name="ChineseID",
        display_name="Chinese ID Number",
        category=ValidatorCategory.LOCALIZATION,
        description="Validates Chinese Resident Identity Card numbers (18 digits).",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
                description="Column containing ID numbers",
            ),
            ParameterDefinition(
                name="validate_region",
                label="Validate Region Code",
                type=ParameterType.BOOLEAN,
                default=True,
                description="Validate the 6-digit region code",
            ),
        ],
        tags=["localization", "chinese", "id", "pii", "identity"],
        severity_default="critical",
    ),
    ValidatorDefinition(
        name="ChineseUSCC",
        display_name="Chinese Unified Social Credit Code",
        category=ValidatorCategory.LOCALIZATION,
        description="Validates Chinese USCC (统一社会信用代码, 18 characters).",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
                description="Column containing USCC values",
            ),
        ],
        tags=["localization", "chinese", "uscc", "business", "registration"],
        severity_default="high",
    ),
    ValidatorDefinition(
        name="ChinesePhone",
        display_name="Chinese Phone Number",
        category=ValidatorCategory.LOCALIZATION,
        description="Validates Chinese phone number formats.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
                description="Column containing phone numbers",
            ),
            ParameterDefinition(
                name="type",
                label="Phone Type",
                type=ParameterType.SELECT,
                options=[
                    {"value": "any", "label": "Any"},
                    {"value": "mobile", "label": "Mobile (1xx)"},
                    {"value": "landline", "label": "Landline"},
                ],
                default="any",
                description="Accepted phone number types",
            ),
        ],
        tags=["localization", "chinese", "phone", "contact"],
        severity_default="medium",
    ),
]
