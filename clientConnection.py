import socket
import time


class ClientConnection:
    def __init__(self, client, timeout):
        self.client = client
        self.closed = False
        self.lastAccess = time.time()
        self.timeout = timeout
        self.buffer = ''
        self.readSize = 1024

    def close(self):
        self.client.close()
        self.closed = True

    def isClosed(self):
        return self.closed

    def isStale(self):
        return time() - self.lastAccess > self.timeout

    def getRequest(self):
        try:
            # get the data from the client
            data = self.client.recv(self.readSize)
            if not data:
                self.close()
                return None

            self.buffer += data

            # update the last access time
            self.lastAccess = time()

            # if the buffer contains a complete request message return it
            (before, separator, after) = self.buffer.partition('\r\n\r\n')
            if before != self.buffer:
                self.buffer = after
                return before
        except socket.error:
            pass

        return None
