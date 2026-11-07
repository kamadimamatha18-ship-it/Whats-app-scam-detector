import os
import re
from urllib.parse import urlparse
from flask import Flask, render_template_string, request

app = Flask(__name__)

# అందమైన వెబ్ పేజ్ డిజైన్ (HTML & UI)
HTML_PAGE = """
<!DOCTYPE html>
<html lang="te">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp Scam Detector</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f7f6; margin: 0; padding: 40px; display: flex; justify-content: center; }
        .container { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 600px; }
        h2 { color: #333; text-align: center; }
        textarea { width: 100%; height: 120px; padding: 12px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; box-sizing: border-box; }
        button { background-color: #25D366; color: white; border: none; padding: 12px 20px; font-size: 16px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%; margin-top: 15px; }
        button:hover { background-color: #128C7E; }
        .result-box { margin-top: 25px; padding: 20px; border-radius: 8px; background: #fafafa; border-left: 6px solid #25D366; }
        .error-text { color: red; font-weight: bold; margin-top: 10px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🛡️ WhatsApp Scam Detector</h2>
        <form method="POST">
            <textarea name="message" placeholder="దయచేసి లింక్ లేదా లింక్‌తో కూడిన మెసేజ్ ఇక్కడ టైప్ చేయండి..." required>{{ user_message }}</textarea>
            <button type="submit">🔍 చెక్ చేయండి</button>
        </form>

        {% if error_msg %}
        <p class="error-text">{{ error_msg }}</p>
        {% endif %}

        {% if result %}
        <div class="result-box">
            <h3>ఫలితం (Result):</h3>
            <p><strong>📊 రిస్క్ స్కోర్:</strong> {{ score }}</p>
            <p><strong>📌 స్టేటస్:</strong> {{ status }}</p>
            <p><strong>💡 సూచన:</strong> {{ advice }}</p>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""


# స్కామ్ డిటెక్షన్ లాజిక్
def check_scam_message(message):
    message_lower = message.lower().strip()

    # 1. పైథాన్ కోడ్ లేదా టెక్నికల్ స్క్రిప్ట్ అయితే సేఫ్
    code_indicators = ["def ", "import ", "print(", "class ", "return ", "for i in", "while "]
    if any(indicator in message for indicator in code_indicators):
        return "0%", "✅ సేఫ్ (Safe - Code Snippet)", "ఇది ప్రోగ్రామింగ్ కోడ్ లా కనిపిస్తోంది. ఇందులో స్కామ్ ప్రమాదం లేదు."

    # 2. లింక్ లేదా డొమైన్‌ను గుర్తించడం (https లేకపోయినా సరే)
    urls = re.findall(r'(?:https?://)?(?:www\.)?[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-z]{2,}(?:/[^\s]*)?', message)

    if not urls:
        return "0%", "⚠️ ఇన్వాలిడ్ ఇన్‌పుట్ (Invalid Input)", "దయచేసి చెక్ చేయడానికి ఏదైనా సరైన లింక్ లేదా డొమైన్ (ఉదా: picsart.com) ఇవ్వండి."

    # 3. Trusted & Government Domains (Whitelist)
    ALLOWED_DOMAINS = {
        "linkedin.com", "github.com", "google.com", "twitter.com", "x.com",
        "ssc.gov.in", "gov.in", "picsart.com", "instagram.com", "facebook.com",
        "youtube.com", "ataop.com", "billgenerator.ai"
    }

    found_url = urls[0]
    test_url = found_url if found_url.startswith("http") else "https://" + found_url

    try:
        parsed_url = urlparse(test_url)
        domain = parsed_url.netloc.lower()
        if ":" in domain:
            domain = domain.split(":")[0]
        if domain.startswith("www."):
            domain = domain[4:]

        # వైట్‌లిస్ట్ డొమైన్‌లలో ఉంటే నేరుగా సేఫ్
        is_trusted = any(domain == trusted or domain.endswith("." + trusted) for trusted in ALLOWED_DOMAINS)
        if is_trusted:
            return "0%", "✅ సురక్షితం (Trusted Domain)", f"ఇది నమ్మదగిన అధికారిక వెబ్‌సైట్ ({found_url}). ఇందులో ఎలాంటి రిస్క్ లేదు."
    except Exception:
        pass

    # 4. కేవలం మెయిన్ డొమైన్ నేమ్‌లో మాత్రమే ఫేక్ పదాలు ఉన్నాయో లేదో చెక్ చేయడం
    risk_score = 0
    scam_keywords = ["free recharge", "click here", "claim now", "lottery", "won prize", "urgent cash", "free",
                     "recharge", "click", "claim", "offer", "win"]

    found_keywords = [kw for kw in scam_keywords if re.search(r'\b' + re.escape(kw) + r'\b', message_lower)]

    if found_keywords:
        risk_score += 50

    # కేవలం డొమైన్ నేమ్‌లో మాత్రమే మోసపూరిత పదాలు ఉన్నాయా అని చెక్ చేయడం
    try:
        domain_only = urlparse(test_url).netloc.lower()
        if any(bad in domain_only for bad in ["fake", "free-", "-win", "reward", "bonus", "prize", "scam"]):
            risk_score += 50
    except Exception:
        pass

    # రిస్క్ లెవెల్స్
    if risk_score >= 50:
        return "100%", "🚨 హై రిస్క్ (HIGH RISK - స్కామ్ లింక్)", "దయచేసి ఈ లింక్‌ని క్లిక్ చేయకండి! ఇది మోసపూరితమైనది."
    else:
        return "0%", "✅ సేఫ్ (Safe Link)", f"ఈ లింక్ ({found_url}) సురక్షితంగా ఉన్నట్లు కనిపిస్తోంది."


@app.route("/", methods=["GET", "POST"])
def home():
    user_message = ""
    result = False
    score, status, advice = "", "", ""
    error_msg = ""

    if request.method == "POST":
        user_message = request.form.get("message", "").strip()

        if not user_message:
            error_msg = "⚠️ దయచేసి ఏదైనా మెసేజ్ లేదా లింక్ ఎంటర్ చేయండి!"
        else:
            score, status, advice = check_scam_message(user_message)
            result = True

    return render_template_string(
        HTML_PAGE,
        user_message=user_message,
        result=result,
        score=score,
        status=status,
        advice=advice,
        error_msg=error_msg
    )


# Render మరియు Local సర్వర్ రెండింటికీ సపోర్ట్ చేసే పోర్ట్ కాన్ఫిగరేషన్
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)