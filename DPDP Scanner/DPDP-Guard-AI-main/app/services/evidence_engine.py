from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

from app.services.requirement_evidence_matrix import (
    get_assessment_elements,
    _topics_for_requirement as matrix_topics_for_requirement,
)


# ============================================================
# V22 EVIDENCE ENGINE
# ============================================================
#
# Goal:
#   1. Only search requirement-relevant fields.
#   2. Never derive evidence from generic requirement wording.
#   3. Reject obvious homepage/navigation/media noise.
#   4. Require semantic signals for evidence.
#   5. Preserve "insufficient evidence" when proof is absent.
#
# Evidence policy:
#   deterministic_element_evidence_v22
# ============================================================


# ------------------------------------------------------------
# Requirement -> assessment-element patterns (137 elements)
# ------------------------------------------------------------

ELEMENT_PATTERNS: Dict[str, List[str]] = {

    # -------------------------
    # 48-hour pre-erasure notice
    # -------------------------
    "48-hour pre-erasure notice": [
        r"\b48\s*(?:hours|hrs)\b.{0,100}\b(?:notice|notif|erase|erasure|delete)\b",
        r"\bnotice\b.{0,100}\b(?:prior\s+to|before)\s+(?:erasure|deletion)\b",
        r"\b48\s*hours\s+notice\b",
    ],

    # -------------------------
    # 72-hour period or permitted extension
    # -------------------------
    "72-hour period or permitted extension": [
        r"\b72\s*(?:hours|hrs)\b",
        r"\bseventy[-\s]?two\s+hours\b",
        r"\bwithin\s+72\s+hours\b",
    ],

    # -------------------------
    # DPIA / Audit
    # -------------------------
    "DPIA/audit report": [
        r"\b(?:DPIA|data\s+protection\s+impact\s+assessment)\s+report\b",
        r"\baudit\s+report\b",
    ],
    "DPO appointed": [
        r"\bappointed\s+(?:a\s+)?(?:DPO|data\s+protection\s+officer)\b",
        r"\bdata\s+protection\s+officer\s+(?:has\s+been\s+)?appointed\b",
    ],
    "DPO based in India": [
        r"\b(?:DPO|data\s+protection\s+officer)\b.{0,100}\b(?:based\s+in\s+India|resident\s+in\s+India|located\s+in\s+India|India)\b",
    ],
    "DPO contact if applicable or processing-questions contact": [
        r"\b(?:data\s+protection\s+officer|DPO|privacy\s+officer|grievance\s+officer)\b",
        r"\b(?:query|question|concern|complaint)\b.{0,100}\b(?:processing|personal\s+data|privacy)\b",
        r"\bcontact\s+(?:the\s+)?(?:DPO|privacy\s+team|grievance\s+officer)\b",
    ],
    "DPO is grievance contact": [
        r"\b(?:DPO|data\s+protection\s+officer)\b.{0,100}\b(?:grievance|complaint|redressal)\b",
        r"\bgrievance\s+officer\b",
    ],
    "DPO represents SDF": [
        r"\b(?:DPO|data\s+protection\s+officer)\b.{0,100}\b(?:represents|on\s+behalf\s+of)\b",
    ],
    "DPO responsible to Board or governing body": [
        r"\b(?:DPO|data\s+protection\s+officer)\b.{0,100}\b(?:governing\s+body|board\s+of\s+directors|management)\b",
    ],
    "Seventh Schedule applicability": [
        r"\bSeventh\s+Schedule\b",
        r"\bclass\s+of\s+data\s+fiduciaries\b",
    ],

    # -------------------------
    # Security
    # -------------------------
    "access control for computer resources": [
        r"\baccess\s+controls?\b",
        r"\brole[-\s]?based\s+access\b",
        r"\bauthori[sz]ed\s+(?:personnel|access|employees|users|agents|service\s+providers)\b",
        r"\bauthentication\s+and\s+authori[sz]ation\b",
        r"\bleast\s+privilege\b",
        r"\brestrict(?:ed)?\s+access\b",
        r"\baccess\s+to\s+(?:your\s+)?(?:personal\s+)?(?:data|information)\s+is\s+restricted\b",
        r"\bsecure\s+(?:login|access|server)\b",
        r"\bpassword\s+protect(?:ed|ion)\b",
        r"\bunauthori[sz]ed\s+access\b",
        r"\bprotect\s+(?:your\s+personal\s+data\s+)?from\s+unauthori[sz]ed\s+access\b",
        r"\bprotect\s+against\s+(?:any\s+)?hacking\s+or\s+(?:other\s+)?unauthori[sz]ed\s+access\b",
    ],
    "access logs": [
        '\\btraffic\\s+logs\\s+for\\s+all\\s+network\\s+devices\\b',
        '\\bmaintain\\s+and\\s+monitor\\s+traffic\\s+logs\\b',
        '\\brecord\\s+of\\s+computer\\s+identification\\s+names\\s+and\\s+corresponding\\s+IP\\b',
        r"\baccess\s+logs?\b",
        r"\baudit\s+logs?\b",
        r"\blog\s+(?:generation|recording|collection)\b",
        r"\bsecurity\s+logs?\b",
    ],
    "algorithmic software risk assessment": [
        r"\balgorithmic\b.{0,80}\brisk\b",
        r"\bautomated\s+decision[-\s]?making\s+risk\b",
    ],
    "annual DPIA": [
        r"\bannual\s+(?:DPIA|data\s+protection\s+impact\s+assessment)\b",
        r"\bperiodic\s+DPIA\b",
    ],
    "annual audit": [
        r"\bannual\s+(?:data\s+)?audit\b",
        r"\bperiodic\s+compliance\s+audit\b",
    ],
    "applicable Third Schedule class/purpose": [
        '\\bacademic\\s+(?:and|or)\\s+official\\s+purposes?\\b',
        '\\bvideo\\s+data\\b',
        '\\bcctv\\b',
        r"\bThird\s+Schedule\b",
        r"\bspecified\s+purpose\s+completed\b",
    ],
    "appropriate backups": [
        r"\bbackup(?:s)?\s+(?:and\s+recovery|procedures|systems)?\b",
        r"\bdata\s+backups?\b",
        r"\bbackup\s+copies\b",
        r"\bdisaster\s+recovery\b",
        r"\bremediate\s+and\s+recover\s+from\s+information\s+security\s+breach\b",
        r"\brecover\s+from\s+(?:information\s+)?security\s+breach\b",
    ],

    # -------------------------
    # Breach
    # -------------------------
    "breach consequences": [
        '\\bresults?\\s+in\\s+damaged\\s+or\\s+lost\\s+files\\b',
        '\\binoperable\\s+computer\\s+resulting\\s+in\\s+loss\\s+of\\s+productivity\\b',
        r"\bconsequences\s+of\s+(?:the\s+)?(?:breach|incident)\b",
        r"\bimpact\s+of\s+(?:the\s+)?(?:breach|incident)\b",
        r"\bnature\s+and\s+extent\s+of\s+(?:the\s+)?breach\b",
    ],
    "breach intimation to Board where required": [
        '\\bcopy\\s+of\\s+the\\s+notification\\s+will\\s+be\\s+sent\\s+to\\s+the\\s+Institution\\s+Administration\\b',
        '\\bwork\\s+with\\s+academic\\s+or\\s+administrative\\s+departments\\s+and\\s+law\\s+enforcement\\b',
        '\\bintimation\\s+to\\s+the\\s+Board\\b',
        r"\bnotify\s+(?:the\s+)?(?:Data\s+Protection\s+)?Board\b",
        r"\bintimat(?:e|ion)\s+to\s+(?:the\s+)?(?:Data\s+Protection\s+)?Board\b",
        r"\breport\s+(?:the\s+)?breach\s+to\s+(?:the\s+)?Board\b",
    ],
    "breach intimation to affected data principals": [
        '\\bnotify\\s+the\\s+individual\\s+responsible\\b',
        '\\bnotification\\s+will\\s+be\\s+done\\s+via\\s+email/telephone\\b',
        '\\breport\\s+the\\s+issue\\s+to\\s+the\\s+concern\\s+team\\b',
        '\\balleged\\s+security\\s+incident\\b',
        r"\bnotify\s+(?:affected\s+)?(?:data\s+principals|users|customers|individuals)\b",
        r"\bintimat(?:e|ion)\s+to\s+(?:affected\s+)?(?:data\s+principals|users|individuals)\b",
        r"\binform\s+affected\s+(?:users|customers|individuals|data\s+principals)\b",
        r"\bnotify\s+you\s+(?:in\s+the\s+event\s+of|upon|following)\s+(?:a\s+)?(?:security\s+)?(?:breach|incident)\b",
        r"\bnotify\s+(?:you|users)\b.{0,40}\b(?:security\s+)?(?:breach|incident)\b",
        r"\bbreach\s+notification\b",
        r"\bincidents?\s+of\s+(?:information\s+)?security\s+breach\b",
        r"\bsecurity\s+breach\s+incidents?\b",
        r"\bincident\s+response\s+team\b",
        r"\btackle\s+incidents\s+of\s+(?:information\s+)?security\s+breach\b",
        r"\brecover\s+from\s+(?:information\s+)?security\s+breach\b",
    ],
    "business contact information": [
        '\\binfo@skcet\\.ac\\.in\\b',
        '\\bprincipal@skcet\\.ac\\.in\\b',
        '\\bhelpdesk@skcet\\.ac\\.in\\b',
        '\\bgrievances@skcet\\.ac\\.in\\b',
        r"\bcontact\s+(?:us|information|details)\b",
        r"\bemail\s*:\s*[\w\.-]+@[\w\.-]+\.\w+\b",
        r"\bphone\s*:\s*[\+\d\s\(\)-]{7,}\b",
        r"\bregistered\s+office\b",
        r"\bcorporate\s+office\b",
        r"\bpostal\s+address\b",
    ],
    "business continuity": [
        '\\bminimum\\s+inconvenience\\s+due\\s+to\\s+interruption\\s+of\\s+services\\b',
        '\\bcontinuous\\s+power\\s+supply\\b',
        '\\breliable\\s+network\\s+connectivity\\b',
        '\\bcontinued\\s+support\\b',
        r"\bbusiness\s+continuity\b",
        r"\bdisaster\s+recovery\b",
        r"\boperational\s+resilience\b",
    ],

    # -------------------------
    # Consent
    # -------------------------
    "clear affirmative action": [
        '\\bsubmit\\b',
        '\\bregister\\b',
        '\\bonline\\s+payment\\b',
        '\\baffirmative\\s+action\\b',
        '\\bapplication\\s+form\\b',
        r"\baffirmative\s+action\b",
        r"\bclear\s+affirmative\b",
        r"\bI\s+agree\b",
        r"\bI\s+accept\b",
        r"\bI\s+consent\b",
        r"\bexplicitly\s+consent\b",
        r"\bcheckbox\b",
        r"\baccept\s+(?:the|all)?\s*(?:terms|privacy|cookies)\b",
    ],
    "clear/plain language": [
        '\\bGeneral\\s+Guidelines\\b',
        '\\bplain\\s+language\\b',
        r"\bclear\s+and\s+plain\s+language\b",
        r"\bplain\s+language\b",
        r"\beasily\s+understandable\b",
    ],
    "communication link": [
        r"\b(?:href|link|url|click\s+here|visit)\b.{0,80}\b(?:contact|privacy|grievance|rights)\b",
        r"\bhttps?://[^\s]+\b",
    ],
    "completeness": [
        '\\bcomplete\\s+information\\b',
        '\\bcomprehensive\\s+warranty\\b',
        '\\bcurriculum\\s+feedback\\b',
        r"\bcompleteness\b",
        r"\bcomplete\s+and\s+accurate\b",
        r"\bkeep\s+(?:your\s+)?information\s+complete\b",
    ],
    "compliance with applicable restriction": [
        '\\bavert\\s+spoofing\\s+of\\s+internal\\s+network\\s+addresses\\s+from\\s+the\\s+Internet\\b',
        '\\bprotect\\s+external\\s+Internet\\s+sites\\b',
        '\\bdeny\\s+all\\s+external\\s+Internet\\s+traffic\\b',
        r"\bcompliance\s+with\s+(?:applicable\s+)?(?:laws|restrictions|regulations)\b",
        r"\bstatutory\s+compliance\b",
    ],
    "consent or legitimate use": [
        '\\bagreeing\\s+to\\s+abide\\s+by\\b',
        '\\buser\\s+consent\\b',
        '\\bconsent\\s+to\\b',
        '\\bexplicitly\\s+consent\\b',
        '\\blegitimate\\s+(?:purpose|interest|educational|academic|use)\\b',
        '\\buse\\s+of\\s+normal\\s+institution\\b',
        '\\bregulations\\s+and\\s+curriculum\\b',
        r"\b(?:explicit\s+)?consent\b",
        r"\blegitimate\s+use(?:s)?\b",
        r"\blawful\s+(?:basis|purpose|grounds)\b",
        r"\bconsent\s+to\s+process\b",
    ],
    "consent request is clear": [
        '\\bclear\\s+and\\s+plain\\b',
        '\\bclear\\s+instructions\\b',
        '\\bgeneral\\s+guidelines\\b',
        r"\bclear\s+(?:and\s+concise|notice|request)\b",
        r"\bconsent\s+request\b",
        r"\bclearly\s+state(?:s|d)?\b",
    ],
    "consent request is plain": [
        '\\bplain\\s+language\\b',
        '\\bgeneral\\s+guidelines\\b',
        r"\bplain\s+language\b",
        r"\bsimple\s+language\b",
        r"\beasily\s+understood\b",
    ],
    "consent request is standalone from unrelated purposes": [
        '\\bseparat(?:e|ed)\\b',
        '\\bdistinct\\b',
        '\\bstandalone\\b',
        '\\bstudent\\s+grievance\\s+form\\b',
        r"\bstandalone\s+(?:consent|notice)\b",
        r"\bseparate\s+(?:consent|checkbox|opt[-\s]?in)\b",
        r"\bnot\s+bundled\b",
    ],
    "consistency where relevant": [
        '\\bconsistent\\b',
        '\\bstandardi[sz]ed\\s+a\\s+series\\b',
        '\\bcorresponding\\s+IP\\s+address\\b',
        r"\bconsistent\b",
        r"\bconsistency\b",
        r"\bdata\s+consistency\b",
    ],
    "contract addresses required obligations": [
        '\\bannual\\s+maintenance\\s+contract\\b',
        '\\bagreement\\s+for\\s+continued\\s+support\\b',
        '\\bcontract\\s+with\\s+an\\s+outsider\\b',
        '\\bunder\\s+contract\\b',
        r"\bcontractual\s+obligations\b",
        r"\bdata\s+processing\s+agreement\b",
        r"\bbinding\s+contract\b",
    ],
    "data audit carried out": [
        r"\bdata\s+audit\b",
        r"\bcompliance\s+audit\b",
        r"\bexternal\s+audit\b",
    ],
    "data fiduciary remains responsible for processing": [
        '\\bSKCET\\s+has\\s+a\\s+legal\\s+responsibility\\b',
        '\\blegal\\s+responsibility\\s+to\\s+secure\\b',
        '\\binstitution\\s+is\\s+responsible\\b',
        '\\bperson\\s+responsible\\s+for\\s+compliance\\b',
        '\\badmin\\s+department\\b.{0,40}\\bresponsible\\b',
        r"\bresponsible\s+for\s+(?:the\s+)?processing\b",
        r"\bresponsibility\s+for\s+personal\s+data\b",
        r"\bdata\s+fiduciary\b",
        r"\binformation\s+under\s+our\s+control\b",
        r"\bprotect\s+(?:your\s+)?(?:personal\s+)?(?:data|information)\s+under\s+our\s+control\b",
        r"\bbig\s+responsibility\s+and\s+work\s+hard\s+to\s+protect\b",
        r"\bfollow\s+this\s+privacy\s+policy\s+with\s+respect\s+to\s+your\s+personal\s+data\b",
        r"\brequired\s+to\s+follow\s+this\s+privacy\s+policy\b",
    ],
    "data limited to what is necessary": [
        '\\bonly\\s+when\\s+it\\s+is\\s+absolutely\\s+required\\b',
        '\\bstrictly\\s+through\\b',
        '\\blimited\\s+to\\s+(?:what\\s+is\\s+)?necessary\\b',
        r"\bnecessary\s+(?:personal\s+)?data\b",
        r"\bdata\s+minimisation\b",
        r"\bdata\s+minimization\b",
        r"\bonly\s+(?:the\s+)?data\s+(?:necessary|required)\b",
        r"\bno\s+more\s+data\s+than\s+necessary\b",
    ],
    "detect unauthorised access": [
        '\\bavert\\s+spoofing\\b',
        '\\binspect\\s+any\\s+unauthorized\\s+access\\b',
        '\\bdeny\\s+all\\s+external\\s+Internet\\s+traffic\\b',
        r"\bdetect\s+(?:and\s+prevent\s+)?unauthori[sz]ed\s+access\b",
        r"\bdetect\s+(?:and\s+protect\s+against\s+)?(?:fraud|error|intrusion|security\s+incident)\b",
        r"\bdetect\s+breach\b",
    ],
    "due diligence on technical measures": [
        r"\bdue\s+diligence\b.{0,60}\btechnical\s+measures\b",
        r"\breview\s+(?:of\s+)?security\s+measures\b",
    ],
    "due diligence verification": [
        r"\bdue\s+diligence\b",
        r"\bverification\s+procedure\b",
    ],
    "encryption or appropriate equivalent protection": [
        r"\bencryption\b",
        r"\bencrypted\b",
        r"\bTLS\b",
        r"\bSSL\b",
        r"\bsecure\s+server\b",
        r"\bencryption\s+(?:at\s+rest|in\s+transit)\b",
    ],
    "erasure after purpose completion": [
        '\\bstored\\s+for\\s+1\\s+month\\b',
        '\\breleasing\\s+the\\s+disk\\s+space\\s+on\\s+the\\s+server\\b',
        '\\bclearing\\s+the\\s+junks\\b',
        r"\bdelete\s+(?:your\s+data\s+)?(?:once|when|after)\s+(?:the\s+)?purpose\s+is\s+(?:completed|served|achieved)\b",
        r"\bno\s+longer\s+required\s+for\s+the\s+purpose\b",
        r"\berase\s+upon\s+completion\b",
    ],
    "erasure after withdrawal": [
        '\\bdisconnection\\s+from\\s+the\\s+institution\\s+network\\b',
        '\\breleasing\\s+the\\s+disk\\s+space\\b',
        '\\bclearing\\s+the\\s+junks\\s+and\\s+cache\\b',
        r"\bdelete\s+(?:your\s+data\s+)?(?:upon|following|after)\s+withdrawal\b",
        r"\berasure\s+after\s+withdrawing\s+consent\b",
    ],
    "erasure when principal neither approaches nor exercises rights": [
        '\\bstored\\s+for\\s+1\\s+month\\b',
        '\\breleasing\\s+the\\s+disk\\s+space\\b',
        r"\bperiod\s+of\s+(?:inactivity|no\s+access)\b",
        r"\bnot\s+accessed\b.{0,60}\b(?:deleted|erased)\b",
        r"\berasure\s+due\s+to\s+inactivity\b",
    ],
    "exception for applicable law": [
        '\\bmonitoring\\s+required\\s+by\\s+law\\s+enforcement\\b',
        '\\bapplicable\\s+law\\b',
        r"\bexcept\s+(?:as|where)\s+required\s+by\s+law\b",
        r"\blegal\s+obligation\s+to\s+retain\b",
        r"\bapplicable\s+statutory\s+or\s+regulatory\s+retention\b",
        r"\bapplicable\s+law\b",
    ],
    "free consent": [
        '\\bvoluntary\\b',
        '\\bstudents\\s+and\\s+faculty\\s+members\\s+are\\s+encouraged\\b',
        '\\bfreely\\s+given\\b',
        r"\bfree\s+consent\b",
        r"\bfreely\s+given\b",
        r"\bvoluntary\b",
        r"\bchoice\s+to\s+decide\b",
    ],
    "government cross-border restriction applies": [
        '\\bhosted\\s+in\\s+G-Suite\\b',
        '\\bdeny\\s+all\\s+external\\s+Internet\\s+traffic\\b',
        r"\bcross[-\s]?border\b",
        r"\btransfer\s+outside\s+India\b",
        r"\bservers\s+located\s+outside\s+of\s+India\b",
        r"\binternational\s+transfer\b",
    ],
    "government-specified localisation restriction applies": [
        r"\bdata\s+locali[sz]ation\b",
        r"\bstore\s+data\s+in\s+India\b",
        r"\bstored\s+in\s+India\b",
    ],
    "grievance mechanism": [
        r"\bgrievance\s+officer\b",
        r"\bgrievance\s+redressal\b",
        r"\bgrievance\s+redressal\s+mechanism\b",
        r"\bcomplaint\s+(?:escalation|resolution|redressal)\b",
    ],
    "grievance response within prescribed period": [
        '\\btimely\\s+and\\s+effective\\s+manner\\b',
        '\\btime[-\\s]?bound\\s+platform\\b',
        '\\baddressing\\s+and\\s+resolving\\s+grievances\\b',
        '\\bterm\\s+of\\s+three\\s+years\\b',
        '\\bescalation\\s+procedure\\b',
        r"\bwithin\s+(?:\d+\s+hours|\d+\s+days)\b",
        r"\bwithin\s+the\s+timeline\s+as\s+prescribed\b",
        r"\b48\s*hours\b.{0,60}\btrack\s+the\s+grievance\b",
        r"\bwithin\s+reasonable\s+period\b",
        r"\b90\s+days\b",
    ],
    "guardian appointed by lawful authority": [
        r"\blawful\s+guardian\b",
        r"\blegal\s+guardian\b",
        r"\bguardian\s+appointed\s+by\b",
    ],
    "independent data auditor appointed": [
        r"\bindependent\s+(?:data\s+)?auditor\b",
        r"\bexternal\s+auditor\b",
    ],
    "informed consent": [
        '\\busers\\s+may\\s+be\\s+aware\\s+that\\s+by\\s+using\\b',
        '\\bofficial\\s+notices\\s+from\\s+the\\s+institution\\b',
        '\\binformed\\s+consent\\b',
        r"\binformed\s+consent\b",
        r"\bprivacy\s+policy\b",
        r"\bprivacy\s+notice\b",
        r"\bexplicitly\s+consent\s+to\s+adhere\b",
    ],
    "investigate unauthorised access": [
        '\\bcopy\\s+or\\s+examine\\s+files\\s+and\\s+information\\s+resident\\s+on\\s+institution\\s+systems\\s+related\\s+to\\s+any\\s+alleged\\s+security\\s+incident\\b',
        '\\bwork\\s+with\\s+academic\\s+or\\s+administrative\\s+departments\\s+and\\s+law\\s+enforcement\\b',
        r"\binvestigate\s+unauthori[sz]ed\s+access\b",
        r"\binvestigate\s+(?:security\s+)?incidents?\b",
        r"\bincident\s+response\s+team\b",
    ],
    "itemised personal data description": [
        '\\b(?:Name|Aadhaar|Email|Mobile|Roll\\s+No|Gender)\\b',
        '\\bitemised\\b',
        r"\bpersonal\s+data\s+(?:we\s+collect|includes|collected)\b",
        r"\bidentifying\s+information\s+like\b",
        r"\bcategories\s+of\s+personal\s+data\b",
        r"\bname,\s*date\s+of\s+birth\b",
        r"\btypes\s+of\s+(?:personal\s+)?data\b",
    ],
    "lawful guardian consent applies": [
        r"\bparent\s+or\s+guardian\b",
        r"\bguardian\s+consent\b",
        r"\bauthority\s+to\s+do\s+so\s+and\s+permit\s+us\b",
    ],
    "lawful purpose": [
        '\\bprimarily\\s+for\\s+(?:academic|official)\\s+purposes?\\b',
        '\\blegal\\s+responsibility\\b',
        '\\bstatutory\\s+(?:compliance|bodies|regulations?)\\b',
        '\\bpurposes?\\s+(?:permitted|authorized|required)\\s+by\\s+law\\b',
        '\\bAICTE\\s+regulations?\\b',
        '\\bdirectives\\s+of\\s+(?:the\\s+)?(?:UGC|AICTE)\\b',
        '\\bofficial\\s+purposes?\\b',
        '\\bnormal\\s+institution\\s+or\\s+student\\s+operations\\b',
        r"\blawful\s+purpose\b",
        r"\blegal\s+obligation\b",
        r"\bapplicable\s+laws\b",
        r"\bpurpose\s+of\s+(?:processing|collection|use)\b",
    ],
    "lawful retention exception": [
        '\\bmonitoring\\s+required\\s+by\\s+law\\s+enforcement\\b',
        '\\bwith\\s+appropriate\\s+management\\s+request\\b',
        '\\bretention\\s+exception\\b',
        r"\blegal\s+obligation\s+to\s+retain\b",
        r"\bstatutory\s+or\s+regulatory\s+retention\b",
        r"\blawful\s+retention\b",
        r"\brequired\s+under\s+any\s+applicable\s+law\b",
    ],
    "login/contact/rights exception": [
        r"\blogin\b.{0,60}\bexception\b",
        r"\bexercis(?:ing|e)\s+rights\b.{0,60}\bexception\b",
        r"\bcontact\s+exception\b",
    ],
    "means for completion": [
        '\\bcurriculum\\s+feedback\\b',
        '\\bcreating\\s+and\\s+updating\\b',
        '\\bcompletion\\b',
        r"\bcomplete\s+(?:your\s+)?personal\s+data\b",
        r"\bcompletion\s+of\s+personal\s+data\b",
        r"\bedit\s+or\s+update\s+your\s+personal\s+data\b",
    ],
    "means for correction": [
        '\\bcurriculum\\s+feedback\\b',
        '\\bcreating\\s+and\\s+updating\\s+the\\s+content\\b',
        '\\battend\\s+the\\s+complaints\\s+related\\s+to\\s+any\\s+maintenance\\b',
        '\\bcorrect\\b',
        r"\bcorrect\s+(?:your\s+)?personal\s+data\b",
        r"\bcorrection\b",
        r"\bedit\s+or\s+update\b",
        r"\bupdate\s+your\s+personal\s+data\b",
    ],
    "means for erasure": [
        '\\breleasing\\s+the\\s+disk\\s+space\\b',
        '\\bclearing\\s+the\\s+junks\\s+and\\s+cache\\b',
        "\\bvideo\\s+data['’]?s\\s+are\\s+stored\\s+for\\s+1\\s+month\\b",
        r"\bdelete\s+(?:your\s+)?(?:account|personal\s+data|data)\b",
        r"\bdeletion\s+of\s+your\s+account\b",
        r"\berase\s+(?:your\s+)?personal\s+data\b",
        r"\bright\s+to\s+(?:erasure|delete)\b",
    ],
    "means for updating": [
        '\\bcreating\\s+and\\s+updating\\s+the\\s+content\\b',
        '\\bupdating\\s+of\\s+the\\s+OS\\b',
        '\\bupdating\\b',
        r"\bupdate\s+(?:your\s+)?personal\s+data\b",
        r"\bedit\s+or\s+update\b",
        r"\bkeep\s+(?:your\s+)?data\s+up\s+to\s+date\b",
    ],
    "means to complain to Board": [
        r"\bcomplaint\s+to\s+(?:the\s+)?(?:Data\s+Protection\s+)?Board\b",
        r"\bapproach\s+(?:the\s+)?Board\b",
        r"\bdata\s+protection\s+board\b",
    ],
    "means to exercise rights": [
        '\\bgrievance\\s+(?:registration\\s+)?portal\\b',
        '\\bonline\\s+grievance\\s+redressal\\b',
        '\\bregister\\s+(?:their\\s+)?grievances\\s+through\\s+the\\s+link\\b',
        '\\bhelp\\s+desk\\b',
        '\\bescalation\\s+procedure\\b',
        '\\bcurriculum\\s+feedback\\b',
        "\\bparent['’]?s\\s+feedback\\b",
        r"\bexercise\s+(?:your\s+)?rights\b",
        r"\bprivacy\s+centre\b",
        r"\bprivacy\s+center\b",
        r"\bself[-\s]?serve\s+portal\b",
        r"\bmanage\s+your\s+data\b",
    ],
    "means to make a complaint to the Board": [
        '\\bOmbuds(?:man|person)\\b',
        '\\bcomplaint\\s+cell\\b',
        '\\bCaste\\s+Discrimination\\s+Complaint\\s+Cell\\b',
        '\\bData\\s+Protection\\s+Board\\b',
        '\\bstatutory\\s+authority\\b',
        r"\bcomplaint\s+to\s+(?:the\s+)?(?:Data\s+Protection\s+)?Board\b",
        r"\bmake\s+a\s+complaint\s+to\s+the\s+board\b",
    ],
    "means to raise grievances": [
        r"\bcontact\s+(?:our\s+)?grievance\s+officer\b",
        r"\bquery,\s*concern,\s*or\s*complaint\b",
        r"\bcustomergrievance@[\w\.-]+\.\w+\b",
        r"\bhelp\s+center\b.{0,60}\bcontact\s+us\b",
        r"\bgrievance\s+redressal\b",
    ],
    "means to withdraw consent": [
        '\\bwithdrawal\\s+of\\s+the\\s+facility\\b',
        '\\bwithdraw\\s+consent\\b',
        '\\bdisconnect\\s+any\\s+system\\b',
        r"\bwithdraw\s+(?:your\s+)?consent\b",
        r"\bwithdrawal\s+of\s+consent\b",
        r"\bopt[-\s]?out\b",
        r"\bunsubscribe\b",
        r"\bdecline\s+(?:our\s+)?cookies\b",
    ],
    "mitigation measures": [
        '\\bsubject\\s+to\\s+immediate\\s+disconnection\\b',
        '\\bbrought\\s+into\\s+compliance\\b',
        r"\bmitigat(?:e|ion)\s+measures\b",
        r"\bcontain(?:ment)?\s+and\s+mitigat(?:e|ion)\b",
        r"\bremediat(?:e|ion)\b",
    ],
    "monitoring": [
        r"\bmonitoring\b",
        r"\bsecurity\s+monitoring\b",
        r"\baudit\s+trail\b",
        r"\bcontinuous\s+monitoring\b",
    ],
    "no child behavioural monitoring": [
        '\\brefrain\\s+from\\s+intercepting\\b',
        '\\binfringing\\s+the\\s+privacy\\b',
        '\\bno\\s+behavioural\\s+monitoring\\b',
        r"\bbehaviou?ral\s+(?:monitoring|tracking)\s+of\s+children\b",
        r"\bdo\s+not\s+(?:knowingly\s+)?collect\b.{0,60}\bchildren\b",
        r"\bavailable\s+only\s+to\s+persons\s+who\s+can\s+form\s+a\s+legally\s+binding\s+contract\b",
    ],
    "no child tracking": [
        '\\brefrain\\s+from\\s+intercepting,?\\s+or\\s+trying\\s+to\\s+break\\s+into\\s+others\\s+email\\b',
        '\\binfringing\\s+the\\s+privacy\\s+of\\s+other\\s+users\\b',
        '\\bno\\s+child\\s+tracking\\b',
        r"\btrack(?:ing)?\s+of\s+children\b",
        r"\bdo\s+not\s+(?:knowingly\s+)?solicit\s+or\s+collect\s+personal\s+data\s+from\s+children\b",
    ],
    "no processing likely to cause detrimental effect on child well-being": [
        '\\bAnti-Ragging\\s+Committee\\b',
        '\\bAnti-Ragging\\s+Squad\\b',
        '\\bInternal\\s+Compliance\\s+Committee\\b',
        '\\bGender\\s+equality\\s+and\\s+equity\\b',
        '\\bhealthy,?\\s+respectful\\s+and\\s+inclusive\\s+environment\\b',
        '\\bshall\\s+not\\s+to\\s+be\\s+used\\s+for\\s+the\\s+creation\\s+or\\s+distribution\\s+of\\s+any\\s+offensive\\s+messages\\b',
        '\\binfringing\\s+the\\s+privacy\\b',
        r"\bdetrimental\s+effect\s+on\s+child\b",
        r"\bwell[-\s]?being\s+of\s+children\b",
        r"\bprotect\s+children\b",
        r"\bnot\s+knowingly\s+(?:solicit\s+or\s+)?collect\s+(?:personal\s+data\s+from\s+)?children\b",
        r"\bchildren\s+under\s+(?:the\s+age\s+of\s+)?18\b",
        r"\bonly\s+to\s+persons\s+who\s+can\s+form\s+a\s+legally\s+binding\s+contract\b",
        r"\bnot\s+intended\s+for\s+children\b",
        r"\bdo\s+not\s+target\s+children\b",
    ],
    "no targeted advertising directed at children": [
        '\\bcommercial\\s+purposes\\s+is\\s+a\\s+direct\\s+violation\\b',
        '\\bunsolicited\\s+bulk\\s+e-mail\\b',
        '\\bno\\s+targeted\\s+advertising\\b',
        r"\btargeted\s+advertising\s+(?:to|directed\s+at)\s+children\b",
        r"\bdo\s+not\s+(?:knowingly\s+)?(?:solicit|collect)\b.{0,60}\bunder\s+the\s+age\s+of\s+18\b",
    ],
    "notice accessible in English": [
        r"\bEnglish\b",
        r"\bEnglish\s+version\b",
    ],
    "notice accessible in an Eighth Schedule language": [
        r"\b(?:Hindi|Bengali|Gujarati|Kannada|Malayalam|Marathi|Punjabi|Tamil|Telugu|Urdu|Eighth\s+Schedule)\b",
        r"\btranslations?\s+provided\b",
        r"\bselect\s+language\b",
    ],
    "notice explains upcoming erasure": [
        r"\bnotice\s+(?:explaining|regarding)\s+(?:upcoming\s+)?erasure\b",
        r"\binform\s+of\s+scheduled\s+erasure\b",
    ],
    "notice is independently understandable": [
        '\\bInformation\\s+Network\\s+Security\\s+Policy\\b',
        '\\bGeneral\\s+Guidelines\\b',
        '\\bindependently\\s+understandable\\b',
        r"\bindependently\s+understandable\b",
        r"\bstand-?alone\s+from\s+terms\b",
        r"\bclear\s+and\s+plain\b",
    ],
    "notice is standalone": [
        '\\bPage:\\s+IT\\s+Policy\\b',
        '\\bTitle:\\s+IT\\s+Policy\\b',
        '\\bMANDATORY\\s+DISCLOSURES\\b',
        '\\bstandalone\\b',
        r"\bPrivacy\s+Policy\b",
        r"\bPrivacy\s+Notice\b",
        r"\bstandalone\s+notice\b",
    ],
    "notice to Board without delay": [
        r"\bnotify\s+the\s+Board\s+without\s+(?:undue\s+)?delay\b",
        r"\breport\s+to\s+the\s+Board\s+without\s+delay\b",
    ],
    "notice to affected Data Principals without delay": [
        '\\bnotify\\s+the\\s+individual\\s+responsible\\b',
        '\\bnotification\\s+will\\s+be\\s+done\\s+via\\s+email/telephone\\b',
        r"\bnotify\s+affected\s+(?:individuals|data\s+principals)\s+without\s+(?:undue\s+)?delay\b",
        r"\bprompt\s+notification\s+to\s+affected\b",
    ],
    "obfuscation/masking/virtual tokens where appropriate": [
        r"\bmasking\b",
        r"\bobfuscation\b",
        r"\bvirtual\s+tokens?\b",
        r"\btokeni[sz]ation\b",
        r"\banonymi[sz]ed\b",
    ],
    "organisational measures": [
        '\\bGOVERNING\\s+BODY\\b',
        '\\bOrganizational\\s+Chart\\b',
        '\\bInternal\\s+Compliance\\s+Committee\\b',
        '\\bAnti-Ragging\\s+Committee\\b',
        '\\bEqual\\s+Opportunity\\s+Facilities\\s+Cell\\b',
        '\\bInternal\\s+Quality\\s+Assurance\\s+Cell\\b',
        '\\bTechnical\\s+team\\b',
        '\\bpolicy\\s+enforcement\\b',
        '\\badministrative\\s+controls\\b',
        r"\borgani[sz]ational\s+measures\b",
        r"\bpolicies\s+and\s+procedures\b",
        r"\btraining\s+and\s+governance\b",
        r"\bsecurity\s+practices\s+and\s+procedures\b",
        r"\badministrative\s+(?:controls|safeguards|measures)\b",
        r"\binternal\s+(?:security\s+)?policies\b",
    ],
    "organisational security measures": [
        '\\bSKCET\\s+technical\\s+team\\b',
        '\\bInformation\\s+Network\\s+Security\\s+Policy\\b',
        '\\bInstitution\\s+Administration\\b',
        '\\bresponsibility\\s+of\\s+all\\s+SKCET\\s+users\\b',
        r"\borgani[sz]ational\s+security\s+measures\b",
        r"\bsecurity\s+practices\s+and\s+procedures\b",
        r"\bindustry\s+standard\s+security\s+measures\b",
    ],
    "parent identified as identifiable adult": [
        '\\bMr\\.\\s+[A-Za-z\\s]+Parent\\b',
        '\\bParent\\s+\\(Male\\)\\b',
        '\\bidentifiable\\s+adult\\b',
        r"\bidentifiable\s+adult\b",
        r"\bidentity\s+of\s+parent\b",
        r"\bparent\s+or\s+guardian\b",
    ],
    "parental consent before processing children data": [
        "\\bParent['’]?s\\s+Feedback\\b",
        '\\bParent\\s+\\(Male\\)\\b',
        '\\bparental\\s+consent\\b',
        r"\bparental\s+consent\b",
        r"\bconsent\s+of\s+(?:a\s+)?parent\s+or\s+guardian\b",
        r"\bunder\s+the\s+age\s+of\s+18\b.{0,60}\bauthority\s+to\s+do\s+so\b",
    ],
    "period not exceeding 90 days": [
        '\\btimely\\s+and\\s+effective\\b',
        '\\btime[-\\s]?bound\\b',
        '\\bterm\\s+of\\s+three\\s+years\\b',
        r"\b90\s+days\b",
        r"\bninety\s+days\b",
        r"\bwithin\s+90\s+days\b",
    ],
    "periodic DPIA undertaken": [
        r"\bperiodic\s+DPIA\b",
        r"\bperiodic\s+data\s+protection\s+impact\b",
    ],
    "periodic compliance audit undertaken": [
        r"\bperiodic\s+compliance\s+audit\b",
        r"\baudit\s+carried\s+out\s+periodically\b",
    ],
    "personal data proposed to be processed": [
        '\\b(?:Aadhaar|Name|Email|Mobile|Phone|Roll\\s+No|Gender|Department)\\b',
        '\\bpersonal\\s+data\\s+(?:collected|proposed|to\\s+be\\s+processed)\\b',
        '\\bdata\\s+collection\\b',
        '\\bstudent\\s+(?:grievance|registration|admission)\\s+form\\b',
        r"\bpersonal\s+data\s+(?:we\s+collect|processed|proposed\s+to\s+be\s+processed)\b",
        r"\binformation\s+we\s+collect\b",
        r"\bcollect\s+basic\s+identifying\s+information\b",
    ],
    "personal data retention one year": [
        r"\bretention\s+(?:for\s+)?(?:at\s+least\s+)?(?:one|1)\s+year\b",
        r"\bperiod\s+of\s+(?:one|1)\s+year\b",
        r"\b12\s+months\b",
    ],
    "pre-Act consent exists or is applicable": [
        r"\bpre-Act\s+consent\b",
        r"\bconsent\s+obtained\s+prior\s+to\b",
        r"\bexisting\s+users?\b",
    ],
    "prescribed detailed information": [
        r"\bprescribed\s+(?:detailed\s+)?information\b",
        r"\bform\s+and\s+manner\b",
    ],
    "prescribed personal-data information can be obtained": [
        '\\bMANDATORY\\s+DISCLOSURES\\b',
        '\\bonline\\s+grievance\\s+redressal\\s+mechanism\\b',
        '\\bhall\\s+ticket\\b',
        '\\btimetable\\b',
        '\\bresults\\b',
        '\\bfee\\s+\\(as\\s+approved\\s+by\\s+the\\s+state\\s+government\\)\\b',
        r"\brequest\s+a\s+copy\s+of\s+your\s+personal\s+data\b",
        r"\bcopy\s+of\s+your\s+personal\s+data\s+held\s+by\s+us\b",
        r"\baccess\s+your\s+personal\s+data\b",
    ],
    "processing ceases after withdrawal": [
        '\\bdisconnection\\s+from\\s+the\\s+institution\\s+network\\b',
        '\\bcease\\s+processing\\b',
        '\\bpromptly\\s+closed\\b',
        '\\bdisconnect\\s+any\\s+system\\b',
        r"\bcease\s+(?:processing|to\s+process)\b",
        r"\bstop\s+processing\b",
        r"\bno\s+longer\s+process\s+your\s+data\b",
    ],
    "processing contact information is published": [
        r"\bcontact\s+(?:us|information|details)\b",
        r"\bemail\s*:\s*[\w\.-]+@[\w\.-]+\.\w+\b",
        r"\bcontact\s+our\s+customer\s+support\b",
    ],
    "processing log retention one year": [
        r"\bprocessing\s+logs?\b.{0,60}\b(?:one|1)\s+year\b",
        r"\blogs?\s+retained\s+for\s+one\s+year\b",
    ],
    "processing/personal-data retention for one year": [
        '\\bstored\\s+for\\s+1\\s+month\\b',
        '\\blifetime\\s+mail\\s+ID\\b',
        r"\bretention\s+(?:of\s+personal\s+data\s+)?for\s+(?:one|1)\s+year\b",
        r"\bretain\b.{0,60}\b(?:one|1)\s+year\b",
    ],
    "processor contract exists where processing is delegated": [
        '\\bcontract\\s+with\\s+an\\s+outsider\\b',
        '\\bhosted\\s+in\\s+G-Suite\\b',
        '\\bannual\\s+maintenance\\s+contract\\s+either\\s+with\\s+a\\s+third\\s+party\\b',
        '\\bWebsite\\s+Partner\\s+ColorWhistle\\b',
        '\\boutsourc(?:ed?|ing)\\b',
        r"\bdata\s+processor\b",
        r"\bprocessor\s+contract\b",
        r"\bthird[-\s]?party\s+(?:processors?|partners|service\s+providers)\b.{0,60}\bcontract\b",
        r"\bcontracts?\s+with\s+(?:third\s+parties|service\s+providers|vendors)\b",
        r"\bcontractually\s+(?:bound|obligated|required)\b",
    ],
    "processor contract security safeguards where applicable": [
        r"\bprocessors?\b.{0,80}\bsecurity\s+safeguards\b",
        r"\bcontractual\s+security\b",
        r"\bcontractually\s+(?:bound|obligated|required)\b",
        r"\bcontractual\s+(?:obligations|agreements?|arrangements?)\b.{0,60}\b(?:security|confidentiality)\b",
        r"\bthird[-\s]?party\s+(?:service\s+providers|vendors|partners)\b.{0,60}\b(?:confidentiality|security)\b",
        r"\bcontracts?\s+with\s+(?:third\s+parties|service\s+providers|vendors)\b",
        r"\bthird\s+party\s+apps\s+and\s+sites\s+you\s+have\s+given\s+access\b",
        r"\bpartners\s+who\s+provide\s+us\s+with\s+information\s+to\s+protect\b",
        r"\brequired\s+to\s+follow\s+this\s+privacy\s+policy\b",
        r"\breceive\s+information\s+from\s+partners\b",
        r"\bdelivery\s+partners\b",
    ],
    "prominent business contact information": [
        r"\bcontact\s+us\b",
        r"\bgrievance\s+officer\b",
        r"\bemail\s*:\s*[\w\.-]+@[\w\.-]+\.\w+\b",
        r"\bphone\s*:\s*[\+\d\s\(\)-]{7,}\b",
        r"\bcorporate\s+office\b",
        r"\bregistered\s+office\b",
    ],
    "prominently published rights-exercise means": [
        '\\bOnline\\s+Grievance\\s+Redressal\\s+Mechanism\\b',
        '\\bavailable\\s+on\\s+the\\s+college\\s+website\\b',
        '\\bhttps://skcet\\.ac\\.in/quick-links/grievance/\\b',
        r"\bPrivacy\s+Centre\b",
        r"\bPrivacy\s+Center\b",
        r"\bmanage\s+your\s+data\s+and\s+exercise\s+your\s+rights\b",
        r"\bself-serve\s+portal\b",
    ],
    "proof of consent": [
        '\\bdigitally\\s+signed\\s+by\\b',
        '\\bmaintain\\s+a\\s+record\\b',
        '\\bprior\\s+written\\s+intimation\\b',
        '\\bwritten\\s+approval\\b',
        r"\bproof\s+of\s+consent\b",
        r"\brecord\s+of\s+consent\b",
        r"\blog\s+consent\b",
    ],
    "proof of notice": [
        '\\bdigitally\\s+signed\\b',
        '\\bofficial\\s+notices?\\b',
        '\\bpublished\\s+on\\s+the\\s+college\\s+website\\b',
        '\\bAICTE\\s+Mandatory\\s+Disclosure\\b',
        r"\bproof\s+of\s+notice\b",
        r"\brecord\s+of\s+notice\b",
    ],
    "published grievance redressal system": [
        r"\bgrievance\s+redressal\s+mechanism\b",
        r"\bgrievance\s+redressal\b",
        r"\bFair\s+treatment\s+to\s+our\s+Consumer\s+and\s+Consumer\s+grievances\b",
    ],
    "purpose of processing": [
        '\\bpurpose\\s+of\\s+(?:processing|this\\s+policy|this\\s+form|collection)\\b',
        '\\bprimarily\\s+for\\s+academic\\s+and\\s+official\\s+purposes\\b',
        '\\bintended\\s+to\\s+shield\\b',
        '\\bfor\\s+the\\s+redressal\\s+of\\b',
        '\\bSKCET\\s+INSP\\s+policy\\s+is\\s+intended\\b',
        r"\bpurpose\s+of\s+(?:processing|collection|use)\b",
        r"\bcollection\s+and\s+purpose\b",
        r"\bwhy\s+we\s+collect\b",
    ],
    "readily available grievance means": [
        r"\bgrievance\s+officer\b",
        r"\breach\s+out\s+to\s+us\s+through\s+\"Contact\s+us\"\b",
        r"\bgrievance\s+redressal\b",
    ],
    "reasonable accuracy": [
        '\\bensure\\s+the\\s+firmness\\s+of\\s+network\\b',
        '\\bup[-\\s]?to[-\\s]?date\\s+list\\b',
        '\\bchecking\\s+for\\s+updates\\s+and\\s+updating\\b',
        '\\bmaintain\\s+a\\s+record\\s+of\\s+computer\\s+identification\\s+names\\b',
        '\\bverify\\s+accuracy\\b',
        r"\breasonable\s+accuracy\b",
        r"\baccurate\b",
        r"\bkeep\s+your\s+information\s+accurate\b",
    ],
    "reasonable security safeguards": [
        '\\badequate\\s+security\\s+installed/maintained\\b',
        '\\bprevent\\s+unauthorized\\s+access\\s+to\\s+institutional,\\s+research\\s+and\\s+personal\\s+data\\b',
        '\\bshield\\s+the\\s+integrity\\s+of\\s+the\\s+campus\\s+network\\b',
        '\\balleviate\\s+the\\s+risks\\s+and\\s+losses\\s+with\\s+security\\s+threats\\b',
        '\\bprohibit\\s+unauthorized\\s+access\\s+or\\s+misuse\\b',
        '\\bInformation\\s+Network\\s+Security\\s+Policy\\b',
        r"\breasonable\s+security\s+practices\s+and\s+procedures\b",
        r"\breasonable\s+security\s+safeguards\b",
        r"\bprotect\s+your\s+personal\s+data\b",
        r"\bindustry\s+standard\s+security\b",
    ],
    "relevant sharing information can be obtained": [
        '\\bsharing\\s+facilities\\s+on\\s+the\\s+computer\\s+over\\s+the\\s+network\\b',
        '\\bfiles\\s+are\\s+shared\\s+through\\s+network\\b',
        '\\bsharing\\s+information\\b',
        r"\bsharing\b",
        r"\bthird[-\s]?party\s+(?:sharing|partners)\b",
        r"\bdisclosed\s+with\s+third\s+parties\b",
    ],
    "remediate unauthorised access": [
        '\\bsubject\\s+to\\s+immediate\\s+disconnection\\b',
        '\\bdisconnect\\s+any\\s+system\\s+or\\s+device\\b',
        '\\bbrought\\s+into\\s+compliance\\b',
        r"\bremediat(?:e|ion)\s+(?:of\s+)?unauthori[sz]ed\s+access\b",
        r"\bremediate\s+and\s+recover\b",
        r"\bincident\s+remediation\b",
    ],
    "report furnished to Board": [
        r"\breport\s+furnished\s+to\s+(?:the\s+)?Board\b",
        r"\bsubmit\s+report\s+to\s+Board\b",
    ],
    "requests acted on as prescribed": [
        '\\baddressed\\s+in\\s+a\\s+timely\\s+and\\s+effective\\s+manner\\b',
        '\\btimely\\s+and\\s+effective\\b',
        '\\btime[-\\s]?bound\\s+platform\\b',
        '\\bescalation\\s+procedure\\b',
        r"\bstatus\s+of\s+(?:any\s+)?(?:existing\s+)?data\s+requests\b",
        r"\bact\s+on\s+requests\b",
        r"\bhandled\s+within\s+prescribed\b",
    ],
    "required identifier information": [
        '\\bName\\s+of\\s+the\\s+Student\\b',
        '\\bRoll\\s+No\\b',
        '\\bAadhaar\\s+Number\\b',
        '\\bEmail\\s+address\\b',
        r"\bidentifier\s+required\b",
        r"\bidentity\s+verification\b",
        r"\bprovide\s+supporting\s+documents\b",
        r"\bticket\s+ID\b",
    ],
    "required notice provided as soon as reasonably practicable": [
        r"\bnotice\s+provided\s+as\s+soon\s+as\b",
        r"\breasonably\s+practicable\b",
    ],
    "response to grievances": [
        '\\btimely\\s+and\\s+effective\\s+manner\\b',
        '\\bresponsive\\s+and\\s+time[-\\s]?bound\\s+platform\\b',
        '\\baddressing\\s+and\\s+resolving\\s+grievances\\b',
        '\\bescalation\\s+procedure\\b',
        '\\bdepartment\\s+will\\s+attend\\s+the\\s+complaints\\b',
        r"\bresolved\s+as\s+expeditiously\b",
        r"\bgrievance\s+status\b",
        r"\bresponse\s+to\s+(?:your\s+)?grievance\b",
        r"\backnowledgment\b",
    ],
    "response within reasonable period": [
        '\\btimely\\s+and\\s+effective\\s+manner\\b',
        '\\bresponsive\\s+and\\s+time[-\\s]?bound\\s+platform\\b',
        r"\bwithin\s+reasonable\s+period\b",
        r"\bexpeditiously\s+within\s+the\s+timeline\b",
        r"\bwithin\s+48\s*hours\b",
        r"\bwithin\s+\d+\s+days\b",
    ],
    "retention after withdrawal is addressed where legally required": [
        '\\breleasing\\s+the\\s+disk\\s+space\\b',
        '\\bretention\\s+after\\s+withdrawal\\b',
        '\\bstored\\s+for\\s+1\\s+month\\b',
        '\\blegally\\s+required\\b',
        r"\bretain\s+data\b.{0,60}\bif\s+there\s+is\s+a\s+legal\s+obligation\b",
        r"\bretention\s+after\s+withdrawal\b",
    ],
    "review": [
        '\\bmonitor,\\s+access,\\s+retrieve,\\s+read\\s+and/or\\s+disclose\\b',
        '\\bcopy\\s+or\\s+examine\\s+files\\b',
        '\\btest\\s+and\\s+monitor\\s+security\\b',
        r"\breview\s+(?:our\s+)?security\b",
        r"\bperiodic\s+review\b",
        r"\bupdated\s+from\s+time\s+to\s+time\b",
    ],
    "risk to Data Principal rights": [
        r"\brisk\s+to\s+(?:data\s+principals|rights)\b",
        r"\bharm\s+to\s+individuals\b",
    ],
    "safety measures": [
        '\\bdisconnect\\s+any\\s+system\\b',
        '\\bpromptly\\s+closed\\b',
        r"\bsafety\s+measures\b",
        r"\bprotective\s+measures\b",
        r"\bsecurity\s+measures\b",
    ],
    "security log retention for one year": [
        '\\bmaintain\\s+and\\s+monitor\\s+traffic\\s+logs\\b',
        '\\bfor\\s+security\\s+auditing\\s+purposes\\b',
        "\\bvideo\\s+data['’]?s\\s+are\\s+stored\\s+for\\s+1\\s+month\\b",
        r"\bsecurity\s+logs?\b.{0,60}\b(?:one|1)\s+year\b",
        r"\blogs?\s+(?:kept|retained)\s+for\s+(?:one|1)\s+year\b",
    ],
    "significant observations": [
        r"\bsignificant\s+observations\b",
        r"\baudit\s+findings\b",
    ],
    "specific consent": [
        '\\bagreeing\\s+to\\s+abide\\s+by\\s+the\\s+following\\s+policies\\b',
        '\\bprior\\s+(?:written\\s+)?approval\\b',
        '\\bspecific\\s+consent\\b',
        r"\bspecific\s+consent\b",
        r"\bterms\s+specific\s+to\s+certain\s+services\b",
        r"\bconsent\s+for\s+specific\b",
    ],
    "specific description of goods/services/uses enabled": [
        '\\bServices\\b.{0,60}\\bSKCET\\s+technical\\s+team\\s+is\\s+responsible\\b',
        '\\bProgrammes\\s+Approved\\s+by\\s+AICTE\\b',
        '\\bCourses\\s+&\\s+Course\\s+Details\\b',
        r"\bgoods\s+and\s+services\b",
        r"\bdescription\s+of\s+services\b",
        r"\bservices\s+offered\b",
        r"\benable\s+(?:features|services)\b",
    ],
    "specified erasure period": [
        "\\bvideo\\s+data['’]?s\\s+are\\s+stored\\s+for\\s+1\\s+month\\b",
        '\\bstored\\s+for\\s+1\\s+month\\b',
        '\\b1\\s+month\\b',
        r"\berasure\s+period\b",
        r"\bperiod\s+of\s+\d+\s+(?:years?|months?)\b",
        r"\bdeleted\s+from\s+our\s+record\b",
    ],
    "specified personal/traffic data not transferred contrary to restriction": [
        r"\bpersonal\s+data\s+is\s+primarily\s+governed\s+by\s+Indian\s+laws\s+and\s+stored\s+in\s+India\b",
        r"\bdata\s+not\s+transferred\b",
    ],
    "specified processing purpose": [
        '\\bprimarily\\s+for\\s+academic\\s+and\\s+official\\s+purposes\\b',
        '\\bintended\\s+to\\s+shield\\b',
        '\\bfor\\s+the\\s+redressal\\s+of\\s+genuine\\s+grievances\\b',
        r"\bpurpose\s+of\s+(?:processing|collection|use)\b",
        r"\bcollection\s+and\s+purpose\b",
        r"\bpurpose\s+for\s+which\s+it\s+was\s+collected\b",
    ],
    "specified purpose": [
        '\\bacademic\\s+and\\s+official\\s+purposes\\b',
        '\\bfor\\s+the\\s+redressal\\s+of\\s+genuine\\s+grievances\\b',
        '\\bspecified\\s+purpose\\b',
        r"\bspecified\s+purpose\b",
        r"\bpurpose\s+of\s+(?:processing|collection)\b",
        r"\bpurpose\s+for\s+which\b",
    ],
    "technical and organisational measures": [
        '\\bOnline\\s+Grievance\\s+Redressal\\s+Mechanism\\b',
        '\\bComposition\\s+of\\s+the\\s+General\\s+Complaints\\s+and\\s+Grievance\\s+Redressal\\s+Committee\\b',
        '\\bhelp\\s+desk\\b',
        r"\btechnical\s+and\s+organi[sz]ational\s+measures\b",
        r"\btechnical\s+measures\b",
        r"\borgani[sz]ational\s+measures\b",
        r"\bsecurity\s+practices\s+and\s+procedures\b",
    ],
    "technical measures": [
        r"\btechnical\s+measures\b",
        r"\btechnical\s+safeguards\b",
        r"\btechnological\s+(?:measures|controls)\b",
        r"\bencryption\b",
        r"\bsecure\s+servers?\b",
        r"\bfirewalls?\b",
        r"\bindustry\s+standard\s+security\b",
        r"\btechnical\s+and\s+organi[sz]ational\b",
    ],
    "technical security measures": [
        '\\bexternal\\s+Internet\\s+firewall\\b',
        '\\bIEEE\\s+802\\.11\\b',
        '\\banti-virus\\s+software\\b',
        '\\bpassword\\s+and\\s+also\\s+with\\s+read\\s+only\\s+access\\b',
        '\\bdecrypt\\s+SSL\\s+traffic\\b',
        r"\btechnical\s+security\s+measures\b",
        r"\bencryption\b",
        r"\bsecure\s+server\b",
        r"\bindustry\s+standard\s+security\s+measures\b",
    ],
    "traffic data retention one year": [
        r"\btraffic\s+data\b.{0,60}\b(?:one|1)\s+year\b",
        r"\baccess\s+records\b.{0,60}\b(?:one|1)\s+year\b",
    ],
    "unambiguous consent": [
        '\\bclear\\s+and\\s+unambiguous\\b',
        '\\bunambiguous\\b',
        r"\bunambiguous\b",
        r"\bexplicitly\s+consent\b",
        r"\bclear\s+affirmative\b",
    ],
    "unconditional consent": [
        '\\bunconditional\\b',
        '\\bwithout\\s+undue\\s+condition\\b',
        r"\bunconditional\b",
        r"\bwithout\s+condition\b",
        r"\bchoice\s+to\s+decide\b",
    ],
    "verifiable parental consent": [
        "\\bParent['’]?s\\s+Feedback\\s+Form\\b",
        '\\bParent\\s+\\((?:Male|Female)\\)\\b',
        '\\bparental\\s+consent\\b',
        '\\bparent\\s+or\\s+guardian\\b',
        r"\bverifiable\s+parental\s+consent\b",
        r"\bparental\s+consent\b",
        r"\bauthority\s+to\s+do\s+so\s+and\s+permit\s+us\b",
    ],
    "withdrawal mechanism is as easy as giving consent": [
        '\\bas\\s+easy\\s+as\\b',
        '\\bwritten\\s+intimation\\b',
        '\\bemail\\s+or\\s+phone\\b',
        r"\beasily\s+withdraw\b",
        r"\beasy\s+to\s+withdraw\b",
        r"\bself-serve\s+portal\b",
        r"\bunsubscribe\s+link\b",
    ],
    "withdrawal or invalidity conditions are not inconsistent with Section 6(2)": [
        '\\bwithdrawal\\s+of\\s+the\\s+facility\\b',
        '\\bopt[-\\s]?out\\b',
        '\\bwithdraw\\s+your\\s+consent\\b',
        '\\bsubject\\s+to\\s+immediate\\s+disconnection\\b',
        r"\bwithdraw(?:al|ing)?\s+(?:of\s+)?consent\b",
        r"\bwithdraw\s+consent\s+at\s+any\s+time\b",
        r"\bwithdrawing\s+consent\b",
        r"\bopt[-\s]?out\b",
        r"\bchoice\s*/\s*opt[-\s]?out\b",
        r"\bstop\s+receiving\s+(?:non-essential|promotional|marketing)\b",
        r"\bopt[-\s]?out\s+at\s+any\s+time\b",
        r"\bwithdrawal\s+(?:does\s+not|shall\s+not)\s+affect\b",
        r"\blegality\s+of\s+processing\s+prior\b",
        r"\bwithdrawal\s+without\s+affecting\b",
        r"\bnot\s+inconsistent\b",
    ],
}


