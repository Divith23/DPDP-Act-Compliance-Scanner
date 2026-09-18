import re
from app.services.requirement_evidence_matrix import build_requirement_matrix


def _extract_relevant_excerpts(
    content: str,
    keywords: list[str],
    window: int = 900,
    max_excerpts: int = 14,
    max_chars: int = 14000,
) -> str:
    """
    Extract bounded, requirement-focused evidence from crawler text.

    The crawler may return very long policy pages. We keep the sections around
    relevant phrases, deduplicate overlapping matches, and cap the final
    evidence size so downstream LLM calls remain small.
    """
    if not content:
        return ""

    text = " ".join(str(content).split())
    if not text:
        return ""

    matches = []
    for keyword in keywords:
        if not keyword:
            continue
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        for match in pattern.finditer(text):
            matches.append((match.start(), match.end(), keyword))

    if not matches:
        return ""

    # Merge overlapping/nearby keyword windows before extracting. This avoids
    # sending the same policy paragraph repeatedly when several keywords occur.
    intervals = []
    for start_pos, end_pos, _ in sorted(matches):
        left = max(0, start_pos - window)
        right = min(len(text), end_pos + window)
        if intervals and left <= intervals[-1][1] + 250:
            intervals[-1] = (intervals[-1][0], max(intervals[-1][1], right))
        else:
            intervals.append((left, right))

    excerpts = []
    seen = set()
    for left, right in intervals[:max_excerpts]:
        excerpt = text[left:right].strip()
        normalized = re.sub(r"\s+", " ", excerpt.lower())[:500]
        if normalized and normalized not in seen:
            seen.add(normalized)
            excerpts.append(excerpt)

    result = "\n\n".join(excerpts)
    if len(result) > max_chars:
        result = result[:max_chars].rstrip() + "\n...[evidence capped]..."
    return result


def _page_matches(page: dict, terms: tuple[str, ...]) -> bool:
    """
    Identify a page using its name, title, URL, and the beginning of its content.

    URL matching matters because many sites use generic page names such as
    "Page" or "Legal", while the actual URL contains /privacy, /terms, etc.
    Checking the first 500 characters of content catches PDFs or generic pages
    whose text begins with "Privacy Policy", "IT Policy", "Information Security", etc.
    """
    name = str(page.get("name", "")).lower()
    title = str(page.get("title", "")).lower()
    url = str(page.get("url", "")).lower()
    head = str(page.get("content", ""))[:500].lower()

    return any(
        term.lower() in name or
        term.lower() in title or
        term.lower() in url or
        term.lower() in head
        for term in terms
    )


def _combine_pages(pages: list[dict]) -> str:
    """Combine page content while preserving page boundaries."""
    parts = []

    for page in pages:
        content = page.get("content", "")
        if not content:
            continue

        parts.append(
            f"Page: {page.get('name', '')}\n"
            f"Title: {page.get('title', '')}\n"
            f"URL: {page.get('url', '')}\n"
            f"Content: {content}"
        )

    return "\n\n".join(parts)



def _stringify_structured_items(value) -> str:
    """Serialize crawler UI structures into compact, human-readable evidence."""
    if not value:
        return ""

    lines=[]
    seen=set()
    text_keys=("text","label","placeholder","aria_label","description","title","value","message")
    meta_keys=("tag","type","name","id","method","action","href","required","checked","selected")

    def add(line):
        line=re.sub(r"\s+"," ",str(line)).strip()
        if line and line.lower() not in seen:
            seen.add(line.lower()); lines.append(line)

    def walk(item, context=""):
        if isinstance(item,dict):
            pieces=[]
            for k in text_keys+meta_keys:
                v=item.get(k)
                if v not in (None,"",[],{}): pieces.append(f"{k}={v}")
            if pieces: add((context+": ") if context else "" + "; ".join(pieces))
            for k,v in item.items():
                if k in text_keys+meta_keys: continue
                if isinstance(v,(dict,list)): walk(v,k)
                elif v not in (None,""): add(f"{k}={v}")
        elif isinstance(item,list):
            for v in item: walk(v,context)
        elif item not in (None,""): add(f"{context}: {item}" if context else item)

    walk(value)
    return "\n".join(lines)


