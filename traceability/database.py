import sqlalchemy
import logging
from datetime import datetime
from . import db
from .models import *
from builtins import str

logger = logging.getLogger(__name__)


class Database(object):

    def __init__(self, name="DB connection"):
        # force foreign keys constraints. to check the data integrity.
        self.name = name
        #@sqlalchemy.event.listens_for(db.engine, "connect")
        #def set_sqlite_pragma(dbapi_connection, connection_record):
        #    cursor = dbapi_connection.cursor()
        #    #cursor.execute("PRAGMA foreign_keys=ON;")
        #    cursor.close()
        db.create_all()  # initialize empty database if required.

    def read_status(self, product_id, station):
        # product_type = str(product_type)
        # serial_number = str(serial_number)
        product_id = product_id
        station = int(station)
        res = Status.query.filter_by(product_id=product_id).filter_by(station_id=station).all()
        if len(res) == 0:
            logger.warn("CON: {dbcon} PID: {product_id} ST: {station} record not found in database - returning undefined".format(dbcon=self.name, product_id=product_id, station=station))
            return 0  # Wabco statuses are not used anymore. Current statuses: (0 undefined, 1 OK, 2 NOK)
        ret = res[-1].status
        logger.info("CON: {dbcon} PID: {product_id} ST: {station} record has status: {status}".format(dbcon=self.name, product_id=product_id, station=station, status=ret))
        return ret

    def read_operator_status(self, operator):
        result = User.query.filter_by(id=operator).all()
        if len(result) == 0:
            logger.warn("CON: {dbcon} OPERATOR: {operator} record for user not found in database - returning undefined".format(dbcon=self.name, operator=operator))
            return 0  # Wabco statuses are not used anymore. Current statuses: (0 undefined, 1 OK, 2 NOK)
        if result[-1].is_operator:
            logger.info("CON: {dbcon} OPERATOR: {operator} Operator User found in DataBase with correct status.".format(dbcon=self.name, operator=operator))
            return 1  # this means user is found in DB and has correct operator status
        else:
            logger.warning("CON: {dbcon} OPERATOR: {operator} User found in DataBase but is not set as an operator".format(dbcon=self.name, operator=operator))
            return 2  # this means user is found in DB but does not have operator status
        logger.error("CON: {dbcon} I should never get here...".format(dbcon=self.name))
        return 0

    def write_status(self, product_id, station, status, program_id, nest_id, operator=0, date_time=datetime.now()):
        #product_type = str(product_type)
        #serial_number = str(serial_number)
        product_id = str(product_id)
        station = int(station)
        status = int(status)
        program_id = int(program_id)
        nest_id = int(nest_id)
        operator = int(operator)
        date_time = str(date_time)
        logger.info("CON: {dbcon} PID: {product_id} ST: {station} STATUS: {status} PROGRAM: {program_id} NEST: {nest_id} OPERATOR: {operator} DT: {date_time}. Saving status record.".format(dbcon=self.name, product_id=product_id, station=station, status=status, program_id=program_id, nest_id=nest_id, operator=operator, date_time=date_time))

        #self.add_program_if_required(program_id)
        self.add_product_if_required(product_id)
        self.add_station_if_required(station)
        self.add_operation_status_if_required(status)  # status and operation status names are kept in one and same table
        self.add_operator_if_required(operator)  # add / operator / user if required.
        self.add_status(status, product_id, program_id, nest_id,station, operator, date_time)

    def write_operation(self, product_id, station_id, operation_status, operation_type, program_id, date_time, result_1, result_1_max, result_1_min, result_1_status, result_2, result_2_max, result_2_min, result_2_status):
        #product_type = str(product_type)
        #serial_number = str(serial_number)
        product_id = Product.calculate_product_id(product_id)
        program_id = str(program_id)
        station_id = int(station_id)

        #self.add_program_if_required(program_id)
        self.add_product_if_required(product_id)
        self.add_station_if_required(station_id)
        self.add_operation_status_if_required(operation_status)
        self.add_operation_status_if_required(result_1_status)
        self.add_operation_status_if_required(result_2_status)
        self.add_operation_type_if_required(operation_type)
        self.add_operation(product_id, station_id, operation_status, operation_type, program_id, date_time, result_1, result_1_max, result_1_min, result_1_status, result_2, result_2_max, result_2_min, result_2_status)

    def add_operation(self, product_id, station_id, operation_status, operation_type, program_id, date_time, result_1, result_1_max, result_1_min, result_1_status, result_2, result_2_max, result_2_min, result_2_status):
        if date_time is None:
            date_time = str(date_time)

        try:
            new_operation = Operation(product=product_id, station=station_id, operation_status_id=operation_status, operation_type_id=operation_type, program_id=program_id, date_time=date_time, r1=result_1, r1_max=result_1_max, r1_min=result_1_min, r1_stat=result_1_status, r2=result_2, r2_max=result_2_max, r2_min=result_2_min, r2_stat=result_2_status)
            db.session.add(new_operation)
            try:
                db.session.commit()
            except sqlalchemy.exc.IntegrityError as e:
                logger.error("CON: {dbcon} {rep} : {err}".format(dbcon=self.name, rep=repr(e), err=e.__str__()))
            logger.info("CON: {dbcon} Adding new Operation to database: {operation}".format(dbcon=self.name, operation=new_operation))

        except sqlalchemy.exc.OperationalError as e:
            logger.error("CON: {dbcon} Database: {dbfile} is locked. Error: {err}".format(dbcon=self.name, dbfile=db.get_app().config['SQLALCHEMY_DATABASE_URI'], err=e.__str__()))
            return False
        return True

    def add_status(self, status, product, program_number, nest_number, station, operator, date_time=None):
        status = int(status)
        product = str(product)
        program_number = int(program_number)
        nest_number = int(nest_number)
        station = int(station)
        operator = int(operator)
        if date_time is None:
            date_time = str(date_time)

        try:
            new_status = Status(status=status, product=product, program_number=program_number, nest_number=nest_number, station=station, user=operator, date_time=date_time)
            db.session.add(new_status)
            try:
                db.session.commit()
            except sqlalchemy.exc.IntegrityError as e:
                logger.error("CON: {dbcon} {rep} : {err}".format(dbcon=self.name, rep=repr(e), err=e.__str__()))
            logger.info("CON: {dbcon} Adding new Status to database: {status}".format(dbcon=self.name, status=new_status))

        except sqlalchemy.exc.OperationalError as e:
            logger.error("CON: {dbcon} Database: {database} is locked. Error: {error}".format(dbcon=self.name, database=db.get_app().config['SQLALCHEMY_DATABASE_URI'], error=e.__str__()))
            return False
        return True

    def add_product_if_required(self, product_id):
        #product_type = str(product_type)
        #serial_number = str(serial_number)
        product_id = product_id

        try:
            _product = Product.query.filter_by(id=product_id).first()
            if _product is None:  # add item if not exists yet.
                new_prod = Product(product_id)
                db.session.add(new_prod)
                try:
                    db.session.commit()
                except sqlalchemy.exc.IntegrityError as e:
                    logger.error("CON: {dbcon} {rep} : {err}".format(dbcon=self.name, rep=repr(e), err=e.__str__()))
                logger.info("CON: {dbcon} Adding new Product to database: {prod}".format(dbcon=self.name, prod=new_prod))

        except sqlalchemy.exc.OperationalError as e:
            logger.error("CON: {dbcon} Database: {dbfile} is locked. Error: {err}".format(dbcon=self.name, dbfile=db.get_app().config['SQLALCHEMY_DATABASE_URI'], err=e.__str__()))
            return False
        return True

    def add_station_if_required(self, station):
        station = int(station)
        try:
            _station = Station.query.filter_by(id=int(station)).first()
            if _station is None:  # add new station if required (should not happen often)
                new_station = Station(ident=station, name=station)
                db.session.add(new_station)
                try:
                    db.session.commit()
                except sqlalchemy.exc.IntegrityError as e:
                    logger.error("CON: {dbcon} {rep} : {err}".format(dbcon=self.name, rep=repr(e), err=e.__str__()))
                logger.info("CON: {dbcon} Adding new Station to database: {station}".format(dbcon=self.name, station=str(new_station)))

        except sqlalchemy.exc.OperationalError as e:
            logger.error("CON: {dbcon} Database: {dbfile} is locked. Error: {err}".format(dbcon=self.name, dbfile=db.get_app().config['SQLALCHEMY_DATABASE_URI'], err=e.__str__()))
            return False
        return True

    def add_operation_type_if_required(self, operation_type):
        operation_type = int(operation_type)

        try:
            _operation_type = Operation_Type.query.filter_by(id=int(operation_type)).first()
            if _operation_type is None:  # add new operation_type if required (should not happen often)
                new_operation_type = Operation_Type(ident=operation_type, name=operation_type)
                db.session.add(new_operation_type)
                try:
                    db.session.commit()
                except sqlalchemy.exc.IntegrityError as e:
                    logger.error("CON: {dbcon} {rep} : {err}".format(dbcon=self.name, rep=repr(e), err=e.__str__()))
                logger.info("CON: {dbcon} Adding new Operation_Type to database: {operation}".format(dbcon=self.name, operation=str(new_operation_type)))

        except sqlalchemy.exc.OperationalError as e:
            logger.error("CON: {dbcon} Database: {dbfile} is locked. Error: {err}".format(dbcon=self.name, dbfile=db.get_app().config['SQLALCHEMY_DATABASE_URI'], err=e.__str__()))
            return False
        return True

    def add_operation_status_if_required(self, operation_status):
        operation_status = int(operation_status)

        try:
            _operation_status = Operation_Status.query.filter_by(id=int(operation_status)).first()
            if _operation_status is None:  # add new operation_status if required (should not happen often)
                new_operation_status = Operation_Status(ident=operation_status, name=operation_status)
                db.session.add(new_operation_status)
                try:
                    db.session.commit()
                except sqlalchemy.exc.IntegrityError as e:
                    logger.error("CON: {dbcon} {rep} : {err}".format(dbcon=self.name, rep=repr(e), err=e.__str__()))
                logger.info("CON: {dbcon} Adding new Operation_Status to database: {operation_status}".format(dbcon=self.name, operation_status=str(new_operation_status)))

        except sqlalchemy.exc.OperationalError as e:
            logger.error("CON: {dbcon} Database: {dbfile} is locked. Error: {err}".format(dbcon=self.name, dbfile=db.get_app().config['SQLALCHEMY_DATABASE_URI'], err=e.__str__()))
            return False
        return True

    def add_operator_if_required(self, operator):
        operator = int(operator)
        try:
            user = User.query.filter_by(id=int(operator)).first()
            if user is None:  # add new user if required (should not happen often)
                new_user = User(id=operator, login="{operator}".format(operator=operator), name="New Operator #{id}".format(id=operator), is_admin=False, is_operator=False)
                db.session.add(new_user)
                try:
                    db.session.commit()
                except sqlalchemy.exc.IntegrityError as e:
                    logger.error("CON: {dbcon} {rep} : {err}".format(dbcon=self.name, rep=repr(e), err=e.__str__()))
                logger.info("CON: {dbcon} Adding new User (operator) to database: {user}".format(dbcon=self.name, user=str(user)))

        except sqlalchemy.exc.OperationalError as e:
            logger.error("CON: {dbcon} Database: {dbfile} is locked. Error: {err}".format(dbcon=self.name, dbfile=db.get_app().config['SQLALCHEMY_DATABASE_URI'], err=e.__str__()))
            return False
        return True

    def add_program_if_required(self, program):
        program = str(program)
        try:
            _program = Program.query.filter_by(id=str(program)).first()
            if _program is None:  # add new program if required (should not happen often)
                new_program = Program(ident=program, name="{id}".format(id=program))
                db.session.add(new_program)
                try:
                    db.session.commit()
                except sqlalchemy.exc.IntegrityError as e:
                    logger.error("CON: {dbcon} {rep} : {err}".format(dbcon=self.name, rep=repr(e), err=e.__str__()))
                logger.info("CON: {dbcon} Adding new Program to database: {program}".format(dbcon=self.name, program=str(program)))

        except sqlalchemy.exc.OperationalError as e:
            logger.error("CON: {dbcon} Database: {dbfile} is locked. Error: {err}".format(dbcon=self.name, dbfile=db.get_app().config['SQLALCHEMY_DATABASE_URI'], err=e.__str__()))
            return False
        return True

    def get_operator_by_login(self, login):
        operator = User.query.filter_by(login=login).first()
        if  operator:
            return  operator.id
        else:
            return 0
 
    def get_product_count(self):
        return Product.query.count()

    def get_station_count(self):
        return Station.query.count()

    def get_status_count(self):
        return Status.query.count()

    def get_status_type_count(self):
        return Operation_Status.query.count()

    def get_opertation_count(self):
        return Operation.query.count()

    def get_operation_type_count(self):
        return Operation_Type.query.count()

    def get_comment_count(self):
        return Comment.query.count()

    def connect(self):
        logger.info("CON: {dbcon} db.connect initiated.".format(dbcon=self.name))

    def disconnect(self):
        logger.info("CON: {dbcon} db.disconnect initiated.".format(dbcon=self.name))

    def get_status(self):
        return True

    def send_keepalive_query(self):
        return db.session.execute(sqlalchemy.text("select 1"))

    def initialize_example_data(self):
        db.drop_all()
        db.create_all()
        product_type = 1234567899
        i1 = Product(product_type, 16666, 42)
        i2 = Product(product_type, 26666, 42)
        i3 = Product(product_type, 1234, 42)
        s10 = Station(10, "192.168.0.10", 102, 0, 2)
        s20 = Station(20, "192.168.0.20", 102, 0, 2)
        s21 = Station(21, "192.168.0.20", 102, 0, 2)
        s22 = Station(22, "192.168.0.20", 102, 0, 2)
        s23 = Station(23, "192.168.0.20", 102, 0, 2)
        # s24 = Station(11, "192.168.0.10", 102, 0, 2)
        """ TODO: FIXME
        t1 = Status(0, Product.calculate_product_id(product_type, 16666), 10, None)
        t2 = Status(1, Product.calculate_product_id(product_type, 26666), 20, None)
        t3 = Status(0, Product.calculate_product_id(product_type, 1234), 10, None)
        t4 = Status(1, Product.calculate_product_id(product_type, 1234), 20, None)
        t5 = Status(1, Product.calculate_product_id(product_type, 1234), 21, None)
        t6 = Status(0, Product.calculate_product_id(product_type, 1234), 21, None)
        """
        db.session.add(i1)
        db.session.add(i2)
        db.session.add(i3)
        # db.session.add(i4)

        db.session.add(s10)
        db.session.add(s20)
        db.session.add(s21)
        db.session.add(s22)
        db.session.add(s23)
        # db.session.add(s24)

        db.session.add(t1)
        db.session.add(t2)
        db.session.add(t3)
        db.session.add(t4)
        db.session.add(t5)
        db.session.add(t6)

        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            logger.error("CON: {dbcon} {rep} : {err}".format(dbcon=self.name, rep=repr(e), err=e.__str__()))
