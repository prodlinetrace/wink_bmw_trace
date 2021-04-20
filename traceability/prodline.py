import snap7
import threading
import concurrent.futures
import os
import locale
import traceback
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from time import sleep
from .helpers import parse_config, parse_args
from .database import Database
import sqlalchemy
from contextlib import contextmanager

LOCALE_LOCK = threading.Lock()

@contextmanager
def setlocale(name):
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)

logger = logging.getLogger(__name__)


class ProdLineBase(object):

    def __init__(self, argv, loglevel=logging.INFO):
        self._argv = argv
        self._opts, self._args = parse_args(self._argv)

        with setlocale('pl'):
            self.year = datetime.strptime("01","%y")
            
        # handle logging - set root logger level
        logging.root.setLevel(logging.INFO)
        logger = logging.getLogger(__name__.ljust(24)[:24])
        logger.setLevel(loglevel)

        # parse config file
        logger.info("Using config file {cfg}.".format(cfg=self._opts.config))
        self._config = parse_config(self._opts.config)
        _fh = TimedRotatingFileHandler(self._config['main']['logfile'][0], when="MIDNIGHT", interval=1, backupCount=30)
        #_fh = logging.FileHandler(self._config['main']['logfile'][0])
        _ch = logging.StreamHandler()
        self.__PLCClass = None
        self._baseurl = 'http://localhost:5000/'
        self._popups  = True
        self._pc_ready_flag_on_poll = False
        self._pollsleep = 0.1
        self._polldbsleep = 0.01

        if self._opts.quiet:
            # log errors to console
            _ch.setLevel(logging.ERROR)
            # log INFO+ to file
            _fh.setLevel(logging.INFO)

        if self._opts.verbose:
            # log INFO+ to console
            _ch.setLevel(logging.INFO)
            # log DEBUG+ to file
            _fh.setLevel(logging.DEBUG)
            logger.setLevel(logging.DEBUG)
            logging.root.setLevel(logging.DEBUG)

        _fh.setFormatter(logging.Formatter('%(asctime)s - %(name)-22s - %(levelname)-8s - %(message)s'))
        _ch.setFormatter(logging.Formatter('%(name)s - %(levelname)8s - %(message)s'))
        # logger.addHandler(_fh)
        logging.root.addHandler(_fh)

        self.__plc_list = []
        self.plcs = []

        self.opf_status = bool(int(self._config['main']['opf'][0]))

    def get_opf_status(self):
        return self.opf_status

    def get_popups(self):
        return self._popups

    def set_popups(self, popups=True):
        logger.info("Popups set to: {popups}".format(popups=popups))
        self._popups = popups

    def get_baseurl(self):
        return self._baseurl

    def set_baseurl(self, baseurl):
        logger.info("Baseurl set to: {baseurl}".format(baseurl=baseurl))
        self._baseurl = baseurl

    def get_pollsleep(self):
        return self._pollsleep

    def set_pollsleep(self, sleep):
        logger.info("pollsleep set to: {sleep}".format(sleep=sleep))
        self._pollsleep = sleep

    def get_polldbsleep(self):
        return self._polldbsleep

    def set_polldbsleep(self, sleep):
        logger.info("polldbsleep set to: {sleep}".format(sleep=sleep))
        self._polldbsleep = sleep

    def get_pc_ready_flag_on_poll(self):
        return self._pc_ready_flag_on_poll

    def set_pc_ready_flag_on_poll(self, flag):
        logger.info("pc_ready_flag_on_poll set to: {flag}".format(flag=flag))
        self._pc_ready_flag_on_poll = flag

    def get_config(self):
        return self._config

    def get_db_file(self):
        return self._config['main']['dbfile'][0]

    def get_dburi(self):
        return self._config['main']['dburi'][0]

    def set_plc_class(self, plcClass):
        self.__PLCClass = plcClass

    # start plc connections
    def connect_plcs(self):
        for plc in self.__plc_list:
            logging.debug("Connecting PLC: {plc} ".format(plc=plc.id))
            plc.connect()
            logger.debug("PLC: {plc} has status: {status} ".format(plc=plc.id, status=plc.get_status()))
            if plc.get_status():
                self.plcs.append(plc)
                logger.debug("PLC: {plc} Set as active.".format(plc=plc.get_id()))
            else:
                logger.warning("Unable connect to PLC: {plc}. Skipping.".format(plc=plc))

    # close plc connections
    def disconnect_plcs(self):
        for plc in self.plcs:
            logger.debug("PLC: {plc} disconnecting.".format(plc=plc))
            plc.disconnect()

    def pc_heartbeat(self):
        for plc in self.plcs:
            try:
                plc.blink_pc_heartbeat()
            except snap7.snap7exceptions.Snap7Exception:
                logging.critical("Connection to PLC: {plc} lost. Trying to re-establish connection.".format(plc=plc))
                plc.connect()

    def sync_plcs_time(self):
        for plc in self.plcs:
            plc.sync_time()

    def sync_plcs_time_if_needed(self):
        for plc in self.plcs:
            try:
                plc.sync_time_if_needed()
            except snap7.snap7exceptions.Snap7Exception:
                logging.critical("Connection to PLC: {plc} lost. Trying to re-establish connection.".format(plc=plc))
                plc.connect()

    def init_plcs(self):
        if 'main' not in self._config:
            logger.warning("unable to find section main in configuration. File: {cfg}".format(cfg=self._opts.config))

        if 'plcs' not in self._config['main']:
            logger.warning("unable to find section plcs in configuration main. File: {cfg}".format(cfg=self._opts.config))

        self.__plc_list = []

        for plc in self._config['main']['plcs']:
            plc = plc.strip()
            ip = self._config[plc]['ip'][0]
            rack = self._config[plc]['rack'][0]
            slot = self._config[plc]['slot'][0]
            port = self._config[plc]['port'][0]
            name = self._config[plc]['name'][0]
            iden = self._config[plc]['id'][0]
            datablocks = []
            for cblock in self._config[plc]['blocks']:
                cblock = cblock.strip()
                if cblock in self._config:
                    dbid = int(self._config[cblock]['id'][0])
                    datablocks.append(dbid)
                else:
                    logger.error("PLC: {plc} is configured to use DB: {db} but this DB is missing in configuration file (not defined).".format(plc=plc, db=cblock))

            if self._config[plc]['status'][0] != '1':
                logger.warning("PLC: {plc} is in status: {status} (in configuration file). Skipped.".format(plc=plc, status=self._config[plc]['status']))
                continue
            c = self.__PLCClass(ip, rack, slot, port, self.get_opf_status())
            c.set_name(name)
            c.set_id(iden)
            c.set_config(self._config)
            logger.debug("PLC: {plc} configuring database engine connectivity".format(plc=plc))
            c._init_database(self.get_dburi())
            logger.debug("PLC: {plc} set active data blocks to: {dbs}".format(plc=plc, dbs=str(datablocks)))
            c.set_active_datablock_list(datablocks)
            # updates PLC instance with config file content to make sure that OFP checker can use it.
            logger.debug("PLC: {plc} is configured now.".format(plc=plc))

            self.__plc_list.append(c)
        return True


