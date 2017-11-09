import sys
import os
import six
try:
    import configparser
except:
    from six.moves import configparser
from optparse import OptionParser


def usage(name=sys.argv[0]):
    ret = """
    Usage: %s
    """ % (name)
    return ret


def parse_args(argv=sys.argv):
    parser = OptionParser(usage=usage(argv))

    cd = os.path.dirname(argv[0])
    fn = os.path.basename(argv[0])
    bn = fn.split('.')[:-1]
    conf_file = os.path.join(cd, ".".join(bn + ['conf']))

    parser.add_option("-c", "--config", help="location of config file, default: %s" % conf_file, default=conf_file)
    parser.add_option("-q", "--quiet", action="store_true", default=False, help="don't print status messages to stdout")
    parser.add_option("-v", "--verbose", action="store_true", default=False, help="verbose mode")

    opts, args = parser.parse_args()
    return opts, args


def parse_config(f):
    config = configparser.RawConfigParser()
    config.read(f)
    c = {}
    for section in config.sections():
        c[section] = {}
        for option in config.options(section):
            #c[section][option] = map(str.strip, config.get(section, option).split(','))
            value_list = config.get(section, option).split(',')
            [x.strip() for x in value_list]  # strip values
            c[section][option] = value_list

    # in case program is not installed correctly try create required paths
    for k in ['logfile']:
        # print(c)
        path = c['main'][k][0]
        # print("path", path, "xxx")
        if not os.path.exists(os.path.dirname(path)):  # in case base directory does not exists try to create it
            os.makedirs(os.path.dirname(path))
        c['main'][k][0] = path

    return c
