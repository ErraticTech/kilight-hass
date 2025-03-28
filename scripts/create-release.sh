#!/bin/bash -e

VERSION_BUMP_PART="$1";

if [ -z "$VERSION_BUMP_PART" ]; then
  echo "Usage: $0 <major|minor|patch>";
  exit 1;
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)";
PROJECT_DIR="$(dirname "$SCRIPT_DIR")";
VENV_PATHS=("$PROJECT_DIR/.venv" "$PROJECT_DIR/.venv/kilight-hass");

VENV_FOUND=false;
for venvPath in "${VENV_PATHS[@]}"; do
  if [ -f "$venvPath/bin/activate" ]; then
    echo "Found venv at $venvPath, activating...";
    source "$venvPath/bin/activate";
    VENV_FOUND=true;
    break;
  fi
done

if ! $VENV_FOUND; then
  echo "ERROR: Unable to find project venv directory (checked ${VENV_PATHS[*]})";
  exit 2;
fi

OLD_VERSION="$(bump-my-version show current_version)";
NEW_VERSION="$(bump-my-version show --increment "$VERSION_BUMP_PART" new_version)";

echo "Bumping $VERSION_BUMP_PART version from $OLD_VERSION to $NEW_VERSION";

git flow release start "$NEW_VERSION";

bump-my-version bump "$VERSION_BUMP_PART";

git flow release finish -s "$NEW_VERSION";

echo "Synchronizing develop and main...";

git switch main;

git merge develop;

git switch develop;

git merge main;

echo "Pushing everything...";

git push --atomic --follow-tags origin main develop
