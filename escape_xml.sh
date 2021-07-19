#!/bin/sh
# ------------------------------------
# Escapes '<' and '>' symbols for XML.
#
# For example:
#
#     $ ./escape_xml.sh '<Master>'
#       &lt;Master&gt;
# ------------------------------------
echo "$1" | \
    sed 's/>/\&gt;/g' | \
    sed 's/</\&lt;/g'
