#from .constants import OPERATOR_LOGIN, OPERATOR_PASSWORD, OPERATOR_STATUS, OPERATOR_DO_LOGIN, OPERATOR_DO_LOGOUT, OPERATOR_IS_LOGIN, PC_READY_FLAG, PLC_QUERY_FLAG, PLC_SAVE_FLAG, DB_BUSY_FLAG, PC_OPEN_BROWSER_FLAG, STATION_ID, PRODUCT_TYPE, SERIAL_NUMBER, DATE_TIME, PLC_HEARTBEAT_FLAG, PC_HEARTBEAT_FLAG, TRC_TMPL_COUNT, STATION_NUMBER, STATION_STATUS, PLC_TRC_ON, PROGRAM_NAME, PROGRAM_NUMBER, CHECKSUM
from .constants import *
from .util import offset_spec_block

"""
Define layouts of DB blocks on PLC.
"""

UDT80 = """
# Tracedb_Logowanie - Begin
0.0     {operator_login}                                     STRING[8]   # set by PLC
10.0    {operator_password}                                  STRING[16]  # set by PLC
28.0    operator.res_r1                                      REAL        # reserve
32.0    operator.res_r2                                      REAL        # reserve
36.0    {operator_status}                                    INT         # PC: 0 - not defined, 1 - logged in, 2 - logged out, 3 - blocked, 4 - wrong password
38.0    {operator_do_login}                                  BOOL        # set by: PLC - flag used to login. PC - switches off flag once login is ready.
38.1    {operator_do_logout}                                 BOOL        # set by: PLC - flag used to logout. PC - switches off flag once logout is ready.
38.2    {operator_is_login}                                  BOOL        # set by: PLC - flag used to check status. constantly set by PLC. Have value 1 when {operator_status} is 1. Otherwise have value of 0. 
38.3    operator.res1_b3                                     BOOL        # reserve
38.4    operator.res1_b4                                     BOOL        # reserve
38.5    operator.res1_b5                                     BOOL        # reserve 
38.6    operator.res1_b6                                     BOOL        # reserve
38.7    operator.res1_b7                                     BOOL        # reserve
39.0    operator.res2_b3                                     BOOL        # reserve
39.1    operator.res2_b4                                     BOOL        # reserve
39.2    operator.res2_b5                                     BOOL        # reserve 
39.3    operator.res2_b3                                     BOOL        # reserve
39.4    operator.res2_b4                                     BOOL        # reserve
39.5    operator.res2_b5                                     BOOL        # reserve 
39.6    operator.res2_b6                                     BOOL        # reserve
39.7    operator.res2_b7                                     BOOL        # reserve
40.0    operator.res_r3                                      REAL        # reserve
44.0    {operator_date_time}                                 DATETIME    # date and time from PLC. size is 8 bytes.
# Tracedb_Logowanie - END - size of 52 bytes
""".format(operator_login=OPERATOR_LOGIN, operator_password=OPERATOR_PASSWORD, operator_status=OPERATOR_STATUS, operator_do_login=OPERATOR_DO_LOGIN, operator_do_logout=OPERATOR_DO_LOGOUT, operator_is_login=OPERATOR_IS_LOGIN, operator_date_time=OPERATOR_DATE_TIME)

