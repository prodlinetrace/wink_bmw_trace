#!/usr/bin/env python
import logging
import sys
from traceability.prodline import ProdLine
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting main app")
    #sys.argv.append("-v")
    app = ProdLine(sys.argv)
    app.main()

if __name__ == "__main__":
    sys.exit(main())
