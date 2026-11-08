"""
Optional: push each night's report to a PRIVATE GitHub repo so the cloud desk
(morning brief, Risk Officer) can read it while your laptop is closed.

Off unless both env vars are set:
  GITHUB_REPO   e.g. "yourname/test-trader-results" (create it empty + private)
  GITHUB_TOKEN  fine-grained token, access to ONLY that repo, "Contents: read & write"
"""
import glob
import logging
import os
import shutil
import subprocess

log = logging.getLogger("strategist.publish")


def _git(*args, cwd=None):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        # never log the remote URL (it contains the token)
        raise RuntimeError(f"git {args[0]} failed: {r.stderr.strip()[:200]}")
    return r.stdout


def publish(data_dir):
    repo, tok = os.environ.get("GITHUB_REPO"), os.environ.get("GITHUB_TOKEN")
    if not (repo and tok):
        return
    results = os.path.join(data_dir, "results")
    dated = sorted(d for d in glob.glob(os.path.join(results, "20*")) if os.path.isdir(d))
    if not dated:
        return
    latest_dir = dated[-1]
    wd = os.path.join(data_dir, "_publish")
    url = f"https://x-access-token:{tok}@github.com/{repo}.git"
    try:
        if not os.path.isdir(os.path.join(wd, ".git")):
            shutil.rmtree(wd, ignore_errors=True)
            _git("clone", "--depth", "1", url, wd)
        else:
            _git("remote", "set-url", "origin", url, cwd=wd)
            _git("pull", "--ff-only", cwd=wd)
        _git("config", "user.name", "strategist-bot", cwd=wd)
        _git("config", "user.email", "strategist-bot@users.noreply.github.com", cwd=wd)
        dest = os.path.join(wd, "results", os.path.basename(latest_dir))
        shutil.copytree(latest_dir, dest, dirs_exist_ok=True)
        shutil.copyfile(os.path.join(latest_dir, "report.md"), os.path.join(wd, "latest.md"))
        _git("add", "-A", cwd=wd)
        if _git("status", "--porcelain", cwd=wd).strip():
            _git("commit", "-m", f"Strategist run {os.path.basename(latest_dir)}", cwd=wd)
            _git("push", "origin", "HEAD", cwd=wd)
            log.info("Published %s to GitHub", os.path.basename(latest_dir))
    except Exception as e:  # noqa: BLE001
        log.warning("Publish skipped: %s", e)