# ------------------------------------------------------------
# Requirement -> topics (all 55 requirements)
# ------------------------------------------------------------

REQUIREMENT_TOPICS: Dict[str, List[str]] = {

    "ACT_SEC_4": ["notice", "operations"],
    "ACT_SEC_5": ["notice", "rights", "grievance"],
    "ACT_SEC_5_2": ["consent", "notice"],
    "ACT_SEC_5_3": ["notice"],

    "ACT_SEC_6_1": ["consent"],
    "ACT_SEC_6_2": ["consent"],
    "ACT_SEC_6_3": ["consent", "notice"],
    "ACT_SEC_6_4": ["consent"],
    "ACT_SEC_6_6": ["consent", "retention"],
    "ACT_SEC_6_10": ["consent"],

    "ACT_SEC_8_1": ["operations"],
    "ACT_SEC_8_2": ["operations"],
    "ACT_SEC_8_3": ["operations"],
    "ACT_SEC_8_4": ["security"],
    "ACT_SEC_8_5": ["security"],
    "ACT_SEC_8_6": ["security", "breach"],
    "ACT_SEC_8_7": ["retention"],
    "ACT_SEC_8_9": ["contact"],
    "ACT_SEC_8_10": ["grievance"],

    "ACT_SEC_9_1": ["children", "consent"],
    "ACT_SEC_9_2": ["children"],
    "ACT_SEC_9_3": ["children"],

    "ACT_SEC_10_DPO": ["contact", "grievance"],
    "ACT_SEC_10_AUDITOR": ["operations"],
    "ACT_SEC_10_DPIA": ["operations"],
    "ACT_SEC_10_AUDIT": ["operations"],

    "ACT_SEC_11": ["rights"],
    "ACT_SEC_12": ["rights"],
    "ACT_SEC_13": ["grievance"],

    "RULE_3": ["notice"],
    "RULE_3_ITEMISED_DATA": ["notice"],
    "RULE_3_PURPOSE": ["notice"],
    "RULE_3_LINKS": ["notice", "rights", "grievance"],

    "RULE_6_ENCRYPTION": ["security"],
    "RULE_6_ACCESS": ["security"],
    "RULE_6_LOGGING": ["security"],
    "RULE_6_BACKUPS": ["security"],
    "RULE_6_LOG_RETENTION": ["security", "retention"],
    "RULE_6_PROCESSOR_CONTRACT": ["security", "operations"],
    "RULE_6_TECH_ORG": ["security"],

    "RULE_7_PRINCIPAL_BREACH": ["breach"],
    "RULE_7_BOARD_BREACH": ["breach"],

    "RULE_8_ERASURE": ["retention"],
    "RULE_8_48_HOURS": ["retention"],
    "RULE_8_ONE_YEAR": ["retention"],

    "RULE_9_CONTACT": ["contact"],
    "RULE_10_CHILD_CONSENT": ["children", "consent"],
    "RULE_11_GUARDIAN": ["children"],

    "RULE_13_DPIA": ["operations"],
    "RULE_13_BOARD_REPORT": ["operations"],
    "RULE_13_ALGORITHMIC_RISK": ["operations", "security"],
    "RULE_13_LOCALISATION": ["operations"],

    "RULE_14_RIGHTS_MEANS": ["rights"],
    "RULE_14_GRIEVANCE_90_DAYS": ["grievance"],

    "RULE_15_CROSS_BORDER": ["operations"],
}


