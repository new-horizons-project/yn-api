#!/usr/bin/env fish

if not test -d "venv"
    python -m venv venv
end

source venv/bin/activate.fish
python -m pip install -r requirements.txt