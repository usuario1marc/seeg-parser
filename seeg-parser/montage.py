import re
import numpy as np
from collections import defaultdict


def bipolar(monopolar_data,
            monopolar_channels:list,
            sep:str='-'):
    """
    Computes a bipolar montage of the input data.
    
    Channels are assumed to follow a naming convention: <prefix><number> (e.g., A1, A2, B10).
    
    Adjacent channels are those with:
    - same prefix
    - consecutive numbers

    Parameters
    ----------

    monopolar_data : ndarray (n_channels, n_samples)
        Input monopolar data array.
    
    monopolar_channels : list of str (n_channels)
        List of input channel names.

    sep : str, optional
        Divider that separates channels in bipolar channel names.

    Returns
    -------

    bipolar_data : ndarray (n_bipolar_channels, n_samples)
        Output bipolar data array.

    bipolar_channels : list of str (n_bipolar_channels)
        List of output channel names.
    """

    bipolar_data = []
    bipolar_channels = []

    ch_idx = {ch: i for i, ch in enumerate(monopolar_channels)}

    # Parse channels into their prefix + their number
    parsed = []
    pattern = re.compile(r"^([A-Za-z]+)(\d+)$")
    for ch in monopolar_channels:
        match = pattern.match(ch)
        if match:
            prefix, num = match.groups()
            parsed.append((prefix, int(num), ch))

    # Group channels by prefix
    groups = defaultdict(list)
    for prefix, num, ch in parsed:
        groups[prefix].append((num, ch))

    # Compute bipolar channel by grouping
    for prefix, items in groups.items():
        items.sort(key=lambda x: x[0])
        for (n1, ch1), (n2, ch2) in zip(items[:-1], items[1:]):
            if n2 > n1:
                idx1 = ch_idx[ch1]
                idx2 = ch_idx[ch2]
                bipolar_data.append(monopolar_data[idx1] - monopolar_data[idx2])
                bipolar_channels.append(f"{ch1}{sep}{ch2}")

    if not bipolar_data:
        raise RuntimeError("No bipolar channels created.")

    bipolar_data = np.vstack(bipolar_data)

    return bipolar_data, bipolar_channels