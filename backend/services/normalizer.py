import re
from typing import Dict, Any, Tuple
from models.transaction import BudgetBucket

MERCHANT_RULES = [
    # Transfers & Income (P2P / Salary)
    (r"(transfer to|sent to|p2p|revolut transfer|wire to)", "P2P Money Transfer", "Transfers", "💸", BudgetBucket.TRANSFERS, True),
    (r"(salary|payroll|income|deposit|employer)", "Monthly Salary Deposit", "Income", "💰", BudgetBucket.TRANSFERS, True),

    # Supermarkets & Groceries (Needs)
    (r"(spar|interspar|despar)", "SPAR", "Groceries", "🛒", BudgetBucket.NEEDS, True),
    (r"(tesco|tesco express)", "Tesco", "Groceries", "🛒", BudgetBucket.NEEDS, True),
    (r"(lidl)", "Lidl", "Groceries", "🛒", BudgetBucket.NEEDS, True),
    (r"(aldi)", "Aldi", "Groceries", "🛒", BudgetBucket.NEEDS, True),
    (r"(auchan)", "Auchan", "Groceries", "🛒", BudgetBucket.NEEDS, True),
    
    # Dining, Cafes & Online Delivery (Wants)
    (r"(starbucks)", "Starbucks", "Coffee & Cafes", "☕", BudgetBucket.WANTS, False),
    (r"(costa coffee|costa)", "Costa Coffee", "Coffee & Cafes", "☕", BudgetBucket.WANTS, False),
    (r"(mcdonalds|mcdonald|mc donald)", "McDonald's", "Fast Food", "🍔", BudgetBucket.WANTS, False),
    (r"(wolt|foodora|uber eats|deliveroo)", "Food Delivery", "Food Delivery", "🛵", BudgetBucket.WANTS, False),
    (r"(restaurant|bistro|trattoria|pizzeria|pub|bar)", "Restaurant & Dining", "Dining Out", "🍽️", BudgetBucket.WANTS, False),

    # Online Purchases & E-Commerce (Wants)
    (r"(amazon|amzn)", "Amazon Online", "Online Shopping", "📦", BudgetBucket.WANTS, False),
    (r"(asos|shein|zalando|aliexpress)", "Online Fashion", "Online Shopping", "🛍️", BudgetBucket.WANTS, False),
    (r"(zara|h&m|uniqlo|mango|bershka)", "Clothing & Apparel", "Shopping", "👗", BudgetBucket.WANTS, False),

    # Transportation & Transit (Needs)
    (r"(bkk|budapest transport|metro|transit)", "BKK Public Transit", "Transportation", "🚇", BudgetBucket.NEEDS, True),
    (r"(uber|bolt|freenow|taxi)", "Bolt / Taxi", "Transportation", "🚕", BudgetBucket.WANTS, False),
    (r"(shell|mol|omv|bp gas|petrol|fuel)", "Fuel & Petrol", "Transportation", "⛽", BudgetBucket.NEEDS, True),

    # Subscriptions & Entertainment (Wants)
    (r"(netflix)", "Netflix", "Subscriptions", "🎬", BudgetBucket.WANTS, False),
    (r"(spotify)", "Spotify", "Subscriptions", "🎵", BudgetBucket.WANTS, False),
    (r"(apple\.com|apple services|itunes|app store)", "Apple Services", "Subscriptions", "🍎", BudgetBucket.WANTS, False),
    (r"(google\*|google play|youtube)", "Google Services", "Subscriptions", "▶️", BudgetBucket.WANTS, False),

    # Utilities & Telecom (Needs)
    (r"(vodafone|t-mobile|telekom|yettel|orange)", "Telecom & Internet", "Utilities", "📶", BudgetBucket.NEEDS, True),
    (r"(electric|water|gas utility|power)", "Household Utilities", "Utilities", "💡", BudgetBucket.NEEDS, True),
    (r"(pharmacy|apotheke|gyogyszertar|cvs|walgreens)", "Pharmacy & Health", "Health", "💊", BudgetBucket.NEEDS, True),
]

class TransactionNormalizer:
    @staticmethod
    def normalize(raw_merchant: str) -> Dict[str, Any]:
        clean_text = raw_merchant.strip()
        lower_text = clean_text.lower()

        for pattern, clean_name, category, icon, bucket, is_essential in MERCHANT_RULES:
            if re.search(pattern, lower_text):
                return {
                    "clean_merchant": clean_name,
                    "category": category,
                    "icon": icon,
                    "bucket": bucket,
                    "is_essential": is_essential
                }

        sanitized = re.sub(r"^(pos|pp\*|bbp\*|v\*|sq\*)\s*(\d+)?\s*", "", clean_text, flags=re.IGNORECASE).strip()
        if not sanitized:
            sanitized = "Card Purchase"

        return {
            "clean_merchant": sanitized.title(),
            "category": "General Spending",
            "icon": "💳",
            "bucket": BudgetBucket.WANTS,
            "is_essential": False
        }

normalizer = TransactionNormalizer()
