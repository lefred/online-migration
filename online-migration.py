#!/usr/bin/python

# GPLv2 - All right reserved to Frederic Descamps - lefred@lefred.be

import sys
import os
import hashlib
import re
import glob
import pickle
import StringIO
import logging
import ConfigParser
import argparse


# New imports
from mysql.utilities.common import (database, options, server, table)
from mysql.utilities.command import dbcompare, dbcopy, dbexport
from mysql.utilities.common.ip_parser import parse_connection


#sys.path.append("./mysql")
from subprocess import call
from contextlib import contextmanager

server_host = '127.0.0.1'
server_port = '3306'
server_user = 'root'
server_password = ''

server_connection = "%s:%s@%s:%s" % (server_user, server_password,
                                     server_host, server_port)
#server_connection = ""

logging.basicConfig(format = "%(levelname)s : %(message)s", level = logging.INFO)

# script version
version=0.4

def memoize(func):
    cache = dict()

    def wrapper(*args, **kwargs):
        key = (func, args, frozenset(kwargs.items()))
        if key in cache:
            return cache.get(key)
        value = func(*args, **kwargs)
        cache[key] = value
        return value
    return wrapper


@contextmanager
def capture():
    old_stdout = sys.stdout
    sys.stdout = StringIO.StringIO()
    try:
        yield sys.stdout
    finally:
        sys.stdout = old_stdout


def calculate_md5(filename):
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest()