def _structured_focus(value, keywords: tuple[str,...], max_chars: int=5000) -> str:
    """Select only structured UI records whose visible semantics match a topic."""
    text=_stringify_structured_items(value)
    if not text: return ""
    selected=[]; seen=set()
    for line in text.splitlines():
        low=line.lower()
        if any(k.lower() in low for k in keywords):
            key=low[:500]
            if key not in seen:
                seen.add(key); selected.append(line)
    result="\n".join(selected)
    return result[:max_chars].rstrip()+("\n...[focused UI evidence capped]..." if len(result)>max_chars else "")


def _merge_nonempty(*values) -> str:
    return "\n\n".join(str(v).strip() for v in values if v and str(v).strip())


def _extract_ui_and_data_evidence(crawler_data: dict, pages: list[dict]) -> dict:
    """
    Extract focused evidence buckets from structured crawler output.

    The crawler may capture many unrelated controls on a modern ecommerce
    homepage. Keeping consent, language, rights, grievance and security UI
    evidence separate prevents generic controls from drowning out the useful
    evidence during requirement-specific analysis.
    """
    def flatten(value) -> str:
        return _stringify_structured_items(value)

    page_forms = []
    page_consent = []
    page_ui = []
    page_data = []
    page_cookies = []

    for page in pages:
        if page.get("forms"):
            page_forms.append(page.get("forms"))
        if page.get("consent_mechanisms"):
            page_consent.append(page.get("consent_mechanisms"))
        if page.get("ui_information"):
            page_ui.append(page.get("ui_information"))
        if page.get("personal_data_collected"):
            page_data.append(page.get("personal_data_collected"))
        if page.get("cookies"):
            page_cookies.append(page.get("cookies"))

    homepage_ui = crawler_data.get("homepage_ui", {})

    forms_text = flatten([crawler_data.get("forms", []), page_forms])
    consent_text = flatten([crawler_data.get("consent_mechanisms", []), page_consent])
    page_ui_text = flatten([page_ui])
    homepage_text = flatten(homepage_ui)
    data_text = flatten([crawler_data.get("personal_data_collected", []), page_data])
    cookies_text = flatten([crawler_data.get("cookies", []), page_cookies])

    # Keep topic-specific UI controls separate from generic ecommerce controls.
    # This is critical because the analyzer sees compact requirement-specific
    # evidence, not the whole crawler DOM.
    consent_ui_structured = _structured_focus(
        [crawler_data.get("forms", []), crawler_data.get("consent_mechanisms", []), page_forms, page_consent, page_ui],
        ("agree","accept","consent","privacy","terms","continue","withdraw",
         "cookie","preference","allow","deny","checkbox","radio","sign up","register"),
    )
    language_ui_structured = _structured_focus(
        [homepage_ui, page_ui],
        ("language","english","hindi","bengali","gujarati","kannada","malayalam",
         "marathi","punjabi","tamil","telugu","urdu","select","choose"),
    )
    rights_ui_structured = _structured_focus(
        [homepage_ui, page_ui],
        ("privacy","rights","access","correct","delete","erase","withdraw",
         "request","download","copy","update","edit","privacy centre","privacy center"),
    )
    grievance_ui_structured = _structured_focus(
        [homepage_ui, page_ui],
        ("grievance","complaint","redress","support","contact","officer","query",
         "raise","concern","helpdesk","email","phone"),
    )
    security_ui_structured = _structured_focus(
        [homepage_ui, page_ui],
        ("security","secure","encrypt","tls","ssl","authentication","authorization",
         "access control","backup","incident","breach","vulnerability","responsible disclosure"),
    )
    child_ui_structured = _structured_focus(
        [homepage_ui, page_ui],
        ("child","children","minor","under 18","parent","guardian","age","tracking",
         "behavioral","behavioural","targeted advertising"),
    )

    all_text = _combine_pages(pages)

    # Focused text extraction from page content.
    consent_excerpts = _extract_relevant_excerpts(
        all_text,
        [
            "I agree", "I accept", "Accept all", "Reject all",
            "Manage preferences", "Cookie settings", "Privacy choices",
            "consent", "consent request", "withdraw consent",
            "checkbox", "radio button", "clear affirmative action",
            "By continuing, I agree", "agree to the Terms",
            "agree to the Privacy Policy", "allow", "deny",
        ],
        window=550,
        max_excerpts=12,
        max_chars=7000,
    )

    language_excerpts = _extract_relevant_excerpts(
        all_text,
        [
            "English", "language", "languages", "select language",
            "choose language", "regional language", "Hindi", "Bengali",
            "Gujarati", "Kannada", "Malayalam", "Marathi", "Punjabi",
            "Tamil", "Telugu", "Urdu", "Eighth Schedule",
        ],
        window=450,
        max_excerpts=10,
        max_chars=5000,
    )

    rights_excerpts = _extract_relevant_excerpts(
        all_text,
        [
            "right to access", "access your personal data",
            "right to correction", "correct your personal data",
            "right to erasure", "delete your personal data",
            "withdraw your consent", "withdrawal of consent",
            "privacy centre", "privacy center", "submit a request",
            "data principal", "request your data",
        ],
        window=600,
        max_excerpts=12,
        max_chars=7000,
    )

    grievance_excerpts = _extract_relevant_excerpts(
        all_text,
        [
            "grievance officer", "grievance", "complaint", "complaints",
            "redressal", "redress", "raise a concern",
            "customer support", "nodal officer", "designated officer",
        ],
        window=600,
        max_excerpts=12,
        max_chars=7000,
    )

    security_excerpts = _extract_relevant_excerpts(
        all_text,
        [
            "security", "security measures", "security safeguards",
            "encryption", "encrypted", "TLS", "SSL", "access control",
            "authentication", "authorization", "incident response",
            "data breach", "breach notification", "vulnerability",
            "responsible disclosure",
        ],
        window=650,
        max_excerpts=12,
        max_chars=7000,
    )

    child_excerpts = _extract_relevant_excerpts(
        all_text,
        [
            "child", "children", "minor", "under 18",
            "parental consent", "guardian", "age verification",
            "age-gating", "tracking", "behavioural monitoring",
            "behavioral monitoring", "targeted advertising",
        ],
        window=600,
        max_excerpts=10,
        max_chars=6000,
    )

    ui_source = _merge_nonempty(
        forms_text,
        consent_text,
        page_ui_text,
        consent_excerpts,
    )

    return {
        # Backward-compatible generic fields.
        "ui_information": ui_source,
        "data_collection_evidence": _merge_nonempty(
            data_text,
            _extract_relevant_excerpts(
                all_text,
                [
                    "information we collect", "data we collect",
                    "personal data", "personal information", "name", "email",
                    "mobile number", "phone number", "address", "location",
                    "device", "IP address", "payment", "order",
                    "purchase", "transaction", "browsing", "cookies",
                ],
                window=650,
                max_excerpts=12,
                max_chars=9000,
            ),
        ),
        "structured_cookie_evidence": cookies_text,

        # Focused buckets for requirement-specific evidence mapping.
        "consent_ui_evidence": _merge_nonempty(
            consent_excerpts, consent_ui_structured, forms_text, consent_text
        ),
        "language_ui_evidence": _merge_nonempty(
            language_excerpts, language_ui_structured, homepage_text
        ),
        "rights_ui_evidence": _merge_nonempty(
            rights_excerpts, rights_ui_structured
        ),
        "grievance_ui_evidence": _merge_nonempty(
            grievance_excerpts, grievance_ui_structured
        ),
        "security_ui_evidence": _merge_nonempty(
            security_excerpts, security_ui_structured
        ),
        "child_ui_evidence": _merge_nonempty(
            child_excerpts, child_ui_structured
        ),
    }


