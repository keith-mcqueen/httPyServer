'''
A HTTP server that handles one client at a time.  Typing Control-C
will quit the server.
'''

import argparse

from pollingServer import Server


class Main:
    ''' Parse command line options and perform the download. '''
    def __init__(self):
        self.parse_arguments()

    def parse_arguments(self):
        ''' parse arguments, which include '-p' for port '''
        parser = argparse.ArgumentParser(
            prog='HTTP Server',
            description='A simple HTTP server that handles one client at a time',
            add_help=True
        )
        parser.add_argument(
            '-p',
            '--port',
            type=int,
            action='store',
            help='port the server will bind to',
            default=8080)
        parser.add_argument(
            '-d',
            '--debug',
            action='store_true',
            help='enable debugging messages')
        self.args = parser.parse_args()

    def run(self):
        s = Server(self.args.port, self.args.debug)
        s.run()


if __name__ == "__main__":
    m = Main()
    try:
        m.run()
    except KeyboardInterrupt:
        pass
