#from .constants import OPERATOR_LOGIN, OPERATOR_PASSWORD, OPERATOR_STATUS, OPERATOR_DO_LOGIN, OPERATOR_DO_LOGOUT, OPERATOR_IS_LOGIN, PC_READY_FLAG, PLC_QUERY_FLAG, PLC_SAVE_FLAG, DB_BUSY_FLAG, PC_OPEN_BROWSER_FLAG, STATION_ID, PRODUCT_TYPE, SERIAL_NUMBER, DATE_TIME, PLC_HEARTBEAT_FLAG, PC_HEARTBEAT_FLAG, TRC_TMPL_COUNT, STATION_NUMBER, STATION_STATUS, PLC_TRC_ON, PROGRAM_NAME, PROGRAM_NUMBER, CHECKSUM
from .constants import *
from .util import offset_spec_block

"""
Define layouts of DB blocks on PLC.
"""

UDT80 = """
# Tracedb_Logowanie
0.0     {operator_login}             STRING[8]   # set by PLC
10.0    {operator_password}          STRING[16]  # set by PLC
28.0    operator.res_d1              DINT        # reserve
32.0    operator.res_d2              DINT        # reserve
36.0    {operator_status}            INT         # PC: 0 - not defined, 1 - logged in, 2 - logged out, 3 - blocked, 4 - wrong password
38.0    {operator_do_login}          BOOL        # set by: PLC - flag used to login. PC - switches off flag once login is ready.
38.1    {operator_do_logout}         BOOL        # set by: PLC - flag used to logout. PC - switches off flag once logout is ready.
38.2    {operator_is_login}          BOOL        # set by: PLC - flag used to check status. constantly set by PLC. Have value 1 when {operator_status} is 1. Otherwise have value of 0. 
38.3    operator.res1_b3             BOOL        # reserve
38.4    operator.res1_b4             BOOL        # reserve
38.5    operator.res1_b5             BOOL        # reserve 
38.6    operator.res1_b6             BOOL        # reserve
38.7    operator.res1_b7             BOOL        # reserve
39.0    operator.res2_b3             BOOL        # reserve
39.1    operator.res2_b4             BOOL        # reserve
39.2    operator.res2_b5             BOOL        # reserve 
39.3    operator.res2_b3             BOOL        # reserve
39.4    operator.res2_b4             BOOL        # reserve
39.5    operator.res2_b5             BOOL        # reserve 
39.6    operator.res2_b6             BOOL        # reserve
39.7    operator.res2_b7             BOOL        # reserve
40.0    operator.res_d3              DINT        # reserve
44.0    {operator_date_time}         DATETIME    # date and time from PLC. size is 8 bytes.
# total size of 52 bytes
""".format(operator_login=OPERATOR_LOGIN, operator_password=OPERATOR_PASSWORD, operator_status=OPERATOR_STATUS, operator_do_login=OPERATOR_DO_LOGIN, \
           operator_do_logout=OPERATOR_DO_LOGIN, operator_is_login=OPERATOR_IS_LOGIN, operator_date_time=OPERATOR_DATE_TIME)

UDT81 = """
# Tracedb_Status_lokalny
0.0    __UDT81_prefix__.Status.res_d1               DINT            # reserve
4.0    __UDT81_prefix__.Status.OperationActive      BOOL            # 0 - Not Active, 1 - Switched ON
4.1    __UDT81_prefix__.Status.res1_b1              BOOL            # reserve
4.2    __UDT81_prefix__.Status.res1_b2              BOOL            # reserve
4.3    __UDT81_prefix__.Status.res1_b3              BOOL            # reserve
4.4    __UDT81_prefix__.Status.res1_b4              BOOL            # reserve
4.5    __UDT81_prefix__.Status.res1_b5              BOOL            # reserve
4.6    __UDT81_prefix__.Status.res1_b6              BOOL            # reserve
4.7    __UDT81_prefix__.Status.res1_b7              BOOL            # reserve
5.0    __UDT81_prefix__.Status.DatabaseSave         BOOL            # TODO: check if it's used?
5.1    __UDT81_prefix__.Status.res2_b1              BOOL            # reserve
5.2    __UDT81_prefix__.Status.res2_b2              BOOL            # reserve
5.3    __UDT81_prefix__.Status.res2_b3              BOOL            # reserve
5.4    __UDT81_prefix__.Status.res2_b4              BOOL            # reserve
5.5    __UDT81_prefix__.Status.res2_b5              BOOL            # reserve
5.6    __UDT81_prefix__.Status.res2_b6              BOOL            # reserve
5.7    __UDT81_prefix__.Status.res2_b7              BOOL            # reserve
6.0    __UDT81_prefix__.Status.res_i1               INT             # reserve TODO: change to int in DOC.
8.0    __UDT81_prefix__.Status.date_time            DATETIME        # date and time
16.0   __UDT81_prefix__.Status.result               INT             # 1 - OK 2 - NOK
18.0   __UDT81_prefix__.Status.res_i2               INT             # reserve
# size of 20 bytes.   
""".format(status_datetime=STATUS_DATE_TIME)