# ------------------------------------------------------------
# Evidence field routing
# ------------------------------------------------------------

TOPIC_FIELDS: Dict[str, set[str]] = {

    "consent": {
        "consent_information",
        "consent_ui_evidence",
        "language_ui_evidence",
        "privacy_policy",
        "data_collection_evidence",
        "security_policy",
        "grievance_information",
    },

    "notice": {
        "privacy_policy",
        "language_ui_evidence",
        "personal_data_information",
        "data_collection_evidence",
        "security_policy",
        "contact_information",
        "grievance_information",
    },

    "rights": {
        "rights_ui_evidence",
        "rights_information",
        "privacy_policy",
        "contact_information",
        "grievance_information",
        "grievance_ui_evidence",
        "data_collection_evidence",
        "security_policy",
    },

    "grievance": {
        "grievance_ui_evidence",
        "grievance_information",
        "contact_information",
        "privacy_policy",
        "security_policy",
    },

    "security": {
        "security_ui_evidence",
        "security_policy",
        "breach_information",
        "privacy_policy",
        "grievance_information",
        "contact_information",
    },

    "breach": {
        "breach_information",
        "security_policy",
        "privacy_policy",
        "contact_information",
        "grievance_information",
    },

    "children": {
        "child_ui_evidence",
        "child_information",
        "privacy_policy",
        "consent_ui_evidence",
        "grievance_information",
        "data_collection_evidence",
        "security_policy",
    },

    "retention": {
        "retention_information",
        "privacy_policy",
        "security_policy",
    },

    "contact": {
        "contact_information",
        "grievance_information",
        "privacy_policy",
        "security_policy",
    },

    "operations": {
        "privacy_policy",
        "security_policy",
        "terms_of_use",
        "cross_border_information",
        "contact_information",
        "grievance_information",
        "data_collection_evidence",
    },
}


