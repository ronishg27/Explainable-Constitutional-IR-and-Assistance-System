#!/usr/bin/env python3
"""Demo script for RAG Workflow."""

from src.llm.rag_workflow import RAGWorkflow

if __name__ == "__main__":
    print("Initializing RAG Workflow...")
    workflow = RAGWorkflow()
    
    print(f"Loaded {len(workflow.documents)} articles from constitution.\n")
    
    # Test retrieval
    query = "President election"
    print(f"Query: '{query}'")
    print("-" * 80)
    
    articles = workflow.retrieve(query)
    print(f"Retrieved {len(articles)} articles:\n")
    
    for i, art in enumerate(articles, 1):
        print(f"{i}. {art['citation']}")
        print(f"   Title: {art['title']}")
        print(f"   Score: {art['score']:.2f}\n")
    
    # Format context and show prompt
    context = workflow.format_context(articles)
    print("=" * 80)
    print("FORMATTED CONTEXT FOR LLM:")
    print("=" * 80)
    print(context[:500] + "...\n" if len(context) > 500 else context + "\n")
    
    print("=" * 80)
    print("RAG Workflow is ready!")
    print("To run LLM query, ensure Ollama is running:")
    print("  ollama serve")
    print("\nThen use: workflow.ask(query)")
    print("=" * 80)
