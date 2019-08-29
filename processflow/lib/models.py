from __future__ import absolute_import, division, print_function, unicode_literals
from peewee import *

database = SqliteDatabase(None)  # Defer initialization


class DataFile(Model):
    case = CharField()
    name = CharField()
    local_path = CharField()
    local_status = IntegerField()
    year = IntegerField()
    month = IntegerField()
    datatype = CharField()
    super_type = CharField()
    local_size = IntegerField()

    class Meta:
        database = database
