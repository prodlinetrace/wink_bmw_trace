#!/usr/bin/env python
import sys
from traceability.layouts import db_specs


def main():
    for ctrl in db_specs:
        print("ctrl: {}".format(ctrl))
        for db_number in db_specs[ctrl]:
            print("{c}->{db}".format(c=ctrl, db=db_number))
            #print(db_specs[ctrl][db_number])
            open("doc/{fname}".format(fname=ctrl+'-'+db_number+'.txt'), "w").write(db_specs[ctrl][db_number])

    return 0

if __name__ == "__main__":
    sys.exit(main())
