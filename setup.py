import sys
import os
from cx_Freeze import setup, Executable
import traceability
import sys
sys.setrecursionlimit(10000)

PROJECT_ROOT, _ = os.path.split(__file__)
VERSION = traceability.__version__
PROJECT_NAME = traceability.NAME
PROJECT_AUTHORS = traceability.AUTHOR
# Please see readme.rst for a complete list of contributors
PROJECT_EMAILS = traceability.EMAIL
PROJECT_URL = "https://github.com/prodlinetrace/wink_bmw_trace"
SHORT_DESCRIPTION = 'Traceability application for PLC based production line.'
ICON = "trace.ico"

try:
    DESCRIPTION = open(os.path.join(PROJECT_ROOT, "README.rst")).read()
except IOError:
    DESCRIPTION = SHORT_DESCRIPTION

hidden_imports = [
                "flask",
                "flask_restful",
                "flask_sqlalchemy",
                "flask.views",
                "flask.templating",
                "flask.signals",
                "flask_restful.utils",
                "flask.helpers",
                "flask_restful.representations",
                "flask_restful.representations.json",
                "sqlalchemy.orm",
                "sqlalchemy.event",
                "sqlalchemy.ext.declarative",
                "sqlalchemy.engine.url",
                "sqlalchemy.connectors.mxodbc",
                #"sqlalchemy.connectors.mysqldb",
                "sqlalchemy.connectors.zxJDBC",
                "sqlalchemy.dialects.sqlite.base",
                "sqlalchemy.dialects.sybase.base",
                "sqlalchemy.dialects.sybase.mxodbc",
                "sqlalchemy.engine.base",
                "sqlalchemy.engine.default",
                "sqlalchemy.engine.interfaces",
                "sqlalchemy.engine.reflection",
                "sqlalchemy.engine.result",
                "sqlalchemy.engine.strategies",
                "sqlalchemy.engine.threadlocal",
                "sqlalchemy.engine.url",
                "sqlalchemy.engine.util",
                "sqlalchemy.event.api",
                "sqlalchemy.event.attr",
                "sqlalchemy.event.base",
                "sqlalchemy.event.legacy",
                "sqlalchemy.event.registry",
                "sqlalchemy.events",
                "sqlalchemy.exc",
                "sqlalchemy.ext.associationproxy",
                "sqlalchemy.ext.automap",
                "sqlalchemy.ext.compiler",
                "sqlalchemy.ext.declarative.api",
                "sqlalchemy.ext.declarative.base",
                "sqlalchemy.ext.declarative.clsregistry",
                "sqlalchemy.ext.horizontal_shard",
                "sqlalchemy.ext.hybrid",
                "sqlalchemy.ext.instrumentation",
                "sqlalchemy.ext.mutable",
                "sqlalchemy.ext.orderinglist",
                "sqlalchemy.ext.serializer",
                "sqlalchemy.inspection",
                "sqlalchemy.interfaces",
                "sqlalchemy.log",
                "sqlalchemy.orm.attributes",
                "sqlalchemy.orm.base",
                "sqlalchemy.orm.collections",
                "sqlalchemy.orm.dependency",
                "sqlalchemy.orm.deprecated_interfaces",
                "sqlalchemy.orm.descriptor_props",
                "sqlalchemy.orm.dynamic",
                "sqlalchemy.orm.evaluator",
                "sqlalchemy.orm.events",
                "sqlalchemy.orm.exc",
                "sqlalchemy.orm.identity",
                "sqlalchemy.orm.instrumentation",
                "sqlalchemy.orm.interfaces",
                "sqlalchemy.orm.loading",
                "sqlalchemy.orm.mapper",
                "sqlalchemy.orm.path_registry",
                "sqlalchemy.orm.persistence",
                "sqlalchemy.orm.properties",
                "sqlalchemy.orm.query",
                "sqlalchemy.orm.relationships",
                "sqlalchemy.orm.scoping",
                "sqlalchemy.orm.session",
                "sqlalchemy.orm.state",
                "sqlalchemy.orm.strategies",
                "sqlalchemy.orm.strategy_options",
                "sqlalchemy.orm.sync",
                "sqlalchemy.orm.unitofwork",
                "sqlalchemy.orm.util",
                "sqlalchemy.pool",
                "sqlalchemy.processors",
                "sqlalchemy.schema",
                "sqlalchemy.sql.annotation",
                "sqlalchemy.sql.base",
                "sqlalchemy.sql.compiler",
                "sqlalchemy.sql.ddl",
                "sqlalchemy.sql.default_comparator",
                "sqlalchemy.sql.dml",
                "sqlalchemy.sql.elements",
                "sqlalchemy.sql.expression",
                "sqlalchemy.sql.functions",
                "sqlalchemy.sql.naming",
                "sqlalchemy.sql.operators",
                "sqlalchemy.sql.schema",
                "sqlalchemy.sql.selectable",
                "sqlalchemy.sql.sqltypes",
                "sqlalchemy.sql.type_api",
                "sqlalchemy.sql.util",
                "sqlalchemy.sql.visitors",
                "sqlalchemy.types",
                "sqlalchemy.util._collections",
                "sqlalchemy.util.compat",
                "sqlalchemy.util.deprecations",
                "sqlalchemy.util.langhelpers",
                "sqlalchemy.util.queue",
                "sqlalchemy.util.topological",
                "flask_sqlalchemy._compat",
                "flask_selfdoc",
                #"jinja2",
                "flask_login",
                "markdown",
                "pkg_resources",
                "bleach",
                "itsdangerous",
                "werkzeug.http",
                "pymysql",
                "asyncio",
                "pyparsing",
                "appdirs",
]

