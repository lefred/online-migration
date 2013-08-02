Puppet::Type.newtype(:mysql_schema) do
    @doc = "Manage MySQL Schemas"
    ensurable do
      defaultvalues
      defaultto :present
    end


    newparam(:schema) do
        desc "the schema to manage"
	isnamevar
    end

    newparam(:version) do
	desc "the schema version to insall"
    end

    newparam(:cwd, :parent => Puppet::Parameter::Path) do
      desc "The directory from which to run the command.  If
        this directory does not exist, the command will fail."
    end

end
