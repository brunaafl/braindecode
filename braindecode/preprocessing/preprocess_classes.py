"""Preprocessor objects based on mne methods.
"""

# Author: Bruna Lopes <brunajaflopes@gmail.com>
#
# License: BSD-3

import mne.io
from braindecode.util import _update_moabb_docstring
from braindecode.preprocessing import Preprocessor


class Resample(Preprocessor):
    doc = """ See mne.io.Raw.resample
    """
    try:
        base_class = mne.io.Raw.resample
        __doc__ = _update_moabb_docstring(base_class, doc)
    except ModuleNotFoundError:
        pass

    def __init__(self, **kwargs):
        # Ignore "fn" parameter -> the only preprocessing that is going to
        # be used here is mne.Epochs's resample
        # Removing this string parameter, because it's going to execute
        # directly the said preprocess

        fn = 'resample'
        self.fn = fn
        self.kwargs = kwargs

        super().__init__(fn, **kwargs)


class DropChannels(Preprocessor):
    doc = """ See mne.io.Raw.drop_channels
    """
    try:
        base_class = mne.io.Raw.drop_channels
        __doc__ = _update_moabb_docstring(base_class, doc)
    except ModuleNotFoundError:
        pass

    def __init__(self, **kwargs):
        fn = 'drop_channels'
        self.fn = fn
        self.kwargs = kwargs
        # Init parent
        super().__init__(fn, **kwargs)


class SetEEGReference(Preprocessor):
    doc = """ See mne.io.Raw.set_eeg_reference
    """
    try:
        base_class = mne.io.Raw.set_eeg_reference
        __doc__ = _update_moabb_docstring(base_class, doc)
    except ModuleNotFoundError:
        pass

    def __init__(self, **kwargs):
        fn = 'set_eeg_reference'
        self.fn = fn
        self.kwargs = kwargs

        super().__init__(fn, **kwargs)


class Filter(Preprocessor):
    doc = """ See mne.io.Raw.filter
    """
    try:
        base_class = mne.io.Raw.filter
        __doc__ = _update_moabb_docstring(base_class, doc)
    except ModuleNotFoundError:
        pass

    def __init__(self, **kwargs):
        fn = 'filter'
        self.fn = fn
        self.kwargs = kwargs

        super().__init__(fn, **kwargs)


class Pick(Preprocessor):
    doc = """ See mne.io.Raw.pick
    """
    try:
        base_class = mne.io.Raw.pick
        __doc__ = _update_moabb_docstring(base_class, doc)
    except ModuleNotFoundError:
        pass

    def __init__(self, **kwargs):
        fn = 'pick'
        self.fn = fn
        self.kwargs = kwargs

        super().__init__(fn, **kwargs)


class Crop(Preprocessor):
    doc = """See mne.io.Raw.crop
    """
    try:
        base_class = mne.io.Raw.crop
        __doc__ = _update_moabb_docstring(base_class, doc)
    except ModuleNotFoundError:
        pass

    def __init__(self, **kwargs):
        fn = 'crop'
        self.fn = fn
        self.kwargs = kwargs

        super().__init__(fn, **kwargs)
