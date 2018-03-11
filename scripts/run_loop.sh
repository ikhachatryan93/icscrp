#!/bin/bash
delay=$1
while :
do
    cd ../
    python3 extractor.py
    sleep $1
done
