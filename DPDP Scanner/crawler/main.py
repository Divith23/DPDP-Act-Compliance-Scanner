import sys

# Force UTF-8 on Windows stdout/stderr
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Fallback: override print to guarantee charmap/encoding safety across Windows terminals
_orig_print = print
def print(*args, **kwargs):
    kwargs.setdefault("flush", True)
    try:
        _orig_print(*args, **kwargs)
    except (UnicodeEncodeError, Exception):
        try:
            safe_args = [
                str(arg).encode("ascii", "replace").decode("ascii")
                for arg in args
            ]
            _orig_print(*safe_args, **kwargs)
        except Exception:
            pass

from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, urlparse
import re
from database import save_website
from site_profiles import build_profile_queue, get_site_profile
import os


# --------------------------------------------------
# 2. Compliance-related keywords
# --------------------------------------------------

policy_keywords = [
    "privacy", "privacy policy", "privacy notice", "privacy statement",
    "data privacy", "data protection", "personal data", "personal information",
    "consent", "consent management", "withdraw consent", "consent withdrawal",
    "your rights", "data subject rights", "data principal", "access your data",
    "correct your data", "correction", "update your information",
    "delete your data", "deletion", "erasure",
    "notice", "information we collect", "data we collect",
    "how we use your data", "purpose of processing", "data processing",
    "use of personal data", "data retention", "retention period",
    "how long we keep", "retention", "data sharing", "third party",
    "third parties", "service providers", "data processor", "data fiduciary",
    "security", "security measures", "security safeguards", "data security",
    "data breach", "breach notification", "incident",
    "children", "child", "parental consent", "minor",
    "grievance", "grievance officer", "complaint", "contact us",
    "privacy contact", "data protection officer", "dpo",
    "cookie", "cookies", "cookie policy", "cookie notice",
        "legal", "terms", "terms of use", "terms and conditions",

    # College / institutional pages that commonly contain
    # personal-data processing evidence
    "admission", "admissions", "application", "apply",
    "registration", "register", "student", "students",
    "faculty", "staff", "employee", "recruitment",
    "career", "careers", "placement", "placements",
    "feedback", "feedback form", "survey",
    "online payment", "payment", "fee", "fees",
    "form", "forms", "portal", "login",
    "alumni", "alumni registration",
    "scholarship", "hostel", "transport",
    "library", "examination", "exam",
    "internship", "internships",
    "contact", "complaint", "grievance",

]

# Known analytics/advertising/tracker cookie name patterns. This is only
# used to flag a cookie as tracker-like for the analyzer's evidence -- it
# never decides compliance itself.
TRACKER_COOKIE_PATTERNS = (
    "_ga", "_gid", "_gat", "_gcl", "_fbp", "_fbc", "ide", "anid", "nid",
    "__utm", "_hjid", "_hjsession", "muid", "personalization_id",
    "_pin_unauth", "_ttp", "_uetsid", "_uetvid", "test_cookie",
)

# Field-name / label keywords used to derive a structured, deterministic
# list of the personal-data categories a form literally asks for. This
# never infers a category that wasn't actually named on a field.
PERSONAL_DATA_FIELD_KEYWORDS = {
    "name": "Name",
    "email": "Email address",
    "phone": "Phone/mobile number",
    "mobile": "Phone/mobile number",
    "address": "Address",
    "pincode": "Postal/PIN code",
    "zip": "Postal/ZIP code",
    "dob": "Date of birth",
    "birth": "Date of birth",
    "gender": "Gender",
    "pan": "PAN number",
    "aadhaar": "Aadhaar number",
    "aadhar": "Aadhaar number",
    "gst": "GST number",
    "bank": "Bank account details",
    "ifsc": "Bank account details",
    "card": "Payment card details",
    "cvv": "Payment card details",
    "otp": "OTP / mobile verification",
}

