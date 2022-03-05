from typing import Optional, Union, Tuple, Dict, TypeVar, Any, List, Iterable, Mapping, Iterator
from .internal_types import JsonableDict, Jsonable, SqlConnection, XJsonableDict, XJsonable

import json

from .store import KvStore
from .value import KvValue, xjson_decode
from .exceptions import KvBadPassphraseError, KvError, KvReadOnlyError, KvNoEnumerationError

from sqlite3 import Cursor
from sqlite3.dbapi2 import DatabaseError

class SqlKvStore(KvStore):
  _db: Optional[SqlConnection] = None
  _passphrase: Optional[str] = None
  _db_pragmas_initialized: bool = False
  _db_initialized: bool = False

  SCHEMA_VERSION: int = 1
  DB_APP_NAME = "SqlKvStore"

  def __init__(self, store_name: Optional[str]=None, db: Optional[SqlConnection]=None, passphrase: Optional[str]=None):
    super().__init__(store_name)
    self._db = db
    self._passphrase = passphrase

  @property
  def db(self) -> Optional[SqlConnection]:
    return self._db

  @db.setter
  def db(self, db: SqlConnection):
    if self._db_pragmas_initialized:
      raise RuntimeError("SqlKvStore: Cannot change db SqlConnection after initialization")
    self._db = db

  def get_db(self) -> SqlConnection:
    db = self.db
    if db is None:
      raise RuntimeError("SqlKvStore: Database has not been connected")
    if not self._db_initialized:
      self.init_db()
    return db

  def set_passhrase(self, passphrase: Optional[str]):
    if self._db_pragmas_initialized:
      raise RuntimeError("SqlKvStore: Cannot set passphrase after initialization")
    self._passphrase = passphrase
    return self._db

  def initialize_db_pragmas(self):
    if not self._db_pragmas_initialized:
      db = self.db
      if not self._passphrase is None:
        # NOTE: sqlite3 interpolation/escaping does not work with pragma.
        #       so we will manually escape the quoted passphrase
        escaped_passphrase = self._passphrase.replace("'", "''")
        db.execute(f"PRAGMA key = '{escaped_passphrase}';")
      db.execute('''PRAGMA foreign_keys = ON;''')
      self._db_pragmas_initialized = True

  def initialize_new_db(self):
    db = self.db
    self.initialize_db_pragmas()
    cur = db.cursor()
    cur.execute(
      '''CREATE TABLE dbinfo (
             dbinfo_id        INTEGER     PRIMARY_KEY NOT NULL,
             app              VARCHAR(50) NOT NULL,
             schema_version   INTEGER     NOT NULL
           );
      ''')
    cur.execute(
      '''CREATE TABLE kv_value (
             kv_value_id      INTEGER       PRIMARY KEY AUTOINCREMENT,
             kv_type          VARCHAR(20)   NOT NULL,
             json_text        VARCHAR(2048) NOT NULL
           );
      ''')
    cur.execute(
      '''CREATE TABLE kv_key (
             kv_key_id                INTEGER       PRIMARY KEY AUTOINCREMENT,
             key_name                 VARCHAR(100)  UNIQUE NOT NULL,
             kv_value_id              INTEGER       NOT NULL,
             CONSTRAINT fk_key_value
                FOREIGN KEY (kv_value_id)
                REFERENCES kv_value (kv_value_id)
                ON DELETE CASCADE
           );
      ''')
    cur.execute(
      '''CREATE TABLE kv_tag (
             kv_tag_id                INTEGER       PRIMARY KEY AUTOINCREMENT,
             tag_name                 VARCHAR(100)  NOT NULL,
             kv_key_id                INTEGER       NOT NULL,
             kv_value_id              INTEGER       NOT NULL,
             CONSTRAINT fk_tag_key
                FOREIGN KEY(kv_key_id)
                REFERENCES kv_key (kv_key_id)
                ON DELETE CASCADE,
             CONSTRAINT fk_tag_value
                FOREIGN KEY(kv_value_id)
                REFERENCES kv_value (kv_value_id)
                ON DELETE CASCADE
           );
      ''')
    cur.execute(
      '''CREATE UNIQUE INDEX kv_key_tag ON kv_tag (kv_key_id, tag_name);
      ''')

    cur.execute(
      '''INSERT INTO dbinfo (dbinfo_id, app, schema_version) VALUES (?,?,?);''',
      (0, self.DB_APP_NAME, self.SCHEMA_VERSION))

    db.commit()

  def init_db(self):
    if not self._db_initialized:
      db = self.db
      self.initialize_db_pragmas()
      cur = db.cursor()
      try:
        cur.execute('''SELECT count(name) FROM sqlite_master WHERE type='table' AND name=? ''', [ "dbinfo" ])
      except Exception as ex:
        if hasattr(ex, 'sqlite_errorname') and ex.sqlite_errorname == 'SQLITE_NOTADB':
          raise KvBadPassphraseError(f"Incorrect passphrase for {self}, or the database is corrupt.") from ex
        raise

      if cur.fetchone()[0] == 0:
        self.initialize_new_db()
      else:
        cur.execute('''SELECT dbinfo_id,app,schema_version FROM dbinfo''')
        dbinfo_id, app_name, schema_version = cur.fetchone()
        dbinfo_id: int
        app_name: str
        schema_version: int
        if app_name != self.DB_APP_NAME:
          raise RuntimeError(f"{self}: Registered app name {json.dumps(app_name)} does not match required value {json.dumps(self.DB_APP_NAME)}")
        if dbinfo_id != 0:
          raise RuntimeError(f"{self}: database dbinfo_id has corrupt value {dbinfo_id}")
        if schema_version > self.SCHEMA_VERSION:
          raise RuntimeError(f"{self}: Database schema version {schema_version} is newer than software schema version {self.SCHEMA_VERSION}; upgrade is required")
        if schema_version < self.SCHEMA_VERSION:
          raise RuntimeError(f"{self}: Database schema version {schema_version} is older than software schema version {self.SCHEMA_VERSION}; schema upgrade is not implemented. Delete the database and recreate.")
      self._db_initialized = True


  def update_passphrase(self, new_passphrase: str) -> None:
    db = self.get_db()
    # NOTE: sqlite3 interpolation/escaping does not work with pragma.
    #       so we will manually escape the quoted passphrase
    escaped_passphrase = new_passphrase.replace("'", "''")
    db.execute(f"PRAGMA rekey = '{escaped_passphrase}';")
    
  def _get_key_id(self, key: str) -> Optional[int]:
    """Look up the key_id for a named key, if it exists

    Args:
        key (str): The name of the key

    Returns:
        Optional[int]: The key_id of the key, if it exists, and None otherwise
    """
    cur = self.get_db().cursor()
    key_id: Optional[int] = None
    cur.execute('''SELECT kv_key_id FROM kv_key WHERE kv_key.key_name = ?''', [ key ])
    row = cur.fetchone()
    if not row is None:
      key_id = row[0]
    return key_id

  def _get_required_key_id(self, key: str) -> int:
    """Look up the key_id for a named key, and raise KeyError if it does not exist

    Args:
        key (str): The name of the key

    Returns:
        int: The key_id of the key
    """
    key_id = self._get_key_id(key)
    if key_id is None:
      raise KeyError(f"{self.store_name}: {json.dumps(key)}")
    return key_id

  def _get_key_id_and_value_id(self, key: str) -> Tuple[Optional[int], Optional[int]]:
    cur = self.get_db().cursor()
    cur.execute('''SELECT kv_key_id, kv_value_id FROM kv_key WHERE kv_key.key_name = ?''', [ key ])
    row = cur.fetchone()
    if row is None:
      key_id: Optional[int] = None
      value_id: Optional[int] = None
    else:
      key_id = row[0]
      value_id = row[1]
    return key_id, value_id

  def _get_key_id_and_value(self, key: str) -> Tuple[Optional[int], Optional[KvValue]]:
    cur = self.get_db().cursor()
    key_id: Optional[int] = None
    value: Optional[KvValue] = None
    cur.execute('''SELECT kv_key_id, kv_type, json_text FROM kv_key INNER JOIN kv_value on kv_key.kv_value_id = kv_value.kv_value_id WHERE kv_key.key_name = ?''', [ key ])
    row = cur.fetchone()
    if not row is None:
      key_id = row[0]
      kv_type: str = row[1]
      if kv_type != 'xjson':
        raise ValueError(f"Unrecognized kv_type in kv_value table: {kv_type}")
      json_text: str = row[2]
      json_data: Jsonable = json.loads(json_text)
      xjson_data = xjson_decode(json_data)
      value = KvValue(xjson_data)
    return key_id, value

  def _get_tag_id_and_value_id(self, key_id: int, tag_name: str) -> Tuple[Optional[int], Optional[int]]:
    cur = self.get_db().cursor()
    cur.execute('''SELECT kv_tag_id, kv_value_id FROM kv_tag WHERE kv_tag.kv_key_id = ? AND kv_tag.tag_name = ?''', [ key_id, tag_name ])
    row = cur.fetchone()
    if row is None:
      tag_id: Optional[int] = None
      value_id: Optional[int] = None
    else:
      tag_id = row[0]
      value_id = row[1]
    return tag_id, value_id

  def _get_tag(self, key_id: int, tag_name: str) -> Optional[KvValue]:
    cur = self.get_db().cursor()
    cur.execute('''SELECT kv_type, json_text FROM kv_tag INNER JOIN kv_value on kv_tag.kv_value_id = kv_value.kv_value_id WHERE kv_tag.kv_key_id = ? AND kv_tag.tag_name = ?''', [ key_id, tag_name ])
    row = cur.fetchone()
    if row is None:
      result: Optional[KvValue] = None
    else:
      kv_type: str = row[0]
      if kv_type != 'xjson':
        raise ValueError(f"Unrecognized kv_type in kv_value table: {kv_type}")
      json_text: str = row[1]
      json_data: Jsonable = json.loads(json_text)
      xjson_data = xjson_decode(json_data)
      result = KvValue(xjson_data)
    return result

  def _has_tag(self, key_id: int, tag_name: str) -> bool:
    cur = self.get_db().cursor()
    cur.execute('''SELECT COUNT(*) FROM kv_tag WHERE kv_tag.kv_key_id = ? AND kv_tag.tag_name = ?''', [ key_id, tag_name ])
    result = cur.fetchone()[0] > 0
    return result

  def _get_tag_names(self, key_id: int) -> Iterable[str]:
    cur = self.get_db().cursor()
    cur.execute('''SELECT tag_name from kv_tag WHERE kv_tag.kv_key_id = ?''', [ key_id ])
    for row in cur:
      tag_name: str = row[0]
      yield tag_name

  def _get_tags_as_items(self, key_id: int) -> Iterable[Tuple[str, KvValue]]:
    cur = self.get_db().cursor()
    cur.execute('''SELECT tag_name, kv_type, json_text FROM kv_tag INNER JOIN kv_value on kv_tag.kv_value_id = kv_value.kv_value_id WHERE kv_tag.kv_key_id = ?''', [ key_id ])
    for row in cur:
      tag_name: str = row[0]
      kv_type: str = row[1]
      if kv_type != 'xjson':
        raise ValueError(f"Unrecognized kv_type in kv_value table: {kv_type}")
      json_text: str = row[2]
      json_data: Jsonable = json.loads(json_text)
      xjson_data = xjson_decode(json_data)
      value = KvValue(xjson_data)
      yield (tag_name, value)

  def _get_tags(self, key_id: int) -> Dict[str, KvValue]:
    return dict(self._get_tags_as_items(key_id))

  def _clear_tags(self, key_id: int):
    cur = self.get_db().cursor()
    cur.execute(
      '''DELETE FROM kv_value
            WHERE EXISTS (
                SELECT * from kv_tag
                  WHERE kv_tag.kv_key_id = ? AND kv_tag.kv_value_id = kv_value.kv_value_id
              );
      ''', [ key_id ])
    # TODO: this may be unnecessary due to CASCADE DELETE
    cur.execute('''DELETE from kv_tag WHERE kv_key_id = ?''', [ key_id] )

  def _delete_tag_and_value_by_id(self, tag_id: int, value_id: int):
    cur = self.get_db().cursor()
    cur.execute('''DELETE FROM kv_value WHERE kv_value_id = ?''', [ value_id ])
    # TODO: this may be unnecessary due to CASCADE DELETE
    cur.execute('''DELETE from kv_tag WHERE kv_tag_id = ?''', [ tag_id ])

  def _delete_tag(self, key_id: int, tag_name: str):
    cur = self.get_db().cursor()
    cur.execute(
      '''DELETE FROM kv_value
            WHERE EXISTS (
                SELECT * from kv_tag
                  WHERE kv_tag.kv_key_id = ? AND kv_tag.tag_name = ? AND kv_tag.kv_value_id = kv_value.kv_value_id
              );
      ''', [ key_id, tag_name ])
    # TODO: this may be unnecessary due to CASCADE DELETE
    cur.execute('''DELETE from kv_tag WHERE kv_key_id = ? AND tag_name = ?''', [ key_id , tag_name])

  def _insert_value(self, value: XJsonable) -> int:
    """Inserts a new unreferenced KvValue into kv_value, and returns its kv_value_id
    The caller must create a reference to the returned id within this transaction,
    (either from a tag or a key) or the newly created row will leak.

    Args:
        value (XJsonable): The new value to insert

    Returns:
        int: The kv_value_id of the newly created kv_value record
    """
    if not isinstance(value, KvValue):
      value = KvValue(value)
    cur = self.get_db().cursor()
    cur.execute('''INSERT INTO kv_value (kv_type, json_text) VALUES (?,?)''', [ "xjson", value.json_text ])
    return cur.lastrowid

  def _delete_value_by_id(self, value_id: int):
    """Deletes a KvValue from kv_value by its id. Because of CASCADE DELETE, this will also
    delete any key or tag that references it, so generally the references should be removed first.

    Args:
        value_id (int): The value_id of the row containing the value
    """
    cur = self.get_db().cursor()
    cur.execute('''DELETE from kv_value WHERE kv_value_id = ?''', [ value_id ])
    return cur.lastrowid

  def _set_tag(self, key_id: int, tag_name: str, value: XJsonable) -> int:
    if not isinstance(value, KvValue):
      value = KvValue(value)
    tag_id, old_value_id = self._get_tag_id_and_value_id(key_id, tag_name)
    value_id = self._insert_value(value)
    cur = self.get_db().cursor()
    if tag_id is None:
      cur.execute('''INSERT INTO kv_tag (tag_name, kv_key_id, kv_value_id ) VALUES(?, ?, ?)''', [ tag_name, key_id, value_id ])
      tag_id = cur.lastrowid
    else:
      assert not old_value_id is None
      cur.execute('''UPDATE kv_tag SET kv_value_id = ? WHERE kv_tag_id = ?''', [ value_id, tag_id ])
      # TODO: this may be unnecessary due to CASCADE DELETE
      self._delete_value_by_id(old_value_id)
    return tag_id

  def _set_tags(self, key_id: int, tags: Mapping[str, XJsonable], clear_tags: bool=False):
    if clear_tags:
      self._clear_tags(key_id)
    for tag_name, value in tags.items():
      if not isinstance(value, KvValue):
        value = KvValue(value)
      self._set_tag(key_id, tag_name, value)

  def _set_key_value(self, key: str, value: XJsonable) -> int:
    if not isinstance(value, KvValue):
      value = KvValue(value)
    key_id, old_value_id = self._get_key_id_and_value_id(key)
    value_id = self._insert_value(value)
    cur = self.get_db().cursor()
    if key_id is None:
      cur.execute('''INSERT INTO kv_key (key_name, kv_value_id ) VALUES(?, ?)''', [ key, value_id ])
      key_id = cur.lastrowid
    else:
      assert not old_value_id is None
      cur.execute('''UPDATE kv_key SET kv_value_id = ? WHERE kv_key_id = ?''', [ value_id, key_id ])
      # TODO: this may be unnecessary due to CASCADE DELETE
      self._delete_value_by_id(old_value_id)
    return key_id

  def get_value_and_tags(self, key: str) -> Tuple[Optional[KvValue], Dict[str, KvValue]]:
    tags: Dict[str, KvValue] = {}
    key_id, value = self._get_key_id_and_value(key)
    if not key_id is None:
      cur = self.get_db().cursor()
      tags = self._get_tags(key_id)
    return value, tags

  def get_value(self, key: str) -> Optional[KvValue]:
    key_id, value = self._get_key_id_and_value(key)
    return value

  def set_value_and_tags(self, key: str, value: XJsonable, tags: Mapping[str, XJsonable], clear_tags: bool=False):
    if not isinstance(value, KvValue):
      value = KvValue(value)
    key_id = self._set_key_value(key, value)
    self._set_tags(key_id, tags, clear_tags=clear_tags)
    self.get_db().commit()

  def set_value(self, key: str, value: XJsonable):
    if not isinstance(value, KvValue):
      value = KvValue(value)
    self._set_key_value(key, value)
    self.get_db().commit()

  def delete_value(self, key: str):
    key_id, value_id = self._get_key_id_and_value_id(key)
    if key_id is None:
      raise KeyError(f"{self.store_name}: {json.dumps(key)}")
    self._clear_tags(key_id)
    cur = self.get_db().cursor()
    cur.execute(
      '''DELETE FROM kv_value
            WHERE EXISTS (
                SELECT * from kv_key
                  WHERE kv_key.kv_key_id = ? AND kv_key.kv_value_id = kv_value.kv_value_id
              );
      ''', [ key_id ])
    # TODO: this may be unnecessary due to CASCADE DELETE
    cur.execute('''DELETE from kv_key WHERE kv_key_id = ? ''', [ key_id ])
    self.get_db().commit()

  def iter_keys(self) -> Iterator[str]:
    cur = self.get_db().cursor()
    cur.execute('''SELECT key_name FROM kv_key''')
    for row in cur:
      yield row[0]

  def iter_items(self) -> Iterator[Tuple[str, KvValue]]:
    cur = self.get_db().cursor()
    cur.execute('''SELECT key_name, kv_type, json_text FROM kv_key INNER JOIN kv_value on kv_key.kv_value_id = kv_value.kv_value_id''')
    for row in cur:
      key: str = row[0]
      kv_type: str = row[1]
      if kv_type != 'xjson':
        raise ValueError(f"Unrecognized kv_type in kv_value table: {kv_type}")
      json_text: str = row[2]
      json_data: Jsonable = json.loads(json_text)
      xjson_data = xjson_decode(json_data)
      value = KvValue(xjson_data)
      yield key, value
  
  def items_with_tags(self) -> Iterable[Tuple[str, KvValue, Dict[str, KvValue]]]:
    cur = self.get_db().cursor()
    cur.execute('''SELECT kv_key_id, key_name, kv_type, json_text FROM kv_key INNER JOIN kv_value on kv_key.kv_value_id = kv_value.kv_value_id''')
    for row in cur:
      key_id: int = row[0]
      key: str = row[1]
      kv_type: str = row[2]
      if kv_type != 'xjson':
        raise ValueError(f"Unrecognized kv_type in kv_value table: {kv_type}")
      json_text: str = row[2]
      json_data: Jsonable = json.loads(json_text)
      xjson_data = xjson_decode(json_data)
      value = KvValue(xjson_data)
      tags = self._get_tags(key_id)
      yield key, value, tags

  def iter_values(self) -> Iterator[KvValue]:
    for key, value in self.items():
      yield value

  def clear(self):
    cur = self.get_db().cursor()
    cur.execute('''DELETE FROM kv_value''')
    # TODO: this may be unnecessary due to CASCADE DELETE
    cur.execute('''DELETE FROM kv_key''')
    # TODO: this may be unnecessary due to CASCADE DELETE
    cur.execute('''DELETE FROM kv_tag''')
    self.get_db().commit()

  def has_key(self, key: str) -> bool:
    cur = self.get_db().cursor()
    cur.execute('''SELECT COUNT(*) FROM kv_key WHERE kv_key.key_name = ?''', [ key ])
    result = cur.fetchone()[0] > 0
    return result

  def get_tags(self, key:str) -> Dict[str, KvValue]:
    key_id = self._get_required_key_id(key)
    tags = self._get_tags(key_id)
    return tags

  def get_num_tags(self, key:str) -> int:
    key_id = self._get_required_key_id(key)
    cur = self.get_db().cursor()
    cur.execute('''SELECT COUNT(*) kv_tag WHERE kv_key_id = ?''', [ key_id ])
    result: int = cur.fetchone()[0]
    return result

  def get_tag(self, key: str, tag_name: str) -> Optional[KvValue]:
    key_id = self._get_required_key_id(key)
    result = self._get_tag(key_id, tag_name)
    return result

  def set_tags(self, key, tags: Mapping[str, XJsonable], clear_tags: bool=False):
    key_id = self._get_required_key_id(key)
    self._set_tags(key_id, tags, clear_tags=clear_tags)
    self.get_db().commit()

  def set_tag(self, key, tag_name: str, value: XJsonable):
    if not isinstance(value, KvValue):
      value = KvValue(value)
    key_id = self._get_required_key_id(key)
    self._set_tag(key_id, tag_name, value)
    self.get_db().commit()

  def delete_tag(self, key, tag_name: str):
    key_id = self._get_required_key_id(key)
    tag_id, value_id = self._get_tag_id_and_value_id(key_id, tag_name)
    if tag_id is None:
      raise KeyError(f"{self.store_name}: key {json.dumps(key)}, tag {json.dumps(key)}")
    assert not value_id is None
    self._delete_tag_and_value_by_id(tag_id, value_id)
    self.get_db().commit()

  def tag_names(self, key: str) -> Iterable[str]:
    key_id = self._get_required_key_id(key)
    return self.get_tags(key).keys()

  def tag_items(self, key:str) -> Iterable[Tuple[str, KvValue]]:
    key_id = self._get_required_key_id(key)
    return self._get_tags_as_items(key_id)
  
  def tag_values(self, key: str) -> Iterable[KvValue]:
    for key, value in self.tag_items(key):
      yield value

  def has_tag(self, key: str, tag_name: str) -> bool:
    key_id = self._get_required_key_id(key)
    return self._has_tag(key_id, tag_name)

  def num_keys(self) -> int:
    cur = self.get_db().cursor()
    cur.execute('''SELECT COUNT(*) FROM kv_key''')
    result: int = cur.fetchone()[0]
    return result

