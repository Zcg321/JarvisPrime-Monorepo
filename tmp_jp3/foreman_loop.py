#!/usr/bin/env python3
"""
 Continuum Foreman (Hands-Free)
 - Full autonomous loop that sends tasks to Codex (OpenAI API), commits/pushes, and advances.
 - No UI automation. Uses API only.

 ENV required:
   OPENAI_API_KEY        -> your API key
   GT_TOKEN              -> GitHub PAT (never printed)
   GIT_OWNER             -> repo owner/org
   GIT_REPO              -> repo name (if single-repo mode) OR define per task in queue
 Optional:
   OPENAI_BASE_URL       -> custom endpoint if needed
   CODEX_MODEL           -> e.g., "gpt-5-codex" (placeholder; set to your Codex-capable model)

 Files:
   foreman/state.json    -> repos, queues, anchors, policy
   foreman/baton.json    -> latest STATUS per repo
   artifacts/            -> outputs and patches
   logs/foreman.log      -> run logs

 Run:
   python foreman_loop.py        # one loop pass (process all ready tasks)
   python foreman_loop.py --watch  # long-running: sleeps & rechecks every N seconds
"""

import os
import sys
import time
import json
import subprocess
import shlex
import argparse
from pathlib import Path
from datetime import datetime, timezone
import yaml

# ------- Paths -------
ROOT = Path.cwd()
FOREMAN = ROOT / "foreman"
FOREMAN.mkdir(exist_ok=True)
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)
PATCHES = ARTIFACTS / "patches"
PATCHES.mkdir(parents=True, exist_ok=True)
LOGS = ROOT / "logs"
LOGS.mkdir(exist_ok=True)

STATE_FILE = FOREMAN / "state.json"
BATON_FILE = FOREMAN / "baton.json"
FOREMAN_LOG = LOGS / "foreman.log"

# ------- Defaults -------
DEFAULT_STATE = {
  "anchors": [
    "JarvisPrime_BootProtocol.md",
    "continuum_master_final.json",
    "continuum_ascension_path.json",
    "continuum_true_endgame.json"
  ],
  "policy": {"max_files_touched": 15, "task_time_hint": "≤90m"},
  "repos": {}
}

EXAMPLE_STATE = {
  "anchors": DEFAULT_STATE["anchors"],
  "policy": DEFAULT_STATE["policy"],
  "repos": {
    "YOURORG/your-repo": {
      "branch": "main",
      "queue": [
        {"title": "Stabilize baseline", "scope": "Make lint/type/test green; wire push; no features."},
        {"title": "Ship Alchohalt MVP", "scope": "Daily 21:00 notification + check-in halted/slipped(+note) + streaks 7/30d + export/import JSON; minimal UI."},
        {"title": "Observability & docs", "scope": "Add /health, logs/alerts.jsonl, artifacts/reports/dashboard.(json|html); expand STATUS.md verification; no business logic changes."}
      ],
      "done": []
    }
  }
}

# ------- Helpers -------

VERBOSE = False

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def log(msg):
    line = f"{now()} | {msg}"
    if VERBOSE:
        print(line)
    with FOREMAN_LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_json(p, default):
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return default

def save_json(p, data):
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False))

def run(cmd, cwd=None, check=False):
    log(f"$ {cmd}")
    res = subprocess.run(shlex.split(cmd), cwd=cwd, capture_output=True, text=True)
    if res.stdout:
        log(res.stdout.strip())
    if res.stderr:
        log(res.stderr.strip())
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")
    return res

def ensure_git_remote(repo_full, branch):
    owner, name = repo_full.split("/", 1)
    # init if needed
    if not (ROOT / ".git").exists():
        run("git init", check=True)
        run('git config user.name "Jarvis Prime"', check=True)
        run('git config user.email "bot@local"', check=True)
    # set default branch
    run(f"git checkout -B {branch}")
    # add remote (idempotent)
    token = os.getenv("GT_TOKEN", "")
    if not token:
        log("WARN: GT_TOKEN not set; push will likely fail.")
    origin = f"https://x-access-token:{token}@github.com/{owner}/{name}.git"
    remotes = run("git remote -v").stdout or ""
    if "origin" not in remotes:
        run(f"git remote add origin {origin}")
    else:
        run(f"git remote set-url origin {origin}")

