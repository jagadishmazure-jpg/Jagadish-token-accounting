"""Evaluation and training text, written for this repo. All companies are fictional.

Six content types, five samples each. The BPE training text is kept separate from the
evaluation samples so the from-scratch tokenizer is not scored on text it was trained on.
"""

from __future__ import annotations

CATEGORIES = ("english", "code", "json", "hindi", "telugu", "emoji")

SAMPLES: dict[str, list[str]] = {
    "english": [
        "Orbitra Freight moved its quarterly planning meeting to Thursday because two of the route managers were travelling.",
        "Please summarise the attached maintenance report and list any pumps that need a replacement part before winter.",
        "The new onboarding guide explains how to request laptop access, where to find the expense form, and who approves leave.",
        "Customers at Lumenfield Grocers asked why their loyalty points expired early; the answer was a timezone bug in the batch job.",
        "A careful reviewer reads the whole contract, marks every clause that changes liability, and writes a short plain summary.",
    ],
    "code": [
        "def total_cost(tokens_in: int, tokens_out: int) -> float:\n    return tokens_in * 0.5e-6 + tokens_out * 1.5e-6\n",
        "for (let i = 0; i < rows.length; i++) {\n  if (rows[i].status === 'late') late.push(rows[i].id);\n}\n",
        "SELECT customer_id, SUM(amount) AS spend FROM orders WHERE created_at >= '2026-01-01' GROUP BY customer_id;",
        "class RateLimiter:\n    def __init__(self, limit: int) -> None:\n        self.limit = limit\n        self.hits: list[float] = []\n",
        "func Retry(n int, f func() error) error {\n\tvar err error\n\tfor i := 0; i < n; i++ {\n\t\tif err = f(); err == nil {\n\t\t\treturn nil\n\t\t}\n\t}\n\treturn err\n}\n",
    ],
    "json": [
        '{"order_id": "ORD-10422", "status": "shipped", "items": [{"sku": "TEA-001", "qty": 2}, {"sku": "MUG-014", "qty": 1}]}',
        '{"name": "lookup_invoice", "description": "Find an invoice by number", "parameters": {"type": "object", '
        '"properties": {"invoice_no": {"type": "string"}}, "required": ["invoice_no"]}}',
        '{"tenant": "Kestrel Analytics", "plan": "team", "seats": 25, "features": {"sso": true, "audit_log": false}}',
        '[{"ts": "2026-03-04T10:15:00Z", "level": "warn", "msg": "retry scheduled"}, {"ts": "2026-03-04T10:15:02Z", "level": "info", "msg": "ok"}]',
        '{"query": "late deliveries", "top_k": 5, "filters": {"region": ["north", "east"], "min_score": 0.72}}',
    ],
    "hindi": [
        "कृपया इस रिपोर्ट का छोटा सारांश लिखिए और बताइए कि कौन से काम अगले हफ्ते तक पूरे होने चाहिए।",
        "हमारे गोदाम में कल सुबह नया माल आएगा, इसलिए टीम को जल्दी पहुँचना होगा।",
        "ग्राहक ने पूछा कि उसका ऑर्डर अब तक क्यों नहीं पहुँचा और वह पैसे वापस कैसे पा सकता है।",
        "इस महीने बिजली का बिल पिछले महीने से बहुत ज़्यादा आया है, कारण पता करना ज़रूरी है।",
        "नई नीति के अनुसार हर कर्मचारी को साल में दो बार सुरक्षा प्रशिक्षण लेना होगा।",
    ],
    "telugu": [
        "దయచేసి ఈ నివేదికను చిన్నగా సంక్షిప్తం చేసి, వచ్చే వారం లోపు పూర్తి చేయాల్సిన పనులు చెప్పండి.",
        "మా గిడ్డంగికి రేపు ఉదయం కొత్త సరుకు వస్తుంది, అందుకే బృందం త్వరగా రావాలి.",
        "తన ఆర్డర్ ఇంకా ఎందుకు రాలేదు, డబ్బు ఎలా తిరిగి పొందాలి అని కస్టమర్ అడిగారు.",
        "ఈ నెల కరెంటు బిల్లు గత నెల కంటే చాలా ఎక్కువగా వచ్చింది, కారణం తెలుసుకోవాలి.",
        "కొత్త విధానం ప్రకారం ప్రతి ఉద్యోగి సంవత్సరానికి రెండుసార్లు భద్రతా శిక్షణ తీసుకోవాలి.",
    ],
    "emoji": [
        "Great job team 🎉🎉 launch went smoothly 🚀 thanks everyone 🙏",
        "Order arrived 📦 but the mug was broken 😞 can I get a replacement? ☕",
        "Weekend plan: 🏃 run, 📚 read, 🍕 pizza, 🎮 games 😄",
        "Status: ✅ build ✅ tests ❌ deploy ⚠️ retrying in 5 min ⏳",
        "Family trip 👨‍👩‍👧‍👦 to the beach 🏖️ with sunscreen 🧴 and snacks 🍉🍪",
    ],
}

# Separate training text for the from-scratch BPE (English prose plus a little code).
BPE_TRAINING_TEXT = (
    "The team reviewed the plan and agreed to ship the update after the tests passed. "
    "Every request is counted before it is sent, and every reply is counted when it comes back. "
    "A token is a small piece of text; common words become one token and rare words split into several. "
    "The planner reads the report, writes a summary, and sends the summary to the owner of each task. "
    "When the queue grows, the service sheds load and returns a clear error instead of waiting forever. "
    "def count(text):\n    return len(text.split())\n\nfor item in items:\n    total += item.cost\n"
    "The customer asked where the order was, and the agent checked the tracking page and replied. "
    "Costs depend on input tokens and output tokens, and output tokens usually cost more than input tokens. "
) * 4


def all_samples() -> list[tuple[str, str]]:
    return [(cat, s) for cat in CATEGORIES for s in SAMPLES[cat]]
