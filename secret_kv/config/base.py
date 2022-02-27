# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Configuration support.

"""

from typing import Optional, Dict, TextIO, Any, Mapping, Type, TypeVar, Union, overload
from ..internal_types import Jsonable, JsonableDict, Nothing, NothingType


import os
import json
import hashlib
import importlib

from ..util import full_name_of_type
from .context import ConfigContext

_T = TypeVar('_T')

class Config:
  _template_json_data: Optional[JsonableDict] = None
  _json_data: Optional[JsonableDict] = None
  _context: Optional[ConfigContext] = None

  def __init__(self):
    pass

  @classmethod  
  def hash_pathname(cls, pathname: str) -> str:
    result = hashlib.sha1(os.path.abspath(os.path.expanduser(pathname)).encode("utf-8")).hexdigest()
    return result

  @classmethod
  def instantiate_config(cls, class_name: str) -> 'Config':
    class_parts = class_name.rsplit('.', 1)
    if len(class_parts) > 1:
      module_name, class_tail = class_parts
    else:
      import secret_kv.config as config_module
      module_name = config_module.__name__
      class_tail = class_name
    module = importlib.import_module(module_name)
    klass = getattr(module, class_tail)
    if not issubclass(klass, Config):
      raise RuntimeError(f"Config: {full_name_of_type(klass)} is not a subclass of {full_name_of_type(Config)}")
    cfg  = klass()
    return cfg

  def bake(self):
    pass

  def render(self):
    self._json_data = self._context.render_template_json_data(self._template_json_data)

  def render_and_bake(self, context: ConfigContext):
    self._context = context.clone()
    self.render()
    self.bake()

  def loads(
        self,
        ctx: ConfigContext,
        config_text: str
      ):
    self._template_json_data = json.loads(config_text)
    self.render_and_bake(ctx)

  def load_json_data(
        self,
        ctx: ConfigContext,
        json_data: JsonableDict
      ):
    config_text = json.dumps(json_data)
    self.loads(ctx, config_text)

  _no_default = object()

  @overload
  def get_cfg_property(self, key: str, default: _T) -> Union[Jsonable, _T]: pass

  @overload
  def get_cfg_property(self, key: str) -> Jsonable: pass

  def get_cfg_property(self, key: str, default = _no_default):
    if not isinstance(self._json_data, dict):
      raise TypeError(f"Config: Expected config data {key} to be dict, got {type(self._json_data)}")
    if default is self._no_default:
      result = self._json_data[key]
    else:
      result = self._json_data.get(key, default)

  @overload
  def get_cfg_property_str(self, key: str, default: _T) -> Union[str, _T]: pass

  @overload
  def get_cfg_property_str(self, key: str) -> str: pass

  def get_cfg_property_str(self, key: str, default: Any=_no_default):
    result = self.get_cfg_property(key, default)
    if not isinstance(result, str):
      raise TypeError(f"Config: Expected property {key} to be str, got {type(result)}")
    return result

  @overload
  def get_cfg_property_int(self, key: str, default: _T) -> Union[int, _T]: pass

  @overload
  def get_cfg_property_int(self, key: str) -> int: pass

  def get_cfg_property_int(self, key: str, default: Any=_no_default):
    result = self.get_cfg_property(key, default)
    if not isinstance(result, int):
      if isinstance(result, str):
        try:
          result = int(result)
        except ValueError:
          pass
    if not isinstance(result, int):
      raise TypeError(f"Config: Expected property {key} to be int, got {type(result)}")
    return result

  @overload
  def get_cfg_property_dict(self, key: str, default: _T) -> Union[JsonableDict, _T]: pass

  @overload
  def get_cfg_property_dict(self, key: str) -> JsonableDict: pass

  def get_cfg_property_dict(self, key: str, default: Any=_no_default):
    result = self.get_cfg_property(key, default)
    if not isinstance(result, dict):
      raise TypeError(f"Config: Expected property {key} to be dict, got {type(result)}")
    return result
