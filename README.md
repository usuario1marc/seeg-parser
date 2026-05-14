# seeg-parser
Python module for parsing stereotactic electroencephalography (SEEG) recordings from equipment-specific formats to universal formats. Used for a project in Hospital Sant Joan de Déu in Barcelona. 

## Features

- Parse Micromed `.TRC` recordings
- Export recordings to BIDS iEEG structure
- Monopolar and bipolar referencing
- Interactive visualization helpers

## Useful links and tutorials

- [How to extract .TRC files from MICROMED's BrainQuick program](docs/TUTORIAL.md)
- [iEEG Brain Imaging Data Structure](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/intracranial-electroencephalography.html)

## Notes

This package was developed primarily for stimulation recordings from Micromed systems and may require adaptation for other acquisition setups.

Built around:
- MNE
- MNE-BIDS
- Wonambi

---

## Installation

```bash
git clone https://github.com/usuario1marc/seeg-parser.git
cd seeg-parser

python -m pip install -e .
```

## Basic usage

The main function of the package can be used with the following syntax:

```python
from seeg_parser import trc2bids

trc2bids(
    trc_filepath="patient01.TRC",
    bids_filepath="bids_dataset/",
    channels_filepath="config/channels.json",
    subject="01"
)
```

An `example.py` file is provided in the `examples` folder. It consists of a script for parsing a dataset of `.TRC` SEEG recordings into the BIDS format.

The script expects the input directory to contain a set of folders. Each folder should be named with the subject BIDS ID.
Inside each patient folder, there should be the raw `.TRC` files.

The script iterates through all patient folders and through all `.TRC` files inside each folder, parsing them and adding them
to the provided output BIDS dataset.

## Channel configuration

The parser requires a JSON configuration defining which electrodes should be included.
The JSON must map electrode names (e.g. "BIA", "HA", "TP") to a dictionary containing at least the key "type" (e.g. "eeg", "seeg"). Channel names in the recording are matched by searching for these electrode bases followed by a numeric contact index (e.g. "BIA1", "HA5") within the raw channel names.

Example:

```json
{
    "BIA": {
        "type": "seeg",
        "name": "Broca Ínsula Anterior",
        "area": "broca"
    },
    "TIA": {
        "type": "seeg",
        "name": "Temporal Ínsula Anterior",
        "area": "wernicke"
    }
}
```

An example `channels.json` file is provided in the `examples` folder.

## Visualization

To obtain information about a `.TRC` file:

```python
from seeg_parser.inspection import trcinfo

trcinfo("EEG_0001.TRC")
```

To visualize the BIDS output:

```python
from seeg_parser.inspection import bidsview

bidsview("bids_root", "sub-01")
```

---

## Dependencies

- numpy
- pandas
- mne
- mne-bids
- wonambi