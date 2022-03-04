# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Package secret_kv provides encrypted rich key/value storage for an application or project
"""

import importlib.metadata as _metadata

__version__ =  "0.4.3"

# __version = _metadata.version(__package__.replace('_','-')) #  e.g., '0.1.0'

__all__ = [ __version__ ]
