#!/bin/bash
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    source ./venv/Scripts/activate
else
    source ./venv/bin/activate
fi

echo "Virtual environment activated!"