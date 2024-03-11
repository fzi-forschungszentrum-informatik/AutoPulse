# Build Instructions

This section will guide you through the process of assembling the hardware components and the main assembly of the AutoPulse system.

## Dissabling the stock hotend

We are using parts of the stock hotend for our EMFI mount, so we need to remove the stock hotend first, if you've already installed it. If the printer is still in its stock configuration, you can skip this step, as the hotend is already removed.

#TODO Add disassembly instructions

## EMFI Mount Assembly

The EMFI mount is a simple assembly consisting of four parts: the clamp, the mounting plate, and the CR-Touch and camera extensions.
We first need to insert the heat-set inserts into each parts.

A minimum of 12 inserts are required for the assembly, but we recommend using 16 inserts for added stability and functionality.
Take a look at the images below for reference on where to insert the inserts.
Set your soldering iron to a temperature between 180-200°C and use a wide and short soldering tip push in the inserts.

### Mounting Clamp

#### Parts List

- 6x M3x6mm SHCS
- 4x M3 washer
- 12x heat-set insert (minimum 10)
- (printed) clamp

#### Assembly

Install the heat-set inserts into the clamp, take a look at the refercence images for the correct mounting positions.

![Carriage Mount Sockets](img/mount/DSC00196.JPG)
![Mounting Plate Sockets](img/mount/DSC00197.JPG)
![CR-Touch Mount Sockets](img/mount/PXL_20240311_082938572.jpg)

### Mounting Plate

#### Parts List

- 4x heat-set insert (minimum 2)
- (optional) 1x M3x10mm SHCS

#### Assembly

Install the heat-set inserts into the mounting plate, take a look at the refercence images for the correct mounting positions.
The two outer inserts on the bottom of the plate are required for the PCB camera extension, the two other inserts are optional, one is for one additional screw on the PCB camera extension, the other is for the optional M3x10mm screw we use as a zip-tie anchor.

![Mounting Plate](img/mount/mounting-plate.png)

### CR-Touch Extension

#### Models

- [Swivel](../models/Touch-Probe/Touch-Probe-Body.step)
- [Mount](../models/Touch-Probe/Touch-Probe-attachment.step)


#### Parts List

- 5x heat-set insert
- 2x M3x6mm SHCS
- 3x M3x10mm SHCS
- 1x M4x16mm SHCS
- 4x 6x3mm Neodym Magnet 

#### Assembly

Install the heat-set inserts into the CR-Touch swivel and mount, take a look at the refercence images for the correct positions.
![CR-Touch Swivel HEAT-SET](img/mount/crtouch/touch_assembly_03.jpg)

Next, install the magnets into the appropriate cutouts. Make sure the magnets are aligned to attract each other, as shown in the reference image. The cutouts are tight, so no glue should be necessary to keep them in there. You might need to push them in using a screwdriver. Be carefull to not break the printed part!
![CR-Touch Magnets 1](img/mount/crtouch/touch_assembly_04.jpg)
![CR-Touch Magnets 2](img/mount/crtouch/touch_assembly_05.jpg)

We are now ready to attach the swivel arm to the mounting bracket. Use the M4 screw and some elbow grease. The swivel arm has enough clearance for it to freely swing around the screw as a pivot, but the mounting bracket screw-hole is designed to be self-tapped by the M4. The clearance is designed for PLA parts, so your milage may vary if you're using a different material. 
![CR-Touch Pivot Screw](img/mount/crtouch/touch_assembly_07.jpg)

Now for attaching the CR-Touch. Use the M3x6mm screws to mount the probe to the swivel arm. Guide the cable through the provided hole. It's easier to keep the cable attached to the CR-Touch rather than attaching it once the probe is screwed in.
![CR-Touch Probe Attachment](img/mount/crtouch/touch_assembly_10.jpg)
![CR-Touch Probe Attachment](img/mount/crtouch/touch_assembly_11.jpg)

Finally, attach the part to the mounting clamp. First insert the heat-set inserts on the front of the mounting clamp, as shown here: 
![CR-Touch Mounting Holes](img/mount/crtouch/touch_assembly_12.jpg)

Then attach the part to the clamp with the M3x10mm screws.
![CR-Touch Pointing Down](img/mount/crtouch/touch_assembly_13.jpg)
You should now be able to tilt the CR-Touch probe out of the way after the initial sequence is done, which helps with clearance on some target boards.
![CR-Touch Tilted Away](img/mount/crtouch/touch_assembly_14.jpg)


### PCB Camera Extension

#TODO Add parts list
#TODO Add assembly instructions

### Probe Camera

For the final assembly of the probe camera, we it's best to have the Raspberry Pi already set-up, as well as all components already connected.
We will then open up the camera view, which simplifies the final alignment of the camera.

