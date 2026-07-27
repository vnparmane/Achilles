from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


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


class PaymentMode(str, Enum):
    CASH = "cash"
    BANK = "bank"
    UPI = "upi"
    CHEQUE = "cheque"
    CARD = "card"


INDIAN_STATES = [
    ("", "-- Select State --"),
    ("AP", "Andhra Pradesh"), ("AR", "Arunachal Pradesh"), ("AS", "Assam"),
    ("BR", "Bihar"), ("CG", "Chhattisgarh"), ("GA", "Goa"),
    ("GJ", "Gujarat"), ("HR", "Haryana"), ("HP", "Himachal Pradesh"),
    ("JK", "Jammu and Kashmir"), ("JH", "Jharkhand"), ("KA", "Karnataka"),
    ("KL", "Kerala"), ("MP", "Madhya Pradesh"), ("MH", "Maharashtra"),
    ("MN", "Manipur"), ("ML", "Meghalaya"), ("MZ", "Mizoram"),
    ("NL", "Nagaland"), ("OD", "Odisha"), ("PB", "Punjab"),
    ("RJ", "Rajasthan"), ("SK", "Sikkim"), ("TN", "Tamil Nadu"),
    ("TS", "Telangana"), ("TR", "Tripura"), ("UP", "Uttar Pradesh"),
    ("UK", "Uttarakhand"), ("WB", "West Bengal"),
    ("AN", "Andaman and Nicobar"), ("CH", "Chandigarh"),
    ("DN", "Dadra and Nagar Haveli"), ("DD", "Daman and Diu"),
    ("DL", "Delhi"), ("LD", "Lakshadweep"), ("PY", "Puducherry"),
]

GST_RATES = [0, 5, 12, 18, 28]

APP_NAME = "TextileERP"
APP_VERSION = "1.0.0"
DB_FILENAME = "textile_erp.db"
