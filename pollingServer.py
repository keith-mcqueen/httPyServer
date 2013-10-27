import select
import socket
import sys
import time
from configuration import Configuration
from clientConnection import ClientConnection
from httpRequestHandler import HttpRequestHandler


'''
Polling Server
'''


class Server:
    '''
    *** initializer ***
    '''
    def __init__(self, port, debug):
        # load the configuration file
        self.config = Configuration('web.conf')
        self.config.setParameter('Debug', debug)

        self.host = ""
        self.port = port
        self.debug = debug

        # prepare the dictionary of clients
        self.clients = {}

        # set the timeout value
        self.timeout = int(self.config.getParameterValue('timeout', 1))

        # open the socket
        self.open_socket()

        self.lastHarvestTime = time.time()

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
        self.pollmask =\
            select.EPOLLIN |\
            select.EPOLLHUP |\
            select.EPOLLERR
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

            # harvest idle/stale connections
            self.harvestIdleConnections()

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
        self.clients[client.fileno()] = ClientConnection(client, self.config)
        self.poller.register(client.fileno(), self.pollmask)

    '''
    Handle client request to server
    '''
    def handleClient(self, socket):
        request = self.clients[socket].getRequest()
        if request:
            self.handleRequest(self.clients[socket], request, self.config)
        else:
            self.poller.unregister(socket)
            self.clients[socket].close()
            del self.clients[socket]

    def handleRequest(self, client, request, config):
        HttpRequestHandler(config).handleRequest(client, request)

    def harvestIdleConnections(self):
        # if it's been long enough since we last harvested, then harvest again
        if (time.time() - self.lastHarvestTime) >= self.timeout:
            for client, connection in self.clients.items():
                if connection.isClosed():
                    del self.clients[client]
                elif connection.isStale():
                    connection.close()

            # reset the last harvest time
            self.lastHarvestTime = time.time()

if __name__ == "__main__":
    s = Server(8080)
