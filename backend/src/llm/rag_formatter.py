class RAGFormatter:
    """Builds prompt context and instructions for constitution Q&A."""

    @staticmethod
    def format_context(articles: list[dict]) -> str:
        if not articles:
            return "No relevant articles found."

        context_lines = []
        for index, article in enumerate(articles, 1):
            context_lines.append(f"{article['citation']}: {article['title']}\n{article['text']}")
            if "score" in article:
                context_lines.append(f"(Relevance Score: {article['score']:.2f})")
            context_lines.append("")

        return "\n".join(context_lines)

    @staticmethod
    def build_system_prompt() -> str:
        return ("""
            1. Determine what the question is asking.

            2. Use all relevant parts of the context.

            3. Adapt the answer style:
            - What → concise explanation
            - Who → identify the person/body
            - When → date/time
            - Where → location/jurisdiction
            - How → explain the procedure step-by-step
            - Why → explain the reason
            - Can/May/Is → answer Yes/No first, then explain

            4. Keep the answer proportional to the question.
            Do not add unnecessary legal background and complex terminology.

            5. Cite the relevant article(s).

            6. If the context does not contain the answer, say:
            "The provided articles do not contain the answer."
        """)   

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
