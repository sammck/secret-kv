# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Package secret_kv provides encrypted rich key/value storage for an application or project
"""

from .version import __version__

from .internal_types import Jsonable, JsonableDict, XJsonable, XJsonableDict
from .store import KvStore
from .sql_store import SqlKvStore
from .value import (
    KvValue,
    xjson_encode,
    xjson_decode,
    xjson_encode_simple_jsonable,
    xjson_decode_simple_jsonable,
    validate_simple_jsonable,
  )

from .exceptions import (
    KvError,
    KvNoEnumerationError,
    KvReadOnlyError,
    KvNoPassphraseError,
  )
  
from .config import (
    Config,
    ConfigContext,
    KvStoreConfig,
    SqlKvStoreConfig,
    PassphraseConfig,
    KeyringPassphraseConfig,
  )

from .simple import (
    get_kv_store_passphrase_keyring_service,
    get_kv_store_default_passphrase_keyring_key,
    get_kv_store_passphrase_keyring_key,
    get_kv_store_default_passphrase,
    set_kv_store_default_passphrase,
    get_kv_store_passphrase,
    set_kv_store_passphrase,
    load_any_config_file,
    load_kv_store_config,
    create_kv_store,
    locate_kv_store_config_file,
    open_kv_store,
    delete_kv_store,
  )

