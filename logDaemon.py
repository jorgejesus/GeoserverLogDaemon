#!/usr/bin/env python 
#Log pip in Apache
#CustomLog "|$/bin/nc -uU /tmp/logDaemon.socket" vhost_combined
import sys,logging,time,os,socket
from daemons.prefab import run
import sqlite3
import apache_log_parser

class LogSocketDaemon(run.RunDaemon):
    
    def __init__(self,pidFile,socketFile,dbFile):
        super(LogSocketDaemon, self).__init__(pidfile=pidFile) 
        self.socketFile=socketFile
        self.dbFile=dbFile
        self.logger=logging.getLogger("LogSocketDaemon")
        self.logDBConn=None
        self.onlyLogGeoserver=False
        #it has to be the same as the Apache log
        self.parser=apache_log_parser.make_parser('%v:%p %h %l %u %t \"%r\" %>s %O \"%{Referer}i\" \"%{User-Agent}i\"')
        
        
    def parseLog(self,lineStr):  
        """Returns a dictionary with parsed content to be inserted into the database"""
        
        dicLine=self.parser(lineStr)
        returnTuple=(dicLine["server_name"]+":"+dicLine["server_port"],
                     dicLine['remote_host'],
                     dicLine['time_received'][1:-1],
                     dicLine['request_url'],
                     dicLine['request_header_user_agent'],
                     dicLine['status'],dicLine['bytes_tx'], )
        return returnTuple
    
    def getDBConnection(self):
        """Returns the DB cursor. If no database it created one """
        self.logger.info("Preparing DB")
        try:
            open(self.dbFile).close()
            workDB=sqlite3.connect(self.dbFile)
            self.logger.info("Using database at %s" % self.dbFile )
            return workDB   
        except IOError as e:
            self.logger.info("No database at %s" % self.dbFile )
            self.logger.info("Creating database at %s" % self.dbFile )
            workDB = sqlite3.connect(self.dbFile)
            workDB.execute('''CREATE TABLE geoserver_log(vhost text, ip text, date text, request text,agent text,status integer,bytes integer)''')
            workDB.commit()
            self.logger.info("Created database at %s" % self.dbFile )
            return workDB
            
    def run(self):
        self.logDBConn=self.getDBConnection()
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
                break
            else:
                if self.onlyLogGeoserver and datagram.find("geoserver")<0:
                    pass
                else:
                    self.logDBConn.execute('INSERT INTO geoserver_log VALUES(?,?,?,?,?,?,?)', self.parseLog(datagram))
                    self.logDBConn.commit()
    
            if "DONE" == datagram:
                break
            
if __name__ == '__main__':
    try:
        action = sys.argv[1]
    except:
        action = "start"
    
    logFile = "/tmp/logDaemon.log"
    pidFile = "/tmp/logDaemon.pid"
    socketFile = "/tmp/logDaemon.socket"
    dbFile = "/tmp/logDB.sqlite"

    logging.basicConfig(filename=logFile, level=logging.DEBUG,format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    d = LogSocketDaemon(pidFile=pidFile,socketFile=socketFile,dbFile=dbFile)

    if action == "start":

        d.start()

    elif action == "stop":

        d.stop()

    elif action == "restart":

        d.restart()
    
