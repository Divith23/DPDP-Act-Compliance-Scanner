"""Fast review profiles. Profiles control discovery only; they never inject evidence."""
from urllib.parse import urlparse

SITE_PROFILES = {
    "skcet.ac.in": {
        "name": "SKCET",
        "seeds": [
            ("Grievance Portal", "/quick-links/grievance/"),
            ("Internal Compliance Committee", "/internal-compliance-committee-icc/"),
            ("AICTE Mandatory Disclosure", "/wp-content/uploads/2025/07/AICTE-Mandatory-Disclosure.pdf"),
            ("IT Policy", "/aqar/c4/4.3/4.3.1/4.3.1%20SKCET%20IT%20POLICY.pdf"),
            ("Institution", "/about-us/institution/"),
            ("IQAC", "/accreditations/iqac/about/"),
        ],
    },
    "psgcas.ac.in": {
        "name": "PSGCAS",
        "seeds": [
            ("Institutional Policies", "https://www.psgcas.ac.in/institutional-policies/"),
            ("Privacy Policy (Application Portal)", "https://applications.psgcas.ac.in/ug/privacyPolicy/privacyPolicy.html"),
        ],
    },
    "ieee.org": {
        "name": "IEEE",
        "seeds": [
            ("IEEE Privacy Policy", "https://www.ieee.org/security-privacy.html"),
            ("Terms and Conditions", "https://www.ieee.org/terms-and-conditions.html"),
            ("Contact", "https://www.ieee.org/contact.html"),
            ("Data Access and Use", "https://events.ieee.org/planning-basics/event-registration/policies-terms-conditions/"),
        ],
    },
    "passportindia.gov.in": {
        "name": "Passport Seva",
        "seeds": [
            ("Privacy Policy", "https://www.passportindia.gov.in/psp/Policy"),
            ("Passport Seva", "https://www.passportindia.gov.in/psp/"),
            ("Feedback and Grievance", "https://www.passportindia.gov.in/psp/feedback"),
            ("Terms and Conditions", "https://www.passportindia.gov.in/psp/termsConditions"),
        ],
    },
    "nike.in": {
        "name": "Nike India",
        "seeds": [
            ("Privacy Policy", "https://www.nike.in/cp/privacy-policy"),
            ("Contact", "https://www.nike.in/help/a/contact-us"),
            ("Terms of Use", "https://www.nike.in/cp/terms-of-use"),
        ],
    },
    "myntra.com": {
        "name": "Myntra",
        "seeds": [
            ("Privacy Policy", "https://www.myntra.com/privacypolicy"),
            ("Legal", "https://www.myntra.com/legal"),
            ("Contact", "https://www.myntra.com/contact"),
            ("Help", "https://www.myntra.com/help"),
            ("Grievance", "https://www.myntra.com/grievance-redressal"),
        ],
    },
    "netflix.com": {
        "name": "Netflix",
        "seeds": [
            ("Privacy Statement", "https://www.netflix.com/privacy"),
            ("Privacy Help", "https://help.netflix.com/en/node/28092"),
            ("Privacy History", "https://help.netflix.com/en/legal/privacy/history"),
            ("Terms of Use", "https://help.netflix.com/legal/termsofuse"),
        ],
    },
    "flipkart.com": {
        "name": "Flipkart",
        "seeds": [
            ("Privacy Policy", "https://www.flipkart.com/pages/privacypolicy"),
            ("Security", "https://www.flipkart.com/security"),
            ("Grievance Redressal", "https://www.flipkart.com/pages/grievance-redressal"),
            ("Terms of Use", "https://www.flipkart.com/pages/terms"),
            ("Help Centre", "https://www.flipkart.com/helpcentre"),
        ],
    },
}

def _host_key(url: str) -> str:
    host = (urlparse(url).netloc or "").lower().split(":", 1)[0]
    return host[4:] if host.startswith("www.") else host

def get_site_profile(url: str) -> dict | None:
    host = _host_key(url)
    for domain, profile in SITE_PROFILES.items():
        if host == domain or host.endswith("." + domain):
            return profile
    return None

def build_profile_queue(base_url: str) -> list[dict]:
    profile = get_site_profile(base_url)
    if not profile:
        return []
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    queue, seen = [], set()
    for name, target in profile["seeds"]:
        target_url = target if target.startswith(("http://", "https://")) else base + target
        normalized = target_url.rstrip("/")
        if normalized in seen:
            continue
        seen.add(normalized)
        queue.append({"name": name, "url": target_url, "depth": 1, "priority": 1000, "profile_seed": True})
    return queue
