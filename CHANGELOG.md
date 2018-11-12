# Changelog
All notable changes to this project will be documented in this file.
This project follows [Semantic Versioning](https://semver.org/).

## [0.7.11] -- Pending
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
