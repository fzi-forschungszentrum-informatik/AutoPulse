# Installing and configuring klipper

## Installation

## Configuration

After you've build klipper using `printd`, will have a `config` directory in the root of the `printd` directory.
This directory contains the `printer.cfg` file which is the configuration file for klipper.
This file is the single source of truth four your device, with it, you can define every possible setting and behavior of your printer.

Instead of the default file from `printd`, we will be using the configuration from this repository, located at `configuration/printd/printer.cfg`.
Either copy or link `ln -s` the file to the configuration directory of your `printd` configuration directory.

### Moonraker

We also need to adjust a setting in `moonraker.conf`, to allow our main computer to connect and send commands to klipper.

1. Open up `moonraker.conf` in the `printd/config` directory.
2. Locate the `[authorization]` section.
3. Add your computers IP address to the list of `trusted_clients`

### LEDs

We use the mainboard and existing connectors to power the two sets of LEDs we use to illuminate both the EMFI-Probe and the target MCU.
For the probe LEDs, we will be using the plug previously used for the heated bed. The pin for that is `PA7`.
The PCB LED is connected to the JST connector previously used for the parts cooling fan. The pin for that is `PA0`.
You don't need to add or adjust these values if you use the `printer.cfg` included in this repository.
