# Python ElkM1 library

[![PyPI version](https://badge.fury.io/py/elkm1-lib.svg)](https://badge.fury.io/py/elkm1-lib)
[![CI](https://github.com/gwww/elkm1/actions/workflows/code-quality.yml/badge.svg)](https://github.com/gwww/elkm1/actions/workflows/code-quality.yml)
[![Downloads](https://pepy.tech/badge/elkm1-lib)](https://pepy.tech/project/elkm1-lib)
[![License](https://img.shields.io/github/license/mashape/apistatus.svg)](https://pypi.org/project/elkm1_lib/)

Library for interacting with ElkM1 alarm/automation panel.

https://github.com/gwww/elkm1

## Requirements

- Python 3.9 (or higher)

## Description

This package is created as a library to interact with an ElkM1 alarm/automation
pattern. The motivation to write this was to use with the Home Assistant
automation platform. The library can be used for writing other ElkM1 integration
applications. The IO with the panel is asynchronous over TCP or over the
serial port.

## Installation

```bash
    $ pip install elkm1_lib
```

## Overview

Basic connection to the Elk panel:

```python
    from elkm1_lib import Elk
    import logging

    # Print to STDOUT
    LOG = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    # Connect to elk
    elk = Elk({'url': 'elk://192.168.1.100'})
    elk.connect()
    elk.run()
```

The above will connect to the Elk panel at IP address 192.168.1.100. the `elk://`
prefix specifies that the connect is plaintext. Alternatively, `elks://` will
connect over TLS. In this case a userid and password must be specified
and the call to `Elk` changes to:

```python
    elk = Elk(
        {'url': 'elks://192.168.1.100', 'userid': 'test', 'password': 'pass'}
    )
```

The following ElkM1 connection protocols are supported:

- serial:// - Serial port;
- elk:// - Elk M1XEP Ethernet, non-secure
- elks:// - Elk M1XEP Ethernet, secure, TLS 1.0
- elksv1_0:// - Elk M1XEP Ethernet, secure, TLS 1.0, supported on M1XEP version < 2.0.46
- elksv1_2:// - Elk M1XEP Ethernet, secure, TLS 1.2, supported on M1XEP version = 2.0.46
- elksv1_3:// - Elk M1XEP Ethernet, secure, TLS 1.2, not yet supported on M1XEP, reserved for future

A username and password are required for any of the secure modes.

To see working example code take a look at the script `bin/simple`.

The `Elk` object supports the concept of `Elements`. An `Element`
is the base class representation of `Zones`, `Lights`, etc. So, for
example there is a list of zones: `elk.zones` and each zone can be
accessed by `elk.zones[index]`. Each element has a `__str__`
representation so that it is easy to print its contents.

All `Elements` are referenced starting at 0. Even though the Elk panel
refers to, for example, zones 1-208, the library references them
as zones 0-207. All translation from base 0 to 1 and vice-versa is
handled internally in the `elkm1_lib.message` module.

After creating the `Elk` object and connecting to the panel the
library code will synchronize all the elements to the data from the Elk panel.

Many Elk messages are handled by the library, caching their contents. When a
message causes a change to an attribute of an `Element`, registered
callbacks are called so that user use of the library can be notified
of changing elements. The following user code shows registering a callback:

```python
    def call_me(element, changeset):
       print(changeset)

    for zone_number in range(Max.ZONES.value):
      elk.zones[zone_number].add_callback(call_me)
```

The library encodes, decodes, and processes messages to/from the
Elk panel. All the encoding and decoding is done in `elkm1_lib.message` module.

Messages received are handled with callbacks. The library
internally registers callbacks so that decoded messages
can be used to update an `Element`. The user of the
library may also register callbacks. Any particular message
may have multiple callbacks.

When the message is received it is decoded
and some validation is done. The message handler is called
with the fields of from the decoded message. Each type of
message has parameters that match the message type. All handler parameters
are named parameters.

Here is an example of a message handler being registered and how it is called:

```python
    def zone_status_change_handler(zone_number, zone_status):
      print(zone_number, zone_status)

    elk.add_handler('ZC', zone_status_change_handler)
```

The above code registers a callback for 'ZC' (Elk zone status change)
messages. When a ZC message is received the handler functions are called
with the zone_number and zone_status.

There are a number of pseudo-handlers that act like the handlers. These are
called when events happen. The pseudo-handlers are:

- `connect`: When a successful connection to the ElkM1 is completed.
- `disconnect`: When a connection to a panel is disconnected.
- `login`: When a login is made to the panel (using `elks://` connection mode.
  A single boolean parameter is passed `succeeded`.
- `sync_complete`: When the panel has completed synchonizing all its elements.
- `timeout`: When a send of a message to the ElkM1 times out (fails to send).
- `unknown`: When a message from the ElkM1 is received and the library does
  not have a method to decode the message. The message is passed to this handler
  and can be decoded outside of the library.

## Utilities

The `bin` directory of the library has one utility program and
a couple of example uses of the library.

### `mkdoc`

The utility `mkdoc` creates a Markdown table of the list of Elk
messages with a check mark for those messages have encoders/decoders
and an X for those messages are not planned to be implemented.
There are no parameters to `mkdoc`. It outputs to stdout.
The data for the report comes from the ElkM1 library code mostly.
A couple of things are hard coded in the mkdoc script, notably
the "no plans to implement" list.

### `simple`

The `simple` Python script is a trivial use of the ElkM1 library.
It connects to the panel, syncs to internal memory, and continues
listening for any messages from the panel. The URL of the ElkM1 to
connect to is retrieved from an environment variable named `ELKM1_URL`.

### `elk`

The `elk` Python script is a bit of a command interpretor. It can run in
two modes. Non-interactive mode is the default. Just run the `elk` command.
The non-interactive mode is similar to `simple` except there are a
couple of message handlers (`timeout` and `unknown` handlers).

The `elk` can also be run in interactive mode by invoking it by
`elk -i`. In this mode is uses curses (full screen use of the terminal)
that has a command line and an output window. `TAB` switches between
the command line and output windows. In the output window the arrow keys
and scrollwheel scroll the contents of the window.

In the command line when running `elk -i` there are a
number of commands. Start with `help`. Then `help <command>` for
details on each command. In general there are commands to dump the internal
state of elements and to invoke any of the encoders to send a message
to the Elk panel.

For example, `light <4, 8, 12-14` would invoke the `__str__` method
for the light element to print the cached info for lights 0-3, 8, and 12-14.

Another example would be `pf 3` which issues the pf (Turn light off)
command for light number 3 (light 4 on the panel -- remember 0
versus 1 base).

All of the commands that send messages to the panel are automatically
discovered and are all the XX_encode functions in the `elkm1_lib.message`
module. The docstring and the XX_encode's parameters are shown as part
of the help.

## Development

This project uses [uv](https://astral.sh/blog/uv-unified-python-packaging) for development dependencies.
Installation instructions are on their website. Other tools used by development are installed as part of
the development dependencies.

To get started developing:

```
git clone https://github.com/gwww/elkm1.git
cd elkm1
uv sync
# Activate the created virtual environment according to the shell you are using.
make test # to ensure everything installed properly
```

There is a `Makefile` in the root directory. The `make` command
followed by one of the targets in the `Makefile` can be used. If you don't
have or wish to use `make` the `Makefile` serves as examples of
commands that are used for code quality in this project. Those commands are
also run on pushes and pull requests.

## Reporting a Bug

No problem ;) — report the bugs! But, logs are most often required. If you
are using Home Assistant, which is about the only use I'm aware of for
this library, then add the following to your `configuration.yaml`:

```
logger:
  default: info
  logs:
    custom_components.elkm1: debug
    elkm1_lib: debug
```

Do everything in your power to trim to logs down to their smallest. One way is
to reproduce your problem quickly so that few other logs are not generated in
between. Another recommendation is to use the simplest configuration that you
can think of to reproduce the problem.

Can you reproduce the problem in other ways? If this is a problem that is
being experienced while using Home Assistant try using the `Services` in `Developer Tools`.

Sometime logs may have sensitive information in them. You may want to
scan your logs for that info and "X" it out. In addition, you can send logs
directly to me. Support email is in the `pyproject.toml` file. You may also
send a link to somewhere you've stored/shared the file (DropBox for example).
