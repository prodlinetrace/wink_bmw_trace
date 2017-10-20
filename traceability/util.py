"""
Utility functions
"""
import sys
import os
import logging
from constants import PC_READY_FLAG
logger = logging.getLogger(__name__.ljust(12)[:12])


def hex_dump(block):
    for byte in block:
        sys.stdout.write("%.2x " % byte)
    sys.stdout.write("\n")


def get_hex_block(block):
    buf = ""
    for byte in block:
        buf += "%.2x " % byte
    return buf


def dec_dump(block):
    for byte in block:
        sys.stdout.write("%.2d " % byte)
    sys.stdout.write("\n")


def get_dec_block(block):
    buf = ""
    for byte in block:
        buf += "%.2d " % byte
    return buf


def set_pc_ready_flag(controler, block, value, check=False):
    flag = PC_READY_FLAG
    return set_flag(controler, block, flag, value, check)


def set_flag(controler, block, flag, value, check=False):
    logger.debug("PLC: %s block: %s flag '%s' set to: %s " % (controler.get_id(), block.get_db_number(), flag, value))
    # set block value in memory
    block[flag] = value
    # write flag to PLC
    block.write_item(controler.get_client(), flag)
    if check:  # check actual value - optional
        block = controler.get_db(block.get_db_number())
        actval = block.__getitem__(flag)
        logger.debug("PLC: %s block: %s flag '%s' actual value is: %s " % (controler.get_id(), block.get_db_number(), flag, actval))


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def file_name_with_size(filename, separator="  =>  "):
    if os.path.exists(filename):
        return "%s %s %s" % (str(filename), str(separator), sizeof_fmt(int(os.path.getsize(filename))))
    else:
        return filename


def offset_spec_block(spec_block, offset=0):
    """
    returns specification block with added offset
    """
    result = []
    for line in spec_block.split('\n'):
        if line and not line.startswith('#'):  # skip commented lines
            row = line.split('#')[0]  # remove trailing comment
            _index, _name, _type = row.split()
            shifted_index = str(float(_index) + offset)
            result.append("   ".join([shifted_index, _name, _type]))

    return "\n".join(result) + "\n"
