# PulseControl

## Development

I found that using the pycharm remote interpreter is the best way to develop on the PI. This way you can use the IDE on your local machine and the code runs on the PI.
![Add New Interpreter](image.png)

Otherwise clone or rsync the code to the PI and run it there.
Make sure the PI has the required dependencies installed:

```bash
rye sync
```

To start the server, run:
```bash
just server-start
```
in the `pulsecontrol` directory.

To start a run with a specific configuration, run:
```bash
just init configuration/<description>/<integrator-name>.json 
just start
```
the description is a directory in the configuration directory and the integrator-name is the name of the integrator in the configuration file.
The integrator needs to have the same name as the python file in the integrators directory.

In the current case, this would be:
```bash
just init configuration/spc/bam.json 
just start
```

This will immediately start the run with the specified configuration.

To stop the server, run:
```bash
just reset
```
or stop the current run in PyCharm.





## Installation


**Note:** This is only required once, on the PI the server is going to run.
```bash
apt install libcap-dev libcamera-dev libksm++-dev libfmt-dev libdrm-dev python3-opencv
```
