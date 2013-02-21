ON THE DEVEL MACHINE
====================

[fred@imac online-migration]$ ./online-migration.py init_sysdb
The database does not exist: online_migration
Creating the database: online_migration
The table does not exist: migration_sys
Creating the table: migration_sys

mysql> create database world


[fred@imac online-migration]$ ./online-migration.py init world


[fred@imac online-migration]$ ./online-migration.py create world examples/world_structure.sql 
migration 0001 created successfully !
[fred@imac online-migration]$ ./online-migration.py create world examples/world_v2.sql 
migration 0002 created successfully !


[fred@imac online-migration]$ ./online-migration.py status
Migration of schema world : 
  +---------+---------------------+------------------+------------------------+
  | VERSION | APPLIED             | STATUS           |                COMMENT |
  +---------+---------------------+------------------+------------------------+
  |    0000 | 2013-02-21 22:38:47 |               ok |           Initial file |
  |    0001 | 2013-02-21 22:38:56 |               ok |                   none |
  |    0002 | 2013-02-21 22:39:11 |               ok |                   none |
  +---------+---------------------+------------------+------------------------+

[fred@imac online-migration]$ ./online-migration.py create world examples/world_v3.sql "add nice column to city"
migration 0003 created successfully !
[fred@imac online-migration]$ ./online-migration.py status world
Migration of schema world : 
  +---------+---------------------+------------------+------------------------+
  | VERSION | APPLIED             | STATUS           |                COMMENT |
  +---------+---------------------+------------------+------------------------+
  |    0000 | 2013-02-21 22:38:47 |               ok |           Initial file |
  |    0001 | 2013-02-21 22:38:56 |               ok |                   none |
  |    0002 | 2013-02-21 22:39:11 |               ok |                   none |
  |    0003 | 2013-02-21 22:42:13 |               ok | add nice column to cit |
  +---------+---------------------+------------------+------------------------+

ON THE PRODUCTION
=================

