import hashlib
import bleach
import logging
import dateutil.parser
from markdown import markdown
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import request, current_app
from flask_login import UserMixin
from . import db
logger = logging.getLogger(__name__)

__version__ = '0.1.5'

try:
    from . import login_manager
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
except ImportError as e:
    # desktop app - ignore in case login_manager is not defined.  
    pass


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(64), nullable=False, unique=True, index=True)
    name = db.Column(db.String(64))
    is_admin = db.Column(db.Boolean)
    is_operator = db.Column(db.Boolean)
    password_hash = db.Column(db.String(128))
    location = db.Column(db.String(64))
    locale = db.Column(db.String(16))
    bio = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.now)
    avatar_hash = db.Column(db.String(32))
    comments = db.relationship('Comment', lazy='dynamic', backref='author')
    status = db.relationship('Status', lazy='dynamic', backref='user', foreign_keys='Status.user_id')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.login is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.login.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        _hash = self.avatar_hash or hashlib.md5(self.login.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=_hash, size=size, default=default, rating=rating)

    def get_api_token(self, expiration=300):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'user': self.id}).decode('utf-8')

    @staticmethod
    def validate_api_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        _id = data.get('user')
        if _id:
            return User.query.get(_id)
        return None

    def __repr__(self):
        return '<User {id} Login {login} Name {name}>'.format(id=self.id, login=self.login, name=self.name)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    product_id = db.Column(db.String(30), db.ForeignKey('product.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def __repr__(self):
        return '<Comment {id} Product {product} Author {author}>'.format(id=self.id, product=self.product_id, author=self.author_id)


db.event.listen(Comment.body, 'set', Comment.on_changed_body)


class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.String(30), nullable=False, unique=True, index=True, primary_key=True)
    date_added = db.Column(db.String(40), index=True)

    comments = db.relationship('Comment', lazy='dynamic', backref='product')
    statuses = db.relationship('Status', lazy='dynamic', backref='product')
    operations = db.relationship('Operation', lazy='dynamic', backref='product')

    def __init__(self, id, date=None):
        self.id = self.calculate_product_id(id)
        if date is None:
            date = datetime.now()
        self.date_added = str(date)

    def __repr__(self):
        return '<Product {id}>'.format(id=self.id)

    @staticmethod
    def calculate_product_id(id):
        return str(id)

    def get_product_id(self, id):
        """
        returns product id.
        """
        return Product.calculate_product_id(id=self.id)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'date_added': self.date_added,
        }

    @property
    def year(self):
        """ Return year number """
        return dateutil.parser.parse(str(self.date_added)).year

    @property
    def month(self):
        """ Return month number """
        return dateutil.parser.parse(str(self.date_added)).month

    @property
    def day(self):
        """ Return day number """
        return dateutil.parser.parse(str(self.date_added)).day

    @property
    def week(self):
        """ Return week number """
        return dateutil.parser.parse(str(self.date_added)).strftime("%V")

    @property
    def status_count(self):
        """ Return number statuses """
        return self.statuses.count()  

    @property
    def status_count_good(self):
        """ Return number of good statuses """
        return self.statuses.filter(Status.status==1).count()  

    @property
    def status_count_bad(self):
        """ Return number of bad statuses """
        return self.statuses.filter(Status.status==2).count()

    @property
    def operation_unsynced_count(self):
        """ Return number of unsynchronized operations """
        return self.operations.filter(Operation.prodasync==0).count()  
    
    @property
    def operation_count(self):
        """ Return number operations """
        return self.operations.count()  

    @property
    def operation_count_good(self):
        """ Return number of good operations """
        return self.operations.filter(Operation.operation_status_id==1).count()  

    @property
    def operation_count_bad(self):
        """ Return number of bad operations """
        return self.operations.filter(Operation.operation_status_id==2).count()

    @property
    def electronic_stamp(self):
        """ Return Electronic Stamp"""
        st = "ok"
        return st
    
    @property
    def processing_time(self):
        st12705 = self.statuses.filter(Status.station_id==12705).order_by(Status.id.desc()).first()
        st12707 = self.statuses.filter(Status.station_id==12707).order_by(Status.id.desc()).first()
        if st12705 is None or st12707 is None:
            return None 
        end_time = dateutil.parser.parse(st12707.date_time)
        start_time = dateutil.parser.parse(st12705.date_time)

        return end_time - start_time


