# DUNE-HV-Crate-Testing
Automated production testing for DUNE HV Crate

Navigate to the simulation directory and use

`./setup.sh`

Which should set up the virtual environment and the require Python packages. Then edit the `config.json` file for your preferences.

Run like:

`python3 dune_hv_crate_test.py config.json`

The script will ask you to name the test once it starts. Alternatively you can just put the name in the command, like:

`python3 dune_hv_crate_test.py config.json name_of_test`
