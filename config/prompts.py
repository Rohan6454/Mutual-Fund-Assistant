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

CONTEXT_INJECTION_TEMPLATE = """Use ONLY the following context to answer the user's question. The context contains factual information from mutual fund documents.

Context:
---
{chunk_1}
---
{chunk_2}
---
{chunk_3}
---

Instructions:
1. If the context contains relevant information to answer the user's question, use it to provide a specific, factual answer
2. If the context mentions the specific scheme or concept asked about, extract and present that information clearly
3. If the context has related but not exact information, acknowledge what is available and suggest how it might help
4. Only respond with "I do not have that information in my current sources" if the context is completely empty or irrelevant

User Question: {user_query}"""

REFUSAL_TEMPLATE = (
    "I'm designed to provide factual information only and cannot offer investment "
    "advice or recommendations. For investment guidance, please consult a "
    "SEBI-registered investment advisor. You may find helpful resources at: {educational_link}"
)

NO_INFO_TEMPLATE = (
    "I don't have specific information about that in my current sources, but I can help guide you. "
    "I have information about mutual fund basics, platform operations, and general investment concepts. "
    "Could you tell me more about what you're looking for? For example, I can help with: "
    "1. General concepts like expense ratios, NAV, AUM, SIP, SWP, ELSS, "
    "2. How to find scheme information on AMC websites (ICICI Prudential, HDFC, Nippon India), "
    "3. How to download account statements and scheme documents, "
    "4. Platform help for Groww and other investment platforms, "
    "5. Basic mutual fund operations and regulations, or "
    "6. Something else about mutual fund investments?"
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