class ProdLine(ProdLineBase):

    def __init__(self, argv, loglevel=logging.INFO):
        ProdLineBase.__init__(self, argv, loglevel)
        self.database = Database(self.__class__.__name__, self.get_config(), opf_status=self.get_opf_status())
        from .plc import PLC
        self.set_plc_class(PLC)

    def get_status(self):
        return " ".join([str(ctrl.get_id()) + ":" + str(ctrl.get_status()) for ctrl in self.plcs])

    def get_counter_status_message_read(self):
        return sum([ctrl.counter_status_message_read for ctrl in self.plcs])

    def get_counter_status_message_write(self):
        return sum([ctrl.counter_status_message_write for ctrl in self.plcs])

    def get_counter_saved_operations(self):
        return sum([ctrl.counter_saved_operations for ctrl in self.plcs])

    def get_counter_product_details_display(self):
        return sum([ctrl.counter_show_product_details for ctrl in self.plcs])

    def get_counter_operator_status_read(self):
        return sum([ctrl.counter_operator_status_read for ctrl in self.plcs])

    def get_counter_status_wrong_order(self):
        return sum([ctrl.counter_status_wrong_order for ctrl in self.plcs])
    
    def get_product_count(self):
        return self.database.get_product_count()

    def get_station_count(self):
        return self.database.get_station_count()

    def get_status_count(self):
        return self.database.get_status_count()

    def get_opertation_count(self):
        return self.database.get_opertation_count()

    def get_operation_type_count(self):
        return self.database.get_operation_type_count()

    def get_status_type_count(self):
        return self.database.get_status_type_count()

    def get_comment_count(self):
        return self.database.get_comment_count()

    def get_all_product_ids(self, qid='q1'):
        if self.get_opf_status() is True:
            if self.database.opf is not None:
                return self.database.opf.get_all_product_ids(qid)
            else:
                return None
        else:
            return None

    def get_next_product_id(self, qid='q1'):
        if self.get_opf_status() is True:
            if self.database.opf is not None:
                return self.database.opf.get_next_product_id(qid)
            else:
                return None
        else:
            return None

    def test_messages(self):
        for plc in self.plcs:
            for msg in self._config['main']['messages']:
                dbid = int(self._config[msg]['id'][0])
                message = plc.getParsedDb(dbid)
                timestamp = "%.2x-%.2x-%.2x %.2x:%.2x:%.2x.%.4x" % (message.__getitem__('head.time.year'), message.__getitem__('head.time.month'), message.__getitem__('head.time.day'), message.__getitem__('head.time.hour'), message.__getitem__('head.time.minute'), message.__getitem__('head.time.second'), message.__getitem__('head.time.msecond'))
                logger.info("PLC: {plc} DB: {db} has timestamp: {timestamp}".format(plc=plc.id, db=dbid, timestamp=timestamp))

    def test_time_get(self):
        for plc in self.plcs:
            logger.info("PLC: {plc} system time: {time}".format(plc=plc, time=plc.get_time()))

    def test_time_set(self):
        dtime = datetime(2015, 4, 1, 22, 12, 13)
        for plc in self.plcs:
            logger.info("PLC: {plc} set system time to: {dtime}".format(plc=plc, dtime=dtime))
            plc.set_time(dtime)

    def test_time_sync(self):
        for plc in self.plcs:
            logger.info("PLC: {plc} Sync system time with PC".format(plc=plc))
            plc.sync_time()

    def test_time(self):
        self.test_time_get()
        self.test_time_set()
        self.test_time_get()
        self.test_time_sync()
        self.test_time_get()

    def poll(self):
        for plc in self.plcs:
            for dbid in plc.get_active_datablock_list():
                try:
                    plc.poll_db(dbid)
                except snap7.snap7exceptions.Snap7Exception:
                    logging.critical("Connection to {plc} lost. Trying to re-establish connection.".format(plc=plc))
                    plc.connect()

    def run(self, times=10):
        """"
            runs main loop of the class.
            @param times -  defines how many poll loops should be executed. (0 for infinity)
        """
        logger.info("Polling for {times} times (zero means infinity)".format(times=times))
        i = 0
        while i < times or times == 0:
            self.poll()
            i += 1
            # try to sync plcs every 1000 times if needed - first sync after 5 times.
            if i % 1000 == 5:
                self.sync_plcs_time_if_needed()

            # change the value of PC heartbeat flag
            self.pc_heartbeat()

    def runExtras(self):
        """"
            run extras: in sync plc time and update heartbeat bit.
        """
        i = 0
        while True:
            sleep(0.1)
            i += 1
            # try to sync plcs time if needed (every 60s by default) - first sync after 5 sec.
            if i % 600 == 50:
                self.sync_plcs_time_if_needed()
            # change the value of PC heartbeat flag (every 100ms by default)
            self.pc_heartbeat()

        return True

    def runPLC(self, plc):
        logger.info("PLC: {plc} Started Processing Thread for DBS: {dbs}".format(plc=plc.id, dbs=plc.get_active_datablock_list()))
        # set some initial values
        threading.currentThread().setName(plc.get_name())
        plc.set_baseurl(self.get_baseurl())  # set baseurl per plc
        plc.set_pollsleep(self.get_pollsleep())
        plc.set_polldbsleep(self.get_polldbsleep())
        plc.set_pc_ready_flag_on_poll(self.get_pc_ready_flag_on_poll())
        locale.setlocale(locale.LC_ALL, "C")

        while True:
            # blink heartbeat
            try:
                plc.blink_pc_heartbeat()
            except snap7.snap7exceptions.Snap7Exception:
                logger.critical("Connection to {plc} lost. Trying to re-establish connection.".format(plc=plc))
                plc.connect()

            # poll plc
            try:
                plc.poll()
            except snap7.snap7exceptions.Snap7Exception:
                logger.critical("Connection to {plc} lost. Trying to re-establish connection.".format(plc=plc))
                plc.connect()

            # sync time
            try:
                plc.sync_time_if_needed()
            except snap7.snap7exceptions.Snap7Exception:
                logger.critical("Connection to {plc} lost. Trying to re-establish connection.".format(plc=plc))
                plc.connect()

            # get configuration update
            try:
                plc.set_popups(self.get_popups())
                # logging.debug("{plc} baseurl: {baseurl} popups: {popups}".format(plc=plc, popups=plc.get_popups(), baseurl=plc.get_baseurl()))
            except snap7.snap7exceptions.Snap7Exception:
                logger.critical("Connection to {plc} lost. Trying to re-establish connection.".format(plc=plc))
                plc.connect()

            try:
                plc.send_database_keepalive()
            except  sqlalchemy.exc.InvalidRequestError:
                logger.critical("PLC: {plc} database connection lost. Trying to re-establish connection.".format(plc=plc))
                plc.database_engine.disconnect()
                plc.database_engine.connect()


        return True

    def main(self):
        # initialize plcs - list of active plcs will be available as self.plcs
        self.init_plcs()
        self.connect_plcs()
        #self.run(0)  # old method

        # start each plc for processing in separate thread.
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_ctrl = {executor.submit(self.runPLC, ctrl): ctrl for ctrl in self.plcs}
            for future in concurrent.futures.as_completed(future_to_ctrl):
                try:
                    data = future.result()
                except Exception as exc:
                    tb = traceback.format_exc()
                    logger.error('Thread {thread} generated an exception: {exc}, {tb}'.format(thread=future, exc=exc, tb=tb))
                else:
                    logger.error("{err}".format(err=data))

        self.disconnect_plcs()
        logger.critical("Something went wrong. Main loop just finished. No plcs started/configured?")
