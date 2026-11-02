import csv
from pathlib import Path

TARGETS = Path("targets.csv")


def main():
    if not TARGETS.exists():
        print("targets.csv not found.")
        return

    with TARGETS.open("r", newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    if not rows:
        print("No accounts to review.")
        return

    print("\nTikTok Account Review")
    print("=" * 45)

    for index, row in enumerate(rows, 1):
        username = row.get("username", "").strip()
        followers = row.get("followers", "").strip()
        age = row.get("age_status", "").strip() or "Unverified"
        message = row.get("message", "").strip()

        print(f"\nAccount {index}")
        print(f"Username: @{username}")
        print(f"Followers: {followers or 'Unknown'}")
        print(f"Age status: {age}")
        print(f"Message draft: {message or 'None'}")
        print("Review status: Pending")
        print("-" * 45)


if __name__ == "__main__":
    main()
