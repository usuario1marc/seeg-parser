import json
import re
from datetime import timezone

import pandas as pd
import mne
import wonambi

from mne_bids import BIDSPath, write_raw_bids

from . import montage as mount

def trc2bids(
    trc_filepath:str,
    bids_filepath:str,
    channels_filepath:str,
    subject:str,
    task:str="cceps",
    session:str="01",
    run:str="01",
    reference:str="monopolar",
    line_freq:float=50.0,
    units:dict=None
    ) -> None:

    """
    Parses Micromed `.TRC` file into BIDS structured data.
    
    This function is intended to be used specifically on `.TRC` recordings with stimulation events.
    See the BIDS (Brain Imaging Data Structure) iEEG specification:
    https://bids-specification.readthedocs.io/en/stable/modality-specific-files/intracranial-electroencephalography.html

    Parameters
    ----------

    trc_filepath : str
        Path to the input `.TRC` file.
    
    bids_filepath : str
        Root directory of the output BIDS dataset.

    channels_filepath : str
        Path to a `.json` file defining the electrode bases to include from the
        input file and their associated metadata.

        The JSON must map electrode base names (e.g. "BIA", "HA", "TP") to a
        dictionary containing at least the key "type" (e.g. "eeg", "seeg").

        Channel names in the recording are matched by searching for these
        electrode bases followed by a numeric contact index (e.g. "BIA1",
        "HA5") within the raw channel names.

        Example:
        {
            "BIA": {"type": "seeg", "area": "broca"},
            "HA":  {"type": "seeg", "area": "wernicke"}
        }
    
    subject : str
        Patient identifier, used to index the output files within the BIDS directory.
    
    task : str, optional
        Name of the experimental task performed during the recording.
        Default is "cceps".
    
    session : str, optional
        Identifier for a grouping of acquisitions for a subject
        (zero-padded, e.g., "01", "02").
        Default is "01".
    
    run : str, optional
        Index of the recording within the session
        (zero-padded, e.g., "01", "02").
        Default is "01".
    
    reference : str, optional
        Channel re-referencing scheme. One of {"monopolar", "bipolar"}.
        If "bipolar", channels are re-referenced according to a bipolar montage.
        Default is "monopolar".

    line_freq : float, optional
        Power line frequency used to annotate line noise in the recording.
        Default is `50.0`.

    units : dict of str, optional
        Units for the stimulation event descriptors. Must contain the keys
        "time" and "amplitude". Default values are {"time": "µsec", "amplitude": "mA"}.
    """

    # ----- PART 1. Channels and data -----

    # Open JSON with channel list
    with open(channels_filepath, 'r', encoding="utf-8") as file:
        included_channels = json.load(file)

    # Read .TRC file using wonambi's Micromed reader
    micromed = wonambi.ioeeg.micromed.Micromed(trc_filepath)
    _, start_time, sfreq, ch_names, n_samples, _ = micromed.return_hdr()
    start_time = start_time.replace(tzinfo=timezone.utc)

    # Select only channels from 'ch_names' that are in 'included_channels'
    included_channel_names = sorted(included_channels.keys(), key=len, reverse=True)
    pattern = re.compile(rf"\b({'|'.join(included_channel_names)})\s*\d+\b")

    trc_channels_i = [] # Channel indices in the TRC files
    monopolar_channels = [] # Clean version of those channel names (e.g. "BIA1" instead of "EEG BIA1-GND")
    channel_types = [] # Found in the JSON file (e.g. "eeg", "seeg")

    for i, ch in enumerate(ch_names):
        match = pattern.search(ch)
        if match:
            trc_channels_i.append(i)
            clean_name = re.sub(r"\s+", "", match.group(0))
            monopolar_channels.append(clean_name)
            channel_types.append(included_channels[match.group(1)]["type"])
    
    # Read data from the selected channels in the .TRC file
    data = micromed.return_dat(trc_channels_i, 0, int(n_samples-1))
    data = data * 1e-6 # Convert from microvolts to volts

    # Re-reference data if necessary
    if reference == "monopolar":

        info = mne.create_info(
            ch_names=monopolar_channels,
            sfreq=sfreq,
            ch_types=channel_types
        )

        with info._unlock():
            info["meas_date"] = start_time
            info["line_freq"] = line_freq

        raw = mne.io.RawArray(data, info)

    elif reference == "bipolar":

        bipolar_data, bipolar_channels = mount.bipolar(data, monopolar_channels)
        
        info = mne.create_info(
            ch_names=bipolar_channels,
            sfreq=sfreq,
            ch_types=channel_types[0] # Assume that the type of the first channel represents the rest
        )

        with info._unlock():
            info["meas_date"] = start_time
            info["line_freq"] = line_freq

        raw = mne.io.RawArray(bipolar_data, info)
    
    else:
        raise ValueError(f"Unrecognized reference type ({reference}).")


    # ----- PART 2. Events -----

    # Assign default values to 'units'
    if units is None:
        units = {"time": "µsec", "amplitude": "mA"}
    conversion = {"µsec": 1e-6, "mA": 1e-3, "sec": 1, "A": 1, "msec": 1e-3}

    # Read event markers
    markers = micromed.return_markers()

    stim_locations = [] # Channel pair between which stimulation was performed
    stim_amplitudes = []
    stim_durations = []
    stim_times = []

    loc, amp, dur = None, None, None

    for mkr in markers:

        # Detect header marker (contains stimulation metadata)
        if units["time"] in str(mkr["name"]) and units["amplitude"] in str(mkr["name"]):
            
            try:
                loc, amp, _, dur = mkr["name"].split()
                continue
            except ValueError:
                # Invalid annotation name
                continue

        # Detect digital trigger markers (contains stimulation time)
        if "-1" in str(mkr["name"]) or "65535" in str(mkr["name"]):

            if loc is None or amp is None or dur is None:
                continue
            
            stim_amplitudes.append(float(amp.replace(units["amplitude"], "")) * conversion[units["amplitude"]])
            stim_durations.append(float(dur.replace(units["time"], "")) * conversion[units["time"]])
        
            ch1, ch2 = sorted(loc.split("-"))
            stim_locations.append(f"{ch1}-{ch2}")

            stim_times.append(mkr["start"])

    # Put event data into pandas dataframe
    events_df = pd.DataFrame()
    events_df["onset"] = stim_times
    events_df["duration"] = stim_durations
    events_df["trial_type"] = "electrical_stimulation"
    events_df["electrical_stimulation_site"] = stim_locations
    events_df["electrical_stimulation_current"] = stim_amplitudes

    # Add annotations to RAW object
    annotations = mne.Annotations(
        onset=events_df["onset"].values,
        duration=events_df["duration"].values,
        description=events_df["electrical_stimulation_site"].values,
        orig_time=start_time,
    )
    raw.set_annotations(annotations)


    # ----- PART 3. Save in BIDS directory -----

    # Create the root BIDS directory and all auxiliary files if it does not exist yet.
    # Add the subdirectory for the specific '.TRC' input recording.
    bids_file = BIDSPath(
        subject=subject,
        session=session,
        task=task,
        run=run,
        datatype="ieeg",
        root=bids_filepath
    )
    
    write_raw_bids(
        raw,
        bids_file,
        overwrite=True,
        allow_preload=True,
        format="EDF",
        events=None
    )

    # Overwrite events.tsv file with extra fields (i.e. electrical stimulation site and current)
    events_file = bids_file.copy().update(suffix="events", extension=".tsv")
    events_df.to_csv(events_file.fpath, sep="\t", index=False)


    # ----- PART 4. Set metadata in JSON file -----

    ieeg_json_path = bids_file.copy().update(suffix="ieeg", extension=".json")
    with open(ieeg_json_path.fpath, "r") as f:
        metadata = json.load(f)

    # Note & to-do: add function argument to modify some metadata fields
    # (e.g. InstitutionName)
    
    metadata.update({
        "iEEGReference": reference,
        "SamplingFrequency": sfreq,
        "PowerLineFrequency": line_freq,
        "ElectricalStimulation": True,
        "RecordingType": "continuous",
        "Manufacturer": "MICROMED",
        "InstitutionName": "Hospital Sant Joan de Déu"
    })

    with open(ieeg_json_path.fpath, "w") as f:
        json.dump(metadata, f, indent=4)


    # ----- PART 5. Set channel types in TSV channels file -----

    # Note & to-do: This part is necessary for ER Detect to recognize the BIDS file.
    # We don't know why it's necessary to enforce the channel types again in the TSV.
    # This snippet can be revised in the future to remove the redundancy it introduces.

    channels_file = bids_file.copy().update(suffix="channels", extension=".tsv")
    channels_df = pd.read_csv(channels_file.fpath, sep="\t")
    if reference == "monopolar":
        channels_df["type"] = channel_types
    elif reference == "bipolar":
        channels_df["type"] = channel_types[0]
    channels_df.to_csv(channels_file.fpath, sep="\t", index=False)


# =========================================================
# EXAMPLE USAGE
# =========================================================

if __name__ == '__main__':
    import inspection

    patient_id = "<patient_id>"

    trc_filepath = rf"<trc_root>/{patient_id}.TRC"
    bids_filepath = r"<bids_root>"
    channels_filepath = r"<channels_config_root>.json"

    inspection.trcinfo(trc_filepath)
    trc2bids(trc_filepath, bids_filepath, channels_filepath, patient_id, "cceps")
    inspection.bidsview(bids_filepath, patient_id)