# Fields which may contain highly aggregated crawler output.
AGGREGATED_FIELDS = {
    "consent_information",
    "language_ui_evidence",
    "ui_information",
    "page_text",
}


# Never use these as deterministic evidence.
NEVER_EVIDENCE_FIELDS = {
    "page_text",
    "ui_information",
}


# ------------------------------------------------------------
# Noise detection
# ------------------------------------------------------------

NOISE_PATTERNS = [
    r"\baria_label\s*=\s*(?:seek|volume|play|pause|mute|fullscreen)\b",
    r"\btype\s*=\s*(?:range|button|submit|search)\b",
    r"\bid\s*=\s*plyr[-_]",
    r"\binput\s+aria_label\s*=",
]

NAVIGATION_ONLY_PATTERNS = [
    r"\bmain\s+menu\b",
    r"\bnavigation\s+menu\b",
    r"\bquick\s+links\b",
    r"\bsite\s+navigation\b",
    r"\btop\s+nav\b",
    r"\bfooter\s+links\b",
    r"\bbreadcrumb\b",
]


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _as_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, (list, tuple)):
        return " ".join(_as_text(item) for item in value)

    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            parts.append(f"{key}: {_as_text(item)}")
        return " ".join(parts)

    return str(value)


def _iter_field_values(data: Dict[str, Any], field: str) -> Iterable[str]:
    value = data.get(field)

    if value is None:
        return

    if isinstance(value, list):
        for item in value:
            text = _as_text(item).strip()
            if text:
                yield text
        return

    if isinstance(value, dict):
        text = _as_text(value).strip()
        if text:
            yield text
        return

    text = _as_text(value).strip()

    if text:
        yield text


