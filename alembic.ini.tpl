[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]

[formatters]

[logger_root]
level = WARN
handlers =
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_root]
class = StreamHandler
level = INFO
formatter =
args = (sys.stderr,)

[handler_alembic]
class = StreamHandler
level = INFO
formatter =
args = (sys.stderr,)

[formatter_root]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S

[formatter_sqlalchemy]
format = %(asctime)s %(levelname)s %(message)s
datefmt = %H:%M:%S

[formatter_alembic]
format = %(levelname)-5.5s %(message)s
datefmt = %H:%M:%S