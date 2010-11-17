import script

class Adapter:
    def __init__(self, prot, chan):
        self.prot = prot
        self.chan = chan
    def msg(self, user, message):
        print('%s: %s'%(user, message))
        self.reply('blaaa')
    def reply(self, message):
        self.prot.msg(self.chan, message)
