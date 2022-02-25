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
    Mapping,
    MutableMapping
  )

NoneType = type(None)
"""A type-hint for the value None"""

if TYPE_CHECKING:
  Jsonable = Union[str, int, float, bool, NoneType, Mapping[str, Any], List[Any]]
  """A Type hint for a simple JSON-serializable value; i.e., str, int, float, bool, None, Mapping[str, Jsonable], List[Jsonable]"""
  MutableJsonable = Union[str, int, float, bool, NoneType, MutableMapping[str, Any], List[Any]]
  """A Type hint for a mutable simple JSON-serializable value; i.e., str, int, float, bool, None, MutableMapping[str, Jsonable], List[Jsonable]"""
else:
  Jsonable = Union[str, int, float, bool, NoneType, Mapping[str, 'Jsonable'], List['Jsonable']]
  """A Type hint for a simple JSON-serializable value; i.e., str, int, float, bool, None, Mapping[str, Jsonable], List[Jsonable]"""
  MutableJsonable = Union[str, int, float, bool, NoneType, MutableMapping[str, 'MutableJsonable'], List['MutableJsonable']]
  """A Type hint for a mutable simple JSON-serializable value; i.e., str, int, float, bool, None, MutableMapping[str, MutableJsonable], List[MutableJsonable]"""

JsonableDict = Mapping[str, Jsonable]
"""A type hint for a simple JSON-serializable dict; i.e., Dict[str, Jsonable]"""
MutableJsonableDict = Mapping[str, MutableJsonable]
"""A type hint for a mutable simple JSON-serializable dict; i.e., Dict[str, Jsonable]"""

import sqlite3

SqlConnection = sqlite3.Connection
"""A type hint for a connection to an SQL database (possibly sqlite3 or sqlcipher3)"""
