"""
OpenRouter client wrapper used by DocuBot.
"""

import os
import requests

# Usamos el enrutador automático de modelos gratuitos.
# Esto evita errores 404 si un modelo específico desaparece.
OPENROUTER_MODEL_NAME = "openrouter/free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

class GeminiClient:
    """
    Wrapper around the OpenRouter API.
    (Class name kept as GeminiClient to avoid breaking main.py)
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Missing GEMINI_API_KEY environment variable. "
                "Set it in your shell or .env file to enable LLM features."
            )
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "DocuBot Tinker"
        }

    def _call_openrouter(self, prompt):
        """Helper to send a request to OpenRouter."""
        payload = {
            "model": OPENROUTER_MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}]
        }
        try:
            response = requests.post(
                OPENROUTER_URL, 
                headers=self.headers, 
                json=payload, 
                timeout=30
            )
            if response.status_code != 200:
                print(f"DEBUG - Error de OpenRouter: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"API error — could not generate answer. ({type(e).__name__}: {e})"

    # -----------------------------------------------------------
    # Phase 0: naive generation over full docs
    # -----------------------------------------------------------

    def naive_answer_over_full_docs(self, query, all_text):
        prompt = f"""
    You are a documentation assistant. 
    Answer this developer question: {query}
    """
        return self._call_openrouter(prompt)

    # -----------------------------------------------------------
    # Phase 2: RAG style generation over retrieved snippets
    # -----------------------------------------------------------

    def answer_from_snippets(self, query, snippets):
        if not snippets:
            return "I do not know based on the docs I have."

        context_blocks = []
        for filename, text in snippets:
            block = f"File: {filename}\n{text}\n"
            context_blocks.append(block)

        context = "\n\n".join(context_blocks)

        prompt = f"""
You are a cautious documentation assistant helping developers understand a codebase.

You will receive:
- A developer question
- A small set of snippets from project files

Your job:
- Answer the question using only the information in the snippets.
- If the snippets do not provide enough evidence, refuse to guess.

Snippets:
{context}

Developer question:
{query}

Rules:
- Use only the information in the snippets. Do not invent new functions,
  endpoints, or configuration values.
- If the snippets are not enough to answer confidently, reply exactly:
  "I do not know based on the docs I have."
- When you do answer, briefly mention which files you relied on.
"""
        return self._call_openrouter(prompt)