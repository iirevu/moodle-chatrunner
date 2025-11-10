# Requires the -C option with a JSON config file.

L=Example/literature.json 
P=Example/problem.md 
A=Example/naiveanswer.md

python3 -m ChatRunner -l $L $* $P $A


