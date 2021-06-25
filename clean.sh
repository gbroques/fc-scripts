#!/bin/sh
# ------------------------------------------------------------
# Clean up *.FCStd1 backup files.
#
# See also:
#   https://forum.freecadweb.org/viewtopic.php?style=10&t=7296
# ------------------------------------------------------------
find . -name "*.FCStd1" -type f -delete
