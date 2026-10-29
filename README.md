# DocuBot

DocuBot is a small documentation assistant that helps answer developer questions about a codebase.  
It can operate in three different modes:

1. **Naive LLM mode**  
   Sends the entire documentation corpus to an LLM and asks it to answer the question.

2. **Retrieval only mode**  
   Uses a custom indexing and scoring system to retrieve relevant snippets without calling an LLM.

3. **RAG mode (Retrieval Augmented Generation)**  
   Retrieves relevant snippets, then asks the LLM to answer using *only* those snippets.

The docs folder contains realistic developer documents (API reference, authentication notes, database notes), but these files are **just text**. They support retrieval experiments and do not require students to set up any backend systems.

---

## Setup

### 1. Install Python dependencies

    pip install -r requirements.txt

### 2. Configure environment variables

Copy the example file:

    cp .env.example .env

Then edit `.env` to include your API key. 
*Note: Although the environment variable is named `GEMINI_API_KEY` (to match the starter code), this implementation uses **OpenRouter** to access free LLMs (like Llama 3).*

    GEMINI_API_KEY=sk-or-v1-your_openrouter_key_here

If you do not set a key, you can still run **Retrieval only mode** (Mode 2).

---

## Running DocuBot

Start the program:

    python main.py

Choose a mode:

- **1**: Naive LLM (The model answers without looking at your docs)  
- **2**: Retrieval only (No LLM, uses the custom Python index)  
- **3**: RAG (Retrieval + LLM)

You can use built-in sample queries or type your own.

---

## Key Implementations (Module 4)

### Retrieval System (`docubot.py`)
- **Inverted Index:** Maps words to documents for fast lookups.
- **Scoring:** Counts keyword matches per line.
- **Guardrails:** Implements a `STOPWORDS` list (ignoring "how", "do", "I", etc.) and a `min_score` threshold. If a query (like "How do I cook a pizza?") has no valid keyword matches, the system refuses to answer with *"I do not know based on these docs."*

### LLM Integration (`llm_client.py`)
- Adapted the original Gemini client to use the **OpenRouter API** (which is OpenAI-compatible).
- Uses strict prompting to force the model to cite its sources from the snippets.

---

## Running Retrieval Evaluation (optional)

    python evaluation.py

This prints simple retrieval hit rates for sample queries.

---

## Modifying the Project

You will primarily work in:

- `docubot.py`  
  Implement or improve the retrieval index, scoring, and snippet selection.

- `llm_client.py`  
  Adjust the prompts and behavior of LLM responses.

- `dataset.py`  
  Add or change sample queries for testing.

---

## Requirements

- Python 3.9+
- An OpenRouter API key for LLM features (only needed for modes 1 and 3)
- No database, no server setup, no external services besides LLM calls