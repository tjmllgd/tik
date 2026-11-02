
import csv
from pathlib import Path

TARGETS = Path("targets.csv")

def save_accounts(accounts, fields):
    with TARGETS.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(accounts)


def main():
    if not TARGETS.exists():
        print("targets.csv not found.")
        return

    with TARGETS.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        fields = reader.fieldnames or []
        accounts = list(reader)

    if not accounts:
        print("No accounts to review.")
        return

    if "review_status" not in fields:
        fields.append("review_status")

    print("\nAccount Review")
    print("=" * 45)

    for index, row in enumerate(accounts, 1):
        username = row.get("username", "").strip()
        followers = row.get("followers", "").strip()
        age = row.get("age_status", "").strip() or "Unverified"
        message = row.get("message", "").strip()

        status = row.get("review_status", "").strip() or "Pending"

        print(f"\nAccount {index}")
        print(f"Username: @{username}")
        print(f"Followers: {followers or 'Unknown'}")
        print(f"Age status: {age}")
        print(f"Message draft: {message or 'None'}")
        print(f"Review status: {status}")

        print("\nChoose status:")
        print("1. Reviewed")
        print("2. Pending")
        print("3. Skipped")
        print("4. Keep current status")

        choice = input("Choice: ").strip()

        if choice == "1":
            row["review_status"] = "Reviewed"
        elif choice == "2":
            row["review_status"] = "Pending"
        elif choice == "3":
            row["review_status"] = "Skipped"
        elif choice != "4" and choice != "":
            print("Invalid choice. Keeping current status.")
            row["review_status"] = status

        save_accounts(accounts, fields)
        print(f"Saved: {row.get('review_status', 'Pending')}")

    print("\nReview complete!")


if __name__ == "__main__":
    main()