class OnlineMigration(object):

    def __init__(self,
                 server,
                 database=u"online_migration",
                 table=u"migration_sys",
                 tmp_prefix=u"tmp_online_mig"):
        self.server = server
        self.database = database
        self.table = table
        self.tmp_prefix = tmp_prefix

    @property
    @memoize
    def migration_db(self):
        """ Connect and return the connection to MySQL """
        return self.connect_db(self.database)

    @property
    def migration_table(self):
        return "%s.%s" % (self.database, self.table)

    @memoize
    def connect_db(self, db_name):
        """ Method to connect to MySQL """
        db_options = {u'skip_grants': True}
        return database.Database(self.server, db_name, db_options)

    def init_sysdb(self):
        """
        Creates the needed system database and table used by online-migration
        """
        if self.migration_db.exists() is False:
            logging.info(u"The database does not exist: %s" % self.database)
            logging.info(u"Creating the database: %s" % self.database)
            self.migration_db.create(self.server, self.database)
        migration_table = table.Table(self.server, self.migration_table)
        if migration_table.exists() is True:
            logging.warning("System table already exists")
        else:
            logging.info(u"The table does not exist: %s" % self.table)
            logging.info(u"Creating the table: %s" % self.table)
            try:
                self.server.exec_query(u"CREATE TABLE %(table)s (id int "
                    u"auto_increment primary key, db varchar(100), version "
                    u"int, start_date datetime, apply_date datetime, "
                    u"status varchar(10));" % {u'table': self.migration_table})
            except Exception, e:
                logging.error(u"Problem creating the system table %s !" % e)
                sys.exit(1)

    def check_arg(self, num=1):
        """ check that a db was entered """
        if len(sys.argv) <= num + 1:
            logging.error(u"%i argument(s) is/are required with command %s !" % (num, sys.argv[1]))
            sys.exit(1)

    def check_sys_init(self, exit=1):
        """ Check if the system table are created """
        if self.migration_db.exists() is False or \
           table.Table(self.server, self.migration_table).exists() is False:
            if exit == 1:
            	logging.error("online-migration was not initialized on this server!\nplease run online-migration init_sysdb.")
            	sys.exit(1)
            else:
		return 1
	return 0

    def create_meta(self, db_name, version, md5check, comment):
        file_meta = open("%s/%04d-up.meta" % (db_name, int(version)), 'w')
        file_meta.write("%s\n" % version)
        file_meta.write("%s\n" % md5check)
        file_meta.write("%s\n" % comment)
        file_meta.close()

    def check_init(self, db_name):
        """ Check if there is already a migration for that database """
        query = u'SELECT * FROM %(from)s WHERE `db` = \"%(db_name)s\";'
        res = self.server.exec_query(query % {u'from': self.migration_table,
                                              u'db_name': db_name})
        return (res is not None and len(res) >= 1)

    def online_schema_change(self, db_name, version, file_name, cmd=u'up'):
        f = open(file_name, "r")
        for line in iter(f):
            self.change_migration_status(db_name, version, 'running')
            line_list = line.split("::")
            if line_list[0] == "OM_IGNORE_TABLE":
                self.server.disable_foreign_key_checks()
                query = line_list[1]
                query_options = {
                    'params': (db_name)
                }
                try:
                    self.server.exec_query("use %s" % db_name)
                    self.server.exec_query(query)
                except Exception, e:
                    logging.error(u"%s !" % e)
                    sys.exit(1)
                # create the undo for table creation here
                if cmd == "up":
                    file_down = open("%s/%04d-down.mig" % (db_name, int(version)), 'a')
                    #if re.search('^create', query, re.IGNORECASE):
                    if re.search('^create' + '(?i)', query):
                        #query = re.sub("`", " ", query, 0, re.IGNORECASE)
                        query = re.sub("`" + '(?i)', " ", query, 0)
                        #regex = re.compile("create\s+table\s+(\w+)", re.IGNORECASE)
                        regex = re.compile("create\s+table\s+(\w+)"+ '(?i)')
                        r = regex.search(query)
                        table = r.group(1)
                        file_down.write("DROP TABLE %s;\n" % table)
                    file_down.close()
                self.server.disable_foreign_key_checks(disable=False)
            else:
                cmd = "pt-online-schema-change h=%s,P=%s,u=%s,p=%s,D=\"%s\",t=%s --alter=\"%s\" --execute >>online_migration.log 2>&1" % (server_host, server_port, server_user, server_password, db_name, line_list[0], line_list[1])
                #print cmd
                if call(cmd, shell=True) != 0:
                    logging.error(u"Problem while running :\n   %s" % cmd )
                    sys.exit(1)
        self.change_migration_status(db_name, version, 'ok')

    def write_stmt_up(self, table, alter_stmt, file):
        #alter_stmt = re.sub("alter\s+table\s+%s" % table, "", alter_stmt, 1, re.IGNORECASE)
        alter_stmt = re.sub("alter\s+table\s+%s" % table + '(?i)', "", alter_stmt, 1)
        alter_stmt = alter_stmt.replace('\n', ' ')
        alter_stmt = re.sub("^\s+", "", alter_stmt)
        file.write("%s::%s\n" % (table, alter_stmt))

    def change_migration_status(self, db_name, version, status):
        last_version = self.last_migration_version(db_name)
        if last_version is None:
            last_version = "-1"
        if int(last_version) == int(version):
            query = "UPDATE %s SET STATUS = '%s', apply_date=now() WHERE db = '%s' AND version = %s" % (self.migration_table, status, db_name, version)
        else:
            query = "SELECT version FROM %s WHERE `version` = %s and `db` = \"%s\";" % (self.migration_table, version, db_name)
            res = self.server.exec_query(query)
            if (res is None or len(res) < 1):
                query = "INSERT INTO %s VALUES (0,'%s',%s,now(),now(),'ok')" % (self.migration_table, db_name, version)
            else:
                query = "UPDATE %s SET STATUS = '%s', apply_date=now() WHERE db = '%s' AND version = %s" % (self.migration_table, status, db_name, version)
        try:
            res = self.server.exec_query(query)
        except Exception, e:
            logging.error(u"%s !" % e)
            sys.exit(1)

    def pending_migration(self, db_name, last_ver):
        pend = 0
        metafiles = glob.glob('%s/*.meta' % db_name)
        metafiles.sort()
	if not last_ver:
	    last_ver=-1
        for mig in metafiles:
            a = mig.split('/')
            b = a[1].split('.')
            c = b[0].split('-')
            if int(c[0]) > int(last_ver):
                pend = pend + 1
        return pend

    def check_version_pending(self, db_name, version):
        last_ver = self.last_migration_version(db_name)
        metafiles = glob.glob('%s/%04d-up.meta' % (db_name, version))
        metafiles.sort()
        for mig in metafiles:
            a = mig.split('/')
            b = a[1].split('.')
            c = b[0].split('-')
            if int(c[0]) > int(last_ver):
                return True
        return False

    def applied_migration(self, db_name):
        query = "SELECT version, apply_date, status FROM %s where status not like 'rollback' AND db = '%s';" % (self.migration_table, db_name)
        res = self.server.exec_query(query)
        return len(res) - 1

    def check_version_applied(self, db_name, version):
        query = "SELECT version, apply_date, status FROM %s where version = %s AND status not like 'rollback' AND db = '%s';" % (self.migration_table, version, db_name)
        res = self.server.exec_query(query)
        if len(res) > 0:
            return True
        else:
            return False

    def new_migration_version(self, db_name):
        query = "SELECT version, apply_date, status FROM %s where db = '%s';" % (self.migration_table, db_name)
        self.server.exec_query(query)
        last_version = self.last_migration_version(db_name)
        return int(last_version) + 1

    def last_migration_version(self, db_name):
        query = "SELECT max(version) FROM %s WHERE status <> 'rollback' AND `db` = \"%s\";" % (self.migration_table, db_name)
        res = self.server.exec_query(query)
        if res is None:
            logging.error(u"There is no migration initilized for database %s !" % db_name)
            sys.exit(1)
        return (res[0][0])

    def add_up_in_db(self, db_name, version):
        query = "INSERT INTO %s VALUES (0,'%s',%s,now(),now(),'started');" % (self.migration_table, db_name, version)
        try:
            self.server.exec_query(query)
        except Exception, e:
            logging.error(u"ERROR: %s !" % e)
            sys.exit(1)

    def create_migration_file(self, db_name, file_name, version, direction):
        file_up = open("%s/%04d-%s.mig" % (db_name, int(version), direction), 'w')
        f = open(file_name, "r")
        alter_stmt = ""
        other_stmt = ""
        open_stmt = 0  # 1=alter, 2=other (insert, create, drop)
        for line in iter(f):
            if re.search('AUTO_INCREMENT=', line):
                logging.debug("Auto_incrment reset to ignore")
            	#line= re.sub("AUTO_INCREMENT=(\d)*","", line, 1, re.IGNORECASE)
            	line= re.sub("AUTO_INCREMENT=(\d)*" + '(?i)',"", line, 1)
                other_stmt += line
            #elif re.search('^alter', line, re.IGNORECASE):
            elif re.search('^alter' + '(?i)', line):
                open_stmt = 1
                if len(alter_stmt) > 0:
                    #as we remove auto_increment we need to replace , by ;
            	    #alter_stmt = re.sub(",$",";", alter_stmt, 1, re.IGNORECASE)
            	    alter_stmt = re.sub(",$" + '(?i)',";", alter_stmt, 1)
	    	    logging.debug(u"[%s]" % alter_stmt)
                    #save the alter statement in a migration file
                    self.write_stmt_up(table, alter_stmt, file_up)
                if len(other_stmt) > 0:
                    self.write_stmt_up("OM_IGNORE_TABLE", other_stmt, file_up)
                    other_stmt = ""
                alter_stmt = line
	    	logging.debug(u"[%s]" % alter_stmt)
                #import pdb; pdb.set_trace()
                regex = re.compile("alter\s+table\s+`([^\s]*)`\.`([^\s]*)`\s+.*"+ '(?i)')
                r = regex.search(line)
                if not r:
                   regex = re.compile("alter\s+table\s+([^\s]*)\s+.*", re.IGNORECASE)
                   r = regex.search(line)
                   table = r.group(1)
                else:
                   table = r.group(2)
            else:
                if re.search('^insert|^create|^drop'+ '(?i)', line) and not re.search(' column | primary | key | index '+ '(?i)', line):
                    open_stmt = 2
                    if len(other_stmt) > 0:
                        self.write_stmt_up("OM_IGNORE_TABLE", other_stmt, file_up)
                        other_stmt = ""
                    if len(alter_stmt) > 0:
                        self.write_stmt_up(table, alter_stmt, file_up)
                        alter_stmt = ""
                    other_stmt += line
                else:
                    if open_stmt == 1:
                            alter_stmt += line
                    else:
                        other_stmt += line
        # save the alter statement in a migration file
        if open_stmt == 1:
            alter_stmt = re.sub("`\w+`\.`\w+`", table, alter_stmt)
            alter_stmt = re.sub(",$", "", alter_stmt)
            self.write_stmt_up(table, alter_stmt, file_up)
        else:
            self.write_stmt_up("OM_IGNORE_TABLE", other_stmt, file_up)
        file_up.close()

    def create_migration(self, db_name, file_name, comment=""):
        if not os.path.exists(file_name):
            logging.error(u"%s doesn't exist !" % file_name)
            sys.exit(1)
        db_obj = self.connect_db(db_name)
        if not db_obj.exists():
            logging.error(u"Database %s doesn't exist !" % db_name)
            sys.exit(1)
        # find the migration version
        last_version = self.last_migration_version(db_name)
        # check first if there are pending migrations
        pend = self.pending_migration(db_name, last_version)
        if pend > 0:
            logging.error(u"ERROR: you have %s pending migration(s) !" % pend)
            sys.exit(1)
        version = self.new_migration_version(db_name)
        self.create_migration_file(db_name, file_name, version, "up")
        self.add_up_in_db(db_name, version)
        self.online_schema_change(db_name, version, "%s/%04d-up.mig" % (db_name, int(version)))
        logging.info(u"migration %04d created successfully !" % int(version))
        md5check = self.create_checksum(db_name, version)
        self.create_meta(db_name, version, md5check, comment)

    def create_checksum(self, db_name, version):
        version = self.last_migration_version(db_name)
        tmp_file = "%s/%04d.schema_tmp" % (db_name, int(version))
        self.create_schema_img(db_name, tmp_file)
        md5check = calculate_md5(tmp_file)
        os.remove(tmp_file)
        return md5check

    def init_migration(self, db_name):
        """ Function to initiate the first migration """
        if self.check_init(db_name):
            logging.error(u"init was already performed for database %s !" % db_name)
            sys.exit(1)
        query = "INSERT INTO %s VALUES (0,'%s',0,now(),now(),'ok');" % (self.migration_table, db_name)
        if os.path.exists("%s/0000-up.mig" % db_name):
            logging.error(u"There's already an init file for this schema (%s/0000-up.mig)" % db_name)
            sys.exit(1)
        try:
            res = self.server.exec_query(query)
        except Exception, e:
            logging.error(u"%s !" % e)
            sys.exit(1)
        db_obj = self.connect_db(db_name)
        table_names = [obj[0] for obj in db_obj.get_db_objects('TABLE')]
        if not os.path.exists(db_name):
            os.makedirs(db_name)
        file_up = open(db_name + "/" + "0000-up.mig", 'w')
        file_up.write("CREATE DATABASE %s;\n" % db_name)
        file_up.write("USE %s;\n" % db_name)
        for tblname in table_names:
            file_up.write("#table: %s\n" % tblname)
            query = "SHOW CREATE TABLE %s.%s;" % (db_name, tblname)
            res = self.server.exec_query(query)
            file_up.write("%s\n" % res[0][1])
        file_up.close()
        md5check = self.create_checksum(db_name, 0)
        self.create_meta(db_name, 0, md5check, "Initial file")

    def status(self, db_name=None):
        """ Display the status of the migration for all or one schema """
        query = "SELECT distinct db FROM %s;" % self.migration_table
        res = self.server.exec_query(query)
        if res is None:
            logging.warning("No migration was ever initiate on this server !")
            #sys.exit(1)
        if db_name is None:
            for db in res:
                self.status_db(db[0])
        else:
            query = "SELECT distinct db FROM %s where db = '%s';" % (self.migration_table, db_name)
            res = self.server.exec_query(query)
            if (res is None or len(res) < 1):
                logging.warning(u"no migration was ever initiate on this server for %s  !" % db_name)
                if not os.path.exists(db_name):
                    logging.error("no data related to any migration available !")
                    sys.exit(1)
            self.status_db(db_name)

    def status_db(self, db_name):
        query = "SELECT version, apply_date, status FROM %s where db = '%s';" % (self.migration_table, db_name)
        res = self.server.exec_query(query)
        last_ver = -2
        print "Migration of schema %s : " % db_name
        print '  +---------+---------------------+------------------+------------------------+'
        print '  | VERSION | APPLIED             | STATUS           |                COMMENT |'
        print '  +---------+---------------------+------------------+------------------------+'
        if len(res) > 0:
            # before displaying the status, let's verify the checksum
            last_ver = self.last_migration_version(db_name)
            for records in res:
                (ver, md5, comment) = self.read_meta(db_name, records[0])
                status = records[2]
                if ver == last_ver:
                    if not self.verify_checksum(db_name, ver, md5) and status != "rollback":
                        status = "checksum problem"
                ver = "%04d" % int(ver)
                print "  | %7s | %s | %16s | %22s |" % (ver, records[1], status, comment[:22])
        metafiles = glob.glob('%s/*.meta' % db_name)
        metafiles.sort()
        for mig in metafiles:
            a = mig.split('/')
            b = a[1].split('.')
            c = b[0].split('-')
            if int(c[0]) > int(last_ver):
                (ver, md5, comment) = self.read_meta(db_name, int(c[0]))
                print "  | %7s | %19s | %16s | %22s |" % (c[0], 'none', 'pending', comment[:22])
        print '  +---------+---------------------+------------------+------------------------+'

    def verify_checksum(self, db_name, version, md5):
        checksum = self.create_checksum(db_name, version)
        logging.debug("md5=%s     checksum=%s" % (md5,checksum))
        if checksum == md5:
            return True
        else:
            return False

    def get_diff(self, db_name, version):
        file_schema = "%s/%04d-schema.img" % (db_name, int(version))
        file_schema_swp = "%s/%04d-schema.swp" % (db_name, int(version))
        tmp_db = "tmp_online_mig_%s" % (db_name)
        query = "CREATE DATABASE %s;" % tmp_db
        self.server.disable_foreign_key_checks()
        self.server.exec_query(query)
        f = open(file_schema, 'r')
        f_swp = open(file_schema_swp, 'w')
        f_swp.write("USE %s\n" % tmp_db)
        buff = ""
        for line in f.readlines():
            #if re.search(';$', line, re.IGNORECASE):
            if re.search(';$' + '(?i)', line):
                buff = buff + line
                f_swp.write(buff)
                buff = ""
            else:
                buff = buff + line.strip()
        f.close()
        f_swp.close()
        query_options = {'multi': True}
        f_swp = open(file_schema_swp, 'r')
        for line in f_swp.readlines():
            self.server.exec_query(line, query_options)
        f_swp.close()
        os.remove(file_schema_swp)
        query_options = {
            'run_all_tests': True, 'reverse': False, 'verbosity': None,
            'no_object_check': False, 'no_data': True, 'quiet': True,
            'difftype': 'differ', 'width': 75, 'changes-for': 'server1',
            'skip_grants': True}
        source_values = parse_connection(server_connection)
        destination_values = parse_connection(server_connection)
        with capture() as stepback:
            dbcompare.database_compare(source_values, destination_values, db_name, tmp_db, query_options)
        buf = ""
        found = 0
        for line in stepback.getvalue().splitlines(True):
            logging.debug(u"%s" % line)
            if re.search('CREATE TABLE', line):
                line = re.sub("CREATE" + '(?i)',"", line, 1)
                #line = re.sub("CREATE","", line, 1, re.IGNORECASE)
                #line = re.sub("\(\n","", line, 1, re.IGNORECASE)
                line = re.sub("\(\n" + '(?i)',"", line, 1)
		buf=line
            if (re.search('^\+', line) or re.search('^\-', line)) and not re.search('CREATE DATABASE', line) and not re.search('CONSTRAINT.*FOREIGN KEY', line):
                #line = re.sub("\n","", line, 1, re.IGNORECASE)
                line = re.sub("\n" + '(?i)',"", line, 1)
                if len(buf) > 0:
		    print u"%s" % buf
                    buf=""
		print u"%s" % line 
        query = "DROP DATABASE %s" % tmp_db
        self.server.exec_query(query)
        self.server.disable_foreign_key_checks(disable=False)

    def print_diff(self, db_name):
        last_version = self.last_migration_version(db_name)
        (ver, md5, comment) = self.read_meta(db_name, int(last_version))
        if self.verify_checksum(db_name, last_version, md5) is False:
            logging.warning(u"Schema of %s doesn't have expected checksum (%s)" % (db_name, md5))
            self.get_diff(db_name, last_version)
        else:
            print "%s matches the expected schema for version %04d" % (db_name, int(last_version))

    def read_meta(self, db_name, version):
        f = open("%s/%04d-up.meta" % (db_name, int(version)), 'r')
        ver = f.readline()
        md5 = f.readline()
        comment = f.readline()
        return(ver.rstrip(), md5.rstrip(), comment.rstrip())

    def mysql_create_schema(self, db_name, file_name):
        #f = open(file_name,"r")
        s_pwd = ""
        if len(server_password) > 0:
		s_pwd="-p%s" % server_password
        self.change_migration_status(db_name, 0, 'running')
        cmd = "mysql -u %s %s -h %s -P %s < %s >>online_migration.log 2>&1" % (server_user, s_pwd, server_host, server_port, file_name)
        if call(cmd, shell=True) == 0:
            logging.info("Schema creation run successfully")
        else:
            logging.error(u"ERROR: problem while running :\n   %s" % cmd)
            sys.exit(1)
        self.change_migration_status(db_name, 0, 'ok')

    def get_schema_img(self, db_name):
        with capture() as dbschema:
            server_values = parse_connection(server_connection)
            query_options = {'skip_data': True, 'skip_grants': True, 'skip_create': True,
                       'rpl_mode': None, 'quiet': True}
        db_list = []
        db_list.append(db_name)
        with capture() as dbschema:
           dbexport.export_databases(server_values, db_list, sys.stdout, query_options)

        db_schema = dbschema.getvalue().splitlines(True)
        return db_schema

    def create_schema_img(self, db_name, filename):
        dbschema = self.get_schema_img(db_name)
        file_schema = open(filename, 'w')
        i = 0
        for line in dbschema:
            if i > 0:
            	if re.search("\s+CONSTRAINT .* FOREIGN KEY", line):
                    # dirty hack to try to support foreign keys
		    logging.debug("We found a constraint to rename")
                    #line = re.sub("CONSTRAINT `_*","CONSTRAINT `", line, 1, re.IGNORECASE)
                    line = re.sub("CONSTRAINT `_*" + '(?i)',"CONSTRAINT `", line, 1)
                
                file_schema.write("%s" % line)
            i += 1
        file_schema.close()

    def migrate_down(self, db_name, last_version):
        logging.info(u"rollback from %04d to %04d" % (int(last_version), int(last_version) - 1))
        self.online_schema_change(db_name, last_version, "%s/%04d-down.mig" % (db_name, int(last_version)), 'down')
        self.change_migration_status(db_name, last_version, 'rollback')

    def migrate_up(self, db_name, last_version):
        (ver, md5, comment) = self.read_meta(db_name, int(last_version))
        if self.verify_checksum(db_name, last_version, md5) is False:
            logging.warning("The current schema doesn't match the last applied migration")
        version = self.new_migration_version(db_name)
        if not os.path.exists("%s/%04d-up.mig" % (db_name, int(version))):
            logging.info("No migration available")
        else:
            logging.info(u"Preparing migration to version %04d" % int(version))
            if os.path.exists("%s/%04d-down.mig" % (db_name, int(version))):
                os.remove("%s/%04d-down.mig" % (db_name, int(version)))
            (ver, md5, comment) = self.read_meta(db_name, int(version))
            query_options = {'skip_data': True, 'force': True}
            db_list = []
            grp = re.match("(\w+)(?:\:(\w+))?", "%s:%s_%s" % (db_name, self.tmp_prefix, db_name))
            db_entry = grp.groups()
            db_list.append(db_entry)
            source_values = parse_connection(server_connection)
            destination_values = parse_connection(server_connection)
            with capture() as stepback:
                dbcopy.copy_db(source_values, destination_values, db_list, query_options)
            self.online_schema_change(db_name, version, "%s/%04d-up.mig" % (db_name, int(version)))
            if self.verify_checksum(db_name, version, md5) is True:
                logging.info("Applied changes match the requested schema")
            else:
                logging.error("Something didn't run as expected, db schema doesn't match !")
                self.change_migration_status(db_name, version, 'invalid checksum')
            query_options = {
                'run_all_tests': True, 'reverse': True, 'verbosity': None,
                'no_object_check': False, 'no_data': True, 'quiet': True,
                'difftype': 'sql', 'width': 75, 'changes-for': 'server1',
                'skip_grants': True}
            with capture() as stepback:
                res = dbcompare.database_compare(source_values, destination_values, db_name, "%s_%s" % (self.tmp_prefix, db_name), query_options)
            str = stepback.getvalue().splitlines(True)
            to_add = 0
            file_down = open("%s/%04d-down.tmp" % (db_name, int(version)), 'a')
            for line in str:
                if line[0] not in ['#', '\n', '+', '-', '@']:
                    # this if is required currently due to missing foreign keys in dbcopy
                    if not re.match("\s+DROP FOREIGN KEY", line):
                        #line = re.sub(" %s\." % db_name, " ", line, 1, re.IGNORECASE)
                        line = re.sub(" %s\." % db_name + '(?i)', " ", line, 1)
                        file_down.write("%s\n" % line.strip())
                elif re.match("# WARNING: Objects in", line):
                    if re.match("# WARNING: Objects in \w+\.tmp_online_mig_", line):
                        to_add = 2
                    else:
                        to_add = 1
                else:
                    grp = re.match("#\s+TABLE\: (\w+)", line)
                    if grp:
                        if to_add == 2:
                            query = "SHOW CREATE TABLE tmp_online_mig_%s.%s;" % (db_name, grp.group(1))
                            res = self.server.exec_query(query)
                            file_down.write("%s\n" % res[0][1])
                        elif to_add == 1:
                            file_down.write("DROP TABLE %s;\n" % grp.group(1))
            file_down.close()
            file_down_tmp = "%s/%04d-down.tmp" % (db_name, int(version))
            self.create_migration_file(db_name, file_down_tmp, version, "down")
            query = "DROP DATABASE %s_%s" % (self.tmp_prefix, db_name)
            res = self.server.exec_query(query)
            #os.remove(file_down_tmp)
            file_schema = "%s/%04d-schema.img" % (db_name, int(version))
            self.create_schema_img(db_name, file_schema)


