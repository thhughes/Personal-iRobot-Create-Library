#Create.py


from CreateBase import CreateBase
from CRE82 import CRE82



def CreatePicker(robotType,comPort,baudRate,host=None,port=None,timeOut=1):
    """ Class to help just in case there are different types of creates """ 
    return { "C2" : CRE82 }[robotType](comPort,baudRate)
