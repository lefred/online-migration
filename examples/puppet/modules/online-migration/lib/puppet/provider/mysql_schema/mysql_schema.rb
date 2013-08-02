Puppet::Type.type(:mysql_schema).provide(:mysql_schema) do
   desc "Provides access to online-migration"

   optional_commands :omcmd => "/usr/local/bin/online-migration.py"

   def create
       info("performing the migration")
       dir = self.resource[:cwd] || Dir.pwd
       Dir.chdir(dir)

       last_version = omcmd "last_version", resource[:schema]
       last_version.chomp!
       if last_version == "None"
          omcmd "up", resource[:schema]
       	  last_version = omcmd "last_version", resource[:schema]
          last_version.chomp!
       end
       if last_version > resource[:version]
          omcmd "down", resource[:schema], "to", resource[:version]
       elsif last_version < resource[:version]	  
          omcmd "up", resource[:schema], "to", resource[:version]
       end
       return true
   end

   def destroy
       omcmd "last_version", resource[:schema]
       info("performing the destruction")
   end

   def exists?
       last_version = omcmd "last_version", resource[:schema]
       last_version.chomp!
       info("performing the check, last_version is #{last_version}")
       if last_version == "-1" 
          info("we need to initialize online-migration")
	  omcmd "init_sysdb"
	  return false
       elsif !( last_version == resource[:version] )
	  info("we need to migrate to another version (#{resource[:version]})")
	  return false
       else
	  return true
       end
   end

end
