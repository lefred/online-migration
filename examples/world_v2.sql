alter table City 
   add PolutionLevel int;
alter table City add index pol_idx(PolutionLevel);
