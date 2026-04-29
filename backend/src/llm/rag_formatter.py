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
    def build_prompt(query: str, context: str) -> str:
        return f"""
You are an expert in constitutional law, specifically the Constitution of Nepal. Your task is to answer the following question based ONLY on the **provided constitutional articles**. Do not reference any external knowledge or sources. **Only cite articles present in the context.**

CONSTITUTION ARTICLES:
{context}

QUESTION: {query}

ANSWER:
- **Strictly** base your answer only on the provided articles. Do not reference any other source or external knowledge.
- **Cite only the articles listed above**. If the answer requires referencing multiple articles, cite them **precisely** as [Part X, Article Y] (e.g., [Part 5, Article 56(2)]).
- If the Constitution does not address the question or if there is no relevant article, **explicitly state** that the question is not addressed by the Constitution and do not attempt to make assumptions or guesses.
- **Do not provide any information** that is not in the provided articles or make any references to sources outside the provided context.
- **If an article is not present in the context**, **do not mention it**. Ensure your answer strictly adheres to the information in the provided articles.
"""
