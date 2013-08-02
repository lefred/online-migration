class percona::server::packages {
   	
	if $percona::server::mysql_version == "5.5" {
                $ps_ver="55"
		$repo="percona"
        } elsif $percona::server::mysql_version == "5.6" {
		info("Congrats ! Using 5.6 !!")
                $ps_ver="56"
		$repo="percona-testing"
        }

	package {
		"Percona-Server-server-$ps_ver.$hardwaremodel":
            		alias => "MySQL-server",
            		require => Yumrepo[$repo],
			ensure => "installed";
		"Percona-Server-client-$ps_ver.$hardwaremodel":
            		alias => "MySQL-client",
            		require => Yumrepo[$repo],
			ensure => "installed";		
		"mysql-libs":
			ensure => "absent";		
		"Percona-Server-shared-compat":
			require => [ Yumrepo[$repo], Package['mysql-libs'], Package['MySQL-client'] ],
			ensure => "installed";
	}
}