#TODO Add parts list
#TODO Add assembly instructions

#### Replacing the stock leveling screws

The default leveling screws are too large for the new probe camera module and will interfere with the movement of the carriage. We have designed a simple replacement part that is easy to print and install.
![Screws](img/PXL_20240311_081916589.jpg)
Our part uses the same threaded insert as the stock screws. Simply use a soldering iron to heat the insert, pushing it out of the stock screw, and insert it into the new part.
We recommend to only replace the screws on the left side of the printer, as the right side is not impacted by our probe camera module.

## Assembly

#### Parts List

- 6x M3x6mm SHCS
- 4x M3 washer
- 1x stock Creality PCB breakout board
- 1x assembled EMFI mount

#### Assembly

Use two of the M3x6mm screws to attach the PCB breakout board to the mounting assembly.
Place two washers each between the printed part and the PCB breakout board.
Be careful when screwing in the screws, the mounting tabs are fragile.

Line up the assembled EMFI mount with the printer carriate, then screw in the M3x6mm screws.

## Electronics

**WARNING**: The following steps require you to open the electronics compartment of the printer. This will void your warranty. We are not responsible for any damage caused to your printer. If you are not comfortable with these steps, please ask for help from someone who is. Keep the printer unplugged while performing these steps.

### Opening the electronics compartment

1. Lay the printer on its right side. Remove the screen beforehand,
   you won't be needing it in the future.
2. Remove the tool-drawer before trying to remove the bottom panel.
3. Remove the 9 screws from the bottom panel.
4. Remove the bottom panel. Carefully detach the cooling fan cable from the control board before removing the panel completely.

### (Optional) Adding UART support for the TMC2208 stepper drivers