class Station(db.Model):
    __tablename__ = 'station'
    id = db.Column(db.Integer, primary_key=True)  # this is real station id
    ip = db.Column(db.String(16), unique=False)
    name = db.Column(db.String(64), unique=False)
    port = db.Column(db.Integer, unique=False)
    rack = db.Column(db.Integer, unique=False)
    slot = db.Column(db.Integer, unique=False)
    statuses = db.relationship('Status', lazy='dynamic', backref='station')
    operations = db.relationship('Operation', lazy='dynamic', backref='station')

    def __init__(self, ident, ip='localhost', name="name", port=102, rack=0, slot=2):
        self.id = ident
        self.ip = ip
        self.name = name
        self.port = port
        self.rack = rack
        self.slot = slot

    def __repr__(self):
        return '<Station {id}>'.format(id=self.id)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'ip': self.ip,
            'name': self.name,
            'port': self.port,
            'rack': self.rack,
            'slot': self.slot,
        }


class Status(db.Model):
    __tablename__ = 'status'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Integer, db.ForeignKey('operation_status.id'))
    date_time = db.Column(db.String(40))
    product_id = db.Column(db.String(30), db.ForeignKey('product.id'))
    # program_id = db.Column(db.String(20), db.ForeignKey('program.id'))
    station_id = db.Column(db.Integer, db.ForeignKey('station.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    program_number = db.Column(db.Integer)
    nest_number = db.Column(db.Integer)

    def __init__(self, status, product, program, nest, station_id, user=None, date_time=None):
        self.status = status
        self.product_id = product
        #self.program_id = program
        self.station_id = station_id
        self.user_id = user
        if date_time is None:
            date_time = datetime.now()
        self.date_time = str(date_time)
        self.program_number = program
        self.nest_number = nest

    def __repr__(self):
        return '<Status Id: {id} for Product: {product} Station: {station} Status: {status} Program: {program_number} Nest: {nest_number}'.format(id=self.id, product=self.product_id, station=self.station_id, status=self.status, program_number=self.program_number, nest_number=self.nest_number)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'status': self.status,
            'product_id': self.product_id,
            'station_id': self.station_id,
            'program_number': self.program_number,
            'nest_number': self.nest_number,
            'user_id': self.user_id,
            'date_time': self.date_time,
        }

    @property
    def operations(self):
        """
            get list of operations matching given status (360 seconds diff from operation and status is the limit). 
        """
        time_diff_limit = 600  # time diff limit in seconds
        
        # filter operations with matching station_id
        operations = filter(lambda x: x.station_id == self.station_id, self.product.operations.all())  
        # filter out operations with with time difference bigger than 360 seconds.
        operations = filter(lambda x: (dateutil.parser.parse(self.date_time) - dateutil.parser.parse(x.date_time)).seconds < time_diff_limit, operations)
        
        #return operations
        # find operations with duplicate operation_type_id and group them
        import itertools
        lists = [list(v) for k,v in itertools.groupby(sorted(operations, key=lambda y: y.operation_type_id), lambda x: x.operation_type_id)]
        operations = []  # reset operations to fill it again with code below
        for items_groupped_by_operation_type_id in lists:
            if len(items_groupped_by_operation_type_id) > 1:  # this means that there is more tham one item with same operation_type_id
                # find item with closest operation date 
                item_with_closest_operation_date = min(items_groupped_by_operation_type_id, key=lambda x: (dateutil.parser.parse(self.date_time) - dateutil.parser.parse(x.date_time)).seconds)
            else:
                item_with_closest_operation_date = items_groupped_by_operation_type_id[0] 
            operations.append(item_with_closest_operation_date)

        return operations


class Operation(db.Model):
    __tablename__ = 'operation'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.String(30), db.ForeignKey('product.id'))
    station_id = db.Column(db.Integer, db.ForeignKey('station.id'))
    operation_status_id = db.Column(db.Integer, db.ForeignKey('operation_status.id'))
    operation_type_id = db.Column(db.Integer, db.ForeignKey('operation_type.id'))
    program_number = db.Column(db.Integer)
    nest_number = db.Column(db.Integer)
    date_time = db.Column(db.String(40))
    results = db.relationship('Result', lazy='dynamic', backref='operation')

    def __init__(self, product, station, operation_status_id, operation_type_id, program_number, nest_number, date_time):
        self.product_id = product
        self.station_id = station
        self.operation_status_id = operation_status_id
        self.operation_type_id = operation_type_id
        #self.program_id = str(program_id)
        self.program_number = str(program_number)
        self.nest_number = str(nest_number)
        if date_time is None:
            date_time = datetime.now()
        self.date_time = str(date_time)

    def __repr__(self):
        return '<Assembly Operation Id: {id} for: Product: {product} Station: {station} Operation_type: {operation_type}>'.format(id=self.id, product=self.product_id, station=self.station_id, operation_type=self.operation_type_id)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""

        return {
            'id': self.id,
            'product_id': self.product_id,
            'station_id': self.station_id,
            'operation_type_id': self.operation_type_id,
            'operation_status_id': self.operation_status_id,
            #'program_id': self.program_id,
            'program_number': self.program_number,
            'nest_number': self.nest_number,
            'date_time': self.date_time
        }

        
