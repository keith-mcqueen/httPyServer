configMethods = {
    'host': 'addDocRootForDomain',
    'media': 'addMimeTypeForExt',
    'parameter': 'addParameter'
}


'''
Configuration class for the server.  This class reads a configuration file
and stores the values internally
'''


class Configuration:
    docRoots = {}
    mimeTypes = {}
    parameters = {}

    def __init__(self, filename):
        with open(filename, 'r') as config_file:
            for line in iter(config_file):
                # strip the trailing EOL char(S)
                line = line.lower().strip('\n\r')

                # split the string into words (delimited by whitespace)
                words = line.split()
                if len(words) <= 0:
                    continue

                # invoke the proper method based on the keyword
                keyword = words[0]
                if keyword in configMethods:
                    getattr(self, configMethods[keyword])(words[1:])

    def addDocRootForDomain(self, args):
        if len(args) > 1:
            self.setDocRootForDomain(args[0], args[1])

    def setDocRootForDomain(self, domain, docRoot):
        self.docRoots[domain] = docRoot

    def addMimeTypeForExt(self, args):
        if len(args) > 1:
            self.setMimeTypeForExt(args[0], args[1])

    def setMimeTypeForExt(self, ext, mediaType):
        self.mimeTypes[ext] = mediaType

    def addParameter(self, args):
        if len(args) > 1:
            self.setParameter(args[0], args[1])

    def setParameter(self, key, value):
        self.parameters[key] = value

    def getDocRootForDomain(self, domain):
        if not domain in self.docRoots:
            return self.getDocRootForDomain('default')

        return self.docRoots[domain]

    def getdocRoots(self):
        return self.docRoots.keys()

    def getMimeTypeForExt(self, ext):
        if not ext in self.mimeTypes:
            return 'text/plain'

        return self.mimeTypes[ext]

    def getExts(self):
        return self.mimeTypes.keys()

    def getParameterValue(self, key, default):
        if key in self.parameters:
            return self.parameters[key]

        return default

    def getParameterKeys(self):
        return self.parameters.keys()

# this is here just for testing purposes
if __name__ == '__main__':
    c = Configuration('web.conf')
    print c.docRoots
    print c.mimeTypes
    print c.parameters
