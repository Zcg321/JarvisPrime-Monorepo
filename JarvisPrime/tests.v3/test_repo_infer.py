from bridge.repo_infer import infer_repo_branch


def test_repo_infer():
    policies = {
        "docs": {"repo": "YOURORG/docs", "branch": "main", "weight": 5, "tokens": ["docs", "readme"]},
        "bridge": {"repo": "YOURORG/foreman", "branch": "main", "weight": 9, "tokens": ["bridge"]},
    }
    default = {"repo": "YOURORG/your-repo", "branch": "main"}
    repo, branch, reason = infer_repo_branch("update docs and readme", policies, default)
    assert repo == "YOURORG/docs"
    assert "matched" in reason
    repo2, _, reason2 = infer_repo_branch("misc task", policies, default)
    assert repo2 == default["repo"]
    assert reason2 == "default"
