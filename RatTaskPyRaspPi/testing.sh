. venv/bin/activate

cd ./Motopya

. .venv/bin/activate

echo "HI"

lxterminal --command "bash -c 'echo "HELLO";exec bash'"

lxterminal --command "bash -c '. .venv/bin/activate; exec bash'"




echo "BYE"

