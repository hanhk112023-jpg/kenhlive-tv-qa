#!/usr/bin/env python3
"""KenhLive Realtime Vision QA — CLI.

  python3 run_realtime.py --out qa_out [--quick] [--serial X]
                          [--missions MISSION_A,MISSION_B]
                          [--vision-budget N] [--no-vision]

--quick: 5 mission trọng tâm (như harness cũ). --no-vision: chạy thuần cục
bộ (không gọi vision — mission cần vision sẽ UNVERIFIED, không PASS giả).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from runner import RealtimeRunner
from missions import get_missions


def main():
    ap = argparse.ArgumentParser(description="KenhLive Realtime Vision QA")
    ap.add_argument("--out", default="/tmp/qa_report_realtime")
    ap.add_argument("--serial", default=None)
    ap.add_argument("--quick", action="store_true", help="5 mission trọng tâm")
    ap.add_argument("--missions", default="",
                    help="chạy riêng các mission, cách nhau bằng dấu phẩy")
    ap.add_argument("--vision-budget", type=int, default=40)
    ap.add_argument("--no-vision", action="store_true")
    args = ap.parse_args()

    only = [m.strip() for m in args.missions.split(",") if m.strip()] or None
    missions = get_missions(quick=args.quick, only=only)
    print("📋 Realtime QA: %d mission, vision budget %d%s" % (
        len(missions), args.vision_budget, " (no-vision)" if args.no_vision else ""), flush=True)
    runner = RealtimeRunner(out_dir=args.out, serial=args.serial,
                            vision_budget=args.vision_budget, no_vision=args.no_vision)
    report = runner.run(missions)
    print("Score: %d/100 · %s · %d findings · %d unverified" % (
        report["score"], report["missions_passed"],
        len(report["findings"]), len(report["unverified"])), flush=True)
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
