import wonambi
import mne
import datetime
import pandas as pd
from mne_bids import BIDSPath, read_raw_bids


def trcinfo(trc_filepath:str) -> None:
    """
    Helper function that prints basic information from a `.TRC` recording into the console.

    Parameters
    ----------
    trc_filepath : str
        Path to the input `.TRC` file.
    """

    micromed = wonambi.ioeeg.micromed.Micromed(trc_filepath)
    _, start_time, sfreq, ch_names, n_samples, _ = micromed.return_hdr()
    markers = micromed.return_markers()
    duration = datetime.timedelta(seconds=int(n_samples/sfreq))

    print(f"\nRecording start:\t{start_time}")
    print(f"Recording finish:\t{start_time + duration}")
    print(f"Recording duration:\t{duration}")

    print(f"\nSampling frequency:\t{sfreq}Hz")

    print("\nChannel names:")
    print("\t".join(ch_names) + "\t")

    print(f"\nNumber of annotations:\t{len(markers)}\n")


def bidsview(bids_root, subject, session="01", task="cceps", run="01"):
    """
    Helper function that opens a MNE-based preview of the EEG in a BIDS file.

    Parameters
    ----------
    bids_filepath : str
        Root directory of the output BIDS dataset.

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
    """

    bids_path = BIDSPath(
        subject=subject,
        session=session,
        task=task,
        run=run,
        datatype="ieeg",
        root=bids_root
    )

    # Load recording
    raw = read_raw_bids(bids_path)

    # Load events.tsv
    events_path = bids_path.copy().update(suffix="events", extension=".tsv")
    events_df = pd.read_csv(events_path.fpath, sep="\t")

    # Convert to MNE annotations
    annotations = mne.Annotations(
        onset=events_df["onset"].values,
        duration=events_df["duration"].values,
        description=events_df["electrical_stimulation_site"].values
    )

    raw.set_annotations(annotations)

    # Open interactive viewer
    raw.plot(
        scalings="auto",
        duration=3,
        n_channels=10,
        title="BIDS stimulation preview"
    )