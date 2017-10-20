from .constants import PC_READY_FLAG, PLC_QUERY_FLAG, PLC_SAVE_FLAG, DB_BUSY_FLAG, PC_OPEN_BROWSER_FLAG, STATION_ID, PRODUCT_TYPE, SERIAL_NUMBER, DATE_TIME, PLC_HEARTBEAT_FLAG, PC_HEARTBEAT_FLAG, TRC_TMPL_COUNT, STATION_NUMBER, STATION_STATUS, PLC_TRC_ON, PROGRAM_NAME, PROGRAM_NUMBER, CHECKSUM, OPERATOR_NUMBER, OPERATOR_STATUS, OPERATOR_QUERY_FLAG, OPERATOR_SAVE_FLAG
from .util import offset_spec_block

"""
Define layouts of DB blocks on PLC.
"""



db3xxHeader = """
0.0     {station_id}                 BYTE        # station_id of given PLC. (0-255 typically: 10, 11, 20, 21, 22, 23, 30, 31)
2.0     {product_type}               STRING[12]  # product_type from nameplate (10 digits)
16.0    {serial_number}              STRING[40]  # serial_number from nameplate (6 digits)
58.0    {program_number}             INT         # Program Number - not used currently. Use {program_name} instead
60.0    {program_name}               STRING[20]  # Program Name - name or id number of assemby program for given product
82.0    head.res_1                   DINT        # reserve
86.0    {plc_live}                   BOOL        # blinks every 300[ms]. Indicates that PLC is alive.
86.1    {plc_trc_on}                 BOOL        # traceability flag. used by PLC to indicate if tracaebility should be switched on.
86.2    ctrl.PLC_reserve_1           BOOL        # not used
86.3    ctrl.PLC_reserve_2           BOOL        # not used
86.4    {pc_live}                    BOOL        # Watched by PLC. PC should blink this bit every 300[ms] to notify that application is connected.
86.5    ctrl.PC_reserve_1            BOOL        # not used
86.6    ctrl.PC_reserve_2            BOOL        # not used
86.7    ctrl.PC_reserve_3            BOOL        # not used
87.0    ctrl.reserve                 BYTE        # not used
88.0    {checksum}                   DINT        # control checksum - not used currently
92.0    {flag_operator_query}        BOOL
92.1    {flag_operator_save}         BOOL
92.2    operator.res_1               BOOL
92.3    operator.res_2               BOOL
92.4    operator.res_3               BOOL
92.5    operator.res_4               BOOL
92.6    operator.res_5               BOOL
92.7    operator.res_6               BOOL
93.0    operator.res_7               BOOL
93.1    operator.res_8               BOOL
93.2    operator.res_9               BOOL
93.3    operator.res_10              BOOL
93.4    operator.res_11              BOOL
93.5    operator.res_12              BOOL
93.6    operator.res_13              BOOL
93.7    operator.res_14              BOOL
94.0    operator.operator_status     BYTE
96.0    operator.operator_number     DINT
100.0   operator.operator_res_15     DINT
104.0   {flag_pc_ready}              BOOL        # PC_Ready bit. Monitored by PLC. PCL waits for True. PC sets to False when it starts processing. PC sets back to True once processing is finished.
104.1   {flag_plc_query}             BOOL        # PLC_Query bit - monitored by PC, set by PLC. PC reads status from database if set to True. Once PC finishes it sets it back to False.
104.2   {flag_plc_save}              BOOL        # PLC_Save bit - monitored by PC, set by PLC. PC saves status if set to True. Once PC finishes it sets it back to False.
104.3   {flag_db_busy}               BOOL        # DB_Busy bit - not really used currently.
104.4   {flag_pc_browser}            BOOL        # PC_OpenBrowser bit - monitored by PC, set by PLC. PC opens new browser tab with product details page if set to True (popups has to be enabled in program configuration). Once done it sets it back to False.
104.5   status.res_1                 BOOL
104.6   status.res_2                 BOOL
104.7   status.res_3                 BOOL
105.0   status.byte_res_1            BYTE
106.0   status.byte_res_2            BYTE
107.0   status.byte_res_3            BYTE
108.0   status.byte_res_4            BYTE
112.0   {station_number}             BYTE        # station_number - used when reading or saving station status. Value set by PLC when reading/writing status to/from database.
113.0   {station_status}             BYTE        # station_status - used when reading or saving station status. Value set by PLC when saving status. Value set by PC when reading status from database.
114.0   {date_time}                  DATETIME    # date and time from PLC. size is 8 bytes.
""".format(station_id=STATION_ID, product_type=PRODUCT_TYPE, serial_number=SERIAL_NUMBER, program_number=PROGRAM_NUMBER, program_name=PROGRAM_NAME, \
           plc_live=PLC_HEARTBEAT_FLAG, pc_live=PC_HEARTBEAT_FLAG, plc_trc_on=PLC_TRC_ON, date_time=DATE_TIME, flag_pc_ready=PC_READY_FLAG, \
           flag_plc_query=PLC_QUERY_FLAG, flag_plc_save=PLC_SAVE_FLAG, flag_db_busy=DB_BUSY_FLAG, flag_pc_browser=PC_OPEN_BROWSER_FLAG, \
           station_number=STATION_NUMBER, station_status=STATION_STATUS, checksum=CHECKSUM, \
           flag_operator_query=OPERATOR_QUERY_FLAG, flag_operator_save=OPERATOR_SAVE_FLAG, operator_status=OPERATOR_STATUS, operator_number=OPERATOR_NUMBER)


db3xxTrcHeader = """
0.0    {trc_template_count}         BYTE        # number of traceability template blocks in message body.
1.0    body.reserve_1               BYTE
""".format(trc_template_count=TRC_TMPL_COUNT)

db3xxTrcTail = """

"""

db3xxTrcTemplate = """
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
    tmp_db = db3xxHeader
    tmp_db += offset_spec_block(db3xxTrcHeader, 122)
    for i in range(0, trcTemplateNumber):  # append py templates.
        base_offset = 124
        block_size = 48
        offset = base_offset + block_size * i
        tmp_db += offset_spec_block(db3xxTrcTemplate, offset).replace("{number}", str(i))

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
