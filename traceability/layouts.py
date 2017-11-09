#from .constants import OPERATOR_LOGIN, OPERATOR_PASSWORD, OPERATOR_STATUS, OPERATOR_DO_LOGIN, OPERATOR_DO_LOGOUT, OPERATOR_IS_LOGIN, PC_READY_FLAG, PLC_QUERY_FLAG, PLC_SAVE_FLAG, DB_BUSY_FLAG, PC_OPEN_BROWSER_FLAG, STATION_ID, PRODUCT_TYPE, SERIAL_NUMBER, DATE_TIME, PLC_HEARTBEAT_FLAG, PC_HEARTBEAT_FLAG, TRC_TMPL_COUNT, STATION_NUMBER, STATION_STATUS, PLC_TRC_ON, PROGRAM_NAME, PROGRAM_NUMBER, CHECKSUM
from .constants import *
from .util import offset_spec_block

"""
Define layouts of DB blocks on PLC.
"""

db8xxHeader = """
0.0     {operator_login}             STRING[8]   # set by PLC
10.0    {operator_password}          STRING[16]  # set by PLC
28.0    operator.rez_d1              DINT        # reserve
32.0    operator.rez_d2              DINT        # reserve
36.0    {operator_status}            INT         # PC: 0 - not defined, 1 - logged in, 2 - logged out, 3 - blocked, 4 - wrong password
38.0    {operator_do_login}          BOOL        # set by: PLC - flag used to login. PC - switches off flag once login is ready.
38.1    {operator_do_logout}         BOOL        # set by: PLC - flag used to logout. PC - switches off flag once logout is ready.
38.2    {operator_is_login}          BOOL        # set by: PLC - flag used to check status. constantly set by PLC. Have value 1 when {operator_status} is 1. Otherwise have value of 0. 
38.3    operator.rez1_b3             BOOL        # reserve
38.4    operator.rez1_b4             BOOL        # reserve
38.5    operator.rez1_b5             BOOL        # reserve 
38.6    operator.rez1_b6             BOOL        # reserve
38.7    operator.rez1_b7             BOOL        # reserve
39.0    operator.rez1_b3             BOOL        # reserve
39.1    operator.rez1_b4             BOOL        # reserve
39.2    operator.rez1_b5             BOOL        # reserve 
39.3    operator.rez1_b3             BOOL        # reserve
39.4    operator.rez1_b4             BOOL        # reserve
39.5    operator.rez1_b5             BOOL        # reserve 
39.6    operator.rez1_b6             BOOL        # reserve
39.7    operator.rez1_b7             BOOL        # reserve
40.0    operator.rez_d3              DINT        # reserve
44.0    {operator_date_time}         DATETIME    # date and time from PLC. size is 8 bytes.

52.0    {head_station_id}            INT         # station ID
54.0    {head_program_number}        INT         # program number
56.0    {head_nest_number}           INT         # nest number
58.0    {head_detail_id}             STRING[30]  # detail ID
90.0    head.rez_i1                  INT         # reserve
92.0    head.rez_i2                  INT         # reserve
94.0    head.rez_d3                  DINT        # reserve
98.0    head.rez_d4                  DINT        # reserve

102.0   status.rez_d1                DINT        # reserve
106.0   {status_plc_trc_on}          BOOL        # traceability flag. used by PLC to indicate if tracaebility should be switched on.
106.1   {status_plc_live}            BOOL        # Controlled by PLC. blinks every 300[ms]. Indicates that PLC is alive
106.3   {status_save_only_mode}      BOOL        # 1 - baza zapisuje wyniki ale PLC nie sprawdza czy z poprzedniej stacji OK
106.4   {status_no_id_scanning}      BOOL        # 1 - praca bez skanowania ID detalu.
106.2   {status_pc_live}             BOOL        # Watched by PLC. PC should blink this bit every 300[ms] to notify that application is connected.
106.5   {status_no_type_verify}      BOOL        # 1 - praca bez weryfikacji typu / rezerwa
106.6   {status_no_scanning}         BOOL        # 1 - wariant bez skanowania (mimo ze praca ze skanowaniem id detalu)
106.7   status_rez_b7                BOOL        # reserve
107.0   {flag_plc_save}              BOOL        # PLC_Save bit - monitored by PC, set by PLC. PC saves status if set to True. Once PC finishes it sets it back to False.
107.1   {flag_plc_query}             BOOL        # PLC_Query bit - monitored by PC, set by PLC. PC reads status from database if set to True. Once PC finishes it sets it back to False.
107.2   {flag_id_query}              BOOL        # ID_Query bit - PLC asks PC to set detail_id
107.3   {flag_pc_ready}              BOOL        # PC_Ready bit. Monitored by PLC. PCL waits for True. PC sets to False when it starts processing. PC sets back to True once processing is finished.
107.4   {flag_id_ready}              BOOL        # ID_Ready bit - PC indicates that detail_id is already set. 
107.5   status.rez_b5                BOOL        # reserve
107.6   status.rez_b6                BOOL        # reserve
107.7   status.rez_b7                BOOL        # reserve
108.0   status.res_i1                INT         # date and time - TODO: report (is set to BOOL in pdf)
110.0   {status_datetime}            DATETIME    # date and time
118.0   status.station_result        INT         # wynik ze stanowiska
120.0   status.database_result       INT         # wynik z bazy danych
""".format(operator_login=OPERATOR_LOGIN, operator_password=OPERATOR_PASSWORD, operator_status=OPERATOR_STATUS, operator_do_login=OPERATOR_DO_LOGIN, operator_do_logout=OPERATOR_DO_LOGIN, operator_is_login=OPERATOR_IS_LOGIN, operator_date_time=OPERATOR_DATE_TIME, \
    head_station_id=HEAD_STATION_ID, head_program_number=HEAD_PROGRAM_NUMBER, head_nest_number=HEAD_NEST_NUMBER, head_detail_id=HEAD_DETAIL_ID, \
    status_plc_live=PLC_HEARTBEAT_FLAG, status_pc_live=PC_HEARTBEAT_FLAG, status_plc_trc_on=PLC_TRC_ON, status_datetime=STATUS_DATE_TIME, \
    status_save_only_mode=STATUS_SAVE_ONLY_MODE_FLAG, status_no_id_scanning=STATUS_NO_ID_SCANNING_FLAG,  status_no_type_verify=STATUS_NO_TYPE_VERIFY_FLAG, status_no_scanning=STATUS_NO_SCANNING_FLAG, \
    flag_pc_ready=PC_READY_FLAG, flag_plc_query=PLC_QUERY_FLAG, flag_plc_save=PLC_SAVE_FLAG, flag_id_query=ID_QUERY_FLAG, flag_id_ready=ID_READY_FLAG)

