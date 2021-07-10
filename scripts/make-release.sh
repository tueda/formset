#!/bin/bash

# Usage:
#   make-release
#   make-release NEW-VERSION
#   make-release NEW-VERSION NEW-DEV-VERSION

set -eu
set -o pipefail

# version_bump <version_number>: a hook function to bump the version.
version_bump() {
  dev_version_bump $1
# NOTE: the "-i" option of sed is a GNU extension.
  sed -i "s|https://raw.githubusercontent.com/tueda/formset/.*/formset/formset.py|https://raw.githubusercontent.com/tueda/formset/$1/formset/formset.py|" README.md
}

# dev_version_bump <version_number_dev>: a hook function to bump to a dev-version.
dev_version_bump() {
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
dev_version_bump $(poetry version -s)
git commit -a -m "chore: bump version to $(poetry version -s)"
