node percona1 {
	include percona::repository
	include percona::toolkit
	include online-migration

	Class['percona::repository'] -> Class['percona::server']

	class {
		'percona::server': 
			mysql_version 	=> "5.5",
			perconaserverid => "1",  
			enable		=> "true",
			ensure		=> "running"
	}

	mysql_schema { "world":
			ensure  => present,
			require => [ Package["online-migration"], Service['mysql'] ],
			version => 1,
			cwd     => "/root/om",
	}

}
