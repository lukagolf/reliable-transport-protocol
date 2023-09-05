#!/usr/bin/env python3

import argparse, socket, time, json, select, sys, functools

# The remaining space for for data in our packets
DATA_SIZE = 1450

class Sender:
    """
    Represents the party sending messages.
    Attributes
    ----------
    host : str 
        The value of the remote host that the Sender will connect to.
    port : int
        The UDP port number to connect to.
    socket : socket
        The socket object that this Sender will use to send messages with.
    
    id_generator : int
        The current ID of our packets.
    window : int
        The current size of our sliding window.
    target_window : int
        The target size of our sliding window.
    last_msg_sent_time : int
        The time value of the message we last sent.
    msg_waiting_ack : dict
        A dictionary of message IDs that hve not been ACK'd yet.
    rtt : double
        The current estimated Round Trip Time (RTT)
    finished : Boolean
        Represents whether or not the Sender is finished sending packets or not.
    waiting : Boolean
        Represents whether or not we are waiting for an ACK from the Reciever.
    alpha : double
        Alpha coefficient.
    """
    id_generator = 0
    window = 4
    target_window = 16
    last_msg_sent_time = 0
    msgs_waiting_ack = {}
    rtt = 0.5
    finished = False
    waiting = False
    alpha = 0.875

    def __init__(self, host, port):
        """
        Parameters
        ----------
        host : str 
            The value of the remote host that the Sender will connect to.
        port : int
            The UDP port number to connect to.
        """
        self.host = host
        self.remote_port = int(port)
        self.log("Sender starting up using port %s" % self.remote_port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', 0))

    def log(self, message):
        """ Logs the given message to standard error (STDERR). """
        sys.stderr.write(message + "\n")
        sys.stderr.flush()

    def checksum256(self, st):
        """ Calculates a checksum of the given message. """
        return functools.reduce(lambda x,y:x+y, map(ord, st)) % 256
    
    def send(self, message):
        """ Sends the given message to the Reciever we are currently pointed at. """
        self.socket.sendto(json.dumps(message).encode('utf-8'), (self.host, self.remote_port))

    def send_msg(self, msg):
        """ 
        Wrapper function for the send() function. Logs that it is sending a message and saves the
        time of the message.
        """
        self.log("Sending message '%s'" % msg)
        self.send(msg)
        self.last_msg_sent_time = time.time()
        if len(self.msgs_waiting_ack) >= self.window:
            self.waiting = True

    def retransmit_msgs(self):
        """
        Retransmits the messages based on the given time and the current time out.
        """
        time_elapsed = time.time() - self.last_msg_sent_time
        if time_elapsed >= 1.75 * self.rtt:
            i = 0
            for msg in self.msgs_waiting_ack.values():
                self.send_msg(msg)
                i += 1
                if i >= self.window:
                    break
        
    def update_time_out(self):
        """
        Updates time out.
        """
        self.rtt = self.alpha * self.rtt + ((1 - self.alpha) * (time.time() - self.last_msg_sent_time))

    def congestion_control(self):
        """
        Optimizes congestion of the messages.
        """
        time_elapsed = time.time() - self.last_msg_sent_time

        if time_elapsed < 1.75 * self.rtt:
            if self.window < self.target_window:
                self.window += 1
        elif time_elapsed > 1.75 * self.rtt and 2 * self.window > self.target_window and len(self.msgs_waiting_ack) + 3> self.window:
            self.window = 1
            if self.target_window > 2:
                self.target_window = self.target_window - 1

    def run(self):
        """
        The main function that runs our program.
        """
        while True:
            sockets = [self.socket, sys.stdin] if not self.waiting and not self.finished else [self.socket]

            socks = select.select(sockets, [], [], 0.1)[0]
            for conn in socks:
                if conn == self.socket:
                    try: 
                        k, addr = conn.recvfrom(65535)
                        msg = json.loads(k.decode('utf-8'))

                        self.log("Received message '%s'" % msg)

                        if msg["id"] in self.msgs_waiting_ack and msg["type"] == "ack":
                            # If we recieve an ACK, remove it from the msgs_waiting_ack list.
                            self.msgs_waiting_ack.pop(msg["id"])              
                        self.waiting = False

                        # Update our time_out value
                        self.update_time_out()
                    except (ValueError, KeyError, TypeError) as e:
                        # If we have an error parsing our message, that means we have a corrupted 
                        # packet and we log it as such.
                        self.log(str(e))
                        self.log("corrupt msg")
                        
                elif conn == sys.stdin:
                    data = sys.stdin.read(DATA_SIZE)
                    if len(data) == 0:
                        self.log("All done!")
                        self.finished = True
                        # If we have no more data to output, we set self.finished to True.
                        continue

                    # Increment our current message ID and craft our msg packet.
                    self.id_generator += 1
                    msg = { "id": self.id_generator, "type": "msg", "data": data, "cs" : self.checksum256(data)}

                    # Add this message to msg_waiting_acct
                    self.msgs_waiting_ack[self.id_generator]= msg

                    self.send_msg(msg)

            if self.finished and len(self.msgs_waiting_ack) == 0:
                return
            self.congestion_control()
            # Decide whether or not to retransmit messages based on the given time.            
            self.retransmit_msgs()

        return

if __name__ == "__main__":
    """
    Here, we parse arguments given on the command line and initialize our Sender object with those values.
    """
    parser = argparse.ArgumentParser(description='send data')
    parser.add_argument('host', type=str, help="Remote host to connect to")
    parser.add_argument('port', type=int, help="UDP port number to connect to")
    args = parser.parse_args()
    sender = Sender(args.host, args.port)
    sender.run()
