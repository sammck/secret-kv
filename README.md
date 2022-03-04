secret-kv: Project-local secret key/value storage
=================================================

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Latest release](https://img.shields.io/github/v/release/sammck/secret-kv.svg?style=flat-square&color=b44e88)](https://github.com/sammck/secret-kv/releases)

A tool and API for managing local secrets for a project.

Table of contents
-----------------

* [Introduction](#introduction)
* [Installation](#installation)
* [Usage](#usage)
  * [Command line](#command-line)
  * [API](api)
* [Known issues and limitations](#known-issues-and-limitations)
* [Getting help](#getting-help)
* [Contributing](#contributing)
* [License](#license)
* [Authors and history](#authors-and-history)


Introduction
------------

Python package `secret-kv` provides a command-line tool as well as a runtime API for managing and accessing a database of secret key/value
pairs that are scoped to a particular project, directory, etc. The entire database is encrypted using a single passphrase that is maintained
in a system keychain.

Some key features of secret-kv:

* Built on [sqlcipher](https://www.zetetic.net/sqlcipher/), an encrypted extension of [sqlite](https://www.sqlite.org/index.html) that
  applies 256-bit AES encryption to a single-file database, using a single passphrase.
* Uses [keyring](https://pypi.org/project/keyring/) to maintain the passphrase for a given database, and optionally to store a
  default passphrase to be used for newly create databases.
* Maintains separation of secrets and the key/value namespace between different projects,
  including passphrases stored in [keyring](https://pypi.org/project/keyring/).
* An entire project's secrets can be destroyed simply by deleting its database (and a single keyring secret)
* Allows a project to access its private secrets with minimal configuration.
* Supports full validated JSON values.
* Supports binary values.
* Allows metadata to be attached to key/value pairs in the form of tag-name/value pairs
* Key enumeration
* database export/import/merge (not yet implemented)
* A rich command-line tool:
  * JSON-formatted results available for all data retrieval operations
  * Optional colored output
  * bash tab-completion available
  * Optional raw (unquoted) results for string and binary data


Installation
------------

### Prerequisites

**Python**: Python 3.7+ is required. See your OS documentation for instructions.

**sqlcipher**: `secret-kv`` depends on [sqlcipher](https://www.zetetic.net/sqlcipher/), which is available in many OS distributions. On
ubuntu/debian, it can be installed with:

```bash
sudo apt-get install sqlcipher
```

### From PyPi

The current released version of `secret-kv` can be installed with 

```bash
pip3 install secret-kv
```

### From GitHub

[Poetry](https://python-poetry.org/docs/master/#installing-with-the-official-installer) is required; it can be installed with:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Clone the repository and install secret-kv into a private virtualenv with:

```bash
cd <parent-folder>
git clone https://github.com/sammck/secret-kv.git
cd secret-kv
poetry install
```

You can then launch a bash shell with the virtualenv activated using:

```bash
poetry shell
```


Usage
=====

Command Line
------------

There is a single command tool `secret-kv` that is installed with the package.

### Setting a default database passphrase

The first time you use `secret-kv` (as an OS user), you may want to set a default passphrase
to be used for creation of new databases. This passphrase will be securely stored in
[keyring](https://pypi.org/project/keyring/) under service="python/secret-kv", username="default-db-passphrase":





This section explains the principles behind this README file.  If this repository were for actual _software_, this [Usage](#usage) section would explain more about how to run the software, what kind of output or behavior to expect, and so on.

### Basic operation

A suggested approach for using this example README file is as follows:

1. Copy the [source file](README.md) for this file to your repository and commit it to your version control system
2. Delete all the body text but keep the section headings
3. Write your README content
4. Commit the new text to your version control system
5. Update your README file as your software evolves

The first paragraph in the README file (under the title at the very top) should summarize your software in a concise fashion, preferably using no more than one or two sentences.

<p align="center"><img width="80%" src=".graphics/screenshot-top-paragraph.png"></p>

The space under the first paragraph and _before_ the [Table of Contents](#table-of-contents) is a good location for optional [badges](https://github.com/badges/shields), which are small visual tokens commonly used on GitHub repositories to communicate project status, dependencies, versions, DOIs, and other information.  The particular badges and colors you use depend on your project and personal tastes.

The [Introduction](#introduction) and [Usage](#usage) sections are described above.

In the [Known issues and limitations](#known-issues) section, summarize any notable issues and/or limitations of your software.  The [Getting help](#getting-help) section should inform readers of how they can contact you, or at least, how they can report problems they may encounter.  The [Contributing](#contributing) section is optional; if your repository is for a project that accepts open-source contributions, then this section is where you can explain to readers how they can go about making contributions.

The [License](#license) section should state any copyright asserted on the project materials as well as the terms of use of the software, files and other materials found in the project repository.  Finally, the [Authors and history](#authors-and-history) section should inform readers who the authors are; it is also a place where you can acknowledge other contributions to the work and the use of other people's software or tools.

### Additional options

Some projects need to communicate additional information to users and can benefit from additional sections in the README file.  It's difficult to give specific instructions &ndash; a lot depends on your software, your intended audience, etc.  Use your judgment and ask for feedback from users or colleagues to help figure out what else is worth explaining.

API
---


Known issues and limitations
----------------------------

* Import/export are not yet supported.

Getting help
------------

Please report any problems/issues [here](https://github.com/sammck/secret-kv/issues).

Contributing
------------

Pull requests welcome.

License
-------

secret-kv is distributed under the terms of the [MIT License](https://opensource.org/licenses/MIT).  The license applies to this file and other files in the [GitHub repository](http://github.com/sammck/secret-kv) hosting this file.

Authors and history
---------------------------

The author of secret-kv is [Sam McKelvie](https://github.com/sammck).