db8xxTrcHeader = """
0.0    {trc_template_count}         BYTE        # number of traceability template blocks in message body.
1.0    body.reserve_1               BYTE
""".format(trc_template_count=TRC_TMPL_COUNT)

db8xxTrcTail = """

"""

db8xxTrcTemplate = """
0.0    body.trc.tmpl.{number}.PC_Ready           BOOL        # PC_Ready bit - currently ignored
0.1    body.trc.tmpl.{number}.res_1              BOOL
0.2    body.trc.tmpl.{number}.PLC_Save           BOOL        # PLC_Save bit - monitored by PC. PC start block processing if set to True. Once PC finishes it sets it to False.
0.3    body.trc.tmpl.{number}.res_2              BOOL
0.4    body.trc.tmpl.{number}.res_3              BOOL
0.5    body.trc.tmpl.{number}.res_4              BOOL
0.6    body.trc.tmpl.{number}.res_5              BOOL
0.7    body.trc.tmpl.{number}.res_6              BOOL
1.0    body.trc.tmpl.{number}.res_byte           BYTE
2.0    body.trc.tmpl.{number}.operation_status   BYTE        # overall operation status. 1 - OK, 2 - NOK, 4 - Not present in this variant,  5 - next one OK, 6 - next one NOK
3.0    body.trc.tmpl.{number}.res_byte_0         BYTE
4.0    body.trc.tmpl.{number}.operation_type     INT         # individual operation type
6.0    body.trc.tmpl.{number}.program_id         INT         # individual program id

8.0    body.trc.tmpl.{number}.1.result           REAL        # operation #1 - measured result.
12.0   body.trc.tmpl.{number}.1.result_max       REAL        # operation #1 - maximum value
16.0   body.trc.tmpl.{number}.1.result_min       REAL        # operation #1 - minimum value
20.0   body.trc.tmpl.{number}.1.result_status    INT         # operation #1 - status
22.0   body.trc.tmpl.{number}.1.word_res         INT         # not used - TODO: could be used as indication flag

24.0   body.trc.tmpl.{number}.2.result           REAL        # operation #2 - measured result.
28.0   body.trc.tmpl.{number}.2.result_max       REAL        # operation #2 - maximum value
32.0   body.trc.tmpl.{number}.2.result_min       REAL        # operation #2 - minimum value
36.0   body.trc.tmpl.{number}.2.result_status    INT         # operation #2 - status
38.0   body.trc.tmpl.{number}.2.word_res         INT

40.0   body.trc.tmpl.{number}.date_time          DATETIME    # date and time - size is 8 bytes
# traceability template size is 48
"""

