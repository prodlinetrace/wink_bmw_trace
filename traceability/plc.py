# this is a class of PLC controller
import snap7
import logging
import webbrowser
import traceback
from time import sleep
from datetime import datetime
#from .constants import PC_HEARTBEAT_FLAG, PLC_QUERY_FLAG, PLC_SAVE_FLAG, STATION_NUMBER, STATION_STATUS, PRODUCT_TYPE, HEAD_DETAIL_ID, STATION_STATUS_CODES, STATION_ID, TRC_TMPL_COUNT, TRC_TMPL_SAVE_FLAG, PC_OPEN_BROWSER_FLAG, DATE_TIME, PC_READY_FLAG, PROGRAM_NAME, OPERATOR_QUERY_FLAG, OPERATOR_STATUS, OPERATOR_NUMBER
from .constants import *
from .models import Product
from .blocks import DBs
from .custom_exceptions import UnknownDB
from .database import Database
from .block import Local_Status
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
                logger.info("PLC: {plc} Dummy SQL keepalive query sent.".format(plc=self.id))
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
        #self.process_id_query(dbid)
        self.save_operation(dbid)
        self.save_status(dbid)
        self.read_status(dbid)
        self.show_product_details(dbid)

        # sleep for configurable amount of time.
        sleep(self._polldbsleep)

    def process_id_query(self, dbid):
        """
            gets the next_product_id from db and saves data in HEAD_DETAIL_ID.
        """
        block = self.get_db(dbid)
        if block is None:
            logger.warn("PLC: {plc} DB: {db} is missing on PLC. Skipping".format(plc=self.get_id(), db=dbid))
            return

        if ID_QUERY_FLAG in block.export():
            if block.__getitem__(ID_QUERY_FLAG):  # ID_QUERY_FLAG is set - begin id generation processing
                block.set_id_ready_flag(False)  # set ID ready flag to False
                
                for field in [HEAD_DETAIL_ID]:
                    if field not in block.export():
                        logger.warning("PLC: {plc} DB: {db} is missing field {field} in block body: {body}. Message skipped. Switching off PLC_Query bit.".format(plc=self.get_id(), db=block.get_db_number(), field=field, body=block.export()))
                        block.set_id_query_flag(False)  # switch off ID_Query bit
                        block.set_id_ready_flag(True)  # set ID ready flag back to true
                        return

                head_detail_id_initial = block[HEAD_DETAIL_ID]

                next_product_id = self.database_engine.get_next_product_id()
                logger.info(f'PLC: {self.get_id()} DB: {block.get_db_number()} calculated next_product_id: {next_product_id}')
                
                block.store_item(HEAD_DETAIL_ID, next_product_id)
                
                # read again to verify if saved correctly
                try:
                    head_detail_id_stored = block[HEAD_DETAIL_ID]
                except ValueError as e:
                    logger.error(f'PLC: {self.get_id()} DB: {block.get_db_number()} Data read error. Input: {head_detail_id_stored} Exception: {e}')

               
                if head_detail_id_stored != next_product_id:
                    logger.error(f'PLC: {self.get_id()} DB: {block.get_db_number()} Data read error. head_detail_id from database: {next_product_id} is different than one stored on PLC: {head_detail_id_stored} (save on PLC failed.)')
                logger.info(f'PLC: {self.get_id()} DB: {block.get_db_number()} next_product_id saved in PLC memory: {next_product_id}. Initial/Stored value: {head_detail_id_initial}/{head_detail_id_stored}')

                block.set_id_query_flag(False)  # switch off ID_Query bit
                block.set_id_ready_flag(True)  # set ID ready flag back to true
                

    def read_status(self, dbid):
        block = self.get_db(dbid)
        if block is None:
            logger.warn("PLC: {plc} DB: {db} is missing on PLC. Skipping".format(plc=self.get_id(), db=dbid))
            return

        if PLC_QUERY_FLAG in block.export():
            if block.__getitem__(PLC_QUERY_FLAG):  # get the station status from db
                block.set_pc_ready_flag(False)  # set PC ready flag to False

                for field in [HEAD_STATION_ID, STATUS_STATION_NUMBER, STATUS_DATABASE_RESULT, HEAD_DETAIL_ID, HEAD_NEST_NUMBER]:
                    if field not in block.export():
                        logger.warning("PLC: {plc} DB: {db} is missing field {field} in block body: {body}. Message skipped. Switching off PLC_Query bit.".format(plc=self.get_id(), db=block.get_db_number(), field=field, body=block.export()))
                        block.set_plc_query_flag(False)  # switch off PLC_Query bit
                        block.set_pc_ready_flag(True)  # set PC ready flag back to true
                        return
                try:
                    head_detail_id = data = block[HEAD_DETAIL_ID]
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    head_detail_id = ""
                try:
                    data = block[HEAD_STATION_ID]
                    head_station_id = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    head_station_id = 0
                try:
                    data = block[STATUS_STATION_NUMBER]
                    station_number = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    station_number = 0
                try:
                    data = block[STATUS_DATABASE_RESULT]
                    station_status_initial = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    station_status_initial = 0
                try:
                    data = block[HEAD_NEST_NUMBER]
                    nest_number = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    nest_number = 0
                    
                logger.debug("PLC: {plc} DB: {db} PID: {head_detail_id} trying to read status from database for station: {station} NEST: {nest_number} ".format(plc=self.get_id(), db=block.get_db_number(), head_detail_id=head_detail_id, station=station_number, nest_number=nest_number))
                station_status = self.database_engine.read_status(head_detail_id, station_number)
                
                try:
                    status = STATION_STATUS_CODES[station_status]['result']
                except ValueError as e:
                    logger.warning("PLC: {plc} DB: {db} wrong value for status, returning undefined. Exception: {e}".format(plc=self.id, db=block.get_db_number(), e=e))
                    status = STATION_STATUS_CODES[99]['result']

                block.store_item(STATUS_DATABASE_RESULT, station_status)
                #sleep(0.1)  # 100ms sleep requested by Marcin Kusnierz @ 24-09-2015
                # try to read data from PLC as test
                try:
                    data = block[STATUS_DATABASE_RESULT]
                    station_status_stored = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    station_status_stored = 0
                
                if station_status != station_status_stored:
                    logger.error("PLC: {plc} DB: PID: {head_detail_id} SID: {head_station_id} status of station ST: {station_number} from database {station_status} if different than one stored on PLC {station_status_stored} (save on PLC failed.)".format(plc=self.get_id(), db=block.get_db_number(), head_detail_id=head_detail_id, head_station_id=head_station_id, station_number=station_number, station_status=station_status, status=status, station_status_initial=station_status_initial, station_status_stored=station_status_stored))
                logger.info("PLC: {plc} DB: {db} PID: {head_detail_id} queried from SID: {head_station_id} status of station ST: {station_number} taken from database is: {station_status} ({status}). Initial/Stored Status: {station_status_initial}/{station_status_stored} ".format(plc=self.get_id(), db=block.get_db_number(), head_detail_id=head_detail_id, head_station_id=head_station_id, station_number=station_number, station_status=station_status, status=status, station_status_initial=station_status_initial, station_status_stored=station_status_stored))

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
                # head_head_station_id=HEAD_STATION_ID, head_program_number=HEAD_PROGRAM_NUMBER, head_nest_number=HEAD_NEST_NUMBER, head_detail_id=HEAD_DETAIL_ID
                for field in [HEAD_STATION_ID, STATUS_STATION_RESULT, HEAD_DETAIL_ID, HEAD_NEST_NUMBER, HEAD_PROGRAM_NUMBER, OPERATOR_LOGIN]:
                    if field not in block.export():
                        logger.warning("PLC: {plc} DB: {db} is missing field {field} in block body: {body}. Message skipped. Switching off PLC_Save bit".format(plc=self.get_id(), db=block.get_db_number(), field=field, body=block.export()))
                        block.set_plc_save_flag(False)
                        block.set_pc_ready_flag(True)  # set busy flag back to ready
                        return
                    
                # TODO: Hack remove me once test PLC is fixed.
                #block.store_item("head.detail_id", "1125")
                try:
                    head_detail_id = data = block[HEAD_DETAIL_ID]
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    head_detail_id = ""
                try:
                    data = block[HEAD_STATION_ID]
                    head_station_id = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    head_station_id = 0
                try:
                    data = block[STATUS_STATION_RESULT]
                    station_status = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    station_status = 0
                try:
                    status = STATION_STATUS_CODES[station_status]['result']
                except ValueError as e:
                    logger.warning("PLC: {plc} DB: {db} wrong value for status, returning undefined. Exception: {e}".format(plc=self.id, db=block.get_db_number(), e=e))
                    status = STATION_STATUS_CODES[99]['result']

                logger.info("PLC: {plc} DB: {db} PID: {head_detail_id} ST: {station} saving status: {station_status} ({status}) to database".format(plc=self.id, db=block.get_db_number(), head_detail_id=head_detail_id, station=head_station_id, station_status=station_status, status=status))

                # get additional data from PLC:
                try:
                    data = block[HEAD_PROGRAM_NUMBER]
                    program_number = int(data)
                except ValueError as e:
                    logger.warning("PLC: {plc} DB: {db} wrong value for program number, returning 0. Exception: {e}".format(plc=self.id, db=block.get_db_number(), e=e))
                    program_number = 0
                try:
                    data = block[HEAD_NEST_NUMBER]
                    nest_number = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    nest_number = 0
                try:
                    data = block[STATUS_DATE_TIME]
                    date_time = str(data)
                except ValueError as e:
                    logger.warning("PLC: {plc} DB: {db} wrong value for data, returning now(). Exception: {e}".format(plc=self.id, db=block.get_db_number(), e=e))
                    date_time = str(datetime.datetime.now())
                # Operator Save flag is set special handling for electronic stamp.
                operator_id = 0
                try:
                    data = block[OPERATOR_LOGIN]
                    operator_login = str(data)
                    operator_id = self.database_engine.get_operator_by_login(operator_login)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    operator_id = 0
                self.database_engine.write_status(head_detail_id, head_station_id, station_status, program_number, nest_number, operator_id, date_time)
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
        
        # print("dbid: {dbid} type: {type}".format(dbid=dbid, type=type(dbid)))
        # logger.info("dbid: {dbid} type: {type}".format(dbid=dbid, type=type(dbid)))
        
        # read data - just hardcode and read whatever is needed.
        # save it to database afterwards.  
        
        if dbid in [500, 800]:
            self.process_UDT83(dbid) 
        
        if dbid in [501, 502, 801, 802]:
            self.process_UDT84(dbid) 
        
        if dbid in [503, 504, 803, 804]:
            self.process_UDT85(dbid)
            
        if dbid in [505, 506, 805, 806]:
            self.process_UDT88(dbid) 

    def process_UDT83(self, dbid):
        """
        Laser marking station handling.
        """
        logger.debug("UDT83 dbid: {dbid} type: {type}".format(dbid=dbid, type=type(dbid)))
        block = self.get_db(dbid)
        if block is None:
            logger.warn(f'PLC: {self.get_id()} DB: {dbid} is missing on PLC. Skipping')
            return

        # Read some global data BEGIN
        detail_id = block[HEAD_DETAIL_ID]
        station_id = int(block[HEAD_STATION_ID])
        station_status = int(block[STATUS_STATION_RESULT])
        program_number = int(block[HEAD_PROGRAM_NUMBER])
        nest_number = int(block[HEAD_NEST_NUMBER])
        date_time = str(block[STATUS_DATE_TIME])
        # Read some global data END       

        if ID_QUERY_FLAG in block.export():
            """
            gets the next_product_id from db and saves data in HEAD_DETAIL_ID.
            """
            if block.__getitem__(ID_QUERY_FLAG):  # ID_QUERY_FLAG is set - begin id generation processing
                block.set_id_ready_flag(False)  # set ID ready flag to False
                
                for field in [HEAD_DETAIL_ID]:
                    if field not in block.export():
                        logger.warning("PLC: {plc} DB: {db} is missing field {field} in block body: {body}. Message skipped. Switching off PLC_Query bit.".format(plc=self.get_id(), db=block.get_db_number(), field=field, body=block.export()))
                        block.set_id_query_flag(False)  # switch off ID_Query bit
                        block.set_id_ready_flag(True)  # set ID ready flag back to true
                        return

                head_detail_id_initial = block[HEAD_DETAIL_ID]

                next_product_id = self.database_engine.get_next_product_id()
                logger.info(f'PLC: {self.get_id()} DB: {block.get_db_number()} calculated next_product_id: {next_product_id}')
                
                block.store_item(HEAD_DETAIL_ID, next_product_id)
                
                # read again to verify if saved correctly
                try:
                    head_detail_id_stored = block[HEAD_DETAIL_ID]
                except ValueError as e:
                    logger.error(f'PLC: {self.get_id()} DB: {block.get_db_number()} Data read error. Input: {head_detail_id_stored} Exception: {e}')

               
                if head_detail_id_stored != next_product_id:
                    logger.error(f'PLC: {self.get_id()} DB: {block.get_db_number()} Data read error. head_detail_id from database: {next_product_id} is different than one stored on PLC: {head_detail_id_stored} (save on PLC failed.)')
                logger.info(f'PLC: {self.get_id()} DB: {block.get_db_number()} next_product_id saved in PLC memory: {next_product_id}. Initial/Stored value: {head_detail_id_initial}/{head_detail_id_stored}')

                block.set_id_query_flag(False)  # switch off ID_Query bit
                block.set_id_ready_flag(True)  # set ID ready flag back to true

        """
        check and verify what has been burned by DMC marking laser.
        """
        LaserMarking_LaserProgramName = block.get("LaserMarking.LaserProgramName")
        LaserMarking_id = block.get("LaserMarking.id")  # id to be burned by laser
        LaserMarking_status = Local_Status("LaserMarking", block)

        LaserMarkingVerification_id = block.get("LaserMarkingVerification.id")   # id read by DMC scanner after burning
        LaserMarkingVerification_status = Local_Status("LaserMarkingVerification", block)


        if LaserMarking_status.active and LaserMarking_status.database_save:
            local_status = LaserMarking_status
            logger.info(f"PLC: {self.id} dbid: {dbid} block: {block} detail_id: {detail_id} LaserMarking active_flag: {local_status.active} database_save_flag: {local_status.database_save} date_time: {local_status.date_time} result: {local_status.result}")
            
            operation_type = 501  # hardcoded operation_id value 501 - scanner burn
            if LaserMarking_id == head_detail_id:
                operation_status = 1   # scanner read OK
            else:
                operation_status = 2   # scanner read NOK

            results = [
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 1,
                    'value': LaserMarking_id, 
                }
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, local_status.date_time, results)
            # mark item as read
            local_status.set_database_save(0)

        if LaserMarkingVerification_status.active and LaserMarkingVerification_status.database_save: 
            local_status = LaserMarking_status
            logger.info(f"PLC: {self.id} dbid: {dbid} block: {block} detail_id: {detail_id} LaserMarkingVerification active_flag: {local_status.active} database_save_flag: {local_status.database_save} date_time: {local_status.date_time} result: {local_status.result}")
            
            operation_type = 502  # hardcoded operation_id value 502 - scanner burn verification
            if LaserMarkingVerification_id == LaserMarking_id:
                operation_status = 1   # scanner read OK
            else:
                operation_status = 2   # scanner read NOK

            results = [
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 1,
                    'value': LaserMarkingVerification_id, 
                }
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, local_status.date_time, results)
            # mark item as read
            local_status.set_database_save(0)

    def process_UDT84(self, dbid):
        logger.debug(f'Processing UDT84 PLC: {self.get_id()} DB: {dbid} type: {type(dbid)}')
        block = self.get_db(dbid)
        if block is None:
            logger.warn(f'PLC: {self.get_id()} DB: {dbid} is missing on PLC. Skipping')
            return

        # TODO remove once scanner is active
        head_detail_id = block.get("head.detail_id")
        block.store_item("ReadID.id", head_detail_id)  # overwrite value read by scanner. 

        ReadID_id = block.get("ReadID.id")
        ReadID_status = Local_Status("ReadID", block)
        logger.debug("dbid: {dbid} block: {block} ReadID: {ReadID} ReadID_Status_Active: {ReadID_Status_Active} ReadID_Status_DatabaseSave: {ReadID_Status_DatabaseSave} ReadID_Status_date_time: {ReadID_Status_date_time} ReadID_Status_result: {ReadID_Status_result}".format(dbid=dbid, block=block, ReadID=ReadID_id, ReadID_Status_Active=ReadID_status.active, ReadID_Status_DatabaseSave=ReadID_status.database_save, ReadID_Status_date_time=ReadID_status.date_time, ReadID_Status_result=ReadID_status.result))

        # Read some global data BEGIN
        detail_id = block[HEAD_DETAIL_ID]
        station_id = int(block[HEAD_STATION_ID])
        station_status = int(block[STATUS_STATION_RESULT])
        program_number = int(block[HEAD_PROGRAM_NUMBER])
        nest_number = int(block[HEAD_NEST_NUMBER])
        date_time = str(block[STATUS_DATE_TIME])
        # Read some global data END        

        if ReadID_status.active and ReadID_status.database_save: 
            local_status = ReadID_status
            logger.info(f"PLC: {self.id} dbid: {dbid} block: {block} detail_id: {detail_id} ReadID active_flag: {local_status.active} database_save_flag: {local_status.database_save} date_time: {local_status.date_time} result: {local_status.result}")
            
            operation_type = 101  # hardcoded operation_id value 101 - scanner read
            if ReadID_id == head_detail_id:
                operation_status = 1   # scanner read OK
            else:
                operation_status = 2   # scanner read NOK

            results = [
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 1,
                    'value': ReadID_id, 
                }
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, local_status.date_time, results)
            # mark item as read
            local_status.set_database_save(0)
            

        SensorOiling_done = block.get("SensorOiling.done")
        SensorOiling_status = Local_Status("SensorOiling", block)
        if SensorOiling_status.active and SensorOiling_status.database_save: 
            operation_type = 102  # hardcoded operation_id value 102 - SensorOiling_done
            operation_status = int(SensorOiling_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 4,
                    'unit_id': 99,
                    'desc_id': operation_type * 100 + 1,
                    'value': SensorOiling_done, 
                }
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, SensorOiling_status.date_time, results)
            # mark item as read
            SensorOiling_status.set_database_save(0)



        ManualSensorMounting_done = block.get("ManualSensorMounting.done")
        ManualSensorMounting_status = Local_Status("ManualSensorMounting", block)
        if ManualSensorMounting_status.active and ManualSensorMounting_status.database_save: 
            operation_type = 103  # hardcoded operation_id value 103 - ManualSensorMounting_done
            operation_status = int(ManualSensorMounting_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 4,
                    'unit_id': 99,
                    'desc_id': operation_type * 100 + 1,
                    'value': ManualSensorMounting_done, 
                }
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, ManualSensorMounting_status.date_time, results)
            # mark item as read
            ManualSensorMounting_status.set_database_save(0)


        SensorDMC_reference = block.get("SensorDMC.reference")
        SensorDMC_read = block.get("SensorDMC.read")
        SensorDMC_compare = block.get("SensorDMC.compare")
        SensorDMC_from_string_sign = block.get("SensorDMC.from_string_sign")
        SensorDMC_string_length = block.get("SensorDMC.string_length")
        SensorDMC_sensor_type = block.get("SensorDMC.sensor_type")
        SensorDMC_status = Local_Status("SensorDMC", block)
        if SensorDMC_status.active and SensorDMC_status.database_save: 
            operation_type = 104  # hardcoded operation_id value 104
            operation_status = int(SensorDMC_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 1,
                    'value': SensorDMC_reference, 
                },
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 2,
                    'value': SensorDMC_read, 
                },
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 3,
                    'value': SensorDMC_compare, 
                },
                {
                    'type_id': 2,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 4,
                    'value': SensorDMC_from_string_sign, 
                },
                {
                    'type_id': 2,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 5,
                    'value': SensorDMC_string_length, 
                },
                {
                    'type_id': 2,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 6,
                    'value': SensorDMC_sensor_type, 
                },                       
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, SensorDMC_status.date_time, results)
            # mark item as read
            SensorDMC_status.set_database_save(0)

        AutomaticSensorMounting_screwdriver_program_number = block.get("AutomaticSensorMounting.screwdriver_program_number")
        AutomaticSensorMounting_torque = block.get("AutomaticSensorMounting.torque")
        AutomaticSensorMounting_angle = block.get("AutomaticSensorMounting.angle")
        AutomaticSensorMounting_torque_max = block.get("AutomaticSensorMounting.torque_max")
        AutomaticSensorMounting_torque_min = block.get("AutomaticSensorMounting.torque_min")        
        AutomaticSensorMounting_angle_max = block.get("AutomaticSensorMounting.angle_max")        
        AutomaticSensorMounting_angle_min = block.get("AutomaticSensorMounting.angle_min")        
        AutomaticSensorMounting_status = Local_Status("AutomaticSensorMounting", block)
        if AutomaticSensorMounting_status.active and AutomaticSensorMounting_status.database_save: 
            operation_type = 105  # hardcoded operation_id value 105
            operation_status = int(AutomaticSensorMounting_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 2,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 1,
                    'value': AutomaticSensorMounting_screwdriver_program_number, 
                },
                {
                    'type_id': 3,
                    'unit_id': 2,
                    'desc_id': operation_type * 100 + 2,
                    'value': AutomaticSensorMounting_torque, 
                },
                {
                    'type_id': 3,
                    'unit_id': 3,
                    'desc_id': operation_type * 100 + 3,
                    'value': AutomaticSensorMounting_angle, 
                },
                {
                    'type_id': 3,
                    'unit_id': 2,
                    'desc_id': operation_type * 100 + 4,
                    'value': AutomaticSensorMounting_torque_max, 
                },
                {
                    'type_id': 3,
                    'unit_id': 2,
                    'desc_id': operation_type * 100 + 5,
                    'value': AutomaticSensorMounting_torque_min, 
                },
                {
                    'type_id': 3,
                    'unit_id': 3,
                    'desc_id': operation_type * 100 + 6,
                    'value': AutomaticSensorMounting_angle_max, 
                },
                {
                    'type_id': 3,
                    'unit_id': 3,
                    'desc_id': operation_type * 100 + 7,
                    'value': AutomaticSensorMounting_angle_min, 
                },
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, AutomaticSensorMounting_status.date_time, results)
            # mark item as read
            AutomaticSensorMounting_status.set_database_save(0)

    def process_UDT85(self, dbid):
        logger.debug(f'Processing UDT85 PLC: {self.get_id()} DB: {dbid} type: {type(dbid)}')
        block = self.get_db(dbid)
        if block is None:
            logger.warn(f'PLC: {self.get_id()} DB: {dbid} is missing on PLC. Skipping')
            return

        # TODO remove once scanner is active
        head_detail_id = block.get("head.detail_id")
        block.store_item("ReadID.id", head_detail_id)  # overwrite value read by scanner. 
        
        ReadID_id = block.get("ReadID.id")
        ReadID_status = Local_Status("ReadID", block)
        
        # Read some global data BEGIN
        detail_id = block[HEAD_DETAIL_ID]
        station_id = int(block[HEAD_STATION_ID])
        station_status = int(block[STATUS_STATION_RESULT])
        program_number = int(block[HEAD_PROGRAM_NUMBER])
        nest_number = int(block[HEAD_NEST_NUMBER])
        date_time = str(block[STATUS_DATE_TIME])
        # Read some global data END        
        
        if ReadID_status.active and ReadID_status.database_save: 
            logger.info("PLC: {plc} dbid: {dbid} block: {block} ReadID: {ReadID} ReadID_Status_Active: {ReadID_Status_Active} ReadID_Status_DatabaseSave: {ReadID_Status_DatabaseSave} ReadID_Status_date_time: {ReadID_Status_date_time} ReadID_Status_result: {ReadID_Status_result}".format(plc=self.id, dbid=dbid, block=block, ReadID=ReadID_id, ReadID_Status_Active=ReadID_status.active, ReadID_Status_DatabaseSave=ReadID_status.database_save, ReadID_Status_date_time=ReadID_status.date_time, ReadID_Status_result=ReadID_status.result))
            #logger.info("PLC: {plc} DB: {db} PID: {head_detail_id} ST: {station} TN: {template_number} FN: {flag}".format(plc=self.id, db=block.get_db_number(), head_detail_id=head_detail_id, station=head_station_id, template_number=template_number, flag=pc_save_flag_name))
            
            operation_type = 201  # hardcoded operation_id value 201 - scanner read
            if ReadID_id == head_detail_id:
                operation_status = 1   # scanner read OK
            else:
                operation_status = 2   # scanner read NOK
            results = [
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 1,
                    'value': ReadID_id, 
                }
            ]

            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, ReadID_status.date_time, results)
            # mark item as read
            ReadID_status.set_database_save(0)
            
        Teilabfrage_done = block.get("Teilabfrage.done")
        Teilabfrage_status = Local_Status("Teilabfrage", block)
        if Teilabfrage_status.active and Teilabfrage_status.database_save: 
        #if Teilabfrage_status.database_save:
            operation_type = 202  # hardcoded operation_id value 202 - Teilabfrage_done
            operation_status = int(Teilabfrage_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 4,
                    'unit_id': 99,
                    'desc_id': operation_type * 100 + 1,
                    'value': Teilabfrage_done, 
                }
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, Teilabfrage_status.date_time, results)
            # mark item as read
            Teilabfrage_status.set_database_save(0)

        Nadelpruefung_done = block.get("Nadelpruefung.done")
        Nadelpruefung_status = Local_Status("Nadelpruefung", block)
        if Nadelpruefung_status.active and Nadelpruefung_status.database_save:
        #if Nadelpruefung_status.database_save:
            operation_type = 203  # hardcoded operation_id value 203 - Nadelpruefung_done
            operation_status = int(Nadelpruefung_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 4,
                    'unit_id': 99,
                    'desc_id': operation_type * 100 + 1,
                    'value': Nadelpruefung_done, 
                }
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, Nadelpruefung_status.date_time, results)
            # mark item as read
            Nadelpruefung_status.set_database_save(0)        

        Mutternabfrage_done = block.get("Mutternabfrage.done")
        Mutternabfrage_status = Local_Status("Mutternabfrage", block)
        if Mutternabfrage_status.active and Mutternabfrage_status.database_save:
            operation_type = 204  # hardcoded operation_id value 204 - Mutternabfrage_done
            operation_status = int(Mutternabfrage_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 4,
                    'unit_id': 99,
                    'desc_id': operation_type * 100 + 1,
                    'value': Mutternabfrage_done, 
                }
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, Mutternabfrage_status.date_time, results)
            # mark item as read
            Mutternabfrage_status.set_database_save(0)     

        Kreismarkierer_done = block.get("Kreismarkierer.done")
        Kreismarkierer_servomotor_number = block.get("Kreismarkierer.servomotor_number")
        Kreismarkierer_marking_time = block.get("Kreismarkierer.marking_time")
        Kreismarkierer_status = Local_Status("Kreismarkierer", block)
        if Kreismarkierer_status.active and Kreismarkierer_status.database_save:
            operation_type = 205  # hardcoded operation_id value 205 - Kreismarkierer_done
            operation_status = int(Kreismarkierer_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 4,
                    'unit_id': 99,
                    'desc_id': operation_type * 100 + 1,
                    'value': Kreismarkierer_done, 
                },
                {
                    'type_id': 2,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 2,
                    'value': Kreismarkierer_servomotor_number, 
                },
                {
                    'type_id': 3,
                    'unit_id': 30,
                    'desc_id': operation_type * 100 + 3,
                    'value': Kreismarkierer_marking_time, 
                },
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, Kreismarkierer_status.date_time, results)
            # mark item as read
            Kreismarkierer_status.set_database_save(0)             
        
        Durchflusspruefung_done = block.get("Durchflusspruefung.done")
        Durchflusspruefung_status = Local_Status("Durchflusspruefung", block)
        if Durchflusspruefung_status.active and Durchflusspruefung_status.database_save: 
            operation_type = 206  # hardcoded operation_id value 206 - Durchflusspruefung_done
            operation_status = int(Durchflusspruefung_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 4,
                    'unit_id': 99,
                    'desc_id': operation_type * 100 + 1,
                    'value': Durchflusspruefung_done, 
                }
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, Durchflusspruefung_status.date_time, results)
            # mark item as read
            Durchflusspruefung_status.set_database_save(0)

        SchemaParams_P_He_vor_PT_REAL = block.get("SchemaParams.P_He_vor_PT_REAL")
        SchemaParams_P_He_Versorgung_REAL = block.get("SchemaParams.P_He_Versorgung_REAL") 
        SchemaParams_P_Vac_PT_REAL = block.get("SchemaParams.P_Vac_PT_REAL")
        SchemaParams_P_He_nach_PT_REAL = block.get("SchemaParams.P_He_nach_PT_REAL")
        SchemaParams_Leckrate = block.get("SchemaParams.Leckrate")
        SchemaParams_P_Glocke_REAL = block.get("SchemaParams.P_Glocke_REAL")
        SchemaParams_Roh_Mittel_Mul_Faktor = block.get("SchemaParams.Roh_Mittel_Mul_Faktor")
        SchemaParams_status = Local_Status("SchemaParams", block)

        if SchemaParams_status.active and SchemaParams_status.database_save: 
            operation_type = 207  # hardcoded operation_id value 207 - SchemaParams_status
            operation_status = int(SchemaParams_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 3,
                    'unit_id': 8,
                    'desc_id': operation_type * 100 + 1,
                    'value': SchemaParams_P_He_vor_PT_REAL,
                },
                {
                    'type_id': 3,
                    'unit_id': 8,
                    'desc_id': operation_type * 100 + 2,
                    'value': SchemaParams_P_He_Versorgung_REAL, 
                },
                {
                    'type_id': 3,
                    'unit_id': 9,
                    'desc_id': operation_type * 100 + 3,
                    'value': SchemaParams_P_Vac_PT_REAL, 
                },
                {
                    'type_id': 3,
                    'unit_id': 8,
                    'desc_id': operation_type * 100 + 4,
                    'value': SchemaParams_P_He_nach_PT_REAL, 
                },
                {
                    'type_id': 3,
                    'unit_id': 7,
                    'desc_id': operation_type * 100 + 5,
                    'value': SchemaParams_Leckrate, 
                },
                {
                    'type_id': 3,
                    'unit_id': 9,
                    'desc_id': operation_type * 100 + 6,
                    'value': SchemaParams_P_Glocke_REAL, 
                },
                {
                    'type_id': 3,
                    'unit_id': 7,
                    'desc_id': operation_type * 100 + 7,
                    'value': SchemaParams_Roh_Mittel_Mul_Faktor, 
                },
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, SchemaParams_status.date_time, results)
            # mark item as read
            SchemaParams_status.set_database_save(0)

        PresetParams_GloVacGrob_Soll = block.get("PresetParams.GloVacGrob_Soll")
        PresetParams_GloVacFein_Soll = block.get("PresetParams.GloVacFein_Soll")
        PresetParams_GloVacGrob = block.get("PresetParams.GloVacGrob")
        PresetParams_GloVacFein = block.get("PresetParams.GloVacFein")
        PresetParams_PtVac_Atmos_Soll_1 = block.get("PresetParams.PtVac_Atmos_Soll_1")
        PresetParams_PtVac_He_Soll_1 = block.get("PresetParams.PtVac_He_Soll_1")
        PresetParams_PT_evakuieren_Atmos = block.get("PresetParams.PT_evakuieren_Atmos")
        PresetParams_PT_evakuieren_Helium = block.get("PresetParams.PT_evakuieren_Helium")
        PresetParams_PT_fluten_1 = block.get("PresetParams.PT_fluten_1")
        PresetParams_Helium_Min_1 = block.get("PresetParams.Helium_Min_1")
        PresetParams_Helium_Soll_1 = block.get("PresetParams.Helium_Soll_1")
        PresetParams_HeliumFuellen = block.get("PresetParams.HeliumFuellen")
        PresetParams_Helium_entspannen_HD = block.get("PresetParams.Helium_entspannen_HD")
        PresetParams_FrgHeliumEvakuieren = block.get("PresetParams.FrgHeliumEvakuieren")
        PresetParams_CzasZapowietrzaniaKomory = block.get("PresetParams.CzasZapowietrzaniaKomory")
        PresetParams_CisnienieZapowietrzaniaKomory = block.get("PresetParams.CisnienieZapowietrzaniaKomory")
        PresetParams_BuzzerTime = block.get("PresetParams.BuzzerTime")
        PresetParams_Prueffreigabe = block.get("PresetParams.Prueffreigabe")
        PresetParams_Doppel_WT = block.get("PresetParams.Doppel_WT")
        PresetParams_status = Local_Status("PresetParams", block)
        if PresetParams_status.active and PresetParams_status.database_save: 
            operation_type = 208  # hardcoded operation_id value 208 - PresetParams_status
            operation_status = int(PresetParams_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 3,
                    'unit_id': 8,
                    'desc_id': operation_type * 100 + 1,
                    'value': PresetParams_GloVacGrob_Soll,
                },
                {
                    'type_id': 3,
                    'unit_id': 8,
                    'desc_id': operation_type * 100 + 2,
                    'value': PresetParams_GloVacFein_Soll,
                },
                {
                    'type_id': 3,
                    'unit_id': 30,
                    'desc_id': operation_type * 100 + 3,
                    'value': PresetParams_GloVacGrob,
                },
                {
                    'type_id': 3,
                    'unit_id': 30,
                    'desc_id': operation_type * 100 + 4,
                    'value': PresetParams_GloVacFein,
                },
                {
                    'type_id': 3,
                    'unit_id': 9,
                    'desc_id': operation_type * 100 + 5,
                    'value': PresetParams_PtVac_Atmos_Soll_1,
                },
                {
                    'type_id': 3,
                    'unit_id': 9,
                    'desc_id': operation_type * 100 + 6,
                    'value': PresetParams_PtVac_He_Soll_1,
                },
                {
                    'type_id': 3,
                    'unit_id': 30,
                    'desc_id': operation_type * 100 + 7,
                    'value': PresetParams_PT_evakuieren_Atmos,
                },
                {
                    'type_id': 3,
                    'unit_id': 30,
                    'desc_id': operation_type * 100 + 8,
                    'value': PresetParams_PT_evakuieren_Helium,
                },
                {
                    'type_id': 3,
                    'unit_id': 30,
                    'desc_id': operation_type * 100 + 9,
                    'value': PresetParams_PT_fluten_1,
                },
                {
                    'type_id': 3,
                    'unit_id': 8,
                    'desc_id': operation_type * 100 + 10,
                    'value': PresetParams_Helium_Min_1,
                },
                {
                    'type_id': 3,
                    'unit_id': 8,
                    'desc_id': operation_type * 100 + 11,
                    'value': PresetParams_Helium_Soll_1,
                },
                {
                    'type_id': 3,
                    'unit_id': 30,
                    'desc_id': operation_type * 100 + 12,
                    'value': PresetParams_HeliumFuellen,
                },
                {
                    'type_id': 3,
                    'unit_id': 30,
                    'desc_id': operation_type * 100 + 13,
                    'value': PresetParams_Helium_entspannen_HD,
                },
                {
                    'type_id': 3,
                    'unit_id': 8,
                    'desc_id': operation_type * 100 + 14,
                    'value': PresetParams_FrgHeliumEvakuieren,
                },
                {
                    'type_id': 2,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 15,
                    'value': PresetParams_Prueffreigabe,
                },
                {
                    'type_id': 4,
                    'unit_id': 99,
                    'desc_id': operation_type * 100 + 16,
                    'value': PresetParams_Doppel_WT,
                },
                {
                    'type_id': 3,
                    'unit_id': 30,
                    'desc_id': operation_type * 100 + 17,
                    'value': PresetParams_CzasZapowietrzaniaKomory,
                },
                {
                    'type_id': 3,
                    'unit_id': 9,
                    'desc_id': operation_type * 100 + 18,
                    'value': PresetParams_CisnienieZapowietrzaniaKomory,
                },
                {
                    'type_id': 3,
                    'unit_id': 30,
                    'desc_id': operation_type * 100 + 19,
                    'value': PresetParams_BuzzerTime,
                },                
           ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, PresetParams_status.date_time, results)
            # mark item as read
            PresetParams_status.set_database_save(0)

        UeberwachGroblBeGlocEvak_done = block.get("UeberwachGroblBeGlocEvak.done")
        UeberwachGroblBeGlocEvak_status = Local_Status("UeberwachGroblBeGlocEvak", block)
        if UeberwachGroblBeGlocEvak_status.active and UeberwachGroblBeGlocEvak_status.database_save: 
            operation_type = 209  # hardcoded operation_id value 209 - UeberwachGroblBeGlocEvak_done
            operation_status = int(UeberwachGroblBeGlocEvak_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 4,
                    'unit_id': 99,
                    'desc_id': operation_type * 100 + 1,
                    'value': UeberwachGroblBeGlocEvak_done, 
                }
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, UeberwachGroblBeGlocEvak_status.date_time, results)
            # mark item as read
            UeberwachGroblBeGlocEvak_status.set_database_save(0)

        UeberwachGroblBeHeliumfu_done = block.get("UeberwachGroblBeHeliumfu.done")
        UeberwachGroblBeHeliumfu_status = Local_Status("UeberwachGroblBeHeliumfu", block)
        if UeberwachGroblBeHeliumfu_status.active and UeberwachGroblBeHeliumfu_status.database_save: 
            operation_type = 210  # hardcoded operation_id value 210 - UeberwachGroblBeHeliumfu_done
            operation_status = int(UeberwachGroblBeHeliumfu_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 4,
                    'unit_id': 99,
                    'desc_id': operation_type * 100 + 1,
                    'value': UeberwachGroblBeHeliumfu_done, 
                }
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, UeberwachGroblBeHeliumfu_status.date_time, results)
            # mark item as read
            UeberwachGroblBeHeliumfu_status.set_database_save(0)

        Leckrate_leak_result = block.get("Leckrate.leak_result")
        Leckrate_leak_max = block.get("Leckrate.leak_max")
        Leckrate_leak_Max_Mantisse_REZ = block.get("Leckrate.leak_Max_Mantisse_REZ")
        Leckrate_leak_Max_Exponent_REZ = block.get("Leckrate.leak_Max_Exponent_REZ")
        Leckrate_leak_Grobleck = block.get("Leckrate.leak_Grobleck")
        Leckrate_leak_Mantisse_Grob_REZ = block.get("Leckrate.leak_Mantisse_Grob_REZ")
        Leckrate_leak_Exponent_Grob_REZ = block.get("Leckrate.leak_Exponent_Grob_REZ")
        Leckrate_leak_UebernahmeLeckrate = block.get("Leckrate.leak_UebernahmeLeckrate")
        Leckrate_status = Local_Status("Leckrate", block)
        if Leckrate_status.active and Leckrate_status.database_save: 
            operation_type = 211  # hardcoded operation_id value 211 - Leckrate_leak
            operation_status = int(Leckrate_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 3,
                    'unit_id': 7,
                    'desc_id': operation_type * 100 + 1,
                    'value': Leckrate_leak_result,
                },
                {
                    'type_id': 3,
                    'unit_id': 7,
                    'desc_id': operation_type * 100 + 2,
                    'value': Leckrate_leak_max, 
                },
                {
                    'type_id': 3,
                    'unit_id': 7,
                    'desc_id': operation_type * 100 + 3,
                    'value': Leckrate_leak_Max_Mantisse_REZ, 
                },
                {
                    'type_id': 3,
                    'unit_id': 7,
                    'desc_id': operation_type * 100 + 4,
                    'value': Leckrate_leak_Max_Exponent_REZ, 
                },
                {
                    'type_id': 3,
                    'unit_id': 7,
                    'desc_id': operation_type * 100 + 5,
                    'value': Leckrate_leak_Grobleck, 
                },
                {
                    'type_id': 3,
                    'unit_id': 7,
                    'desc_id': operation_type * 100 + 6,
                    'value': Leckrate_leak_Mantisse_Grob_REZ, 
                },
                {
                    'type_id': 3,
                    'unit_id': 7,
                    'desc_id': operation_type * 100 + 7,
                    'value': Leckrate_leak_Exponent_Grob_REZ, 
                },
                {
                    'type_id': 3,
                    'unit_id': 30,
                    'desc_id': operation_type * 100 + 8,
                    'value': Leckrate_leak_UebernahmeLeckrate, 
                },
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, Leckrate_status.date_time, results)
            # mark item as read
            Leckrate_status.set_database_save(0)

    def process_UDT88(self, dbid):
        logger.debug(f'Processing UDT88 PLC: {self.get_id()} DB: {dbid} type: {type(dbid)}')
        block = self.get_db(dbid)
        if block is None:
            logger.warn(f'PLC: {self.get_id()} DB: {dbid} is missing on PLC. Skipping')
            return        

        # TODO remove once scanner is active
        head_detail_id = block.get("head.detail_id")
        block.store_item("ReadID.id", head_detail_id)  # overwrite value read by scanner. 

        # Read some global data BEGIN
        detail_id = block[HEAD_DETAIL_ID]
        station_id = int(block[HEAD_STATION_ID])
        station_status = int(block[STATUS_STATION_RESULT])
        program_number = int(block[HEAD_PROGRAM_NUMBER])
        nest_number = int(block[HEAD_NEST_NUMBER])
        date_time = str(block[STATUS_DATE_TIME])
        # Read some global data END        

        ReadID_id = block.get("ReadID.id")
        ReadID_status = Local_Status("ReadID", block)
        logger.debug("dbid: {dbid} block: {block} ReadID: {ReadID} ReadID_Status_Active: {ReadID_Status_Active} ReadID_Status_DatabaseSave: {ReadID_Status_DatabaseSave} ReadID_Status_date_time: {ReadID_Status_date_time} ReadID_Status_result: {ReadID_Status_result}".format(dbid=dbid, block=block, ReadID=ReadID_id, ReadID_Status_Active=ReadID_status.active, ReadID_Status_DatabaseSave=ReadID_status.database_save, ReadID_Status_date_time=ReadID_status.date_time, ReadID_Status_result=ReadID_status.result))
        if ReadID_status.active and ReadID_status.database_save: 
            logger.info("PLC: {plc} dbid: {dbid} block: {block} ReadID: {ReadID} ReadID_Status_Active: {ReadID_Status_Active} ReadID_Status_DatabaseSave: {ReadID_Status_DatabaseSave} ReadID_Status_date_time: {ReadID_Status_date_time} ReadID_Status_result: {ReadID_Status_result}".format(plc=self.id, dbid=dbid, block=block, ReadID=ReadID_id, ReadID_Status_Active=ReadID_status.active, ReadID_Status_DatabaseSave=ReadID_status.database_save, ReadID_Status_date_time=ReadID_status.date_time, ReadID_Status_result=ReadID_status.result))
            
            operation_type = 301  # hardcoded operation_id value 301 - scanner read
            if ReadID_id == head_detail_id:
                operation_status = 1   # scanner read OK
            else:
                operation_status = 2   # scanner read NOK
            results = [
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 1,
                    'value': ReadID_id, 
                }
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, ReadID_status.date_time, results)
            # mark item as read
            ReadID_status.set_database_save(0)

        Tool_name = block.get("Tool.name")
        Tool_status = Local_Status("Tool", block)
        if Tool_status.active and Tool_status.database_save: 
            operation_type = 302  # hardcoded operation_id value 302 - Tool_name
            operation_status = int(Tool_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 1,
                    'value': Tool_name, 
                }
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, Tool_status.date_time, results)
            # mark item as read
            Tool_status.set_database_save(0)

        Detection_name = block.get("Detection.name")
        Detection_status = Local_Status("Detection", block)
        if Detection_status.active and Detection_status.database_save: 
            operation_type = 303  # hardcoded operation_id value 303 - Detection_status
            operation_status = int(Detection_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 1,
                    'value': Detection_name, 
                }
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, Detection_status.date_time, results)
            # mark item as read
            Detection_status.set_database_save(0)

        VendorDMCCodeMarking_laser_program_name = block.get("VendorDMCCodeMarking.laser_program_name")
        VendorDMCCodeMarking_laser_program_filename = block.get("VendorDMCCodeMarking.laser_program_filename")
        VendorDMCCodeMarking_laser_program_number = block.get("VendorDMCCodeMarking.laser_program_number")
        VendorDMCCodeMarking_status = Local_Status("VendorDMCCodeMarking", block)
        if VendorDMCCodeMarking_status.active and VendorDMCCodeMarking_status.database_save: 
            operation_type = 304  # hardcoded operation_id value 304 - VendorDMCCodeMarking_status
            operation_status = int(VendorDMCCodeMarking_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 1,
                    'value': VendorDMCCodeMarking_laser_program_name, 
                },
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 2,
                    'value': VendorDMCCodeMarking_laser_program_filename, 
                },
                {
                    'type_id': 2,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 3,
                    'value': VendorDMCCodeMarking_laser_program_number, 
                },
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, VendorDMCCodeMarking_status.date_time, results)
            # mark item as read
            VendorDMCCodeMarking_status.set_database_save(0)

        VendorDMCCodeRead_vendor_dmc = block.get("VendorDMCCodeRead.vendor_dmc")
        VendorDMCCodeRead_dmc_position = block.get("VendorDMCCodeRead.dmc_position")
        VendorDMCCodeRead_status = Local_Status("VendorDMCCodeRead", block)
        if VendorDMCCodeRead_status.active and VendorDMCCodeRead_status.database_save: 
            operation_type = 305  # hardcoded operation_id value 305- VendorDMCCodeRead_status
            operation_status = int(VendorDMCCodeRead_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 1,
                    'value': VendorDMCCodeRead_vendor_dmc, 
                },
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 2,
                    'value': VendorDMCCodeRead_dmc_position, 
                },
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, VendorDMCCodeRead_status.date_time, results)
            # mark item as read
            VendorDMCCodeRead_status.set_database_save(0)

        VendorDMCCodeClass_CodeClass = block.get("VendorDMCCodeClass.CodeClass")
        VendorDMCCodeClass_Modulation = block.get("VendorDMCCodeClass.Modulation")
        VendorDMCCodeClass_FixedPatternDamage = block.get("VendorDMCCodeClass.FixedPatternDamage")
        VendorDMCCodeClass_SymbolContrast = block.get("VendorDMCCodeClass.SymbolContrast")
        VendorDMCCodeClass_AxialNonUniformity = block.get("VendorDMCCodeClass.AxialNonUniformity")
        VendorDMCCodeClass_UnusedErrorCorrection = block.get("VendorDMCCodeClass.UnusedErrorCorrection")
        VendorDMCCodeClass_GridNonUniformity = block.get("VendorDMCCodeClass.GridNonUniformity")
        VendorDMCCodeClass_MinimalClass_res = block.get("VendorDMCCodeClass.MinimalClass_res")
        VendorDMCCodeClass_AcceptableClass = block.get("VendorDMCCodeClass.AcceptableClass")
        VendorDMCCodeClass_CurrentClass = block.get("VendorDMCCodeClass.CurrentClass")
        VendorDMCCodeClass_status = Local_Status("VendorDMCCodeClass", block)
        if VendorDMCCodeClass_status.active and VendorDMCCodeClass_status.database_save: 
            operation_type = 306  # hardcoded operation_id value 306 - VendorDMCCodeClass_status
            operation_status = int(VendorDMCCodeClass_status.result)  # 1 OK, 0 NOK
            results = [
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 1,
                    'value': VendorDMCCodeClass_CodeClass, 
                },
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 2,
                    'value': VendorDMCCodeClass_Modulation, 
                },
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 3,
                    'value': VendorDMCCodeClass_FixedPatternDamage, 
                },
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 4,
                    'value': VendorDMCCodeClass_SymbolContrast, 
                },
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 5,
                    'value': VendorDMCCodeClass_AxialNonUniformity, 
                },
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 6,
                    'value': VendorDMCCodeClass_UnusedErrorCorrection, 
                },
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 7,
                    'value': VendorDMCCodeClass_GridNonUniformity, 
                },
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 8,
                    'value': VendorDMCCodeClass_MinimalClass_res, 
                },
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 9,
                    'value': VendorDMCCodeClass_AcceptableClass, 
                },
                {
                    'type_id': 1,
                    'unit_id': 0,
                    'desc_id': operation_type * 100 + 10,
                    'value': VendorDMCCodeClass_CurrentClass, 
                },
            ]
            # write status
            self.database_engine.write_operation_result(detail_id, station_id, operation_status, operation_type, program_number, nest_number, VendorDMCCodeClass_status.date_time, results)
            # mark item as read
            VendorDMCCodeClass_status.set_database_save(0)


    def show_product_details(self, dbid):
        block = self.get_db(dbid)
        if block is None:
            logger.warn("PLC: {plc} DB: {db} is missing on PLC. Skipping.".format(plc=self.get_id(), db=dbid))
            return

        if PC_OPEN_BROWSER_FLAG in block.export():
            if block.__getitem__(PC_OPEN_BROWSER_FLAG):  # get the station status from db
                block.set_pc_ready_flag(False)  # set PC ready flag to False
                """
                try:
                    data = block[PRODUCT_TYPE]
                    product_type = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    product_type = 0
                """
                try:
                    data = block[HEAD_DETAIL_ID]
                    head_detail_id = data
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    head_detail_id = ""
                try:
                    data = block[HEAD_STATION_ID]
                    head_station_id = int(data)
                except ValueError as e:
                    logger.error("PLC: {plc} DB: {db} Data read error. Input: {data} Exception: {e}, TB: {tb}".format(plc=self.id, db=dbid, data=data, e=e, tb=traceback.format_exc()))
                    head_station_id = 0
                logger.info("PLC: {plc} ST: {station} PID: {head_detail_id} browser opening request - show product details.".format(plc=self.get_id(), station=head_station_id, head_detail_id=head_detail_id))

                url = "/".join([self.get_baseurl(), 'product', str(Product.calculate_product_id(product_type, head_detail_id))])
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
                        logger.info("PLC: {plc} ST: {station} URL: {url} product details window opened successfully.".format(plc=self.get_id(), station=head_station_id, type=product_type, head_detail_id=head_detail_id, url=url))
                    else:
                        logger.warning("PLC: {plc} ST: {station} URL: {url} failed to open product details window".format(plc=self.get_id(), station=head_station_id, type=product_type, head_detail_id=head_detail_id, url=url))
                else:
                    logger.warning("PLC: {plc} ST: {station} URL: {url} Popup event registered but popups are disabled by configuration.".format(plc=self.get_id(), station=head_station_id, type=product_type, head_detail_id=head_detail_id, url=url))

                self.counter_show_product_details += 1
                block.set_pc_open_browser_flag(False) # cancel PC_OPEN_BROWSER flag
                block.set_pc_ready_flag(True)  # set PC ready flag back to true
