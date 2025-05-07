# -*- coding: utf-8 -*-

"""
This module contains the global variables and utility functions for CHRocodile lib.

Copyright Precitec Optronik GmbH, 2022
"""

import os
from ctypes import CDLL
from typing import Tuple


def load_client_dll(dll_path=None) -> Tuple[str, CDLL]:
    """
    Load the chrocodile library from the specified path. If the full path is not specified,
    the library is loaded from the default location.
    :param dll_path: Full path to the client DLL including the library name
    :type dll_path: str
    :return: Path the chrocodile client library was loaded from, handle to the client library
    :rtype: str, CDLL
    """
    chr_dll_path = dll_path
    if chr_dll_path is None:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        chr_dll_path = os.path.join(dir_path, "CHRocodile.dll")
        
    chr_dll = CDLL(os.path.abspath(chr_dll_path))
    return chr_dll_path, chr_dll
