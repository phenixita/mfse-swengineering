#!/usr/bin/env python3
"""
Count completed (merged) pull requests in an Azure DevOps project.

Usage:
    python azdo_closed_prs.py --org https://dev.azure.com/myorg --project MyProject --pat <TOKEN>
    python azdo_closed_prs.py --org https://dev.azure.com/myorg --project MyProject --pat <TOKEN> \
        --from-date 2024-01-01 --to-date 2024-12-31
"""

import argparse
import base64
import sys
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print("Missing dependency: install it with 'pip install requests'", file=sys.stderr)
    sys.exit(1)


def make_headers(pat: str) -> dict:
    token = base64.b64encode(f":{pat}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }


def get_json(url: str, headers: dict, params: dict = None) -> dict:
    response = requests.get(url, headers=headers, params=params)
    if not response.ok:
        print(f"HTTP {response.status_code} — {response.text}", file=sys.stderr)
        sys.exit(1)
    return response.json()


def list_repositories(base_url: str, headers: dict) -> list:
    url = f"{base_url}/_apis/git/repositories"
    data = get_json(url, headers, params={"api-version": "7.1"})
    return data.get("value", [])


def count_completed_prs(
    base_url: str,
    headers: str,
    repo_id: str,
    from_dt: datetime | None,
    to_dt: datetime | None,
) -> int:
    url = f"{base_url}/_apis/git/repositories/{repo_id}/pullrequests"
    count = 0
    skip = 0
    top = 100

    while True:
        params = {
            "searchCriteria.status": "completed",
            "$top": top,
            "$skip": skip,
            "api-version": "7.1",
        }
        data = get_json(url, headers, params=params)
        prs = data.get("value", [])

        for pr in prs:
            closed_date_str = pr.get("closedDate")
            if closed_date_str and (from_dt or to_dt):
                # Azure DevOps returns ISO 8601 with 7 fractional digits — normalize to 6
                closed_date_str = closed_date_str[:26] + "Z" if len(closed_date_str) > 27 else closed_date_str
                try:
                    closed_dt = datetime.fromisoformat(closed_date_str.replace("Z", "+00:00"))
                except ValueError:
                    closed_dt = None

                if closed_dt:
                    if from_dt and closed_dt < from_dt:
                        continue
                    if to_dt and closed_dt > to_dt:
                        continue

            count += 1

        if len(prs) < top:
            break
        skip += top

    return count


def parse_date(value: str, end_of_day: bool = False) -> datetime:
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        print(f"Invalid date format '{value}'. Use YYYY-MM-DD.", file=sys.stderr)
        sys.exit(1)
    if end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59)
    return dt.replace(tzinfo=timezone.utc)


def main():
    parser = argparse.ArgumentParser(
        description="Count completed (merged) pull requests in an Azure DevOps project."
    )
    parser.add_argument("--org", required=True, help="Organization URL (e.g. https://dev.azure.com/myorg)")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--pat", required=True, help="Personal Access Token")
    parser.add_argument("--from-date", metavar="YYYY-MM-DD", help="Filter PRs closed on or after this date")
    parser.add_argument("--to-date", metavar="YYYY-MM-DD", help="Filter PRs closed on or before this date")
    args = parser.parse_args()

    org = args.org.rstrip("/")
    base_url = f"{org}/{args.project}"
    headers = make_headers(args.pat)

    from_dt = parse_date(args.from_date) if args.from_date else None
    to_dt = parse_date(args.to_date, end_of_day=True) if args.to_date else None

    print(f"Fetching repositories for project '{args.project}'...", file=sys.stderr)
    repos = list_repositories(base_url, headers)

    if not repos:
        print("No repositories found.", file=sys.stderr)
        print("Total completed PRs: 0")
        return

    total = 0
    for repo in repos:
        repo_name = repo["name"]
        repo_id = repo["id"]
        print(f"  Scanning '{repo_name}'...", file=sys.stderr)
        count = count_completed_prs(base_url, headers, repo_id, from_dt, to_dt)
        total += count

    print(f"Total completed PRs: {total}")


if __name__ == "__main__":
    main()
