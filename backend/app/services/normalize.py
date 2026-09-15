import re

# Strips the rail/channel prefix that Indian bank statements prepend to every
# line (UPI, POS, NEFT, IMPS, ...), plus trailing reference numbers, so
# "UPI-SWIGGY-swiggy@ybl-123456789012" becomes "SWIGGY".
_PREFIX_RE = re.compile(
    r"^(UPI|POS|NEFT|IMPS|RTGS|ACH|ECS|NACH|ATW|ATM|CHQ|BIL|MMT|CARD)[\s/\-:]*",
    re.IGNORECASE,
)
_TRAILING_REF_RE = re.compile(r"[\s/\-]*\d{6,}[\s/\-]*$")
_UPI_HANDLE_RE = re.compile(r"[\w.]+@[\w.]+")
_MULTI_SPACE_RE = re.compile(r"\s+")
_SEPARATOR_RE = re.compile(r"[/\-:]+")

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


def clean_merchant(raw_description: str) -> str:
    text = raw_description.strip()
    text = _PREFIX_RE.sub("", text)
    text = _TRAILING_REF_RE.sub("", text)
    text = _UPI_HANDLE_RE.sub("", text)

    # Take the first meaningful token when the rail encodes it as
    # "MERCHANT-payee_handle-reference" — the merchant name is usually the
    # first segment.
    parts = [p.strip() for p in _SEPARATOR_RE.split(text) if p.strip()]
    candidate = parts[0] if parts else text

    candidate = _MULTI_SPACE_RE.sub(" ", candidate).strip()
    return candidate.title() if candidate else raw_description.strip()[:255]


def looks_like_transfer(raw_description: str) -> bool:
    lower = raw_description.lower()
    return any(keyword in lower for keyword in TRANSFER_KEYWORDS)


def looks_like_subscription(merchant: str) -> bool:
    lower = merchant.lower()
    return any(hint in lower for hint in _SUBSCRIPTION_HINTS)