This step is optional, but highly recommended. It will enable UART for the stepper drivers, allowing for higher accuracy and quieter operation.
If you want to do this, follow the instructions in the [Enabling UART for the TMC2208 Stepper Drivers](#part-99999-optional-enabling-uart-for-the-tmc2208-stepper-drivers) section, then return here.
You can also do this step after the initial setup, but it is easier to do it now, while the electronics compartment is already open.

### Wiring

1. Locate the heated-bed cable and thermistor cable. Both are located on the left of the board, labeled as "BED" and "BED TEM" respectively. Take a look at our [wiring diagram](img/wiring-diagram.png) for reference.
2. Use your fingers to remove the hot-glue from the heated-bed cable and the thermistor cable. Try to avoid using metal tools for removing the hot-glue, as you might damage the PCB.
3. Unscrew the terminals of the heated-bed cable and the thermistor cable. You can use a flat-head screwdriver for this.
4. Insert the cables for the probe-LEDs into the terminals previously used for the heated-bed.
   Keep the polarity in mind.
   Test this before before closing the electronics compartment.
5. Use the cable-clip at the top of the aluminium extrusion to secure LED cable.
6. (Optional) While the panel is open, remove the bottom cable clip which usually holds the rainbow cable. Secure the end with the tape that's already holding it down.
7. Note down the exact chip on the control board. We will need this in the future. It should be one of either `STM32F401` or `STM32F103`.
8. Replace the bottom panel and secure it with the 9 screws. Keep in mind to reattach the cooling fan cable to the control board.

### Raspberry Pi

#### Power Supply

We are using the official Raspberry Pi power supply, but it is entirely possible to use one of these [img/variable-power-supply.jpg](variable power supplies) instead. The official power supply is rated at 5.1V and 5.0A. The power supply should be connected to the USB-C port on the Raspberry Pi.

As an alternative, we have also tested the Raspberry Pi with a cheap variable power supply.
This has the advantage of being able to power the Pi with the 24V power supply of the printer, requiring one less power outlet.
The power supply should be connected to the GPIO pins on the Raspberry Pi.
The positive wire should be connected to pin 2 and the negative wire should be connected to pin 6.

#### CSI Camera Cables

Next, you should connect the CSI camera cables to the Raspberry Pi.
The camera cables should be connected to the CSI port on the Raspberry Pi.
The camera cables should be connected to the Raspberry Pi with the black side facing away from the Ethernet port.
The order of the cameras doesn't matter, just route them as fits best with the physical layout of your components.
You can verify both cameras work by running `libcamera-hello -n` in the command line.
There will be two outputs of `Registered camera`, each providing a path to `/dev/media{0,1,2,3}`.
All cameras should be detected out of the box when using the default raspbian image.
Try rebooting you can't connect to the cameras.
Never unplug the cameras while the Raspberry Pi is powered on.
The metal contacts on the ribbon cable can short something during unplugging, which could damage the Raspberry Pi or the Cameras.

#### Connecting the Raspberry Pi to the Printer

Use a USB-A to USB-C cable to connect the Raspberry Pi to the printer. The USB-A side should be connected to the Raspberry Pi and the USB-C side should be connected to the printer.

## Installing Klipper

### Part 0: Installing Docker

We like to use the `printd` service to manage the `klipper` configuration. This will use marginally more resources than a direct deployment of klipper, but comes with advantage of simplified dependency management simple installation.
It does require a working docker installation, so we will start by setting that up.

To do this, follow the instructions at [docs.docker.com/engine/install/debian](https://docs.docker.com/engine/install/debian/#install-using-the-repository).
Then add your user to the `docker` group with `sudo usermod -aG docker $USER`.
You will need to log out and back in for this change to take effect.

### Part 1: Setting up `printd`

1. Clone the repository with `git clone https://github.com/mkuf/prind.git`.
2. Move into the directory with `cd printd`.
3. Register the alias for simplifying the following commands. Run `alias pmake="docker compose -f docker-compose.extra.make.yaml run --rm make"`.
4. Run `pmake menuconfig`.
   Use the arrow keys to navigate the TUI, use the space bar to select and deselect options, and use the enter key to enter sub-menus.
5. Select `Enable extra low-level configuration options`
6. Select `STMMicroelectronics STM32` as your microcontroller architecture.
7. The processor model is the model number you have noted down in the wiring step.
8. If you have the `STM32F401`, select the `64KiB bootloader` offset. If you have the `STM32F103`, select the `28KiB bootloader` offset.
9. Press `q` to exit the menu and `y` to save the configuration.
10. Run `pmake` to build the firmware.
11. The finished firmware will be at `out/klipper.bin`.

#### Copying the configuration

The default location for the `printer.cfg` in `printd` is ... [TODO]: # Add path, update this description

## Part 2: Flashing the Mainboard

1. You should already have the `klipper.bin` from the previous step.
   - If you have the `STM32F103`, move this file to the root of the SD-card that came with the printer.
   - If you have the `STM32F401`, create a subfolder called `STM32F4_UPDATE` and move the file there.
2. With the printer turned off, insert the SD-card into the printer, then turn the printer on.
3. You'll get no feedback as to if you've been successful, but the printer should now be running Klipper.

**Note** If you want to change some settings and flash the firmware again, re-name the `*.bin` to something else. The MCU will not flash the same firmware file again if it has the same name.

Use these images to compare with your settings:

![STM32F401](img/klipper/firmware401.png)
![STM32F103](img/klipper/firmware103.png)

**Note** You are now ready to start using klipper. The next steps are optional, but highly recommended.

## Part 99999: (Optional) Enabling UART for the TMC2208 Stepper Drivers

The default configuration of the steppers on the Ender 3 S1 is tuned for fast and silent movements during prints. We do not care about speed or noise, we want the highest possible accuracy. To achieve this, we will need to enable UART for the TMC2208 stepper drivers.

### Removing the control board

1. Take a picture of the control board, to make reassembly easier.
2. Remove all hot-glue from the connectors, then
3. Disconnect all cables from the board.
4. Remove the five screws holding it in place.
5. Remove the board from the printer.

### Soldering the jumpers

1. Orient the board in such a way that the USB and SD-card slots are on the right side.
2. Locate the stepper drivers, they are on the top of the board, with each having a small heat sink glued to it.
   - Underneath each heat sink are multiple resistors in a row. One of these resistor pads is unpopulated, and this is where we will solder the jumper.
   - The upper pad itself is connected to the resistor to the left of it, which in turn is connected to the UART pin of the stepper driver.
   - We will use this empty pad to solder the jumper, because it gives us a larger target for our soldering iron.
3. Solder a Jumper to the upper pad of the three leftmost stepper drivers. We don't care about the extruder stepper driver, as it is not used in our device.
   - It's possible to use the extruder stepper as a backup, if one of the other steppers is damaged during our modifications.
4. Either crimp a dupont connector to the other end of the jumper, or solder it directly to one of the unused pins for the touch screen. Take a look at the pictures for reference.
5. Update the `printer.cfg` with the correct UART pins. Uncomment the `[tmc2209 stepper_{x|y|z>}` section if you used the same pins as in the pictures.
   - Pins `PB2`, `PB1` and `PA2` of the `STM32F401` are connected to the empty touchscreen-connector on the control board. We chose to use those because of them being in a straight, direct line, making it easier to attach a dupont connector to them.
   - Take a look at the data sheet of your chip if you want to use other pins. Simply use a multimeter to measure for continuity between the legs of the chip and the pins on the board to find the correct ones.
6. Continue with the instructions in the [Wiring](#wiring) section.
