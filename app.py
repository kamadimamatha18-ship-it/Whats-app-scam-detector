from flask import Flask, request, render_template_string
import re

app = Flask(__name__)

# HTML వెబ్ పేజ్ డిజైన్ (అందరికీ సులభంగా అర్థమయ్యేలా)
HTML_PAGE = """
<!DOCTYPE html>
<html lang="te">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp & Message Scam Detector</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .container { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 600px; }
        h2 { color: #333; text-align: center; margin-bottom: 10px; }
        p.subtitle { text-align: center; color: #666; font-size: 14px; margin-bottom: 25px; }
        textarea { width: 100%; height: 120px; padding: 12px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; resize: none; box-sizing: border-box; }
        button { background-color: #25D366; color: white; border: none; padding: 12px 20px; font-size: 16px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%; margin-top: 15px; transition: 0.3s; }
        button:hover { background-color: #128C7E; }
        .result-box { margin-top: 25px; padding: 20px; border-radius: 8px; background: #fafafa; border-left: 6px solid #25D366; }
        .high-risk { border-left-color: #ff4d4d; background: #fff5f5; }
        .med-risk { border-left-color: #ffa500; background: #fffaf0; }
        .safe { border-left-color: #28a745; background: #f0fff4; }
        h3 { margin-top: 0; color: #333; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🛡️ ఫేక్ మెసేజ్ & స్కామ్ డిటెక్టర్</h2>
        <p class="subtitle">సందేహాస్పదమైన మెసేజ్ లేదా లింక్‌ని కింద టైప్ చేసి చెక్ చేయండి.</p>

        <form method="POST">
            <textarea name="message" placeholder="ఉదాహరణకు: Claim free ₹5000 recharge now by clicking this link..." required>{{ user_message }}</textarea>
            <button type="submit">🔍 చెక్ చేయండి (Check Message)</button>
        </form>

        {% if result %}
        <div class="result-box {{ risk_class }}">
            <h3>పరిశీలన ఫలితం (Analysis Report):</h3>
            <p><strong>📊 రిస్క్ స్కోర్:</strong> {{ score }}%</p>
            <p><strong>📌 స్టేటస్:</strong> {{ status }}</p>
            <p><strong>💡 సూచన:</strong> {{ advice }}</p>
            {% if reasons %}
            <p><strong>🔍 కారణాలు:</strong></p>
            <ul>
                {% for r in reasons %}
                <li>{{ r }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""


def analyze_message(message):
    message_lower = message.lower()
    risk_score = 0
    reasons = []

    scam_keywords = ["free", "recharge", "click", "claim", "lottery", "won", "prize", "urgent", "congratulations",
                     "offer", "cashback"]
    found_keywords = [kw for kw in scam_keywords if kw in message_lower]

    if found_keywords:
        risk_score += 40
        reasons.append(f"అనుమానాస్పద పదాలు గుర్తించబడ్డాయి: {', '.join(found_keywords)}")

    urls = re.findall(r'https?://[^\s]+', message)
    if urls:
        risk_score += 50
        reasons.append(f"అనుమానాస్పద లింక్ ఉంది: {urls[0]}")
        if "fake" in urls[0] or "free" in urls[0] or "offer" in urls[0] or "win" in urls[0]:
            risk_score += 10
            reasons.append("నకిలీ లేదా అనుమానాస్పద వెబ్‌సైట్ డొమైన్.")

    if risk_score >= 80:
        status = "🚨 హై రిస్క్ (HIGH RISK - 100% స్కామ్)"
        advice = "దయచేసి ఈ మెసేజ్‌ని నమ్మకండి మరియు లింక్‌ని అస్సలు క్లిక్ చేయకండి!"
        risk_class = "high-risk"
    elif risk_score >= 40:
        status = "⚠️ మీడియం రిస్క్ (Moderate Risk - జాగ్రత్త)"
        advice = "ఇది మోసపూరితమయ్యే అవకాశం ఉంది. తొందరపడి ఎలాంటి వివరాలు ఇవ్వకండి."
        risk_class = "med-risk"
    else:
        status = "✅ సురక్షితం (Safe)"
        advice = "ఈ మెసేజ్‌లో ఎలాంటి ప్రమాదకరమైన అంశాలు కనిపించలేదు."
        risk_class = "safe"

    return risk_score, status, advice, reasons, risk_class


@app.route("/", methods=["GET", "POST"])
def home():
    user_message = ""
    result = False
    score = 0
    status = ""
    advice = ""
    reasons = []
    risk_class = "safe"

    if request.method == "POST":
        user_message = request.form.get("message", "")
        if user_message.strip():
            score, status, advice, reasons, risk_class = analyze_message(user_message)
            result = True

    return render_template_string(HTML_PAGE, user_message=user_message, result=result, score=score, status=status,
                                  advice=advice, reasons=reasons, risk_class=risk_class)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)