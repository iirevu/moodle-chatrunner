# Requires the -C option with a JSON config file.

L=Example/Mikroskop/literature.json 
P=Example/Mikroskop/problem.md 
A=Example/Mikroskop/naiveanswer.md

python3 -m ChatRunner -l $L $* $P $A


