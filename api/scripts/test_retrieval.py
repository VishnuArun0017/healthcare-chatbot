from datetime import datetime
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from rag.retriever import retrieve


def main() -> None:
    reports_dir = Path(__file__).resolve().parent / "logs"
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = reports_dir / f"retrieval_{timestamp}.txt"

    queries = [
        "I have fever and body ache",
        "My child has diarrhea",
        "Panic attack breathing techniques",
        "How to use ORS",
        "What to do for vaginal discharge",
        "I feel chest tightness with shortness of breath",
        "Child with high fever and rash",
        "Signs of stroke warning",
        "How to manage asthma attack at home",
        "Self care for migraine headache",
        "Burn first aid steps",
        "Postpartum warning signs",
        "Safe exercises for diabetes",
        "Hypertension lifestyle advice",
        "When to seek urgent care",
        "What to do for constipation",
        "Red flags for abdominal pain in pregnancy",
        "Basics of anxiety self care",
        "How to reduce alcohol safely",
        "Itchy fungal infection management",
    ]

    log_lines: list[str] = []

    for query in queries:
        print(f"\nQuery: {query}")
        log_lines.append(f"Query: {query}")

        results = retrieve(query, k=2)
        if not results:
            print("  No results")
            log_lines.append("  No results")
            continue

        for idx, res in enumerate(results, 1):
            meta = (
                f"source={res.get('source')}, "
                f"title={res.get('title')}, "
                f"category={res.get('category')}"
            )
            snippet = res["chunk"][:180].replace("\n", " ")
            print(f"  {idx}. {meta}")
            print(f"     {snippet}...")
            log_lines.append(f"  {idx}. {meta}")
            log_lines.append(f"     {snippet}...")

    report_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(f"\nSaved retrieval log to {report_path}")


if __name__ == "__main__":
    main()

