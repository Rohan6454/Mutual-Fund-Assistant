# Phase 4 — LLM Response Generation & Guardrails

## Objective

Generate concise, factual, source-backed responses using Google Gemini with comprehensive input/output guardrails for facts-only compliance.

## Scope

- System prompt engineering (facts-only, context-grounded, max 3 sentences)
- Gemini LLM integration (gemini-2.0-flash, temperature=0.1)
- Input guardrails (PII regex, advisory keywords, comparison detection)
- Output guardrails (sentence cap, advice scan, PII scan)
- Response formatting (answer + citation + footer)
- Hallucination mitigation (confidence threshold, number verification)

## Key files (this folder)

| File | Purpose |
|------|---------|
| `phase-4-response-generation/generator.py` | Gemini LLM call + formatting + output validation |
| `phase-4-response-generation/output_guardrails.py` | Output guardrail checks + refusal mapping |
| `phase-4-response-generation/rag_engine.py` | Orchestrates Phase 3 retrieval -> generation/refusal |
| `config/prompts.py` | Prompts + refusal/no-info templates + educational links |

## Response Format

```
{answer in 1-3 sentences}

Source: {primary_source_url}
Last updated from sources: {date}
```

## Gemini Configuration

| Parameter | Value |
|-----------|-------|
| Model | gemini-2.0-flash |
| Temperature | 0.1 |
| Max output tokens | 256 |
| Top-p | 0.95 |

## Dependencies

- `google-generativeai` — Gemini API
- `re` — Regex for guardrails (stdlib)

## Connections

- **Inputs from Phase 3:** RetrievalResult (chunks + metadata)
- **Outputs to Phase 5:** Formatted response string, source URL, intent classification