def normalize_crawler_data(crawler_data: dict) -> dict:
    pages = crawler_data.get("pages", [])

    page_titles = []
    page_texts = []

    privacy_pages = []
    security_pages = []
    terms_pages = []
    contact_pages = []
    rights_pages = []
    cookie_pages = []
    child_pages = []
    consent_pages = []

    for page in pages:
        name = str(page.get("name", ""))
        title = str(page.get("title", ""))
        content = str(page.get("content", ""))

        if title:
            page_titles.append(title)

        if content:
            page_texts.append(
                f"Page: {name}\n"
                f"Title: {title}\n"
                f"URL: {page.get('url', '')}\n"
                f"Content: {content}"
            )

        # Use page identity (name/title/URL), not arbitrary words appearing
        # in body text, to decide which policy corpus is authoritative.
        if _page_matches(page, (
            "privacy", "privacy policy", "privacy notice", "data protection",
            "privacy statement", "data privacy", "mandatory disclosure",
        )):
            privacy_pages.append(page)

        if _page_matches(page, (
            "security", "security policy", "responsible disclosure",
            "information security", "it policy", "it_policy",
            "information network security", "cyber security", "cybersecurity",
        )):
            security_pages.append(page)

        if _page_matches(page, (
            "terms", "terms of use", "terms and conditions", "legal",
            "terms of service", "conditions of use",
        )):
            terms_pages.append(page)

        if _page_matches(page, (
            "contact", "customer support", "help", "grievance",
            "internal compliance", "icc", "complaint", "redressal",
            "ombudsman", "feedback mechanism", "samadhaan",
        )):
            contact_pages.append(page)

        if _page_matches(page, (
            "rights",
            "data rights",
            "privacy rights",
            "your rights",
            "data subject rights",
        )):
            rights_pages.append(page)

        if _page_matches(page, (
            "cookie",
            "cookies",
            "cookie policy",
        )):
            cookie_pages.append(page)

        if _page_matches(page, (
            "child",
            "children",
            "minor",
            "parental",
            "guardian",
        )):
            child_pages.append(page)

        if _page_matches(page, (
            "consent",
            "preferences",
            "privacy choices",
        )):
            consent_pages.append(page)

    privacy_text = _combine_pages(privacy_pages)
    security_text = _combine_pages(security_pages)
    terms_text = _combine_pages(terms_pages)
    contact_text = _combine_pages(contact_pages)
    rights_text = _combine_pages(rights_pages)
    cookie_text = _combine_pages(cookie_pages)
    child_text = _combine_pages(child_pages)
    consent_text = _combine_pages(consent_pages)

    # Structured/UI evidence can exist outside named policy pages (for example
    # on a homepage, login/signup page, cookie banner, or support flow).
    extra_evidence = _extract_ui_and_data_evidence(crawler_data, pages)
    ui_information = extra_evidence["ui_information"]
    data_collection_evidence = extra_evidence["data_collection_evidence"]
    structured_cookie_evidence = extra_evidence["structured_cookie_evidence"]

    # If a site puts rights/consent/child information inside its privacy
    # policy, include the privacy corpus as a source without treating the
    # whole policy as evidence for every requirement.
    rights_source = "\n\n".join(
        x for x in (privacy_text, rights_text, contact_text) if x
    )
    consent_source = "\n\n".join(
        x for x in (privacy_text, consent_text, child_text, ui_information) if x
    )
    child_source = "\n\n".join(
        x for x in (privacy_text, child_text) if x
    )
    security_source = "\n\n".join(
        x for x in (security_text, privacy_text) if x
    )
    breach_source = "\n\n".join(
        x for x in (privacy_text, security_text, terms_text) if x
    )
    cross_border_source = "\n\n".join(
        x for x in (privacy_text, terms_text) if x
    )
    retention_source = "\n\n".join(
        x for x in (privacy_text, terms_text) if x
    )
    personal_data_source = "\n\n".join(
        x for x in (
            privacy_text,
            rights_text,
            data_collection_evidence,
            structured_cookie_evidence,
        ) if x
    )

    grievance_information = _extract_relevant_excerpts(
        rights_source,
        [
            "grievance",
            "grievance officer",
            "complaint",
            "complaints",
            "redressal",
            "redress",
            "raise a concern",
            "raise concerns",
            "query, concern, or complaint",
            "customer support",
        ],
    )

    contact_information = _extract_relevant_excerpts(
        "\n\n".join(
            x for x in (contact_text, privacy_text, rights_text) if x
        ),
        [
            "data protection officer",
            "DPO",
            "privacy officer",
            "privacy contact",
            "grievance officer",
            "customer grievance",
            "contact",
            "email",
            "e-mail",
            "telephone",
            "phone",
            "address",
            "postal address",
            "registered office",
            "designated officer",
            "nodal officer",
        ],
    )

    security_policy = _extract_relevant_excerpts(
        security_source,
        [
            "encryption",
            "encrypted",
            "encrypt",
            "obfuscation",
            "masking",
            "masked",
            "virtual token",
            "tokenisation",
            "tokenization",
            "access control",
            "access controls",
            "authentication",
            "authorization",
            "authorisation",
            "security safeguard",
            "security measure",
            "technical measure",
            "organisational measure",
            "organizational measure",
            "backup",
            "backups",
            "logging",
            "logs",
            "monitoring",
            "review",
            "audit trail",
            "security",
            "encryption at rest",
            "encryption in transit",
            "TLS",
            "SSL",
            "firewall",
            "intrusion detection",
            "vulnerability",
            "penetration test",
            "least privilege",
            "role-based access",
            "access logs",
            "incident management",
            "disaster recovery",
            "backup and recovery", "reasonable security safeguards",
            "reasonable security practices", "protect personal data", "data security",
            "security standards", "industry standard", "secure server",
        ],
    )

    retention_information = _extract_relevant_excerpts(
        retention_source,
        [
            "retention",
            "retain",
            "retained",
            "stored",
            "storage period",
            "retention period",
            "delete",
            "deletion",
            "erasure",
            "erase",
            "destroy",
            "destroyed",
            "as long as necessary",
            "no longer necessary",
            "business purpose",
            "legal obligation",
            "statutory requirement",
            "account closure",
            "after termination",
            "period of one year",
            "one year", "two years", "three years", "retention schedule",
            "delete after", "deleted after", "purged", "dispose", "disposed",
            "necessary for the purpose", "necessary to comply",
        ],
    )

    breach_information = _extract_relevant_excerpts(
        breach_source,
        [
            "data breach",
            "personal data breach",
            "breach",
            "security incident",
            "incident",
            "incident response",
            "notify",
            "notification",
            "notified",
            "affected users",
            "affected individuals",
            "data principal",
            "board",
            "data protection board",
            "security incident",
            "incident response plan",
            "incident response procedure",
            "breach response",
            "report to the board",
            "notify the board",
            "notify affected",
            "without undue delay",
            "in such form and manner",
            "prescribed manner", "72 hours", "72-hour", "within 72",
            "affected data principal", "affected individual", "data protection board",
        ],
    )

    consent_information = _extract_relevant_excerpts(
        consent_source,
        [
            "consent",
            "consent request",
            "affirmative action",
            "clear affirmative action",
            "i agree",
            "i accept",
            "withdraw consent",
            "withdrawal of consent",
            "withdraw your consent",
            "consent preferences",
            "privacy choices",
            "parental consent",
            "verifiable consent",
            "guardian consent",
            "age verification",
            "verify parental",
            "accept all",
            "reject all",
            "manage preferences",
            "cookie settings",
            "privacy choices",
            "consent banner",
            "checkbox",
            "radio button",
            "signup",
            "sign up",
            "registration",
            "account creation",
            "allow",
            "deny",
        ],
    )

    personal_data_information = _extract_relevant_excerpts(
        personal_data_source,
        [
            "personal data",
            "personal information",
            "personal details",
            "information we collect",
            "data we collect",
            "collect your data",
            "categories of personal data",
            "types of personal data",
            "name",
            "email",
            "email id",
            "phone number",
            "telephone number",
            "address",
            "date of birth",
            "device identifiers",
            "ip address",
            "bank account",
            "credit card",
            "debit card",
            "pan",
            "gst",
            "kyc",
        ],
    )

    # Rights evidence is intentionally kept separate from generic policy text.
    # This gives the compliance analyzer a focused source for Sections 11-13
    # and Rule 14 without making generic mentions of "rights" look conclusive.
    rights_information = _extract_relevant_excerpts(
        rights_source,
        [
            "right to access",
            "access your personal data",
            "access personal data",
            "personal data being processed",
            "categories of personal data",
            "data shared",
            "recipients",
            "right to correction",
            "correct your personal data",
            "update your personal data",
            "complete your personal data",
            "right to erasure",
            "delete your personal data",
            "erase your personal data",
            "right to grievance",
            "grievance",
            "complaint",
            "registered email",
            "registered mobile",
            "user id",
            "account id",
            "identifier required",
            "request",
            "submit a request",
            "privacy centre",
            "privacy center",
            "copy of your personal data",
            "status of your request",
            "edit your personal data",
            "update your details",
            "withdraw",
            "withdrawal",
            "nominee",
            "nominate",
            "response",
            "within 90 days",
        ],
    )

    # Cross-border evidence is deliberately keyword-focused. A generic
    # statement that data is "stored" must not become evidence of transfer.
    cross_border_information = _extract_relevant_excerpts(
        cross_border_source,
        [
            "cross-border",
            "cross border",
            "international transfer",
            "international transfers",
            "transfer outside",
            "transferred outside",
            "outside india",
            "outside India",
            "overseas",
            "foreign country",
            "third country",
            "data localisation",
            "data localization",
            "store data in india",
            "stored in india",
        ],
    )

    child_information = _extract_relevant_excerpts(
        child_source,
        [
            "child",
            "children",
            "minor",
            "under 18",
            "under the age of 18",
            "parental consent",
            "verifiable parental consent",
            "guardian",
            "age verification",
            "age-gating",
            "age gate",
            "tracking",
            "behavioural monitoring",
            "behavioral monitoring",
            "targeted advertising",
            "targeted ads",
            "targeted advertising",
            "interest-based advertising",
            "behavioural advertising",
            "behavioral advertising",
            "age restriction",
            "age restricted",
            "under 18",
            "below 18",
            "parent or guardian",
        ],
    )

    normalized = dict(crawler_data)

    normalized.update({
        "url": crawler_data.get("website", ""),
        "title": page_titles[0] if page_titles else "",
        "description": "",

        "page_titles": page_titles,
        "page_text": "\n\n".join(page_texts),

        # Full policy text is retained for reference.
        "privacy_policy": privacy_text,
        "security_policy": security_text,
        "terms_of_use": terms_text,

        # Targeted evidence used by the compliance analyzer.
        "contact_information": contact_information,
        "grievance_information": grievance_information,
        "retention_information": retention_information,
        "breach_information": breach_information,
        "consent_information": consent_information,
        "personal_data_information": personal_data_information,
        "rights_information": rights_information,
        "cross_border_information": cross_border_information,
        "child_information": child_information,

        # Structured/UI evidence recovered from crawler output.
        "ui_information": ui_information,
        "data_collection_evidence": data_collection_evidence,
        "structured_cookie_evidence": structured_cookie_evidence,

        # Focused UI evidence buckets used by requirement-specific analysis.
        "consent_ui_evidence": extra_evidence.get("consent_ui_evidence", ""),
        "language_ui_evidence": extra_evidence.get("language_ui_evidence", ""),
        "rights_ui_evidence": extra_evidence.get("rights_ui_evidence", ""),
        "grievance_ui_evidence": extra_evidence.get("grievance_ui_evidence", ""),
        "security_ui_evidence": extra_evidence.get("security_ui_evidence", ""),
        "child_ui_evidence": extra_evidence.get("child_ui_evidence", ""),

        # Existing crawler fields.
        "forms": crawler_data.get("forms", []),
        "products_services": crawler_data.get("products_services", []),
        "personal_data_collected": crawler_data.get(
            "personal_data_collected", []
        ),
        "cookies": crawler_data.get("cookies", []),
        "consent_mechanisms": (
            crawler_data.get("consent_mechanisms", [])
            or ([ui_information] if ui_information else [])
        ),
        "requirement_matrix": {r["id"]: r for r in build_requirement_matrix()},
    })

    return normalized
