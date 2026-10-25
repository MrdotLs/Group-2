import argparse

from src.report import load_assumptions, run_pipeline, summary_frame, write_report

def main() -> None:
    p = argparse.ArgumentParser(description="Group 2 Energy and TEA(Work in progress)")
    p.add_argument("--assumptions", default="data/assumptions.yaml")
    p.add_argument("--scenarios", default="data/scenario_summary.csv")
    p.add_argument("--properties", default="data/feedstock.csv")
    p.add_argument("--out", default="outputs")
    p.add_argument("--no-charts", default="store_true")
    args = p.parse_args()

    a = load_assumptions(args.assumptions)
    results = run_pipeline(a, args.scenarios, args.properties)

    print(summary_frame(results).to_string(index=False))
    if results["placeholders"]:
        print("\nPlaceholder assumptions used:", ", ".join(results["placeholders"]))
 
    written = write_report(results, args.out, charts=not args.no_charts)
    print("\nWritten:")
    for name, path in written.items():
        print(f"  {name:<12} {path}")

if __name__ == "__main__":
    main()