UDT81 = """
# # Tracedb_Status_lokalny - Begin
0.0    __UDT81_prefix__.Status.res_r1                        REAL        # reserve
4.0    __UDT81_prefix__.Status.OperationActive               BOOL        # 0 - Not Active, 1 - Switched ON
4.1    __UDT81_prefix__.Status.res1_b1                       BOOL        # reserve
4.2    __UDT81_prefix__.Status.res1_b2                       BOOL        # reserve
4.3    __UDT81_prefix__.Status.res1_b3                       BOOL        # reserve
4.4    __UDT81_prefix__.Status.res1_b4                       BOOL        # reserve
4.5    __UDT81_prefix__.Status.res1_b5                       BOOL        # reserve
4.6    __UDT81_prefix__.Status.res1_b6                       BOOL        # reserve
4.7    __UDT81_prefix__.Status.res1_b7                       BOOL        # reserve
5.0    __UDT81_prefix__.Status.DatabaseSave                  BOOL        # TODO: check if it's used?
5.1    __UDT81_prefix__.Status.res2_b1                       BOOL        # reserve
5.2    __UDT81_prefix__.Status.res2_b2                       BOOL        # reserve
5.3    __UDT81_prefix__.Status.res2_b3                       BOOL        # reserve
5.4    __UDT81_prefix__.Status.res2_b4                       BOOL        # reserve
5.5    __UDT81_prefix__.Status.res2_b5                       BOOL        # reserve
5.6    __UDT81_prefix__.Status.res2_b6                       BOOL        # reserve
5.7    __UDT81_prefix__.Status.res2_b7                       BOOL        # reserve
6.0    __UDT81_prefix__.Status.res_i1                        INT         # reserve
8.0    __UDT81_prefix__.Status.date_time                     DATETIME    # date and time
16.0   __UDT81_prefix__.Status.result                        INT         # 1 - OK 2 - NOK
18.0   __UDT81_prefix__.Status.res_i2                        INT         # reserve
# # Tracedb_Status_lokalny - END - size of 20 bytes.   
""".format(status_datetime=STATUS_DATE_TIME)


GlobalHead = """
# Tracedb_Global_Head - Begin
0.0    {head_station_id}                                     INT         # station ID
2.0    {head_program_number}                                 INT         # program number
4.0    {head_nest_number}                                    INT         # nest number
6.0    {head_detail_id}                                      STRING[30]  # detail ID
38.0   head.res_i1                                           INT         # reserve
40.0   head.res_i2                                           INT         # reserve
42.0   head.res_r3                                           REAL        # reserve
46.0   head.res_r4                                           REAL        # reserve
# Tracedb_Global_Head - END - size of 50 bytes.
""".format(head_station_id=HEAD_STATION_ID, head_program_number=HEAD_PROGRAM_NUMBER, head_nest_number=HEAD_NEST_NUMBER, head_detail_id=HEAD_DETAIL_ID)

UDT82 = """
# Tracedb_Status_Globalny - Begin
0.0   status.res_r1                                          REAL        # reserve
4.0   {status_plc_trc_on}                                    BOOL        # traceability flag. used by PLC to indicate if tracaebility should be switched on.
4.1   {status_plc_live}                                      BOOL        # Controlled by PLC. blinks every 300[ms]. Indicates that PLC is alive
4.2   {status_pc_live}                                       BOOL        # Watched by PLC. PC should blink this bit every 300[ms] to notify that application is connected.
4.3   {status_save_only_mode}                                BOOL        # 1 - baza zapisuje wyniki ale PLC nie sprawdza czy z poprzedniej stacji OK
4.4   {status_no_id_scanning}                                BOOL        # 1 - praca bez skanowania ID detalu.
4.5   {status_no_type_verify}                                BOOL        # 1 - praca bez weryfikacji typu / rezerwa
4.6   {status_no_scanning}                                   BOOL        # 1 - wariant bez skanowania (mimo ze praca ze skanowaniem id detalu)
4.7   status_rez_b7                                          BOOL        # reserve
5.0   {flag_plc_save}                                        BOOL        # PLC_Save bit - monitored by PC, set by PLC. PC saves status if set to True. Once PC finishes it sets it back to False.
5.1   {flag_plc_query}                                       BOOL        # PLC_Query bit - monitored by PC, set by PLC. PC reads status from database if set to True. Once PC finishes it sets it back to False.
5.2   {flag_id_query}                                        BOOL        # ID_Query bit - PLC asks PC to set next detail_id to be burned with laser. Output is generated by database and saved to HEAD_DETAIL_ID.
5.3   {flag_pc_ready}                                        BOOL        # PC_Ready bit. Monitored by PLC. PCL waits for True. PC sets to False when it starts processing. PC sets back to True once processing is finished.
5.4   {flag_id_ready}                                        BOOL        # ID_Ready bit - PC indicates that next_detail_id is already set - PC processing finished.
5.5   status.res_b5                                          BOOL        # reserve
5.6   status.res_b6                                          BOOL        # reserve
5.7   status.res_b7                                          BOOL        # reserve
6.0   {status_station_number}                                INT         # station_number - used to query station status. Result should be saved in status_database_result  (System will use head.station_id while saving status to database)
8.0   {status_datetime}                                      DATETIME    # date and time
16.0  {status_station_result}                                INT         # wynik ze stanowiska
18.0  {status_database_result}                               INT         # wynik z bazy danych
# Tracedb_Status_Globalny - END - size of 20 bytes. 
""".format(status_plc_live=PLC_HEARTBEAT_FLAG, status_pc_live=PC_HEARTBEAT_FLAG, status_plc_trc_on=PLC_TRC_ON, status_datetime=STATUS_DATE_TIME, \
    status_save_only_mode=STATUS_SAVE_ONLY_MODE_FLAG, status_no_id_scanning=STATUS_NO_ID_SCANNING_FLAG, status_no_type_verify=STATUS_NO_TYPE_VERIFY_FLAG, status_no_scanning=STATUS_NO_SCANNING_FLAG, \
    flag_pc_ready=PC_READY_FLAG, flag_plc_query=PLC_QUERY_FLAG, flag_plc_save=PLC_SAVE_FLAG, flag_id_query=ID_QUERY_FLAG, flag_id_ready=ID_READY_FLAG, \
    status_station_result=STATUS_STATION_RESULT, status_database_result=STATUS_DATABASE_RESULT, status_station_number=STATUS_STATION_NUMBER)

