#!/bin/bash
#
# Compare estimated memory usage with actual memory usage.
#
# Usage:
#   memcheck.sh [path/to/python] [path/to/tform] [formset-options...]
#
# Examples:
#   memcheck.sh
#   memcheck.sh tform-4.2.0
#   memcheck.sh --ncpus 2 --total-cpus 2 --total-memory 4G
#
# Remarks:
#   - This script works only on Linux (checking "VmPeak" in /proc/pid/status).
#   - It (over)writes "form.set" in the current working directory.

set -eu
set -o pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PYTHON=python3
FORM=tform
FORMSET="$SCRIPT_DIR/../formset/formset.py"

while [ $# -gt 0 ]; do
  if [[ $1 =~ python ]]; then
    PYTHON=$1
    shift
    continue
  fi
  if [[ $1 =~ form ]]; then
    FORM=$1
    shift
    continue
  fi
  break
done

$FORM -v
$PYTHON $FORMSET "$@" -o -H
cat form.set
$PYTHON $FORMSET "$@" -u -H
$FORM $($PYTHON $FORMSET "$@" -f) $SCRIPT_DIR/memcheck.frm >/dev/null 2>&1 &
pid=$!
sleep 1
grep VmPeak /proc/$pid/status
