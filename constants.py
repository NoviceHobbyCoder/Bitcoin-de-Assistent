from enum import Enum

# API Constants
API_URL = "https://api.bitcoin.de"
API_VERSION = "v4"

class TradingPairs:
    BTCEUR = "btceur"
    BCHEUR = "bcheur"
    ETHEUR = "etheur"
    SOLEUR = "soleur"
    XRPEUR = "xrpeur"
    LTCEUR = "ltceur"
    DOGEEUR = "dogeeur"
    BTGEUR = "btgeur"
    TRXEUR = "trxeur"
    USDCEUR = "usdceur"

    DISPLAY_NAMES = {
        "btceur": "BTC/EUR",
        "bcheur": "BCH/EUR",
        "etheur": "ETH/EUR",
        "soleur": "SOL/EUR",
        "xrpeur": "XRP/EUR",
        "ltceur": "LTC/EUR",
        "dogeeur": "DOGE/EUR",
        "btgeur": "BTG/EUR",
        "trxeur": "TRX/EUR",
        "usdceur":"USDC/EUR"
    }

    @classmethod
    def get_all_pairs(cls):
        return [
            cls.BTCEUR,
            cls.BCHEUR,
            cls.ETHEUR,
            cls.SOLEUR,
            cls.XRPEUR,
            cls.LTCEUR,
            cls.DOGEEUR,
            cls.BTGEUR,
            cls.TRXEUR,
            cls.USDCEUR
        ]

    @classmethod
    def get_all_display_names(cls):
        """Return list of all display names"""
        return list(cls.DISPLAY_NAMES.values())

    @classmethod
    def get_api_name(cls, display_name):
        """Convert display name to API name"""
        for api_name, display in cls.DISPLAY_NAMES.items():
            if display == display_name:
                return api_name
        return None

class TradingConstants:
    # Payment method constants
    TRADE_PAYMENT_METHOD_SEPA = 1
    TRADE_PAYMENT_METHOD_EXPRESS = 2
    TRADE_PAYMENT_METHOD_SEPA_INSTANT = 3

    # Orderbook parameter constants
    ORDERBOOK_PAYMENT_OPTION_EXPRESS_ONLY = 1
    ORDERBOOK_PAYMENT_OPTION_SEPA_ONLY = 2
    ORDERBOOK_PAYMENT_OPTION_EXPRESS_OR_SEPA = 3
    
    # SEPA options
    SEPA_OPTION_NONE = 0
    SEPA_OPTION_ACCELERATED = 1

    # Payment options mapping
    PAYMENT_OPTIONS = {
        ORDERBOOK_PAYMENT_OPTION_EXPRESS_ONLY: "Express-Only",
        ORDERBOOK_PAYMENT_OPTION_SEPA_ONLY: "SEPA-Only",
        ORDERBOOK_PAYMENT_OPTION_EXPRESS_OR_SEPA: "Express & SEPA"
    }

    # SEPA options mapping
    SEPA_OPTIONS = {
        SEPA_OPTION_NONE: "No SEPA option",
        SEPA_OPTION_ACCELERATED: "Accelerated payment"
    }

    # Default validation settings
    DEFAULT_MIN_AMOUNT = '0.000'
    DEFAULT_MAX_AMOUNT = '00.0'
    DEFAULT_MIN_PRICE = '0000.0'
    DEFAULT_MAX_PRICE = '000000.0'

    class TrustLevel(str, Enum):
        BRONZE = 'bronze'
        SILVER = 'silver'
        GOLD = 'gold'
        PLATINUM = 'platinum'

    class BankCountry(str, Enum):
        AUSTRIA = 'AT'
        BELGIUM = 'BE'
        BULGARIA = 'BG'
        SWITZERLAND = 'CH'
        CYPRUS = 'CY'
        CZECH_REPUBLIC = 'CZ'
        GERMANY = 'DE'
        DENMARK = 'DK'
        ESTONIA = 'EE'
        SPAIN = 'ES'
        FINLAND = 'FI'
        FRANCE = 'FR'
        GREAT_BRITAIN = 'GB'
        GREECE = 'GR'
        CROATIA = 'HR'
        HUNGARY = 'HU'
        IRELAND = 'IE'
        ICELAND = 'IS'
        ITALY = 'IT'
        LIECHTENSTEIN = 'LI'
        LITHUANIA = 'LT'
        LUXEMBOURG = 'LU'
        LATVIA = 'LV'
        MALTA = 'MT'
        MARTINIQUE = 'MQ'
        NETHERLANDS = 'NL'
        NORWAY = 'NO'
        POLAND = 'PL'
        PORTUGAL = 'PT'
        ROMANIA = 'RO'
        SWEDEN = 'SE'
        SLOVENIA = 'SI'
        SLOVAKIA = 'SK'

    # Bank country names mapping
    BANK_COUNTRY_NAMES = {
        'AT': 'Austria',
        'BE': 'Belgium',
        'BG': 'Bulgaria',
        'CH': 'Switzerland',
        'CY': 'Cyprus',
        'CZ': 'Czech Republic',
        'DE': 'Germany',
        'DK': 'Denmark',
        'EE': 'Estonia',
        'ES': 'Spain',
        'FI': 'Finland',
        'FR': 'France',
        'GB': 'Great Britain',
        'GR': 'Greece',
        'HR': 'Croatia',
        'HU': 'Hungary',
        'IE': 'Ireland',
        'IS': 'Iceland',
        'IT': 'Italy',
        'LI': 'Liechtenstein',
        'LT': 'Lithuania',
        'LU': 'Luxembourg',
        'LV': 'Latvia',
        'MT': 'Malta',
        'MQ': 'Martinique',
        'NL': 'Netherlands',
        'NO': 'Norway',
        'PL': 'Poland',
        'PT': 'Portugal',
        'RO': 'Romania',
        'SE': 'Sweden',
        'SI': 'Slovenia',
        'SK': 'Slovakia'
    }

class ApiEndpoints:
    """API endpoint constants"""
    BASE_URL = "https://api.bitcoin.de/v4"
    ACCOUNT = "account"
    RATES = "rates"
    ORDERS = "orders/compact"

class CurrencyPrecision:
    """Currency precision settings"""
    PRECISION = {
        'btc': 8,
        'eth': 8,
        'bch': 8,
        'btg': 8,
        'ltc': 8,
        'xrp': 8,
        'doge': 8,
        'trx': 8,
        'usdc': 8,
        'sol': 8,
        'eur': 3
    }
    DEFAULT_PRECISION = 8

class Currency:
    """Currency constants"""
    All_CURRENCIES = [
        'btc', 
        'eth', 
        'bch', 
        'btg', 
        'ltc', 
        'xrp', 
        'doge', 
        'trx', 
        'usdc', 
        'sol'  
    ]

class CurrencyUpper:
    """Currency constants"""
    All_CURRENCIES = [
        'BTC', 
        'ETH', 
        'BCH', 
        'BTG', 
        'LTC', 
        'XRP', 
        'DOGE', 
        'TRX', 
        'USDC', 
        'SOL'  
    ]