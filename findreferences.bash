#!/bin/bash
# ----------------------------------------------
# Find all references to a spreadsheet variable.
# ----------------------------------------------
if [ -z "$1" ]; then
    echo "Usage: findreferences.bash <variable name>"
    exit 1
fi
freecad_documents=`find . -type f -name "*.FCStd"`
variable=$1

SAVEIFS=$IFS
IFS=$(echo -en "\n\b")
for document in $freecad_documents
do
    result1=$(zipgrep "Master_of_Puppets#Spreadsheet.$variable" "$document")
    result2=$(zipgrep "&lt;&lt;Master of Puppets&gt;&gt;#Spreadsheet.$variable" "$document")

    if [ ! -z "$result1" ] || [ ! -z "$result2" ]; then
        printf "$document\n"
        if [ ! -z "$result1" ]; then
            echo $result1 | xargs | grep --color=auto $variable
        fi
        if [ ! -z "$result2" ]; then
            echo $result2 | xargs | grep --color=auto $variable
        fi
        printf "\n"
    fi
done
IFS=$SAVEIFS
