
import re
from decimal import Decimal, InvalidOperation

# Regex uniquement pour : "Vous avez recu X USD ... Ref: XXXXX"
SMS_REGEX = re.compile(
    r"vous avez re[çc]u\s+([\d\.,]+)\s*USD.*?Ref[:\s]+([A-Z0-9\.]+)",
    flags=re.IGNORECASE | re.DOTALL
)

def parse_payment_sms(sms_text: str):
    """
    Retourne (amount_decimal, reference) ou (None, None) si non trouvé.
    """
    m = SMS_REGEX.search(sms_text or "")
    if not m:
        return None, None

    raw_amount = m.group(1).strip()
    reference = m.group(2).strip()

    # Normaliser le montant
    normalized = raw_amount.replace(",", ".")
    
    try:
        amount = Decimal(normalized)
    except InvalidOperation:
        return None, None

    return amount, reference