from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class PartyType(str, Enum):
    CUSTOMER = "customer"
    VENDOR = "vendor"
    BOTH = "both"


class RegistrationType(str, Enum):
    REGULAR = "regular"
    COMPOSITION = "composition"
    UNREGISTERED = "unregistered"


class ItemUnit(str, Enum):
    METER = "meter"
    KG = "kg"
    ROLL = "roll"
    BALE = "bale"
    CONE = "cone"
    BOX = "box"
    PIECE = "piece"
    DOZEN = "dozen"
    BAG = "bag"
    LITER = "liter"
    SQUARE_METER = "sq_meter"
    NUMBER = "number"


class StockTransactionType(str, Enum):
    PURCHASE = "purchase"
    SALES = "sales"
    ADJUSTMENT_PLUS = "adjustment_plus"
    ADJUSTMENT_MINUS = "adjustment_minus"


class PaymentMode(str, Enum):
    CASH = "cash"
    BANK = "bank"
    UPI = "upi"
    CHEQUE = "cheque"
    CARD = "card"


class BillStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


GST_RATES = [0, 5, 12, 18, 28]

APP_NAME = "TextileERP"
APP_VERSION = "1.0.0"
DB_FILENAME = "textile_erp.db"
