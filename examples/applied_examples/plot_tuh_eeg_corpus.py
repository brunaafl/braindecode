"""
Process a big data EEG resource (TUH EEG Corpus)
================================================

In this example, we showcase usage of the Temple University Hospital EEG Corpus
(https://www.isip.piconepress.com/projects/tuh_eeg/html/downloads.shtml#c_tueg)
including simple preprocessing steps as well as cutting of compute windows.

.. contents:: This example covers:
   :local:
   :depth: 2


"""

# Author: Lukas Gemein <l.gemein@gmail.com>
#
# License: BSD (3-clause)

import tempfile

import numpy as np
import matplotlib.pyplot as plt
import mne

from braindecode.datasets import TUH
from braindecode.preprocessing import (
    preprocess, Preprocessor, create_fixed_length_windows, scale as multiply)


plt.style.use('seaborn')
mne.set_log_level('ERROR')  # avoid messages everytime a window is extracted


###############################################################################
# Creating the dataset using TUHMock
# -------------------------------------
#
# Since the data is not available at the time of the creation of this example,
# we are required to mock some of the dataset functionality. Therefore, if you
# want to try this code with the actual data, please disconsider this section.

from braindecode.datasets.tuh import _TUHMock as TUH  # noqa F811


###############################################################################
# Firstly, we start by creating a TUH mock dataset using braindecode's _TUHMock class.
# This class is able to read the recordings from TUH_PATH and generate a description
# by parsing information from file paths, such as patient id and recording data.
# THis description can later be accessed by the object's .description method.
# After that, the files are sorted chronologically by year, month, day,
# patient id, recording session and segment, and then use the description corresponding
# to the specified by recording ids.
# FInally, additional information regarding age and gender of the subjects are parsed
# directly to the description.

TUH_PATH = 'please insert actual path to data here'
N_JOBS = 2  # specify the number of jobs for loading and windowing
tuh = TUH(
    path=TUH_PATH,
    recording_ids=None,
    target_name=None,
    preload=False,
    add_physician_reports=False,
    n_jobs=1 if TUH.__name__ == '_TUHMock' else N_JOBS,  # Mock dataset can't
    # be loaded in parallel
)

###############################################################################
# We can visualize our data's statistics using the class' "description" method

fig, ax = plt.subplots() #1, 1, figsize=(15, 5)
genders = tuh.description.gender.unique()
x = [tuh.description.age[tuh.description.gender == g] for g in genders]
ax.hist(
    x=x,
    stacked=True,
    bins=np.arange(100, dtype=int),
    alpha=.5,
)
ax.legend(genders, fontsize=10)
ax.set_xlabel('Age [years]', fontsize=10)
ax.set_ylabel('Count', fontsize=10)
plt.show()


###############################################################################
# Preprocessing
# -------------------------------------
#
# Selecting recordings
# ~~~~~~~~~~~~~
#
# First, we will do some selection of available recordings based on the duration.
# We will select those recordings that have at least five minutes duration.
#

def select_by_duration(ds, tmin=0, tmax=None):
    if tmax is None:
        tmax = np.inf
    # determine length of the recordings and select based on tmin and tmax
    split_ids = []
    for d_i, d in enumerate(ds.datasets):
        duration = d.raw.n_times / d.raw.info['sfreq']
        # select the ones in the required duration range
        if tmin <= duration <= tmax:
            split_ids.append(d_i)
    splits = ds.split(split_ids)
    split = splits['0']
    return split


tmin = 5 * 60
tmax = None
tuh = select_by_duration(tuh, tmin, tmax)


###############################################################################
# Next, we will discard all recordings that have an incomplete channel
# configuration on the channels that we are interested. The dataset is subdivided into
# recordings with 'le' and 'ar' (?) reference which we will have to consider.

short_ch_names = sorted([
    'A1', 'A2',
    'FP1', 'FP2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2',
    'F7', 'F8', 'T3', 'T4', 'T5', 'T6', 'FZ', 'CZ', 'PZ'])

# TUH data is subdivided into 'le' and 'ar' recordings references
ar_ch_names = sorted([
    'EEG A1-REF', 'EEG A2-REF',
    'EEG FP1-REF', 'EEG FP2-REF', 'EEG F3-REF', 'EEG F4-REF', 'EEG C3-REF',
    'EEG C4-REF', 'EEG P3-REF', 'EEG P4-REF', 'EEG O1-REF', 'EEG O2-REF',
    'EEG F7-REF', 'EEG F8-REF', 'EEG T3-REF', 'EEG T4-REF', 'EEG T5-REF',
    'EEG T6-REF', 'EEG FZ-REF', 'EEG CZ-REF', 'EEG PZ-REF'])
