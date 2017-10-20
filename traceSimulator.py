import logging
import sys
import os
from traceability.prodline import ProdLineBase
from traceability.simulator import Simulator
import time
import snap7

logger = logging.getLogger(__name__)

class ProdLineSimulator(ProdLineBase):

    def __init__(self, argv, loglevel=logging.WARNING):
        ProdLineBase.__init__(self, argv, loglevel)

        self.set_plc_class(Simulator)

    def init_mem_blocks(self):
        for ctrl in self.plcs:
            areaCode = snap7.snap7types.srvAreaDB
            for db in ctrl.get_active_datablock_list():
                _file = os.path.join(os.path.abspath(os.path.curdir), 'data', 'dbdump', ctrl.get_id() + "_" + str(db) + '.block')
                data = bytearray(open(_file, "rb").read())
                ctrl.register_area(areaCode, db, data)
                logger.info("Simulator: %s registered block: %s" % (ctrl, db))
                print "Simulator: %s registered block: %s" % (ctrl, db)

    def run(self):
        # initialize plcs - list of active plcs will be available as self._controlers
        self.init_plcs()
        self.connect_plcs()
        self.init_mem_blocks()
        # do tests
        j = 0
        while j < 100:
            for _sim in self.plcs:
                j += 1
                print "XXXXXXXX", j, _sim
                _sim.run()
            time.sleep(1)

        # close plc connections and exit cleanly
        self.disconnect_plcs()


def main():
    logger.info("Starting test app")
    sys.argv.append("-v")
    prodLine = ProdLineSimulator(sys.argv, logging.DEBUG)
    prodLine.run()
    logger.info("Test app finished")

if __name__ == "__main__":
    sys.exit(main())
