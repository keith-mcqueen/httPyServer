configMethods = {
    'host': 'addDomain',
    'media': 'addMediaType',
    'parameter': 'addParameter'
}


'''
Configuration class for the server.  This class reads a configuration file
and stores the values internally
'''


class Configuration:
    domains = {}
    mediaTypes = {}
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

    def addDomain(self, args):
        if len(args) > 1:
            self.setDomainHandler(args[0], args[1])

    def setDomainHandler(self, domain, handler):
        self.domains[domain] = handler

    def addMediaType(self, args):
        if len(args) > 1:
            self.setMediaType(args[0], args[1])

    def setMediaType(self, ext, mediaType):
        self.mediaTypes[ext] = mediaType

    def addParameter(self, args):
        if len(args) > 1:
            self.setParameter(args[0], args[1])

    def setParameter(self, key, value):
        self.parameters[key] = value

    def getDomainHandler(self, domain):
        return self.domains[domain]

    def getDomains(self):
        return self.domains.keys()

    def getMediaType(self, ext):
        return self.mediaTypes[ext]

    def getMediaExtensions(self):
        return self.mediaTypes.keys()

    def getParameterValue(self, key):
        return self.parameters[key]

    def getParameterKeys(self):
        return self.parameters.keys()

# this is here just for testing purposes
if __name__ == '__main__':
    c = Configuration('web.conf')
    print c.domains
    print c.mediaTypes
    print c.parameters
