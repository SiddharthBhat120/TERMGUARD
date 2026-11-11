"""Find which checklist items a clause is most similar to.

We use TF-IDF cosine similarity written in plain Python, so the app installs fast on any
machine. If `sentence-transformers` is installed and USE_EMBEDDINGS=1, it uses real
embeddings instead (same interface).
"""
from __future__ import annotations

import math
import os
import re
from collections import Counter

from .models import ChecklistItem

STOP = set(
    "the a an and or of to in on for by with any all be is are shall will may this that such as at from "
    "it its your you he she his her their them which who whom per under upon into than other said".split()
)


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z]+", text.lower())
    out = []
    for w in words:
        if w in STOP or len(w) < 3:
            continue
        # tiny stemmer: deposits -> deposit, increased -> increas
        for suf in ("ing", "ed", "es", "s"):
            if len(w) > 5 and w.endswith(suf):
                w = w[: -len(suf)]
                break
        out.append(w)
    return out


class TfidfMatcher:
    def __init__(self, items: list[ChecklistItem]):
        self.items = items
        docs = [_tokens(f"{i.name} {i.look_for} {i.example} {i.why}") for i in items]
        df: Counter[str] = Counter()
        for d in docs:
            df.update(set(d))
        n = len(docs)
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
        self.vecs = [self._vec(d) for d in docs]

    def _vec(self, toks: list[str]) -> dict[str, float]:
        tf = Counter(toks)
        v = {t: c * self.idf.get(t, 0.0) for t, c in tf.items() if t in self.idf}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / norm for t, x in v.items()}

    def top(self, text: str, k: int = 3, min_score: float = 0.12) -> list[tuple[ChecklistItem, float]]:
        q = self._vec(_tokens(text))
        scored = [(item, sum(q.get(t, 0.0) * w for t, w in vec.items())) for item, vec in zip(self.items, self.vecs)]
        scored.sort(key=lambda p: p[1], reverse=True)
        return [(i, s) for i, s in scored[:k] if s >= min_score]


class EmbeddingMatcher:  # pragma: no cover - optional heavy dependency
    def __init__(self, items: list[ChecklistItem]):
        from sentence_transformers import SentenceTransformer

        self.items = items
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.emb = self.model.encode([f"{i.name}. {i.look_for} {i.example}" for i in items], normalize_embeddings=True)

    def top(self, text: str, k: int = 3, min_score: float = 0.3) -> list[tuple[ChecklistItem, float]]:
        q = self.model.encode([text], normalize_embeddings=True)[0]
        scores = (self.emb @ q).tolist()
        pairs = sorted(zip(self.items, scores), key=lambda p: p[1], reverse=True)
        return [(i, float(s)) for i, s in pairs[:k] if s >= min_score]


def make_matcher(items: list[ChecklistItem]) -> TfidfMatcher | EmbeddingMatcher:
    if os.getenv("USE_EMBEDDINGS") == "1":
        try:
            return EmbeddingMatcher(items)
        except Exception:  # library missing or model download failed
            pass
    return TfidfMatcher(items)
