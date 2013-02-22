This is a script to keep track of database schema. It helps to check and migrate to a new version of
the schema and rollback is necessary.

It uses pt-online-schema-change as backend (http://www.percona.com/doc/percona-toolkit/2.1/pt-online-schema-change.html)
and Oracle MySQL utilities (http://dev.mysql.com/doc/workbench/en/mysql-utilities.html).

Requirements:
-------------

* pt-online-schema-change (currently provided with the script)
* mysql-utilities 
* mysql-connector-python
* mysql client
* perl-DBI (dependency of pt-online-schema-change)
* perl-DBD-MySQL (dependency of pt-online-schema-chane)


