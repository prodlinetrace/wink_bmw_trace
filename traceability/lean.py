import logging
import sqlalchemy
from . import db
from .models import *

logger = logging.getLogger(__name__)

class DBQ(object):

    def __init__(self, name, max_size):
        self.name = name
        self.max_size = max_size

    def append(self, product_id):
        if not self.check_if_present(product_id):
            logger.debug("Queue: {name} product_id: {product_id} already present".format(name=self.name, product_id=product_id))
            return False

        try:
            new_item = Queue(product_id=product_id, name=self.name)
            db.session.add(new_item)
            try:
                db.session.commit()
            except sqlalchemy.exc.IntegrityError as e:
                logger.error("Queue: {name} {rep}: {err}".format(name=self.name, rep=repr(e), err=e.__str__()))
            logger.info("Queue: {name} Adding new item to queue: {item}".format(name=self.name, item=new_item))

        except sqlalchemy.exc.OperationalError as e:
            logger.error("Queue: {name} Database: {dbfile} is locked. Error: {err}".format(dbcon=self.name, dbfile=db.get_app().config['SQLALCHEMY_DATABASE_URI'], err=e.__str__()))
            return False

    def get_name(self):
        return self.name
    
    def get_max_size(self):
        return self.max_size

    def get_all(self):
        return Queue.query.filter_by(name=self.name).all()

    def get_all_product_ids(self):
        return [ p.product_id for p in Queue.query.filter_by(name=self.name).all() ]

    def remove(self, product_id):
        items = Queue.query.filter_by(name=self.name).filter_by(product_id=product_id).all()
        try:
            Queue.query.filter_by(name=self.name).filter_by(product_id=product_id).delete()
            #db.session.delete(items)
            db.session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            logger.error("Queue: {name} {rep}: {err}".format(name=self.name, rep=repr(e), err=e.__str__()))
        logger.info("Queue: {name} deleting product from the queue: {item}".format(name=self.name, item=items))

    def check_if_present(self, product_id):
        if Queue.query.filter_by(name=self.name).filter_by(product_id=product_id).count():
            return False
        return True

    def get_next_product(self):
        return Queue.query.filter_by(name=self.name).first()

    def get_next_product_id(self):
        next_product = Queue.query.filter_by(name=self.name).first()
        if next_product is not None:
            return next_product.product_id
        return None

    def size(self):
        #return Queue.count(self.name)
        return Queue.query.filter_by(name=self.name).count()