le_ch_names = sorted([
    'EEG A1-LE', 'EEG A2-LE',
    'EEG FP1-LE', 'EEG FP2-LE', 'EEG F3-LE', 'EEG F4-LE', 'EEG C3-LE',
    'EEG C4-LE', 'EEG P3-LE', 'EEG P4-LE', 'EEG O1-LE', 'EEG O2-LE',
    'EEG F7-LE', 'EEG F8-LE', 'EEG T3-LE', 'EEG T4-LE', 'EEG T5-LE',
    'EEG T6-LE', 'EEG FZ-LE', 'EEG CZ-LE', 'EEG PZ-LE'])
assert len(short_ch_names) == len(ar_ch_names) == len(le_ch_names)
ar_ch_mapping = {ch_name: short_ch_name for ch_name, short_ch_name in zip(
    ar_ch_names, short_ch_names)}
le_ch_mapping = {ch_name: short_ch_name for ch_name, short_ch_name in zip(
    le_ch_names, short_ch_names)}
ch_mapping = {'ar': ar_ch_mapping, 'le': le_ch_mapping}

def select_by_channels(ds, ch_mapping):
    split_ids = []
    for i, d in enumerate(ds.datasets):
        ref = 'ar' if d.raw.ch_names[0].endswith('-REF') else 'le'
        # these are the channels we are looking for
        seta = set(ch_mapping[ref].keys())
        # these are the channels of the recoding
        setb = set(d.raw.ch_names)
        # if recording contains all channels we are looking for, include it
        if seta.issubset(setb):
            split_ids.append(i)
    return ds.split(split_ids)['0']


tuh = select_by_channels(tuh, ch_mapping)


###############################################################################
# Combining preprocessing steps
# ~~~~~~~~~~~~~
#
# Next, we use braindecode's preprocess to combine and execute several preprocessing
# steps that are executed through 'mne`:
#
# #. Crop the recordings to a region of interest
# #. Re-reference all recordings to 'ar' (requires load)
# #. Rename channels to short channel names
# #. Pick channels of interest
# #. Scale signals to micro volts (requires load)
# #. Clip outlier values to +/- 800 micro volts (requires load)
# #. Resample recordings to a common frequency (requires load)

def custom_rename_channels(raw, mapping):
    # rename channels which are dependent on referencing:
    # le: EEG 01-LE, ar: EEG 01-REF
    # mne fails if the mapping contains channels as keys that are not present
    # in the raw
    reference = raw.ch_names[0].split('-')[-1].lower()
    assert reference in ['le', 'ref'], 'unexpected referencing'
    reference = 'le' if reference == 'le' else 'ar'
    raw.rename_channels(mapping[reference])


def custom_crop(raw, tmin=0.0, tmax=None, include_tmax=True):
    # crop recordings to tmin – tmax. can be incomplete if recording
    # has lower duration than tmax
    # by default mne fails if tmax is bigger than duration
    tmax = min((raw.n_times - 1) / raw.info['sfreq'], tmax)
    raw.crop(tmin=tmin, tmax=tmax, include_tmax=include_tmax)


tmin = 1 * 60
tmax = 6 * 60
sfreq = 100

preprocessors = [
    Preprocessor(custom_crop, tmin=tmin, tmax=tmax, include_tmax=False,
                 apply_on_array=False),
    Preprocessor('set_eeg_reference', ref_channels='average', ch_type='eeg'),
    Preprocessor(custom_rename_channels, mapping=ch_mapping,
                 apply_on_array=False),
    Preprocessor('pick_channels', ch_names=short_ch_names, ordered=True),
    Preprocessor(multiply, factor=1e6, apply_on_array=True),
    Preprocessor(np.clip, a_min=-800, a_max=800, apply_on_array=True),
    Preprocessor('resample', sfreq=sfreq),
]


###############################################################################
# Next, we apply the preprocessors on the selected recordings in parallel.
# We additionally use the serialization functionality of
# :func:`braindecode.preprocessing.preprocess` to limit memory usage during
# preprocessing (as each file must be loaded into memory for some of the
# preprocessing steps to work). This also makes it possible to use the lazy
# loading capabilities of :class:`braindecode.datasets.BaseConcatDataset`, as
# the preprocessed data is automatically reloaded with ``preload=False``.
#
# .. note::
#    Here we use ``n_jobs=2`` as the machines the documentation is build on
#    only have two cores. This number should be modified based on the machine
#    that is available for preprocessing.

OUT_PATH = tempfile.mkdtemp()  # please insert actual output directory here
tuh_preproc = preprocess(
    concat_ds=tuh,
    preprocessors=preprocessors,
    n_jobs=N_JOBS,
    save_dir=OUT_PATH
)

###############################################################################
# We can finally generate compute windows. The resulting dataset is now ready
# to be used for model training.

window_size_samples = 1000
window_stride_samples = 1000
# generate compute windows here and store them to disk
tuh_windows = create_fixed_length_windows(
    tuh_preproc,
    window_size_samples=window_size_samples,
    window_stride_samples=window_stride_samples,
    drop_last_window=False,
    n_jobs=N_JOBS,
)

for x, y, ind in tuh_windows:
    break
