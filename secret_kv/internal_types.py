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
    MutableMapping,
    Sequence,
  )

if TYPE_CHECKING:
  from .value import XJsonSerializable
else:
  XJsonSerializable = object

JsonableTypes = ( str, int, float, bool, dict, list )
# A tuple of types to use for isinstance checking of JSON-serializable types. Excludes None. Useful for isinstance.

if TYPE_CHECKING:
  Jsonable = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
  """A Type hint for a simple JSON-serializable value; i.e., str, int, float, bool, None, Dict[str, Jsonable], List[Jsonable]"""
else:
  Jsonable = Union[str, int, float, bool, None, Dict[str, 'Jsonable'], List['Jsonable']]
  """A Type hint for a simple JSON-serializable value; i.e., str, int, float, bool, None, Dict[str, Jsonable], List[Jsonable]"""

JsonableDict = Dict[str, Jsonable]
"""A type hint for a simple JSON-serializable dict; i.e., Dict[str, Jsonable]"""

XJsonableTypes = ( str, int, float, bool, bytes, bytearray, Mapping, Iterable, XJsonSerializable )
# A tuple of types to use for isinstance checking of JSON-serializable types. Excludes None. Useful for isinstance.

if TYPE_CHECKING:
  XJsonable = Union[str, int, float, bool, bytes, bytearray, XJsonSerializable, None, Mapping[str, Any], Iterable[Any]]
  """A Type hint for an extended JSON-serializable value; i.e., str, int, float, bool, bytes, bytearray, XJsonSerializable, None, Mapping[str, XJsonable], Iterable[XJsonable]"""
else:
  XJsonable = Union[str, int, float, bool, bytes, bytearray, XJsonSerializable, None, Mapping[str, 'XJsonable'], Iterable['XJsonable']]
  """A Type hint for an extended JSON-serializable value; i.e., str, int, float, bool, bytes, bytearray,XJsonSerializable, None, Dict[str, Jsonable], List[Jsonable]"""

XJsonableDict = Mapping[str, XJsonable]
"""A type hint for an extended JSON-serializable dict; i.e., Mapping[str, XJsonable]"""

import sqlite3

SqlConnection = sqlite3.Connection
"""A type hint for a connection to an SQL database (possibly sqlite3 or sqlcipher3)"""

from .sentinel import Sentinel, Nothing, NothingType
