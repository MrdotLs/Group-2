import argparse

from src.report import load_assumptions, run_pipeline, summary_frame, write_report

def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Group 2 Energy and TEA(Work in progress)")
    p.add_argument("--assumptions", default="data/assumptions.yaml")
    p.add_argument("--scenarios", default="data/scenario_summary_v2.csv")
    p.add_argument("--feedstock", default="data/feedstock.csv")
    p.add_argument("--scenario", help="headline scenario, overrides pretreatment.scenario_id(e.g S16)")
    p.add_argument("--all", nargs="?", const="all", metavar="IDS", help="also run every scenario, or a selection such as S1-S24 pr S1,S3,S16")
    p.add_argument("--out", default="outputs")
    p.add_argument("--no-charts", action="store_true")
    args = p.parse_args(argv)

    a = load_assumptions(args.assumptions)
    if args.all:
        a["scenarios"] = {**(a.get("scenarios") or {}), "run": args.all}
    results = run_pipeline(a, args.scenarios, args.feedstock, args.scenario)
    for name, path in write_report(results, args.out, charts=not args.no_charts).items():
        print(f"{name:<16}{path}")


if __name__ == "__main__":
    main()