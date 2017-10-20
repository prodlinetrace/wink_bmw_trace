import snap7
import logging
from .block import DB
from .custom_exceptions import UnknownDB

logger = logging.getLogger(__name__)


class DBs(object):
    """
    This class provides a container-like API which gives
    access to all db records defined on the PLC. It behaves
    like a dict in which keys are db numbers and values are actual
    db objects.
    """

    def __init__(self, plc):
        self.blockType = snap7.snap7types.block_types['DB']
        self.plc = plc

    def __len__(self):
        return len(self.keys)

    def keys(self):
        """
        Return a list of the names of all dbs
        """
        return list(self.iterkeys())

    def iterkeys(self):
        """
        Get the numbers of all available blocks
        """
        for block in self.plc.get_client().list_blocks_of_type(self.blockType):
            yield block

    def iteritems(self):
        """
        Get the names & objects for all dbs
        """
        for db in self.plc.get_client().list_blocks_of_type(self.blockType):
            yield db, DB(db, self.plc)

    def items(self):
        return [x for x in self.iteritems()]

    def __getitem__(self, db):
            return DB(db, self.plc)

    def __contains__(self, db):
        """
        True if db_name is the name of a defined database block
        """
        return db in self.keys()
