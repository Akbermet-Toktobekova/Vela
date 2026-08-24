from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime

class TransactionSource(str, Enum):
    NFC_TAP = "nfc_tap"
    APPLE_PAY = "apple_pay"
    GOOGLE_WALLET = "google_wallet"
    OPEN_BANKING = "open_banking"
    MANUAL = "manual"

class BudgetBucket(str, Enum):
    NEEDS = "needs"       # 50% Essential living
    WANTS = "wants"       # 30% Discretionary
    SAVINGS = "savings"   # 20% Financial goals / Debt principal
    TRANSFERS = "transfers" # P2P Transfers / Inflows

class IngestTransactionRequest(BaseModel):
    raw_merchant: str
    amount: float
    currency: str = "EUR"
    source: TransactionSource = TransactionSource.NFC_TAP
    account_name: str = "Main Card"
    timestamp: Optional[str] = None

class Transaction(BaseModel):
    id: str
    amount: float
    currency: str = "EUR"
    raw_merchant: str
    clean_merchant: str
    category: str
    icon: str
    bucket: BudgetBucket
    is_essential: bool
    source: TransactionSource
    account_name: str
    timestamp: str

class CategorySpend(BaseModel):
    category: str
    amount: float
    percentage: float
    icon: str
    bucket: BudgetBucket

class ExpenseSummary(BaseModel):
    total_spent: float
    currency: str = "EUR"
    needs_total: float
    wants_total: float
    savings_total: float
    needs_percentage: float
    wants_percentage: float
    savings_percentage: float
    category_breakdown: List[CategorySpend]
    recent_transactions: List[Transaction]
