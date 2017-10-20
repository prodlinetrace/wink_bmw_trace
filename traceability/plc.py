# this is a class of PLC controller
import snap7
import logging
import webbrowser
import traceback
from time import sleep
from datetime import datetime
from .constants import PC_HEARTBEAT_FLAG, PLC_QUERY_FLAG, PLC_SAVE_FLAG, STATION_NUMBER, STATION_STATUS, PRODUCT_TYPE, SERIAL_NUMBER, STATION_STATUS_CODES, STATION_ID, TRC_TMPL_COUNT, TRC_TMPL_SAVE_FLAG, PC_OPEN_BROWSER_FLAG, DATE_TIME, PC_READY_FLAG, PROGRAM_NAME, OPERATOR_QUERY_FLAG, OPERATOR_STATUS, OPERATOR_NUMBER
from .models import Product
from .blocks import DBs
from .custom_exceptions import UnknownDB
from .database import Database
logger = logging.getLogger(__name__)


class PLCBase(object):

    def __init__(self, ip='127.0.0.1', rack=0, slot=2, port=102, reconnect=10):
        self.__ip = ip
        self.__rack = int(rack)
        self.__slot = int(slot)
        self.__port = int(port)
        self.client = snap7.client.Client()
        self.__name = self.__ip
        self.__id = self.__ip
        self._reconnect = reconnect  # number of attempts to reconnect
        self.time = None
        self._active_data_blocks = []
        # configure database items
        self.database_engine = None
        self.database_client = None
        self.database_cursor = None
        self.counter_status_message_read = 0
        self.counter_status_message_write = 0
        self.counter_saved_operations = 0
        self.counter_show_product_details = 0
        self.counter_operator_status_read = 0
        self._baseurl = 'http://localhosts/app'
        self._popups = True
        self._pc_ready_flag_on_poll = False
        self._pollsleep = 0.1
        self._polldbsleep = 0.01
        self.__database_keepalive_sent = False

    def _init_database(self, dburi=''):
        self.database_engine = Database("{plc}".format(plc=self.get_id()))
        logger.info("PLC: {plc} connected to SQLite @ {dburi}. Status: {status}".format(plc=self.get_id(), dburi=dburi, status=self.database_engine.get_status()))

    def __repr__(self):
        return """<{module}.{name} {me}>""".format(module=self.__class__.__module__, name=self.__class__.__name__, me=str(self))

    @property
    def dbs(self):
        return DBs(self)

    @property
    def active_dbs(self):
        # we should list configuration file activated data blocks only
        # WARNING: this function reads value online from PLC and causes some network traffic that may cause connection errors.
        # please consider to use get_active_datablock_list() instead that is offline equivalent.
        ret = {}
        for k, v in DBs(self).items():
            if k in self._active_data_blocks:
                ret[k] = v
        return ret

    def items(self):
        """
        :param return: A list of pairs. Each pair will be (db name, db object)
        """
        return list(self.dbs.items())

    def __getitem__(self, dbid):
        """
        Get a db by number
        :param db: number of the db, int
        :return: db obj
        """
        return self.dbs[dbid]
        raise UnknownDB("PLC: {plc} DB: {db}. Failed to get db block.".format(plc=self.id, db=dbid))

    def iteritems(self):
        """
        Get the names & objects for all db's
        """
        return self.dbs.iteritems()

    def __contains__(self, dbid):
        """
        True if db is the number of a defined Data Block
        """
        return dbid in self.keys()

    def get_dbs(self):
        return self.items()

    def get_active_dbs(self):
        return self.active_dbs

    def get_db(self, dbid):
        """
        Get a db by number
        :param db: number of the db, int
        :return: db obj
        """
        return self.dbs[dbid]

    def keys(self):
        return [a for a in self.iterkeys()]

    def iterkeys(self):
        for block in self.dbs.iterkeys():
            yield block

    def __str__(self):
        return "PLC Id: {id} Name: {name} @ {ip}:{port}".format(id=self.__id, name=self.__name, ip=self.__ip, port=self.__port)

    def connect(self, attempt=0):
        if attempt < self._reconnect:
            attempt += 1  # increment connection attempts
            logger.debug("PLC: {plc} Trying to connect to: {ip}:{port}. Attempt: {attempt}/{total}".format(plc=self.__id, ip=self.__ip, port=self.__port, attempt=attempt, total=self._reconnect))
            try:
                self.client.connect(self.__ip, self.__rack, self.__slot, self.__port)
            except snap7.snap7exceptions.Snap7Exception:
                logger.warning("PLC: {plc} connection to: {ip}:{port} Failed. Attempt: {attempt}/{total}".format(plc=self.__id, ip=self.__ip, port=self.__port, attempt=attempt, total=self._reconnect))
                sleep(1)
                self.client.disconnect()

            if self.client.get_connected():
                logger.info("PLC: {plc} connected to: {ip}:{port}".format(plc=self.id, ip=self.__ip, port=self.__port))
                # clean pc_ready_flags
                try:
                    self.reset_pc_ready_flags()
                except snap7.snap7exceptions.Snap7Exception:
                    logger.error("PLC: {plc} connection to: {ip}:{port} Failed. Attempt {attempt}/{total}".format(plc=self.id, ip=self.__ip, port=self.__port, attempt=attempt, total=self._reconnect))
                    self.connect(attempt)
            else:
                logger.error("PLC: {plc} connection to: {ip}:{port} Failed. Attempt {attempt}/{total}".format(plc=self.id, ip=self.__ip, port=self.__port, attempt=attempt, total=self._reconnect))
                self.connect(attempt)
                return

    def disconnect(self):
        logger.info("PLC: {plc}. disconnection procedure started...".format(plc=self.id))
        if self.database_engine is not None:
            self.database_engine.disconnect()
        self.client.disconnect()
        self.reset_pc_ready_flags()

    def reset_pc_ready_flags(self):
        logger.info("PLC: {plc} resetting PC_Ready flags.".format(plc=self.id))
        for dbid in self.get_active_datablock_list():
            _block = self.get_db(dbid)
            if PC_READY_FLAG in _block.export():
                _block.set_pc_ready_flag(True)

    def get_client(self):
        return self.client

    def get_time(self):
        logger.debug("PLC: {plc}. Reading time from PLC.".format(plc=self.id))
        self.time = self.client.get_plc_date_time()
        return self.time

    def set_time(self, dtime):
        """
            Sets the time on PLC. Please use datetime.datetime input value format
        """
        logger.info("PLC: {plc}. Setting time on PLC to: {date}.".format(plc=self.id, date=dtime))
        self.client.set_plc_date_time(dtime)
        self.time = dtime

    def sync_time(self):
        """
            Synchronizes time on the PLC with PC.
        """
        logger.info("PLC: {plc}. Synchronizing PLC time with PC".format(plc=self.id))
        self.client.set_plc_system_date_time()

    def sync_time_if_needed(self, diff=3):
        """
            Synchronizes time on the PLC with PC.
            Time sync will be started if time differs more than `diff` value
            :param diff - time diff in seconds that triggers the sync (default 3 seconds)
        """
        ctrl_time = self.get_time()
        delta = datetime.now() - ctrl_time
        if abs(delta.total_seconds()) > diff:
            logger.info("PLC: {plc}. Time diff between PLC and PC {delta} is bigger than the trigger {trigger}. Synchronizing.".format(plc=self.id, delta=abs(delta.total_seconds()), trigger=diff))
            self.sync_time()

    def blink_pc_heartbeat(self):
        """
            Changes status of PC heart beat flag.
        """
        for dbid in self.get_active_datablock_list():
            _block = self.get_db(dbid)

            if _block is None:
                logger.warn("PLC: {plc} DB: {db} is missing on PLC. Skipping".format(plc=self.get_id(), db=dbid))
                return

            if PC_HEARTBEAT_FLAG in _block.export():
                # change the status of PLC_HEARTBEAT_FLAG flag
                if _block.__getitem__(PC_HEARTBEAT_FLAG) is True:
                    _block.set_flag(PC_HEARTBEAT_FLAG, False, False)
                else:
                    _block.set_flag(PC_HEARTBEAT_FLAG, True, False)

    def get_name(self):
        return self.__name

    def set_name(self, value):
        self.__name = value

    def get_id(self):
        return self.__id

    @property
    def id(self):
        return self.__id

    def set_id(self, value):
        self.__id = value

    def get_status(self):
        return self.client.get_connected()

    def get_ip(self):
        return self.__ip

    def get_port(self):
        return self.__port

    def set_active_datablock_list(self, dbs):
        self._active_data_blocks = dbs

    def get_active_datablock_list(self):
        return self._active_data_blocks

    def set_baseurl(self, baseurl):
        self._baseurl = baseurl

    def get_baseurl(self):
        return self._baseurl

    def set_popups(self, popups=True):
        self._popups = popups

    def get_popups(self):
        return self._popups

    def set_pollsleep(self, sleep=0):
        try:
            res = float(sleep)
        except ValueError as e:
            logger.error("PLC: {plc} Unable to set pollsleep value with '{val}' as input. Exception: {e}, TB: {tb}".format(plc=self.id, val=sleep, e=e, tb=traceback.format_exc()))
            res = 0
        logger.debug("PLC: {plc} Setting pollsleep to: {val}".format(plc=self.id, val=res))
        self._polldbsleep = res

    def get_pollsleep(self):
        return self._pollsleep

    def set_polldbsleep(self, sleep=0):
        try:
            res = float(sleep)
        except ValueError as e:
            logger.error("PLC: {plc} Unable to set polldbsleep value with '{val}' as input. Exception: {e}, TB: {tb}".format(plc=self.id, val=sleep, e=e, tb=traceback.format_exc()))
            res = 0
        logger.debug("PLC: {plc} Setting polldbsleep to: {val}".format(plc=self.id, val=res))
        self._polldbsleep = res

    def get_polldbsleep(self):
        return self._polldbsleep

    def set_pc_ready_flag_on_poll(self, val=True):
        try:
            res = int(val)
        except ValueError as e:
            logger.error("PLC: {plc} Unable to set pc_ready_flag_on_poll value with '{val}' as input. Exception: {e}, TB: {tb}".format(plc=self.id, val=val, e=e, tb=traceback.format_exc()))
            res = 0
        logger.debug("PLC: {plc} Setting pc_ready_flag_on_poll to: {val}".format(plc=self.id, val=res))
        self._pc_ready_flag_on_poll = bool(res)

    def get_pc_ready_flag_on_poll(self):
        return self._pc_ready_flag_on_poll
    
    def send_database_keepalive(self):
        """
        Sends some dummy sql query to keepalive database connection. Will be executed once in a minute. 
        """
        
        if datetime.now().second == 20:
            if self.__database_keepalive_sent == False: 
                self.database_engine.send_keepalive_query()
                self.__database_keepalive_sent = True
                logger.info("PLC: {plc}. Dummy SQL keepalive query sent.".format(plc=self.id))
        else:
            self.__database_keepalive_sent = False


