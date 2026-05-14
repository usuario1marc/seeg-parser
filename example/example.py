"""
Example script for parsing a dataset of '.TRC' SEEG recordings into the BIDS format.

The script expects the input directory to contain a set of folders. Each folder should be named with the SUBJECT BIDS ID.
Inside each patient folder, there should be the raw '.TRC' files.

The script iterates through all patient folders and through all '.TRC' files inside each folder, parsing them and adding them
to the provided output BIDS dataset.
"""

from pathlib import Path
from seeg_parser import trc2bids, inspection

# =========================================================
# USER INPUT
# =========================================================

root = Path(r"D:\SJD")
trc_dir = root / "TRC"
bids_dir = root / "BIDS"
channels_config = r"example/channels.json"

# =========================================================
# MAIN LOOP
# =========================================================

for patient_dir in trc_dir.iterdir():
    if patient_dir.is_dir():
        patient_id = patient_dir.name
        print(f"\nConverting patient: {patient_id}")
        
        for i, trc_file in enumerate(patient_dir.glob("*.TRC")):
            run = str(i+1).zfill(2)
            print(f"\nConverting run: {run}\n")
            
            inspection.trcinfo(trc_file)
            trc2bids(trc_file, bids_dir, channels_config, patient_id, "cceps", session="01", run=run, reference="monopolar")