#!/usr/bin/python

import socket
import struct
import threading
import math
import msgpack
import sys
from ast import literal_eval
# from time import sleep


msg_template = '{{ "l": {hp}, "p": {pos}, "d": {dir}, "s": 0, "v": 0, "k": 0, "vp": {players}, "pi": [[1, 100], [2, 75]], "vo": 0, "ao": 0, "ev": 0, "ti": {ti} }}'


def run_server():
    mastersocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # mastersocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    mastersocket.bind(('localhost', 9999))
    mastersocket.listen(1)

    (clientsocket, address) = mastersocket.accept()
    game = GameMock(clientsocket)

    t = threading.Thread(target=game._receive_forever)
    t.daemon = True  # helpful if you want it to die automatically
    t.start()
    t.join()


class OtherPlayer(object):
    def __init__(self):
        self.x = 200
        self.y = 200
        self.rotation = 0
        self.id = 42
        self.team = 1

    def update(self):
        # self.x = (self.x + 5) % 200
        # self.y = (self.y + 5) % 200
        self.rotation = (self.rotation + 15) % 360
        if self.x > 100 and self.x < 150:
            return
        else:
            return [self.id, self.x, self.y, self.rotation]


class GameMock(object):
    def __init__(self, socket):
        self._socket = socket
        self.charpos = [100, 200]
        self.hp = 100
        self.remaining_time = 300
        self.op = OtherPlayer()

        init_info = myreceive(socket)
        mysend(socket, {
            'team': init_info['team'],
            'id': 0,
            'max_hp': self.hp,
            'pos': self.charpos,
            'players': [[init_info['nick'], 0, init_info['team']], ['plop', self.op.id, self.op.team]],
            'map': 'test.hfm',
            'map_hash': 'aefa653685023a786f34830756e09db4e8401af1'
        })

    def _receive_forever(self):
        while 1:
            msg = myreceive(self._socket)
            if 'd' in msg:
                self.update_pos(msg)
        print 'fin'

    def update_pos(self, msg):
        direction = float(msg['d'])
        print direction
        speed = float(msg['s'])
        dx = -math.sin(math.radians(direction)) * speed * 20
        dy = math.cos(math.radians(direction)) * speed * 20
        print dx, dy
        self.charpos = [self.charpos[0] + dx, self.charpos[1] + dy]
        print self.charpos
        self.hp = self.hp-1
        self.remaining_time = self.remaining_time - 1
        msg = msg_template.format(pos=self.charpos, hp=self.hp, dir=direction, ti=self.remaining_time,
                                  players=[self.op.update()])
        mysend(self._socket, literal_eval(msg))


def mysend(socket, msg):
    print msg
    msg = msgpack.packb(msg)
    msglen = len(msg)
    print 'msglen:', msglen
    msglenb = struct.pack('!i', msglen)
    socket.send(msglenb)
    totalsent = 0
    while totalsent < msglen:
        sent = socket.send(msg[totalsent:])
        if sent == 0:
            raise RuntimeError("socket connection broken")
        totalsent = totalsent + sent


def myreceive(socket):
    msg_len = socket.recv(4)
    if msg_len is None or len(msg_len) == 0:
        sys.exit()
    msg_len = struct.unpack('!i', msg_len)[0]
    msg = socket.recv(int(msg_len))
    msg = msgpack.unpackb(msg)

    # msg = ''
    # while len(msg) < msglen:
    #     chunk = socket.recv(msglen-len(msg))
    #     if chunk == '':
    #         raise RuntimeError("socket connection broken")
    #     msg = msg + chunk
    print msg
    return msg


if __name__ == '__main__':
    run_server()
