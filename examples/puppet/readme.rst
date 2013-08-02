Automate schema version in puppet
=================================

It's possible to automate the installation of MySQL (or Percona Server or MariaDB ;-) ) but
I wanted to also automate the schema installation or migration with Puppet.

This is how it works:

On your node you make sure you have all the needed packages installed (seen manifests/site.pp) and
for the schema, this is what it's needed::

        include online-migration

        mysql_schema { "world":
                        ensure  => present,
                        require => [ Package["online-migration"], Service['mysql'] ],
                        version => 1,
                        cwd     => "/root/om",
        }


The name of the resource ("world") is the name of the schema (database) and the migration files
are located in */root/om*

*/root/om* contains the *world* folder with all definitions for each available version, this is how it's defined in puppet::

        file {
                "/root/om/":
                        owner   => root,
                        ensure  => directory;
                "/root/om/world/":
                        owner   => root,
                        require => File["/root/om/"],
                        source => "puppet:///modules/online-migration/world/",
                        ensure  => directory,
                        recurse => true;
        }

There are some message when the type **mysql_schema** is used, this is an example of puppet execution::

        info: Mysql_schema[world](provider=mysql_schema): performing the check, last_version is None
        info: Mysql_schema[world](provider=mysql_schema): we need to migrate to another version (1)
        info: Mysql_schema[world](provider=mysql_schema): performing the migration
        notice: /Stage[main]//Node[percona1]/Mysql_schema[world]/ensure: created


