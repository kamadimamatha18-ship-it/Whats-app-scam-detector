import re
from urllib.parse import urlparse


def analyze_message(message):
    message_lower = message.lower().strip()

    # 1. కోడ్ లేదా టెక్నికల్ స్క్రిప్ట్ అయితే వెంటనే సేఫ్ అని గుర్తించడం (False Positive నివారించడానికి)
    code_indicators = ["def ", "import ", "print(", "class ", "return ", "for i in", "while "]
    if any(indicator in message for indicator in code_indicators):
        return "0%", "✅ సురక్షితం (Safe - Code Snippet)", "ఇది ప్రోగ్రామింగ్ కోడ్ లా కనిపిస్తోంది. ఇందులో స్కామ్ ప్రమాదం లేదు.", [
            "ఇది వాలిడ్ టెక్నికల్ కోడ్/స్క్రిప్ట్."], "safe"

    # 2. ఫస్ట్ URLs ni extract cheyadam
    urls = re.findall(r'https?://[^\s]+', message)

    # Trusted Domains Check
    ALLOWED_DOMAINS = {
        "linkedin.com", "www.linkedin.com", "in.linkedin.com",
        "github.com", "www.github.com",
        "google.com", "www.google.com",
        "twitter.com", "www.twitter.com", "x.com", "www.x.com"
    }

    if urls:
        try:
            parsed_url = urlparse(urls[0])
            domain = parsed_url.netloc.lower()
            if ":" in domain:
                domain = domain.split(":")[0]

            is_trusted = any(domain == trusted or domain.endswith("." + trusted) for trusted in ALLOWED_DOMAINS)
            if is_trusted:
                return "0%", "✅ సురక్షితం (Safe - Trusted Domain)", "ఇది నమ్మదగిన అధికారిక వెబ్‌సైట్.", [
                    f"తెలిసిన సురక్షిత డొమైన్: {urls[0]}"], "safe"
        except Exception:
            pass

    risk_score = 0
    reasons = []

    # 3. Whole-word scam keywords check (\b వాడితే సబ్‌స్ట్రింగ్ సమస్య రాదు)
    scam_keywords = ["free recharge", "click here", "claim now", "lottery", "won prize", "urgent cash",
                     "congratulations won"]

    found_keywords = []
    for kw in scam_keywords:
        # Regex వాడి పదం పూర్తిగ ఉందో లేదో చెక్ చేయడం
        if re.search(r'\b' + re.escape(kw) + r'\b', message_lower):
            found_keywords.append(kw)

    if found_keywords:
        risk_score += 40
        reasons.append(f"అనుమానాస్పద పదాలు గుర్తించబడ్డాయి: {', '.join(found_keywords)}")

    if urls:
        risk_score += 50
        reasons.append(f"అనుమానాస్పద లింక్ ఉంది: {urls[0]}")

    # Risk Levels formatting
    if risk_score >= 80:
        return f"{risk_score}%", "🚨 హై రిస్క్ (HIGH RISK - స్కామ్)", "దయచేసి ఈ మెసేజ్‌ని నమ్మకండి!", reasons, "high-risk"
    elif risk_score >= 40:
        return f"{risk_score}%", "⚠️ మీడియం రిస్క్ (Moderate Risk - జాగ్రత్త)", "ఇది మోసపూరితమయ్యే అవకాశం ఉంది.", reasons, "med-risk"
    else:
        return "0%", "✅ సురక్షితం (Safe)", "ఈ మెసేజ్‌లో ఎలాంటి ప్రమాదకరమైన అంశాలు కనిపించలేదు.", [
            "ప్రమాదం ఏమీ లేదు."], "safe"