import sys

import logging as log
log.basicConfig(
    level=log.DEBUG,
    format="%(module)s: %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
import random

from cosim_interface import CosimInterface
import wbfbd


WRITE_FIFO_PATH = sys.argv[1]
READ_FIFO_PATH  = sys.argv[2]

CLK_PERIOD = 10

def delay_function():
    return CLK_PERIOD * random.randrange(5, 10)


cosim_interface = CosimInterface(WRITE_FIFO_PATH, READ_FIFO_PATH, delay_function, True)

try:
    log.info("Starting cosimulation")

    main = wbfbd.main(cosim_interface)

    expected0 = 0b010101
    expected1 = 0b11

    log.info(f"Expecting cfg0 value: {expected0}")

    log.info("Reading cfg0")
    read_val = main.cfg0.read()
    if read_val != expected0:
        raise Exception(f"Read wrong value form cfg0 {read_val}")

    log.info("Reading st0")
    read_val = main.st0.read()
    if read_val != expected0:
        raise Exception(f"Read wrong value form st0 {read_val}")


    log.info(f"Expecting cfg1 value: {expected1}")

    log.info("Reading cfg1")
    read_val = main.cfg1.read()
    if read_val != expected1:
        raise Exception(f"Read wrong value form cfg1 {read_val}")

    log.info("Reading st1")
    read_val = main.st1.read()
    if read_val != expected1:
        raise Exception(f"Read wrong value form st1 {read_val}")

    cosim_interface.wait(5 * CLK_PERIOD)
    log.info("Ending cosimulation")
    cosim_interface.end(0)

except Exception as E:
    cosim_interface.end(1)
    log.exception(E)
