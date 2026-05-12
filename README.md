# seeg-parser
Python module for parsing stereotactic electroencephalography (SEEG) recordings from equipment-specific formats to universal formats. Used for a project in Hospital Sant Joan de Déu in Barcelona.

Built around:
- MNE
- MNE-BIDS
- Wonambi

## Features

- Parse Micromed `.TRC` recordings
- Export recordings to BIDS iEEG structure
- Automatic stimulation event extraction
- Monopolar and bipolar referencing
- Interactive visualization helpers

---

## Installation

```bash
git clone https://github.com/usuario1marc/seeg-parser.git
cd seeg-parser

pip install -e .
```

---

## Basic usage

```python
from seeg_parser import trc2bids

trc2bids(
    trc_filepath="patient01.TRC",
    bids_filepath="bids_dataset/",
    channels_filepath="channels.json",
    subject="patient01"
)
```

---

## Channel configuration

The parser requires a JSON configuration defining which electrodes should be included.

Example:

```json
{
    "FO"  : {"type": "seeg", "area": "broca"},
    "GSM" : {"type": "seeg", "area": "none"},
    "WCP" : {"type": "seeg", "area": "wernicke"},
}
```

---

## Bipolar referencing

Bipolar referencing is computed automatically using adjacent contacts:

```text
A1-A2
A2-A3
A3-A4
```

---

## Visualization

```python
from seeg_parser.inspectfile import bidsview

bidsview("bids_root", "patient01")
```

---

## Notes

This package was developed primarily for stimulation recordings from Micromed systems and may require adaptation for other acquisition setups.

---

## Dependencies

- numpy
- pandas
- mne
- mne-bids
- wonambi