# Fallback paths to probe when a category (privacy/terms/contact/etc.)
# was never discovered via the on-page link scan or sitemap.xml.
FALLBACK_PATHS = {
    ("privacy",): ["/privacy-policy", "/privacy", "/legal/privacy-policy", "/privacy-notice"],
    ("terms",): ["/terms-of-use", "/terms", "/terms-and-conditions", "/legal/terms"],
    ("contact", "grievance"): ["/contact-us", "/contact", "/grievance-redressal", "/grievance"],
    ("cookie",): ["/cookie-policy", "/cookies"],
    ("security",): ["/security", "/security-policy"],
}

FAST_DEMO_MODE = os.getenv("DPDP_FAST_MODE", "1") == "1"
MAX_PAGES = 8 if FAST_DEMO_MODE else 40
MAX_CRAWL_DEPTH = 1 if FAST_DEMO_MODE else 3


# --------------------------------------------------
# 3. Small helpers
# --------------------------------------------------

def _clean(value):
    return " ".join(str(value or "").split())


def _normalize_url(u: str) -> str:
    """Strip fragment/query noise so the same page isn't queued twice."""
    parsed = urlparse(u)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")


def _is_skippable_href(href: str) -> bool:
    href = (href or "").strip().lower()
    return (
        href.startswith("javascript:")
        or href.startswith("#")
        or href == ""
    )


def _all_field_like_items(ui_evidence: dict) -> list:
    """Flatten form fields + standalone input/textarea/select UI items
    into one list of field-like dicts for personal-data-category detection."""
    items = []
    for form in ui_evidence.get("forms", []):
        items.extend(form.get("fields", []))
    for item in ui_evidence.get("ui_information", []):
        if item.get("element") in ("input", "textarea", "select"):
            items.append(item)
    return items


def _extract_data_type_labels(fields) -> list:
    """Turn captured field name/id/placeholder/label/aria_label text into
    a deduplicated, sorted list of personal-data categories a form
    literally names. Purely keyword-based -- never invents a category."""
    found = set()
    for field in fields:
        haystack = " ".join(
            str(field.get(k, "")) for k in
            ("name", "id", "placeholder", "aria_label", "label", "text")
        ).lower()
        for keyword, label in PERSONAL_DATA_FIELD_KEYWORDS.items():
            if keyword in haystack:
                found.add(label)
    return sorted(found)


def _capture_cookies(page, page_label: str) -> list:
    """Snapshot cookies set in this page's (isolated) browser context and
    flag any that match known tracker/analytics name patterns."""
    try:
        raw_cookies = page.context.cookies()
    except Exception:
        return []

    cookies = []
    for cookie in raw_cookies:
        name = cookie.get("name", "")
        cookies.append({
            "name": name,
            "domain": cookie.get("domain", ""),
            "secure": cookie.get("secure", False),
            "http_only": cookie.get("httpOnly", False),
            "same_site": cookie.get("sameSite", ""),
            "seen_on": page_label,
            "looks_like_tracker": any(
                pattern in name.lower() for pattern in TRACKER_COOKIE_PATTERNS
            ),
        })
    return cookies


# --------------------------------------------------
# 4. UI / operational evidence extraction (unchanged)
# --------------------------------------------------

