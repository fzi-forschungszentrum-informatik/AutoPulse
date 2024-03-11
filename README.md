# AutoPulse: The ultimate do-it-yourself EMFI automation platform

This project was created researchers at KASTEL and the FZI Forschungszentrum Informatik.
In this repository, you will find the necessary files to build your own EMFI automation platform.

## [Assembly](/assembly/README.md)

This section contains the build instructions, as well as a BOM and the necessary 3D files to build your own EMFI automation platform.
As a note, these instruction are heavily reliant on the use of a specific 3D printer, the Ender 3 S1.
We used this printer because it was widely available, and contains both reliable as well as very affordable components.
It's possible to follow these instructions with a different 3D printer, but you may need to adjust the 3D files accordingly.
Take a look at these requirements when selecting a different 3D printer:

1. UART capable TMC stepper drivers.
   - The Ender 3 S1 uses TMC2208 stepper drivers, which are UART capable.
   - We needed to modify the mainboard slightly to enable UART mode.
2. Dual Z-Axis stepper motors.
   - Some Ender 3 models only have one stepper motor for the Z-Axis, which reduces the Z-Axis consistency across the X-Axis.
3. [klipper](https://klipper3d.org/) compatibility.
4. v-slot rollers on the X and Y-Axis.
   - Other solutions exhibit larger static friction, which will reduce the accuracy during small movements.

## Software

Take a look at the [Readme](pulsecontrol/README.md) in `pulsecontrol`, it details the steps required to install and configure the software part of this project.
