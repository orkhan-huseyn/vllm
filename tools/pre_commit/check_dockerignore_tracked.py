# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""Check that no `.dockerignore` entry excludes tracked files.

Docker builds bind-mount `.git` but copy the working tree through the build
context, so git sees any tracked file that `.dockerignore` drops as deleted.
That dirty tree fails `tools/check_repo.sh` in release builds
(`GIT_REPO_CHECK=1`) and adds a `.dYYYYMMDD` dirty suffix to the wheel version.

Usage:
    python tools/pre_commit/check_dockerignore_tracked.py
"""

import subprocess
import sys
from pathlib import Path

DOCKERIGNORE = Path(".dockerignore")


def main() -> int:
    # Docker matches every pattern from the context root (`foo` == `/foo`),
    # which is what git's `:(glob)` pathspec does too.
    # shortcut: `!` exceptions are skipped, so an entry they re-include is
    # still reported; handle them if `.dockerignore` starts using them.
    patterns = [
        f":(glob){line.strip().strip('/')}"
        for line in DOCKERIGNORE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith(("#", "!"))
    ]
    if not patterns:
        return 0
    tracked = subprocess.run(
        ["git", "ls-files", "--", *patterns],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.split()
    if not tracked:
        return 0
    print(
        f"{DOCKERIGNORE} excludes {len(tracked)} tracked file(s). Docker builds "
        "would see them as deleted and the git tree as dirty, failing "
        "tools/check_repo.sh in release builds. First few:"
    )
    for path in tracked[:10]:
        print(f"  {path}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
