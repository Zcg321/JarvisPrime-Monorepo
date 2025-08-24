import os
import time
import json
import requests
from typing import Optional


def _app_install_token() -> Optional[str]:
    app_id = os.getenv("GH_APP_ID")
    inst_id = os.getenv("GH_APP_INSTALLATION_ID")
    pem = os.getenv("GH_APP_PRIVATE_KEY_PEM")
    if not (app_id and inst_id and pem):
        return None
    try:
        import jwt  # type: ignore
    except Exception:
        return None
    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + 600, "iss": app_id}
    token = jwt.encode(payload, pem, algorithm="RS256")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com/app/installations/{inst_id}/access_tokens"
    res = requests.post(url, headers=headers, timeout=30)
    if res.status_code == 201:
        return res.json().get("token")
    return None


def _pat_token(repo: str) -> Optional[str]:
    owner, name = repo.split("/", 1)
    env = f"GITHUB_TOKEN_{owner}__{name}".upper().replace("-", "_")
    return os.getenv(env) or os.getenv("GT_TOKEN")


def ensure_pull_request(repo: str, head_branch: str, base_branch: str, title: str, body: str) -> str:
    token = _app_install_token() or _pat_token(repo)
    if not token:
        raise RuntimeError("no GitHub token available")
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    api = f"https://api.github.com/repos/{repo}/pulls"
    data = {"title": title, "head": head_branch, "base": base_branch, "body": body}
    res = requests.post(api, headers=headers, json=data, timeout=30)
    if res.status_code == 201:
        return res.json().get("html_url", "")
    if res.status_code == 422:
        # maybe already exists; search
        owner = repo.split("/")[0]
        search = requests.get(api, headers=headers, params={"head": f"{owner}:{head_branch}", "state": "open"}, timeout=30)
        if search.ok and search.json():
            return search.json()[0].get("html_url", "")
    res.raise_for_status()
    return res.json().get("html_url", "")


def set_commit_status(repo: str, sha: str, state: str, context: str, description: str, target_url: str | None = None) -> None:
    token = _app_install_token() or _pat_token(repo)
    if not token:
        return
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    api = f"https://api.github.com/repos/{repo}/statuses/{sha}"
    data = {"state": state, "context": context, "description": description}
    if target_url:
        data["target_url"] = target_url
    requests.post(api, headers=headers, json=data, timeout=30)


def ensure_labels(repo: str, issue_number: str, labels: list[str]) -> None:
    token = _app_install_token() or _pat_token(repo)
    if not token:
        return
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    api = f"https://api.github.com/repos/{repo}/issues/{issue_number}/labels"
    requests.post(api, headers=headers, json={"labels": labels}, timeout=30)


def enable_automerge(repo: str, pr_number: str, method: str = "squash") -> None:
    token = _app_install_token() or _pat_token(repo)
    if not token:
        return
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    pr = requests.get(f"https://api.github.com/repos/{repo}/pulls/{pr_number}", headers=headers, timeout=30)
    if not pr.ok:
        return
    node_id = pr.json().get("node_id")
    if not node_id:
        return
    gql = {"query": "mutation($id:ID!){enablePullRequestAutoMerge(input:{pullRequestId:$id, mergeMethod:SQUASH}){clientMutationId}}", "variables": {"id": node_id}}
    requests.post("https://api.github.com/graphql", headers=headers, json=gql, timeout=30)
