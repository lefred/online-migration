class percona::server::service {


	service {
		"mysql":
			enable  => $percona::server::enable,
                        ensure  => $percona::server::ensure,
			require => Package['MySQL-server'],
	}

}
