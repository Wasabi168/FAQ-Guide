import os
import sys

# This is currently a hack till I figure out how to do it properly.
chrdll4_file_dir = os.path.dirname(__file__)
sys.path.append(os.path.abspath(chrdll4_file_dir))

from . import chr_cmd_id
from . import chr_def
from . import chr_dll
from . import chr_utils
from . import chr_connection


def get_chrdll4_version():
    return "0.6.0"