excludes = [    "tkinter",
                "werkzeug.http.os",
                "werkzeug.http.sys",
                "werkzeug.http._sre",
                "werkzeug.http.array",
                "werkzeug.http._locale",
                "werkzeug.http._warnings",
                "werkzeug.http.errno",
                "werkzeug.http.nt",
                "werkzeug.http.strop",
]

includes = [    "traceability",
                "flask",
                #"werkzeug.http",
]

include_files = [
                "trace.conf",
                ICON,
                "lib/snap7.dll",
                "trace.xrc",
                ("tool/sqlitebrowser.exe", "sqlitebrowser.exe"),
                ("tool/clientdemo.exe", "clientdemo.exe"),
]

zip_includes = [
]

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
                     "packages": hidden_imports,
                     "excludes": excludes,
                     "includes": includes,
                     "include_files": include_files,
                     'include_msvcr': True,
                     'zip_includes': zip_includes,
}

# http://msdn.microsoft.com/en-us/library/windows/desktop/aa371847(v=vs.85).aspx
with open(ICON, 'rb') as f:
  ICON_content = f.read()

icon_table = [
    (ICON, ICON_content),
    
]

shortcut_table = [(
         "DesktopShortcut",        # Shortcut
         "DesktopFolder",          # Directory_
         PROJECT_NAME,             # Name
         "TARGETDIR",              # Component_
         "[TARGETDIR]trace.exe",   # Target
         None,                     # Arguments
         SHORT_DESCRIPTION,        # Description
         None,                     # Hotkey
         None,                     # Icon
         None,                     # IconIndex
         None,                     # ShowCmd
         'TARGETDIR'               # WkDir
     )
]
msi_data = {"Shortcut": shortcut_table}
bdist_msi_options = {
    'data': msi_data,
    'initial_target_dir': r'E:\\%s' % PROJECT_NAME,
    'add_to_path': False,
}
# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"


setup(
    name=PROJECT_NAME.lower(),
    version=VERSION,
    url=PROJECT_URL,
    description=SHORT_DESCRIPTION,
    long_description=DESCRIPTION,
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=[
        Executable(
            script='trace.py',
            base=base,
            icon=ICON,
        ),
        Executable(
            script='traceCLI.py',
            base=base,
            icon=ICON,
        )
    ]
)
