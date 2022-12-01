# Changelog
All notable changes to this project will be documented in this file.
This project follows [Semantic Versioning](https://semver.org/).

## [2.2.1]
- Change minimum Python version back to 3.9

## [2.2.0]
- Refactor connection.py; no functional changes
- Refactor get_description; no functional changes
- Bump minimum Python version to 3.10

## [2.1.0]
- Add keypad function key and chime sync (Thx @jimboca)

## [2.0.2]
- Use a more liberal cipher set.

## [2.0.1]
- Support for Python 3.10; SSL cipher must be explicitly set

## [2.0.0]
- **Breaking change**: use Enums proper instead of Enum.values; signature of many
  of the xx_encode/xx_decode functions change as the parameters that were str,
  int, etc are now AlarmLevel, etc. Full list of of the enums used is in `const.py`
  Inspiration for this change from from Home Assistant move to using more
  enums to eliminate constants. Attribute changes:
  - Zone.definition (switch to Enum)
  - Zone.logical_status (switch to Enum)
  - Zone.physical_status (switch to Enum)
  - Area.armed_status (switch to Enum)
  - Area.arm_up_state (switch to Enum)
  - Area.alarm_status (switch to Enum)
  - Area.arm method uses ArmLevel instead of a string
  - Thermostat.mode (switch to Enum)
  - Thermostat.fan (switch to Enum)
  - Thermostat.set (use Enum)
  - Setting.value_format (switch to Enum)
  - Area.alarm_memory (changed from "0"/"1" string to bool)
- Add use of Generics on Elements to give better typing of self.elements

## [1.3.6]
- Refactor to separate concerns. Major part of this separation was pulling the
  observer code out of message.py and putting it in a separate class. This
  simplified message.py so that it is now just a set of encode/decode functions,
  no more class. This also made the connection.py code cleaner and focused
  on just the transport concerns.

## [1.3.5]
- Add logging of exception information on disconnect
- Add login event callback when first message received
- Move user/pass sending from connection to elk.py (cleaner connection code)

## [1.3.4]
- Fix wrong parameter introduced in typing exercise.

## [1.3.3]
- Remove pause/resume from `elk.py`; not used outside of internal lib and
  available in `Connection` if really needed
- Fix over zealous cleanup where password sent after sync. Doh.

## [1.3.2]
- Fix __iter__ type to be a Generator
- All the elements (Areas, Counters, Zones, etc) are now attributes of the
  Elk class instead of being dynamic attributes

## [1.3.1]
- Add py.typed
- Tweak CI to be more informative

## [1.3.0]
- Add typing: https://peps.python.org/pep-0561/
- Changed minimum Python version to 3.9
- Part of the typing change caused a circular import for username in util;
  Moved username to be a method on Users

## [1.2.2]
- On a non-secure connection still generate a login event on got_connection 
  (it will always be successful)

## [1.2.1]
- Bug in decode of UA message; did not handle hex for areas
- Cleanup after sync_complete to remove handler; allows for apps
  to send there own UA messages

## [1.0.0]
- Time to take this out of beta! The code has been stable for well over a year.
- Added support for TLS 1.2 secure connection mode. This is required for M1XEP
  version 2.0.46 and higher

## [0.8.11]
- Add get_voltage on zone.

## [0.8.8]
- Fix panel not recognized when using auto-configure.

## [0.8.7]
- Fix https://github.com/home-assistant/core/issues/20630

## [0.8.6]
- Many small non-functional code cleanups.

## [0.8.5]
- Lint and isort cleanup
- Move from .format to f-string for string formatting

## [0.8.4]
- Black formatting
- configured flag for each element set based on whether element has
  a description

## [0.8.3]
- Added rw (set time) support and RR (realtime clock) support
- Added callbacks when get connected and disconnected from panel
- KC now supports keycode 0

## [0.8.2]
- Added zone bypass helper and area bypass helper
- Zone bypass handler bug fix (did not handle bypass all)
- Renamed zone_trigger to trigger (breaking change)
- Fix comment typo

## [0.8.1]
- Duh, left breakpoint in code; removed
- Update dependencies (pytz left in poetry.lock)

## [0.8.0]
- Beefed up README with error reporting.
- Improve LD handling by simplifying and adding feature to note last_user

## [0.7.15]
- Switch to `poetry` from `pipenv` for dependency management; allowed
  removal of __version.py__, setup.py, setup.cfg, and of course
  Pipfile*

## [0.7.14]
- Support multiple elk instances in same process by associating
  _message_handlers, _sync_handlers, and the description processing
  code with elk object rather than as file globals.
- Moved message encoders/decoders into new MessageDecode class
  to facilitate the above.

## [0.7.13]
- Fix updating counter value
- Add alarm memory processing

## [0.7.12]
- Add system_trouble_status decoding.

## [0.7.11]
- Add pytz as dependency
- Add KC (keypress) handling

## [0.7.10]
- Add level() helper to control lights
- Remove turn_on and turn_off for lights

## [0.7.9]
- Add time of change to IC message. The will force callbacks to be called.
  Useful when multiple IC messages with same content come in. This way the
  app using the callback can record the multiple attempts.
- Add username utility function to get a user's name from an user number

## [0.7.8]
- Add zt decode and helper
- Add dm helper
- Fix speak word. Was using wrong Elk message code.

## [0.7.7]
- Add 30 second timeout to create connection
- lint cleanups

## [0.7.6]
- Set user name to default name if not configured
- Enhance IC decode to handle prox
- IC handler now saves user code
- Heartbeat bug; connect was called on heartbeat timeout AND then again on
  disconnect callback
- Made log messages on connect/disconnect/error clearer and more consistent
- Change max time on connection retry to 60 seconds (was 120 seconds)
- Tidied up a couple of comments

## [0.7.5]
- Add heartbeat

## [0.7.4]
- Fix triggered_alarm attr to zone
- Add support for system trouble status (attached to panel)

## [0.7.3]
- Add triggered_alarm attr to zone

## [0.7.2]
- changed callback now dict instead of list

## [0.7.1]
- Fix bug on changed callback

## [0.7.0]
- Breaking change in attr changed callback

## [0.6.1]
- Tweak to as_dict
-
## [0.6.0]
- Rename package from elkm1 to elkm1_lib (due to conflicts with HASS component)

## [0.5.0]
- Many small fixes.
  - Fix lint errors.
  - Fix couple of syntax errors (speak_work for example)
  - Changed a number of initial values to make it easier to use
    library (examples are temperatures, initial area numbers)

## [0.4.9]
- Allow lowercase and single digit housecodes

## [0.4.8]
- Add formating to version strings
- Lower retry max time on connection lost
- Make `make clean` clean cleanerer

## [0.4.7]
- Change connect/reconnect to not block for HASS
- Update README with section on development setup

## [0.4.6]
- Change ee_decode to return str for armed status (was int)

## [0.4.5]
- Fixed typos

## [0.4.4]
- Add entry/exit message handling

## [0.4.3]
- Speak word, speak phrase helpers added (no constants for words/phrases)

## [0.4.2]
- Add handling for ST (temperature) messages
- Users were disabled and not working; enabled and fixed
- Retrieve temperatures on startup added

## [0.4.1]
- Add serial io dependency

## [0.4.0]
- Breaking change: no longer need to call 
  elk.loop.run_until_complete(elk.connect()); now call elk.connect()
- Retrieve counter values that have a description
- Fix for HASS Recorder errors about not being JSON serializable

## [0.3.7]
- Add asyncio serial support
  - Add test program to test serial support (bin/test-serial); requires data
    file that can be grokked from debug output of bin/elk
- Add proper command line parsing for bin/elk including URL as param
  - URL can also be read from environment variable ELKM1_URL
- Add reconnect logic with exponetial backoff
- Add pause writing to Elk when in remote programming mode
- Add const for format of setting
- Add const for RP mode
- Change thermostat const to match semantics of other const (e.g.: FAN_ON
  changed to ON, MODE_AUTO to AUTO, etc). Makes for better formatting when
  using pretty_const

## [0.3.6]
- Start of cleanup of cmdr.py; using attrs lib
- Change return on pretty_const to string (was tuple)
- First cut of adding disconnect handling
  - Reconnect to be handler by client; will get a callback on disconnect
- Fix alarm armup/state/etc to char from int

## [0.3.5]
- Lint cleanup
- Constants now all uppercase with underscores (can use pretty_const to print)
- Added encode for az, decode for AZ (no handler yet)

## [0.3.4]
Fix syntax; more descriptive docstrings

## [0.3.3]
- Make elk attribute in Element private
- Allow separator in default_name() to be specified
- Add constants for arming, alarms

## [0.3.1]
- Add elk attribute to Element

## [0.3.0]
- Add NS, NZ to no plans to implement list
- Make default name 1-based
- Add helpers to Output
- Add helpers to Light
- Add helper to Counter
- Add helper to Task
- Add helpers to Area
- Add handler for task change (TC) message
- Add thermostat setting
- Add helper for Setting (custom value)
- Added const for thermostat setting
- Added pretty_const (see test_util.py for API)

## [0.2.1] - 2018-04-13
- Add display message encoder

## [0.2.0] - 2018-04-13
- Add thermostats (not Omnistat)

## [0.1.1] - 2018-04-08
### Added
- MANIFEST.in to include bin files and LICENSE in distro

### Changed
- Makefile updated to include build and upload rules

## [0.1.0] - 2018-04-07
### Added
- Initial version, see README.rst for overview of project.

### Changed

### Removed
