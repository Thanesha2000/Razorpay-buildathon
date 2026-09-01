"""
PayMind — Day 2: Inject a causal degradation into the baseline dataset.

Takes the clean baseline from Day 1 and deliberately breaks one narrow
segment: a specific route + payment method, during a specific time
window. Everything outside that segment stays exactly as it was. Writes:
  - data/transactions.csv        (overwritten — now contains the degradation)
  - data/ground_truth.json       (the exact answer key for what we broke)
"""

import json
import random

import pandas as pd

random.seed(42)

# --- The exact segment we're going to break. Change these to retune the scenario. ---
# Deliberately only 2 filters (route + method), not 4 — stacking route + method +
# amount band + time window on a 5-10k row dataset leaves almost no matching rows.
DEGRADED_ROUTE = "route_b"
DEGRADED_METHOD = "UPI"
WINDOW_START = pd.Timestamp("2026-08-10T00:00:00")
WINDOW_END = pd.Timestamp("2026-08-15T00:00:00")
DEGRADED_FAILURE_RATE = 0.45  # vs. ~0.05 baseline elsewhere
DEGRADED_FAILURE_CODE = "bank_timeout"  # the specific reason, consistent across the incident


def main():
    df = pd.read_csv("data/transactions.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    mask = (
        (df["payment_route"] == DEGRADED_ROUTE)
        & (df["payment_method"] == DEGRADED_METHOD)
        & (df["timestamp"] >= WINDOW_START)
        & (df["timestamp"] < WINDOW_END)
    )
    affected_count = mask.sum()
    print(f"Rows matching the target segment: {affected_count}")

    def degrade_row(row):
        if random.random() < DEGRADED_FAILURE_RATE:
            row["status"] = "failed"
            row["failure_code"] = DEGRADED_FAILURE_CODE
            row["latency_ms"] = random.randint(4000, 9500)
            row["retry_count"] = random.randint(1, 3)
        else:
            row["status"] = "success"
            row["failure_code"] = None
        return row

    df.loc[mask] = df.loc[mask].apply(degrade_row, axis=1)

    segment_failure_rate = (df.loc[mask, "status"] == "failed").mean()
    rest_failure_rate = (df.loc[~mask, "status"] == "failed").mean()
    print(f"Failure rate INSIDE degraded segment: {segment_failure_rate:.3f}")
    print(f"Failure rate OUTSIDE degraded segment: {rest_failure_rate:.3f}")

    df.to_csv("data/transactions.csv", index=False)

    ground_truth = {
        "degraded_route": DEGRADED_ROUTE,
        "degraded_method": DEGRADED_METHOD,
        "window_start": str(WINDOW_START),
        "window_end": str(WINDOW_END),
        "target_failure_rate": DEGRADED_FAILURE_RATE,
        "failure_code": DEGRADED_FAILURE_CODE,
        "affected_row_count": int(affected_count),
        "observed_segment_failure_rate": round(float(segment_failure_rate), 4),
        "observed_rest_failure_rate": round(float(rest_failure_rate), 4),
    }
    with open("data/ground_truth.json", "w") as f:
        json.dump(ground_truth, f, indent=2)

    print("\nGround truth written to data/ground_truth.json")


if __name__ == "__main__":
    main()