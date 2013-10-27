#httPyServer
## A Simple Web Server Written in Python
### By Keith McQueen For BYU CS 360 Fall 2013

#### Source Files
Below are the source files that make up this project with a short description of their content and purpose.

* clientConnection.py

>Contains the `ClientConnection` class which wraps the actual client socket.  This class provides methods for getting the request, sending the response, and closing the connection as well as determining if the connection has been previously closed and/or if the connection has gone stale (see [Timeouts](#Timeouts) below).  The former methods are useful for timing out of the connection and harvesting the idle connections as part of the mark and sweep algorithm.

* configuration.py
 
>Contains code to load the configuration data from a named file.  The `Configuration` class reads the file supplied to the constructor and then parses the lines to load the data into internal storage.  Methods are provided to extract values from the configuration, such as listing all configured domains, MIME types and parameters as well as getting the document root location for a given domain, getting the MIME type for a given file extension, and getting the value for a named parameter.  Methods for retrieving values include implicit or explicit defaults.

* httpRequestHandler.py

>Contains the `HttpRequestHandler` class which performs all the work related to handling a client request.  It currently supports the `HEAD` and `GET` (not including Range requests) verbs from HTTP 1.1.  The `handleRequest` method makes use of some lightweight reflection to determine which internal method should be used to actually handle the request based on the verb specified in the reqeust header.  Both the `handleHead` and `handleGet` methods use the `getResponseHeader` method to read the details of the request headers and to resolve the requested resource to an actual file.

* pollingServer.py

>Contains the `Server` class which is where the actual server socket is set up along with the poller to handle multiplexing of clients.

* web.py

>Contains the `Main` class and is the entry point for the project.  This class handles the reading in of the command-line arguments and then starts up an instance of the `Server` class.

#### Non-Blocking I/O
Non-blocking I/O is used for both the client and server sockets.  The `Server` class' `open_socket` method (in pollingServer.py) creates the socket and sets it to use non-blocking I/O.  The `handleServer` method, called when an incoming connection is detected by the poller,accepts the client connection, setting it to also use non-blocking I/O. 

From here, the remaining communication with the client socket is handled by the `ClientConnection` class.  Its `getRequest` and `sendResponse` methods both work to receive and send data from and to the client respectively.  

The `getRequest` method attempts to read in a pre-determined amount of data from the client socket.  If an exception occurs or not enough data has been received to formulate a full request message, then the method simply returns `None`.  Otherwise the text of the request message is returned.

The `sendResponse` method takes two (2) parameters, the response headers and the response entity or body.  The headers are always expected and are sent first to the client.  If the body is supplied (as it would be with a `GET` request, or in the case of an error), it is read in chunks of 64kB (64 * 1024 bytes) to the client.  Internally, a `sendBytes` method is used for sending all data down to the client.  This method ensures that each byte is sent.  When an exception is raised while trying to send data to the client, if the associated error is either `EWOULDBLOCK` or `EAGAIN`, then we attempt to send the data again immediately.  Otherwise, we cease attempting to send anymore data.

#### Timeouts
The timeout period is read in from the configuration file (`web.conf`) and is available from the `Configuration` instance (created at startup) as one of the parameters.  This timeout value is used in the `Server` class (in pollingServer.py) both when the poller is set up, and when determining if client connections need to be harvested.  Each time the poller wakes the `Server` instance, after having serviced all ready clients, the `harvestIdleConnections` method is called.  This method checks to see if enough time has past since the last time connections were harvested, and if so, then iterates through the connections closing any that are stale and disposing of any that have already been closed.

The `ClientConnection` class (in clientConnection.py) also makes use of the timeout value.  When data is read from the client, the current time is stored in the `lastAccess` instance variable.  The `isStale` method subtracts this time from the current time and compares it to the timeout value.  If the time since the last access is greater than the timeout value, then the connection is considered stale and ripe for harvesting.

#### Caching
Caching of incoming request data is done in the `Server` class (in pollingServer.py).  It maintains a dictionary of client sockets and associated `ClientConnection` instances.  Each `ClientConnection` instance maintains the buffer of data received from the client and is capable of returning a fully-formed request message, if one has been received.