def main():
    
    # let's add cfg file to deal with the connections
    # file will be /etc/online-migration.cfg
    #
    # content will be like:
    #
    # [world]
    # user=root
    # password=fred
    # host=127.0.0.1
    # port=3340
    #
    # [sysbench]
    # user=test
    # password=test
    # host=127.0.0.1
    # port=3306 
    
    
    if len(sys.argv) < 2:
        logging.error("A command is needed\ncommands are: init, create, status, checksum, down, up, diff, version")
        sys.exit(1)
    else:
        with capture() as nowhere:
            try:
            	migration = OnlineMigration(
                	server.get_server(u'localhost', server_connection, False))
            except Exception, e:
                logging.error("%s" % e[0])
                sys.exit(1)
	
        if sys.argv[1] == 'init_sysdb':
            migration.init_sysdb()
        elif sys.argv[1] == 'init':
            migration.check_arg()
            migration.check_sys_init()
            migration.init_migration(sys.argv[2])
        elif sys.argv[1] == 'create':
            migration.check_arg(2)
            migration.check_sys_init()
            if len(sys.argv) > 4:
                comment = sys.argv[4]
            else:
                comment = "none"
            migration.create_migration(sys.argv[2], sys.argv[3], comment)
        elif sys.argv[1] == 'status':
            migration.check_arg(0)
            migration.check_sys_init()
            if len(sys.argv) == 3:
                db_name = (sys.argv[2])
            else:
                db_name = None
            migration.status(db_name)
        elif sys.argv[1] == 'checksum':
            migration.check_arg(1)
            migration.check_sys_init()
            db_name = (sys.argv[2])
            checksum = migration.create_checksum(db_name, "0")
            print "%s's current schema checksum = %s" % (db_name, checksum)
        elif sys.argv[1] == 'down':
            migration.check_arg(1)
            migration.check_sys_init()
            db_name = (sys.argv[2])
            last_version = migration.last_migration_version(db_name)
            if len(sys.argv) == 4 and re.search("\d", sys.argv[3]):
                logging.info(u"You want to migrate down %d version(s)" % int(sys.argv[3]))
                tot = 0
                tot_app = migration.applied_migration(db_name)
                if tot_app >= int(sys.argv[3]):
                    while tot < int(sys.argv[3]):
                        last_version = migration.last_migration_version(db_name)
                        migration.migrate_down(db_name, last_version)
                        tot += 1
                else:
                    logging.error(u"Only %d applied migration(s) available !" % tot_app)
                    sys.exit(1)
            elif len(sys.argv) == 5:
                if sys.argv[3] == 'to' and re.search("\d", sys.argv[4]):
                    logging.info(u"You want to migrate down to version %04d" % int(sys.argv[4]))
                    if migration.check_version_applied(db_name, int(sys.argv[4])):
                        logging.info("Ok this version was applied")
                        while int(last_version) > int(sys.argv[4]):
                            migration.migrate_down(db_name, last_version)
                            last_version = migration.last_migration_version(db_name)
            else:
                if last_version is not None and int(last_version) > 0:
                    migration.migrate_down(db_name, last_version)
                else:
                    logging.error("Impossible to rollback as nothing was migrated yet !")
                    sys.exit(1)
        elif sys.argv[1] == 'up':
            migration.check_arg(1)
            migration.check_sys_init()
            db_name = (sys.argv[2])
            last_version = migration.last_migration_version(db_name)
            if last_version is None and len(sys.argv) > 3:
                logging.error("You can only migrate multiple versions when at least one has been already performed")
                sys.exit(1)
             
            if len(sys.argv) == 4 and re.search("\d", sys.argv[3]):
                logging.info(u"You want to migrate up %d version(s)" % int(sys.argv[3]))
                tot = 0
                tot_pend = migration.pending_migration(db_name, last_version)
                if tot_pend >= int(sys.argv[3]):
                    while tot < int(sys.argv[3]):
                        last_version = migration.last_migration_version(db_name)
                        migration.migrate_up(db_name, last_version)
                        tot += 1
                else:
                    logging.error(u"Only %d pending migration(s) available !" % tot_pend)
                    sys.exit(1)
            elif len(sys.argv) == 5:
                if sys.argv[3] == 'to' and re.search("\d", sys.argv[4]):
                    logging.info(u"You want to migrate up to version %04d" % int(sys.argv[4]))
                    if migration.check_version_pending(db_name, int(sys.argv[4])):
                        logging.info("Ok this version is pending")
                        while int(last_version) < int(sys.argv[4]):
                            migration.migrate_up(db_name, last_version)
                            last_version = migration.last_migration_version(db_name)
		    else:
                        logging.error(u"This version (%04d) is not available as a pending migration !" % int(sys.argv[4]))
                        sys.exit(1)
            else:
                if last_version is not None:
                    migration.migrate_up(db_name, last_version)
                else:
                    migration.mysql_create_schema(db_name, "%s/0000-up.mig" % db_name)
        elif sys.argv[1] == 'diff':
            migration.check_arg(1)
            migration.check_sys_init()
            db_name = (sys.argv[2])
            migration.print_diff(db_name)
        elif sys.argv[1] == 'version':
	    print "online-migration.py %s" % version
	elif sys.argv[1] == 'last_version':
            migration.check_arg(1)
            if migration.check_sys_init(0) == 1:
	       	print -1
            else:
            	db_name = (sys.argv[2])
            	last_version = migration.last_migration_version(db_name)
	    	print last_version

main()
