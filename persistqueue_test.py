#!/usr/bin/python3 

import sys
from persistqueue.queue import Queue, Empty, Full
from traceability.lean import OnePieceFlow
from traceability.helpers import parse_config
from traceability.database import Database
database = Database()


sys.argv.append('trace.conf')
config = parse_config('trace.conf')

#print(config)
#import os
#print(os.path.abspath(os.path.curdir))
opf = OnePieceFlow(config)
opf.print_queues_config()
print("OPF queues:", opf.get_queue_ids())
print("One piece Flow Status:", opf.get_opf())


print(f'q1: {opf.dump_queue("q1")} q2: {opf.dump_queue("q2")}')
print(opf.status_save( "12345", 'c1', 1))
print(opf.status_save( "1234", 'c1', 14))
print(opf.status_save( "1234", 'c1', 1))
print(f'q1: {opf.dump_queue("q1")} q2: {opf.dump_queue("q2")}')
print(opf.status_save( "12345", 'c2', 1))
print(f'q1: {opf.dump_queue("q1")} q2: {opf.dump_queue("q2")}')
print(opf.status_save( "123476", 'c2', 1))
print(f'q1: {opf.dump_queue("q1")} q2: {opf.dump_queue("q2")}')
print(opf.status_save( "123", 'c1', 1))
print(f'q1: {opf.dump_queue("q1")} q2: {opf.dump_queue("q2")}')
