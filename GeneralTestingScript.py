import Robot
import time
import os, sys
import Create
import CreateCommand
import CreateSensor
from create_dictionaries import createCommands
from create_dictionaries import createSensors

robot = Create.CreatePicker('C2',"COM11", 115200)
Robot.start(robot)


    
def BumpAndWheelDrop():
    while True:
        s = robot.getBumpAndWheelDrop()
        print s
        time.sleep(0.1)

def WallSensor():
    while True:
        s = robot.getWallSensor()
        print s
        time.sleep(0.3)

def CliffSensors():  # Digital return 
    while True:
        s = robot.getCliffSensors()
        print s
        time.sleep(0.1)
def CliffSensors_A():
    while True:
        s = robot.getSensorValue("Cliff Left Signal")
        print s
        time.sleep(0.3)
        


def getSensorValue(packetID="Wall"):
    while True:
        s = robot.getSensorValue(packetID)
        print s
        time.sleep(0.3)

def c():
    robot.DirectDrive(500,500)
    while True:
        s = int(robot.getSensorValue('Current'))
        print s
        time.sleep(0.3)
    
def ss():
    robot.stopRobot()
    
print "Starting"
#getSensorValue("Light Bump Left")
#CliffSensors()
#a = robot.getSensorValue("Group 0")


