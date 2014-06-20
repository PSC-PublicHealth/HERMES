# call with mysql -u root -p <network_db_reset.sql
#drop user hermes@localhost;
drop database hermes;
create database hermes;
grant all privileges on hermes.* to hermes@localhost;
