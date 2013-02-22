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

[fred@imac online-migration]$ ./online-migration.py init_sysdb
The database does not exist: online_migration
Creating the database: online_migration
The table does not exist: migration_sys
Creating the table: migration_sys

[fred@imac online-migration]$ ./online-migration.py status world
Warning: no migration was ever initiate on this server for world  !
Migration of schema world : 
  +---------+---------------------+------------------+------------------------+
  | VERSION | APPLIED             | STATUS           |                COMMENT |
  +---------+---------------------+------------------+------------------------+
  |    0000 |                none |          pending |           Initial file |
  |    0001 |                none |          pending |                   none |
  |    0002 |                none |          pending |                   none |
  |    0003 |                none |          pending | add nice column to cit |
  +---------+---------------------+------------------+------------------------+

[fred@imac online-migration]$ ./online-migration.py up world
Schema creation run successfully
[fred@imac online-migration]$ ./online-migration.py status world
Migration of schema world : 
  +---------+---------------------+------------------+------------------------+
  | VERSION | APPLIED             | STATUS           |                COMMENT |
  +---------+---------------------+------------------+------------------------+
  |    0000 | 2013-02-22 09:17:16 |               ok |           Initial file |
  |    0001 |                none |          pending |                   none |
  |    0002 |                none |          pending |                   none |
  |    0003 |                none |          pending | add nice column to cit |
  +---------+---------------------+------------------+------------------------+

[fred@imac online-migration]$ ./online-migration.py up world
Preparing migration to version 0001
Applied changes match the requested schema
[fred@imac online-migration]$ ./online-migration.py status world
Migration of schema world : 
  +---------+---------------------+------------------+------------------------+
  | VERSION | APPLIED             | STATUS           |                COMMENT |
  +---------+---------------------+------------------+------------------------+
  |    0000 | 2013-02-22 09:17:16 |               ok |           Initial file |
  |    0001 | 2013-02-22 09:17:46 |               ok |                   none |
  |    0002 |                none |          pending |                   none |
  |    0003 |                none |          pending | add nice column to cit |
  +---------+---------------------+------------------+------------------------+

[fred@imac online-migration]$ ./online-migration.py up world to 3
NOTICE: you want to migrate up to version 0003
NOTICE: ok this version is pending
Preparing migration to version 0002
Applied changes match the requested schema
Preparing migration to version 0003
Applied changes match the requested schema
[fred@imac online-migration]$ ./online-migration.py status world
Migration of schema world : 
  +---------+---------------------+------------------+------------------------+
  | VERSION | APPLIED             | STATUS           |                COMMENT |
  +---------+---------------------+------------------+------------------------+
  |    0000 | 2013-02-22 09:17:16 |               ok |           Initial file |
  |    0001 | 2013-02-22 09:17:46 |               ok |                   none |
  |    0002 | 2013-02-22 09:18:24 |               ok |                   none |
  |    0003 | 2013-02-22 09:18:36 |               ok | add nice column to cit |
  +---------+---------------------+------------------+------------------------+


