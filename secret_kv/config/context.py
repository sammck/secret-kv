# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Configuration context."""

from tty import CFLAG
from typing import Optional, Dict, Any, TYPE_CHECKING, TextIO

from secret_kv.util import full_name_of_type, full_type
from ..internal_types import Jsonable, JsonableDict

if TYPE_CHECKING:
  from .base import Config

import os
import json
from collections import UserDict
from copy import copy, deepcopy
from string import Template
import importlib
import hashlib

class ConfigDict(UserDict):
  pass

  # _T = TypeVar('_T', bound='ConfigDict')
  # def __deepcopy__(self: _T) -> _T:
  #   pass


class ConfigContext(ConfigDict):
  def __init__(self, globals: Optional[Dict[str, Any]]=None, os_environ: Optional[Dict[str, str]]=None):
    super().__init__()
    if not globals is None:
      globals = deepcopy(globals)
      self.update(globals)
    if os_environ is None:
      # NOTE: not thread safe if anyone is calling setvar
      os_environ = dict(os.environ)
    for k, v in os_environ.items():
      self[f"env:{k}"] = v

  def clone(self) -> 'ConfigContext':
    result = deepcopy(self)
    return result

  def render_template_str(self, template_str: str) -> str:
    t: Template = Template(template_str)
    result: str = t.substitute(self)
    return result

  def render_template_json_data(
        self,
        template_json_data: Jsonable,
        *args,
        **kwargs
      ) -> Jsonable:
    template_str = json.dumps(template_json_data)
    json_text: str = self.render_template_str(template_str)
    result: Jsonable = json.loads(json_text)
    return result

  def instantiate_config(self, class_name: str) -> 'Config':
    from .base import Config
    class_parts = class_name.rsplit('.', 1)
    module_name: str
    if len(class_parts) > 1:
      module_name, class_tail = class_parts
    else:
      from .. import config as config_module
      module_name = config_module.__name__
      class_tail = class_name
    module = importlib.import_module(module_name)
    klass = getattr(module, class_tail)
    if not issubclass(klass, Config):
      raise RuntimeError(f"Config: {full_name_of_type(klass)} is not a subclass of {full_name_of_type(Config)}")
    cfg  = klass()
    return cfg

  def hash_pathname(self, pathname: str) -> str:
    result = hashlib.sha1(os.path.abspath(os.path.expanduser(pathname)).encode("utf-8")).hexdigest()
    return result

  def set_config_file(self, config_file: str):
    config_file = os.path.abspath(os.path.expanduser(config_file))
    config_dir = os.path.dirname(config_file)
    config_file_hash = self.hash_pathname(config_file)
    config_dir_hash = self.hash_pathname(config_dir)
    self['config_file'] = config_file
    self['config_dir'] = config_dir
    self['config_file_hash'] = config_file_hash
    self['config_dir_hash'] = config_dir_hash

  def loads(self, s: str, config_file: Optional[str]=None) -> 'Config':
    data: Jsonable = json.loads(s)
    if config_file is None:
      ctx = self
    else:
      ctx = self.clone()
      ctx.set_config_file(config_file)

    if not isinstance(data, dict):
      raise ValueError(f"ConfigContext: expected json dict, got {full_type(data)}")
    if 'version' in data:
      version_s = data['version']
      if not isinstance(version_s, str):
        raise ValueError(f"ConfigContext: expected str version, got {full_type(version_s)}")
      version = tuple(int(x) for x in version_s.split('.'))
      from .. import __version__ as my_version_s
      my_version = tuple(int(x) for x in my_version_s.split('.'))
      if version > my_version:
        raise RuntimeError(f"ConfigContext: configuration version {version_s} is newer than ConfigContext version {my_version_s}")
    cfg_class_name = data['cfg_class']
    if not isinstance(cfg_class_name, str):
      raise ValueError(f"ConfigContext: expected str cfg_class, got {full_type(cfg_class_name)}")
    cfg_data: Jsonable = data.get('data', {})
    if not isinstance(cfg_data, (dict, str)):
      raise ValueError(f"ConfigContext: expected dict or str data, got {full_type(cfg_data)}")
    cfg = self.instantiate_config(cfg_class_name)
    if isinstance(cfg_data, str):
      cfg.loads(ctx, cfg_data)
    else:
      cfg.load_json_data(ctx, cfg_data)
    return cfg

  def load_json_data(self, data: JsonableDict, config_file: Optional[str]=None) -> 'Config':
    s = json.dumps(data)
    cfg = self.loads(s, config_file=config_file)
    return cfg

  def load_stream(self, stream: TextIO, config_file: Optional[str]=None) -> 'Config':
    s = stream.read()
    cfg = self.loads(s, config_file=config_file)
    return cfg

  def load_file(self, config_file: str):
    with open(config_file) as f:
      cfg = self.load_stream(f, config_file=config_file)
    return cfg
