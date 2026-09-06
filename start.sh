#!/bin/sh
CITY_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 -B "$CITY_ROOT/tools/controltower/city_native.py" "$@"
