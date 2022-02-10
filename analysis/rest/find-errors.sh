#!/bin/bash

set -e
cd /home/data/abcd/abcd-hispanic-via/code/log/3dTproject
rm -rf 3dErrors.txt

LIST=($(ls 3dTproject_*.err))

for file in ${LIST[@]}; do
	echo "--- ${file}" >> 3dErrors.txt
	err=$(echo "NO ERROR")
	err=$(echo $(grep -s 'ERROR' ${file}))
	echo "------------ ${err}" >> 3dErrors.txt
done