class PLC(PLCBase):

    def __init__(self, ip='127.0.0.1', rack=0, slot=2, port=102, reconnect=10):
        PLCBase.__init__(self, ip, rack, slot, port, reconnect)

    def poll(self):
        for dbid in self.get_active_datablock_list():
            self.poll_db(dbid)
        # sleep for configurable amount of time.
        sleep(self._pollsleep)

    def poll_db(self, dbid):
        """
        This function will check if there's some message to be processed.
        It will take necessary actions if required.
        1. Remove missing blocks from plc
        2.1. reset pc_ready to have clean start (if set in configuration)
        2.2. Read station status from database and respond to status query message.
        2.3. Save station status to database.
        2.4. Open popup window with product details.
        2.5  Read Operator status from database and respond to operator query message.
        3. Save operations from traceability template blocks to database.
        4. sleep for configurable amount of time.
        """

        # remove block from active list if not found.
        block = self.get_db(dbid)
        if block is None:
            logger.warn("PLC: {plc} DB: {db} is missing on PLC. Removing from active block list.".format(plc=self.get_id(), db=dbid))
            self._active_data_blocks.remove(dbid)
            logger.info("PLC: {plc} Remaining active block list {list}".format(plc=self.get_id(), list=self._active_data_blocks))
            return

        if self.get_pc_ready_flag_on_poll():
            # reset pc_ready flag in case it get's accidentally changed.
            # unsafe - it may cause some race condition in special condition.
            block.set_pc_ready_flag(True)
        self.save_operation(dbid)
        self.save_status(dbid)
        self.read_status(dbid)
        self.show_product_details(dbid)
        self.read_operator_status(dbid)

        # sleep for configurable amount of time.
        sleep(self._polldbsleep)

    def read_status(self, dbid):
        block = self.get_db(dbid)
        if block is None:
            logger.warn("PLC: {plc} DB: {db} is missing on PLC. Skipping".format(plc=self.get_id(), db=dbid))
            return

        if PLC_QUERY_FLAG in block.export():
            if block.__getitem__(PLC_QUERY_FLAG):  # get the station status from db
                block.set_pc_ready_flag(False)  # set PC ready flag to False
                # body

                for field in [STATION_ID, STATION_NUMBER, STATION_STATUS, SERIAL_NUMBER, PRODUCT_TYPE]:
                    if field not in block.export():
                        logger.warning("PLC: {plc} DB: {db} is missing field {field} in block body: {body}. Message skipped. Switching off PLC_Query bit.".format(plc=self.get_id(), db=block.get_db_number(), field=field, body=block.export()))
                        block.set_plc_query_flag(False)  # switch off PLC_Query bit
                        block.set_pc_ready_flag(True)  # set PC ready flag back to true
                        return

                try:
                    data = block[PRODUCT_TYPE]
                    product_type = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    product_type = 0
                try:
                    data = block[SERIAL_NUMBER]
                    serial_number = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    serial_number = 0
                try:
                    data = block[STATION_ID]
                    station_id = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    station_id = 0
                try:
                    data = block[STATION_NUMBER]
                    station_number = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    station_number = 0
                try:
                    data = block[STATION_STATUS]
                    station_status_initial = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    station_status_initial = 0

                logger.debug("PLC: {plc} DB: {db} PT: {type} SN: {serial} trying to read status from database for station: {station}".format(plc=self.get_id(), db=block.get_db_number(), type=product_type, serial=serial_number, station=station_number))
                station_status = self.database_engine.read_status(int(product_type), int(serial_number), int(station_number))

                try:
                    status = STATION_STATUS_CODES[station_status]['result']
                except ValueError as e:
                    logger.warning("PLC: {plc} DB: {db} wrong value for status, returning undefined. Exception: {e}".format(plc=self.id, db=block.get_db_number(), e=e))
                    status = STATION_STATUS_CODES[99]['result']

                block.store_item(STATION_STATUS, station_status)
                #sleep(0.1)  # 100ms sleep requested by Marcin Kusnierz @ 24-09-2015
                # try to read data from PLC as test
                try:
                    data = block[STATION_STATUS]
                    station_status_stored = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    station_status_stored = 0

                if station_status != station_status_stored:
                    logger.error("PLC: {plc} DB: {db} PT: {type} SN: {serial} SID: {station_id} status of station ST: {station_number} from database {station_status} if different than one stored on PLC {station_status_stored} (save on PLC failed.)".format(plc=self.get_id(), db=block.get_db_number(), type=product_type, serial=serial_number, station_id=station_id, station_number=station_number, station_status=station_status, status=status, station_status_initial=station_status_initial, station_status_stored=station_status_stored))
                logger.info("PLC: {plc} DB: {db} PT: {type} SN: {serial} queried from SID: {station_id} status of station ST: {station_number} taken from database is: {station_status} ({status}). Initial/Stored Status: {station_status_initial}/{station_status_stored} ".format(plc=self.get_id(), db=block.get_db_number(), type=product_type, serial=serial_number, station_id=station_id, station_number=station_number, station_status=station_status, status=status, station_status_initial=station_status_initial, station_status_stored=station_status_stored))

                self.counter_status_message_read += 1
                block.set_plc_query_flag(False)
                block.set_pc_ready_flag(True)  # set pc_ready flag back to true

            else:
                pass
                # too verbose
                # logger.debug("PLC: %s block: %s flag '%s' idle" % (self.get_id(), block.get_db_number(), PLC_QUERY_FLAG))

    def save_status(self, dbid):
        # save the status to
        block = self.get_db(dbid)
        if block is None:
            logger.warn("PLC: {plc} DB: {db} is missing on PLC. Skipping".format(plc=self.get_id(), db=dbid))
            return

        if PLC_SAVE_FLAG in block.export():
            if block.__getitem__(PLC_SAVE_FLAG):  # get the station status from db
                block.set_pc_ready_flag(False)  # set PC ready flag to False
                # query PLC for required fields...
                for field in [STATION_ID, STATION_STATUS, SERIAL_NUMBER, PRODUCT_TYPE, PROGRAM_NAME, OPERATOR_NUMBER]:
                    if field not in block.export():
                        logger.warning("PLC: {plc} DB: {db} is missing field {field} in block body: {body}. Message skipped. Switching off PLC_Save bit".format(plc=self.get_id(), db=block.get_db_number(), field=field, body=block.export()))
                        block.set_plc_save_flag(False)
                        block.set_pc_ready_flag(True)  # set busy flag back to ready
                        return
                try:
                    data = block[PRODUCT_TYPE]
                    product_type = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    product_type = 0
                try:
                    data = block[SERIAL_NUMBER]
                    serial_number = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    serial_number = 0
                try:
                    data = block[STATION_ID]
                    station_id = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    station_id = 0
                try:
                    data = block[STATION_STATUS]
                    station_status = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    station_status = 0
                try:
                    status = STATION_STATUS_CODES[station_status]['result']
                except ValueError as e:
                    logger.warning("PLC: {plc} DB: {db} wrong value for status, returning undefined. Exception: {e}".format(plc=self.id, db=block.get_db_number(), e=e))
                    status = STATION_STATUS_CODES[99]['result']

                logger.info("PLC: {plc} DB: {db} PT: {type} SN: {serial} ST: {station} saving status: {station_status} ({status}) to database".format(plc=self.id, db=block.get_db_number(), type=product_type, serial=serial_number, station=station_id, station_status=station_status, status=status))

                # get additional data from PLC:
                try:
                    data = block[PROGRAM_NAME]
                    program_name = str(data)
                except ValueError as e:
                    logger.warning("PLC: {plc} DB: {db} wrong value for program name, returning 0. Exception: {e}".format(plc=self.id, db=block.get_db_number(), e=e))
                    program_name = 0
                try:
                    data = block[DATE_TIME]
                    date_time = str(data)
                except ValueError as e:
                    logger.warning("PLC: {plc} DB: {db} wrong value for data, returning now(). Exception: {e}".format(plc=self.id, db=block.get_db_number(), e=e))
                    date_time = str(datetime.datetime.now())

                # Operator Save flag is set special handling for electronic stamp.
                operator_number = 0
                try:
                    data = block[OPERATOR_NUMBER]
                    operator_number = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    operator_number = 0

                self.database_engine.write_status(product_type, serial_number, station_id, station_status, program_name, operator_number, date_time)
                self.counter_status_message_write += 1
                block.set_plc_save_flag(False)
                block.set_pc_ready_flag(True)  # set PC ready flag back to true
            else:
                pass
                # too verbose
                # logger.debug("PLC: %s, block: %s, flag %s idle" % (self.get_id(), block.get_db_number(), PLC_SAVE_FLAG))

    def save_operation(self, dbid):
        block = self.get_db(dbid)

        if block is None:
            logger.warn("PLC: {plc} DB: {db} is missing on PLC. Skipping".format(plc=self.get_id(), db=dbid))
            return

        if TRC_TMPL_COUNT in block.export():
            template_count = block.__getitem__(TRC_TMPL_COUNT)
            logger.debug("PLC: {plc} DB: {db} traceability template count: {count}".format(plc=self.get_id(), db=dbid, count=template_count))

            for template_number in range(0, template_count):
                pc_save_flag_name = TRC_TMPL_SAVE_FLAG.replace("__no__", str(template_number))
                operation_status_name = "body.trc.tmpl.__no__.operation_status".replace("__no__", str(template_number))
                operation_type_name = "body.trc.tmpl.__no__.operation_type".replace("__no__", str(template_number))
                program_id_name = "body.trc.tmpl.__no__.program_id".replace("__no__", str(template_number))
                date_time_name = "body.trc.tmpl.__no__.date_time".replace("__no__", str(template_number))

                result_1_name = "body.trc.tmpl.__no__.1.result".replace("__no__", str(template_number))
                result_1_max_name = "body.trc.tmpl.__no__.1.result_max".replace("__no__", str(template_number))
                result_1_min_name = "body.trc.tmpl.__no__.1.result_min".replace("__no__", str(template_number))
                result_1_status_name = "body.trc.tmpl.__no__.1.result_status".replace("__no__", str(template_number))
                result_2_name = "body.trc.tmpl.__no__.2.result".replace("__no__", str(template_number))
                result_2_max_name = "body.trc.tmpl.__no__.2.result_max".replace("__no__", str(template_number))
                result_2_min_name = "body.trc.tmpl.__no__.2.result_min".replace("__no__", str(template_number))
                result_2_status_name = "body.trc.tmpl.__no__.2.result_status".replace("__no__", str(template_number))

                if block.__getitem__(pc_save_flag_name):  # process only if PLC_Save flag is set for given template
                    # read basic data
                    # make sure that basic data is set on PLC (skip otherwise)
                    for field in [STATION_ID, SERIAL_NUMBER, PRODUCT_TYPE, PROGRAM_NAME]:
                        if field not in block.export():
                            logger.warning("PLC: {plc} DB: {db} is missing field {field} in block body: {body}. Message skipped.".format(plc=self.get_id(), db=block.get_db_number(), field=field, body=block.export()))
                            return
                    # get some basic data from data block
                    try:
                        data = block[PRODUCT_TYPE]
                        product_type = int(data)
                    except ValueError as e:
                        logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                        product_type = 0
                    try:
                        data = block[SERIAL_NUMBER]
                        serial_number = int(data)
                    except ValueError as e:
                        logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                        serial_number = 0
                    try:
                        data = block[STATION_ID]
                        station_id = int(data)
                    except ValueError as e:
                        logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                        station_id = 0
                    try:
                        data = block[program_id_name]
                        program_id = str(data)
                    except ValueError as e:
                        logger.warning("PLC: {plc} DB: {db} wrong value for program name, returning 0. Exception: {e}".format(plc=self.id, db=block.get_db_number(), e=e))
                        program_id = 0

                    # read specific data
                    operation_status = block.__getitem__(operation_status_name)
                    operation_type = block.__getitem__(operation_type_name)
                    date_time = block.__getitem__(date_time_name)

                    result_1 = block.__getitem__(result_1_name)
                    result_1_max = block.__getitem__(result_1_max_name)
                    result_1_min = block.__getitem__(result_1_min_name)
                    result_1_status = block.__getitem__(result_1_status_name)
                    result_2 = block.__getitem__(result_2_name)
                    result_2_max = block.__getitem__(result_2_max_name)
                    result_2_min = block.__getitem__(result_2_min_name)
                    result_2_status = block.__getitem__(result_2_status_name)

                    logger.info("PLC: {plc} DB: {db} PT: {type} SN: {serial} ST: {station} TN: {template_number} FN: {flag}".format(plc=self.id, db=block.get_db_number(), type=product_type, serial=serial_number, station=station_id, template_number=template_number, flag=pc_save_flag_name))

                    self.database_engine.write_operation(product_type, serial_number, station_id, operation_status, operation_type, program_id, date_time, result_1, result_1_max, result_1_min, result_1_status, result_2, result_2_max, result_2_min, result_2_status)
                    self.counter_saved_operations += 1
                    block.set_flag(pc_save_flag_name, False)  # cancel save flag:

    def show_product_details(self, dbid):
        block = self.get_db(dbid)
        if block is None:
            logger.warn("PLC: {plc} DB: {db} is missing on PLC. Skipping.".format(plc=self.get_id(), db=dbid))
            return

        if PC_OPEN_BROWSER_FLAG in block.export():
            if block.__getitem__(PC_OPEN_BROWSER_FLAG):  # get the station status from db
                block.set_pc_ready_flag(False)  # set PC ready flag to False

                try:
                    data = block[PRODUCT_TYPE]
                    product_type = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    product_type = 0
                try:
                    data = block[SERIAL_NUMBER]
                    serial_number = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    serial_number = 0
                try:
                    data = block[STATION_ID]
                    station_id = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    station_id = 0
                logger.info("PLC: {plc} ST: {station} PT: {type} SN: {serial} browser opening request - show product details.".format(plc=self.get_id(), station=station_id, type=product_type, serial=serial_number))

                url = "/".join([self.get_baseurl(), 'product', str(Product.calculate_product_id(product_type, serial_number))])
                if self.get_popups():
                    """
                    In order to open product details in same tab please reconfigure your firefox:
                    1) type about:config in firefox address bar
                    2) set browser.link.open_newwindow property to value 1
                    more info on:
                    http://kb.mozillazine.org/Browser.link.open_newwindow
                    http://superuser.com/questions/138298/force-firefox-to-open-pages-in-a-specific-tab-using-command-line
                    """

                    if webbrowser.open(url):
                        logger.info("PLC: {plc} ST: {station} URL: {url} product details window opened successfully.".format(plc=self.get_id(), station=station_id, type=product_type, serial=serial_number, url=url))
                    else:
                        logger.warning("PLC: {plc} ST: {station} URL: {url} failed to open product details window".format(plc=self.get_id(), station=station_id, type=product_type, serial=serial_number, url=url))
                else:
                    logger.warning("PLC: {plc} ST: {station} URL: {url} Popup event registered but popups are disabled by configuration.".format(plc=self.get_id(), station=station_id, type=product_type, serial=serial_number, url=url))

                self.counter_show_product_details += 1
                block.set_pc_open_browser_flag(False) # cancel PC_OPEN_BROWSER flag
                block.set_pc_ready_flag(True)  # set PC ready flag back to true
                
    def read_operator_status(self, dbid):
        block = self.get_db(dbid)
        if block is None:
            logger.warn("PLC: {plc} DB: {db} is missing on PLC. Skipping".format(plc=self.get_id(), db=dbid))
            return

        if OPERATOR_QUERY_FLAG in block.export():
            if block.operator_query_flag():  # get the operator query flag value from db
                block.set_pc_ready_flag(False)  # set PC ready flag to False
                # body

                for field in [STATION_ID, OPERATOR_NUMBER, OPERATOR_STATUS]:
                    if field not in block.export():
                        logger.warning("PLC: {plc} DB: {db} is missing field {field} in block body: {body}. Message skipped. Switching off PLC_Query bit.".format(plc=self.get_id(), db=block.get_db_number(), field=field, body=block.export()))
                        block.set_plc_query_flag(False)  # switch off PLC_Query bit
                        block.set_pc_ready_flag(True)  # set PC ready flag back to true
                        return

                try:
                    data = block[STATION_ID]
                    station_id = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    station_id = 0
                try:
                    data = block[OPERATOR_NUMBER]
                    operator_number = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    operator_number = 0
                try:
                    data = block[OPERATOR_STATUS]
                    operator_status_initial = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    operator_status_initial = 0

                logger.debug("PLC: {plc} DB: {db} SID: {station_id} trying to check operator status for OP: {operator_number}".format(plc=self.get_id(), db=block.get_db_number(), station_id=station_id, operator_number=operator_number))
                operator_status = self.database_engine.read_operator_status(int(operator_number))

                block.store_item(OPERATOR_STATUS, operator_status)

                # try to read data from PLC for a test
                try:
                    data = block[OPERATOR_STATUS]
                    operator_status_stored = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    operator_status_stored = 0

                if operator_status != operator_status_stored:
                    logger.error("PLC: {plc} DB: {db} SID: {station_id} OP: {operator_number} Operator Status from database {operator_status} if different than one stored on PLC {operator_status_stored} - save on PLC failed. (Initial was: {operator_status_initial})".format(plc=self.get_id(), db=block.get_db_number(), station_id=station_id, operator_number=operator_number, operator_status=operator_status, operator_status_initial=operator_status_initial, operator_status_stored=operator_status_stored))
                logger.info("PLC: {plc} DB: {db} SID: {station_id} OP: {operator_number} Operator Status taken from database is: {operator_status}. Initial/Stored Status: {operator_status_initial}/{operator_status_stored} ".format(plc=self.get_id(), db=block.get_db_number(), station_id=station_id, operator_number=operator_number, operator_status=operator_status, operator_status_initial=operator_status_initial, operator_status_stored=operator_status_stored))

                self.counter_operator_status_read += 1
                block.set_operator_query_flag(False)
                block.set_pc_ready_flag(True)  # set pc_ready flag back to true
                