def extract_ui_evidence(page):
    """
    Capture operational evidence that body.inner_text() can miss:
    forms, fields, checkboxes, buttons, relevant links, and language/select
    controls.

    High-performance: runs a single in-browser JS evaluation to eliminate
    hundreds of synchronous Playwright DevTools IPC roundtrips.
    """
    try:
        raw_dom = page.evaluate("""() => {
            const clean = (s) => (s || '').replace(/\\s+/g, ' ').trim();

            const forms = Array.from(document.querySelectorAll('form')).map(f => {
                const controls = Array.from(f.querySelectorAll('input, textarea, select, button')).map(c => ({
                    tag: c.tagName.toLowerCase(),
                    type: c.getAttribute('type') || '',
                    name: c.getAttribute('name') || '',
                    id: c.getAttribute('id') || '',
                    placeholder: c.getAttribute('placeholder') || '',
                    aria_label: c.getAttribute('aria-label') || '',
                    required: c.hasAttribute('required'),
                    text: (c.tagName.toLowerCase() === 'button' || c.tagName.toLowerCase() === 'select') ? clean(c.innerText) : ''
                }));
                return {
                    action: f.getAttribute('action') || '',
                    method: f.getAttribute('method') || '',
                    text: clean(f.innerText).slice(0, 2000),
                    fields: controls.slice(0, 40)
                };
            });

            const buttonEls = Array.from(document.querySelectorAll("button, input[type='button'], input[type='submit'], input[type='checkbox'], [role='button']")).map(b => ({
                text: clean(b.innerText || b.getAttribute('aria-label') || b.getAttribute('value') || b.getAttribute('title')).slice(0, 300),
                type: b.getAttribute('type') || '',
                aria_label: b.getAttribute('aria-label') || '',
                name: b.getAttribute('name') || '',
                id: b.getAttribute('id') || ''
            }));

            const inputs = Array.from(document.querySelectorAll('input, textarea, select')).map(c => {
                let labelText = '';
                const cid = c.getAttribute('id');
                if (cid) {
                    try {
                        const l = document.querySelector(`label[for='${CSS.escape(cid)}']`);
                        if (l) labelText = clean(l.innerText);
                    } catch (e) {}
                }
                if (!labelText) {
                    const p = c.closest('label');
                    if (p) labelText = clean(p.innerText);
                }
                return {
                    element: c.tagName.toLowerCase(),
                    type: (c.getAttribute('type') || '').toLowerCase(),
                    name: c.getAttribute('name') || '',
                    id: cid || '',
                    placeholder: c.getAttribute('placeholder') || '',
                    aria_label: c.getAttribute('aria-label') || '',
                    label: labelText.slice(0, 300),
                    required: c.hasAttribute('required')
                };
            });

            const links = Array.from(document.querySelectorAll('a')).map(a => ({
                text: clean(a.innerText).slice(0, 300),
                href: (a.getAttribute('href') || '').slice(0, 1000)
            }));

            const selects = Array.from(document.querySelectorAll('select')).map(s => ({
                options: Array.from(s.options).map(o => ({
                    text: clean(o.innerText).slice(0, 100),
                    value: (o.value || '').slice(0, 200)
                })).filter(o => o.text).slice(0, 50)
            })).filter(s => s.options.length > 1);

            return { forms, buttonEls, inputs, links, selects };
        }""")
    except Exception:
        raw_dom = {"forms": [], "buttonEls": [], "inputs": [], "links": [], "selects": []}

    forms = raw_dom.get("forms", [])
    consent_mechanisms = []
    ui_information = []

    consent_terms = (
        "i consent", "i agree", "i accept", "give consent",
        "opt in", "opt-in", "opt out", "opt-out",
        "withdraw consent", "manage choices",
        "manage preferences", "privacy choices",
        "cookie preferences", "cookie choices",
    )
    for b in raw_dom.get("buttonEls", []):
        text = b.get("text", "")
        if not text:
            continue
        item = {
            "element": "button_or_control",
            "text": text,
            "type": b.get("type", ""),
            "aria_label": b.get("aria_label", ""),
            "name": b.get("name", ""),
            "id": b.get("id", ""),
        }
        lowered = text.lower()
        if any(term in lowered for term in consent_terms):
            consent_mechanisms.append({**item, "source": "button/control"})

    consent_label_terms = (
        "consent", "agree", "privacy", "marketing",
        "terms", "cookie", "communication",
        "personal data", "personal information"
    )
    for inp in raw_dom.get("inputs", []):
        ui_information.append(inp)
        label_text = inp.get("label", "")
        if any(term in label_text.lower() for term in consent_label_terms):
            consent_mechanisms.append({**inp, "source": "input/label"})

    relevant_link_terms = (
        "privacy", "privacy centre", "privacy center",
        "data rights", "your rights", "access your data",
        "delete your data", "erase", "withdraw",
        "consent preference", "privacy choice",
        "cookie preference", "grievance", "complaint",
        "dpo", "data protection officer", "language"
    )
    for link in raw_dom.get("links", []):
        text = link.get("text", "")
        href = link.get("href", "")
        if not text:
            continue
        combined = f"{text} {href}".lower()
        if any(term in combined for term in relevant_link_terms):
            item = {
                "element": "link",
                "text": text,
                "href": href,
            }
            ui_information.append(item)
            if any(term in combined for term in ("privacy", "consent", "withdraw", "cookie preference", "privacy choice")):
                consent_mechanisms.append({**item, "source": "link"})

    for sel in raw_dom.get("selects", []):
        ui_information.append({
            "element": "select",
            "options": sel["options"]
        })

    def dedupe(items):
        seen = set()
        result = []
        for item in items:
            key = repr(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    return {
        "forms": dedupe(forms)[:50],
        "consent_mechanisms": dedupe(consent_mechanisms)[:100],
        "ui_information": dedupe(ui_information)[:250],
    }


# --------------------------------------------------
# 5. Link discovery + page crawling helpers
# --------------------------------------------------

def _collect_links(source_page, depth, visited, queue, mailto_tel_evidence):
    """Scan a page's <a> tags for compliance-relevant links.

    mailto:/tel: links are captured directly as contact evidence (no
    navigation needed). Everything else is matched against policy_keywords
    and queued for crawling if not already visited, up to MAX_CRAWL_DEPTH.
    """
    if depth > MAX_CRAWL_DEPTH:
        return

    try:
        raw_links = source_page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                href: a.getAttribute('href') || '',
                text: (a.innerText || '').replace(/\\s+/g, ' ').trim()
            }));
        }""")
    except Exception:
        raw_links = []

    for item in raw_links:
        href = item.get("href")
        link_text = _clean(item.get("text"))

        if not href:
            continue

        lowered_href = href.strip().lower()

        if lowered_href.startswith("mailto:") or lowered_href.startswith("tel:"):
            target = href.split(":", 1)[1].split("?")[0]
            kind = "Email" if lowered_href.startswith("mailto:") else "Phone"
            mailto_tel_evidence.append(
                f"{kind}: {target} (link text: '{link_text}')"
            )
            continue

        if _is_skippable_href(href):
            continue

        full_url = urljoin(source_page.url, href)
        normalized = _normalize_url(full_url)

        if normalized in visited:
            continue

        combined_text = (link_text + " " + full_url).lower()

        for keyword in policy_keywords:
            if keyword in combined_text:
                visited.add(normalized)
                queue.append({"name": link_text, "url": full_url, "depth": depth})
                break


def _extract_pdf_content(context, url: str) -> str:
    """Download and extract text from a PDF document using PyMuPDF (fitz)."""
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            print("PyMuPDF (fitz) is not installed; skipping PDF extraction.")
            return ""

    try:
        resp = context.request.get(url, timeout=15000)
        if not resp.ok:
            return ""
        pdf_bytes = resp.body()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []
        for page_num in range(min(len(doc), 30)):
            page_text = doc[page_num].get_text()
            if page_text:
                text_parts.append(page_text)
        doc.close()
        raw_text = "\n".join(text_parts)
        raw_text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", raw_text)
        return _clean(raw_text)
    except Exception as e:
        print(f"Failed to extract PDF from {url}: {e}")
        return ""


def _visit_and_extract(context, item, visited, queue, mailto_tel_evidence):
    """Crawl one queued page: extract text + UI evidence, capture cookies,
    derive personal-data-field evidence, and queue any new compliance-
    relevant links found on it (depth-capped)."""
    policy_url = item["url"]

    print("\n------------------------------------")
    print("Opening:", policy_url)
    print("------------------------------------")

    # Handle direct PDF URLs
    is_pdf = policy_url.lower().split("?")[0].endswith(".pdf")
    if is_pdf:
        print("Detected PDF document, extracting text via PyMuPDF...")
        try:
            pdf_text = _extract_pdf_content(context, policy_url)
            print(f"Extracted {len(pdf_text)} characters from PDF.")
            if pdf_text:
                return {
                    "name": item.get("name", ""),
                    "url": policy_url,
                    "title": item.get("name") or "PDF Document",
                    "content": pdf_text,
                    "forms": [],
                    "consent_mechanisms": [],
                    "ui_information": [],
                    "cookies": [],
                    "personal_data_collected": [],
                }
        except Exception as e:
            print("Failed to process PDF:", e)
            return None

    policy_page = context.new_page()
    try:
        policy_page.set_default_timeout(8000 if FAST_DEMO_MODE else 25000)
        policy_page.goto(policy_url, wait_until="domcontentloaded", timeout=8000 if FAST_DEMO_MODE else 25000)
        policy_page.wait_for_timeout(50 if FAST_DEMO_MODE else 500)

        # Light scroll to reveal footer / lazy elements
        try:
            policy_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            policy_page.wait_for_timeout(50 if FAST_DEMO_MODE else 250)
            policy_page.evaluate("window.scrollTo(0, 0)")
        except Exception:
            pass

        policy_title = policy_page.title()
        policy_content = _clean(policy_page.locator("body").inner_text())
        ui_evidence = extract_ui_evidence(policy_page)
        page_cookies = _capture_cookies(policy_page, item.get("name") or policy_url)
        page_data_types = _extract_data_type_labels(_all_field_like_items(ui_evidence))

        result = {
            "name": item.get("name", ""),
            "url": policy_url,
            "title": policy_title,
            "content": policy_content,
            "forms": ui_evidence["forms"],
            "consent_mechanisms": ui_evidence["consent_mechanisms"],
            "ui_information": ui_evidence["ui_information"],
            "cookies": page_cookies,
            "personal_data_collected": page_data_types,
        }

        print("Title:", policy_title)
        print("\nContent preview:")
        preview = policy_content[:500].encode("ascii", "replace").decode("ascii")
        print(preview)
        print("\nUI evidence:")
        print("Forms:", len(ui_evidence["forms"]))
        print("Consent controls:", len(ui_evidence["consent_mechanisms"]))
        print("Relevant UI elements:", len(ui_evidence["ui_information"]))
        print("Cookies observed:", len(page_cookies))

        # One more hop: a page like the Privacy Policy often links to a
        # dedicated Grievance Officer / Cookie Policy page the homepage
        # never linked to directly.
        _collect_links(
            policy_page,
            depth=item.get("depth", 1) + 1,
            visited=visited,
            queue=queue,
            mailto_tel_evidence=mailto_tel_evidence,
        )

        return result

    except Exception as e:
        print("Could not crawl this page.")
        print("Reason:", e)
        return None
    finally:
        try:
            policy_page.close()
        except Exception:
            pass


def _drain_queue(context, queue, idx, visited, results, mailto_tel_evidence, max_pages):
    while idx < len(queue) and len(results) < max_pages:
        item = queue[idx]
        idx += 1
        record = _visit_and_extract(context, item, visited, queue, mailto_tel_evidence)
        if record:
            results.append(record)
    return idx


def _category_present(results, category_terms):
    return any(
        any(
            term in (r.get("name", "") + " " + r.get("url", "")).lower()
            for term in category_terms
        )
        for r in results
    )


# --------------------------------------------------
# 6. Start Playwright
# --------------------------------------------------

def crawl_website(url: str) -> str:
    """
    Crawl a website, store the extracted DPDP evidence in MongoDB,
    and return the generated MongoDB scan_id.
    """
    url = (url or "").strip()
    if not url:
        raise ValueError("Website URL is required.")

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False,
            args=[
                "--headless=new",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Block heavy resources (images, fonts, media) to speed up page loading 5x-10x
        def _block_heavy(route):
            if route.request.resource_type in {"image", "media", "font"}:
                route.abort()
            else:
                route.continue_()

        context.route("**/*", _block_heavy)

        page = context.new_page()
        page.set_default_timeout(10000 if FAST_DEMO_MODE else 30000)
        page.set_default_navigation_timeout(12000 if FAST_DEMO_MODE else 60000)

        try:
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=12000 if FAST_DEMO_MODE else 60000
            )
        except Exception as e:
            # Fallback retry with commit state if protocol/domcontentloaded issues arise
            try:
                page.goto(
                    url,
                    wait_until="commit",
                    timeout=15000 if FAST_DEMO_MODE else 30000
                )
            except Exception:
                print(f"[WARNING] Page navigation timeout/error for {url}: {e}")
                try:
                    browser.close()
                except Exception:
                    pass
                raise RuntimeError(f"Could not connect to {url}: {e}")

        # Give client-rendered homepage content a chance to settle before reading it.
        try:
            page.wait_for_load_state("networkidle", timeout=1200 if FAST_DEMO_MODE else 8000)
        except Exception:
            pass
        page.wait_for_timeout(50 if FAST_DEMO_MODE else 500)

        # Light scroll to reveal lazy footer links and trigger banner observers
        try:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(50 if FAST_DEMO_MODE else 300)
            page.evaluate("window.scrollTo(0, 0)")
        except Exception:
            pass

        print("\n====================================")
        print("WEBSITE INFORMATION")
        print("====================================")

        print("Title:", page.title())
        print("URL:", page.url)

        # --------------------------------------------------
        # 7. Extract homepage content + UI evidence
        #
        # The homepage's own text and controls are now kept (previously the
        # body text was only printed and discarded, and homepage_ui was never
        # merged into most evidence buckets downstream).
        # --------------------------------------------------

        homepage_text = _clean(page.locator("body").inner_text())
        homepage_ui = extract_ui_evidence(page)
        homepage_cookies = _capture_cookies(page, "homepage")
        homepage_data_types = _extract_data_type_labels(_all_field_like_items(homepage_ui))

        print("\nWebsite content:")
        print(homepage_text[:3000])

        print("\nUI evidence:")
        print("Forms:", len(homepage_ui["forms"]))
        print("Consent controls:", len(homepage_ui["consent_mechanisms"]))
        print("Relevant UI elements:", len(homepage_ui["ui_information"]))
        print("Cookies observed:", len(homepage_cookies))

        # --------------------------------------------------
        # 8. Discover compliance-related links (depth 1: homepage)
        # --------------------------------------------------

        visited = {_normalize_url(page.url)}
        queue = []
        mailto_tel_evidence = []

        # Seed known high-value public pages for the review websites. This is
        # routing only; every finding still comes from live website content.
        for item in build_profile_queue(url):
            normalized = _normalize_url(item["url"])
            if normalized not in visited:
                visited.add(normalized)
                queue.append(item)

        _collect_links(page, depth=1, visited=visited, queue=queue, mailto_tel_evidence=mailto_tel_evidence)

        print("\n====================================")
        print("COMPLIANCE LINKS FOUND")
        print("====================================")

        if not queue:
            print("No compliance-related links found on the homepage.")
        else:
            for index, item in enumerate(queue):
                print(f"\n[{index + 1}]")
                print("Name:", item["name"])

                print("URL :", item["url"])

        # --------------------------------------------------
        # 9. Optional sitemap discovery
        # --------------------------------------------------

        if FAST_DEMO_MODE:
            print("Fast review mode: sitemap discovery skipped.")
        else:
            print("\n====================================")
            print("DISCOVERING ADDITIONAL COMPLIANCE PAGES")
            print("====================================")

            parsed_base = urlparse(url)
            base = f"{parsed_base.scheme}://{parsed_base.netloc}"

            try:
                for sitemap_path in ("/sitemap.xml", "/sitemap_index.xml", "/sitemap/"):
                    sitemap_url = urljoin(base, sitemap_path)
                    try:
                        sitemap_resp = page.context.request.get(sitemap_url, timeout=10000)
                        if not sitemap_resp.ok:
                            continue
                        sitemap_text = sitemap_resp.text()
                        sitemap_urls = re.findall(r"<loc>\s*(.*?)\s*</loc>", sitemap_text, flags=re.IGNORECASE)
                        print(f"Sitemap discovered: {sitemap_url} ({len(sitemap_urls)} URLs)")
                        for loc in sitemap_urls[:1000]:
                            loc = loc.strip()
                            if not loc.startswith(("http://", "https://")):
                                continue
                            normalized = _normalize_url(loc)
                            if normalized in visited:
                                continue
                            lowered = loc.lower()
                            if any(keyword in lowered for keyword in policy_keywords):
                                visited.add(normalized)
                                queue.append({"name": "(from sitemap)", "url": loc, "depth": 1, "priority": 1})
                        if sitemap_urls:
                            break
                    except Exception as sitemap_error:
                        print(f"Could not read {sitemap_url}: {sitemap_error}")
            except Exception as e:
                print("Sitemap discovery failed:", e)

        # --------------------------------------------------
        # 9b. Prioritize high-value pages
        # --------------------------------------------------

        HIGH_VALUE_TERMS = (
            "privacy",
            "grievance",
            "complaint",
            "contact",
            "data",
            "consent",
            "cookie",
            "admission",
            "application",
            "registration",
            "feedback",
            "form",
            "payment",
            "student",
            "portal",
            "scholarship",
            "recruitment",
            "career",
            "alumni",
        )

        def page_priority(item):
            text = (
                str(item.get("name", "")) + " " +
                str(item.get("url", ""))
            ).lower()

            # Seeded target profile pages have high authority for compliance discovery
            score = int(item.get("priority", 0))

            for term in HIGH_VALUE_TERMS:
                if term in text:
                    score += 10

            # Explicit privacy/legal pages get highest priority.
            if "privacy" in text or "data-protection" in text or "data protection" in text:
                score += 150

            if "grievance" in text or "complaint" in text or "redress" in text or "icc" in text or "internal compliance" in text:
                score += 120

            if "security" in text or "it-policy" in text or "it policy" in text or "whitehat" in text:
                score += 110

            if "consent" in text or "cookie" in text:
                score += 90

            if "terms" in text or "legal" in text or "conditions" in text:
                score += 70

            if "form" in text or "application" in text:
                score += 30

            if "admission" in text or "registration" in text:
                score += 25

            if "payment" in text or "fee" in text:
                score += 20

            return score


        queue.sort(
            key=lambda item: page_priority(item),
            reverse=True
        )

        print("\nPrioritized pages:")

        for index, item in enumerate(queue[:MAX_PAGES]):
            print(
                f"[{index + 1}] "
                f"Priority={page_priority(item)} "
                f"{item.get('name', '')} -> {item.get('url', '')}"
            )


        # --------------------------------------------------
        # 9c. Crawl discovered pages
        # --------------------------------------------------

        print("\n====================================")
        print("EXTRACTING POLICY + UI CONTENT")
        print("====================================")

        results = []

        idx = _drain_queue(
            context,
            queue,
            0,
            visited,
            results,
            mailto_tel_evidence,
            MAX_PAGES
        )

        # --------------------------------------------------
        # 9d. Probe fallback paths for missing essential categories
        # --------------------------------------------------
        parsed_base = urlparse(url)
        base = f"{parsed_base.scheme}://{parsed_base.netloc}"
        fallback_candidates = []

        for cat_terms, paths in FALLBACK_PATHS.items():
            if not _category_present(results, cat_terms):
                for path in paths:
                    candidate_url = urljoin(base, path)
                    normalized = _normalize_url(candidate_url)
                    if normalized not in visited:
                        visited.add(normalized)
                        try:
                            resp = page.context.request.get(
                                candidate_url,
                                timeout=1000 if FAST_DEMO_MODE else 5000
                            )
                            if resp.ok and resp.status < 400:
                                label = f"Fallback ({'/'.join(cat_terms)})"
                                fallback_candidates.append({
                                    "name": label,
                                    "url": candidate_url,
                                    "depth": 1,
                                })
                                print(f"Discovered fallback page for {cat_terms}: {candidate_url}")
                                break
                        except Exception:
                            pass

        if fallback_candidates and len(results) < MAX_PAGES:
            queue.extend(fallback_candidates)
            idx = _drain_queue(
                context,
                queue,
                idx,
                visited,
                results,
                mailto_tel_evidence,
                MAX_PAGES
            )


        # --------------------------------------------------
        # 10. Crawling summary
        # --------------------------------------------------

        print("\n====================================")
        print("CRAWLING COMPLETED")
        print("====================================")

        print("Pages queued:", len(queue))
        print("Pages successfully extracted:", len(results))
        print("Mailto/tel contact links captured:", len(mailto_tel_evidence))

        # --------------------------------------------------
        # 11. Prepare data for MongoDB
        # --------------------------------------------------

        print("\nPreparing data for MongoDB...")

        homepage_page = {
            "name": "Homepage",
            "url": page.url,
            "title": page.title(),
            "content": homepage_text,
            "forms": homepage_ui["forms"],
            "consent_mechanisms": homepage_ui["consent_mechanisms"],
            "ui_information": homepage_ui["ui_information"],
            "cookies": homepage_cookies,
            "personal_data_collected": homepage_data_types,
        }

        pages = [homepage_page] + results

        if mailto_tel_evidence:
            pages.append({
                "name": "Contact details (extracted from mailto/tel links)",
                "url": urljoin(page.url, "#extracted-contact-links"),
                "title": "Extracted contact links",
                "content": "\n".join(sorted(set(mailto_tel_evidence))),
                "forms": [],
                "consent_mechanisms": [],
                "ui_information": [],
                "cookies": [],
                "personal_data_collected": [],
            })

        all_cookies = []
        seen_cookie_keys = set()
        for p_ in pages:
            for c in p_.get("cookies", []):
                key = (c.get("name"), c.get("domain"))
                if key not in seen_cookie_keys:
                    seen_cookie_keys.add(key)
                    all_cookies.append(c)

        all_forms = [f for p_ in pages for f in p_.get("forms", [])]
        all_consent_mechanisms = [c for p_ in pages for c in p_.get("consent_mechanisms", [])]
        all_data_types = sorted({dt for p_ in pages for dt in p_.get("personal_data_collected", [])})

        profile = get_site_profile(url)

        website_data = {
            "website": url,
            "pages": pages,
            "crawl_profile": profile.get("name") if profile else None,
            "fast_review_mode": FAST_DEMO_MODE,

            # Kept for backward compatibility / debugging.
            "homepage_ui": homepage_ui,

            # Top-level aggregates -- these are what crawler_normalization.py
            # and compliance_analyzer.py's _build_rag_queries() actually read.
            "forms": all_forms,
            "consent_mechanisms": all_consent_mechanisms,
            "cookies": all_cookies,
            "personal_data_collected": all_data_types,
        }

        # --------------------------------------------------
        # 12. Save data to MongoDB
        # --------------------------------------------------

        print("Sending data to MongoDB...")

        scan_id = save_website(website_data)

        print("MongoDB operation completed.")

        print(f"Scan ID: {scan_id}")

        # --------------------------------------------------
        # 13. Close browser
        # --------------------------------------------------

        browser.close()

        print("\nCrawler finished successfully!")

    return scan_id

if __name__ == "__main__":
    website_url = input("Enter website URL: ").strip()
    generated_scan_id = crawl_website(website_url)
    print(f"Generated Scan ID: {generated_scan_id}")