db8xxHeader = """# db8xxHeader BEGIN
""" \
+ offset_spec_block(UDT80, 0) \
+ offset_spec_block(GlobalHead, 52) \
+ offset_spec_block(UDT82, 52+50) \
+ """
# db8xxHeader END - size of 122
"""  

LaserMarking = """
# LaserMarking Begin
0.0     LaserMarking.LaserProgramName                        STRING[20]  # Nazwa Programu Lasera
22.0    LaserMarking.id                                      STRING[30]  # Wypalane id
54.0    LaserMarking.res1                                    REAL        # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "LaserMarking"), 58) + """
# LaserMarking END - size of 78 bytes
"""

LaserMarkingVerification = """
# LaserMarkingVerification Begin
0.0     LaserMarkingVerification.id                         STRING[30]  # Odczytane id ze skanera DMC
32.0    LaserMarkingVerification.res1                        REAL        # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "LaserMarkingVerification"), 36) + """
# LaserMarkingVerification END - size of 56 bytes
"""

UDT83 = """
# Tracedb_laser BEGIN
""" \
+ db8xxHeader \
+ offset_spec_block(LaserMarking, 122) \
+ offset_spec_block(LaserMarkingVerification, 122+78) \
+ """
# Tracedb_laser END - size of 256 bytes
""" 

ReadID = """
# ReadID Begin
0.0     ReadID.id                                            STRING[30]  # Odczytane id ze skanera DMC
32.0    ReadID.res_r1                                        REAL        # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "ReadID"), 36) + """
# ReadID END - size of 56 bytes
"""

SensorOiling = """
# SensorOiling Begin
0.0     SensorOiling.done                                    INT         # 0 - NO, 1 - YES
2.0     SensorOiling.res_r1                                  REAL        # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "SensorOiling"), 6) + """
# SensorOiling END - size of 26 bytes
"""

ManualSensorMounting = """
# ManualSensorMounting Begin
0.0     ManualSensorMounting.done                            INT         # 0 - NO, 1 - YES
2.0     ManualSensorMounting.res_r1                          REAL        # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "ManualSensorMounting"), 6) + """
# ManualSensorMounting END - size of 26 bytes
"""

SensorDMC = """
# SensorDMC Begin
0.0     SensorDMC.reference                                  STRING[50]  # 
52.0    SensorDMC.read                                       STRING[50]  # 
104.0   SensorDMC.compare                                    STRING[50]  # 
156.0   SensorDMC.from_string_sign                           INT
158.0   SensorDMC.string_length                              INT
160.0   SensorDMC.sensor_type                                INT
162.0   SensorDMC.res_r1                                     DINT
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "SensorDMC"), 166) + """
# SensorDMC END - size of 186 bytes
"""

