from peewee import *

database = SqliteDatabase(None)  # Defer initialization


class DataFile(Model):
    case = CharField()
    name = CharField()
    local_path = CharField()
    local_status = IntegerField()
    remote_path = CharField()
    remote_status = IntegerField()
    year = IntegerField()
    month = IntegerField()
    datatype = CharField()
    super_type = CharField()
    local_size = IntegerField()
    transfer_type = CharField()
    remote_uuid = CharField()
    remote_hostname = CharField()

    class Meta:
        database = database
