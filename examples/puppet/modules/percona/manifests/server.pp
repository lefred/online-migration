class percona::server ($perconaserverid=undef,$mysql_version="5.5", $enable="false",$ensure="running") {
	include percona::server::packages
	include percona::server::config
	include percona::server::service

	Class['percona::server::packages'] ->  Class['percona::server::config'] -> Class['percona::server::service']	
}
