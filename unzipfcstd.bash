#!/bin/bash
# -------------------------------------------------
# Unzip all FreeCAD documents in current directory.
# -------------------------------------------------
freecad_documents=`find . -type f -name "*.FCStd"`
echo $freecad_documents

SAVEIFS=$IFS
IFS=$(echo -en "\n\b")
for document in $freecad_documents
do
  name=`echo $document | sed -rn 's/\.\/(.*).FCStd$/\1/p'`
  unzip $document -d $name
done
IFS=$SAVEIFS