# create db map for given controller.
# controller id from config file should be used as key. currently controller id's are hardcoded
db_specs = {
    'c1': {},
    'c2': {},
    'c3': {},
    'c4': {},
    'c5': {},
    'c6': {},
}

def generate_db_spec(trcTemplateNumber=1):
    tmp_db = db8xxHeader
    tmp_db += offset_spec_block(db8xxTrcHeader, 122)
    for i in range(0, trcTemplateNumber):  # append py templates.
        base_offset = 124
        block_size = 48
        offset = base_offset + block_size * i
        tmp_db += offset_spec_block(db8xxTrcTemplate, offset).replace("{number}", str(i))

    return tmp_db

#############################################################################################
# St1x
#############################################################################################
db_specs['c1']['db301'] = generate_db_spec(1)
db_specs['c1']['db302'] = generate_db_spec(1)
db_specs['c1']['db303'] = generate_db_spec(4)
db_specs['c1']['db304'] = generate_db_spec(2)
db_specs['c1']['db305'] = generate_db_spec(15)

#############################################################################################
# St2x
#############################################################################################
db_specs['c2']['db301'] = generate_db_spec(3)
db_specs['c2']['db302'] = generate_db_spec(1)
db_specs['c2']['db303'] = generate_db_spec(4)
db_specs['c2']['db304'] = generate_db_spec(5)

#############################################################################################
# St3x
#############################################################################################
db_specs['c3']['db301'] = generate_db_spec(1)
db_specs['c3']['db302'] = generate_db_spec(3)
db_specs['c3']['db303'] = generate_db_spec(3)

#############################################################################################
# St4x
#############################################################################################
db_specs['c4']['db301'] = generate_db_spec(4)
db_specs['c4']['db302'] = generate_db_spec(13)

#############################################################################################
# St5x
#############################################################################################
db_specs['c5']['db301'] = generate_db_spec(1)
db_specs['c5']['db302'] = generate_db_spec(1)
db_specs['c5']['db303'] = generate_db_spec(1)
db_specs['c5']['db304'] = generate_db_spec(1)
db_specs['c5']['db305'] = generate_db_spec(2)

#############################################################################################
# St6x
#############################################################################################
db_specs['c6']['db301'] = generate_db_spec(1)

# special cases hacking...
db100 = ""
db101 = ""
db1 = ""
db2 = ""
db3 = ""
