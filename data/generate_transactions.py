"""
PayMind — Day 1: Baseline synthetic transaction generator.

Generates realistic-looking payment transactions with NO degradation
injected yet — failure rate is roughly even across every route, method,
and time window. This is the clean baseline. The degradation gets
injected in a separate script tomorrow (Day 2), on top of this data.
"""

import random
import uuid
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker

fake = Faker("en_IN")  # Indian locale — names, phone formats etc. match context
random.seed(42)         # fixed seed so results are reproducible for you and for judges

NUM_TRANSACTIONS = 10000
BASE_FAILURE_RATE = 0.05  # 5% of all transactions fail, evenly, on this baseline

PAYMENT_METHODS = ["UPI", "credit_card", "debit_card", "netbanking", "wallet"]
UPI_APPS = ["gpay", "phonepe", "paytm", "bhim", None]  # None = not a UPI transaction
PAYMENT_ROUTES = ["route_a", "route_b", "route_c", "route_d"]
BANKS = ["HDFC", "ICICI", "SBI", "Axis", "Kotak", "Yes Bank"]
GEOGRAPHIES = ["Mumbai", "Delhi", "Bengaluru", "Chennai", "Hyderabad", "Pune", "Kolkata"]
DEVICE_TYPES = ["android", "ios", "web"]
FAILURE_CODES = ["insufficient_funds", "bank_timeout", "invalid_otp", "gateway_error", None]

START_TIME = datetime(2026, 8, 1, 0, 0, 0)


def make_transaction(i: int) -> dict:
    method = random.choice(PAYMENT_METHODS)
    is_upi = method == "UPI"
    failed = random.random() < BASE_FAILURE_RATE

    return {
        "transaction_id": str(uuid.uuid4()),
        "merchant_id": "merchant_paymind_demo",
        "customer_id": f"cust_{random.randint(1, 1200)}",
        "timestamp": (START_TIME + timedelta(minutes=random.randint(0, 60 * 24 * 20))).isoformat(),
        "amount": round(random.uniform(50, 25000), 2),
        "currency": "INR",
        "payment_method": method,
        "payment_route": random.choice(PAYMENT_ROUTES),
        "bank": random.choice(BANKS),
        "upi_app": random.choice(UPI_APPS) if is_upi else None,
        "geography": random.choice(GEOGRAPHIES),
        "device_type": random.choice(DEVICE_TYPES),
        "order_id": f"order_{i}",
        "status": "failed" if failed else "success",
        "failure_code": random.choice(FAILURE_CODES[:-1]) if failed else None,
        "latency_ms": random.randint(300, 2500) if not failed else random.randint(2000, 9000),
        "retry_count": 0,
    }


def main():
    rows = [make_transaction(i) for i in range(NUM_TRANSACTIONS)]
    df = pd.DataFrame(rows)
    df.to_csv("data/transactions.csv", index=False)

    print(f"Generated {len(df)} transactions -> data/transactions.csv")
    print("\nOverall status distribution:")
    print(df["status"].value_counts(normalize=True))
    print("\nFailure rate by route (should be roughly even — this is the baseline):")
    print(df.groupby("payment_route")["status"].apply(lambda s: (s == "failed").mean()))


if __name__ == "__main__":
    main()