from time import sleep


class BackdropHandler:

    def __init__(self, backdrop, scanner, iprange):
        self.backdrop = backdrop
        self.scanner = scanner
        self.iprange = iprange

    def start(self):
        while True:
            active = self.backdrop.getActive()
            print("Current Active cameras", active)
            tmp = self.scanner.scan(self.iprange)
            active_ip = [x[0] for x in active]
            for x in tmp:
                if x not in active_ip:
                    self.backdrop.add(x)
            sleep(60)
            self.backdrop.check_alive()
            self.backdrop.cleanup_cache()
            self.backdrop.offline_check()
            self.backdrop.ping_location()
            self.backdrop.cache()