db8xxHead = """
0.0    {head_station_id}           INT         # station ID
2.0    {head_program_number}       INT         # program number
4.0    {head_nest_number}          INT         # nest number
6.0    {head_detail_id}            STRING[30]  # detail ID
38.0   head.res_i1                 INT         # reserve
40.0   head.res_i2                 INT         # reserve
42.0   head.res_d3                 DINT        # reserve
46.0   head.res_d4                 DINT        # reserve
# size of 50 bytes.
""".format(head_station_id=HEAD_STATION_ID, head_program_number=HEAD_PROGRAM_NUMBER, head_nest_number=HEAD_NEST_NUMBER, head_detail_id=HEAD_DETAIL_ID)

UDT82 = """
# Tracedb_Status_Globalny
0.0   status.res_d1                DINT        # reserve
4.0   {status_plc_trc_on}          BOOL        # traceability flag. used by PLC to indicate if tracaebility should be switched on.
4.1   {status_plc_live}            BOOL        # Controlled by PLC. blinks every 300[ms]. Indicates that PLC is alive
4.2   {status_pc_live}             BOOL        # Watched by PLC. PC should blink this bit every 300[ms] to notify that application is connected.
4.3   {status_save_only_mode}      BOOL        # 1 - baza zapisuje wyniki ale PLC nie sprawdza czy z poprzedniej stacji OK
4.4   {status_no_id_scanning}      BOOL        # 1 - praca bez skanowania ID detalu.
4.5   {status_no_type_verify}      BOOL        # 1 - praca bez weryfikacji typu / rezerwa
4.6   {status_no_scanning}         BOOL        # 1 - wariant bez skanowania (mimo ze praca ze skanowaniem id detalu)
4.7   status_rez_b7                BOOL        # reserve
5.0   {flag_plc_save}              BOOL        # PLC_Save bit - monitored by PC, set by PLC. PC saves status if set to True. Once PC finishes it sets it back to False.
5.1   {flag_plc_query}             BOOL        # PLC_Query bit - monitored by PC, set by PLC. PC reads status from database if set to True. Once PC finishes it sets it back to False.
5.2   {flag_id_query}              BOOL        # ID_Query bit - PLC asks PC to set detail_id
5.3   {flag_pc_ready}              BOOL        # PC_Ready bit. Monitored by PLC. PCL waits for True. PC sets to False when it starts processing. PC sets back to True once processing is finished.
5.4   {flag_id_ready}              BOOL        # ID_Ready bit - PC indicates that detail_id is already set. 
5.5   status.res_b5                BOOL        # reserve
5.6   status.res_b6                BOOL        # reserve
5.7   status.res_b7                BOOL        # reserve
6.0   status.res_i1                INT         # reserve
8.0   {status_datetime}            DATETIME    # date and time
16.0   status.station_result       INT         # wynik ze stanowiska
18.0   status.database_result      INT         # wynik z bazy danych
# size of 20 bytes. 
""".format(status_plc_live=PLC_HEARTBEAT_FLAG, status_pc_live=PC_HEARTBEAT_FLAG, status_plc_trc_on=PLC_TRC_ON, status_datetime=STATUS_DATE_TIME, \
    status_save_only_mode=STATUS_SAVE_ONLY_MODE_FLAG, status_no_id_scanning=STATUS_NO_ID_SCANNING_FLAG,  status_no_type_verify=STATUS_NO_TYPE_VERIFY_FLAG, status_no_scanning=STATUS_NO_SCANNING_FLAG, \
    flag_pc_ready=PC_READY_FLAG, flag_plc_query=PLC_QUERY_FLAG, flag_plc_save=PLC_SAVE_FLAG, flag_id_query=ID_QUERY_FLAG, flag_id_ready=ID_READY_FLAG)

db8xxHeader = """# db8xxHeader BEGIN
""" + UDT80 +  offset_spec_block(db8xxHead, 52) + offset_spec_block(UDT82, 52+50)  + """
# db8xxHeader END - size of 122
"""  