def _patterns_for_element(element: str) -> List[str]:
    return ELEMENT_PATTERNS.get(element, [])


def _topics_for_requirement(requirement_id: str) -> List[str]:
    if requirement_id in REQUIREMENT_TOPICS:
        return REQUIREMENT_TOPICS[requirement_id]
    return matrix_topics_for_requirement(requirement_id)


def _allowed_fields(requirement_id: str) -> set[str]:
    topics = _topics_for_requirement(requirement_id)

    fields: set[str] = set()

    for topic in topics:
        fields.update(TOPIC_FIELDS.get(topic, set()))

    # Never permit these noisy aggregate fields.
    fields.difference_update(NEVER_EVIDENCE_FIELDS)

    return fields


def _has_noise(text: str) -> bool:
    lowered = text.lower()

    return any(
        re.search(pattern, lowered, re.IGNORECASE)
        for pattern in NOISE_PATTERNS
    )


def _looks_navigation_only(text: str) -> bool:
    lowered = text.lower()

    matches = sum(
        1
        for pattern in NAVIGATION_ONLY_PATTERNS
        if re.search(pattern, lowered, re.IGNORECASE)
    )

    # A blob containing many unrelated navigation terms is
    # almost certainly a homepage/navigation extraction.
    return matches >= 4


def _matched_patterns(
    text: str,
    patterns: List[str],
) -> List[str]:

    matches = []

    for pattern in patterns:
        try:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                matches.append(pattern)
        except re.error:
            continue

    return matches


