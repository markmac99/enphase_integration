#!/bin/bash
source ~/.bashrc
here="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $here
source ~/miniconda3/etc/profile.d/conda.sh
conda activate openhabstuff
echo starting $(date)
python getEnphaseData.py
echo done $(date)
