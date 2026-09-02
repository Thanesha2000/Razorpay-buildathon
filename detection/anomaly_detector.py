"""
PayMind — Day 3: Deterministic anomaly detector.

Reads transactions.csv WITHOUT looking at ground_truth.json, and finds
the degraded segment on its own by comparing failure rates across
groups against the overall baseline. Outputs anomaly.json.
"""

import json

import pandas as pd

MIN_TRANSACTIONS = 30       # ignore groups too small to trust
DEVIATION_MULTIPLIER = 3.0  # flag if a group's failure rate is >= 3x baseline


def main():
    df = pd.read_csv("data/transactions.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date

    overall_failure_rate = (df["status"] == "failed").mean()
    print(f"Overall baseline failure rate: {overall_failure_rate:.4f}")

    # --- Step A: group by (route, method), find the segment that stands out ---
    grouped = df.groupby(["payment_route", "payment_method"]).agg(
        count=("status", "size"),
        failed=("status", lambda s: (s == "failed").sum()),
    )
    grouped["failure_rate"] = grouped["failed"] / grouped["count"]

    flagged = grouped[
        (grouped["count"] >= MIN_TRANSACTIONS)
        & (grouped["failure_rate"] >= overall_failure_rate * DEVIATION_MULTIPLIER)
    ].sort_values("failure_rate", ascending=False)

    print("\nFlagged (route, method) segments:")
    print(flagged)

    if flagged.empty:
        print("\nNo anomaly found above threshold.")
        return

    top_route, top_method = flagged.index[0]
    top_row = flagged.iloc[0]

    # --- Step B: drill into daily breakdown for that segment, find the actual window ---
    segment_df = df[(df["payment_route"] == top_route) & (df["payment_method"] == top_method)]
    daily = segment_df.groupby("date").agg(
        count=("status", "size"),
        failed=("status", lambda s: (s == "failed").sum()),
    )
    daily["failure_rate"] = daily["failed"] / daily["count"]

    bad_days = daily[daily["failure_rate"] >= overall_failure_rate * DEVIATION_MULTIPLIER]
    print(f"\nDaily breakdown for {top_route}/{top_method}:")
    print(daily)

    # --- Step C: estimate revenue at risk from the actually-failed rows in the bad window ---
    incident_rows = segment_df[
        segment_df["date"].isin(bad_days.index) & (segment_df["status"] == "failed")
    ]
    revenue_at_risk = float(incident_rows["amount"].sum())

    anomaly = {
        "segment": {"payment_route": top_route, "payment_method": top_method},
        "window_start": str(bad_days.index.min()) if not bad_days.empty else None,
        "window_end": str(bad_days.index.max()) if not bad_days.empty else None,
        "segment_failure_rate": round(float(top_row["failure_rate"]), 4),
        "baseline_failure_rate": round(float(overall_failure_rate), 4),
        "deviation_multiplier": round(float(top_row["failure_rate"] / overall_failure_rate), 2),
        "affected_transaction_count": int(top_row["count"]),
        "failed_transaction_count": int(top_row["failed"]),
        "revenue_at_risk": round(revenue_at_risk, 2),
        "confidence": "high" if top_row["failure_rate"] / overall_failure_rate >= 5 else "medium",
    }

    with open("detection/anomaly.json", "w") as f:
        json.dump(anomaly, f, indent=2)

    print("\nAnomaly written to detection/anomaly.json:")
    print(json.dumps(anomaly, indent=2))


if __name__ == "__main__":
    main()