import os
import json
import re
from typing import List, Dict

try:
    from groq import Groq
except Exception:
    Groq = None  # type: ignore


DEFAULT_MODEL = os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant')
LAST_SOURCE = 'mock'  # 'groq' when API returns usable items
LAST_ERROR: str | None = None


def _get_api_key() -> str | None:
    # Read on each call so changes in .env are picked up without restart in dev
    return os.getenv('GROQ_API_KEY')


def _get_model() -> str:
    return os.getenv('GROQ_MODEL', DEFAULT_MODEL)


MOCK_QUESTIONS: List[Dict] = [
    {
        'text': 'Which statement best describes formative assessment?',
        'choices': [
            'An evaluation at the end of a course to assign grades',
            'A process to monitor learning and give feedback during instruction',
            'A standardized test administered annually',
            'An accreditation requirement for institutions',
        ],
    },
    {
        'text': 'In a multiple-choice question, what is the distractor?',
        'choices': [
            'The correct answer',
            'Any incorrect option intended to mislead',
            'The question stem',
            'The explanation after submission',
        ],
    },
]


def _extract_json_array(s: str) -> str | None:
    if not s:
        return None
    m = re.search(r"\[.*\]", s, flags=re.DOTALL)
    return m.group(0) if m else None


def _normalize_items(items: List[Dict]) -> List[Dict]:
    out: List[Dict] = []
    for it in items:
        qtext = it.get('text') or it.get('question') or it.get('prompt')
        choices = it.get('choices') or it.get('options') or []
        if qtext and isinstance(choices, list):
            out.append({'text': str(qtext).strip(), 'choices': [str(c).strip() for c in choices[:4]]})
    return out


def generate_exit_tickets_from_text(text: str, max_tickets: int = 3) -> List[Dict]:
    """Create short-response exit ticket prompts from text using Groq.

    Returns a list of dicts with keys: text (prompt), choices is empty list.
    Falls back to a small mock set when the API key is missing or on errors.
    """
    global LAST_SOURCE, LAST_ERROR
    api_key = _get_api_key()
    model = _get_model()
    if not api_key or Groq is None:
        LAST_SOURCE = 'mock'
        LAST_ERROR = None if api_key else 'Missing GROQ_API_KEY'
        return [
            {'text': 'In 2–3 sentences, explain one new concept you learned today and how you might apply it next week.', 'choices': []},
            {'text': 'Describe a real-world scenario where today’s topic would be useful. What steps would you take?', 'choices': []},
            {'text': 'What part of today’s lesson still feels unclear, and how would you try to resolve it?', 'choices': []},
        ][:max_tickets]

    client = Groq(api_key=api_key)

    system_msg = (
        "You generate concise, open-ended exit ticket prompts that require students to apply the material. "
        "Only output JSON as requested; no prose."
    )
    user_prompt = (
        "From the material below, write up to {n} exit ticket prompts that require short written responses.\n"
        "Each item must be a JSON object with key: text (string prompt). Do not include choices.\n"
        "Return a single JSON array only. No explanations.\n\n"
        "MATERIAL:\n{material}"
    ).format(n=max_tickets, material=(text or '')[:12000])

    fallbacks = []
    fb_env = os.getenv('GROQ_FALLBACK_MODEL')
    if fb_env and fb_env != model:
        fallbacks.append(fb_env)
    for cand in ('llama-3.2-11b-text-preview', 'mixtral-8x7b-32768'):
        if cand != model and cand not in fallbacks:
            fallbacks.append(cand)

    errors: list[str] = []
    for m in [model] + fallbacks:
        try:
            resp = client.chat.completions.create(
                model=m,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=800,
            )
            content = resp.choices[0].message.content if resp.choices else ''
            try:
                data = json.loads(content)
            except Exception:
                arr = _extract_json_array(content)
                data = json.loads(arr) if arr else []
            # normalize: map to text + empty choices
            out: List[Dict] = []
            for it in data if isinstance(data, list) else []:
                t = it.get('text') or it.get('prompt') or it.get('question')
                if t:
                    out.append({'text': str(t).strip(), 'choices': []})
            if out:
                LAST_SOURCE = 'groq'
                LAST_ERROR = None
                return out[:max_tickets]
            errors.append(f"{m}: Empty or unparseable model output")
        except Exception as e:
            errors.append(f"{m}: {str(e)[:200]}")

    LAST_SOURCE = 'mock'
    LAST_ERROR = '; '.join(errors)[:300] if errors else 'Unknown error'
    return [
        {'text': 'In 2–3 sentences, explain one new concept you learned today and how you might apply it next week.', 'choices': []},
        {'text': 'Describe a real-world scenario where today’s topic would be useful. What steps would you take?', 'choices': []},
        {'text': 'What part of today’s lesson still feels unclear, and how would you try to resolve it?', 'choices': []},
    ][:max_tickets]


def generate_questions_from_text(text: str, max_questions: int = 6) -> List[Dict]:
    """Create multiple-choice questions from text using Groq chat completions.

    Returns a list of dicts with keys: text, choices (list[str]).
    Falls back to a small mock set when the API key is missing or on errors.
    """
    global LAST_SOURCE, LAST_ERROR
    api_key = _get_api_key()
    model = _get_model()
    if not api_key or Groq is None:
        LAST_SOURCE = 'mock'
        LAST_ERROR = None if api_key else 'Missing GROQ_API_KEY'
        return MOCK_QUESTIONS[:max_questions]

    client = Groq(api_key=api_key)

    system_msg = (
        "You generate clear, concise multiple-choice questions from provided teaching materials. "
        "Only output valid JSON as requested; do not include prose or markdown."
    )

    user_prompt = (
        "From the material below, write up to {n} multiple-choice questions.\n"
        "Each item must be a JSON object with keys: text (string), choices (array of exactly 4 strings).\n"
        "Return a single JSON array only. No explanations.\n\n"
        "MATERIAL:\n{material}"
    ).format(n=max_questions, material=(text or '')[:12000])

    # Try the requested model, then a small set of known fallbacks
    fallbacks = []
    fb_env = os.getenv('GROQ_FALLBACK_MODEL')
    if fb_env and fb_env != model:
        fallbacks.append(fb_env)
    for cand in ('llama-3.1-8b-instant'):
        if cand != model and cand not in fallbacks:
            fallbacks.append(cand)

    errors: list[str] = []
    for m in [model] + fallbacks:
        try:
            resp = client.chat.completions.create(
                model=m,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1200,
            )
            content = resp.choices[0].message.content if resp.choices else ''
            try:
                data = json.loads(content)
            except Exception:
                arr = _extract_json_array(content)
                data = json.loads(arr) if arr else []
            normalized = _normalize_items(data)
            if normalized:
                LAST_SOURCE = 'groq'
                LAST_ERROR = None
                return normalized[:max_questions]
            errors.append(f"{m}: Empty or unparseable model output")
        except Exception as e:
            msg = str(e)
            errors.append(f"{m}: {msg[:200]}")

    LAST_SOURCE = 'mock'
    LAST_ERROR = '; '.join(errors)[:300] if errors else 'Unknown error'
    return MOCK_QUESTIONS[:max_questions]
