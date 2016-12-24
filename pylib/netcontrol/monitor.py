from wakeonlan import wol

class MachineMonitor:

    def __init__(self, name, *, mac, ip, **kwargs):
        self.name = name
        self.mac = mac
        self.ip = ip

    def wakeup(self):
        wol.send_magic_packet(self.mac);

    def shutdown(self):
        pass
