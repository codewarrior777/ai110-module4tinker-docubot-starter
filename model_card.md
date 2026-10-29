# DocuBot Model Card

This model card is a short reflection on your DocuBot system. Fill it out after you have implemented retrieval and experimented with all three modes:

1. Naive LLM over full docs  
2. Retrieval only  
3. RAG (retrieval plus LLM)

Use clear, honest descriptions. It is fine if your system is imperfect.

---

## 1. System Overview

**What is DocuBot trying to do?**  
DocuBot is a documentation assistant that uses Retrieval-Augmented Generation (RAG) to answer developer questions. Its goal is to provide accurate answers by retrieving relevant text snippets from a codebase's markdown documentation and passing them to a Language Model, strictly preventing the model from hallucinating.

**What inputs does DocuBot take?**  
- A user question (e.g., "Where is the auth token generated?").
- A folder containing `.md` or `.txt` files (`docs/`).
- An API Key provided via a `.env` file (using OpenRouter for LLM access).

**What outputs does DocuBot produce?**
- **Naive Mode:** A generic LLM-generated answer.
- **Retrieval Mode:** Raw text snippets from the docs.
- **RAG Mode:** A concise, LLM-generated answer based *only* on the retrieved snippets, including citations of the files used.

---

## 2. Retrieval Design

**How does your retrieval system work?**  
- **Indexing:** The system reads all documents and splits them into words. Punctuation is stripped, and words are lowercased. It builds an inverted index (a dictionary) mapping every word to the files it appears in.
- **Scoring:** For a user query, it counts how many times the meaningful words in the query appear in the document. 
- **Choosing Snippets:** The text is split line-by-line into chunks. The system scores each chunk, sorts them by the highest score, and returns the top 3 chunks.

**What tradeoffs did you make?**  
- **Speed vs. Precision:** Keyword matching (using exact words) is incredibly fast and requires no heavy machine learning models, but it fails if the user asks a question using synonyms (e.g., searching "login" when the doc says "auth").
- **Simplicity vs. Context:** Splitting chunks by line makes retrieval precise (it grabs the exact line), but it can sometimes split a sentence in half, losing surrounding context.

---

## 3. Use of the LLM (OpenRouter API)

**When does DocuBot call the LLM and when does it not?**  
- **Naive LLM mode:** Calls the LLM for every query but provides **no context**. 
- **Retrieval only mode:** Does **not** call the LLM at all. It only uses the local Python index and returns raw text.
- **RAG mode:** Calls the retrieval system first, then passes the retrieved snippets *and* the query to the LLM.

**What instructions do you give the LLM to keep it grounded?**  
The prompt explicitly tells the LLM:
1. "Use only the information in the snippets."
2. "If the snippets do not provide enough evidence, refuse to guess."
3. "If not enough evidence, reply exactly: 'I do not know based on the docs I have.'"
4. "Briefly mention which files you relied on."

---

## 4. Experiments and Comparisons

| Query | Naive LLM: helpful or harmful? | Retrieval only: helpful or harmful? | RAG: helpful or harmful? | Notes |
|------|---------------------------------|--------------------------------------|---------------------------|-------|
| Where is the auth token generated? | Harmful | Helpful | Highly Helpful | Naive hallucinated generic internet advice. RAG cited `AUTH.md` and `generate_access_token`. |
| How do I connect to the database? | Harmful | Helpful | Highly Helpful | Retrieval found the `DATABASE_URL` line. RAG explained the format clearly. |
| Which endpoint lists all users? | Harmful | Helpful | Highly Helpful | Naive guessed REST conventions. RAG found the exact endpoint in `API_REFERENCE.md`. |
| How do I cook a pizza? | Harmful | Helpful (Refused) | Helpful (Refused) | Guardrails successfully prevented the system from returning random documentation snippets. |

**What patterns did you notice?**  
- **Naive LLM** looks impressive at first because it speaks fluently, but it is untrustworthy because it invents APIs that don't exist in the project.
- **Retrieval only** is clearly better when you just want to `Ctrl+F` and read the developer's exact words, but it's hard to read if multiple files are returned.
- **RAG** is clearly better than both because it combines the speed of retrieval with the readability and synthesis of an LLM, without the hallucination.

---

## 5. Failure Cases and Guardrails

**Failure case 1:** 
- *Question:* "How do I cook a pizza?"
- *What did it do:* Initially, before the guardrail, it returned random snippets because words like "how", "do", and "I" matched the docs.
- *What should have happened:* It should say "I do not know".
- *Fix:* We added a list of `STOPWORDS` to ignore common English words.

**Failure case 2:**
- *Question:* "How do I log in?"
- *What did it do:* It failed to retrieve anything because the docs use the word "auth" or "token" instead of "log in".
- *What should have happened:* It should have found the authentication docs.
- *Fix:* This is a limitation of keyword search. To fix it truly, we would need semantic search (embeddings).

**When should DocuBot say "I do not know based on the docs I have"?**  
1. When the user asks a question completely unrelated to the software project.
2. When the question is relevant, but the specific feature isn't documented yet.

**What guardrails did you implement?**  
- **Stopword Filtering:** Ignored common words ("the", "how", "is") to prevent false matches.
- **Min Score Threshold:** If a snippet doesn't have a score of at least 1 (meaning no meaningful words matched), the system returns "I do not know" instead of forcing a bad answer.
- **Strict Prompting:** The LLM is instructed to refuse if the snippets don't answer the question.

---

## 6. Limitations and Future Improvements

**Current limitations**  
1. **Keyword only:** It can't understand synonyms or typos (e.g., asking for "login" instead of "auth").
2. **Line-based chunking:** Splitting by newlines can cut off context if a bullet point spans multiple lines.
3. **API Dependency:** The RAG mode requires an internet connection and relies on free external APIs which can change or fail.

**Future improvements**  
1. **Vector Embeddings:** Implement FAISS or ChromaDB to allow semantic search instead of exact word matching.
2. **Better Chunking:** Split documents by paragraphs or markdown headers rather than just newlines.
3. **Local LLM:** Run a small model locally (like Ollama) to remove the dependency on external APIs.

---

## 7. Responsible Use

**Where could this system cause real world harm if used carelessly?**  
If a developer asks "How do I authenticate the admin endpoint?" and the docs are outdated, DocuBot might say "I don't know" (which is safe). But if a developer over-trusts the RAG mode and it accidentally pulls a snippet from an old deprecated file, it might lead the developer to use insecure authentication methods. Over-trusting the LLM is dangerous if the source docs are flawed.

**What instructions would you give real developers who want to use DocuBot safely?**  
- Always click and read the cited source files (`[AUTH.md]`) that DocuBot mentions to verify the context.
- Treat DocuBot as a search accelerator, not an absolute oracle.
- Do not blindly copy-paste security keys or configurations suggested by the AI without verifying them against the actual codebase.