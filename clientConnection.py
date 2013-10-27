import socket
import time
import errno


class ClientConnection:
    def __init__(self, client, config):
        self.client = client
        self.closed = False
        self.lastAccess = time.time()
        self.timeout = config.getParameterValue('timeout', 1)
        self.debug = config.getParameterValue('Debug', False)
        self.buffer = ''
        self.readSize = 1024

    def close(self):
        self.client.close()
        self.closed = True

    def isClosed(self):
        return self.closed

    def isStale(self):
        return time.time() - self.lastAccess > self.timeout

    def getRequest(self):
        try:
            # get the data from the client
            data = self.client.recv(self.readSize)
            if not data:
                self.close()
                return None

            self.buffer += data

            # update the last access time
            self.lastAccess = time.time()

            # if the buffer contains a complete request message return it
            (before, separator, after) = self.buffer.partition('\r\n\r\n')
            if before != self.buffer:
                self.buffer = after
                return before
        except socket.error:
            pass

        return None

    def sendResponse(self, headers, response=None):
        self.sendBytes(headers)

        if response:
            try:
                bytes = 'empty'
                while (bytes):
                    bytes = response.read(65*1024)
                    self.sendBytes(bytes)
            finally:
                response.close()

    def sendBytes(self, bytes):
        totalsent = 0
        while totalsent < len(bytes):
            try:
                totalsent += self.client.send(bytes[totalsent:])
            except socket.error as e:
                if e.errno & (errno.EWOULDBLOCK | errno.EAGAIN):
                    #time.sleep(0.1)
                    continue
                else:
                    break
