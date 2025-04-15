#!/bin/bash
#
# Make a release tag.
#
# Usage:
#   make-release.sh
#   make-release.sh NEW-VERSION
#   make-release.sh NEW-VERSION NEW-DEV-VERSION

set -eu
set -o pipefail

# Trap ERR to print the stack trace when a command fails.
# See: https://gist.github.com/ahendrix/7030300
function _errexit() {
  local err=$?
  set +o xtrace
  local code="${1:-1}"
  echo "Error in ${BASH_SOURCE[1]}:${BASH_LINENO[0]}: '${BASH_COMMAND}' exited with status $err" >&2
  # Print out the stack trace described by $FUNCNAME
  if [ ${#FUNCNAME[@]} -gt 2 ]; then
    echo 'Traceback:' >&2
    for ((i=1;i<${#FUNCNAME[@]}-1;i++)); do
      echo "  [$i]: at ${BASH_SOURCE[$i+1]}:${BASH_LINENO[$i]} in function ${FUNCNAME[$i]}" >&2
    done
  fi
  echo "Exiting with status ${code}" >&2
  exit "${code}"
}
trap '_errexit' ERR
set -o errtrace

##

# Tag prefix.
v=''

# pre_version_message <current_version_number> <version_number> <dev_version_number>:
# a hook function to print some message before bumping the version number.
function pre_version_message() {
  echo 'Please make sure that CHANGELOG.md is up-to-date.'
  echo 'You can use the output of the following command:'
  echo
  echo "  git-chglog --next-tag $v$2"
  echo
}

# get_current_version: prints the current version.
function get_current_version() {
  poetry version -s
}

# get_next_version <current_version_number>: prints the next version.
function get_next_version() {
  local next_version
  poetry version patch >/dev/null
  next_version=$(poetry version -s)
  git restore pyproject.toml
  echo "$next_version"
}

# get_next_dev_version <current_version_number> <next_version_number>: prints the next dev-version.
function get_next_dev_version() {
  local next_dev_version
  poetry version "$2" >/dev/null
  poetry version prepatch >/dev/null
  next_dev_version=$(poetry version -s)
  git restore pyproject.toml
  echo "$next_dev_version"
}

# version_bump <version_number>: a hook function to bump the version.
version_bump() {
  dev_version_bump "$1"
# NOTE: the "-i" option of sed is a GNU extension.
  sed -i "s|https://raw.githubusercontent.com/tueda/formset/.*/formset/formset.py|https://raw.githubusercontent.com/tueda/formset/$1/formset/formset.py|" README.md
}

# dev_version_bump <version_number_dev>: a hook function to bump to a dev-version.
dev_version_bump() {
  # NOTE: the "-i" option of sed is a GNU extension.
  sed -i "s/^__version__ *=.*/__version__ = \"$1\"/" formset/formset.py
}

##

# abort <message>: aborts the program with the given message.
function abort {
  echo "error: $*" 1>&2
  exit 1
}

# isclean: checks if the working repository is clean (untracked files are ignored).
function isclean() {
  [[ $(git diff --stat) == '' ]] && [[ $(git diff --stat HEAD) == '' ]]
}

# numstat <file>: prints number of added and deleted lines for the file (e.g., "0,0").
function numstat() {
  local stat
  stat=$(git diff --numstat "$1")
  if [[ $stat =~ ([0-9]+)[[:blank:]]+([0-9]+) ]]; then
    echo "${BASH_REMATCH[1]},${BASH_REMATCH[2]}"
  else
    echo 0,0
  fi
}

# Require the git command.
command -v git >/dev/null || abort 'git not available'

# Stop if the working directory is dirty.
isclean || abort 'working directory is dirty'

# Ensure that we are in the project root.
cd "$(git rev-parse --show-toplevel)"

# Determine the current version.
current_version=$(get_current_version)
[[ $current_version != '' ]] || abort 'current version not determined'

# Determine the next version.
if [[ $# == 0 ]]; then
  next_version=$(get_next_version "$current_version")
  [[ $next_version != '' ]] || abort 'next version not determined'
else
  next_version=$1
fi

# Determine the next dev-version.
if [[ $# -lt 2 ]]; then
  next_dev_version=$(get_next_dev_version "$current_version" "$next_version")
  [[ $next_dev_version != '' ]] || abort 'next dev-version not determined'
else
  next_dev_version=$2
fi

# Print the versions and confirm if they are fine.
pre_version_message "$current_version" "$next_version" "$next_dev_version"
echo 'This script will bump the version number.'
echo "  current commit      : $(git rev-parse --short HEAD)"
echo "  current version     : $current_version"
echo "  next version        : $next_version"
echo "  next dev-version    : $next_dev_version"
while :; do
  read -r -p 'ok? (y/N): ' yn
  case "$yn" in
    [yY]*)
      break
      ;;
    [nN]*)
      echo 'Aborted' >&2
      exit 1
      ;;
    *)
      ;;
  esac
done

# Bump the version.
version_bump "$next_version"
git commit -a -m "chore(release): bump version to $next_version"
git tag "$v$next_version"
dev_version_bump "$next_dev_version"
git commit -a -m "chore: bump version to $next_dev_version"

# Completed. Show some information.
echo "A release tag $v$next_version was successfully created."
echo "The current development version is now $next_dev_version"
echo "To push it to the origin:"
echo "  git push origin $v$next_version"
