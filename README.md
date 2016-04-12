# GeoserverLogDaemon

TL;DR 
Sending access log to python daemon listening on unix socket file, parsing data and insert it  on database

#logTable.sql 
Contains the SQL to create a table in web_service schema that will contain the logs

#logDaemon.py
Python script that creates the socket, listens to it and sends content to database

#geoserver_logger
Bash script that creates the service

#Notes

I use a file, /etc/.netrc that keeps the login and password to the database, you need to create a file for your credencials.

Paths to location of log file, pid etc is located at the end of the script

The stript needs some improvment on the try/except

