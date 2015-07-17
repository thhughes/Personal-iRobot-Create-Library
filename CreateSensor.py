#Create_Sensor



class CreateSensor():
    def __init__(self, packetID, nBytes, signed, groupList, message):
        self.packetID = packetID
        self.nBytes = nBytes
        self.signed = signed
        self.message = message
        self.groupList = groupList
        
    def getPacketID(self):
        return self.packetID

    def getNBytes(self):
        return self.nBytes

    def getSigned(self):
        return self.signed

    def isInGroup(self, group):
        return group in self.groupList

    def getGroupList(self):
        return self.groupList

    def getMessage(self):
        return self.message

    

    
