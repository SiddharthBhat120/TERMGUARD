# TermGuard: demo script, resume bullets, interview prep

## 2-minute demo script

1. **Problem (15 s).** "When I rented my first flat, I signed an agreement that let the owner keep my deposit for any reason. Students sign these every day. TermGuard reads the agreement and shows you the risky lines before you sign."
2. **Upload (15 s).** Click the *Bengaluru Strict* sample. Point at the verdict stamp: "10 clauses to question." Point at the key facts row: rent, deposit, lock-in, notice, all copied exactly from the document.
3. **Proof (30 s).** Click *Deposit can be kept*. The PDF jumps to clause 4 and the line is highlighted. "Every point quotes the document. If the quote is not on the page, my code drops the finding. That is how I stop the AI from making things up."
4. **Missing items (15 s).** Open *Not mentioned*: "No deadline for returning the deposit. A fair agreement has one, so ask."
5. **Language (10 s).** Switch to ಕನ್ನಡ or हिंदी. "The explanation changes, the quote stays in the original."
6. **Privacy (15 s).** Point at the footer line: "9 personal details hidden before analysis, file deletes itself in 60 minutes." Click *Delete now*.
7. **Numbers (20 s).** Open `eval/results.md`: "98% precision, 89% recall on 88 labelled clauses, zero findings without a verified quote. The failure section lists exactly what it misses."

## Resume bullets

- Built **TermGuard**, a FastAPI + React tool that flags risky clauses in rental agreements and offer letters, with every finding tied to a verbatim, position-highlighted quote from the uploaded PDF (text and scanned via OCR).
- Designed a quote-verification layer and a 24-item YAML red-flag checklist; reached **89% recall and 98% precision on 88 hand-labelled clauses** across 11 documents with **zero uncited findings**, and documented every failure case.
- Added privacy by design: personal details (names, Aadhaar, PAN, phones, addresses) redacted before any LLM call, auto-deletion of uploads, and plain-language explanations in English, Hindi and Kannada (Flesch reading ease 83).

> The scores are measured on synthetic sample documents. If you label real documents, update the numbers from your new `eval/results.md`.

## 10 interview questions with answers

**1. What is hallucination, and how does your quote check stop it?**
Hallucination is when a model writes something fluent that is not true or not in the source. I make every finding include an exact quote, then search for that quote in the clause text in code. Spacing and quote marks are normalised; the words are not. If the search fails, the finding is dropped and counted. The model can still be wrong about *how risky* a real line is, but it cannot show the user a clause that is not in their document.

**2. Precision or recall: which matters more here?**
Recall. Missing a forfeiture clause can cost a student their whole deposit; an extra explanation costs them a minute of reading. So the patterns lean towards catching more. Precision is still protected because every finding is quoted, so a false alarm is visible and easy to dismiss.

**3. Why a written checklist instead of just asking the AI "is this risky?"**
Three reasons. It is auditable: anyone can read `rental.yaml` and see what we look for and why. It is consistent: the same clause gets the same answer every time. And it is measurable: I can compute precision and recall per checklist item. The LLM only chooses among checklist candidates; it cannot invent new categories.

**4. How do you protect users' private documents?**
Regex rules (and optional spaCy NER) replace names, phone numbers, emails, Aadhaar, PAN, account numbers and addresses with placeholders like `[PERSON_1]` before anything goes to the LLM. The mapping stays on my server. Files auto-delete after 60 minutes, there is a delete button, logs never contain document text, and the repo has no real documents. A test checks that the prompt sent to the LLM contains no names or phone numbers.

**5. How would you handle laws that differ between states?**
Add a `state` field to checklist items, ask the user for their state, and load state-specific rules on top of the general list, for example the Model Tenancy Act's two-month deposit cap only where a state has adopted it. Until then the app says clearly that rules differ by state and points to a lawyer for serious cases.

**6. How do you find the position of a quote to highlight it?**
During extraction I keep every line with its page, bounding box and character offsets into the full text. When a quote is verified I know its character span, so I find the lines that overlap it and estimate the horizontal start and end from character positions. The frontend scales those PDF-point boxes to the rendered canvas size.

**7. How does clause splitting work, and what if there is no numbering?**
Each line is checked against patterns for `1.`, `2.1`, `(a)`, `Clause 5` and short ALL-CAPS headings, with guards so amounts like `1,00,000` and dates are not headings. If fewer than three headings are found, I fall back to PDF text blocks (paragraphs). With an LLM key, the model groups paragraphs into titled clauses, and I only accept its answer if it covers every paragraph once, in order.

**8. How do you detect scanned PDFs?**
If a page has fewer than about 25 characters of text but contains images, it is treated as a scan. I render it at 300 DPI and run Tesseract, which gives words with boxes; I group them into lines and convert pixels back to PDF points so highlighting works the same way.

**9. What happens if the LLM returns bad JSON or is down?**
Every reply is parsed and validated with Pydantic. On any failure, that batch of clauses falls back to the rule engine, so the user still gets a result. The model can also only use checklist ids that were candidates for that clause; anything else is ignored.

**10. What would you improve next?**
Label 30 to 50 real, redacted documents to get honest numbers; add state-specific rules; use sentence embeddings for matching by default; let users mark a finding as "not relevant" to collect feedback; and add word-level highlight boxes from PyMuPDF instead of estimating inside a line.