AutomaticSensorMounting = """
# AutomaticSensorMounting Begin
0.0     AutomaticSensorMounting.screwdriver_program_number   INT 
2.0     AutomaticSensorMounting.torque                       REAL
6.0     AutomaticSensorMounting.angle                        REAL
10.0    AutomaticSensorMounting.res_r1                       DINT
14.0    AutomaticSensorMounting.torque_max                   REAL
18.0    AutomaticSensorMounting.torque_min                   REAL
22.0    AutomaticSensorMounting.angle_max                    REAL
26.0    AutomaticSensorMounting.angle_min                    REAL
30.0    AutomaticSensorMounting.res_r2                       REAL
34.0    AutomaticSensorMounting.res_r3                       REAL
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "AutomaticSensorMounting"), 38) + """
# AutomaticSensorMounting END - size of 58 bytes
"""

FlowTestHeader = """
# FlowTest Begin
0.0     FlowTest.type                                        INT         # Test type 1 - Cycle, 2 - Dummy, 3 - Calibration 
2.0     FlowTest.dummy1                                      INT         # DummyiKalibrGodzZmaiana1
4.0     FlowTest.dummy2                                      INT         # DummyiKalibrGodzZmaiana2
6.0     FlowTest.dummy3                                      INT         # DummyiKalibrGodzZmaiana3
8.0     FlowTest.res_r1                                      REAL        # reserve
12.0    FlowTest.res_r2                                      REAL        # reserve
# FlowTestHeader size is 16 bytes
"""

FlowTestFooter = """
# FlowTest END - size of 400 bytes
"""

FlowTestTemplate = """
# FlowTestTemplate {number} - Begin
0.0    FlowTest.{number}.FlowResult                          REAL        # [ln/min] 
4.0    FlowTest.{number}.FlowMax                             REAL        # [ln/min]
8.0    FlowTest.{number}.FlowMin                             REAL        # [ln/min]
12.0   FlowTest.{number}.res_r1                              REAL        # reserve
16.0   FlowTest.{number}.res_r2                              REAL        # reserve
20.0   FlowTest.{number}.TimeElapsed                         REAL        # [s]
24.0   FlowTest.{number}.res_r3                              REAL        # reserve
""" + offset_spec_block(UDT81, 28).replace("__UDT81_prefix__", "FlowTest.{number}") + """
# FlowTestTemplate {number} - END template size is 48
"""

FlowTest = FlowTestHeader
for i in range(0, 7):  # append eight templates
    header_size = 16
    template_size = 48
    offset = header_size + template_size * i
    FlowTest += offset_spec_block(FlowTestTemplate, offset).replace("{number}", str(i))
FlowTest += FlowTestFooter

Marking = """
# Marking Begin
0.0     Marking.done                                         INT         # 0 - NO, 1 - YES
2.0     Marking.res_r1                                       REAL        # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "Marking"), 6) + """
# Marking END - size of 26 bytes
"""


UDT84 = """
# Tracedb_12705 BEGIN
""" + db8xxHeader \
+ offset_spec_block(ReadID, 122) \
+ offset_spec_block(SensorOiling, 122+56) \
+ offset_spec_block(ManualSensorMounting, 122+56+26) \
+ offset_spec_block(SensorDMC, 122+56+26+26) \
+ offset_spec_block(AutomaticSensorMounting, 122+56+26+26+186) \
+ offset_spec_block(FlowTest, 122+56+26+26+186+58) \
+ offset_spec_block(Marking, 122+56+26+26+186+58+400) \
+ """
# Tracedb_12705 END - size of 900 bytes
""" 

Teilabfrage = """
# Teilabfrage Begin                                                      # ; FC1 NW12
0.0    Teilabfrage.done                                      INT         # 0 - NO, 1 - YES
2.0    Teilabfrage.res_r1                                    REAL        # reserve # DB8.DBX  656.2 
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "Teilabfrage"), 6) + """
# Teilabfrage END - size of 26 bytes
"""

