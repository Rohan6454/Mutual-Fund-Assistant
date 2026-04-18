# System prompts, refusal templates, and educational links

SYSTEM_PROMPT = """You are a facts-only mutual fund FAQ assistant.

STRICT RULES:
1. Answer only factual, verifiable queries using the provided context. If the context does not contain the answer, say you do not have that information in your current sources.
2. Use a maximum of 3 sentences. Be concise and factual.
3. Always include exactly ONE source link in your response (no additional URLs in the answer body).
4. NEVER provide investment advice, recommendations, opinions, or comparisons.
5. NEVER fabricate information. NEVER extrapolate beyond what the context states.
6. NEVER mention that you are using "context" or "provided documents." Respond naturally.
7. Use a professional, neutral, helpful tone.
8. If the query is advisory or asks what to buy/sell/hold, refuse politely and include exactly one AMFI or SEBI educational link in that refusal."""

CONTEXT_INJECTION_TEMPLATE = """Use ONLY the following context to answer the user's question.

Context:
---
{chunk_1}
---
{chunk_2}
---
{chunk_3}
---

User Question: {user_query}"""

REFUSAL_TEMPLATE = (
    "I'm designed to provide factual information only and cannot offer investment "
    "advice or recommendations. For investment guidance, please consult a "
    "SEBI-registered investment advisor. You may find helpful resources at: {educational_link}"
)

NO_INFO_TEMPLATE = (
    "I don't have reliable information about that in my current sources. "
    "You can check the official AMC website, AMFI, or SEBI for the latest details."
)

PII_WARNING_TEMPLATE = (
    "I detected personal information in your message. For your security, please "
    "do not share PAN, Aadhaar, account numbers, or other sensitive details. "
    "I can only answer factual questions about mutual fund schemes."
)

OUT_OF_SCOPE_TEMPLATE = (
    "I can only answer factual questions about mutual fund schemes from "
    "ICICI Prudential, HDFC, and Nippon India AMCs. "
    "Please ask about topics like expense ratios, exit loads, SIP amounts, "
    "or scheme details."
)

# Educational redirect links (used in refusal responses)
EDUCATIONAL_LINKS = {
    "general": "https://www.amfiindia.com/investor-corner/knowledge-center",
    "investor_corner": "https://www.amfiindia.com/investor-corner",
    "sebi_mf_faq": "https://www.sebi.gov.in/sebi_data/faqfiles/mutual_funds.html",
    "mf_basics": "https://www.amfiindia.com/mutual-fund/new-to-mutual-fund",
}

# Known scheme names for fuzzy matching (across all 3 AMCs)
KNOWN_SCHEMES = [
    # ICICI Prudential
    "ICICI Prudential Bluechip Fund",
    "ICICI Prudential Flexicap Fund",
    "ICICI Prudential Value Discovery Fund",
    # HDFC Mutual Fund
    "HDFC Flexi Cap Fund",
    "HDFC Large Cap Fund",
    "HDFC Mid-Cap Opportunities Fund",
    "HDFC Small Cap Fund",
    # Nippon India Mutual Fund
    "Nippon India Large Cap Fund",
    "Nippon India Small Cap Fund",
    "Nippon India Growth Fund",
    "Nippon India Tax Saver (ELSS) Fund",
]

# AMC name mapping for scheme -> AMC resolution
AMC_MAPPING = {
    "ICICI Prudential Bluechip Fund": "ICICI Prudential",
    "ICICI Prudential Flexicap Fund": "ICICI Prudential",
    "ICICI Prudential Value Discovery Fund": "ICICI Prudential",
    "HDFC Flexi Cap Fund": "HDFC Mutual Fund",
    "HDFC Large Cap Fund": "HDFC Mutual Fund",
    "HDFC Mid-Cap Opportunities Fund": "HDFC Mutual Fund",
    "HDFC Small Cap Fund": "HDFC Mutual Fund",
    "Nippon India Large Cap Fund": "Nippon India Mutual Fund",
    "Nippon India Small Cap Fund": "Nippon India Mutual Fund",
    "Nippon India Growth Fund": "Nippon India Mutual Fund",
    "Nippon India Tax Saver (ELSS) Fund": "Nippon India Mutual Fund",
}
