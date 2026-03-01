"""Entry point: python -m rust_twins_mut"""

import argparse

from .runner import continuous_fuzzing


def main():
    parser = argparse.ArgumentParser(
        description="LLM-based Rust code mutator using GPT-OSS-20B via Google Vertex AI"
    )
    parser.add_argument("folder", help="Folder containing Rust files (searches recursively)")
    parser.add_argument("--processes", type=int, default=4,
                        help="Number of parallel processes (default: 4)")
    parser.add_argument("--timeout", type=int, default=3600,
                        help="Global timeout in seconds — stops submitting new tasks (default: 3600)")
    parser.add_argument("--api-timeout", type=int, default=120,
                        help="Per-call API timeout in seconds (default: 120)")
    parser.add_argument("--grace-period", type=int, default=30,
                        help="Seconds to wait for running tasks after timeout (default: 30)")
    parser.add_argument("--output", default="./fuzz_output",
                        help="Output directory for mutated files (default: ./fuzz_output)")

    args = parser.parse_args()

    continuous_fuzzing(
        folder_path=args.folder,
        num_processes=args.processes,
        global_timeout=args.timeout,
        output_dir=args.output,
        api_timeout=args.api_timeout,
        grace_period=args.grace_period,
    )


if __name__ == "__main__":
    main()