Nadelpruefung = """
# Nadelpruefung Begin                                                    # ; FC1 NW12
0.0    Nadelpruefung.done                                    INT         # 0 - NO, 1 - YES
2.0    Nadelpruefung.res_r1                                  REAL        # reserve # DB8.DBX656.6
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "Nadelpruefung"), 6) + """
# Nadelpruefung END - size of 26 bytes
"""

Mutternabfrage = """
# Mutternabfrage Begin                                                   # DB9.DBX3.7; FB310
0.0    Mutternabfrage.done                                   INT         # 0 - NO, 1 - YES
2.0    Mutternabfrage.res_r1                                 REAL        # reserve # DB8.DBX656.5
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "Mutternabfrage"), 6) + """
# Mutternabfrage END - size of 26 bytes
"""

Kreismarkierer = """
# Kreismarkierer Begin                                                   # DB9.DBX3.4; FB312; Znakowanie
0.0    Kreismarkierer.done                                   INT         # 0 - NO, 1 - YES
2.0    Kreismarkierer.servomotor_number                      INT         # numer silownika # DB8.DBW658
4.0    Kreismarkierer.marking_time                           REAL        # czas znakowania 
8.0    Kreismarkierer.res_r1                                 REAL        # reserve # DB8.DBX656.3
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "Kreismarkierer"), 12) + """
# Kreismarkierer END - size of 32 bytes
"""

Durchflusspruefung = """
# Durchflusspruefung Begin                                               # DB8.DBX656.7; Durchflusspruefung - Tego chyba nie ma na tej stacji
0.0    Durchflusspruefung.done                               INT         # 0 - NO, 1 - YES
2.0    Durchflusspruefung.res_r1                             REAL        # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "Durchflusspruefung"), 6) + """
# Durchflusspruefung END - size of 26 bytes
"""

DrucksensorNachPruefling = """
# DrucksensorNachPruefling Begin                                         # DB8.DBX656.4; Drucksensor nach Pruefling
0.0    DrucksensorNachPruefling.done                         INT         # 0 - NO, 1 - YES
2.0    DrucksensorNachPruefling.res_r1                       REAL        # reserve # DB8.DBX656.5
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "DrucksensorNachPruefling"), 6) + """
# DrucksensorNachPruefling END - size of 26 bytes
"""