class Result(db.Model):
    __tablename__ = 'result'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.String(30), db.ForeignKey('product.id'))
    station_id = db.Column(db.Integer, db.ForeignKey('station.id'))
    operation_id = db.Column(db.Integer, db.ForeignKey('operation.id'))
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('type.id'))  # type should be used for casting.
    desc_id = db.Column(db.Integer, db.ForeignKey('desc.id'))
    value = db.Column(db.String(30))
    
    """
        # type_id = 1  # 1 - STRING, 2 - INT, 3 - REAL, 4 - BOOL
        # unit_id = 3  # 0 [None], 1 [N], 2 [Nm], 3 [deg], 4 [mm], 5 [kN],  7 [mbar l/s], 8 [bar], 9 [mbar], 10 [m], 20 [Pa], 30 [s], 99 [bool], 
        self.database_engine.write_result(detail_id, station_id, operation_id, unit_id=unit_id, value_type_id=value_type_id, value=ReadID_id)
    """

    def __init__(self, product, station, operation_id, unit_id, type_id, desc_id, value, date_time=None):
        self.product_id = product
        self.station_id = station
        self.operation_id = operation_id
        self.unit_id = unit_id
        self.type_id = type_id
        self.desc_id = desc_id
        self.value = value

    def __repr__(self):
        return '<Assembly Result Id: {id} for: Product: {product} Station: {station} operation_id: {operation_id}>'.format(id=self.id, product=self.product_id, station=self.station_id, operation_id=self.operation_id)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""

        return {
            'id': self.id,
            'product_id': self.product_id,
            'station_id': self.station_id,
            'operation_id': self.operation_id,
            'unit_id': self.unit_id,
            'type_id': self.type_id,
            'desc_id': self.desc_id,
            'value': self.value,
        }


class Operation_Status(db.Model):
    __tablename__ = 'operation_status'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(255))
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'))
    operations = db.relationship('Operation', lazy='dynamic', backref='operation_status',  foreign_keys='Operation.operation_status_id')
    status = db.relationship('Status', lazy='dynamic', backref='status_name', foreign_keys='Status.status')

    def __init__(self, ident, name="Default Operation Status", description="Default Operation Status Description", unit_id=None):
        self.id = ident
        self.name = name
        self.description = description
        self.unit_id = unit_id

    def __repr__(self):
        return '<Operation_Status Id: {id} Name: {name} Description: {desc}>'.format(id=self.id, name=self.name, desc=self.description)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'unit_id': self.unit_id,
        }


class Operation_Type(db.Model):
    __tablename__ = 'operation_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(255))
    operations = db.relationship('Operation', lazy='dynamic', backref='operation_type')

    def __init__(self, ident, name="Default Operation Name", description="Default Operation Description"):
        self.id = ident
        self.name = name
        self.description = description

    def __repr__(self):
        return '<Operation_Type Id: {id} Name: {name} Description: {desc}>'.format(id=self.id, name=self.name, desc=self.description)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
        }


class Unit(db.Model):
    __tablename__ = 'unit'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    symbol = db.Column(db.String(16))
    description = db.Column(db.String(255))
    operation_status = db.relationship('Operation_Status', lazy='dynamic', backref='unit', foreign_keys='Operation_Status.unit_id')
    result = db.relationship('Result', lazy='dynamic', backref='unit')

    def __init__(self, ident, name="Default Unit Name", symbol="Default Unit Symbol", description="Default Unit Description"):
        self.id = ident
        self.name = name
        self.symbol = symbol
        self.description = description

    def __repr__(self):
        return '<Unit Id: {id} Name: {name} Symbol: {symbol} Description: {desc}>'.format(id=self.id, name=self.name, symbol=self.symbol, desc=self.description)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'symbol': self.symbol,
            'description': self.description,
        }


class Desc(db.Model):
    __tablename__ = 'desc'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(255))
    result = db.relationship('Result', lazy='dynamic', backref='desc')

    def __init__(self, ident, name="Default Desc Name", description="Default Desc Description"):
        self.id = ident
        self.name = name
        self.description = description

    def __repr__(self):
        return '<Desc Id: {id} Name: {name} Description: {desc}>'.format(id=self.id, name=self.name, desc=self.description)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
        }


class Type(db.Model):
    __tablename__ = 'type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    symbol = db.Column(db.String(16))
    description = db.Column(db.String(255))
    result = db.relationship('Result', lazy='dynamic', backref='type', foreign_keys='Result.type_id')


    def __init__(self, ident, name="Default Type Name", symbol="Default Type Symbol", description="Default Type Description"):
        self.id = ident
        self.name = name
        self.symbol = symbol
        self.description = description

    def __repr__(self):
        return '<Type Id: {id} Name: {name} Symbol: {symbol} Description: {desc}>'.format(id=self.id, name=self.name, symbol=self.symbol, desc=self.description)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'symbol': self.symbol,
            'description': self.description,
        }
