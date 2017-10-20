STATION_ID              = 'head.station_id'      # byte
SERIAL_NUMBER           = 'head.serial_number'   # string(8) - 6 digits
PRODUCT_TYPE            = 'head.product_type'    # string(12) - 10 digits
PROGRAM_NUMBER          = 'head.program_number'  # integer
PROGRAM_NAME            = 'head.program_name'    # string(20)

# operator section
OPERATOR_QUERY_FLAG     = 'operator.operator_Query'
OPERATOR_SAVE_FLAG      = 'operator.operator_Save'
OPERATOR_NUMBER         = 'operator.operator_number'  # dint
OPERATOR_STATUS         = 'operator.operator_status'  # byte

PC_HEARTBEAT_FLAG       = 'ctrl.PC_live'
PLC_HEARTBEAT_FLAG      = 'ctrl.PLC_live'
PLC_TRC_ON              = 'ctrl.PLC_trc_on'
CHECKSUM                = 'ctrl.checksum'

PC_READY_FLAG           = 'status.PC_Ready'
PLC_QUERY_FLAG          = 'status.PLC_Query'
PLC_SAVE_FLAG           = 'status.PLC_Save'
DB_BUSY_FLAG            = 'status.DB_Busy'
PC_OPEN_BROWSER_FLAG    = 'status.PC_OpenBrowser'
STATION_NUMBER          = 'status.station_number'  # byte
STATION_STATUS          = 'status.station_status'  # byte
DATE_TIME               = 'status.date_time'       # 8 bytes

TRC_TMPL_COUNT          = 'body.trc.template_count'
TRC_TMPL_SAVE_FLAG      = 'body.trc.tmpl.__no__.PLC_Save'
TRC_TMPL_PROGRAM_ID     = 'body.trc.tmpl.__no__.program_id'

STATION_STATUS_CODES = {
    0: {"result": "UNDEFINED", "desc": "status undefined (not present in database)"},
    1: {"result": "OK", "desc": "Status ok"},
    2: {"result": "NOK", "desc": "Status not ok"},
    4: {"result": "NOTAVAILABLE", "desc": "Not present in given type"},
    5: {"result": "REPEATEDOK", "desc": "Repeated test was ok"},
    6: {"result": "REPEATEDNOK", "desc": "Repeated test was not ok"},
    9: {"result": "WAITING", "desc": "status reset - PLC set status to 'WAITING' and waiting for PC response"},
    10: {"result": "INTERRUPTED", "desc": "Test was interrupted"},
    11: {"result": "REPEATEDINTERRUPTED", "desc": "Repeated test was interrupted"},
    99: {"result": "VALUEERROR", "desc": "Faulty value was passed. Unable to process data."},
}
