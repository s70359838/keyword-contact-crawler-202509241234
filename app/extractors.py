import re
from typing import List, Tuple

import phonenumbers

EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-]+)\s*(?:\[?at\]?|\(at\)|@)\s*([A-Za-z0-9.-]+)\s*(?:\[?dot\]?|\(dot\)|\.|\s*\.\s*)([A-Za-z]{2,})", re.I)
EMAIL_CLEAN_RE = re.compile(r"[\[\]\(\)\s]")

PHONE_RE = re.compile(r"(?:(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4})")

WECHAT_RE = re.compile(r"(?:微信|weixin|wechat|vx|v信)[^\w]?[:：\-\s]*([A-Za-z0-9_\-]{3,})", re.I)
QQ_RE = re.compile(r"(?:QQ|扣扣)[^\d]*([1-9]\d{4,11})", re.I)
TELEGRAM_RE = re.compile(r"(?:t\.me/([A-Za-z0-9_]{3,}))|(?:telegram[^\w]?[:：\-\s]*@([A-Za-z0-9_]{3,}))", re.I)
WHATSAPP_RE = re.compile(r"(?:wa\.me/(\d{5,15}))|(?:WhatsApp[^\d]*([\+\d][\d\s\-]{6,}))", re.I)

SOCIAL_RE = re.compile(r"https?://(?:www\.)?(?:twitter|x|linkedin|facebook|weibo|zhihu|bilibili|github)\.[^\s\"]+", re.I)


def extract_emails(text: str) -> List[str]:
    emails = []
    for m in EMAIL_RE.finditer(text or ""):
        local, dom, tld = m.groups()
        email = f"{local}@{dom}.{tld}"
        email = EMAIL_CLEAN_RE.sub("", email)
        emails.append(email)
    for m in re.finditer(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text or ""):
        emails.append(m.group(0))
    seen = set()
    uniq = []
    for e in emails:
        e2 = e.lower()
        if e2 not in seen:
            uniq.append(e2)
            seen.add(e2)
    return uniq


def extract_phones(text: str, default_region: str = "CN") -> List[str]:
    candidates = set()
    for m in PHONE_RE.finditer(text or ""):
        candidates.add(m.group(0))
    results = []
    for c in candidates:
        try:
            parsed = phonenumbers.parse(c, default_region)
            if phonenumbers.is_valid_number(parsed):
                results.append(phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164))
        except Exception:
            continue
    return sorted(set(results))


def extract_wechat(text: str) -> List[str]:
    res = []
    for m in WECHAT_RE.finditer(text or ""):
        res.append(m.group(1))
    return sorted(set(res))


def extract_qq(text: str) -> List[str]:
    res = []
    for m in QQ_RE.finditer(text or ""):
        res.append(m.group(1))
    return sorted(set(res))


def extract_telegram(text: str) -> List[str]:
    res = []
    for m in TELEGRAM_RE.finditer(text or ""):
        h = m.group(1) or m.group(2)
        if h:
            if not h.startswith("@"): h = "@" + h
            res.append(h)
    return sorted(set(res))


def extract_whatsapp(text: str) -> List[str]:
    res = []
    for m in WHATSAPP_RE.finditer(text or ""):
        num = m.group(1) or m.group(2)
        if num:
            num = re.sub(r"\D", "", num)
            if 6 <= len(num) <= 15:
                res.append("+" + num if not num.startswith("+") else num)
    return sorted(set(res))


def extract_social_links(text: str) -> List[str]:
    return sorted(set([m.group(0) for m in SOCIAL_RE.finditer(text or "")]))


def extract_all(text: str) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for e in extract_emails(text):
        pairs.append(("email", e))
    for p in extract_phones(text):
        pairs.append(("phone", p))
    for w in extract_wechat(text):
        pairs.append(("wechat", w))
    for q in extract_qq(text):
        pairs.append(("qq", q))
    for t in extract_telegram(text):
        pairs.append(("telegram", t))
    for w in extract_whatsapp(text):
        pairs.append(("whatsapp", w))
    for s in extract_social_links(text):
        pairs.append(("social", s))
    return pairs
