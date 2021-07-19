#!/bin/bash
# ----------------------------------------------
# Find all references to a spreadsheet alias.
# Third positional alias argument is optional.
# Supports escaping '<' and '>' symbols for XML.
# ----------------------------------------------
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: findrefs.bash <document> <spreadsheet> [alias]"
    exit 1
fi

# https://unix.stackexchange.com/a/635518
escape_xml="${0%/*}/escape_xml.sh"

freecad_documents=`find . -type f -name "*.FCStd"`
document=$($escape_xml $1)
spreadsheet=$($escape_xml $2)
alias=$3

SAVEIFS=$IFS
IFS=$(echo -en "\n\b")
for freecad_document in $freecad_documents
do
    result=$(zipgrep "$document#$spreadsheet.$alias" "$freecad_document")

    if [ ! -z "$result" ]; then
        printf "$freecad_document\n"
        if [ ! -z "$result" ]; then
            echo $result | xargs | grep --color=auto $document#$spreadsheet.$alias
        fi
        printf "\n"
    fi
done
IFS=$SAVEIFS
