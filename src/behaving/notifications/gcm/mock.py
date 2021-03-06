import argparse
import logging
import os
import sys
import json
import codecs
try:
    from SimpleHTTPServer import SimpleHTTPRequestHandler
    import SocketServer
    from urlparse import parse_qs
except ImportError:
    from http.server import SimpleHTTPRequestHandler
    import socketserver as SocketServer
    from urllib.parse import parse_qs
import time

output_dir = None


class GCMServer(SimpleHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers.get('content-length'))
        body = self.rfile.read(content_length).decode('utf-8')

        try:
            message = json.loads(body)
        except:
            self.send_response(400)
            return

        if 'registration_ids' in message:
            recipients = message['registration_ids']
            del message['registration_ids']

        if 'to' in message:
            to = message['to']
            del message['to']
            recipients = [to]

        if not recipients:
            self.send_response(400)
            return

        global output_dir
        for recipient in recipients:
            recipient = str(recipient)
            recipient_dir = os.path.join(output_dir, recipient)
            if not os.path.exists(recipient_dir):
                try:
                    os.makedirs(recipient_dir)
                except OSError:
                    self.send_error(
                        400,
                        "Device directory [%s] could not be created"
                        % recipient_dir)

            filename = (
                time.strftime("%Y-%m-%d-%H%M%S", time.gmtime(time.time())))
            dest = os.path.join(recipient_dir, "%s.gcm" % filename)
            with codecs.open(dest, "w", encoding='utf-8') as f:
                f.write(json.dumps(message, ensure_ascii=False))

        self.send_response(200)


def main(args=sys.argv[1:]):
    """Main function called by `gcmmock` command.
    """
    parser = argparse.ArgumentParser(description='GCM mock server')
    parser.add_argument('-p', '--port',
                        default='8200',
                        help='The port to use')

    parser.add_argument('-o', '--output_dir',
                        default=None,
                        required=True,
                        help='Directory where to dump the GCMs')

    options = parser.parse_args(args=args)

    if not os.path.exists(options.output_dir):
        try:
            os.mkdir(options.output_dir)
        except OSError:
            logging.error('Output directory could not be created')
    global output_dir
    output_dir = options.output_dir

    httpd = SocketServer.TCPServer(("", int(options.port)), GCMServer)
    httpd.serve_forever()


if __name__ == '__main__':
    main()
