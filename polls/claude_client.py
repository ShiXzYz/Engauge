import os
import json
import re
from typing import List, Dict

import anthropic


DEFAULT_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-latest')
API_KEY = os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY')


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
    {
        'text': 'Which Python library is commonly used to parse PDF text?',
        'choices': [
            'matplotlib',
            'numpy',
            'pdfminer.six',
            'scikit-learn',
        ],
    },
]


def _extract_json_array(s: str) -> str | None:
    if not s:
        return None
    # Try to find the first JSON array in the text
    m = re.search(r"\[.*\]", s, flags=re.DOTALL)
    return m.group(0) if m else None


def _normalize_items(items: List[Dict]) -> List[Dict]:
    out: List[Dict] = []
    for it in items:
        qtext = it.get('text') or it.get('question') or it.get('prompt')
        choices = it.get('choices') or it.get('options') or []
        if qtext and isinstance(choices, list):
            # keep up to 4 choices; pad is not necessary
            out.append({'text': str(qtext).strip(), 'choices': [str(c).strip() for c in choices[:4]]})
    return out


def generate_questions_from_text(text: str, max_questions: int = 6) -> List[Dict]:
    """Create multiple-choice questions from text using Claude.

    Returns a list of dicts with keys: text, choices (list[str]).
    Falls back to a small mock set when the API key is missing or on errors.
    """
    if not API_KEY:
        return MOCK_QUESTIONS[:max_questions]

    client = anthropic.Anthropic(api_key=API_KEY)

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

    try:
        resp = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=1000,
            temperature=0.2,
            system=system_msg,
            messages=[{"role": "user", "content": user_prompt}],
        )

        # Concatenate text blocks
        parts = []
        for block in getattr(resp, 'content', []) or []:
            if getattr(block, 'type', None) == 'text':
                parts.append(block.text)
            elif isinstance(block, dict) and block.get('type') == 'text':
                parts.append(block.get('text', ''))
        text_out = "".join(parts)

        # Parse JSON strictly, or extract array substring
        payload = text_out
        try:
            data = json.loads(payload)
        except Exception:
            arr = _extract_json_array(payload)
            data = json.loads(arr) if arr else []

        normalized = _normalize_items(data)
        if normalized:
            return normalized[:max_questions]
        return MOCK_QUESTIONS[:max_questions]
    except Exception:
        return MOCK_QUESTIONS[:max_questions]
