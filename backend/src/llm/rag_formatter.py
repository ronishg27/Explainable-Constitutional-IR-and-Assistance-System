class RAGFormatter:
    """Builds prompt context and instructions for constitution Q&A."""

    @staticmethod
    def format_context(articles: list[dict]) -> str:
        if not articles:
            return "No relevant articles found."

        context_lines = []
        for index, article in enumerate(articles, 1):
            context_lines.append(f"[Article {index}]")
            context_lines.append(f"Citation: {article['citation']}")
            context_lines.append(f"Title: {article['title']}")
            context_lines.append(f"Content:\n{article['text']}")
            if "score" in article:
                context_lines.append(f"(Relevance Score: {article['score']:.2f})")
            context_lines.append("")

        return "\n".join(context_lines)

    @staticmethod
    def build_system_prompt() -> str:
        return (
            "You are a constitutional law expert specializing in the Constitution of Nepal. "
            "You must answer questions using ONLY the constitutional articles provided in the user message. "
            "The user will give you a list of retrieved articles from the Constitution of Nepal as context. "
            "Follow these rules strictly:\n"
            "1. Base your answer ONLY on the articles shown in the context below.\n"
            "2. If the context does not contain a relevant article, say: "
            "'The provided articles from the Constitution of Nepal do not address this question.'\n"
            "3. Never reference any other constitution (Indian, US, etc.) or any external knowledge.\n"
            "4. Cite articles exactly as shown in the context (e.g., [Part 3, Article 16]).\n"
            "5. Do not add headings, summaries, or explanations beyond answering the question."
        )

    @staticmethod
    def build_user_prompt(query: str, context: str) -> str:
        return f"""
CONTEXT — Constitution of Nepal:
{context}

QUESTION (Constitution of Nepal only): {query}

ANSWER based solely on the articles above:
"""
