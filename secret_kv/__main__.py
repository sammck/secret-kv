#!/usr/bin/env python3
#
# Copyright (c) 2022 Samuel J. McKelvie
#
# MIT License - See LICENSE file accompanying this package.
#

"""Command-line interface for secret_kv package"""


from typing import Optional, Sequence, List

import sys

# NOTE: this module runs with -m; do not use relative imports
from secret_kv import __version__ as pkg_version
from secret_kv.sql_store import test_me

def run(argv: Optional[Sequence[str]]=None) -> int:
  """Run the secret-kv command-line tool with provided arguments

  Args:
      argv (Optional[Sequence[str]], optional):
           A list of commandline arguments (NOT including the program as argv[0]!),
           or None to use sys.argv[1:]. Defaults to None.

  Returns:
      int: The exit code that would be returned if this were run as a standalone command.
  """
  import argparse

  parser = argparse.ArgumentParser(description="Access a secret key/value database.")
  parser.add_argument('--version', action='store_true', default=False,
                      help='Display version')
  parser.add_argument('--test', action='store_true', default=False,
                      help='Run a test')
  args = parser.parse_args(argv)

  if args.version:
    print(pkg_version)
    return 0
  if args.test:
    test_me()

  return 0

# allow running with "python3 -m", or as a standalone script
if __name__ == "__main__":
  sys.exit(run())