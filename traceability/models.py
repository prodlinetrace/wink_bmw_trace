import hashlib
import bleach
import logging
from markdown import markdown
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import request, current_app
from flask_login import UserMixin
from . import db
logger = logging.getLogger(__name__)

__version__ = '0.1.1'


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

    #new_status = Status(status=status, product=product, program=program, nest=nest, station=station, user=operator, date_time=date_time)

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


class Operation(db.Model):
    __tablename__ = 'operation'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.String(30), db.ForeignKey('product.id'))
    station_id = db.Column(db.Integer, db.ForeignKey('station.id'))
    operation_status_id = db.Column(db.Integer, db.ForeignKey('operation_status.id'))
    operation_type_id = db.Column(db.Integer, db.ForeignKey('operation_type.id'))
    #program_id = db.Column(db.String(20), db.ForeignKey('program.id'))
    program_number = db.Column(db.Integer)
    nest_number = db.Column(db.Integer)
    date_time = db.Column(db.String(40))
    """
    result_1 = db.Column(db.Float)
    result_1_max = db.Column(db.Float)
    result_1_min = db.Column(db.Float)
    result_1_status_id = db.Column(db.Integer, db.ForeignKey('operation_status.id'))
    result_2 = db.Column(db.Float)
    result_2_max = db.Column(db.Float)
    result_2_min = db.Column(db.Float)
    result_2_status_id = db.Column(db.Integer, db.ForeignKey('operation_status.id'))
    """
    #def __init__(self, product, station, operation_status_id, operation_type_id, program_number, nest_number, date_time, r1=None, r1_max=None, r1_min=None, r1_stat=None, r2=None, r2_max=None, r2_min=None, r2_stat=None):
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
        """
        self.result_1 = r1
        self.result_1_max = r1_max
        self.result_1_min = r1_min
        self.result_1_status_id = r1_stat

        self.result_2 = r2
        self.result_2_max = r2_max
        self.result_2_min = r2_min
        self.result_2_status_id = r2_stat
        """
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
        '''
        'result_1': self.result_1,
        'result_1_max': self.result_1_max,
        'result_1_min': self.result_1_min,
        'result_1_status_id': self.result_1_status_id,

        'result_2': self.result_2,
        'result_2_max': self.result_2_max,
        'result_2_min': self.result_2_min,
        'result_2_status_id': self.result_2_status_id,
        '''
        
class Result(db.Model):
    __tablename__ = 'result'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.String(30), db.ForeignKey('product.id'))
    station_id = db.Column(db.Integer, db.ForeignKey('station.id'))
    operation_id = db.Column(db.Integer, db.ForeignKey('operation.id'))
    # TODO FIXME
    # unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'))
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'))
    type_id = db.Column(db.Integer)  # type should be used for casting.
    desc_id = db.Column(db.Integer, db.ForeignKey('desc.id'))
    value = db.Column(db.String(30))

    """
        # type_id = 1  # 1 - STRING, 2 - INT, 3 - REAL, 4 - BOOL
        # unit_id = 3  # 1 [Nm], 2 [N], 3 [Pa], 4 [bool], 5 [s], 6 [None], 7 [mbar l/s], 8 [bar], 9 [mbar]
        self.database_engine.write_result(detail_id, station_id, operation_id, unit_id=unit_id, value_type_id=value_type_id, value=ReadID_id)
    """
    def __init__(self, product, station, operation_id, unit_id, type_id, desc_id, value):
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
            'value': self.value
        }


class Operation_Status(db.Model):
    __tablename__ = 'operation_status'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(255))
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'))
    operations = db.relationship('Operation', lazy='dynamic', backref='operation_status',  foreign_keys='Operation.operation_status_id')

    #result_1_status = db.relationship('Operation', lazy='dynamic', backref='result_1_status', foreign_keys='Operation.result_1_status_id')
    #result_2_status = db.relationship('Operation', lazy='dynamic', backref='result_2_status', foreign_keys='Operation.result_2_status_id')

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


class Program(db.Model):
    __tablename__ = 'program'
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(255))
    #operations = db.relationship('Operation', lazy='dynamic', backref='program', foreign_keys='Operation.program_id')
    #statuses = db.relationship('Status', lazy='dynamic', backref='program', foreign_keys='Status.program_id')

    def __init__(self, ident, name="Default Program Name", description="Default Program Description"):
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
    unit = db.relationship('Operation_Status', lazy='dynamic', backref='unit', foreign_keys='Operation_Status.unit_id')

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
