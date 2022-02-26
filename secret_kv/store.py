# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Base class definition for KvStore, an abstract key/value store.

   A KvStore supports string keys, and rich value types including json-serializable data and binary data.
   A mechanism is also provided to attach metadata to a key via named tags, which may themselves
   have rich value types.

   Subclasses of KvStore must override and implement a few get/set methods. Default implementations
   are provided in the base class for most methods, and to provide a MutableMapping interface.
"""

from typing import Iterator, Optional, Union, Tuple, Dict, TypeVar, Type, Generator, Iterable, Mapping, MutableMapping, KeysView, ValuesView, ItemsView, overload
from .internal_types import JsonableDict, Jsonable, JsonableTypes

import json

from .value import KvValue, KvType, KvValueCoercible, KvValueCoercibleTypes
from .exceptions import KvError, KvReadOnlyError, KvNoEnumerationError

class KvStore(MutableMapping[str, KvValue]):
  class KvStoreKeysView(KeysView[str]):
    _kv_store: 'KvStore'

    def __init__(self, kv_store: 'KvStore'):
      self._kv_store = kv_store

    def __len__(self) -> int:
      return len(self._kv_store)

    def __iter__(self) -> Iterator[str]:
      return self._kv_store.iter_keys()

    def __contains__(self, key: object) -> bool:
      return key in self._kv_store

  class KvStoreValuesView(ValuesView[KvValue]):
    _kv_store: 'KvStore'

    def __init__(self, kv_store: 'KvStore'):
      self._kv_store = kv_store

    def __len__(self) -> int:
      return len(self._kv_store)

    def __iter__(self) -> Iterator[KvValue]:
      return self._kv_store.iter_values()

    def __contains__(self, value: object) -> bool:
      return self._kv_store.contains_value(value)
    
  class KvStoreItemsView(ItemsView[str, KvValue]):
    _kv_store: 'KvStore'

    def __init__(self, kv_store: 'KvStore'):
      self._kv_store = kv_store

    def __len__(self) -> int:
      return len(self._kv_store)

    def __iter__(self) -> Iterator[Tuple[str, KvValue]]:
      return self._kv_store.iter_items()

    def __contains__(self, item: object) -> bool:
      return self._kv_store.contains_item(item)

    
  _store_name: Optional[str] = None
  """The name of the store. Typically a pathname or URI. If not set, a unique name for the in-memory object is used."""

  def __init__(self, store_name: Optional[str]=None):
    """Create a Key/value store.

    This is a generic base class that provides docstrings and default implementations of public methods.
    It is not intended to be instantiated without subclassing.

    Args:
        store_name (Optional[str], optional): The name of the store. Typically a pathname or URI. Defaults to None.
    """
    self._store_name = store_name

  @property
  def store_name(self) -> str:
    """The name of the store. Typically a pathname or URI."""
    name = self._store_name
    if name is None:
      name = f"KvStore({id(self)})"
    return name

  def __str__(self) -> str:
    name = self._store_name
    if name is None:
      result = f"<KvStore {id(self)}>"
    else:
      result = f"<KvStore {json.dumps(name)}>"
    return result

  def __repr__(self) -> str:
    name = self._store_name
    if name is None:
      result = f"<KvStore@{id(self)}>"
    else:
      result = f"<KvStore@{id(self)} {json.dumps(name)}>"
    return result

  def get_value_and_tags(self, key: str) -> Tuple[Optional[KvValue], Dict[str, KvValue]]:
    """Get a KvValue and all tags associated with a key, if it exists

    Args:
        key (str): The key for which a KvValue and tags are requested

    Returns:
        Tuple[Optional[KvValue], Dict[str, KvValue]]:
                  A tuple with two values:
                         [0]:  The KvValue associated with the key, or None if the key does not exist.
                         [1]:  A dictionary mapping all tag names assocated with the key to their respective
                               tag KvValue. If the key does not exist, {} is returned.
    """
    return None, {}

  def get_value(self, key: str) -> Optional[KvValue]:
    """Get the KvValue associated with a key, if it exists

    Args:
        key (str): The key for which a KvValue is requested

    Returns:
        Optional[KvValue]: The KvValue associated with the key, or None if the key does not exist.
    """
    return self.get_value_and_tags(key)[0]

  def set_value_and_tags(self, key: str, value: KvValueCoercible, tags: Mapping[str, KvValueCoercible], clear_tags: bool=False):
    """Set the KvValue and tags associated with a key. If the key does not exist it is created.

    Args:
        key (str): The key that is being created or updated.
        value (KvValueCoercible): A KvValue or KvValue-Coercible value to assign to the key
        tags (Mapping[str, KvValueCoercible]): A dict mapping tag names to KvValue-coercible tag values
        clear_tags (bool, optional): If true, any existing tags will be cleared before setting new tags. Defaults to False.

    Raises:
        KvReadOnlyError: The KvStore does not support writing the requested values or keys
    """
    raise KvReadOnlyError(f"{self.store_name}: Cannot set value for key {json.dumps(key)}")

  def set_value(self, key: str, value: KvValueCoercible):
    self.set_value_and_tags(key, value, {}, clear_tags=False)

  def delete_value(self, key: str):
    if not self.has_key(key):
      raise KeyError(f"{self.store_name}: {json.dumps(key)}")
    raise KvReadOnlyError(f"{self.store_name}: Cannot delete key {json.dumps(key)}")

  def keys(self) -> KeysView[str]:
    return self.KvStoreKeysView(self)

  def values(self) -> ValuesView[KvValue]:
    return self.KvStoreValuesView(self)

  def items(self) -> ItemsView[str, KvValue]:
    return self.KvStoreItemsView(self)

  def iter_keys(self) -> Iterator[str]:
    raise KvNoEnumerationError(f"{self.store_name}: Key enumeration is not supported")

  def iter_items(self) -> Iterator[Tuple[str, KvValue]]:
    for key in self.keys():
      value = self.get_value(key)
      assert not value is None
      yield key, value
  
  def iter_values(self) -> Iterator[KvValue]:
    for key in self.keys():
      value = self.get_value(key)
      assert not value is None
      yield value

  def contains_value(self, value: object) -> bool:
    if not value is None and not isinstance(value, KvValueCoercibleTypes):
      return False
    if not isinstance(value, KvValue):
      value = KvValue(value)
    for tvalue in self.values():
      if value == tvalue:
        return True
    return False

  def contains_item(self, item: object) -> bool:
    if not isinstance(item, tuple) or len(item) != 2:
      return False
    key, value = item
    if not isinstance(key, str) or (not value is None and not isinstance(value, KvValueCoercibleTypes)):
      return False
    if not isinstance(value, KvValue):
      value = KvValue(value)
    tvalue = self.get_value(key)
    if tvalue is None:
      return False
    return value == tvalue

  def items_with_tags(self) -> Iterable[Tuple[str, KvValue, Dict[str, KvValue]]]:
    for key in self.keys():
      value, tags = self.get_value_and_tags(key)
      assert not value is None
      yield key, value, tags

  def as_json_obj_no_type(self) -> Dict[str, Jsonable]:
    result: Dict[str, Jsonable] = {}
    for key, value in self.items():
      result[key] = value.json_data
    return result

  def as_json_obj(self, include_tags=True) -> JsonableDict:
    result: JsonableDict = {}
    if include_tags:
      for key, value, tags in self.items_with_tags():
        tag_dict = {}
        for tag_name, tag_value in tags.items():
          tag_dict[tag_name] = dict(kv_type=str(tag_value.kv_type), data=tag_value.json_data)
        result[key] = dict(kv_type=str(value.kv_type), data=value.json_data, tags=tag_dict)
    else:
      for key, value in self.items():
        result[key] = dict(kv_type=str(value.kv_type), data=value.json_data)
    return result

  def clear(self):
    for key in list(self.keys()):
      self.delete_value(key)

  def update(self, *args: Union[Mapping[str, KvValueCoercible], Iterable[Tuple[str, KvValueCoercible]]], **kwargs: KvValueCoercible):
    if len(args) > 0:
      if len(args) > 1:
        raise TypeError(f"update expected at most 1 argument, got {len(args)}")
      seq = args[0]
      if isinstance(seq, Mapping):
        seq = seq.items()
      for k, v in seq:
        self.set_value(k, v)
    for k, v in kwargs.items():
        self.set_value(k, v)

  def get_tags(self, key:str) -> Dict[str, KvValue]:
    value, tags = self.get_value_and_tags(key)
    if value is None:
      raise KeyError(f"{self}: {json.dumps(key)}")
    return tags

  def get_num_tags(self, key:str) -> int:
    return len(self.get_tags(key))

  def get_tag(self, key: str, tag_name: str) -> Optional[KvValue]:
    return self.get_tags(key).get(tag_name, None)

  def set_tags(self, key, tags: Dict[str, KvValueCoercible], clear_tags: bool=False):
    old_tags = self.get_tags(key)
    if clear_tags:
      new_tags = tags
    else:
      new_tags = dict(old_tags)
      for tag_name, tag_value in tags.items():
        if not isinstance(tag_value, KvValue):
          tag_value = KvValue(tag_value)
        new_tags[tag_name] = tag_value
    if old_tags != new_tags:
      raise KvReadOnlyError(f"{self.store_name}: Cannot set tags for key {json.dumps(key)}")

  def set_tag(self, key, tag_name: str, value: KvValueCoercible):
    if not isinstance(value, KvValue):
      value = KvValue(value)
    try:
      self.set_tags(key, { tag_name: value }, clear_tags=False)
    except KvReadOnlyError:
      raise KvReadOnlyError(f"{self.store_name}: Cannot set tag {json.dumps(tag_name)} for key {json.dumps(key)}")

  def delete_tag(self, key, tag_name: str) -> KvValue:
    if not self.has_tag(key, tag_name):
      raise KeyError(f"{self}: {json.dumps(key)}")
    raise KvReadOnlyError(f"{self.store_name}: Cannot delete tag {json.dumps(tag_name)} for key {json.dumps(key)}")

  def clear_tags(self, key: str):
    return self.set_tags(key, {}, clear_tags=True)

  def tag_names(self, key: str) -> Iterable[str]:
    return self.get_tags(key).keys()

  def tag_items(self, key:str) -> Iterable[Tuple[str, KvValue]]:
    return self.get_tags(key).items()
  
  def tag_values(self, key: str) -> Iterable[KvValue]:
    return self.get_tags(key).values()

  def has_tag(self, key: str, tag_name: str) -> bool:
    return not self.get_tag(key, tag_name) is None

  def has_key(self, key: str) -> bool:
    return not self.get_value(key) is None

  def num_keys(self) -> int:
    return sum(1 for _ in self.keys())

  def close(self):
    pass

  def __eq__(self, other: object) -> bool:
    if not isinstance(other, Mapping):
      return False
    items = sorted(self.items())
    other_items = sorted(other.items())
    if len(items) != len(other_items):
      return False
    for i, item in enumerate(items):
      if item != other_items[i]:
        return False
    return True

  def __ne__(self, other: object) -> bool:
    return not (self == other)

  def __setitem__(self, key: str, value: KvValue):
    self.set_value(key, value)

  def __delitem__(self, key: str):
    self.delete_value(key)

  def __getitem__(self, key: str) -> KvValue:
    result = self.get_value(key)
    if result is None:
      raise KeyError(f"{self}: {json.dumps(key)}")
    return result

  def __len__(self) -> int:
    return self.num_keys()

  def __contains__(self, key: object) -> bool:
    if not isinstance(key, str):
      return False
    return self.has_key(key)

  def __iter__(self) -> Iterator[str]:
    return self.iter_keys()