class OnePieceFlow(object):

    def __init__(self, config, loglevel=logging.INFO):
        # handle logging - set root logger level
        logging.root.setLevel(logging.INFO)
        logger = logging.getLogger(__name__.ljust(24)[:24])
        logger.setLevel(loglevel)

        self.opf = None
        self._config = config
        # initialize queues
        self._queues_config = {}
        self._queues = {}
        for q in self._config['main']['queues']:
            q = q.strip()
            queue_config = {
                'id': self._config[q]['id'][0],
                'size': int(self._config[q]['size'][0]),
            }
            self._queues_config[q] = queue_config
            queue = DBQ(name=queue_config['id'], max_size=queue_config['size'])
            self._queues[q] = queue

        self.opf = bool(int(self._config['main']['opf'][0]))

    def print_queues_config(self):
        for q in self._queues_config.keys():
            print(self._queues_config[q])

    def get_queue_ids(self):
        """
            gets queue ids for all defined queues
        """
        return self._queues.keys()

    def get_queue(self, id):
        return self._queues[id]

    def dump_queue(self, id):
        return self._queues[id].get_all()

    def get_opf(self):
        return self.opf

    def get_next_product_id_for_db(self, db):
        qid = 'q0'
        if db in [803, 804]:
            qid = 'q1'
        if db in [805, 806]:
            qid = 'q2'

        if qid == 'q0':
            return 0  # unable to find queue id for given db
        return self.get_queue(qid).get_next_product_id()

    def get_next_product_id(self, id):
        return self.get_queue(id).get_next_product_id()

    def get_all_product_ids(self, id):
        return self.get_queue(id).get_all_product_ids()

    def overflow_check(self, product_id, station_id, result):
        return

    """
        Enforces one piece flow for the production line.
        Chodzi o to, aby detale byly robione w takiej kolejnosci, w jakiej wchodza na poprzednia stacje.

    1.  
        Pomiedzy maszynami 12705 a 12706 i 12706 a 12707 potrzebne sa bufory 10 sztuk.
        W buforze beda zapisywane ID sztuk z globalnym OK w kolejnosci, w jakiej schodza z maszyny n.
        Poprawne wykonanie sztuki na maszynie n+1 zdejmuje ja z bufora maszyny n, przesuwa bufor i robi miejsce na kolejna sztuke do wykonania na maszynie n.
        Jezeli bufor maszyny n jest pelen to wstrzymywana jest na niej praca do czasu az zwolni sie miejsce.
        Bedzie potrzebny pewnie globalny status 16 - BUFFER_FULL zwracany kiedy przepelni sie bufor.

    2.  
        Maszyna n+1 skanuje detal i pyta o status globalny.
        Jezeli jest to status pierwszy z kolejki w buforze dla n to dziala jak do tej pory.
        Jezeli nie jest pierwszy, to trejs zwraca zamiast 1-OK lub 2-NOK, np. 13 - WRONG_ORDER (dla dalszych potrzeb bedzie jeszcze 14- NOK_OUT, 15 - OK_BUT_DONE, 16 - BUFFER_FULL
        W przypadku WRONG_ORDER PC zwraca ID, jakie powinno trafic na maszyne w ktore PLC wyswietla operatorowi, aby wiedzial, co wlozyc na maszyne.

        Operator albo wymienia sztuke na inna i sprawa zaczyna sie na nowo od punktu 2 albo zatwierdza na panelu, ze sztuka wypadla z procesu. 
        Wowczas stanowisko wpisuje do trejsa globalny status NOK_OUT (id 14)
        Bezie to status, ktory nie pozwoli na prace na zadnym stanowisku. Czyli przy odpytaniach z innych stanowisk trzeba sprawdzac nie tylko poprzednia stacje, ale rowniez czy gdzies indziej nie bylo 14 - NOK_OUT.

    3.  
        Potrzeba bedzie jeszcze blokada, zeby nie dalo sie zrobic na stanowisku n jak juz byla na nim wykonana i ma status globalny OK. Jak juz byla wykonana, ale ma NOK to mozna zrobic jeszcze raz. 
        Czyli oprocz zapytania o OK. na poprzednim stanowisku i NOK_OUT na ktorymkolwiek to jeszcze nie moze byc OK. na danym stanowisku (wlowczas trejs zwraca jak do tej pory 1 - OK.)

    4. 
        Jak juz byla wykonana OK na pytajacym stanowisku to trejs zwraca 15 - OK_BUT_DONE i PLC wyswietla to na stanowisku.

    """

    def ok_but_done_check(self, stations=[], product_id=None):
        for station in stations:  # should be done for station_id + greater stations only
            res = Status.query.filter_by(product_id=product_id).filter_by(station_id=station).all()
            if len(res) > 0:
                if res[-1].status == 1:  # if last status was OK
                    return 15  # OK_BUT_DONE            

    def status_save(self, product_id, station_id, plc_status):
        """
        # check the order (how to check without reading from the queue) - possibly has to be implementaed as database
        """

        logger.info("OPF: status_save() product_id: {product_id} station_id: {station_id} plc_status: {plc_status} opf: {opf}".format(product_id=product_id, station_id=station_id, plc_status=plc_status, opf=self.opf))

        if self.opf is not True:
            return plc_status  # the OPF checks are disabled - do not modify status and return original one
        
        # allow to save NOK_OUT in a first place.
        if plc_status == 14:
            self.get_queue('q1').remove(product_id)
            self.get_queue('q2').remove(product_id)
            return 14  # NOK_OUT

        # NOK_OUT - # return NOK_OUT - if there were NOK_OUT on any station for given product_id
        if Status.query.filter_by(product_id=product_id).filter_by(status=14).count() > 0:
            self.get_queue('q1').remove(product_id)
            self.get_queue('q2').remove(product_id)
            return 14  # NOK_OUT

        if station_id == 12705:
            if plc_status == 1:
                self.get_queue('q1').append(product_id)
                return 1  # OK

        if station_id == 12706:
            if plc_status == 1:
                self.get_queue('q1').remove(product_id)
                self.get_queue('q2').append(product_id)
                return 1  # OK

        if station_id == 12707:
            if plc_status == 1:
                self.get_queue('q2').remove(product_id)
                return 1  # OK
        
        return plc_status  # success scenario - possibly will be used for saving status other than: 1 (OK)

    def status_read(self, product_id, station_id, db_status):
        """
        Maszyna n+1 skanuje detal i pyta o status globalny.
        Jezeli jest to status pierwszy z kolejki w buforze dla n to działa jak do tej pory.
        Jezeli nie jest pierwszy, to trejs zwraca zamiast 1-OK lub 2-NOK, np. 13 - WRONG_ORDER (dla dalszych potrzeb bedzie jeszcze 14 - NOK_OUT, 15 - OK_BUT_DONE, 16 - BUFFER_FULL
        W przypadku WRONG_ORDER PC zwraca ID, jakie powinno trafic na maszyne w ktore PLC wyswietla operatorowi, aby wiedzial, co wlozyc na maszyne.
        status_read() - station_id - id stacji o ktora pytamy (niezaleznie skad przychodzi zapytanie)
        """

        logger.info("OPF: status_read() product_id: {product_id} station_id: {station_id} db_status: {db_status} opf: {opf}".format(product_id=product_id, station_id=station_id, db_status=db_status, opf=self.opf))

        if self.opf is not True:
            return db_status  # the OPF checks are disabled - do not modify status and return original one

        # handle NOK_OUT - # return NOK_OUT - if there were NOK_OUT on any station for given product_id
        if Status.query.filter_by(product_id=product_id).filter_by(status=14).count() > 0:
            return 14  # NOK_OUT
        
        if station_id == 12705:
            queue = self.get_queue('q1')
            station_ids_to_check = [12706, 12707]

            # handle OK_BUT_DONE (15)
            if self.ok_but_done_check(station_ids_to_check, product_id) == 15:
                return 15  # OK_BUT_DONE

            # handle BUFFER_FULL (16)
            if queue.size() >= queue.get_max_size():
                return 16  # BUFFER_FULL
            
            # handle WRONG_ORDER (13)
            expected_product_id = queue.get_next_product_id()
            if expected_product_id is not None:
                if product_id != expected_product_id:  # is not a first element on the list
                    logger.warning(f"{queue.get_name().upper()}: WRONG_ORDER PID: {product_id} SID: {station_id} EXPECTED_PID: {expected_product_id}")
                    return 13  # WRONG_ORDER

        if station_id == 12706:
            queue = self.get_queue('q2')
            station_ids_to_check = [12707]

            # handle OK_BUT_DONE (15)
            if self.ok_but_done_check(station_ids_to_check, product_id) == 15:
                return 15  # OK_BUT_DONE

            # handle BUFFER_FULL (16)
            if queue.size() >=  queue.get_max_size():
                return 16  # BUFFER_FULL

            # handle WRONG_ORDER (13)
            expected_product_id = queue.get_next_product_id()
            if expected_product_id is not None:
                if product_id != expected_product_id:  # is not a first element on the list
                    logger.warning(f"{queue.get_name().upper()}: WRONG_ORDER PID: {product_id} SID: {station_id} EXPECTED_PID: {expected_product_id}")
                    return 13  # WRONG_ORDER

        return db_status  # success scenario
