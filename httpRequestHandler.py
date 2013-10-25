import time
import os
from StringIO import StringIO

handlerMethods = {
    'GET': 'handleGet',
    'HEAD': 'handleHead'
}

responseHeaderMethods = {
    'Date': 'generateDateHeader',
    'Server': 'generateServerHeader',
    'Content-Type': 'generateContentTypeHeader',
    'Content-Length': 'generateContentLengthHeader',
    'Last-Modified': 'generateLastModifiedHeader'
}

responseCodes = {
    200: ('OK', ''),
    400: ('Bad Request', 'The request is not properly formatted or is missing required information.'),
    403: ('Forbidden', 'You do not have sufficient privileges for the requested resource.'),
    404: ('Not Found', 'The requested resource could not be found.'),
    500: ('Internal Server Error', 'The server encountered an error'),
    501: ('Not Implemented', 'The requested method is not implemented')
}

errorResponseTemplate =\
    '<!DOCTYPE HTML>\r\n' +\
    '<html>\r\n' +\
    '<head><title>{eno} {emsg}</title></head>\r\n' +\
    '<body><h1>{emsg}</h1><p>{emsgl}<br/></p></body>\r\n' +\
    '</html>'

defaultResponse =\
    '<!DOCTYPE HTML>\r\n' +\
    '<html>\r\n' +\
    '<head><title>httPyServer</title></head>\r\n' +\
    '<body>\r\n' +\
    '<h1>Success!</h1>\r\n' +\
    '<p>\r\n' +\
    'If you''re seeing this, then you have successfully configured the ' +\
    'httPyServer for your system. You may replace this message by installing ' +\
    'a file named index.html in the document root location for the configured ' +\
    'domain(s).' +\
    '</p>\r\n' +\
    '</body>\r\n' +\
    '</html>'


class HttpRequestHandler:
    def __init__(self):
        self.requestHeaderValues = {}
        self.responseHeaderValues = {}
        self.resource = None

    def handleRequest(self, client, request, config):
        line = request.split('\r\n', 1)[0]
        verb = line.split(' ', 1)[0]
        if verb in handlerMethods:
            return getattr(self, handlerMethods[verb])(client, request, config)

        return self.handlerError(501)

    def handleHead(self, client, request, config):
        # split the request into lines
        lines = request.splitlines()
        if len(lines) <= 0:
            return self.handleError(400)

        # get the resource URL from the first line
        url = lines[0].split()[1]

        # parse out the remaining header lines
        for line in lines[1:]:
            (key, sep, val) = line.partition(': ')
            self.requestHeaderValues[key] = val

        # try to resolve the resource based on the given URI
        try:
            self.resolveResource(url, config)
        except HttpException as e:
            self.handleError(client, e.errNum)

        # generate the response headers
        client.sendResponse(self.generateResponseHeaders(200))

    def handleGet(self, client, request, config):
        # get the HEAD
        self.handleHead(client, request, config)

        if self.resource:
            self.sendResource(client, self.resource)

    def handleError(self, client, errorNum):
        if not errorNum in responseCodes:
            return self.handleError(501)

        (err_msg, err_msg_long) = responseCodes[errorNum]

        # generate the response entity
        entity = errorResponseTemplate.\
            format(eno=errorNum, emsg=err_msg, emsgl=err_msg_long)

        # set the response header values
        self.responseHeaderValues['Content-Type'] = 'text/html'
        self.responseHeaderValues['Content-Length'] = len(entity)

        # generate the response headers
        headers = self.generateResponseHeaders(errorNum)

        client.sendResponse('%s\r\n%s' % (headers, entity))

    def generateResponseHeaders(self, responseCode):
        if not responseCode in responseCodes:
            return self.generateResponseHeaders(501)

        (resp_msg, resp_msg_long) = responseCodes[responseCode]
        headers = 'HTTP/1.1 %d %s\r\n' % (responseCode, resp_msg)

        for key in responseHeaderMethods:
            headers += getattr(self, responseHeaderMethods[key])()

        return headers + '\r\n'

    def generateDateHeader(self):
        return 'Date: %s\r\n' % (self.formatTime(time.time()))

    def generateServerHeader(self):
        return 'Server: httPyServer (BYU CS 360 Python Web Server Project)\r\n'

    def generateContentTypeHeader(self):
        if not 'Content-Type' in self.responseHeaderValues:
            return ''

        return 'Content-Type: %s\r\n' %\
            (self.responseHeaderValues['Content-Type'])

    def generateContentLengthHeader(self):
        if not 'Content-Length' in self.responseHeaderValues:
            return ''

        return 'Content-Length: %d\r\n' %\
            (self.responseHeaderValues['Content-Length'])

    def generateLastModifiedHeader(self):
        if not 'Last-Modified' in self.responseHeaderValues:
            return ''

        return 'Last-Modified: %s\r\n' %\
            (self.formatTime(self.responseHeaderValues['Last-Modified']))

    def formatTime(self, t):
        return time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(t))

    def resolveResource(self, url, config):
        # if no host was specified, then we're in trouble
        if not 'Host' in self.requestHeaderValues:
            raise HttpException(400)

        # get the document root location
        host = self.requestHeaderValues['Host']
        docRoot = config.getDocRootForDomain(host)
        if not docRoot:
            docRoot = '.'

        # get the file name (path to file from doc root)
        filename = url
        if '/' == filename:
            filename = '/index.html'

        # assemble the file path
        filepath = docRoot + filename

        # get the resource (handling any errors)
        try:
            self.resource = open(filepath, 'rb')

            # put info about the file in the response header values
            stats = os.stat(filepath)
            self.responseHeaderValues['Content-Length'] = stats.st_size
            self.responseHeaderValues['Last-Modified'] = stats.st_mtime

            # get the content type from the configuration
            parts = filename.split('.')
            if len(parts) >= 1:
                self.responseHeaderValues['Content-Type'] = config.getMimeTypeForExt(parts[-1])
        except IOError as (errno, strerror):
            if errno == 13:  # Forbidden
                raise HttpException(403)
            elif errno == 2:  # Not Found
                if filename == '/index.html':
                    self.resource = StringIO(defaultResponse)
                    self.responseHeaderValues['Content-Type'] = 'text/html'
                    self.responseHeaderValues['Content-Length'] = len(defaultResponse)
                    self.responseHeaderValues['Last-Modified'] = time.time()
                else:
                    raise HttpException(404)
            else:  # Internal Error
                raise HttpException(500)

    def sendResource(self, client, resource):
        try:
            bytes = 'empty'
            while (bytes):
                bytes = resource.read(512*1024)
                client.sendResponse(bytes)
        finally:
            resource.close()


class HttpException(Exception):
    def __init__(self, errNum):
        self.errNum = errNum

    def __str__(self):
        return str(self.errNum)
