# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Package secret_kv provides encrypted rich key/value storage for an application or project
"""

import importlib.metadata
__version__ =  importlib.metadata.version(__package__.replace('_','-')) #  '0.1.0'

from .internal_types import Jsonable, JsonableDict
from .store import KvStore
from .sql_store import SqlKvStore
from .value import KvType, KvTypeBinary, KvTypeJsonable, KvValue
from .exceptions import KvError, KvNoEnumerationError, KvReadOnlyError
from .config import Config, ConfigContext
