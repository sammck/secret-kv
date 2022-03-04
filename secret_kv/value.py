# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Definition of KvValue, an abstraction for an immutable value that has a type and is is serializable to JSON.

   Typical usage example:

   a = KvValue("foo")
   b = KvValue(7)
   c = KvValue(dict(x=5, y=7))
   d = KvValue([ 4, 5, 6])
   e = KvValue(None)
   f = KvValue(3.14159)
   g = KvValue(b'binary data')  # encoded as a base64 string

   a_data = a.data
   a_json_data = a.json_data
   a_json_text = a.json_text
"""

from typing import Optional, Union, Tuple, NewType, Mapping, Iterable, TypeVar, Type, Any
from .internal_types import JsonableDict, Jsonable, JsonableTypes, XJsonable, XJsonableDict

import json
from base64 import b64encode, b64decode
from copy import deepcopy
import re
import importlib

from .util import clone_json_data, full_type, full_name_of_type

_xjson_type_key_pattern = re.compile(r'^@+xjson_type$')

class XJsonSerializable:
  _Cls = TypeVar("_Cls", bound='XJsonSerializable')

  def __xjson__get_type_name(self) -> str:
    return full_type(self)

  def  __xjson_encode__(self) -> Jsonable:
    raise NotImplementedError()

  def  __xjson_decode__(self, json_data: Jsonable) -> None:
    raise NotImplementedError()

  @classmethod
  def  __xjson_create_and_decode__(cls: Type[_Cls], json_data: Jsonable) -> XJsonable:
    from copy import copy
    obj: XJsonSerializable = cls.__new__(cls)
    obj.__xjson_decode__(json_data)
    return obj

def xjson_encode(data: XJsonable) -> Jsonable:
  result: Jsonable
  if data is None or isinstance(data, (int, float, bool, str)):
    result = data
  elif isinstance(data, (bytes, bytearray)):
    b64 = b64encode(data).decode('utf-8')
    result = { "@xjson_type": "binary", "data": b64 }
  elif isinstance(data, XJsonSerializable):
    rtype = data.__xjson__get_type_name()
    rdata = data.__xjson_encode__()
    result = { "@xjson_type": rtype, "data": rdata }
  elif isinstance(data, Mapping):
    result = {}
    for k, v in data.items():
      if not isinstance(k, str):
        raise ValueError(f"xjson: expected str as dict property key, got {full_type(k)}")
      if _xjson_type_key_pattern.match(k):
        # to avoid key collision, we add an extra '@' to the front of any property key that begins with "@xjson_type", "@@xjson_type", ...
        # These will be restored on decode.
        k = '@' + k
      rv = xjson_encode(v)
      result[k] = v
  elif isinstance(data, Iterable):
    result = []
    for v in data:
      rv = xjson_encode(v)
      result.append(rv)
  else:
    raise ValueError(f"xjson: Cannot encode type {full_type(data)}")
  return result

def xjson_encode_simple_jsonable(data: Jsonable) -> Jsonable:
  result: Jsonable
  if data is None or isinstance(data, (int, float, bool, str)):
    result = data
  elif not isinstance(data, XJsonSerializable) and isinstance(data, Mapping):
    result = {}
    for k, v in data.items():
      if not isinstance(k, str):
        raise ValueError(f"xjson: expected str as dict property key, got {full_type(k)}")
      if _xjson_type_key_pattern.match(k):
        # to avoid key collision, we add an extra '@' to the front of any property key that begins with "@xjson_type", "@@xjson_type", ...
        # These will be restored on decode.
        k = '@' + k
      rv = xjson_encode_simple_jsonable(v)
      result[k] = v
  elif not isinstance(data, XJsonSerializable) and isinstance(data, Iterable):
    result = []
    for v in data:
      rv = xjson_encode_simple_jsonable(v)
      result.append(rv)
  else:
    raise ValueError(f"xjson: Cannot encode type {full_type(data)} as simple JSON")
  return result

def xjson_decode_extended_value(rtype: str, rdata: Jsonable) -> XJsonable:
  if not isinstance(rtype, str):
    raise ValueError(f"xjson: expected str as extended value type, got {full_type(rtype)}")
  if rtype == 'binary':
    if not isinstance(rdata, str):
      raise ValueError(f"xjson: Expected str for base-64 encoded binary data, got {full_type(rdata)}")
    try:
      result = b64decode(rdata)
    except Exception as ex:
      raise ValueError(f"xjson: Invalid base-64 binary encoding: {ex}") from ex
  else:
    cls_name = rtype
    cls_name_parts = cls_name.rsplit('.', 1)
    module_name: str
    if len(cls_name_parts) > 1:
      module_name, class_tail = cls_name_parts
    else:
      from . import value as value_module
      module_name = value_module.__name__
      class_tail = cls_name
    try:
      module = importlib.import_module(module_name)
      klass = getattr(module, class_tail)
    except Exception as ex:
      raise ValueError(f"xjson: cannot instantiate extended type '{module_name}.{class_tail}': {ex}")
    if not issubclass(klass, XJsonSerializable):
      raise TypeError(f"xjson: extended type {full_name_of_type(klass)} cannot be decoded--no implementation of XJsonSerializable")
    assert issubclass(klass, XJsonSerializable)   # for mypy...?
    result = klass.__xjson_create_and_decode__(rdata)
  return result
    
def xjson_decode(data: Jsonable) -> XJsonable:
  result: XJsonable
  if data is None or isinstance(data, (int, float, bool, str)):
    result = data
  elif isinstance(data, Mapping):
    if '@xjson_type' in data:
      rtype = data['@xjson_type']
      if not isinstance(rtype, str):
        raise ValueError(f"xjson: expected str value of '@xjson_type' property got {full_type(rtype)}")
      if not 'data' in data:
        raise ValueError(f"xjson: Missing 'data' property in extended value descriptor")
      rdata = data['data']
      if len(data) != 2:
        raise ValueError(f"xjson: extraneous properties in extended value descriptor")
      result = xjson_decode_extended_value(rtype, rdata)
    else:
      rdict = {}
      for k, v in data.items():
        if not isinstance(k, str):
          raise ValueError(f"xjson: expected str as dict property key, got {full_type(k)}")
        if _xjson_type_key_pattern.match(k):
          # to avoid key collision, we previously added an extra '@' to the front of any property key that begins with "@xjson_type", "@@xjson_type", ...
          # These will be restored here.
          k = k[1:]
        rv = xjson_decode(v)
        rdict[k] = rv
      result = rdict
  elif isinstance(data, Iterable):
    result = []
    for v in data:
      rv = xjson_decode(v)
      result.append(rv)
  else:
    raise ValueError(f"xjson: Cannot decode type {full_type(data)}")
  return result

def xjson_decode_simple_jsonable(data: Jsonable) -> Jsonable:
  result: Jsonable
  if data is None or isinstance(data, (int, float, bool, str)):
    result = data
  elif not isinstance(data, XJsonSerializable) and isinstance(data, Mapping):
    if '@xjson_type' in data:
      raise ValueError("xjson: Cannot decode simple JSON-able; dict includes '@xjson_type' property")
    else:
      rdict = {}
      for k, v in data.items():
        if not isinstance(k, str):
          raise ValueError(f"xjson: expected str as dict property key, got {full_type(k)}")
        if _xjson_type_key_pattern.match(k):
          # to avoid key collision, we previously added an extra '@' to the front of any property key that begins with "@xjson_type", "@@xjson_type", ...
          # These will be restored here.
          k = k[1:]
        rv = xjson_decode_simple_jsonable(v)
        rdict[k] = rv
      result = rdict
  elif not isinstance(data, XJsonSerializable) and isinstance(data, Iterable):
    result = []
    for v in data:
      rv = xjson_decode_simple_jsonable(v)
      result.append(rv)
  else:
    raise ValueError(f"xjson: Cannot decode type {full_type(data)}")
  return result

def clone_simple_jsonable(data: Jsonable) -> Jsonable:
  result: Jsonable
  if data is None or isinstance(data, (int, float, bool, str)):
    result = data
  elif not isinstance(data, XJsonSerializable) and isinstance(data, Mapping):
    rdict = {}
    for k, v in data.items():
      if not isinstance(k, str):
        raise ValueError(f"xjson: expected str as dict property key, got {full_type(k)}")
      rv = clone_simple_jsonable(v)
      rdict[k] = rv
    result = rdict
  elif not isinstance(data, XJsonSerializable) and isinstance(data, Iterable):
    result = []
    for v in data:
      rv = clone_simple_jsonable(v)
      result.append(rv)
  else:
    raise ValueError(f"clone_simple_jsonable: Not a simple JSON-able type: {full_type(data)}")
  return result

def validate_simple_jsonable(data: Any) -> Jsonable:
  if data is None or isinstance(data, (int, float, bool, str)):
    pass
  elif isinstance(data, dict):
    for k, v in data.items():
      if not isinstance(k, str):
        raise ValueError(f"Not simple JSON-able: property key of non-str type: {full_type(k)}")
      validate_simple_jsonable(v)
  elif isinstance(data, list):
    for v in data:
      validate_simple_jsonable(v)
  else:
    raise ValueError(f"Not a simple JSON-able type: {full_type(data)}")
  return data

class KvValue(XJsonSerializable):

  """An immutable representation of a XJsonable value that is serializable to and from JSON.
     Allows optional metadata to be attached.
  """

  _json_data: Jsonable
  """The simple JSON-serializable value that represents the KvValue. immutable"""
  _json_text: str
  """The serialized JSON string that represents the value. immutable"""
  _xjson_data: XJsonable
  """The extended JSON-serializable value that represents the native instantiated KvValue"""

  def __init__(self, data: XJsonable):
    """Create an immutable representation of a value that is serializable to and from JSON.
    """
    self._xjson_data = deepcopy(data)
    self._json_data = xjson_encode(self._xjson_data)
    self._json_text = json.dumps(self._json_data, sort_keys=True, separators=(',',':'))
  
  @property
  def json_data(self) -> Jsonable:
    """The JSON-serializable representation of the value. Must not be modified."""
    return self._json_data

  @property
  def data(self) -> XJsonable:
    """The extended JSON-serializable value. Must not be modified."""
    return self._xjson_data

  @property
  def json_text(self) -> str:
    """The serialized JSON text representation of the value"""
    return self._json_text

  def as_simple_jsonable(self) -> Jsonable:
    return xjson_decode_simple_jsonable(self.json_data)

  def __str__(self) -> str:
    jt = self.json_text
    if len(jt) > 1000:
      result = f"<KvValue data={jt[:1000]}...>"
    else:
      result = f"<KvValue data={jt}>"
    return result

  def as_sortable_value(self) -> Tuple[str, str]:
    """Returns an opaque value that can be hashed or compared to similar values
    for sorting and equality-testing purposes.

    NOTE: this does not provide true ordinal sort order for scalar integers and floats. It
          simply sorts by serialized json string.
    Returns:
        Tuple[str, str]: An opaque value that represents this KvValue in a way that can be compared/sorted
    """
    # TODO: include metadata
    return self.json_text, ""

  def __eq__(self, other: object) -> bool:
    return isinstance(other, KvValue) and self.as_sortable_value() == other.as_sortable_value()

  def __ne__(self, other: object) -> bool:
    return not isinstance(other, KvValue) or self.as_sortable_value() != other.as_sortable_value()

  def __gt__(self, other: object) -> bool:
    if not isinstance(other, KvValue):
      raise TypeError(f"'>' not supported between instances of KvValue and {full_type(other)}")
    return self.as_sortable_value() > other.as_sortable_value()

  def __lt__(self, other: object) -> bool:
    if not isinstance(other, KvValue):
      raise TypeError(f"'<' not supported between instances of KvValue and {full_type(other)}")
    return self.as_sortable_value() < other.as_sortable_value()

  def __ge__(self, other: object) -> bool:
    if not isinstance(other, KvValue):
      raise TypeError(f"'>=' not supported between instances of KvValue and {full_type(other)}")
    return self.as_sortable_value() >= other.as_sortable_value()

  def __le__(self, other: object) -> bool:
    if not isinstance(other, KvValue):
      raise TypeError(f"'<=' not supported between instances of KvValue and {full_type(other)}")
    return self.as_sortable_value() <= other.as_sortable_value()

  def __hash__(self) -> int:
    return hash(self.as_sortable_value())

  def __copy__(self) -> 'KvValue':
    # we are immutable:
    return self

  def __deepcopy__(self, memo: Any) -> 'KvValue':
    # we are immutable:
    return self

  def clone(self) -> 'KvValue':
    # we are immutable:
    return self

  def __xjson__get_type_name(self) -> str:
    return "KvValue"

  def  __xjson_encode__(self) -> Jsonable:
    return deepcopy(self._json_data)

  def  __xjson_decode__(self, json_data: Jsonable) -> None:
    xdata = xjson_decode(json_data)
    self.__init__(xdata)  # type: ignore[misc]

