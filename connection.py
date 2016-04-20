import logging
import tornadio2.conn


class ClientConnection(tornadio2.conn.SocketConnection):
    clients = set()
    def on_open(self, *args, **kwargs):
        self.send("Welcome from the server.")
        self.clients.add(self)

    def on_close(self):
        logging.warning('client disconnected')
        self.clients.remove(self)
