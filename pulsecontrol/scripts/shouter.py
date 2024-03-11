import chipshouter as cs
import chipwhisperer as cw


shouter = cs.ChipSHOUTER("/dev/serial/by-id/usb-NewAE_ChipSHOUTER_Serial_NA4GI3AL-if00-port0")
shouter.hwtrig_term = False
shouter.hwtrig_mode = False
shouter.emode = True

scope = cw.scope()
scope.glitch.output = "enable_only"
scope.io.glitch_lp = True
scope.glitch.repeat = 1
scope.glitch.trigger_src = 'ext_single'
scope.glitch.arm_timing = 'before_scope'
scope.glitch.clk_src = 'clkgen'


scope.glitch.ext_offset = 0
scope.glitch.repeat = 20
shouter.voltage = 100

scope.arm()
shouter.faults_current = 0
shouter.armed = True


