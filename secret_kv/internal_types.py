#
# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Type hints used internally by this package"""

from typing import (
    Dict,
    Union,
    Any,
    List,
    Optional,
    Callable,
    Awaitable,
    NewType,
    AsyncIterable,
    AsyncGenerator,
    AsyncContextManager,
    AsyncIterable,
    Tuple,
    Type,
    Set,
    TypeVar,
    TYPE_CHECKING,
    FrozenSet,
    Coroutine,
    Generator,
    Iterable,
    Iterable,
  )

NoneType = type(None)
"""A type-hint for the value None"""

if TYPE_CHECKING:
  JsonData = Union[str, int, float, bool, NoneType, Dict[str, Any], List[Any]]
  """A Type hint for a simple JSON-serializable value; i.e., str, int, float, bool, None, Dict[str, JsonData], List[JsonData]"""
else:
  JsonData = Union[str, int, float, bool, NoneType, Dict[str, 'JsonData'], List['JsonData']]
  """A Type hint for a simple JSON-serializable value; i.e., str, int, float, bool, None, Dict[str, JsonData], List[JsonData]"""

JsonDict = Dict[str, JsonData]
"""A type hint for a simple JSON-serializable dict; i.e., Dict[str, JsonData]"""

import sqlite3

SqlConnection = sqlite3.Connection
"""A type hint for a connection to an SQL database (possibly sqlite3 or sqlcipher3)"""
