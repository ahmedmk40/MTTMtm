"""
Constants for Transaction Monitoring and Fraud Detection System.
"""

# Transaction Types
TRANSACTION_TYPE_ACQUIRING = 'acquiring'
TRANSACTION_TYPE_WALLET = 'wallet'

# Transaction Channels
CHANNEL_POS = 'pos'
CHANNEL_ECOMMERCE = 'ecommerce'
CHANNEL_WALLET = 'wallet'

# Payment Method Types
PAYMENT_METHOD_CREDIT_CARD = 'credit_card'
PAYMENT_METHOD_DEBIT_CARD = 'debit_card'
PAYMENT_METHOD_WALLET = 'wallet'
PAYMENT_METHOD_BANK_TRANSFER = 'bank_transfer'

# Card Entry Modes
ENTRY_MODE_CHIP = 'chip'
ENTRY_MODE_SWIPE = 'swipe'
ENTRY_MODE_CONTACTLESS = 'contactless'
ENTRY_MODE_MANUAL = 'manual'
ENTRY_MODE_ONLINE = 'online'

# Response Codes
RESPONSE_APPROVED = 'approved'
RESPONSE_DECLINED = 'declined'
RESPONSE_ERROR = 'error'
RESPONSE_TIMEOUT = 'timeout'
RESPONSE_FLAGGED = 'flagged'

# Risk Levels
RISK_LEVEL_LOW = 'low'
RISK_LEVEL_MEDIUM = 'medium'
RISK_LEVEL_HIGH = 'high'
RISK_LEVEL_CRITICAL = 'critical'

# Rule Types
RULE_TYPE_VELOCITY = 'velocity'
RULE_TYPE_AMOUNT = 'amount'
RULE_TYPE_LOCATION = 'location'
RULE_TYPE_CARD = 'card'
RULE_TYPE_DEVICE = 'device'
RULE_TYPE_BEHAVIORAL = 'behavioral'
RULE_TYPE_AML = 'aml'
RULE_TYPE_CUSTOM = 'custom'

# Rule Actions
RULE_ACTION_APPROVE = 'approve'
RULE_ACTION_DECLINE = 'decline'
RULE_ACTION_FLAG = 'flag'
RULE_ACTION_NOTIFY = 'notify'
RULE_ACTION_STEP_UP = 'step_up'

# High-Risk Countries (ISO 3166-1 alpha-2 codes)
HIGH_RISK_COUNTRIES = [
    'AF',  # Afghanistan
    'BY',  # Belarus
    'BI',  # Burundi
    'CF',  # Central African Republic
    'CD',  # Democratic Republic of the Congo
    'IR',  # Iran
    'IQ',  # Iraq
    'LY',  # Libya
    'ML',  # Mali
    'MM',  # Myanmar
    'KP',  # North Korea
    'SO',  # Somalia
    'SS',  # South Sudan
    'SD',  # Sudan
    'SY',  # Syria
    'VE',  # Venezuela
    'YE',  # Yemen
    'ZW',  # Zimbabwe
]

# Suspicious Merchant Category Codes (MCC)
SUSPICIOUS_MCCS = [
    '7995',  # Gambling
    '5933',  # Pawn Shops
    '5944',  # Jewelry, Watches, Clocks, and Silverware Stores
    '6211',  # Securities Brokers/Dealers
    '4829',  # Wire Transfer Money Orders
    '6051',  # Non-Financial Institutions – Foreign Currency, Money Orders, Travelers' Checks
]

# Time Windows for Velocity Checks (in seconds)
TIME_WINDOW_5_MIN = 300
TIME_WINDOW_15_MIN = 900
TIME_WINDOW_1_HOUR = 3600
TIME_WINDOW_6_HOURS = 21600
TIME_WINDOW_24_HOURS = 86400
TIME_WINDOW_7_DAYS = 604800
TIME_WINDOW_30_DAYS = 2592000

# Default Thresholds
DEFAULT_VELOCITY_THRESHOLD = 5
DEFAULT_AMOUNT_THRESHOLD = 1000.00
DEFAULT_DISTANCE_THRESHOLD_KM = 500
DEFAULT_TIME_THRESHOLD_HOURS = 24