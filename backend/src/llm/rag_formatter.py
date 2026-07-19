class RAGFormatter:
    """Builds prompt context and instructions for constitution Q&A."""

    @staticmethod
    def format_context(articles: list[dict]) -> str:
        if not articles:
            return "No relevant articles found."

        context_lines = []
        for index, article in enumerate(articles, 1):
            # context_lines.append(f"[Article {index}]")
            # context_lines.append(f"Citation: {article['citation']}")
            # context_lines.append(f"Title: {article['title']}")
            # context_lines.append(f"Content:\n{article['text']}")
            context_lines.append(f"{article['citation']}: {article['title']}\n{article['text']}")
            if "score" in article:
                context_lines.append(f"(Relevance Score: {article['score']:.2f})")
            context_lines.append("")

        return "\n".join(context_lines)

    @staticmethod
    def build_system_prompt() -> str:
        return (
            "You are a legal QA assistant for the Constitution of Nepal.\n"
            "Answer ONLY the questions using the Context.\n\n"

            "Important Instructions:\n"
            "- Focus ONLY on the question.\n"
            "- Do NOT explain all articles.\n"
            "- Select ONLY the relevant parts of the context.\n"
            "- Ignore unrelated information.\n"
            "- Ensure the user understands the answer.\n"
            "- Explain the answer to the question using simple language.\n\n"

            "Answer Guidelines:\n"
            "- First, give a clear answer to the question in 2–4 sentences.\n"
            "- Then, cite the relevant article(s) in brackets.\n"
            "- Do NOT summarize all articles.\n"
            "- Do NOT add extra explanation beyond what is needed.\n\n"
            "- If necessary, provide a brief explanation of the answer in 3-5 sentences.\n"

            "If the answer is not in the context, STRICTLY say:\n"
            "'The provided articles do not contain the answer.'"
        )   

    @staticmethod
    def build_user_prompt(query: str, context: str) -> str:
        return f"""
    Context:
    {context}

    Question:
    {query}
    
    Task:
    Find the exact answer to the question using the context above.
    Answer:
    """
