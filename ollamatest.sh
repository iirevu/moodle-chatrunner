#!/bin/sh

# Note - ChatRunner package must be installed

U="http://localhost:11434/api/chat"

# M=deepseek-r1
M=llama3
# M=gpt-4o

L=Example/literature.json 
P=Example/problem.md 
A=Example/naiveanswer.md

python3 -m ChatRunner -l $L -u $U -m $M -A ollama  $* $P $A

