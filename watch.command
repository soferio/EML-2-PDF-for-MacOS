#!/bin/sh
here="`dirname \"$0\"`"
echo "cd-ing to $here"
cd "$here" || exit 1

source .venv/bin/activate
python3 console.py -w EML_DIRECTORY 2>&1 &