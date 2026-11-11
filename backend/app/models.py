"""Pydantic models shared across the pipeline and the API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Risk = Literal["high", "medium", "low"]
DocType = Literal["rental", "offer_letter", "other"]


class Rect(BaseModel):
    page: int  # 0-based page index
    x0: float
    y0: float
    x1: float
    y1: float


class Line(BaseModel):
    """One line of text with its position. start/end are offsets into Document.text."""
    page: int
    block: int
    text: str
    start: int
    end: int
    rect: Rect


class PageInfo(BaseModel):
    width: float
    height: float
    ocr: bool = False


class ExtractedDoc(BaseModel):
    text: str
    lines: list[Line]
    pages: list[PageInfo]
    ocr_missing: bool = False  # a scanned page was found but Tesseract is not installed


class Clause(BaseModel):
    id: str
    number: str = ""
    title: str
    text: str
    start: int
    end: int
    body_start: int = 0  # offset inside text where the clause body begins (after a heading line)
    rects: list[Rect] = Field(default_factory=list)


class ChecklistItem(BaseModel):
    id: str
    name: str
    look_for: str
    why: str
    risk: Risk
    question: str
    example: str = ""
    explanation: str
    explanation_hi: str = ""
    explanation_kn: str = ""
    triggers: list[str] = Field(default_factory=list)
    escalate: list[str] = Field(default_factory=list)  # patterns that raise risk one level
    soften: list[str] = Field(default_factory=list)    # patterns that mean the clause is fair
    require: list[str] = Field(default_factory=list)   # the quoted sentence must also match one of these


class ExpectedItem(BaseModel):
    id: str
    name: str
    why: str
    question: str
    present: list[str]


class Checklist(BaseModel):
    doc_type: DocType
    title: str
    disclaimer: str
    items: list[ChecklistItem]
    expected: list[ExpectedItem]


class LLMFinding(BaseModel):
    """What we require the LLM to return for each finding (strict)."""
    checklist_id: str
    risk: Risk
    explanation: str = Field(min_length=10, max_length=600)
    quote: str = Field(min_length=4)
    question: str = Field(min_length=5)


class LLMFindingList(BaseModel):
    findings: list[LLMFinding]


class Finding(BaseModel):
    id: str
    clause_id: str
    clause_title: str
    checklist_id: str
    name: str
    risk: Risk
    explanation: str
    explanation_hi: str = ""
    explanation_kn: str = ""
    quote: str
    question: str
    why: str
    source: Literal["rules", "llm"]
    rects: list[Rect] = Field(default_factory=list)


class MissingItem(BaseModel):
    id: str
    name: str
    why: str
    question: str


class KeyFact(BaseModel):
    key: str
    label: str
    value: str
    quote: str
    rects: list[Rect] = Field(default_factory=list)


class Analysis(BaseModel):
    id: str
    filename: str
    doc_type: DocType
    doc_type_label: str
    engine: Literal["rules", "llm"]
    pages: list[PageInfo]
    ocr_used: bool
    ocr_missing: bool
    clauses: list[Clause]
    findings: list[Finding]
    missing: list[MissingItem]
    facts: list[KeyFact]
    counts: dict[str, int]
    dropped_unverified: int
    redactions: int
    disclaimer: str
    created_at: float
    expires_at: float
