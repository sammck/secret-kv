#
# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Sentinel values"""

from typing import Type, Tuple

class Sentinel:
  _name: str

  def __init__(self, name: str):
    self._name = name

  def __str__(self) -> str:
    return self._name

  def __repr__(self) -> str:
    return f"<Sentinel '{self._name}'>"

def sentinel(name: str) -> Tuple[Sentinel, Type[Sentinel]]:
  class SentinelType(type):
    __name__ = f"{name}Type"

    def __str__(self) -> str:
      return self.__name__

    def __repr__(self) -> str:
      return f"<SentinelType '{self.__name__}'>"

  class Sentinel1(Sentinel, metaclass=SentinelType):
    pass
  result = Sentinel1(name)
  return result, type(result)

# Convenient sentinel for missing optional argument
Nothing, NothingType = sentinel('Nothing')
