#!/bin/bash

VENV_PATH="./venv/bin/activate"

TERMINAL_COUNT=1

TERMINAL_COMMAND="lxterminal -e  'bash -c \"source $VENV_PATH; exec bash\"'"

for i in $(seq 1 $TERMINAL_COUNT); do
	eval $TERMINAL_COMMAND &
done

source venv/bin/activate

echo "System 22 hut"