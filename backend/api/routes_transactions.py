from fastapi import APIRouter
from typing import List
from models.transaction import Transaction, IngestTransactionRequest, ExpenseSummary, TransactionSource
from services.transaction_store import tx_store

router = APIRouter(prefix="/api/expenses", tags=["Expenses & Data Ingestion"])

@router.post("/ingest", response_model=Transaction)
async def ingest_transaction(request: IngestTransactionRequest):
    """
    Ingest a real-time transaction event (from Apple Pay, Google Wallet, NFC tap, or Bank Push).
    """
    return tx_store.ingest(request)

@router.get("/summary", response_model=ExpenseSummary)
async def get_expenses_summary():
    """
    Get live expense totals, category breakdown, 50/30/20 percentages, and transaction stream.
    """
    return tx_store.get_summary()

@router.get("/transactions", response_model=List[Transaction])
async def get_all_transactions():
    """
    List all ingested transactions.
    """
    return tx_store.get_all()

@router.post("/simulate", response_model=Transaction)
async def simulate_tap_to_pay(
    merchant: str = "Starbucks Coffee",
    amount: float = 4.20,
    source: TransactionSource = TransactionSource.NFC_TAP
):
    """
    Helper endpoint to simulate an instant NFC purchase for testing/demo purposes.
    """
    req = IngestTransactionRequest(
        raw_merchant=merchant,
        amount=amount,
        currency="EUR",
        source=source,
        account_name="Apple Pay / Revolut"
    )
    return tx_store.ingest(req)
