#CreateBase.py
#Only compatible with robot-2007-05-24-1746 and later
#Black Box Vars valid only for robot-2007-06-05-17XX and later? (black-box-defs.tl 1.15)

import serial
import sys
import struct
import time
import traceback

if sys.platform == 'win32': import pywintypes

from serial import SerialException

import SerialSocket

READ_ATTEMPT_TIMEOUT = 3


def int16(h,l):
    """Convert 2 bytes (previously ord()'d ) repersenting a 2's comp number into a python int."""
    num = chr(h) + chr(l)
    #'>h' passing in big endian format a signed short integer (2 bytes, high first)
    return struct.unpack('>h',num)[0]
    
def int8(b):
    """Convert 1 byte (previously ord()'d ) repersenting a 2's comp number into a python int."""
    num = chr(b)
    return struct.unpack('b',num)[0]

def two_comp16(to_convert):
    """Converts 16 bit numbers into their 2's complement equivelant number"""
   ## print bin(to_convert)
    if ((to_convert >> 15)& 1):
        return to_convert - (2**16)
    else:
        return to_convert
        
    
class CreateException(Exception):
    """
    Exception class for Create
    """
    pass
 

class CreateBase(object):
    """
    Create base class not to be instansiated on it's own.
    The method names should match the command names listed in the Create/OI
    documentation. These may differ slightly from what we use internally.
    """
    CreateStates = {"Off" : 0,
                "Passive" : 1,
                "Safe" : 2,
                "Full" : 3}
    
    def __init__(self, comPort = 'COM1', baudRate=57600, host=None, port=None, timeOut = 1, connect=True):
        self.bot_type = None
        self.comPort = comPort
        self.baudRate = baudRate
        self.timeOut = timeOut
        self.host = host
        self.port = port
        self.last_time = 0.0
        self.this_time = time.time
        self.s = False
        self.state = self.CreateStates["Off"]
        if connect:
            while not self.s:
                try:
                    if not self.host: self.s = serial.Serial(self.comPort, self.baudRate, timeout = self.timeOut)
                    if self.host: self.s = SerialSocket.SerialSocket(host=self.host,port=self.port,timeout=self.timeOut)
                    self.s.flushInput()
                    self.s.flushOutput()
                except SerialException:
                    raise
                    print "Could not open serial port. Fix connection, wait 10 seconds and press return."
                    sys.stdin.readline()
                    continue
            
        #Baud rate ditcionary
                self.bdict ={300    :   0,
                             600    :   1,
                             1200   :   2,
                             2400   :   3,
                             2400   :   4,
                             4800   :   5,
                             9600   :   6,
                             14400  :   7,
                             19200  :   8,
                             28800  :   9,
                             57600  :   10,
                             115200 :   11}

                self.specify()
                assert self.bot_type, "Can't instanciate Create base class."
                try:
                    self.sendStart()
                except:
                    print 'Closing serial connection'
                    self.s.close()
                    raise IOError("Failed to set OI to passive mode.")

    def close(self):
        self.sendStop()
        time.sleep(0.2)
        self.s.close()
        

        
    def throttle(function):
        """
        Decorator function to limit how fast you can poll the Create so as
        not to confuse robot.
        """
        
        def throttle_deco(self,*args,**kwargs):
            while (self.this_time() - self.last_time) <= self.minWaitTime:
                pass
            self.last_time = time.time()
            function(self,*args,**kwargs)
        return throttle_deco
        
    
    def flushCreate(self):
        if self.s:
            self.s.flushInput()
            self.s.flushOutput()

    @throttle
    def send(self,command,dataList = []):
        """Utility function for turning opcode and data into string to be sent."""
        #cmdStr = "%c"%command
        cmdStr = struct.pack('B',command)

        for byte in dataList: 
            #cmdStr += "%c"%byte
            #for signed bytes
            if byte < 0: 
                cmdStr += struct.pack('b',byte)
            #and unsigned bytes
            else:
                cmdStr += struct.pack('B',byte)

        self.s.write(cmdStr)
     
        
    def sendStart(self):
        """Send the start opcode to the robot."""
        self.send(128)
        self.s.flushInput()
        if (not self.verifyCreatePassiveMode()):
            self.sendStop()
            raise CreateException("Failed to set OI mode to passive.")
        
        self.state = self.CreateStates["Passive"]
       
        

    def sendStop(self):
        """Send the stop opcode to the robot."""
        self.send(173)
        self.s.flushInput()
        self.state = self.CreateStates["Passive"]
        time.sleep(0.2)

        self.s.write("\x01\x01\x01\x00")  #enables monit streaming 
        
    def sendBaud(self,baudRate):
        """Change the default baud rate."""
        if not self.bdict.has_key(baudRate):
            raise ValueError("The "+self.bot_type+" Create does not support baud rate "+str(baudRate))
        self.send(129,[self.bdict[baudRate]]) 
        
    def sendControl(self):
        self.send(130)
        self.state = self.CreateStates["Safe"]
        
    def sendSafe(self):
        """Send the Safe Mode opcode."""
        self.send(131)
        self.state = self.CreateStates["Safe"]
        
    def sendFull(self):
        """Send the Full Mode opcode."""
        self.send(132)
        self.state = self.CreateStates["Full"]
        
    def sendPower(self):
        """Send the Power Down opcode."""
        self.send(133)
        self.state = self.CreateStates["Passive"]
        
    def sendSpot(self):
        """Send the Spot Clean opcode."""
        self.send(134)
        self.state = self.CreateStates["Passive"]
        
    def sendClean(self):
        """Send the Clean cycle opcode."""
        self.send(135)
        self.state = self.CreateStates["Passive"]
        
    def sendMax(self):
        """Send the Max Cycle opcode."""
        self.send(136)
        self.state = self.CreateStates["Passive"]
    
    def sendOIMode(self):
        self.sendSensors

    def sendDrive(self,velocity,radius=0,driveStraight=False,revolveClockwise=False,revolveCC=False):
        """Provides control of the robot's drive wheels."""
        if velocity >500 or velocity <-500:
            raise ValueError("Bad velocity: "+str(velocity)+" mm/sec   ")
        if radius >2000 or radius <-2000:
            raise ValueError("Bad radius: "+str(radius)+" mm   ")
        if driveStraight and (revolveClockwise or revolveCC) or revolveClockwise and revolveCC:
            raise ValueError("Bad combination of turning flags")
        if driveStraight: radius = 0x8000
        elif revolveClockwise: radius = 0xFFFF
        elif revolveCC: radius = 1
        vh = (velocity & 0xFF00) >> 8
        vl = velocity & 0x00FF
        rh = (radius & 0xFF00) >> 8
        rl = radius & 0x00FF
        self.send(137,[vh,vl,rh,rl])

    def sendMotors(self,cmd):
        """Virtual Function"""
        raise Exception("Virtual function sendMotors needs to be overridden")

    def sendLEDs(self,cmd):
        """Virtual Function"""
        raise Exception("Virtual function sendLEDs needs to be overridden")

    def sendSong(self,number,notesList):
        """Send a new song to the robot."""
        self.send(140,[number, len(notesList)/2] + notesList)

    def sendPlay(self,number):
        """Tell the robot to play song x."""
        self.send(141,[number])
  
    def sendSensors(self,packetID=0):
        """Send the Get Sensors opcode and packet requested."""
        self.send(142,[packetID])
 
    def getSensors(self):
        """Utility function to actually get the sensors, do processing and error checking."""
        self.s.flushInput()
        self.s.flushOutput()
        try:
            out = self.acquirePacket()
            return self.processSensorPacket(out)
        except CreateException,e:
            raise CreateException(" Error getting robot sensors: %s"%str(e))

    def acquirePacket(self):
        """Virtual Function to get physically get the sensor packet."""
        raise Exception("Virtual Function. acquirePacket needs to be overridden.")

    def processSensorPacket(self,pack):
        """Virtual Function"""
        raise Exception("Virtual func. processSensorPacket needs to be overridden")

    def specify(self): #needs to be overridden
        """Virtual Function"""
        self.bot_type = ""
        #append values to baud dict here
        
    def hasStatusAndStop(self):
        """Allows for runtime determination of if robot can report status and stop code."""
        return False           

    def retry_read_wrapper(self,read_function,bytes,error_string,retries=2,sql_escape=False):
        
        """
        Wrapper to deal with capturing spurious serial data and to deal
        with retrying a sensor read request.
        read_function = <string>, bytes = <int>, error_string = <string>
        """
        data = ''
        attempt = 0
        done = False
        self.s.flushInput()
        self.s.flushOutput()
        
        while attempt <= retries:
            trytime = time.time()
            eval(read_function)
            
            attempt,data,done = self.serial_read_wait(bytes,attempt,trytime)
            if done:
                break
        self.check_data_attempts(attempt,retries,data,error_string)
        
        return data

    def check_data_attempts(self, attempt, retries, data, error_string):
        """
        Helper to abstract the data checking process
        attempt<int> -n'th time that the data is trying to be read
        retries<int> - total number of alotted attempts
        data<None or Encoded Bytes> - This data is information that is either None (in the case that something went wrong and no data was returned) or Encoded Bytes (in the case that actual data is returned)
        """
        if attempt > retries:
            raise CreateException("Robot has exceeded max read request retries: %s"%error_string)
        if data == None:
            raise CreateException("Error has occured in Serial_read_wait(...) causing data to evaluate to None")


    def serial_read_wait(self,bytes,attempt,trytime):
        """
        Helper to abstract the waiting process

        bytes<int> - Number of bytes that need to be read from the stream
        attempt<int> - number try to get the data
        trytime<int> - Time that the try started
        """
        done = False
        data = ''
        self.wait_for_data(trytime,bytes)
        
        if self.s.inWaiting() >= bytes: 
            data = self.s.read(bytes)
            done = True
        else:
            attempt += 1
            print "Retry serial attempt ",attempt
            
        return attempt,data,done
        
    def wait_for_data(self,trytime,bytes):
        """
        Helper that waits for a specific number of bytes to show up in the serial queue, or the time to required to run out. 

        trytime<int> - time that the try started
        bytes<int> - number of bytes that need to be in the queue

        """
        while ((time.time() - trytime) <= READ_ATTEMPT_TIMEOUT)  \
              and (self.s.inWaiting() < bytes):
            pass
        
    def retry_read_wrapper_socket(self,read_function,bytes,error_string,sql_escape=False,retries=6):
        """
        Wrapper to deal with capturing spurious serial data and to deal
        with retrying a sensor read request.
        read_function = <string>, bytes = <int>, error_string = <string>
        """
        attempt = 0
        self.s.flushInput()
        self.s.flushOutput()
        
        while attempt <= retries:  

            data = ''
            
            bytesleft = bytes
            eval(read_function)

            while (bytesleft > 0):
                try:
                    data += self.s.read(bytesleft)
                    bytesleft = bytes - len(data) 
                except Exception,e:
                    attempt += 1
                    print "Retry socket attempt %i,  exception: %s"%(attempt,e)
                    break             
                    
            if(bytesleft == 0): return data

       
        raise CreateException("Robot has exceeded max read request retries: %s"%error_string)
        

    def verifyCreatePassiveMode(self, timeout=3, retries=3, reqSuccess=2):
        # If it was already verified that the robot is in a Create Passive state
        if (self.state == self.CreateStates["Passive"]):
            return True
        packet = ''
        attempt = 0  # Only attempt to verify n times
        success = 0  # Require n successes prior to passing

        while attempt <= retries:
            try:
                packet = self.retry_read_wrapper('self.sendSensors(packetID=35)',1,'PassiveMode')
            except Exception,e :
                print e
                if (packet == '') or (packet == None):
                    attempt+=1
                    print "Verify passive mode attempt: %d" % attempt
                    print "Packet: " + (":".join("{:02x}".format(ord(c)) for c in packet))
                    continue
                else:
                    print e
                    pass
                
            
                # If in passive mode
            if (ord(packet) & 0x1):
                success += 1
                if (success >= reqSuccess):
                    return True
            else:  # If data incorrect
                print "Retry passive mode attempt: %d" % attempt
                print "Packet: " + (":".join("{:02x}".format(ord(c)) for c in packet))
                attempt += 1
        raise CreateException("Robot OI failed to set to passive")
