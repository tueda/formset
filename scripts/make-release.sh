#!/bin/bash

# Usage:
#   make-release
#   make-release NEW-VERSION
#   make-release NEW-VERSION NEW-DEV-VERSION

set -eu
set -o pipefail

# Hook function.
version_bump() {
# NOTE: the "-i" option of sed is a GNU extension.
  sed -i "s/^__version__ *=.*/__version__ = \"$1\"/" formset/formset.py
}

# Check if the working repository is clean.
{
  [[ $(git diff --stat) == '' ]] && [[ $(git diff --stat HEAD) == '' ]]
} || {
  echo 'error: working directory is dirty' 1>&2
  exit 1
}

# Determine the next versions.
next_version=patch
next_dev_version=prepatch
if [[ $# -ge 2 ]]; then
  next_version=$1
  next_dev_version=$2
elif [[ $# -eq 1 ]]; then
  next_version=$1
fi

# Bump the version.
poetry version $next_version
version_bump $(poetry version -s)
git commit -a -m "chore: bump version to $(poetry version -s)"
git tag $(poetry version -s)
poetry version $next_dev_version
version_bump $(poetry version -s)
git commit -a -m "chore: bump version to $(poetry version -s)"