LaserMarking = """
# LaserMarking Begin
0.0     LaserMarking.LaserProgramName                        STRING[20]      # Nazwa Programu Lasera
22.0    LaserMarking.id                                      STRING[30]      # Wypalane id
54.0    LaserMarking.res1                                    DINT            # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "LaserMarking"), 58) + """
# LaserMarking END - size of 78 bytes
"""

LaserMarkingVerification = """
# LaserMarkingVerification Begin
0.0     LaserMarkingVerification.read_id                     STRING[30]      # Odczytane id ze skanera DMC
32.0    LaserMarkingVerification.res1                        DINT            # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "LaserMarkingVerification"), 36) + """
# LaserMarkingVerification END - size of 56 bytes
"""

UDT83 = """
# Tracedb_laser BEGIN
""" + db8xxHeader + offset_spec_block(LaserMarking, 122) + offset_spec_block(LaserMarkingVerification, 122+78) + """
# Tracedb_laser END - size of 256 bytes
""" 

ReadID = """
# ReadID Begin
0.0     ReadID.id                                            STRING[30]      # Odczytane id ze skanera DMC
32.0    ReadID.res_d1                                        DINT            # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "ReadID"), 36) + """
# ReadID END - size of 56 bytes
"""

SensorOiling = """
# SensorOiling Begin
0.0     SensorOiling.done                                    INT      # 0 - NO, 1 - YES
2.0     SensorOiling.res_d1                                  DINT     # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "SensorOiling"), 6) + """
# SensorOiling END - size of 26 bytes
"""

ManualSensorMounting = """
# ManualSensorMounting Begin
0.0     ManualSensorMounting.done                            INT      # 0 - NO, 1 - YES
2.0     ManualSensorMounting.res_d1                          DINT     # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "ManualSensorMounting"), 6) + """
# ManualSensorMounting END - size of 26 bytes
"""

SensorDMC = """
# SensorDMC Begin
0.0     SensorDMC.reference                                  STRING[50]      # 
52.0    SensorDMC.read                                       STRING[50]      # 
104.0   SensorDMC.compare                                    STRING[50]      # 
156.0   SensorDMC.from_string_sign                           INT
158.0   SensorDMC.string_length                              INT
160.0   SensorDMC.sensor_type                                INT
162.0   SensorDMC.res_d1                                     DINT
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "SensorDMC"), 166) + """
# SensorDMC END - size of 186 bytes
"""

AutomaticSensorMounting = """
# AutomaticSensorMounting Begin
0.0     AutomaticSensorMounting.screwdriver_program_number   INT 
2.0     AutomaticSensorMounting.torque                       REAL
6.0     AutomaticSensorMounting.angle                        REAL
10.0    AutomaticSensorMounting.res_d1                       DINT
14.0    AutomaticSensorMounting.torque_max                   REAL
18.0    AutomaticSensorMounting.torque_min                   REAL
22.0    AutomaticSensorMounting.angle_max                    REAL
26.0    AutomaticSensorMounting.angle_min                    REAL
30.0    AutomaticSensorMounting.res_r2                       REAL
34.0    AutomaticSensorMounting.res_r3                       REAL
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "AutomaticSensorMounting"), 38) + """
# AutomaticSensorMounting END - size of 58 bytes
"""

# TODO: implement ME
FlowTest = """
# FlowTest Begin
0.0     FlowTest.done                                        INT      # 0 - NO, 1 - YES
2.0     FlowTest.res_d1                                      DINT     # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "FlowTest"), 6) + """
# FlowTest END - size of 400 bytes
"""

Marking = """
# Marking Begin
0.0     Marking.done                                         INT      # 0 - NO, 1 - YES
2.0     Marking.res_d1                                       DINT     # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "Marking"), 6) + """
# Marking END - size of 26 bytes
"""


UDT84 = """
# Tracedb_12705 BEGIN
""" + db8xxHeader + offset_spec_block(ReadID, 122) + offset_spec_block(SensorOiling, 122+56) + offset_spec_block(ManualSensorMounting, 122+56+26) \
+ offset_spec_block(SensorDMC, 122+56+26+26) + offset_spec_block(AutomaticSensorMounting, 122+56+26+26+186) + offset_spec_block(FlowTest, 122+56+26+26+186+58) \
+ offset_spec_block(Marking, 122+56+26+26+186+58+400) + """
# Tracedb_12705 END - size of 900 bytes
""" 


UDT85 = """
# Tracedb_12706 BEGIN
""" + db8xxHeader + offset_spec_block(ReadID, 122) + """
# Tracedb_12706 END - size of 628 bytes
""" 


UDT88 = """
# Tracedb_12707 BEGIN
""" + db8xxHeader + offset_spec_block(ReadID, 122) + """
# Tracedb_12707 END - size of 518 bytes
""" 




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
# St 12705 - Stacja Lasera
#############################################################################################
db_specs['c1']['db500'] = UDT83
db_specs['c1']['db501'] = UDT84
db_specs['c1']['db502'] = UDT84

#############################################################################################
# St 12706 - Stacja Testu przeplywu
#############################################################################################
db_specs['c2']['db503'] = UDT85
db_specs['c2']['db504'] = UDT85

#############################################################################################
# St 12707 - Stacja Znakowanie BMW
#############################################################################################
db_specs['c3']['db505'] = UDT88  # lewa
db_specs['c3']['db506'] = UDT88  # prawa

# special cases hacking...
db100 = ""
db101 = ""
db1 = ""
db2 = ""
db3 = ""
