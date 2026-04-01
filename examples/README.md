# Examples of using the FIA API
This repo contains some example scripts of utilising the FIA API. 

## PEARL Jobs
There are currently two types of example jobs in this directory: Simple jobs and Fast Jobs.


## Using pearl_automation.py in command line
This python script can be used to submit a script, currently in quotes at the top of the file, to the simple jobs endpoint for FIA API. 
Info about pearl_automation can be found by running:

```python -m examples.job_scripts.pearl_automation --help```

which should print the following: 

```
usage: python.exe -m examples.job_scripts.pearl_automation [-h] [--fia-url FIA_URL][--auth-url AUTH_URL][--username USERNAME] [--password PASSWORD][--output-dir OUTPUT_DIR] [--runner RUNNER]

Automate PEARL Mantid jobs via FIA API

options:
  -h, --help            show this help message and exit
  --fia-url FIA_URL     FIA API URL
  --auth-url AUTH_URL   Auth API URL
  --username USERNAME   Auth Username
  --password PASSWORD   Auth Password
  --output-dir OUTPUT_DIR
                        Output directory for results
  --runner RUNNER       Specific Mantid runner image to use
  ```

As you can see, there are a few environment variables required to authenticate and run this python script. These can either be set in a .env file, in the command line itself, or through calling the PearlAutomation method in a python environment (example below).

You can also run the individual methods of this script in a venv: 

```
from fia_api.scripts.pearl_automation import PearlAutomation

pa = PearlAutomation(
    fia_url="http://localhost:8080/api",
    auth_url="http://localhost:8001/auth",
    username="your_user",
    password="your_password",
    output_dir="./manual_test_output",
)

# Test each step in isolation:
pa.authenticate()          # Check pa.token is set
pa.get_runner_image()      # Check a version string is returned
job_id = pa.submit_job(pa.__class__.__module__, pa.runner_image)  # Check an int is returned
job_data = pa.monitor_job(job_id)   # Watch the polling logs
pa.download_results(job_id, job_data.get("outputs"))  # Confirm files land in ./manual_test_output
```

Or you can simple do the following, also in a venv: 

```
from fia_api.scripts.pearl_automation import PearlAutomation

pa = PearlAutomation(
    fia_url="http://localhost:8080/api",
    auth_url="http://localhost:8001/auth",
    username="your_user",
    password="your_password",
    output_dir="./manual_test_output",
)

pa.run()
```

## Using pearl_fast_jobs in command line




These examples scripts were written in part with Antigravity, specifically Claude Opus 4.6, and Gemini 3 Flash