SchemaParams = """
# SchemaParams Begin                                         # Parametry z nastaw
0.0    SchemaParams.P_He_vor_PT_REAL                         REAL        # DB475.DBD8; [bar] HMI_IW.Kammer1.P_He_vor_PT_REAL 
4.0    SchemaParams.P_He_Versorgung_REAL                     REAL        # DB475.DBD448; [bar] HMI_IW.Anlage.P_He_Versorgung_REAL 
8.0    SchemaParams.P_Vac_PT_REAL                            REAL        # DB475.DBD20; [mbar] HMI_IW.Kammer1.P_Vac_PT_REAL
12.0   SchemaParams.P_He_nach_PT_REAL                        REAL        # DB475.DBD14; [bar] HMI_IW.Kammer1.P_He_nach_PT_REAL 
16.0   SchemaParams.Leckrate                                 REAL        # DB9.DBD10; [mbar l/s] Pruef-Erg.Glocke.Kammer1.Leckrate 
20.0   SchemaParams.P_Glocke_REAL                            REAL        # DB475.DBD2; [mbar] HMI_IW.Kammer1.P_Glocke_REAL 
24.0   SchemaParams.Roh_Mittel_Mul_Faktor                    REAL        # DB20.DBD608; [mbar l/s] INFICON-DB.Leckratenscalierung .Roh_Mittel_Mul_Faktor
28.0   SchemaParams.res_r1                                   REAL        # reserve
32.0   SchemaParams.res_r2                                   REAL        # reserve
36.0   SchemaParams.res_r3                                   REAL        # reserve
40.0   SchemaParams.res_r4                                   REAL        # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "SchemaParams"), 44) + """
# SchemaParams END - size of 64 bytes
"""

PresetParams = """
# PresetParams Begin                                         # Parametry z nastaw
0.0    PresetParams.GloVacGrob_Soll                          REAL        # DB8.DBD4; [bar] Glockenvakuum GROB 
4.0    PresetParams.GloVacFein_Soll                          REAL        # DB8.DBD16; [bar] Glockenvakuum FEIN
8.0    PresetParams.GloVacGrob                               REAL        # DB8.DBD160; [s] Ueberwachungszeit Glockenvakuum GROB
12.0   PresetParams.GloVacFein                               REAL        # DB8.DBD164; [s] Ueberwachungszeit Glockenvakuum FEIN
16.0   PresetParams.PtVac_Atmos_Soll_1                       REAL        # DB8.DBD28; [mbar] Pruefteil-Vakkum ATMOSPHAERE
20.0   PresetParams.PtVac_He_Soll_1                          REAL        # DB8.DBD56; [mbar] Pruefteil-Vakkum HELIUM
24.0   PresetParams.PT_evakuieren_Atmos                      REAL        # DB8.DBD172; [s] Ueberwachungszeit Pruefteil evakuieren ATMOSPHAERE
28.0   PresetParams.PT_evakuieren_Helium                     REAL        # DB8.DBD176; [s] Ueberwachungszeit Pruefteil evakuieren HELIUM
32.0   PresetParams.PT_fluten_1                              REAL        # DB8.DBD180; [s] Pruefteil mit Atmosphaere fluten
36.0   PresetParams.Helium_Min_1                             REAL        # DB8.DBD44; [bar] Helium -Fuelldruck MIN
40.0   PresetParams.Helium_Soll_1                            REAL        # DB8.DBD40; [bar] Helium -Fuelldruck SOLL
44.0   PresetParams.HeliumFuellen                            REAL        # DB8.DBD184; [s] Ueberwachungszeit Pruefteil mit Helium fuellen
48.0   PresetParams.Helium_entspannen_HD                     REAL        # DB8.DBD168; [s] Ueberwachungszeit Helium entspannen
52.0   PresetParams.FrgHeliumEvakuieren                      REAL        # DB8.DBD48; [bar] Freigabe Pruefteil evakuieren ab
56.0   PresetParams.res_r1                                   REAL        # reserve
60.0   PresetParams.res_r2                                   REAL        # reserve
64.0   PresetParams.res_r3                                   REAL        # reserve
68.0   PresetParams.res_r4                                   REAL        # reserve
72.0   PresetParams.Prueffreigabe                            INT         # DB8.DBW480; 1-Tylko komora 1, 2-Tylko komora 2, 3-Obie komory
74.0   PresetParams.Doppel_WT                                INT         # DB8.DBX656.1; Doppel-WT; 0-NIE; 1-TAK
76.0   PresetParams.res_r1                                   REAL        # reserve
80.0   PresetParams.res_r2                                   REAL        # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "PresetParams"), 84) + """
# PresetParams END - size of 104 bytes
"""

UeberwachGroblBeGlocEvak = """
# UeberwachGroblBeGlocEvak Begin                                         # DB9.DBX3.2; FB310; Ueberwachung Grobleck beim Glocke ev akuieren
0.0    UeberwachGroblBeGlocEvak.done                         INT         # 0 - NO, 1 - YES
2.0    UeberwachGroblBeGlocEvak.res_r1                       REAL        # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "UeberwachGroblBeGlocEvak"), 6) + """
# UeberwachGroblBeGlocEvak END - size of 26 bytes
"""

UeberwachGroblBeHeliumfu = """
# UeberwachGroblBeHeliumfu Begin                                         # DB9.DBX3.3; FB310; Ueberwachung Grobleck beim Heliumfuel len
0.0    UeberwachGroblBeHeliumfu.done                         INT         # 0 - NO, 1 - YES
2.0    UeberwachGroblBeHeliumfu.res_r1                       REAL        # reserve # DB8.DBX656.5
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "UeberwachGroblBeHeliumfu"), 6) + """
# UeberwachGroblBeHeliumfu END - size of 26 bytes
"""

