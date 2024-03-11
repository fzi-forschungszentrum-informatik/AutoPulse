from dataclasses import dataclass
from time import sleep

import chipwhisperer as cw
import click

from chipwhisperer.capture.scopes import OpenADC
from chipwhisperer.capture.targets import SimpleSerial

from pulsecontrol.helpers import format_hex

public_password: list[int] = [0xFE, 0xED, 0xFA, 0xCE, 0xCA, 0xFE, 0xBE, 0xEF]


@dataclass
class Store:
    scope: OpenADC
    target: SimpleSerial


@click.group()
@click.pass_context
def cli(ctx):
    click.echo('Starting...')
    ctx.obj = Store(*setup())


def reset(scope: OpenADC):
    # reset the target
    scope.io.nrst = False
    sleep(0.05)
    scope.io.nrst = None
    sleep(0.2)


def setup():
    scope: OpenADC = cw.scope()
    scope.default_setup()
    scope.io.tio1 = 'serial_tx'
    scope.io.tio2 = 'serial_rx'
    target = cw.target(scope, SimpleSerial, noflush=True)
    target.baud = 38400
    # target.baud = 14400

    return scope, target


def pprint_hex(*data: int | bytes):
    out = []
    for d in data:
        tmp = '0x'
        tmp += hex(d)[2:].upper()
        out.append(tmp)

    print(*out)


def send_password(ser, password: list[int]):
    # Autobaud
    # ser.write(bytearray([0x00]))
    for i in password:
        t = bytearray([i])
        ser.write(t)
        sleep(0.05)
        res = ser.hardware_read(5)
        # pprint_hex(t[0], *res)
        print("tho %s" % format_hex(*res))
        sleep(0.05)


def init_uart(ser):
    ser.write(b"\x00")
    sleep(0.05)
    pprint_hex(*ser.hardware_read(1))


def check_echo(ser) -> bool:
    ser.write(b"\x20")
    res = ser.hardware_read(4)
    # print('res', repr(res))
    pprint_hex(*res)
    return bool(res)


@cli.command()
@click.pass_obj
def real_password(store: Store):
    ser = store.target.ser
    reset(store.scope)
    ser.flush()
    init_uart(ser)

    send_password(ser, public_password)

    if check_echo(ser):
        click.echo('Got a response')
    else:
        click.echo('No Response from board')


@cli.command()
@click.pass_obj
def wrong_password(store: Store):
    ser = store.target.ser
    reset(store.scope)
    ser.flush()
    init_uart(ser)

    broken = public_password
    broken[-2] = 0xFF
    # print(broken)
    send_password(ser, broken)
    if check_echo(ser):
        click.echo('Got a response')
    else:
        click.echo('No Response from board')


if __name__ == "__main__":
    cli()
    # real_password(*setup())
    # test_all(*setup())
