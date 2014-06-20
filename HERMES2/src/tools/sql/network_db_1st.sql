# call with mysql -u root -p <network_db_1st.sql
create user hermes@localhost identified by 'hermes_pass';
create database hermes;
grant all privileges on hermes.* to hermes@localhost;
