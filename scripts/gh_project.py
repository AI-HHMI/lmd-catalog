"""Fetch every item of an AI-HHMI GitHub Project (v2) with one hand-written GraphQL query, paged 100 items at a time.

`gh project item-list` asks for every field value's nested lists too, which GitHub bills at about 1 point per item
(measured: 101 points for 100 items). This query asks only for what the rebuild scripts store, and gets each issue's
creation date in the same request, for about 3 points per 100 items. Needs `gh` authenticated with `read:project`.
"""

from __future__ import annotations

import json
import subprocess
import sys

OWNER = "AI-HHMI"
QUERY = """
query($number: Int!, $after: String) {
  organization(login: "%s") { projectV2(number: $number) { items(first: 100, after: $after) {
    pageInfo { hasNextPage endCursor }
    nodes {
      content { __typename ... on Issue {
        number title url createdAt repository { nameWithOwner }
        assignees(first: 100) { totalCount nodes { login } }
        labels(first: 100) { totalCount nodes { name } }
      } }
      fieldValues(first: 100) { totalCount nodes {
        __typename
        ... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2FieldCommon { name } } }
        ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2FieldCommon { name } } }
        ... on ProjectV2ItemFieldNumberValue { number field { ... on ProjectV2FieldCommon { name } } }
        ... on ProjectV2ItemFieldDateValue { date field { ... on ProjectV2FieldCommon { name } } }
      } }
    }
  } } }
}
""" % OWNER
# Value types of the custom columns, and where each keeps its value.
VALUE_KEYS = {
    "ProjectV2ItemFieldTextValue": "text",
    "ProjectV2ItemFieldSingleSelectValue": "name",
    "ProjectV2ItemFieldNumberValue": "number",
    "ProjectV2ItemFieldDateValue": "date",
}
# GitHub's built-in columns (assignees, labels, ... come from the issue itself), not stored as columns.
BUILT_IN = {
    "ProjectV2ItemFieldUserValue", "ProjectV2ItemFieldLabelValue", "ProjectV2ItemFieldRepositoryValue",
    "ProjectV2ItemFieldMilestoneValue", "ProjectV2ItemFieldPullRequestValue", "ProjectV2ItemFieldReviewerValue",
    "ProjectV2ItemFieldIterationValue",
}


def inconsistent(item, msg):
    """Upstream data problem: report it (sync_github.py collects these) and carry on instead of failing the whole sync."""
    print(f"INCONSISTENT: {item['issue']['url']}: {msg}", file=sys.stderr)


def fetch_page(number: int, after: str | None) -> dict:
    cmd = ["gh", "api", "graphql", "-f", f"query={QUERY}", "-F", f"number={number}"]
    if after:
        cmd += ["-f", f"after={after}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"gh api graphql failed for project {number}: {result.stderr}"
    return json.loads(result.stdout)["data"]["organization"]["projectV2"]["items"]


def to_item(node: dict) -> dict:
    """{"issue", "title", "created_at", "assignees", "labels", "fields": {column name: value}} for one project item."""
    content = node["content"]
    assert content["__typename"] == "Issue", f"non-issue project item: {node}"
    for key in ("assignees", "labels"):
        assert content[key]["totalCount"] <= 100, f"{content['url']}: more than 100 {key}"
    assert node["fieldValues"]["totalCount"] <= 100, f"{content['url']}: more than 100 field values"
    fields = {}
    for value in node["fieldValues"]["nodes"]:
        kind = value["__typename"]
        assert kind in VALUE_KEYS or kind in BUILT_IN, f"{content['url']}: unhandled project field type {kind}"
        if kind in VALUE_KEYS:
            name, v = value["field"]["name"], value[VALUE_KEYS[kind]]
            assert name not in fields, f"{content['url']}: two project columns named {name!r}"
            fields[name] = int(v) if isinstance(v, float) and v.is_integer() else v
    return {
        "issue": {"number": content["number"], "url": content["url"], "repository": content["repository"]["nameWithOwner"]},
        "title": content["title"],
        "created_at": content["createdAt"][:10],
        "assignees": [a["login"] for a in content["assignees"]["nodes"]],
        "labels": [label["name"] for label in content["labels"]["nodes"]],
        "fields": fields,
    }


def fetch_items(number: int) -> list[dict]:
    items, after = [], None
    while True:
        page = fetch_page(number, after)
        items += [to_item(n) for n in page["nodes"]]
        if not page["pageInfo"]["hasNextPage"]:
            return items
        after = page["pageInfo"]["endCursor"]
