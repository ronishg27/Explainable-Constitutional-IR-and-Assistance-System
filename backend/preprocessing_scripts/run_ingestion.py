"""Run the full offline ingestion pipeline in one command."""

from preprocessing_scripts.build_index import main as build_inverted_index
from preprocessing_scripts.flatten_constitution import main as flatten_constitution
from preprocessing_scripts.generate_safe_lemma_dict import main as generate_safe_lemma_dict


def main() -> None:
    print("[1/3] Flattening constitution data...")
    flatten_constitution()

    print("[2/3] Building inverted index...")
    build_inverted_index()

    print("[3/3] Generating lemma dictionary...")
    generate_safe_lemma_dict()

    print("Ingestion pipeline completed successfully.")


if __name__ == "__main__":
    main()