Leckrate = """
# Leckrate Begin                                                         # DB9.DBX1.1; FB310; Wyciek
0.0    Leckrate.leak_result                                  REAL        # DB9.DBD10; [mbar l/s]
4.0    Leckrate.leak_max                                     REAL        # DB8.DBD328; [mbar l/s] Maximale Leckrate
8.0    Leckrate.leak_Max_Mantisse_REZ                        REAL        # DB8.DBD320; Maximal zulaessige Leckrate Mantisse
12.0   Leckrate.leak_Max_Exponent_REZ                        REAL        # DB8.DBD324; Maximal zulaessige Leckrate Exponent
16.0   Leckrate.leak_Grobleck                                REAL        # DB8.DBD340; [mbar l/s] Leckrate Grobleckerkennung
20.0   Leckrate.leak_Mantisse_Grob_REZ                       REAL        # DB8.DBD332; Maximal zulaessige Leckrate Mantisse
24.0   Leckrate.leak_Exponent_Grob_REZ                       REAL        # DB8.DBD336; Maximal zulaessige Leckrate Exponent
28.0   Leckrate.leak_UebernahmeLeckrate                      REAL        # DB8.DBD188; [s] uebernahme Leckrate nach
32.0   Leckrate.res_r1                                       REAL        # reserve
36.0   Leckrate.res_r2                                       REAL        # reserve
40.0   Leckrate.res_r3                                       REAL        # reserve
44.0   Leckrate.res_r4                                       REAL        # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "Leckrate"), 48) + """
# Leckrate END - size of 68 bytes
"""

UDT85 = """
# Tracedb_12706 BEGIN
""" + db8xxHeader \
+ offset_spec_block(ReadID, 122) \
+ offset_spec_block(Teilabfrage, 122+56) \
+ offset_spec_block(Nadelpruefung, 122+56+26) \
+ offset_spec_block(Mutternabfrage, 122+56+26+26) \
+ offset_spec_block(Kreismarkierer, 122+56+26+26+26) \
+ offset_spec_block(Durchflusspruefung, 122+56+26+26+26+32) \
+ offset_spec_block(DrucksensorNachPruefling, 122+56+26+26+26+32+26) \
+ offset_spec_block(SchemaParams, 122+56+26+26+26+32+26+26) \
+ offset_spec_block(PresetParams, 122+56+26+26+26+32+26+26+64) \
+ offset_spec_block(UeberwachGroblBeGlocEvak, 122+56+26+26+26+32+26+26+64+104) \
+ offset_spec_block(UeberwachGroblBeHeliumfu, 122+56+26+26+26+32+26+26+64+104+26) \
+ offset_spec_block(Leckrate, 122+56+26+26+26+32+26+26+64+104+26+26) + """
# Tracedb_12706 END - size of 628 bytes
""" 

Tool = """
# Tool Begin
0.0     Tool.name                                            STRING[30]  # DB554.DBW2; np. TU1 : WP10D00-D
32.0    Tool.res_r1                                          REAL        # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "Tool"), 36) + """
# Tool END - size of 56 bytes
"""

Detection = """
# Detection Begin
0.0     Detection.name                                       STRING[20]  # DB553.DBW6; np. BRAK lub MODEL 1
22.0    Detection.res_r1                                     REAL        # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "Detection"), 26) + """
# Detection END - size of 46 bytes
"""

VendorDMCCodeMarking = """
# VendorDMCCodeMarking Begin
0.0     VendorDMCCodeMarking.laser_program_name              STRING[20]  # DB553.DBW2; np. BMW403DM
22.0    VendorDMCCodeMarking.laser_program_filename          STRING[20]  # DB560.DBB0; np. Job_0002.xlp
44.0    VendorDMCCodeMarking.laser_program_number            INT         # numer programu lasera
46.0    VendorDMCCodeMarking.res_r1                          REAL        # reserve
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "VendorDMCCodeMarking"), 50) + """
# VendorDMCCodeMarking END - size of 70 bytes
"""

