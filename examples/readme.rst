ON THE DEVEL MACHINE
====================

Initialization of the tool::

	[fred@imac online-migration]$ ./online-migration.py init_sysdb
	The database does not exist: online_migration
	Creating the database: online_migration
	The table does not exist: migration_sys
	Creating the table: migration_sys

	mysql> create database world


	[fred@imac online-migration]$ ./online-migration.py init world


Creation of migration releases::


	[fred@imac online-migration]$ ./online-migration.py create world examples/world_structure.sql 
	INFO : migration 0001 created successfully !
	[fred@imac online-migration]$ ./online-migration.py create world examples/world_v2.sql 
	INFO : migration 0002 created successfully !

Check the status::

	[fred@imac online-migration]$ ./online-migration.py status
	Migration of schema world : 
	  +---------+---------------------+------------------+------------------------+
	  | VERSION | APPLIED             | STATUS           |                COMMENT |
	  +---------+---------------------+------------------+------------------------+
	  |    0000 | 2013-02-21 22:38:47 |               ok |           Initial file |
	  |    0001 | 2013-02-21 22:38:56 |               ok |                   none |
	  |    0002 | 2013-02-21 22:39:11 |               ok |                   none |
	  +---------+---------------------+------------------+------------------------+

Creation of migration releases with comment::

        [fred@imac online-migration]$ ./online-migration.py create world examples/world_v3.sql "add nice column to city"
        INFO : migration 0003 created successfully !
        [fred@imac online-migration]$ ./online-migration.py status world
        Migration of schema world : 
          +---------+---------------------+------------------+------------------------+
          | VERSION | APPLIED             | STATUS           |                COMMENT |
          +---------+---------------------+------------------+------------------------+
          |    0000 | 2013-02-21 22:38:47 |               ok |           Initial file |
          |    0001 | 2013-02-21 22:38:55 |               ok |                   none |
          |    0002 | 2013-02-21 22:39:11 |               ok |                   none |
          |    0003 | 2013-02-21 22:42:13 |               ok | add nice column to cit |
          +---------+---------------------+------------------+------------------------+

ON THE PRODUCTION
=================

Again first initialization is required::

	[fred@imac online-migration]$ ./online-migration.py init_sysdb
	INFO : The database does not exist: online_migration
	INFO : Creating the database: online_migration
	INFO : The table does not exist: migration_sys
	INFO : Creating the table: migration_sys

We can see the status with all pending releases::

	[fred@imac online-migration]$ ./online-migration.py status world
	WARNING : no migration was ever initiate on this server for world  !
	Migration of schema world : 
	  +---------+---------------------+------------------+------------------------+
	  | VERSION | APPLIED             | STATUS           |                COMMENT |
	  +---------+---------------------+------------------+------------------------+
	  |    0000 |                none |          pending |           Initial file |
	  |    0001 |                none |          pending |                   none |
	  |    0002 |                none |          pending |                   none |
	  |    0003 |                none |          pending | add nice column to cit |
	  +---------+---------------------+------------------+------------------------+

Let's migrate (up) to the next version::

	[fred@imac online-migration]$ ./online-migration.py up world
	INFO : Schema creation run successfully
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

It is also possible to update to a specific version::

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

This works also with downgrades (rollback)::

	[fred@macbookair online-migration]$ ./online-migration.py down world to 1
	INFO : You want to migrate down to version 0001
	INFO : Ok this version was applied
	INFO : rollback from 0003 to 0002
	INFO : rollback from 0002 to 0001
	[fred@macbookair online-migration]$ ./online-migration.py status
	Migration of schema world : 
	  +---------+---------------------+------------------+------------------------+
	  | VERSION | APPLIED             | STATUS           |                COMMENT |
	  +---------+---------------------+------------------+------------------------+
	  |    0000 | 2013-04-17 00:20:22 |               ok |           Initial file |
	  |    0001 | 2013-04-17 01:13:02 |               ok |                   none |
	  |    0002 | 2013-04-17 01:30:30 |         rollback |                   none |
	  |    0003 | 2013-04-17 01:30:29 |         rollback | add nice column to cit |
	  |    0002 |                none |          pending |                   none |
	  |    0003 |                none |          pending | add nice column to cit |
	  +---------+---------------------+------------------+------------------------+

Example of checksum error::

	mysql> alter table City modify CountryCode varchar(10);

	[fred@macbookair online-migration]$ ./online-migration.py status world
	Migration of schema world : 
	  +---------+---------------------+------------------+------------------------+
	  | VERSION | APPLIED             | STATUS           |                COMMENT |
	  +---------+---------------------+------------------+------------------------+
	  |    0000 | 2013-04-17 00:20:22 |               ok |           Initial file |
	  |    0001 | 2013-04-17 00:20:25 |               ok |                   none |
	  |    0002 | 2013-04-17 00:24:26 |               ok |                   none |
	  |    0003 | 2013-04-17 00:24:27 | checksum problem | add nice column to cit |
	  +---------+---------------------+------------------+------------------------+

Overview to the difference between the current schema and the expected schema::

	[fred@macbookair online-migration]$ ./online-migration.py diff world
	WARNING : Schema of world doesn't have expected checksum (4478d85870969436400bac023f2b2b7c)
	   TABLE `City` 
	-   `CountryCode` varchar(10) DEFAULT NULL,
	+   `CountryCode` char(3) NOT NULL DEFAULT '',


