import snap7
import logging
from .layouts import db_specs
import re
from .constants import PC_READY_FLAG, PLC_QUERY_FLAG, PLC_SAVE_FLAG, TRC_TMPL_COUNT, PC_OPEN_BROWSER_FLAG, OPERATOR_QUERY_FLAG, OPERATOR_SAVE_FLAG

logger = logging.getLogger(__name__)


class DB(object):
    """
    Provide API for DB bytearray
    """
    _bytearray = None      # data of reference to parent DB
    _specification = None  # row specification

    def __init__(self, db_number, plc=None, _bytearray=None, _specification=None):
        self.db_number = db_number
        self.plc = plc
        self.db_name = 'db' + str(self.db_number)

        self.db_offset = 0          # start point of row data in db
        self.layout_offset = 0  # start point of row data in layout

        # handle specification
        if _specification is None:
            # db specification = db_number + plc * 10. DB 300 remains unchanged
            # ugly hack caused by Diko lazyness to make db specifications unique across whole production line.
            #logger.debug("PLC: %s reading db spec for: %s " % (self.plc.get_id(), self.db_name))
            if self.db_name in db_specs[self.plc.get_id()]:
                _block_spec = db_specs[self.plc.get_id()][self.db_name]
            else:
                logger.error("PLC: {plc} Data Block DB: {db} not configured in plc block definition. Returning empty spec.".format(plc=self.plc.get_id(), db=self.db_name))
                _block_spec = ""
        else:
            _block_spec = _specification
        self._specification = snap7.util.parse_specification(_block_spec)
        #logger.debug("PLC: %s db:  %s spec: %s" % (self.plc.get_id(), self.db_name, self._specification))

        # handle bytearray
        if _bytearray is None:  # read byte array from plc if not passed.
            self.read()
        else:
            self._bytearray = _bytearray

    def get_plc(self):
        return self.plc

    def get_db_number(self):
        return self.db_number

    def get_bytearray(self):
        """
        return bytearray
        """
        return self._bytearray

    def export(self):
        """
        export dictionary with values
        """
        data = {}
        for key in self._specification:
            data[key] = self[key]
        return data

    def __getitem__(self, key):
        """
        Get a specific db field
        """
        #logger.debug("PLC: %s db:  %s reading key: %s" % (self.plc.get_id(), self.db_name, key))
        try:
            assert key in self._specification
            index, _type = self._specification[key]
        except AssertionError, e:
            logger.error("PLC: {plc} DB: {db} unable to read key: {key}".format(plc=self.plc.get_id(), db=self.db_name, key=key))
            logger.warning("PLC: {plc} DB: {db} specification: {spec}".format(plc=self.plc.get_id(), db=self.db_name, spec=self._specification))
            if TRC_TMPL_COUNT in self._specification:
                template_count = self.__getitem__(TRC_TMPL_COUNT)
                logger.warn("PLC: {plc} DB: {db} traceability template count: {count}".format(plc=self.plc.get_id(), db=self.db_name, count=template_count))
            import traceback
            logger.error("PLC: {plc} DB: {db} Raise exception: {exc}, TB: {tb}".format(plc=self.plc.get_id(), db=self.db_name, exc=e, tb=traceback.format_exc()))
            raise(e)
        return self.get_value(index, _type)

    def __setitem__(self, key, value):
        assert key in self._specification
        index, _type = self._specification[key]
        self.set_value(index, _type, value)

    def __repr__(self):
        string = ""
        for var_name, (index, _type) in self._specification.items():
            string = '%s\n%-20s %-10s' % (string, var_name, self.get_value(index, _type))
        return string

    def __str__(self):
        string = """DB: #{db}""".format(db=self.db_number)
        if self.plc is not None:
            string += " of PLC: {plc}".format(plc=self.plc.id)
        return string

    def get_dict(self):
        elem = {}
        for name, (index, _type) in self._specification.items():
            value = self.get_value(index, _type)
            elem[name] = value
        return elem

    def unchanged(self, _bytearray):
        if self.get_bytearray() == _bytearray:
            return True
        return False

    def get_offset(self, byte_index):
        """
        Calculate correct beginning position for a row
        the db_offset = row_size * index
        """
        return int(float(byte_index) - self.layout_offset + self.db_offset)

    def get_value(self, byte_index, _type):
        _bytearray = self.get_bytearray()

        if _type == 'BOOL':
            byte_index, bool_index = byte_index.split('.')
            return snap7.util.get_bool(_bytearray, self.get_offset(byte_index), int(bool_index))

        # remove 4 from byte index since
        # first 4 bytes are used by db
        byte_index = self.get_offset(byte_index)

        if _type.startswith('STRING'):
            max_size = re.search('\d+', _type).group(0)
            max_size = int(max_size)
            return snap7.util.get_string(_bytearray, byte_index, max_size)

        if _type == 'REAL':
            return snap7.util.get_real(_bytearray, byte_index)

        if _type == 'DWORD':
            return snap7.util.get_dword(_bytearray, byte_index)

        if _type == 'BYTE':
            return snap7.util.get_byte(_bytearray, byte_index)

        if _type == 'INT':
            return snap7.util.get_int(_bytearray, byte_index)

        if _type == 'DINT':
            return snap7.util.get_int(_bytearray, byte_index)

        if _type == 'DATETIME':
            return snap7.util.get_datetime(_bytearray, byte_index)

        raise ValueError

    def set_value(self, byte_index, _type, value):
        _bytearray = self.get_bytearray()

        if _type == 'BOOL':
            byte_index, bool_index = byte_index.split('.')
            return snap7.util.set_bool(_bytearray, self.get_offset(byte_index), int(bool_index), value)

        byte_index = self.get_offset(byte_index)

        if _type.startswith('STRING'):
            max_size = re.search('\d+', _type).group(0)
            max_size = int(max_size)
            try:
                ret = snap7.util.set_string(_bytearray, byte_index, value, max_size)
            except ValueError, e:
                import traceback
                logger.warning("PLC: {plc} DB: {db} Unable to set string type. Exception: {exc}, TB: {tb}".format(plc=self.get_plc(), db=self.db_number, exc=e, tb=traceback.format_exc()))
                return False
            return ret

        if _type == 'REAL':
            return snap7.util.set_real(_bytearray, byte_index, value)

        if _type == 'DWORD':
            return snap7.util.set_dword(_bytearray, byte_index, value)

        if _type == 'INT':
            return snap7.util.set_int(_bytearray, byte_index, value)

        if _type == 'BYTE':
            return snap7.util.set_byte(_bytearray, byte_index, value)

        if _type == 'DINT':
            return snap7.util.set_int(_bytearray, byte_index, value)

        if _type == 'DATETIME':
            return snap7.util.set_datetime(_bytearray, byte_index, value)

        raise ValueError

    def get_type_size(self, item, _type):
        """
        Returns size of given type
        """
        if _type == 'BOOL':
            return 1

        if _type.startswith('STRING'):
            length = len(item) + 2
            maxlen = int(_type.replace('STRING[', '').replace(']', ''))
            if length <= maxlen:
                return length
            else:
                return maxlen

        if _type == 'REAL':
            return 4

        if _type == 'DWORD':
            return 4

        if _type == 'INT':
            return 2

        if _type == 'BYTE':
            return 1

        if _type == 'DINT':
            return 4

        raise ValueError

    def store_item(self, key, value):
        """
        sets key and value pair and save it to PLC memory
        """
        #print "VALUE before store:", key, ":", value, "xxx"
        self.set_item(key, value)
        self.write_item(key)
        v = self.__getitem__(key)
        #print "plc:", self.plc
        #print "VALUE after store:", key, ":", v, "xxx"

    def set_item(self, key, value):
        """
        sets key and value pair of db
        """
        self[key] = value

    def write_item(self, key):
        """
        Write specific key to PLC
        """
        value = self.__getitem__(key)
        byte_index, _type = self._specification[key]
        size = self.get_type_size(value, _type)
        offset = self.get_offset(byte_index)
        db_nr = self.db_number
        data = self.get_bytearray()[offset:offset + size]
        if self.plc is not None:
            #print "Writing item", db_nr, offset, data
            self.plc.get_client().db_write(db_nr, offset, data)
        return data

    def read_item(self, key):
        """
        Read specific key from PLC
        """
        value = self.__getitem__(key)
        byte_index, _type = self._specification[key]
        size = self.get_type_size(value, _type)
        offset = self.get_offset(byte_index)
        db_nr = self.db_number
        if self.plc is not None:
            data = self.plc.get_client().db_read(db_nr, offset, size)
        # overwrite bytearray with data from PLC
        self._bytearray[offset:size] = data
        return self[key]

    def write(self):
        """
        Write current data to db in PLC # BE CAREFULL
        """
        db_nr = self.db_number
        data = self.get_bytearray()
        if self.plc is not None:
            self.plc.get_client().client.db_write(db_nr, self.db_offset, data)

    def read(self):
        """
        read current data from PLC # TEST if READY
        """
        if self.plc is not None:
            _ba = self.plc.get_client().db_get(self.db_number)
            self._bytearray = _ba

    def get_parsed_data(self):
        # parsed = DB(db, data, layout) # this was ok
        return self

    def pc_ready_flag(self):
        """
        returns value of PC_READY_FLAG
        """
        return self[PC_READY_FLAG]

    def pc_open_browser_flag(self):
        """
        returns value of PC_OPEN_BROWSER_FLAG
        """
        return self[PC_OPEN_BROWSER_FLAG]

    def plc_query_flag(self):
        """
        returns value of PLC_QUERY_FLAG
        """
        return self[PLC_QUERY_FLAG]

    def plc_save_flag(self):
        """
        returns value of PLC_SAVE_FLAG
        """
        return self[PLC_SAVE_FLAG]

    def operator_query_flag(self):
        return self[OPERATOR_QUERY_FLAG]

    def operator_save_flag(self):
        return self[OPERATOR_SAVE_FLAG]

    def set_operator_query_flag(self, value=True, check=True):
        flag = OPERATOR_QUERY_FLAG
        return self.set_flag(flag, value, check)

    def set_operator_save_flag(self, value=True, check=True):
        flag = OPERATOR_SAVE_FLAG
        return self.set_flag(flag, value, check)

    def set_plc_save_flag(self, value=True, check=True):
        flag = PLC_SAVE_FLAG
        return self.set_flag(flag, value, check)

    def set_plc_query_flag(self, value=True, check=True):
        flag = PLC_QUERY_FLAG
        return self.set_flag(flag, value, check)

    def set_pc_ready_flag(self, value=True, check=True):
        flag = PC_READY_FLAG
        return self.set_flag(flag, value, check)

    def set_pc_open_browser_flag(self, value=True, check=True):
        flag = PC_OPEN_BROWSER_FLAG
        return self.set_flag(flag, value, check)

    def set_flag(self, flag, value, check=True):
        logger.debug("PLC: {plc} DB: {db} FLAG: {flag} set to: {value}.".format(plc=self.plc.get_id(), db=self.get_db_number(), flag=flag, value=value))
        # set block value in memory
        self[flag] = value
        # write flag to PLC
        self.write_item(flag)
        if check:  # check actual value - optional
            #self.read_item(flag)  # this shit shifts db block by 1 !!!!! DO NOT DO IT!!
            block = self.get_parsed_data()
            checkedval = self.__getitem__(flag)
            logger.debug("PLC: {plc} DB: {db} FLAG: {flag} set/checked value: {value}/{checkedval}.".format(plc=self.plc.get_id(), db=self.get_db_number(), flag=flag, value=value, checkedval=checkedval))
            if value != checkedval:
                logger.warning("PLC: {plc} DB: {db} FLAG: {flag} set/checked value does not match: {value}/{checkedval}.".format(plc=self.plc.get_id(), db=self.get_db_number(), flag=flag, value=value, checkedval=checkedval))
