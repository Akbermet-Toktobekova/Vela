import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
from models.transaction import Transaction, IngestTransactionRequest, ExpenseSummary, CategorySpend, TransactionSource, BudgetBucket
from services.normalizer import normalizer

INITIAL_TRANSACTIONS: List[Transaction] = [
    Transaction(
        id="tx_01",
        amount=38.50,
        currency="EUR",
        raw_merchant="POS 0923 SPAR CORVIN BUDAPEST HU",
        clean_merchant="SPAR",
        category="Groceries",
        icon="🛒",
        bucket=BudgetBucket.NEEDS,
        is_essential=True,
        source=TransactionSource.APPLE_PAY,
        account_name="Revolut Standard",
        timestamp="Today, 14:23"
    ),
    Transaction(
        id="tx_02",
        amount=4.80,
        currency="EUR",
        raw_merchant="STARBUCKS #1024 DEAK FERENC",
        clean_merchant="Starbucks",
        category="Coffee & Cafes",
        icon="☕",
        bucket=BudgetBucket.WANTS,
        is_essential=False,
        source=TransactionSource.NFC_TAP,
        account_name="OTP Master Card",
        timestamp="Today, 11:15"
    ),
    Transaction(
        id="tx_03",
        amount=14.99,
        currency="EUR",
        raw_merchant="NETFLIX.COM PAYMENT AMSTERDAM",
        clean_merchant="Netflix",
        category="Subscriptions",
        icon="🎬",
        bucket=BudgetBucket.WANTS,
        is_essential=False,
        source=TransactionSource.OPEN_BANKING,
        account_name="OTP Master Card",
        timestamp="Yesterday, 09:00"
    ),
    Transaction(
        id="tx_04",
        amount=9.50,
        currency="EUR",
        raw_merchant="BKK BUDAPEST MOBILJEGY",
        clean_merchant="BKK Public Transit",
        category="Transportation",
        icon="🚇",
        bucket=BudgetBucket.NEEDS,
        is_essential=True,
        source=TransactionSource.GOOGLE_WALLET,
        account_name="Wise Account",
        timestamp="Yesterday, 18:40"
    ),
    Transaction(
        id="tx_05",
        amount=54.20,
        currency="EUR",
        raw_merchant="ZARA FASHION VACI UTCA",
        clean_merchant="Clothing & Apparel",
        category="Shopping",
        icon="👗",
        bucket=BudgetBucket.WANTS,
        is_essential=False,
        source=TransactionSource.APPLE_PAY,
        account_name="Revolut Standard",
        timestamp="2 days ago"
    ),
    Transaction(
        id="tx_06",
        amount=62.00,
        currency="EUR",
        raw_merchant="LIDL HU BP 042 CORVIN",
        clean_merchant="Lidl",
        category="Groceries",
        icon="🛒",
        bucket=BudgetBucket.NEEDS,
        is_essential=True,
        source=TransactionSource.NFC_TAP,
        account_name="OTP Master Card",
        timestamp="3 days ago"
    ),
]

class TransactionStore:
    def __init__(self):
        self.transactions: List[Transaction] = list(INITIAL_TRANSACTIONS)

    def ingest(self, req: IngestTransactionRequest) -> Transaction:
        enriched = normalizer.normalize(req.raw_merchant)
        
        now_str = datetime.now(timezone.utc).strftime("%H:%M")
        timestamp_label = f"Just now, {now_str}" if not req.timestamp else req.timestamp

        tx = Transaction(
            id=f"tx_{uuid.uuid4().hex[:8]}",
            amount=req.amount,
            currency=req.currency,
            raw_merchant=req.raw_merchant,
            clean_merchant=enriched["clean_merchant"],
            category=enriched["category"],
            icon=enriched["icon"],
            bucket=enriched["bucket"],
            is_essential=enriched["is_essential"],
            source=req.source,
            account_name=req.account_name,
            timestamp=timestamp_label
        )
        
        # Insert at top of list
        self.transactions.insert(0, tx)
        return tx

    def get_all(self) -> List[Transaction]:
        return self.transactions

    def get_summary(self) -> ExpenseSummary:
        total_spent = sum(t.amount for t in self.transactions)
        needs_total = sum(t.amount for t in self.transactions if t.bucket == BudgetBucket.NEEDS)
        wants_total = sum(t.amount for t in self.transactions if t.bucket == BudgetBucket.WANTS)
        savings_total = sum(t.amount for t in self.transactions if t.bucket == BudgetBucket.SAVINGS)

        needs_pct = (needs_total / total_spent * 100) if total_spent > 0 else 0
        wants_pct = (wants_total / total_spent * 100) if total_spent > 0 else 0
        savings_pct = (savings_total / total_spent * 100) if total_spent > 0 else 0

        # Group by category
        cat_map: Dict[str, Dict[str, Any]] = {}
        for t in self.transactions:
            if t.category not in cat_map:
                cat_map[t.category] = {
                    "amount": 0.0,
                    "icon": t.icon,
                    "bucket": t.bucket
                }
            cat_map[t.category]["amount"] += t.amount

        category_breakdown = [
            CategorySpend(
                category=cat,
                amount=round(info["amount"], 2),
                percentage=round((info["amount"] / total_spent * 100) if total_spent > 0 else 0, 1),
                icon=info["icon"],
                bucket=info["bucket"]
            )
            for cat, info in sorted(cat_map.items(), key=lambda item: item[1]["amount"], reverse=True)
        ]

        return ExpenseSummary(
            total_spent=round(total_spent, 2),
            currency="EUR",
            needs_total=round(needs_total, 2),
            wants_total=round(wants_total, 2),
            savings_total=round(savings_total, 2),
            needs_percentage=round(needs_pct, 1),
            wants_percentage=round(wants_pct, 1),
            savings_percentage=round(savings_pct, 1),
            category_breakdown=category_breakdown,
            recent_transactions=self.transactions[:15]
        )

tx_store = TransactionStore()
