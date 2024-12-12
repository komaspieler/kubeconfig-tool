# kubeconfig-tool
small script to update kubeconfig to work with granted

## Requirements
This script assumes the following tools to be installed:

- aws cli
- granted
- kubectl

## Running the script
Set up venv using `python -m venv .`, activate with `source bin/activate` and install dependencies with `pip install -r requirements.txt`

Afterwards, execute the script using `python generate_kubeconfig.py` and follow the output.