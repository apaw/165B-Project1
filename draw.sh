#!/bin/bash

if [ -z "$1" ]; then
    NAME="mondial"
else
    NAME=$1
fi

DNAME=$NAME'.gv'
PNAME=${DNAME%.*}'.png'
python psv.py > $DNAME
#dot -Tpng $DNAME > $PNAME
sfdp -x -Goverlap=scale -Tpng $DNAME > $PNAME 
xdg-open $PNAME