def codex_call(prompt_text, retries=3, backoff=5):
    """Send prompt to Codex-capable model via OpenAI API with simple retries."""
    import requests

    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("CODEX_MODEL", "gpt-5-codex")  # set to your Codex model
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set.")

    url = f"{base}/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are Jarvis Prime (Codex) execution engine. Produce code, tests, docs, git steps exactly as instructed. Keep diffs small. Never print secrets.",
            },
            {"role": "user", "content": prompt_text},
        ],
        "temperature": 0.2,
    }

    for attempt in range(1, retries + 1):
        try:
            r = requests.post(url, headers=headers, json=data, timeout=300)
            r.raise_for_status()
            j = r.json()
            return j["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt == retries:
                raise
            log(f"codex_call failed ({e}); retrying in {backoff * attempt}s")
            time.sleep(backoff * attempt)

def make_task_prompt(repo_full, branch, anchors, baton_excerpt, task, max_files):
    acceptance = [
        "lint/type/test green",
        "STATUS.md updated (What/Why/Testing + commands/outputs)",
        "artifacts/reports/dashboard.(json|html) updated if present",
        "push success OR artifacts/patches/*.patch + apply steps",
    ]
    acc = "\n".join([f"- {x}" for x in acceptance])
    return f"""# === REPO === {repo_full} (branch: {branch}). Env present: GT_TOKEN, GIT_OWNER, GIT_REPO (never print).

# === CONTEXT (BATON EXCERPT) === {baton_excerpt or "—"}

# === SCOPE === {task["title"]} — {task["scope"]}

# === RULES ===
- Keep diffs small (≤{max_files} files). Preserve prior work. Add/update tests and README snippets.
- If push fails (auth/policy), emit artifacts/patches/*.patch and write exact apply steps into STATUS.md.
- Do not print secrets.

# === ACCEPTANCE ===
{acc}

# === CONTINUUM ANCHORS (reference if present) === {", ".join(anchors)}

# === START === Proceed now. Commit logically; push at end (or emit patch).
"""

def extract_status_excerpt(codex_text):
    """
    Heuristic: find a STATUS-like summary in Codex output.
    We look for a fenced block or lines starting with 'STATUS'/'What/Why/Testing'.
    If none, return first ~30 lines as excerpt.
    """
    lines = codex_text.splitlines()
    buf, take = [], False
    for ln in lines:
        if "STATUS" in ln.upper() or "What:" in ln or "WHY:" in ln.upper():
            take = True
        if take:
            buf.append(ln)
            if len(buf) > 60:
                break
    if not buf:
        buf = lines[:30]
    excerpt = "\n".join(buf).strip()
    return excerpt[:3000]

def try_push(branch):
    # stage & commit everything if changes exist
    run("git add -A")
    diff = run("git diff --cached").stdout
    if not diff:
        log("No staged changes to commit.")
        return True, ""
    msg = f'feat(auto): foreman loop commit {now()}'
    try:
        run(f'git commit -m "{msg}"', check=True)
    except Exception as e:
        log(f"Commit failed: {e}")
        return False, ""
    pr = run(f"git push -u origin {branch}")
    if pr.returncode == 0:
        return True, ""
    # fallback: emit patch
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    patch = PATCHES / f"foreman_{ts}.patch"
    run(f'git format-patch -1 -o "{PATCHES.as_posix()}"')
    if patch.exists():
        return False, patch.name
    else:
        patches = sorted(PATCHES.glob("*.patch"), key=lambda p: p.stat().st_mtime, reverse=True)
        return False, patches[0].name if patches else ""

def one_pass(dry_run=False):
    state = load_json(STATE_FILE, DEFAULT_STATE)
    baton = load_json(BATON_FILE, {})
    anchors = state["anchors"]
    max_files = state["policy"]["max_files_touched"]

    progressed = False

    for repo_full, meta in list(state["repos"].items()):
        queue = meta.get("queue", [])
        branch = meta.get("branch", "main")
        if not queue:
            continue

        log(f"== Processing repo {repo_full} (branch {branch}) ==")
        ensure_git_remote(repo_full, branch)

        task = queue[0]
        baton_excerpt = baton.get(repo_full, {}).get("excerpt", "")

        prompt = make_task_prompt(repo_full, branch, anchors, baton_excerpt, task, max_files)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        if dry_run:
            prompt_file = ARTIFACTS / f"prompt_{repo_full.replace('/', '_')}_{ts}.txt"
            prompt_file.write_text(prompt)
            log(f"Saved prompt → {prompt_file}")
            progressed = True
            continue

        # Call Codex
        try:
            codex_out = codex_call(prompt)
        except Exception as e:
            log(f"ERROR: Codex call failed: {e}")
            continue

        # Save codex output
        out_file = ARTIFACTS / f"codex_{repo_full.replace('/', '_')}_{ts}.md"
        out_file.write_text(codex_out)
        log(f"Saved Codex output → {out_file}")

        # Try push; else emit patch
        ok, patch_name = try_push(branch)
        if ok:
            last_commit = (run("git rev-parse HEAD").stdout or "").strip()
            status_note = f"Pushed on branch {branch}, commit {last_commit}"
        elif patch_name:
            status_note = f"Push blocked — emitted patch: artifacts/patches/{patch_name}"
        else:
            status_note = "Push blocked — commit failed"

        # Update baton
        excerpt = extract_status_excerpt(codex_out)
        baton[repo_full] = {
            "excerpt": f"{excerpt}\n\n{status_note}",
            "last_commit": (run("git rev-parse HEAD").stdout or "").strip(),
            "updated": now(),
        }
        save_json(BATON_FILE, baton)

        # Advance queue
        meta["queue"].pop(0)
        if "done" not in meta:
            meta["done"] = []
        task["completed"] = now()
        task["result"] = "pushed" if ok else "patched"
        meta["done"].append(task)
        save_json(STATE_FILE, state)

        log(f"Advanced task: [{task['title']}] → {task['result']}")
        progressed = True

    return progressed


def parse_args():
    parser = argparse.ArgumentParser(description="Continuum foreman loop")
    parser.add_argument("--init", action="store_true", help="create required folders and empty state/baton")
    parser.add_argument("--seed-example", action="store_true", help="write example queue to state.json")
    parser.add_argument("--run", action="store_true", help="process one pass of tasks")
    parser.add_argument("--watch", action="store_true", help="keep running and rechecking queues")
    parser.add_argument("--interval", type=int, default=int(os.getenv("FOREMAN_INTERVAL", "90")), help="seconds between passes in watch mode")
    parser.add_argument("--status", action="store_true", help="print baton.json")
    parser.add_argument("--print-next", action="store_true", help="show next queued task per repo")
    parser.add_argument("--add-repo", help="add repo slug (owner/name) to state.json")
    parser.add_argument("--branch", default="main", help="branch for --add-repo")
    parser.add_argument("--enqueue", nargs=2, metavar=("TITLE", "SCOPE"), help="enqueue task (requires --add-repo)")
    parser.add_argument("--set-anchors", nargs="+", help="override anchors list in state.json")
    parser.add_argument("--set-policy", help="YAML to merge into policy")
    parser.add_argument("--dry-run", action="store_true", help="generate prompts without API or push")
    parser.add_argument("--verbose", action="store_true", help="print logs to stdout")
    args = parser.parse_args()
    return args, parser


def check_env(dry_run=False):
    required = ["OPENAI_API_KEY", "GT_TOKEN"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        log(f"WARN: missing env vars: {', '.join(missing)}")
        if not dry_run:
            sys.exit(1)


def init_files():
    FOREMAN.mkdir(exist_ok=True)
    ARTIFACTS.mkdir(exist_ok=True)
    LOGS.mkdir(exist_ok=True)
    if not STATE_FILE.exists():
        save_json(STATE_FILE, DEFAULT_STATE)
    if not BATON_FILE.exists():
        save_json(BATON_FILE, {})
    log("Initialized foreman folders")


def seed_example():
    save_json(STATE_FILE, EXAMPLE_STATE)
    log("Seeded example state")


def print_status():
    print(json.dumps(load_json(BATON_FILE, {}), indent=2, ensure_ascii=False))


def print_next():
    state = load_json(STATE_FILE, DEFAULT_STATE)
    for repo, meta in state.get("repos", {}).items():
        if meta.get("queue"):
            t = meta["queue"][0]
            print(f"{repo}: {t['title']} — {t['scope']}")
        else:
            print(f"{repo}: queue empty")


def add_repo(args):
    state = load_json(STATE_FILE, DEFAULT_STATE)
    if args.add_repo not in state["repos"]:
        state["repos"][args.add_repo] = {"branch": args.branch, "queue": [], "done": []}
    save_json(STATE_FILE, state)
    log(f"Added repo {args.add_repo}")


def enqueue_task(args):
    state = load_json(STATE_FILE, DEFAULT_STATE)
    repo = args.add_repo
    if repo not in state["repos"]:
        log(f"Repo {repo} missing; use --add-repo")
        return
    title, scope = args.enqueue
    state["repos"][repo].setdefault("queue", []).append({"title": title, "scope": scope})
    save_json(STATE_FILE, state)
    log(f"Enqueued task for {repo}")


def set_anchors(args):
    state = load_json(STATE_FILE, DEFAULT_STATE)
    state["anchors"] = args.set_anchors
    save_json(STATE_FILE, state)
    log("Updated anchors")


def set_policy(args):
    state = load_json(STATE_FILE, DEFAULT_STATE)
    policy = yaml.safe_load(args.set_policy)
    state["policy"].update(policy)
    save_json(STATE_FILE, state)
    log("Updated policy")


def main():
    args, parser = parse_args()
    global VERBOSE
    VERBOSE = args.verbose

    if not any([args.init, args.seed_example, args.run, args.watch, args.status, args.print_next, args.add_repo, args.enqueue, args.set_anchors, args.set_policy]):
        parser.print_help()
        return

    if args.init:
        init_files()
        return
    if args.seed_example:
        seed_example()
        return
    if args.status:
        print_status()
        return
    if args.print_next:
        print_next()
        return
    if args.add_repo and not args.run and not args.watch:
        add_repo(args)
        if args.enqueue:
            enqueue_task(args)
        return
    if args.enqueue and not args.add_repo and not args.run and not args.watch:
        enqueue_task(args)
        return
    if args.set_anchors:
        set_anchors(args)
        return
    if args.set_policy:
        set_policy(args)
        return

    check_env(args.dry_run)
    init_files()

    if args.run:
        one_pass(dry_run=args.dry_run)
        return

    if args.watch:
        log("Watching mode ON")
        try:
            while True:
                one_pass(dry_run=args.dry_run)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            log("Stopping watch loop")

if __name__ == "__main__":
    main()
