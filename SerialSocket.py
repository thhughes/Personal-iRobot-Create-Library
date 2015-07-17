#A module for making a socket look like a serial port - SerialSocket.py

#Chris Vogt
#cvogt@irobot.com

#Written in Python 2.5

import socket

from collections import deque
from time import localtime, strftime

class SerialSocketException(Exception):
    """
    Base exception class for SerialSocket
    """
    pass

class SocketNotOpenError(SerialSocketException):
    pass


class SerialSocket():
    """
    This class implements a subset of the standard functions offered by
    pySerial applied to python sockets.
    """

    def __init__(self,host=None,port=None,timeout=1):
        """
        Constructor: Opens socket and returns Serial socket object

        Properties:
        
        host (string)
            The AF_INET address of the host.

        port (int)
            Port on the host to connet to.


        Methods:

        read(n) -> string
        write(data) -> void
        flushInput() -> void
        flushOutput() -> void
        setBaudrate() -> void
        inWaiting() -> int
        close() -> void
        """

        self._isOpen = False

        self.host = host
        self.port = port
        self.timeout = float(3.0)
        

        print self.host
        print self.port
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket.settimeout(self.timeout)

        if (self.host!=None) and (self.port != None):
            self.open()


    def open(self):
        if (self.host==None) or (self.port == None): raise SerialSocketException("Host and port must be assigned before opening.")      
        try:
            self.socket.connect((self.host,self.port))
            self._isOpen = True
        except Exception,e:
            self._isOpen = False
            raise SerialSocketException("Error connecting socket to remote host: %s"%str(e))


    def close(self):
        """
        Close the socket connection. Delete buffers.
        """
        if self._isOpen:
            try:
                self.socket.close()
            except:
                pass

        self._isOpen = False


    def isOpen(self):
        """
        Return status of the 'port'.
        """
        return self._isOpen
    
        
    def read(self,bytes):
        """
        Read n-bytes from the socket.
        Return said bytes as a string.
        """
        if not self._isOpen: raise SocketNotOpenError
        
        print "number of bytes to read : ",bytes
        #print "at time : ",strftime("%a, %d %b %Y %X +0000", localtime()) 

        return self.socket.recv(bytes)

    
    def inWaiting(self):
        """
        Return the number of bytes waiting to be read
        from the recieve buffer.
        """
        raise "inWaiting is not implemented for wifi socket based communication"



    def write(self,data):
        """
        Write data out the socket.
        """
        if not self._isOpen: raise SocketNotOpenError

        self.socket.sendall(data)


    def flushInput(self,timeout=0.1):
        """
        Clear the input buffer.
        """
        if not self._isOpen: raise SocketNotOpenError

        self.socket.settimeout(timeout)
        while True:
            try:
                self.socket.recv(4096)
            except:
                self.socket.settimeout(3.0)
                break
        



    def flushOutput(self):
        """
        Clear the output buffer.
        No-Op.
        """
        if not self._isOpen: raise SocketNotOpenError


    def setBaudrate(self,x):
        """
        No-op on socket.
        """
        if not self._isOpen: raise SocketNotOpenError






        
        
