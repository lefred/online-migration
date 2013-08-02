class online-migration {

	package { 
		"mysql-utilities":
			ensure => present,
	}

	package {
		"online-migration":
		  	ensure   => installed,
			require  => [ Package['mysql-utilities'], Package['percona-toolkit'] ],
			provider => rpm,
			source   => '/vagrant/online-migration-0.2-1.noarch.rpm';
        }

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


}
