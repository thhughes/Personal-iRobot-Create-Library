import os, sys
import Create
from CreateBase import CreateException

import time
#from SCI import SCI
#from SCI.SCIBase import SCIException

comPort = "COM18"
ledOff = 0
ledOn = -1
# Clean Led Colors
LedRed = 255
LedGreen = 0
LedOrange = 75

# Blink Types
blinkSingleStep = 0
blinkLong5 = 1


def start(robot):
    try:
        robot.sendStart()
        robot.sendFull()
        ## print 'Entered Full mode'
        
    except Exception,e:
        # Connection error
        if (robot):
            robot.sendSafe()
            robot.close()                    
            print "Failed to connect to robot board, Check power and connection"
        raise
    return

        
def end(robot):
    try:
        robot.sendSafe()
        time.sleep(0.2)
        robot.sendStop()
        time.sleep(0.2)
        robot.close()
        # Serial communication issue
    except Exception:
        print Exception
        # Make sure the serial port is closed
        robot.s.close()
        raise
    return


class Led:
    # To track number of blinks and how long it has delayed
    currentPeriodTime = 0
    currentNumBlinks = 0

    def __init__(self, name,period=ledOff,blinkCount=0,noBlinkDelay=0,blinkType=blinkSingleStep):
        self.name = name
        self.halfPeriod   = period/2.0
        self.blinkCount   = blinkCount
        self.noBlinkDelay = noBlinkDelay
        self.blinkType = blinkType
        self.ledOn = self.halfPeriod != ledOff

        return

    # Return true if led state changed, false otherwise
    def updateStatus(self, amount):
        self.currentPeriodTime += amount

        # Check if led status should change
        if (self.currentNumBlinks >= self.blinkCount) and (self.blinkCount > 0):
            ledStatus = self.ledOn
            self.ledOn = False
            if self.currentPeriodTime >= (self.noBlinkDelay +
                                          self.halfPeriod):
                self.currentNumBlinks = 0
                self.triggerLed()
            return ledStatus != self.ledOn
        elif self.currentPeriodTime >= self.determineBlinkType():
            self.triggerLed()
            return True
        return False

    def triggerLed(self):
        self.currentPeriodTime = 0
        # Increment the blink count on the falling edge of signal
        self.ledOn = not self.ledOn
        if not self.ledOn:
            self.decrementBlinkCount()
        return

    def determineBlinkType(self):
        if (((self.blinkCount - self.currentNumBlinks) >= 5)and 
            (self.blinkType == blinkLong5) and self.ledOn):
            return self.halfPeriod*4.0
        return self.halfPeriod


    def decrementBlinkCount(self):
        if self.blinkCount == 0:
            return
        if (self.blinkType == blinkLong5):
            if (self.blinkCount - self.currentNumBlinks) >= 5:
                self.currentNumBlinks += 5
            else:
                self.currentNumBlinks += 1
        elif self.blinkType == blinkSingleStep:
            self.currentNumBlinks += 1
        else:
            raise Exception('BlinkType', 'Invalid decrement value')
        return

    def isLedConstant(self):
        return self.halfPeriod <= 0
    
    # Returns a list containing if the led is on or off. Returns a list
    # so it can be extended into an existing list
    def getLedStatus(self):
        return [int(self.ledOn)]

    def updateParameter(self, parameter, value):
        if parameter == 'period':
            self.halfPeriod = value/2.0
        elif parameter == 'blinkCount':
            self.blinkCount = value
        elif parameter == 'noBlinkDelay':
            self.noBlinkDelay = value
        else:
            print "***Invalid parameter***"
            return False
        return True


class CleanLed(Led):
    maxIntensity = 250
    intensity = maxIntensity
    powerZoomDir = 1

    def __init__(self,name,period=ledOff,blinkCount=0,noBlinkDelay=0,
                 zoom=0,blinkType=blinkSingleStep,color=LedGreen):
        self.name = name
        self.halfPeriod   = period/2.0
        self.blinkCount   = blinkCount
        self.noBlinkDelay = noBlinkDelay
        self.ledOn = self.halfPeriod != ledOff
        self.zoom = zoom
        self.blinkType = blinkType
        self.color = color
        return

    def updateStatus(self, amount):
        if self.zoom:
            zoomAmount = 2*self.maxIntensity*amount/(self.halfPeriod*2)
            self.intensity += zoomAmount*self.powerZoomDir
            if (self.intensity > self.maxIntensity) or (self.intensity < 0):
                self.powerZoomDir -= 2*self.powerZoomDir
                self.intensity = max(min(self.intensity,255), 0)
            return True
        # Not zooming, update the time and led at max intensity
        changed = Led.updateStatus(self,amount)
        self.intensity = self.ledOn*self.maxIntensity
        return changed

    def getLedStatus(self):
        return [self.color, self.intensity]
