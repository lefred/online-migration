online-migration
================

This is a script to keep track of database schema. It helps to check and migrate to a new version of
the schema and rollback if necessary.

It uses pt-online-schema-change as backend (http://www.percona.com/doc/percona-toolkit/2.2/pt-online-schema-change.html)
and Oracle MySQL utilities (http://dev.mysql.com/doc/workbench/en/mysql-utilities.html).

Requirements:
-------------

* pt-online-schema-change 
* mysql-utilities (1.3.3)
* mysql-connector-python
* mysql client
* perl-DBI (dependency of pt-online-schema-change)
* perl-DBD-MySQL (dependency of pt-online-schema-chane)


Puppet:
-------

A new type (**mysql_schema**) and its provider as been added to the project

Extra:
------

Currently rollback the addition of foreign keys doesn't work because foreign keys are not copied with
mysqldbcopy see http://bugs.mysql.com/bug.php?id=63783

A bug in pt-online-schema-change fails the example with the world database, see https://bugs.launchpad.net/percona-toolkit/+bug/1207186



Copyrights:
-----------

GPLv2 all rights reserved to Frédéric Descamps <lefred@lefred.be>
