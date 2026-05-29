"""Terminal chat interface for the RAG application.

Provides a simple REPL-style loop where the user can type questions
and receive answers grounded in the indexed document collection.
"""

from .rag import RAG


def run() -> None:
    """Start the interactive chat loop."""
    rag = RAG()

    print("=" * 60)
    print("Welcome to Chat-with-Docs!")
    print("Ask questions about your indexed documents.")
    print("Press Ctrl+C to exit.")
    print("=" * 60)

    try:
        while True:
            # Prompt the user for input.
            try:
                question = input("\nQuestion: ").strip()
            except EOFError:
                # Handle Ctrl+D / EOF gracefully.
                print()
                break

            # Skip empty submissions so we don't waste an LLM call.
            if not question:
                continue

            # Retrieve context and generate an answer.
            result = rag.answer(question, debug=True)

            # Display the LLM response.
            print(f"Answer: {result['answer']}")

            # Show which source files contributed to the answer.
            if result["sources"]:
                sources_str = ", ".join(result["sources"])
                print(f"Sources: {sources_str}")
            else:
                print("Sources: (none)")

    except KeyboardInterrupt:
        # Exit cleanly on Ctrl+C without dumping a traceback.
        print("\n\nGoodbye!")


if __name__ == "__main__":
    run()
