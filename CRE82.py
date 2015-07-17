#CRE82.py

import binascii
import time
from create_dictionaries import createSensors
from create_dictionaries import createCommands
from collections import deque

from CreateBase import CreateBase,CreateException,int8,int16,two_comp16

READ_ATTEMPTS = 10000
#READ_ATTEMPT_TIMEOUT = 10 #10 second timeout
READ_ATTEMPT_TIMEOUT = 40  #Matching software timeout to hardware timeout. Attempting to cut down on dropped connections.
#READ_STAT_ATTEMPT_TIMEOUT = .05
#throw exception if robot fails to respond to this many consecutive sensor-read requests

class CRE82(CreateBase):
    """C2 Create/OI Class"""
    cdict = { 0 : 'Not Charging',
              1 : 'Reconditioning Charging',
              2 : 'Full Charging',
              3 : 'Trickle Charging',
              4 : 'Waiting',
              5 : 'Charging Fault'
              }

    cadict = { 0 : 'No Charger',
               1 : 'Internal Charger Present',
               2 : 'Home Base Present',
               3 : 'Internal Charger and Home Base Present'
               }

    oidict = { 0 : 'Off',
               1 : 'Passive',
               2 : 'Safe',
               3 : 'Full'
               }

    statusdict = { 0  : 'Off',
                   1  : 'Waiting',
                   2  : 'Starting',
                   3  : 'Running',
                   4  : 'Starting-Spotting',
                   5  : 'Spotting',
                   6  : 'Remote-Drive',
                   7  : 'Dead',
                   8  : 'Testing',
                   9  : 'Tutorial',
                   10 : 'Power-Saving',
                   11 : 'Turning-Off',
                   12 : 'Charging',
                   13 : 'Charging-Recovery',
                   14 : 'Charging-Trickle',
                   15 : 'Charging-Waiting',
                   16 : 'Charging-Error',
                   17 : 'Create'
                   }
        
    stopdict = { 0  : 'None',
                 1  : 'Wheel Drop Left',
                 2  : 'Main Brush Stall',
                 3  : 'Wheel Drop Right',
                 4  : 'Drive Stall Left',
                 5  : 'Drive Stall Right',
                 6  : 'Constant Cliff',
                 7  : 'Wheel Drop Rate',
                 8  : 'Stasis stuck',
                 9  : 'Constant Bump',
                 10 : 'No Bump',
                 11 : 'No Bump',
                 12 : 'Cliff Sensors Failed',
                 13 : 'Wheel Drop Both',
                 14 : 'Drive Stall Both'
                 }


    panicdict = { 0  : 'None',
                  1  : 'Main Brush Stall Low',
                  5  : 'Side Brush Stall Low',
                  6  : 'Wedge Escape Termination',
                  9  : 'Wheel Drop Rate Low',
                  10 : 'Wheel Drop Rate High',
                  11 : 'Constant Bump High',
                  12 : 'No Bump High',
                  13 : 'Stasis Stuck High',
                  14 : 'Average Bump Distance',
                  15 : 'No Drive'
                  }
    
    chargeabort = { 0  : 'None',
                    1  : 'Temberature Max',
                    2  : 'Voltage Max',
                    3  : 'Coulombs Max',
                    4  : 'Full Charge Timer Max',
                    5  : 'No Battery Error',
                    6  : 'Overcurrent Error',
                    7  : 'Fets Failed Error',
                    8  : 'No Current Error',
                    9  : 'Low Current Error',
                    10 : 'Overtemp Error',
                    11 : 'Not Cooling Error'
                    }     
    
    def __init__(self,comPort = 'COM1', baudRate=115200,host=None,port=None,timeOut = 1):
        CreateBase.__init__(self,comPort,baudRate,host,port,timeOut)
        streamed_data = []
        
        
    
    def specify(self):
        """Sets type label and loads model specific dictionaries into memory."""
        self.bot_type = "R3"
        #minimum time to wait between asking for Create data.
        self.minWaitTime = 0.015  
        
        self.cdict = CRE82.cdict
        self.cadict = CRE82.cadict
        self.oidict = CRE82.oidict
        self.statusdict = CRE82.statusdict
        self.stopdict = CRE82.stopdict
        self.panicdict = CRE82.panicdict
        self.chargeabort = CRE82.chargeabort


    def runCreateCommand(self, command, data=[]):
        """
        Wrapper for sending data with Create Commands
        """
        self.send(command,data)

    def sendCommand(self, command, data = []):
        """ Wrapper for sending Create commands through the CreateCommands dictionaries"""
        self.runCreateCommand(createCommands[command].opcode,data)

        
    def stopRobot(self):
        self.DirectDrive(0,0)

    def Drive(self, velocity, radius):
        if (velocity > 500) or (velocity < -500):
            raise ValueError("Bad Right Velocity: " + str(velocity) + "mm/s. -500 < V < 500.")
        if (radius > 2000) or (radius < -2000):
            raise ValueError("Bad Right Radius: " + str(radius) + "mm. -2000 < R < 2000.")

        vh = (velocity & 0xFF00) >> 8
        vl = (velocity & 0x00FF)
        rh = (radius & 0xFF00) >> 8
        rl = (radius & 0x00FF)

        self.sendCommand('Drive',[vh,vl,rh,rl])

    def DirectDrive(self,rightV,leftV):
        """Allows for direct 'tank conrtol' of Roomba's wheels."""
        if (rightV > 500) or (rightV < -500):
            raise ValueError("Bad Right Velocity: " + str(rightV) + "mm/s. -500 < V < 500.")
        if (leftV > 500) or (leftV < -500):
            raise ValueError("Bad Left Velocity: " + str(leftV) + "mm/s. -500 < V < 500.")
        rh = (rightV & 0xFF00) >> 8
        rl = rightV & 0x00FF
        lh = (leftV & 0xFF00) >> 8
        ll = leftV & 0x00FF
        self.sendCommand("Drive Wheels",[rh,rl,lh,ll])

    def DirectDrive_PWM(self,rightPWM,leftPWM):
        """Allows for direct PWM 'tank control' of Roomba's wheels."""
        if (rightPWM > 127) or (rightPWM < -127):
            raise ValueError("Bad Right PWM: " + str(rightV) + ". -127 < V < 127.")
        if (leftPWM > 500) or (leftPWM < -500):
            raise ValueError("Bad Left PWM: " + str(leftV) + ". -127 < V < 127.")
        rh = (rightPWM & 0xFF00) >> 8
        rl = rightPWM & 0x00FF
        lh = (leftPWM & 0xFF00) >> 8
        ll = leftPWM & 0x00FF
        self.sendCommand('Drive Pwm',[rh,rl,lh,ll])

        
    def sendMotors(self,mainBrushDir,sideBrushDir,mainBrushOn,vacuumOn,sideBrushOn):
        """Control direction of main and side brushes and on and off of
           main brush, side brush and vacuum."""
        motors = 0
        if mainBrushDir: motors |= 0x10
        if sideBrushDir: motors |= 0x8
        if mainBrushOn:  motors |= 0x4
        if vacuumOn:     motors |= 0x2
        if sideBrushOn:  motors |= 0x1
        self.send(138,[motors])


    def sendPWM(self,mainPWM,sidePWM,vacPWM):
        """Directly control the PWM of the main brush, side brush
           and the vacuum."""
        if (mainPWM > 127) or (mainPWM < -127):
            raise ValueError("Bad Main Brush PWM: " +str(mainPWM)+". -128 < PWM < 128")
        if (sidePWM > 127) or (sidePWM < -127):
            raise ValueError("Bad Side Brush PWM: " +str(sidePWM)+". -128 < PWM < 128")
        if (vacPWM > 127) or (vacPWM < 0):
            raise ValueError("Bad Vacuum PWM: " +str(vacPWM)+". 0 <= PWM < 128")
        self.send(144,[mainPWM,sidePWM,vacPWM])

    def stopBrushes(self):
        self.sendPWM(0,0,0)
        
        
    def sendLEDS(self,check=False,home=False,spot=False,debris=False,powerColor=0,powerInt=0):
        """Control the LEDs common to all the R3 models."""
        if (powerColor < 0) or (powerColor > 255):
            raise ValueError("Bad Power LED Color value:" +str(powerColor)+". 0 <= Color < 256")
        if (powerInt < 0) or (powerInt > 255):
            raise ValueError("Bad Power LED Intensity value:" +str(powerInt)+". 0 <= Intensity < 256")

        leds = 0
        if check:   leds |= 0x8
        if home:    leds |= 0x4
        if spot:    leds |= 0x2
        if debris:  leds |= 0x1

        self.send(139,[leds,powerColor,powerInt])

        
    def sendStream(self,numPackets,packetList=[]):
        """Start a data stream from the robot."""
        ## Bugged
        self.streamed_data = packetList
        
        packetList.insert(0,numPackets)
        self.sendCommand('Stream',packetList)
        
    def clearStream(self):
        ## Bugged
        self.s.flushInput()
        self.s.flushOutput()
        
    def sendQueryList(self,numPackets,packetList=[]):
        """Request a list of sensor packets."""
        pl = packetList
        pl.insert(0,numPackets)
        self.send(149,pl)

        
    def sendDoStream(self,run):
        """Pause the sensor packet stream or resume a paused stream."""
        ## Bugged
        if run: self.send(150,[1])
        if not run: self.send(150,[0])

        
    def forceSeekingDock(self):
        self.sendClean()
        time.sleep(1)
        self.sendDock()
 
        
    def sendDock(self):
        self.send(143)
        self.state = self.CreateStates["Passive"]

    def sendWaitTime(self,msec):
        """Wait for x tenths of seconds."""
        if (msec < 0) or (msec > 255):
            raise ValueError("Bad time value: " + str(msec) + ". 0 <= t =255")
        self.send(155,[msec])

        
    def sendWaitDist(self,dist):
        """Go x distance, ignore everything else"""
        if (dist < -32767) or (dist > 32768):
            raise ValueError("Bad distance value: " +str(dist) + ". -32768 < t < 32769")

        distH = (dist & 0xFF00) >> 8
        distL = dist & 0x00FF
        self.send(156,[distH,distL])

        
    def sendWaitAngle(self,angle):
        """Rotate x degrees, ignore everything else."""
        if (angle < -32767) or (angle > 32768):
            raise ValueError("Bad angle value: " +str(angle) + ". -32768 < t < 32769")

        angH = (angle & 0xFF00) >> 8
        angL = angle & 0x00FF
        self.send(157,[angH,angL])

        
    def sendWaitEvent(self,event):
        """Wait on event. See OI doc."""
        if not ((0 < event < 23) or (233 < event < 256)):
            raise ValueError("Bad event code: " + str(event)+ ". Valid events are 1-22, 234-255.")

        self.send(158,[event])

        
    def sendScheduleLEDS(self,sun=False,mon=False,tues=False,wed=False,thurs=False,fri=False,sat=False,next=False,
                         noschedule=False,weekdays=False,custom=False,setC=False,am=False,pm=False,colon=False):
        """Controls the Scheduling leds on Roomba 560 and 570"""
        weekLED = 0
        scheduleLED = 0
                           
        if sun:   weekLED |= 0x80
        if mon:   weekLED |= 0x40
        if tues:  weekLED |= 0x20
        if wed:   weekLED |= 0x10
        if thurs: weekLED |= 0x08
        if fri:   weekLED |= 0x04
        if sat:   weekLED |= 0x02
        if next:  weekLED |= 0x01

        if noschedule: scheduleLED |= 0x40
        if weekdays:   scheduleLED |= 0x20
        if custom:     scheduleLED |= 0x10
        if setC:       scheduleLED |= 0x08
        if am:         scheduleLED |= 0x04
        if pm:         scheduleLED |= 0x02
        if colon:      scheduleLED |= 0x01

        self.send(162,[weekLED,scheduleLED])

        
    def sendRawLEDS(self,digit3,digit2,digit1,digit0):
        """Allows raw control of the 7segment LEDs.
           See OI manual."""
        self.send(163,[digit3,digit2,digit1,digit0])

        
    def sendCharLEDS(self,digit3,digit2,digit1,digit0):
        """Send ascii characters to the 7segment LEDs.
           See OI manual."""
        self.send(164,[digit3,digit2,digit1,digit0])

        
    def sendButtons(self,clock=False,schedule=False,day=False,hour=False,minute=False,home=False,spot=False,clean=False):
        """Push Roomba's buttons."""
        btn = 0

        if clock:    btn |= 0x80
        if schedule: btn |= 0x40
        if day:      btn |= 0x20
        if hour:     btn |= 0x10
        if minute:   btn |= 0x08
        if home:     btn |= 0x04
        if spot:     btn |= 0x02
        if clean:    btn |= 0x01

        self.send(165,[btn])

        
    def sendSchedule(self,sun=False,mon=False,tues=False,wed=False,thurs=False,fri=False,sat=False,sunH=0,sunM=0,
                     monH=0,monM=0,tueH=0,tueM=0,wedH=0,wedM=0,thursH=0,thursM=0,friH=0,friM=0,satH=0,satM=0):
        """Send Roomba a new schedule. To disable send all 0.
           Valid hours: 0-23  Valid minutes: 0-59"""

        if not (0 <= sunH <=23):
            raise ValueError("Bad Sunday Hour Value: " +str(sunH)+". 0 <= hour <= 23")
        if not (0 <= sunM <= 59):
            raise ValueError("Bad Sunday Minute Value: " +str(sunM)+". 0 <= minute <= 59")
        if not (0 <= monH <=23):
            raise ValueError("Bad Monday Hour Value: " +str(monH)+". 0 <= hour <= 23")
        if not (0 <= monM <= 59):
            raise ValueError("Bad Monday Minute Value: " +str(monM)+". 0 <= minute <= 59")
        if not (0 <= tueH <=23):
            raise ValueError("Bad Tuesday Hour Value: " +str(tueH)+". 0 <= hour <= 23")
        if not (0 <= tueM <= 59):
            raise ValueError("Bad Tuesday Minute Value: " +str(tueM)+". 0 <= minute <= 59")
        if not (0 <= wedH <=23):
            raise ValueError("Bad Wednesday Hour Value: " +str(wedH)+". 0 <= hour <= 23")
        if not (0 <= wedM <= 59):
            raise ValueError("Bad Wednesday Minute Value: " +str(wedM)+". 0 <= minute <= 59")
        if not (0 <= thursH <=23):
            raise ValueError("Bad Thursday Hour Value: " +str(thursH)+". 0 <= hour <= 23")
        if not (0 <= thursM <= 59):
            raise ValueError("Bad Thrusday Minute Value: " +str(thursM)+". 0 <= minute <= 59")
        if not (0 <= friH <=23):
            raise ValueError("Bad Friday Hour Value: " +str(friH)+". 0 <= hour <= 23")
        if not (0 <= friM <= 59):
            raise ValueError("Bad Friday Minute Value: " +str(friM)+". 0 <= minute <= 59")
        if not (0 <= satH <=23):
            raise ValueError("Bad Saturday Hour Value: " +str(satH)+". 0 <= hour <= 23")
        if not (0 <= satM <= 59):
            raise ValueError("Bad Saturday Minute Value: " +str(satM)+". 0 <= minute <= 59")
        
        days = 0

        if sat:   days |= 0x40
        if fri:   days |= 0x20
        if thurs: days |= 0x10
        if wed:   days |= 0x08
        if tues:  days |= 0x04
        if mon:   days |= 0x02
        if sun:   days |= 0x01

        self.send(167,[days,sunH,sunM,monH,monM,tueH,tueM,wedH,wedM,thursH,thursM,friH,friM,satH,satM])

        
    def sendSetTime(self,day,hour,minute):
        """Set Roomba's day and time. Day: 0(Sunday) - 6(Saturday)
           Hour: 0-23  Minute:0-59"""
        if not (0 <= day <= 6):
            raise ValueError("Bad Day Value: " + str(day)+". 0 <= day <=6")
        if not (0 <= hour <=23):
            raise ValueError("Bad Hour Value: " +str(hour)+". 0 <= hour <= 23")
        if not (0 <= minute <= 59):
            raise ValueError("Bad Minute Value: " +str(minute)+". 0 <= minute <= 59")
        
        self.send(168,[day,hour,minute])


    def readStream(self,sets_of_data,error_string,retries=3):
        """
        Wrapper to deal with capturing spurious serial data and to deal
        with retrying a sensor read request.
        read_function = <string>, bytes = <int>, error_string = <string>
        """
        stream_return = []
        stream_length = self.flush_for_start()
        one_byte = 1
        
        for i in range(0,sets_of_data):
            data = ''
            attempt = 0
            trytime = time.time()
            
            while attempt <= retries:                         
                attempt,data,done = self.serial_read_wait(stream_length,attempt,trytime)
                if done:
                    break
            self.check_data_attempts(attempt,retries,data,error_string)
            mapped_data = map(ord,list(data))
            #print (mapped_data)
            stream_return.append(self.unpackStream(mapped_data))
            
            stream_length = self.check_continue_stream()
            
        #print stream_return
        return stream_return

    def unpackStream(self,single_stream):
        """ Unpacks stream into getSensorValue() Return values """
        unpacked_stream = []
        q = deque(single_stream)
        while len(q)>1:
            pack_id = q.popleft()
            pack_name = self.getPacketName(pack_id)
            pack_data = []
            for j in range(0,createSensors[pack_name].nBytes):
                pack_data.append(q.popleft())
            
            
            unpacked_stream.append(pack_name)
            unpacked_stream.append(self.parseSensorValue(pack_data,pack_name))
        return unpacked_stream
            
    def getPacketName(self,pack_id):
        for sensor in createSensors.iterkeys():
            if createSensors[sensor].packetID == pack_id:
		return sensor

        
    def check_continue_stream(self,retries=3):
        self.wait_for_data(time.time(),2)
        attempt = 0
        trytime = time.time()
        
        while attempt <= retries:                         
            attempt,data,done = self.serial_read_wait(2,attempt,trytime)
            if done:
                break
        try:
            self.check_data_attempts(attempt,retries,data,'Continuing Stream Data')
            r_data = map(ord,list(data))
            if r_data[0]!=19:
                raise CreateException("First packet after Stream data is not a correct headder")
            return r_data[1]+1 # Should return the stream size of the next stream input
            
        except CreateException,e:
            print e
            print "Failed in 'check_continue_stream'"
            raise e
        
        
    def find_stream_start(self,headder=19):
        """ Finds the start of the stream denoted by the headder"""
        done = False
        bytes_needed = 2 ## This will get the start byte, and the number of bytes
        attempt =0
        trytime = time.time()
        while not done:
            attempt,pack,done = self.serial_read_wait(bytes_needed,attempt,trytime)
            data = map(ord,list(pack))
            
            if data[0] == headder:
               #print 'Found the start'
                done = True
            else:
                done = False
            if attempt> 10:
                raise CreateException("Erroring out for taking too long")
        return (data[1]+1)  # Return the number of bytes needed, plus the checksum
            

    def flush_for_start(self):
        """ Finds the front of the stream"""
        
        self.s.flushInput()
        self.s.flushOutput()
        done = False
        bytes_needed = 1
        attempts = 0
        trytime = time.time()
        return self.find_stream_start()
    
    def check_streaming(self,retries=1):
        """ Checks if there is Serial data being communicated back and forth """
        """ USUALLY, the robot will not transmit more data when not in stream and
        when stationary. However, the code works to catch a large majority of non-ideal
        cases. Note: this could pass when there is nothing for it to pass on.  
 """

        #Provides a floor for the number of retries
        if retries<=1:
            retries = 3
        bytes_needed = 1
        num_passes = 0
        for i in range(0,retries):
            self.s.flushInput()
            self.s.flushOutput()
            
            print 'Checking for data... '+str((i+1))
            trytime = time.time()
            self.wait_for_data(trytime,bytes_needed)
            
            if self.s.inWaiting() >= bytes_needed:
                num_passes +=1
            if retries <= 3:
                if num_passes >=2:
                    return False
            else: #If system is going to fail, it should fail more often than it passes.
                if num_passes >= (2+(retries/2)):
                    return False
                
            
        return True
    
    def getAngle(self):
        """
        Get just the angle sensor packet.
        """
        pack = self.retry_read_wrapper('self.sendSensors(packetID=20)',
                                             2,'Angle Sensors')
        data = map(ord,list(pack))
        sensors = (data[0]<<8)| data[1]
        return sensors


    def getDistance(self):
        """
        Get just the angle sensor packet.
        """
        pack = self.retry_read_wrapper('self.sendSensors(packetID=19)',
                                             2,'Angle Sensors')
        data = map(ord,list(pack))
        sensors = (data[0]<<8)| data[1]
        return sensors

    def getCliffSensors(self):
        """
        Returns dictionary of the Cliff Sensors sorted by sensor name
        """
        pack = self.retry_read_wrapper('self.sendSensors(packetID=1)',
                                       10, 'Cliff Sensor Packet')

        #Differentiate between a bad sensor packet and no sensor packet.
        #print len(packet)
        if len(pack) != 10:
            return CreateException("Bad packet returned.") 
        if len(pack) == 0:
            raise CreateException("No sensor packet returned.")
            
        packet = map(ord,list(pack))

        sensors = { "Cliff Left" : bool(packet[2]),
                    "Cliff Front Left" : bool(packet[3]),
                    "Cliff Front Right": bool(packet[4]),
                    "Cliff Right": bool(packet[5])}
        return sensors


    def getWallSensor(self):

        pack = self.retry_read_wrapper('self.sendSensors(packetID=8)',1,'Wall Sensor')

        packet = map(ord,list(pack))

        return packet

    def getChargingState(self):
        pack = self.retry_read_wrapper('self.sendSensors(packetID=21)',1,'Charging State')
        packet = map(ord,list(pack))

        return packet


    def getSensorValue(self, sensorName):
        # Create send string from the Query command and the ID of the passed sensor
        sendString = "self.send(%i, [%i])" %(int(createCommands["Query"].getOpcode()),
                                                  int(createSensors[sensorName].packetID))
        # Query the robot for the data, store in pack
        pack = self.retry_read_wrapper(sendString, createSensors[sensorName].nBytes, sensorName)
        data = map(ord,list(pack))
        return self.parseSensorValue(data, sensorName)

    def parseSensorValue(self, data, sensorName):
        # Handle different sized sensor requests
        if createSensors[sensorName].getNBytes() == 1:
            sensor = data[0]
        elif createSensors[sensorName].getNBytes() == 2:
            sensor = (data[0]<<8)| data[1]
        else:
            # Not fast, but will have to do for now
            sensor = self.unpackGroup(data, createSensors[sensorName])

        bitwise_unpacked = self._bitwiseSensorUnpack(sensor, int(createSensors[sensorName].packetID))
        signed_value = self._signedSensorUnpack(bitwise_unpacked,sensorName)
        return signed_value

    def _signedSensorUnpack(self, bitwise_unpacked, sensorName):
        if (createSensors[sensorName].getSigned()):
            return two_comp16(bitwise_unpacked)
        else: ## Value does not need to be signed. 
            return bitwise_unpacked

    def _bitwiseSensorUnpack(self, sensor, packetID):
        """
        *helper*
        checks for packetID's that return bitwise digital data
        and unpackages that data for use. 

        returns booleans of unpackaged data, or the original passed data (if no packageID match)
        """
        
        if packetID == createSensors["Bumps Wheeldrops"].packetID:
            return self._bitwiseBumpWalldrops(sensor)
        elif packetID == createSensors["Buttons"].packetID:
            return self._bitwiseButtons(sensor)
        elif packetID == createSensors["Charger Available"].packetID:
            return self._bitwiseChargerAvailable(sensor)
        elif packetID == createSensors["Light Bumper"].packetID:
            return self._bitwiseLightBumper(sensor)
        elif packetID == createSensors["Overcurrents"].packetID:
            return self._bitwiseOvercurrent(sensor)
        else:
            return sensor
        
    def _bitwiseOvercurrent(self,sensor):
        """
        *helper*
        Returns dictionary of the overcurrent sensors sorted by name
        """
        
        sensors = { "Side Brush" : bool(sensor & 1),
                    "Main Brush"  : bool(sensor & 4),
                    "Right Wheel" : bool(sensor & 8),
                    "Left Wheel" : bool(sensor & 16)
                    }
        return sensors
    
    def _bitwiseBumpWalldrops(self, sensor):
        """
        *helper*
        Returns dictionary of the Bump and Wheel drop sensors sorted by name
        """
        
        sensors = { "Right Bump" : bool(sensor & 1),
                    "Left Bump"  : bool(sensor & 2),
                    "Right Wheel Drop" : bool(sensor & 4),
                    "Left Wheel Drop" : bool(sensor & 8)
                    }
        return sensors

    def _bitwiseButtons(self, sensor):
        """
        Returns dictionary of the button values sorted by name
        """

        sensors = { "Clean" : bool(sensor & 0x01),
                    "Spot"  : bool(sensor & 0x02),
                    "Dock"  : bool(sensor & 0x04),
                    "Minute": bool(sensor & 0x08),
                    "Hour"  : bool(sensor & 0x10),
                    "Day"   : bool(sensor & 0x20),
                    "Schedule": bool(sensor & 0x40),
                    "Clock" : bool(sensor & 0x80)
        }
        
        return sensors


    def _bitwiseChargerAvailable(self, sensor):
        """
        *helper*
        Returns dictionary of the charging state sorted by name
        """

        sensors = { "Internal Charger" : bool(sensor & 0x01),
                    "Home Base"        : bool(sensor & 0x02)
        }

        return sensor

    def _bitwiseLightBumper(self, sensor):
        """
        *helper*
        returns dictionary of the light bumper detection as digital response
        """

        sensors = {"Light Bumper Left" : bool(sensor & 0x01),
                   "Light Bumper Front Left" : bool(sensor & 0x02),
                   "Light Bupmer Center Left" : bool(sensor & 0x04),
                   "Light Bumper Center Right": bool(sensor & 0x08),
                   "Light Bumper Front Right" : bool(sensor & 0x10),
                   "Light Bupmer Right" : bool(sensor & 0x20)
                   }

        return sensors
        
    def unpackGroup(self, data, group):
        min = group.getGroupList()[0]
        max = group.getGroupList()[1]
        unpackedData = {}
        dIndex = 0

        # Must do this in order, since collected data is in this order
        for i in range(min, max+1):
            packetFound = False
            # Find corresponding packet
            for key in createSensors:
                if createSensors[key].getPacketID() == i:
                    if createSensors[key].getNBytes() == 2:
                        unparsedData = [data[dIndex], data[dIndex+1]]
                        dIndex += 2
                    else:
                        unparsedData = [data[dIndex]]
                        dIndex += 1
                    parsedData = self.parseSensorValue(unparsedData, key)
                    unpackedData.update({key:parsedData})
                    packetFound = True
                    break
            if not packetFound:
                raise IndexError("Could not unpack group. Sensor not found")
        return unpackedData
                                  
                                  
    
    def getSensors(self):
        """
        Get just the standard sensor packets.
        """
        pack,other = self.retry_read_wrapper('self.sendSensors(packetID=100)',
                                             80,'Sensors')
        sensors = self.processSensorPacket(pack)
        return sensors


    def getPackage(self):
        """Utility function to get the sensors, status and stop
           all at the same time in one serial call."""
        pack,other = self.retry_read_wrapper('self.sendQueryList(3,packetList=[100,128,129])',
                                82,'Package')
        sensors = self.processSensorPacket(pack[:80])

        #Do some bounds checking to avoid exceptrions from lying robots.
        sp = ord(pack[80])
        if not (sp >= 0 and sp <= 17):
            status = 'Invalid Status code %s' %sp
        else:
            status = self.statusdict[sp]

        st = ord(pack[81])
        if not (st >= 0 and st <= 12):
            stop = 'Invalid Stop code %s' %st
        else:
            stop = self.stopdict[st]
        
        return sensors,status,stop


    def processSensorPacket(self,packet):
        """Takes in raw binary sensor data and returns a dictionary
           of sensor values."""
        #Differentiate between a bad sensor packet and no sensor packet.
        #print len(packet)
        if len(packet) != 80:
            return False
        if len(packet) == 0:
            raise CreateException("No sensor packet returned.")
            
        packet = map(ord,list(packet))

        #Do some bounds checking to avoid exceptions from lying robots.
        if not (packet[16] >= 0 and packet[16] <= 5):
            cs = 'Invalid Charging State code %s' %packet[16]
        else:
            cs = self.cdict[packet[16]]
        if not (packet[39] >= 0 and packet[39] <= 3):
            ca = 'Invalid charger availible code %s' %packet[39]
        else:
            ca = self.cadict[packet[39]]
        if not (packet[40] >= 0 and packet[40] <= 3):
            oi = 'Invalid OI code %s' %packet[40]
        else:
            oi = self.oidict[packet[40]]
        
        ret =  {
            'Bump Left'                 :   bool(packet[0]&0x02), 
            'Bump Right'                :   bool(packet[0]&0x01), 
            'Left Wheeldrop'            :   bool(packet[0]&0x08),
            'Right Wheeldrop'           :   bool(packet[0]&0x04), 
            'Wall'                      :   bool(packet[1]),
            'Cliff Left'                :   bool(packet[2]),
            'Cliff Front Left'          :   bool(packet[3]),
            'Cliff Front Right'         :   bool(packet[4]),
            'Cliff Right'               :   bool(packet[5]),
            'Virtual Wall'              :   bool(packet[6]),
            'Side Brush Overcurrent'    :   bool(packet[7]&0x01),
            'Main Brush Overcurrent'    :   bool(packet[7]&0x04),
            'Drive Right Overcurrent'   :   bool(packet[7]&0x08),
            'Drive Left Overcurrent'    :   bool(packet[7]&0x16),
            'Dirt Detector Left'        :   packet[8],
            'Unused1'                   :   packet[9],
            'Remote Control Opcode'     :   packet[10],
            'Clean Button'              :   bool(packet[11]&0x01),
            'Spot Button'               :   bool(packet[11]&0x02),
            'Home Button'               :   bool(packet[11]&0x04),
            'Minute Button'             :   bool(packet[11]&0x08),
            'Hour Button'               :   bool(packet[11]&0x10),
            'Day Button'                :   bool(packet[11]&0x20),
            'Schedule Button'           :   bool(packet[11]&0x40),
            'Clock Button'              :   bool(packet[11]&0x80),
            'Distance'                  :   int16(packet[12],packet[13]),
            'Angle'                     :   int16(packet[14],packet[15]),
            'Charging State'            :   cs,
            'Voltage'                   :   (packet[17]<<8)|packet[18],
            'Current'                   :   int16(packet[19],packet[20]),
            'Temperature'               :   int8(packet[21]),
            'Charge'                    :   (packet[22]<<8)|packet[23],
            'Capacity'                  :   (packet[24]<<8)|packet[25],
            'Wall Signal'               :   (packet[26]<<8)|packet[27],
            'Cliff Left Signal'         :   (packet[28]<<8)|packet[29],
            'Cliff Front Left Signal'   :   (packet[30]<<8)|packet[31],
            'Cliff Front Right Signal'  :   (packet[32]<<8)|packet[33],
            'Cliff Right Signal'        :   (packet[34]<<8)|packet[35],
            'Unused2'                   :   packet[36],
            'Unused3'                   :   (packet[37]<<8)|packet[38],
            'Charger Available'         :   ca,
            'Open Interface Mode'       :   oi,
            'Song Number'               :   packet[41],   
            'Song Playing'              :   bool(packet[42]),
            'Stream Number Of Packets'  :   packet[43],
            'Velocity'                  :   int16(packet[44],packet[45]),
            'Radius'                    :   int16(packet[46],packet[47]),
            'Velocity Right'            :   int16(packet[48],packet[49]),
            'Velocity Left'             :   int16(packet[50],packet[51]),
            'Encoder Counts Left'       :   (packet[52]<<8)|packet[53],
            'Encoder Counts Right'      :   (packet[54]<<8)|packet[55],
            'LightBump Left'            :   bool(packet[56]&0x01),
            'LightBump Front Left'      :   bool(packet[56]&0x02),
            'LightBump Center Left'     :   bool(packet[56]&0x04),
            'LightBump Center Right'    :   bool(packet[56]&0x08),
            'LightBump Front Right'     :   bool(packet[56]&0x10),
            'LightBump Right'           :   bool(packet[56]&0x20),          
            'LightBump Left Level'      :   (packet[57]<<8)|packet[58],
            'LightBump Front Left Level':   (packet[59]<<8)|packet[60],
            'LightBump Center Left Level':  (packet[61]<<8)|packet[62],
            'LightBump Center Right Level': (packet[63]<<8)|packet[64],
            'LightBump Front Right Level':  (packet[65]<<8)|packet[66],
            'LightBump Right Level'     :   (packet[67]<<8)|packet[68],
            'IR Opcode Left'            :   packet[69],
            'IR Opcode Right'           :   packet[70],
            'Right Motor Current'       :   (packet[71]<<8)|packet[72],
            'Left Motor Current'        :   (packet[73]<<8)|packet[74],
            'Main Brush Current'        :   (packet[75]<<8)|packet[76],
            'Side Brush Current'        :   (packet[77]<<8)|packet[78],
            'Stasis'                    :   bool(packet[79]&0x01),
            'Stasis Disabled'           :   bool(packet[79]&0x02)
            }

        return ret
    
