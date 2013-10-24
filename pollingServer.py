import select
import socket
import sys
from configuration import Configuration
from clientConnection import ClientConnection


'''
Polling Server
'''


class Server:
    '''
    *** initializer ***
    '''
    def __init__(self, port):
        # load the configuration file
        self.config = Configuration('web.conf')

        self.host = ""
        self.port = port

        # open the socket
        self.open_socket()

        # prepare the dictionary of clients
        self.clients = {}

        self.timeout = int(self.config.getParameterValue('timeout', 1))

    '''
    Set up the socket for incoming clients
    '''
    def open_socket(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((self.host, self.port))
            self.server.listen(5)
            self.server.setblocking(0)
        except socket.error, (value, message):
            if self.server:
                self.server.close()
            print "Could not open socket: " + message
            sys.exit(1)

    '''
    Use poll() to handle each incoming client
    '''
    def run(self):
        self.poller = select.epoll()
        self.pollmask = select.EPOLLIN | select.EPOLLHUP | select.EPOLLERR
        self.poller.register(self.server, self.pollmask)
        while True:
            # poll sockets
            try:
                sockets = self.poller.poll(timeout=self.timeout)
            except:
                return

            for (socket, event) in sockets:
                # handle errors
                if event & (select.POLLHUP | select.POLLERR):
                    self.handleError(socket)
                    continue

                # handle the server socket
                if socket == self.server.fileno():
                    self.handleServer()
                    continue

                # handle client socket
                self.handleClient(socket)

    '''
    Handle error condition
    '''
    def handleError(self, socket):
        self.poller.unregister(socket)
        if socket == self.server.fileno():
            # recreate server socket
            self.server.close()
            self.open_socket()
            self.poller.register(self.server, self.pollmask)
        else:
            # close the socket
            self.clients[socket].close()
            del self.clients[socket]

    '''
    Handle client connection to server
    '''
    def handleServer(self):
        (client, address) = self.server.accept()
        client.setblocking(0)
        self.clients[client.fileno()] = ClientConnection(client, self.timeout)
        self.poller.register(client.fileno(), self.pollmask)

    '''
    Handle client request to server
    '''
    def handleClient(self, socket):
        request = self.clients[socket].getRequest()
        if request:
            self.clients[socket].send(request)
        else:
            self.poller.unregister(socket)
            self.clients[socket].close()
            del self.clients[socket]


if __name__ == "__main__":
    s = Server(8080)
