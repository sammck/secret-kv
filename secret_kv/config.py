# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Configuration support.

"""

from typing import Optional, Dict, TextIO
from .internal_types import JsonableDict

import os
from string import Template
import json
import hashlib
import importlib
import keyring

from .util import full_name_of_type

class KvConfigBase:
  _template_text: Optional[str] = None
  _template_json_data: Optional[JsonableDict] = None
  _json_text: Optional[str] = None
  _json_data: Optional[JsonableDict] = None
  _config_file: Optional[str] = None

  def __init__(self):
    pass

  @classmethod  
  def hash_pathname(cls, pathname: str) -> str:
    result = hashlib.sha1(os.path.abspath(os.path.expanduser(pathname)).encode("utf-8")).hexdigest()
    return result

  @classmethod
  def create_config_obj(cls, class_name: str) -> 'KvConfigBase':
    class_parts = class_name.rsplit('.', 1)
    if len(class_parts) > 1:
      module_name, class_tail = class_parts
    else:
      class_tail = class_name
      module_name = __package__
    module = importlib.import_module(module_name)
    klass = getattr(module, class_tail)
    if not issubclass(klass, KvConfigBase):
      raise RuntimeError(f"KvConfig: {full_name_of_type(klass)} is not a subclass of KvConfigBase")
    cfg = klass()
    return cfg

  def bake(self):
    pass

  def populate_template_env(self, template_env: Dict[str, str]):
    pass

  def loads(
        self,
        config_text: str,
        config_file: Optional[str]=None,
        expand_templates: bool=False,
        template_env: Optional[Dict[str, str]]=None
      ):
    self._template_text = config_text
    if not config_file is None:
      config_file = os.path.abspath(os.path.expanduser(config_file))
    self._config_file = config_file
    self._template_json_data = json.loads(self._template_text)
    if expand_templates:
      if template_env is None:
        template_env = {}
      else:
        template_env = dict(template_env)
      if not self._config_file is None and not 'config_file' in template_env:
        self.populate_template_env(template_env)
        
      t = Template(self._template_text)
      self._json_text = t.substitute(template_env)
      self._json_data = json.loads(self._json_text)
    else:
      self._json_text = self._template_text
      self._json_data = self._template_json_data
    self.bake()

  def load_json_data(
        self,
        json_data: JsonableDict,
        config_file: Optional[str]=None,
        expand_templates: bool=False,
        template_env: Optional[Dict[str, str]]=None
      ):
    config_text = json.dumps(json_data)
    self.loads(config_text, config_file=config_file, expand_templates=expand_templates, template_env=template_env)
  
  def load_stream(
        self,
        stream: TextIO,
        config_file: Optional[str]=None,
        expand_templates: bool=False,
        template_env: Optional[Dict[str, str]]=None
      ):
    config_text = stream.read()
    self.loads(config_text, config_file=config_file, expand_templates=expand_templates, template_env=template_env)
  
  def load_file(
        self,
        config_file: str,
        expand_templates: bool=False,
        template_env: Optional[Dict[str, str]]=None
      ):
    with open(config_file) as f:
      self.load_stream(f, config_file=config_file, expand_templates=expand_templates, template_env=template_env)

class KvConfig(KvConfigBase):
  _version: Optional[str] = None
  _cfg_class_name: Optional[str] = None
  _cfg_json_data: Optional[JsonableDict] = None
  _cfg: Optional[KvConfigBase] = None

  def populate_template_env(self, template_env: Dict[str, str]):
    if not self._config_file is None:
      template_env['config_file'] = self._config_file
      template_env['config_file_hash'] = self.hash_pathname(self._config_file)
      config_dir = os.path.dirname(self._config_file)
      template_env['config_dir'] = config_dir
      template_env['config_dir_hash'] = self.hash_pathname(config_dir)

  def bake(self):
    self._version = self._json_data['version']
    self._cfg_class_name = self._json_data['cfg_class']
    self._cfg_json_data = self._json_data['cfg_data']
    self._cfg = self.create_config_obj(self._cfg_class_name)
    self._cfg.load_json_data(self._cfg_json_data, config_file=self._config_file, expand_templates=False)

class KvPassphraseConfig(KvConfigBase):
  def get_passphrase(self) -> str:
    raise NotImplementedError()

class KvKeyringPassphraseConfig(KvPassphraseConfig):
  _keyring_service: Optional[str] = None
  _keyring_key: Optional[str] = None
  
  def bake(self):
    self._keyring_service = self._json_data['service']
    self._keyring_key = self._json_data['key']

  def get_passphrase(self) -> str:
    assert not self._keyring_service is None
    assert not self._keyring_key is None
    result = keyring.get_password(self._keyring_service, self._keyring_key)
    if result is None:
      raise KeyError(f"KvKeyringPassphraseConfig: service '{self._keyring_service}', key name '{self._keyring_key}' does not exist")
    return result