VendorDMCCodeRead = """
# VendorDMCCodeRead Begin
0.0     VendorDMCCodeRead.vendor_dmc                         STRING[60]  # DB559.DBB24; np. 
62.0    VendorDMCCodeRead.dmc_position                       STRING[20]  # DB553.DBW2; np. BMW403DM
84.0    VendorDMCCodeRead.res_r1                             REAL        # reserve
88.0    VendorDMCCodeRead.res_r2                             REAL        # reserve # Blad odczytu. DB559.DBX0.1; 1-OK; 2-NOK 
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "VendorDMCCodeRead"), 92) + """
# VendorDMCCodeRead END - size of 112 bytes
"""

VendorDMCCodeClass = """
# VendorDMCCodeRead Begin
0.0     VendorDMCCodeClass.CodeClass                         STRING[2]   # DB559.DBB17; np. A  
4.0     VendorDMCCodeClass.Modulation                        STRING[2]   # DB559.DBB8; np. A
8.0     VendorDMCCodeClass.FixedPatternDamage                STRING[2]   # DB559.DBB9; np. A
12.0    VendorDMCCodeClass.SymbolContrast                    STRING[2]   # DB559.DBB11; np. A
16.0    VendorDMCCodeClass.AxialNonUniformity                STRING[2]   # DB559.DBB12; np. A
20.0    VendorDMCCodeClass.UnusedErrorCorrection             STRING[2]   # DB559.DBB13; np. A
24.0    VendorDMCCodeClass.GridNonUniformity                 STRING[2]   # DB559.DBB15; np. A
28.0    VendorDMCCodeClass.Class_3_res                       STRING[2]   # DB559.DBB10; np. A
32.0    VendorDMCCodeClass.Class_7_res                       STRING[2]   # DB559.DBB14; np. A
36.0    VendorDMCCodeClass.Class_9_res                       STRING[2]   # DB559.DBB16; np. A
40.0    VendorDMCCodeClass.MinimalClass_res                  STRING[2]   # DB559.DBB18; np. A
44.0    VendorDMCCodeClass.AcceptableClass                   STRING[2]   # DB559.DBW22; np. A
48.0    VendorDMCCodeClass.CurrentClass                      STRING[2]   # DB559.DBW20; np. A 
52.0    VendorDMCCodeClass.res_r1                            REAL        # reserve
56.0    VendorDMCCodeClass.res_r2                            REAL        # reserve # Jakosc odczytu. DB559.DBW4; 1-OK; 2-NOK
""" + offset_spec_block(UDT81.replace("__UDT81_prefix__", "VendorDMCCodeClass"), 60) + """
# VendorDMCCodeClass END - size of 80 bytes
"""

UDT88 = """
# Tracedb_12707 BEGIN
""" + db8xxHeader \
+ offset_spec_block(ReadID, 122) \
+ offset_spec_block(Tool, 122+56) \
+ offset_spec_block(Detection, 122+56+56) \
+ offset_spec_block(VendorDMCCodeMarking, 122+56+56+46) \
+ offset_spec_block(VendorDMCCodeRead, 122+56+56+46+70) \
+ offset_spec_block(VendorDMCCodeClass, 122+56+56+46+70+112) \
+ """
# Tracedb_12707 END - size of 542 bytes
""" 

# create db map for given controller.
# controller id from config file should be used as key. currently controller id's are hardcoded
db_specs = {
    'c1': {},
    'c2': {},
    'c3': {},
}

#############################################################################################
# St 12705 - Stacja Lasera
#############################################################################################
db_specs['c1']['db800'] = UDT83
db_specs['c1']['db801'] = UDT84
db_specs['c1']['db802'] = UDT84

#############################################################################################
# St 12706 - Stacja Testu przeplywu
#############################################################################################
db_specs['c2']['db803'] = UDT85
db_specs['c2']['db804'] = UDT85


#############################################################################################
# St 12707 - Stacja Znakowanie BMW
#############################################################################################
db_specs['c3']['db805'] = UDT88  # lewa
db_specs['c3']['db806'] = UDT88  # prawa


# special cases hacking...
db100 = ""
db101 = ""
db1 = ""
db2 = ""
db3 = ""
