import re

# Strips the rail/channel prefix that Indian bank statements prepend to every
# line (UPI, POS, NEFT, IMPS, ...), plus trailing reference numbers, so
# "UPI-SWIGGY-swiggy@ybl-123456789012" becomes "SWIGGY".
_PREFIX_RE = re.compile(
    r"^(UPI|POS|NEFT|IMPS|RTGS|ACH|ECS|NACH|ATW|ATM|CHQ|BIL|MMT|CARD)[\s/\-:]*",
    re.IGNORECASE,
)
_TRAILING_REF_RE = re.compile(r"[\s/\-]*\d{6,}[\s/\-]*$")
_UPI_HANDLE_RE = re.compile(r"^[\w.]+@[\w.]+$")
_MULTI_SPACE_RE = re.compile(r"\s+")
_SEPARATOR_RE = re.compile(r"[/\-:]+")

# Segments that carry no merchant identity — UPI transaction-type codes
# ("UPI/P2M/<ref>/Merchant/remarks/Bank Name" is a very common Indian bank
# layout), pure reference numbers, and the counterparty's bank name.
_UPI_TYPE_CODE_RE = re.compile(r"^P2[MAPC]$", re.IGNORECASE)
_PURE_DIGITS_RE = re.compile(r"^\d{6,}$")
_BANK_NAME_RE = re.compile(r"\bbank\b", re.IGNORECASE)
_INTEREST_RE = re.compile(r"\bint\.?\s*p(?:ai)?d\b", re.IGNORECASE)

TRANSFER_KEYWORDS = (
    "self transfer",
    "own account",
    "fund transfer to self",
    "a/c transfer",
)

_SUBSCRIPTION_HINTS = {
    "netflix", "spotify", "amazon prime", "prime video", "youtube premium",
    "hotstar", "disney", "adobe", "icloud", "google one", "apple music",
}


def _is_junk_segment(segment: str) -> bool:
    return bool(
        _UPI_TYPE_CODE_RE.match(segment)
        or _PURE_DIGITS_RE.match(segment)
        or _BANK_NAME_RE.search(segment)
        or _UPI_HANDLE_RE.match(segment)
    )


def clean_merchant(raw_description: str) -> str:
    if _INTEREST_RE.search(raw_description):
        return "Interest"

    text = raw_description.strip()
    text = _PREFIX_RE.sub("", text)
    text = _TRAILING_REF_RE.sub("", text)

    parts = [p.strip() for p in _SEPARATOR_RE.split(text) if p.strip()]
    candidates = [p for p in parts if not _is_junk_segment(p)]

    # Prefer the longest surviving segment — the merchant/payee name is
    # usually the most substantive one; short leftovers tend to be wrap
    # artifacts ("Paid v", "paymen" cut off mid-word by the source PDF).
    candidate = max(candidates, key=len) if candidates else (parts[0] if parts else text)

    candidate = _MULTI_SPACE_RE.sub(" ", candidate).strip()
    return candidate.title() if candidate else raw_description.strip()[:255]


def looks_like_transfer(raw_description: str) -> bool:
    lower = raw_description.lower()
    return any(keyword in lower for keyword in TRANSFER_KEYWORDS)


def looks_like_subscription(merchant: str) -> bool:
    lower = merchant.lower()
    return any(hint in lower for hint in _SUBSCRIPTION_HINTS)
