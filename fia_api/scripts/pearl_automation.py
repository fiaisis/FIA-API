import argparse
import logging
import os
import sys
import time
from pathlib import Path

import requests

from fia_api.core.models import State

# Simple Mantid Script for PEARL as provided in the issue
PEARL_SCRIPT = """
from mantid.simpleapi import *
import numpy as np

Cycles2Run=['25_4']
Path2Save = r'E:\\\\Data\\\\Moderator'
Path2Data = r'X:\\\\data'

CycleDict = {
    "start_25_4": 124987,
    "end_25_4": 124526,
}

for cycle in Cycles2Run:
    reject=[]
    peak_centres=[]
    peak_centres_error=[]
    peak_intensity=[]
    peak_intensity_error=[]
    uAmps=[]
    RunNo=[]
    index=0
    start=CycleDict['start_'+cycle]
    end=CycleDict['end_'+cycle]
    for i in range(start,end+1):
        if i == 95382:
            continue
        Load(Filename=Path2Data+'\\\\cycle_'+cycle+'\\\\PEARL00'+ str(i)+'.nxs', OutputWorkspace=str(i))
        ws = mtd[str(i)]
        run = ws.getRun()
        pcharge = run.getProtonCharge()
        if pcharge <1.0:
            reject.append(str(i))
            DeleteWorkspace(str(i))
            continue
        NormaliseByCurrent(InputWorkspace=str(i), OutputWorkspace=str(i))
        ExtractSingleSpectrum(InputWorkspace=str(i),WorkspaceIndex=index, OutputWorkspace=str(i)+ '_' + str(index))
        CropWorkspace(InputWorkspace=str(i)+ '_' + str(index), Xmin=1100, Xmax=19990, OutputWorkspace=str(i)+ '_' + str(index))
        DeleteWorkspace(str(i))

        fit_output = Fit(Function='name=Gaussian,Height=19.2327,\\\\PeakCentre=4843.8,Sigma=1532.64,\\\\constraints=(4600<PeakCentre<5200,1100<Sigma<1900);\\\\name=FlatBackground,A0=16.6099,ties=(A0=16.6099)', InputWorkspace=str(i)+ '_' + str(index), MaxIterations=1000, CreateOutput=True, Output=str(i)+ '_' + str(index) + '_fit', OutputCompositeMembers=True, StartX=3800, EndX=6850, Normalise=True)
        paramTable = fit_output.OutputParameters

        if paramTable.column(1)[1] < 4600.0 or paramTable.column(1)[1] > 5200.0:
            DeleteWorkspace(str(i)+'_0_fit_Parameters')
            DeleteWorkspace(str(i)+'_0_fit_Workspace')
            DeleteWorkspace(str(i)+'_0')
            DeleteWorkspace(str(i)+'_0_fit_NormalisedCovarianceMatrix')
            reject.append(str(i))
            continue
        else:
            uAmps.append(pcharge)
            peak_centres.append(paramTable.column(1)[1])
            peak_centres_error.append(paramTable.column(2)[1])
            peak_intensity.append(paramTable.column(1)[0])
            peak_intensity_error.append(paramTable.column(2)[0])
            RunNo.append(str(i))
            DeleteWorkspace(str(i)+'_0')
            DeleteWorkspace(str(i)+'_0_fit_Parameters')
            DeleteWorkspace(str(i)+'_0_fit_Workspace')
            DeleteWorkspace(str(i)+'_0_fit_NormalisedCovarianceMatrix')

    combined_data=np.column_stack((RunNo, uAmps, peak_intensity, peak_intensity_error, peak_centres, peak_centres_error))
    np.savetxt(Path2Save+'\\\\peak_centres_'+cycle+'.csv', combined_data, delimiter=", ", fmt='% s',)
"""

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class PearlAutomation:
    def __init__(self, fia_url, auth_url, username, password, output_dir, runner_image=None):
        self.fia_url = fia_url.rstrip("/")
        self.auth_url = auth_url.rstrip("/")
        self.username = username
        self.password = password
        self.output_dir = Path(output_dir)
        self.runner_image = runner_image
        self.token = None

    def authenticate(self):
        logger.info(f"Authenticating user {self.username} at {self.auth_url}")
        try:
            response = requests.post(
                f"{self.auth_url}/login", json={"username": self.username, "password": self.password}, timeout=30
            )
            response.raise_for_status()
            self.token = response.json().get("token")
            if not self.token:
                raise ValueError("No token found in login response")
            logger.info("Authentication successful")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def get_runner_image(self):
        if self.runner_image:
            return self.runner_image

        logger.info("Fetching available Mantid runners")
        response = requests.get(f"{self.fia_url}/jobs/runners", headers=self.get_headers(), timeout=30)
        response.raise_for_status()
        runners = response.json()
        if not runners:
            raise ValueError("No Mantid runners found")

        # Select latest version if possible, or just the first one
        latest_version = sorted(runners.keys())[-1]
        logger.info(f"Selected Mantid runner: {latest_version}")
        return latest_version

    def submit_job(self, script, runner_image):
        logger.info(f"Submitting simple job with runner {runner_image}")
        payload = {"runner_image": runner_image, "script": script}
        response = requests.post(f"{self.fia_url}/job/simple", json=payload, headers=self.get_headers(), timeout=30)
        response.raise_for_status()
        job_id = response.json()
        logger.info(f"Job submitted successfully. Job ID: {job_id}")
        return job_id

    def monitor_job(self, job_id, poll_interval=5):
        logger.info(f"Monitoring job {job_id}")
        while True:
            response = requests.get(f"{self.fia_url}/job/{job_id}", headers=self.get_headers(), timeout=30)
            response.raise_for_status()
            job_data = response.json()
            state = job_data.get("state")

            logger.info(f"Job {job_id} current state: {state}")

            if state == State.SUCCESSFUL.value:
                logger.info(f"Job {job_id} completed successfully")
                return job_data
            if state in [State.ERROR.value, State.UNSUCCESSFUL.value]:
                error_msg = job_data.get("status_message", "No error message provided")
                logger.error(f"Job {job_id} failed with state {state}: {error_msg}")
                raise RuntimeError(f"Job {job_id} failed: {error_msg}")

            time.sleep(poll_interval)

    def download_results(self, job_id, outputs):
        if not outputs:
            logger.warning(f"No outputs found for job {job_id}")
            return

        # Outputs is expected to be a string or list of filenames
        filenames = outputs.split(",") if isinstance(outputs, str) else outputs

        self.output_dir.mkdir(parents=True, exist_ok=True)

        for file in filenames:
            filename = file.strip()
            if not filename:
                continue

            logger.info(f"Downloading {filename} for job {job_id}")
            response = requests.get(
                f"{self.fia_url}/job/{job_id}/filename/{filename}", headers=self.get_headers(), timeout=30, stream=True
            )
            response.raise_for_status()

            file_path = self.output_dir / filename
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Downloaded {filename} to {file_path}")

    def run(self):
        try:
            self.authenticate()
            runner_image = self.get_runner_image()
            job_id = self.submit_job(PEARL_SCRIPT, runner_image)
            job_data = self.monitor_job(job_id)
            self.download_results(job_id, job_data.get("outputs"))
            logger.info("PEARL automation completed successfully")
        except Exception as e:
            logger.error(f"PEARL automation failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate PEARL Mantid jobs via FIA API")
    parser.add_argument("--fia-url", default=os.environ.get("FIA_API_URL", "http://localhost:8080"), help="FIA API URL")
    parser.add_argument(
        "--auth-url", default=os.environ.get("AUTH_API_URL", "http://localhost:8001"), help="Auth API URL"
    )
    parser.add_argument("--username", default=os.environ.get("PEARL_USERNAME"), help="Auth Username")
    parser.add_argument("--password", default=os.environ.get("PEARL_PASSWORD"), help="Auth Password")
    parser.add_argument(
        "--output-dir", default=os.environ.get("OUTPUT_DIRECTORY", "./output"), help="Output directory for results"
    )
    parser.add_argument(
        "--runner", default=os.environ.get("MANTID_RUNNER_IMAGE"), help="Specific Mantid runner image to use"
    )

    args = parser.parse_args()

    if not args.username or not args.password:
        logger.error(
            "Username and password must be provided via arguments or environment variables (PEARL_USERNAME, PEARL_PASSWORD)"
        )
        sys.exit(1)

    automation = PearlAutomation(
        args.fia_url, args.auth_url, args.username, args.password, args.output_dir, args.runner
    )
    automation.run()