def _is_relevant_evidence(
    requirement_id: str,
    element: str,
    field: str,
    text: str,
    matched_patterns: List[str],
) -> bool:

    if not matched_patterns:
        return False

    if not text.strip():
        return False

    # Obvious media-control contamination.
    if _has_noise(text):
        return False

    # Huge navigation blobs are not useful just because one
    # generic word happened to match.
    if field not in {"privacy_policy", "security_policy", "grievance_information", "contact_information", "rights_information", "consent_information", "data_collection_evidence"}:
        if _looks_navigation_only(text):
            return False

    # Aggregated fields need stronger semantic evidence.
    if field in AGGREGATED_FIELDS:

        lowered = text.lower()

        # Consent-related aggregated content must contain
        # an explicit consent/privacy signal.
        if requirement_id.startswith("ACT_SEC_6"):
            consent_signals = [
                "consent",
                "i agree",
                "i accept",
                "withdraw",
                "privacy notice",
                "privacy policy",
            ]

            if not any(signal in lowered for signal in consent_signals):
                return False

        # Security evidence must explicitly mention security.
        if requirement_id in {
            "ACT_SEC_8_4",
            "ACT_SEC_8_5",
            "RULE_6_ENCRYPTION",
            "RULE_6_ACCESS",
            "RULE_6_LOGGING",
            "RULE_6_BACKUPS",
            "RULE_6_TECH_ORG",
        }:
            security_signals = [
                "security",
                "encryption",
                "encrypted",
                "access control",
                "backup",
                "logging",
                "monitoring",
                "masking",
                "obfuscation",
            ]

            if not any(signal in lowered for signal in security_signals):
                return False

        # Contact evidence must contain actual contact identity.
        if requirement_id in {
            "ACT_SEC_8_9",
            "RULE_9_CONTACT",
        }:
            contact_signals = [
                "dpo",
                "data protection officer",
                "privacy officer",
                "privacy contact",
                "data protection contact",
                "grievance officer",
                "grievance",
                "customer grievance",
            ]

            if not any(signal in lowered for signal in contact_signals):
                return False

    return True


