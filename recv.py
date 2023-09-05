#!/usr/bin/env python3

import argparse, socket, time, json, select, struct, sys, math, functools

class Receiver:
    """
    Represents the party recieving messages.
    Attributes
    ----------
    socket : socket
        The socoket we will be listening and sending messages with.
    port : int
        The port number we bind to.
    remote_host : str
        The address of the remote host we are recieving messages from.
    remote_port : int
        The port of the remote host.
    printed_id : int
        ID of the message last recieved.
    received_msgs : dict
        Dictionary that stores messages with their message ID as the key.
    """
    printed_id = 0
    received_msgs = {}
    def __init__(self):
        """
        Initializes our Reciever object.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', 0))
        self.port = self.socket.getsockname()[1]
        self.log("Bound to port %d" % self.port)

        self.remote_host = None
        self.remote_port = None

    def send(self, message):
        """
        Sends the given message to our current remote host.
        """
        self.socket.sendto(json.dumps(message).encode('utf-8'), (self.remote_host, self.remote_port))

    def log(self, message):
        """
        Logs the given message to standard error.
        """
        sys.stderr.write(message + "\n")
        sys.stderr.flush()

    def checksum256(self, st):
        """
        Calculates a checksum value for the given string.
        """
        return functools.reduce(lambda x,y:x+y, map(ord, st)) % 256
    
    def print_msgs(self):
        """
        Prints out the last recieved message.
        """
        while self.printed_id +1 in self.received_msgs:
            self.printed_id += 1
            # Print out the data to stdout
            print(self.received_msgs[self.printed_id]["data"], end='', flush=True)
    
    def run(self):
        """
        Our main method that runs our Receiver object.
        """
        while True:
            socks = select.select([self.socket], [], [])[0]
            for conn in socks:
                try:
                    data, addr = conn.recvfrom(65535)

                    # Grab the remote host/port if we don't already have it
                    if self.remote_host is None:
                        self.remote_host = addr[0]
                        self.remote_port = addr[1]

                    # Decode the data which should be in the JSON format.
                    msg = json.loads(data.decode('utf-8'))

                    if msg["cs"] != self.checksum256(msg["data"]):
                        # If our checksum is not correct, we have a corrupted packet and thus drop it.
                        self.log("corrupt msg")
                        continue

                    if not(msg["id"] in self.received_msgs): 
                        # If the current msg is new, we put it into received_msgs and print it out.
                        self.received_msgs[msg["id"]] = msg
                        self.print_msgs()
                    
                    self.log("Received data message %s" % msg)
                        
                    # Always send back an ack
                    self.send({ "id": msg["id"], "type": "ack" })
                except (ValueError, KeyError, TypeError):
                    # Another way to check if our message is corrupt. Here, we check if decoding
                    # if the msg in JSON caused an error. If so, we catch the exception and log as such.
                    self.log("corrupt msg")

        return

if __name__ == "__main__":
    """
    Here, we parse the arguments given and start our Receiver object.
    """
    parser = argparse.ArgumentParser(description='receive data')
    args = parser.parse_args()
    sender = Receiver()
    sender.run()
