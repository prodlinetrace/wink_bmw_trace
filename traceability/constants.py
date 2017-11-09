# operator section
OPERATOR_LOGIN          = 'operator.login'
OPERATOR_PASSWORD       = 'operator.password'

# operator section
OPERATOR_STATUS         = 'operator.operator_status'  # int
OPERATOR_DO_LOGIN       = 'operator.operator_do_login'
OPERATOR_DO_LOGOUT      = 'operator.operator_do_logout'
OPERATOR_IS_LOGIN       = 'operator.operator_is_login'
OPERATOR_DATE_TIME      = 'operator.operator_datetime'



# head section
HEAD_STATION_ID         = 'head.station_id'
HEAD_PROGRAM_NUMBER     = 'head_program_number'
HEAD_NEST_NUMBER        = 'head.nest_number'
HEAD_DETAIL_ID          = 'head.detail_id'
#SERIAL_NUMBER           = 'head.serial_number'   # string(8) - 6 digits
#PRODUCT_TYPE            = 'head.product_type'    # string(12) - 10 digits
#PROGRAM_NUMBER          = 'head.program_number'  # integer
#PROGRAM_NAME            = 'head.program_name'    # string(20)


# status section
PC_HEARTBEAT_FLAG       = 'ctrl.PC_live'
PLC_HEARTBEAT_FLAG      = 'ctrl.PLC_live'
PLC_TRC_ON              = 'ctrl.PLC_trc_on'
CHECKSUM                = 'ctrl.checksum'
STATUS_SAVE_ONLY_MODE_FLAG = 'status_save_only_mode'
STATUS_NO_ID_SCANNING_FLAG = 'status_no_id_scanning'
STATUS_NO_TYPE_VERIFY_FLAG = 'status_no_type_verify'
STATUS_NO_SCANNING_FLAG = 'status_no_scanning' 

PC_READY_FLAG           = 'status.PC_Ready'
PLC_QUERY_FLAG          = 'status.PLC_Query'
PLC_SAVE_FLAG           = 'status.PLC_Save'
ID_QUERY_FLAG           = 'status.flag_id_query' 
ID_READY_FLAG           = 'status.flag_id_ready'

STATUS_DATE_TIME        = 'status.date_time'       # 8 bytes

#STATION_NUMBER          = 'status.station_number'  # byte
#STATION_STATUS          = 'status.station_status'  # byte


# trc templates
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