def _extract_evidence_snippet(
    text: str,
    patterns: List[str],
    max_length: int = 1200,
) -> str:

    if len(text) <= max_length:
        return text.strip()

    # Try to return a local context window around the first
    # meaningful match rather than the entire homepage blob.
    for pattern in patterns:
        try:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE | re.DOTALL,
            )
        except re.error:
            continue

        if not match:
            continue

        start = max(0, match.start() - 300)
        end = min(len(text), match.end() + 700)

        snippet = text[start:end].strip()

        if snippet:
            return snippet[:max_length]

    return text[:max_length].strip()


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def assess_requirement(
    requirement_id: str,
    crawler_data: Dict[str, Any],
) -> Dict[str, Any]:

    topics = _topics_for_requirement(requirement_id)
    allowed_fields = _allowed_fields(requirement_id)

    # Obtain the requirement's assessment elements from the
    # deterministic matrix if available, otherwise retrieve
    # directly from requirement_evidence_matrix.
    matrix = crawler_data.get("requirement_matrix", {})

    requirement = None
    if isinstance(matrix, dict):
        requirement = matrix.get(requirement_id)

    elements = []
    if isinstance(requirement, dict):
        elements = requirement.get("assessment_elements", []) or []

    if not elements:
        elements = get_assessment_elements(requirement_id)

    # Fallback only if the requirement has no defined matrix elements.
    if not elements:
        elements = [requirement_id]

    element_results = []

    all_evidence: Dict[str, List[str]] = {}
    all_fields: set[str] = set()

    for element in elements:

        element_name = (
            element.get("element")
            if isinstance(element, dict)
            else str(element)
        )

        patterns = _patterns_for_element(element_name)

        matched_fields = []
        evidence = []
        matched_pattern_names = []

        if patterns:

            for field in sorted(allowed_fields):

                for raw_text in _iter_field_values(
                    crawler_data,
                    field,
                ):

                    matched_patterns = _matched_patterns(
                        raw_text,
                        patterns,
                    )

                    if not matched_patterns:
                        continue

                    if not _is_relevant_evidence(
                        requirement_id=requirement_id,
                        element=element_name,
                        field=field,
                        text=raw_text,
                        matched_patterns=matched_patterns,
                    ):
                        continue

                    snippet = _extract_evidence_snippet(
                        raw_text,
                        patterns,
                    )

                    if field not in matched_fields:
                        matched_fields.append(field)

                    if snippet not in evidence:
                        evidence.append(snippet)

                    matched_pattern_names.extend(
                        matched_patterns
                    )

        if evidence:
            status = "sufficient"
        else:
            status = "not_observable"

        element_results.append(
            {
                "element": element_name,
                "status": status,
                "matched_fields": matched_fields,
                "evidence": evidence,
                "matched_patterns": list(
                    dict.fromkeys(matched_pattern_names)
                ),
            }
        )

        for field in matched_fields:
            all_fields.add(field)

        for field in matched_fields:
            all_evidence.setdefault(
                field,
                [],
            )

            for snippet in evidence:
                if snippet not in all_evidence[field]:
                    all_evidence[field].append(snippet)

    observable_count = sum(
        1
        for item in element_results
        if item["status"] == "sufficient"
    )

    required_count = len(element_results)

    if observable_count == 0:
        overall_status = "insufficient"
    elif observable_count >= required_count:
        overall_status = "sufficient"
    else:
        overall_status = "partial"

    return {
        "requirement_id": requirement_id,
        "topics": topics,
        "allowed_evidence_fields": sorted(
            allowed_fields
        ),
        "evidence_fields_available": sorted(
            all_fields
        ),
        "overall_evidence_status": overall_status,
        "observable_elements": observable_count,
        "required_elements": required_count,
        "elements": element_results,
        "evidence": all_evidence,
        "evidence_policy": (
            "deterministic_element_evidence_v22"
        ),
    }


def build_llm_evidence_package(
    requirement_id: str,
    crawler_data: Dict[str, Any],
) -> Dict[str, Any]:

    assessment = assess_requirement(
        requirement_id,
        crawler_data,
    )

    return {
        "requirement_id": requirement_id,
        "overall_evidence_status": (
            assessment["overall_evidence_status"]
        ),
        "observable_elements": (
            assessment["observable_elements"]
        ),
        "required_elements": (
            assessment["required_elements"]
        ),
        "allowed_evidence_fields": (
            assessment["allowed_evidence_fields"]
        ),
        "evidence_fields_available": (
            assessment["evidence_fields_available"]
        ),
        "elements": assessment["elements"],
        "evidence": assessment["evidence"],
        "evidence_policy": (
            "deterministic_element_evidence_v22"
        ),
    }
