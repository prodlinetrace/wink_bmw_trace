"""
Utility functions
"""
import sys
import os
import logging
import time
from .constants import PC_READY_FLAG
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
        if line and line.startswith('#'):  # just append comments and continue. 
            result.append(line)
            continue
        if line:
            row = line.split('#')[0].strip()  # read the row without comment
            _comment = ''
            if len(line.split('#')) > 1:
                 _comment = "#".join(line.split("#")[1:]).strip()  # read comment if present 
            _index, _name, _type = row.split()
            shifted_index = str(float(_index) + offset)
            #result.append("   ".join([shifted_index, _name, _type, _comment]))
            result.append("{index:10} {name:62} {type:10} # {comment}".format(index=shifted_index, name=_name, type=_type, comment=_comment))

    return "\n".join(result) + "\n"


def retry_and_catch(exceptions, tries=5, logger=None, level=logging.ERROR, logger_attr=None, delay=0, backoff=0, max_delay=0):
    """
    Retries function up to amount of tries.

    Backoff disabled by default.

    :param exceptions: List of exceptions to catch
    :param tries: Number of attempts before raising any exceptions
    :param logger: Logger to print out to.
    :param level: Log level.
    :param logger_attr: Attribute on decorated class to get the logger ie self._logger you would give "_logger"
    :param delay: initial delay seconds
    :param backoff: backoff multiplier
    :param max_delay: maximum possible delay
    """
    def deco_retry(f):
        def f_retry(*args, **kwargs):
            max_tries = tries
            d = delay
            exs = tuple(exceptions)
            log = logger
            md = max_delay
            while max_tries > 1:
                try:
                    return f(*args, **kwargs)
                except exs as e:
                    sleep_time = min(d, md) if max_delay else d
                    message = "Caught Exception: {}. Retrying in {}[s] for {} more times.".format(e.__repr__(), round(sleep_time, 2), max_tries)

                    # Get logger from cls instance of function
                    # Grabbing 'self'
                    instance = args[0]
                    if not log and logger_attr and hasattr(instance, logger_attr):
                        log = getattr(instance, logger_attr, None)

                    if log:
                        log.log(level, message)
                    else:
                        print(message)

                    # Sleep current delay
                    if d:
                        time.sleep(sleep_time)

                        # Increment delay
                        if backoff:
                            d *= backoff
                    max_tries -= 1

            return f(*args, **kwargs)  # Final attempt will not catch any errors.
        return f_retry
    return deco_retry