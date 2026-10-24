"""AI features (OpenAI): book summaries, passage explanations, Q&A, key concepts and chat."""

import json
import logging
import os
from functools import lru_cache
from typing import Any, Dict

import pdfplumber
from openai import OpenAI

logger = logging.getLogger(__name__)

MAX_CONTEXT_CHARS = 15000
PDF_PAGES = 10


@lru_cache(maxsize=16)
def extract_pdf_text(pdf_path: str, max_pages: int = PDF_PAGES) -> str:
    """Text of the first `max_pages` pages, truncated for the model's context."""
    with pdfplumber.open(pdf_path) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages[:max_pages]]
    return "\n".join(pages)[:MAX_CONTEXT_CHARS]


def api_key_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _ask(system: str, user: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def _json(text: str) -> Dict[str, Any]:
    """Parse the JSON object in a model reply; empty dict if it isn't valid JSON."""
    try:
        return json.loads(text[text.index("{"): text.rindex("}") + 1])
    except ValueError:
        return {}


def _safe(fn):
    """Turn failures (missing key, bad PDF, API error) into {'success': False, 'error': ...}."""
    def wrapper(*args, **kwargs):
        if not api_key_configured():
            return {"success": False, "error": "OPENAI_API_KEY is not configured."}
        try:
            return {"success": True, **fn(*args, **kwargs)}
        except Exception as exc:
            # Details stay in the server log: provider errors can echo parts of the API key.
            logger.exception("AI request failed")
            return {"success": False, "error": f"AI service error ({type(exc).__name__}). Check the server log."}
    return wrapper


class AIService:
    @staticmethod
    @_safe
    def summarize_book(pdf_path: str, summary_length: str = "medium") -> Dict[str, Any]:
        length = {
            "short": "a 1-2 paragraph summary",
            "medium": "a 3-5 paragraph summary",
            "long": "a comprehensive 7-10 paragraph summary",
        }[summary_length]
        summary = _ask(
            "You are an expert book summarizer. Highlight the main themes and key ideas.",
            f"Provide {length} of this book content:\n\n{extract_pdf_text(pdf_path)}",
        )
        words = len(summary.split())
        return {
            "summary": summary,
            "length": summary_length,
            "words": words,
            "estimated_reading_time_minutes": max(1, words // 200),
        }

    @staticmethod
    @_safe
    def explain_text(pdf_path: str, selected_text: str) -> Dict[str, Any]:
        reply = _ask(
            "You are an expert at explaining book passages to readers of any background.",
            f'Passage: "{selected_text}"\n\nBook context:\n{extract_pdf_text(pdf_path)}\n\n'
            'Reply with JSON only: {"explanation": str, "key_concepts": [str], "importance": str}',
        )
        parsed = _json(reply)
        return {
            "selected_text": selected_text[:100],
            "explanation": parsed.get("explanation", reply),
            "key_concepts": parsed.get("key_concepts", []),
            "importance": parsed.get("importance", ""),
        }

    @staticmethod
    @_safe
    def ask_question(pdf_path: str, question: str) -> Dict[str, Any]:
        answer = _ask(
            "Answer questions about a book using only the provided content. "
            'If the answer is not in the content, say "This question cannot be fully answered based on the book content."',
            f"Book content:\n{extract_pdf_text(pdf_path, 15)}\n\nQuestion: {question}",
        )
        return {
            "question": question,
            "answer": answer,
            "confidence": "low" if "cannot" in answer.lower() else "high",
        }

    @staticmethod
    @_safe
    def get_key_concepts(pdf_path: str) -> Dict[str, Any]:
        parsed = _json(_ask(
            "You extract key information from books. Reply with JSON only.",
            f"Book content:\n{extract_pdf_text(pdf_path)}\n\n"
            'Reply with JSON only: {"main_themes": [str], "key_concepts": [str], "important_topics": [str]}',
        ))
        return {key: parsed.get(key, []) for key in ("main_themes", "key_concepts", "important_topics")}

    @staticmethod
    @_safe
    def padhai_chat(message: str) -> Dict[str, Any]:
        reply = _ask(
            "You are PadhAI, a friendly literary companion for BookSetu, a platform for buying and "
            "selling books. Recommend books with short descriptions, discuss authors and themes, "
            "and keep answers to 2-3 paragraphs.",
            message,
            max_tokens=500,
            temperature=0.8,
        )
        return {"response": reply}
