"""Local seed, evaluation, and replay entry points."""

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from finagent.evaluation import evaluate
from finagent.persistence.store import Store
from finagent.service import Service
from finagent.sources.personas import seed_files


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["seed", "evaluate", "replay"])
    parser.add_argument("--persona", default="P2", choices=["P1", "P2", "P3", "P4"])
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()
    if args.command == "evaluate":
        result = evaluate()
        print(json.dumps(result["metrics"], indent=2))
    else:
        import os

        service = Service(Store(os.getenv("FINAGENT_DB", "sqlite:///finagent.db")))
        if args.command == "seed":
            seed_files(Path("data/personas"))
            service.reset_persona(args.persona)
            print("Generated four deterministic personas and loaded " + args.persona)
        else:
            print(json.dumps(service.replay(args.days)))


if __name__ == "__main__":
    main()
