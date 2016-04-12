##!/usr/bin/env python
# -*- coding: UTF-8 -*-

#DOCS:
#http://daemons.readthedocs.org/en/latest/
#http://www.gavinj.net/2012/06/building-python-daemon-process.html

import sys,logging,time,datetime,os,socket
from daemons.prefab import run
import psycopg2
import apache_log_parser
import netrc

class LogSocketDaemon(run.RunDaemon):
    
    def __init__(self,pidFile,socketFile,netrcFile):
        super(LogSocketDaemon, self).__init__(pidfile=pidFile) 
        self.socketFile=socketFile
        self.logger=logging.getLogger("LogSocketDaemon")
        self.logDBConn=None
        self.netrc=netrc.netrc(netrcFile)
        self.onlyLogGeoserver=True
        #it has to be the same as the Apache log
        self.parser=apache_log_parser.make_parser('%v:%p %a %l %u %t \"%r\" %>s %O \"%{Referer}i\" \"%{User-Agent}i\"')
        self.parserAlternative=apache_log_parser.make_parser('%v:%p %a %l %u %t \"%r\" %>s %O')
        
    def parseLog(self,lineStr):  
        """Returns a dictionary with parsed content to be inserted into the database"""
        #Default tuple with no content in case of error
	returnTuple=("-","0.0.0.0",datetime.datetime.now(),"-","-",0,0, )
	try:
                dicLine=self.parser(lineStr)
                
                returnTuple=(dicLine["server_name"]+":"+dicLine["server_port"],
                         	dicLine['remote_ip'],
                         	dicLine['time_received_tz_datetimeobj'],
                         	dicLine['request_url'],
                         	dicLine['request_header_user_agent'],
                         	dicLine['status'],dicLine['bytes_tx'], )
               	
        except apache_log_parser.LineDoesntMatchException:
                try:
                    dicLine = self.parserAlternative(lineStr)
                    returnTuple=(dicLine["server_name"]+":"+dicLine["server_port"],
                                 dicLine['remote_ip'],
                                 dicLine['time_received_tz_datetimeobj'],
                                 dicLine['request_url'],
                                 '',
                                 dicLine['status'],'', )
        	except:
                    self.logger.debug("Problems parsing request below")
                    self.logger.debug(lineStr)
              
        
	except Exception:
		self.logger.debug("Generic exception from request below")
                self.logger.debug(lineStr)
            
        return returnTuple

    
    def getDBConnection(self):
        """Returns the DB cursor. If no database it created one """
        self.logger.info("Connecting to DB")
        try:
            #SET THE DUMMY / FOO AS NECESSARY
            connStr = "host='DUMMY' dbname='FOOO' user='%s' password='%s'" % (self.netrc.authenticators('DUMMY')[0],self.netrc.authenticators('DUMMY')[2])
            conn = psycopg2.connect(connStr)
            self.logger.info("Connected to log database")
            return conn   
        except Exception as e:
            self.logger.debug("Could not connect to data" )
            self.logger.debug("Closing down daemon")
            self.logger.debug(str(e))
            self.stop()
            sys.exit(1) 
        
            
    def run(self):
        self.logDBConn=self.getDBConnection()
        cur=self.logDBConn.cursor()
        self.logger.info("Starting run loop")
       
        if os.path.exists(self.socketFile):
                os.remove(self.socketFile)
        self.logger.info("Opening socket...")
        server = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
        server.bind(self.socketFile)
        self.logger.info("Listening to socket: %s" % self.socketFile)
        
        while True:
            time.sleep(0.2) 
            datagram = server.recv( 1024 )
            if not datagram:
		self.logger.debug("No datagram calling break")
                break
            else:
                if self.onlyLogGeoserver and datagram.find("geoserver")<0:
                    pass
                else:
                    intoDB=self.parseLog(datagram)   
         
		    try:
                    	cur.execute('INSERT INTO web_services.geoserver_log VALUES(%s,%s,%s,%s,%s,%s,%s)', intoDB)
                    	self.logDBConn.commit()
		    except Exception as e:
		        self.logger.debug("Problems inserting in DB")
 			self.logger.debug(str(e))
			self.logger.debug(str(intoDB))
			self.logDBConn.commit()
            
if __name__ == '__main__':
    try:
        action = sys.argv[1]
    except:
        action = "start"
    
    logFile = "/var/log/logDaemon.log"
    pidFile = "/var/run/logDaemon.pid"
    socketFile = "/tmp/logDaemon.socket"
    netrcFile = "/etc/.netrc"

    logging.basicConfig(filename=logFile, level=logging.DEBUG,format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    d = LogSocketDaemon(pidFile=pidFile,socketFile=socketFile, netrcFile=netrcFile)

    if action == "start":

        d.start()

    elif action == "stop":

        d.stop()

    elif action == "restart":

        d.restart()
    
