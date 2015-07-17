#Create_command



class CreateCommand():
    def __init__(self, Opcode, Byte_sent=0, Byte_received=0, Message=''):
        self.opcode = Opcode
        self.byte_sent = Byte_sent
        self.byte_received = Byte_received
        self.message = Message


    def getOpcode(self):
        return self.opcode

    def getByte_sent(self):
        return self.byte_sent

    def getByte_received(self):
        return self.byte_received

    def getMessgae(self):
        return self.Message

    def checkCommandData(self):
        if self.byte_sent is 0 and self.byte_received is 0:
            return True
        return False



    
