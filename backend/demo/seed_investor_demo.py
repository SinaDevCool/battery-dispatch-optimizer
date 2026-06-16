import argparse

from backend.services.investor_demo_seed import seed_investor_demo_json


def main():
    parser = argparse.ArgumentParser(
        description="Seed mock evidence for the investor demo workflow.",
    )
    parser.add_argument(
        "--asset-id",
        default=None,
        help="Optional asset id. Defaults to all mock investor-demo assets.",
    )
    parser.add_argument(
        "--optimizer-engine",
        default="rule_based_v1",
        help="Optimizer engine used for signal and workflow generation.",
    )
    args = parser.parse_args()

    print(
        seed_investor_demo_json(
            asset_id=args.asset_id,
            optimizer_engine=args.optimizer_engine,
        )
    )


if __name__ == "__main__":
    main()
