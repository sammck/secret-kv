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
   g = KvValue(b'binary data', kv_type=KvTypeBinary)  # encoded as a base64 string

   a_kv_type: KvType = a.kv_type
   a_json_data = a.json_data
   a_json_text = a.json_text
"""

from typing import Optional, Union, Tuple, NewType
from .internal_types import JsonableDict, Jsonable, JsonableTypes

import json
from base64 import b64encode, b64decode
from copy import deepcopy

from .util import clone_json_data, full_type

KvType = NewType('KvType', str)
"""The string name for a native type that is represented by a KvValue. Currently either KvTypeJsonable or KvTypeBinary"""

KvTypeBinary: KvType = KvType('binary')
"""Used to indicate that a KvValue represents a JSON serialization (using base-64) of a 'bytes' value"""

KvTypeJsonable: KvType = KvType('json')
"""Used to indicate jthat a KvValue represents a simple JSON-serializable value"""

KvValueCoercible = Union['KvValue', Jsonable, bytes, bytearray]
"""A type-hint that describes either a KvValue, or a native value that can be implicitly encoded as a KvValue"""

class KvValue:
  """An immutable representation of a value and its type that is serializable to and from JSON.

  Currently, the following value types are supported:

  KvTypeJsonable:   Any of the basic types that is directly serializable with json.dumps();
                    e.g., None, int, float, str, bool, List[Jsonable], or Dict[str, Jsonable]

  KvTypeBinary:     A bytes/bytearray value
  """

  _kv_type: KvType
  """The type of data that is encoded into json_data. Currently either KvTypeBinary or KvTypeJsonable"""
  _json_data: Jsonable
  """The JSON-serializable value that represents the KvValue"""
  _json_text: str
  """The serialized JSON string that represents the value"""

  def __init__(self, data: KvValueCoercible, kv_type: Optional[KvType]=None):
    """Create an immutable representation of a value that is serializable to and from JSON.

    Args:
        data KvValueCoercible:
                            The value to represent. Possibilities:
                              A KvValue:  Makes a duplicate of another KvValue. kv_type is ignored.
                                    This is provided for convenience but is never necessary, since
                                    a KvValue is immutable and can be shared.
                              A Jsonable type (the basic types serializable to JSON): makes a deep
                                    copy of the value.
                              bytes or bytearray: Encodes the value as base-64.
        kv_type (Optional[KvType], optional):
                            The KvType to be associated with the data, or
                              None to infer a type from the data. Currently only KvTypeJsonable and
                              KvTypeBinary are supported. Defaults to None.
    """
    if isinstance(data, KvValue):
      kv_type = data._kv_type
      # because KvValue is immutable, we can share the json_data
      self._json_data = data._json_data
      self._json_text = data._json_text
    elif isinstance(data, (bytes, bytearray)):
      self._json_data = b64encode(data).decode('utf-8')
      self._json_text = json.dumps(self._json_data, sort_keys=True)
      if kv_type is None:
        kv_type = KvTypeBinary
    else:
      # Here, we effectively clone the provided json data, and verify it is Jsonable, by running it through
      # json.dumps and back again.
      self._json_text = json.dumps(data)
      self._json_data = json.loads(self._json_text)
      if kv_type is None:
        kv_type = KvTypeJsonable
      if kv_type == KvTypeBinary:
        if not isinstance(self._json_data, str):
          raise ValueError(f"Expected base64 data as str, got {full_type(self._json_data)}")
        try:
          b64decode(self._json_data, validate=True)
        except Exception as ex:
          raise ValueError(f"Invalid base64-encoded KvValue: {ex}") from ex
    if not kv_type in [ KvTypeBinary, KvTypeJsonable ]:
      raise ValueError(f"Invalid KvType: '{str(kv_type)}'")
    self._kv_type = kv_type
  
  @property
  def json_data(self) -> Jsonable:
    """The JSON-serializable representation of the value. Must not be modified."""
    return self._json_data

  @property
  def kv_type(self) -> KvType:
    """The type of data represented by the serialized form.  Currently either KvTypeJsonable or KvTypeBinary"""
    return self._kv_type

  def as_typed_jsonable(self) -> JsonableDict:
    """Creates a new, modifiable JsonableDict that contains 'kv_type' and 'data' as properties.

    Returns:
        JsonableDict: a new, modifiable JsonableDict that contains 'kv_type' and 'data' as properties.
    """
    result: JsonableDict = dict(kv_type=str(self.kv_type), data=deepcopy(self.json_data))
    return result

  @classmethod
  def from_typed_jsonable(cls, typed_data: JsonableDict) -> 'KvValue':
    if not isinstance(typed_data, dict):
      raise ValueError(f"typed-JSON value must be a dict, got {full_type(typed_data)}")
    for k in typed_data.keys():
      if not k in [ 'kv_type', 'data' ]:
        raise ValueError(f"typed-JSON value has unrecognized '{k}' property")
    if not 'kv_type' in typed_data:
      raise ValueError(f"typed-JSON value must have a 'kv_type' property")
    kv_type_s = typed_data['kv_type']
    if not isinstance(kv_type_s, str):
      raise ValueError(f"typed-JSON 'kv_type' property must be a string, go {full_type(kv_type_s)}")
    if not kv_type_s in [ 'json', 'binary' ]:
      raise ValueError(f"typed-JSON has invalid 'kv_type': '{kv_type_s}'")
    kv_type = KvType(kv_type_s)
    if not 'data' in typed_data:
      raise ValueError(f"typed-JSON value must have a 'data' property")
    data: Jsonable = typed_data['data']
    result = KvValue(data, kv_type)
    return result

  @classmethod
  def from_optionally_typed_jsonable(cls, data: Union[Jsonable, bytes, bytearray]) -> 'KvValue':
    if isinstance(data, dict) and len(data) == 2 and 'kv_type' in data and 'data' in data:
      result = cls.from_typed_jsonable(data)
    else:
      result = KvValue(data)
    return result

  def __str__(self) -> str:
    jt = self.json_text
    if len(jt) > 1000:
      result = f"<KvValue type={self.kv_type} data={jt[:1000]}...>"
    else:
      result = f"<KvValue type={self.kv_type} data={jt}>"
    return result

  def get_decoded_value(self) -> Union[Jsonable, bytes]:
    """Gets the native nonserializable form of the value, as a value that must not be modified

    Returns:
        Union[Jsonable, bytes]: The native representation of the value. The caller must not modify this value.
    """
    result: Union[Jsonable, bytes]
    if self.kv_type == KvTypeBinary:
      if not isinstance(self.json_data, str):
        raise TypeError(f"KvValue: KvTypeBinary should be encoded as str, but found {full_type(self.json_data)}")
      result = b64decode(self.json_data)
    elif self.kv_type == KvTypeJsonable:
      result = self.json_data
    else:
      raise TypeError(f"KvValue: cannot decode unknown KvType '{self.kv_type}'")
    return result

  def decode(self) -> Union[Jsonable, bytes]:
    """Gets the native nonserializable form of the value, as a modifiable value

    Returns:
        Union[Jsonable, bytes]: The native representation of the value. The returned value
                is owned by the caller to do with is they please.
    """
    if self.kv_type == KvTypeBinary:
      if not isinstance(self.json_data, str):
        raise TypeError(f"KvValue: KvTypeBinary should be encoded as str, but found {full_type(self.json_data)}")
      result = b64decode(self.json_data)
    elif self.kv_type == KvTypeJsonable:
      # make a private copy
      result = json.loads(self.json_text) 
    else:
      raise TypeError(f"KvValue: cannot decode unknown KvType '{self.kv_type}'")
    return result

  @property
  def json_text(self) -> str:
    """The serialized JSON text representation of the value"""
    return self._json_text

  def as_sortable_value(self) -> Tuple[KvType, str]:
    """Returns an opaque tuple that can be hashed or compared to similar tuples
    for sorting and equality-testing purposes.

    NOTE: this does not provide true ordinal sort order for scalar integers and floats. It
          simply sorts by serialized json string.
    Returns:
        Tuple[KvType, str]: An opaque tuple that represents this KvValue in a way that can be compared/sorted
    """
    return self.kv_type, self.json_text

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

KvValueCoercibleTypes = ( KvValue, ) + JsonableTypes
"""A Tuple containing the basic types that can be coerced to a KvValue. Excludes None. Useful for isinstance"""
