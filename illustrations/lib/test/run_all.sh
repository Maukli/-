#!/bin/sh
cd "$(dirname "$0")"
for f in *.json; do node ../build.js "$f" || exit 1; done
