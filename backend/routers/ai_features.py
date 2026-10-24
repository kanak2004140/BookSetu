"""AI endpoints. Handlers are plain `def` so blocking PDF/OpenAI calls run in the threadpool."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Book, User
from ..schemas import (
    AIAskQuestionRequest, AIAskQuestionResponse, AIBookSummarizeRequest, AIBookSummarizeResponse,
    AIChatRequest, AIChatResponse, AIExplainTextRequest, AIExplainTextResponse, AIKeyConceptsResponse,
)
from ..services import AIService, api_key_configured

router = APIRouter(prefix="/api/ai", tags=["AI Features"])


def book_pdf(book_id: int, db: Session) -> str:
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Book with ID {book_id} not found")
    if not book.pdf_file:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "PDF file for this book is not available")
    return book.pdf_file


@router.get("/health")
def ai_health_check():
    return {"ai_provider": "OpenAI", "api_key_configured": api_key_configured()}


@router.post("/chat", response_model=AIChatResponse)
def chat(request: AIChatRequest, current_user: User = Depends(get_current_user)):
    result = AIService.padhai_chat(request.message)
    return AIChatResponse(**{"response": "Sorry, I couldn't answer that right now.", **result})


@router.post("/summarize-book/{book_id}", response_model=AIBookSummarizeResponse)
def summarize_book(
    book_id: int,
    request: AIBookSummarizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AIService.summarize_book(book_pdf(book_id, db), request.summary_length)


@router.post("/explain-text", response_model=AIExplainTextResponse)
def explain_text(
    request: AIExplainTextRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AIService.explain_text(book_pdf(request.book_id, db), request.selected_text)


@router.post("/ask-book", response_model=AIAskQuestionResponse)
def ask_question(
    request: AIAskQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AIService.ask_question(book_pdf(request.book_id, db), request.question)


@router.get("/key-concepts/{book_id}", response_model=AIKeyConceptsResponse)
def get_key_concepts(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AIService.get_key_concepts(book_pdf(book_id, db))
