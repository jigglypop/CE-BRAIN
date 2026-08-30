from __future__ import annotations

from reality_stone.clarus.history_state_benchmark import evaluate_history_state

try:
    from examples.agi._bench_main import bench_main
except ImportError:  # direct script execution: examples/agi is sys.path[0]
    from _bench_main import bench_main


def main() -> int:
    return bench_main(evaluate_history_state)


if __name__ == "__main__":
    raise SystemExit(main())
