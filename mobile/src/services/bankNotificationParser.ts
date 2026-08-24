export interface ParsedBankNotification {
  isTransaction: boolean;
  merchant: string;
  amount: number;
  currency: string;
  category: 'needs' | 'wants' | 'savings';
}

/**
 * Intelligent regex parser for Bank Push notifications & SMS
 * Supports: Revolut, OTP Bank, MBank, Optima, Kaspi, Halyk, Erste, Wise, Apple Pay, Google Pay
 */
export function parseBankNotification(title: string, text: string): ParsedBankNotification | null {
  const fullText = `${title || ''} ${text || ''}`.trim();
  if (!fullText) return null;

  // 1. Check if it's a payment / debit transaction
  const isDebit = /(spent|paid|purchase|payment|оплата|списание|покупка|vasarlas|fizetes|transzfer|kartyas fizetes)/i.test(fullText);
  if (!isDebit && !/(spar|starbucks|lidl|aldi|mcdonald|uber|bolt|amazon|tesco|auchan|dm|rossmann)/i.test(fullText)) {
    return null;
  }

  // 2. Extract amount and currency
  // Examples: "€14.50", "14.50 EUR", "450 KGS", "3,200 Ft", "3200 HUF", "$25.00"
  let amount = 0;
  let currency = 'EUR';

  const eurMatch = fullText.match(/(?:€\s*(\d+[.,]?\d*)|(\d+[.,]?\d*)\s*(?:eur|евро))/i);
  const hufMatch = fullText.match(/(?:(\d+[\s.,]?\d*)\s*(?:ft|huf|forint))/i);
  const kgsMatch = fullText.match(/(?:(\d+[\s.,]?\d*)\s*(?:kgs|сом|c))/i);
  const usdMatch = fullText.match(/(?:\$\s*(\d+[.,]?\d*)|(\d+[.,]?\d*)\s*usd)/i);

  if (eurMatch) {
    const rawNum = (eurMatch[1] || eurMatch[2]).replace(',', '.');
    amount = parseFloat(rawNum);
    currency = 'EUR';
  } else if (hufMatch) {
    const rawNum = hufMatch[1].replace(/[\s.,]/g, '');
    amount = parseFloat(rawNum);
    currency = 'HUF';
  } else if (kgsMatch) {
    const rawNum = kgsMatch[1].replace(/[\s.,]/g, '');
    amount = parseFloat(rawNum);
    currency = 'KGS';
  } else if (usdMatch) {
    const rawNum = (usdMatch[1] || usdMatch[2]).replace(',', '.');
    amount = parseFloat(rawNum);
    currency = 'USD';
  } else {
    // Generic fallback number match
    const genericMatch = fullText.match(/(\d+[.,]\d{2})/);
    if (genericMatch) {
      amount = parseFloat(genericMatch[1].replace(',', '.'));
    }
  }

  if (amount <= 0 || isNaN(amount)) return null;

  // 3. Extract Merchant name
  let merchant = 'Bank Payment';
  const atMatch = fullText.match(/(?:at|в|от|helyszin:)\s+([A-Za-z0-9\s._'-]{3,25})/i);
  if (atMatch && atMatch[1]) {
    merchant = atMatch[1].trim();
  } else {
    // Check known brands
    const knownMerchants = ['SPAR', 'Lidl', 'Aldi', 'Tesco', 'Starbucks', 'McDonald', 'Uber', 'Bolt', 'Amazon', 'DM', 'Rossmann', 'Auchan', 'KFC', 'Burger King', 'BKK'];
    for (const m of knownMerchants) {
      if (new RegExp(m, 'i').test(fullText)) {
        merchant = m;
        break;
      }
    }
  }

  // 4. Determine 50/30/20 category
  let category: 'needs' | 'wants' | 'savings' = 'wants';
  const needsKeywords = /(spar|lidl|aldi|tesco|auchan|groceries|supermarket|продукты|bkk|metro|transport|rent|pharmacy|аптека|dm|rossmann|gyogyszertar)/i;
  const savingsKeywords = /(vault|savings|deposit|накопления|вклад|invest|revolut vault)/i;

  if (savingsKeywords.test(fullText) || savingsKeywords.test(merchant)) {
    category = 'savings';
  } else if (needsKeywords.test(fullText) || needsKeywords.test(merchant)) {
    category = 'needs';
  }

  return {
    isTransaction: true,
    merchant,
    amount,
    currency,
    category,
  };
}
