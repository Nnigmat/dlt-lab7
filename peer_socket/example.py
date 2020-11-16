from peer_socket import PeerSocket
from random import randint
from Crypto.Cipher import AES
import base64
import os
import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES
from time import sleep

BLOCK_SIZE = 32
PADDING = '{'
GREETING = 'GREETING'
DELETE = 'DELETE'

def _unpad(s):
    return s[:-ord(s[len(s)-1:])]

def _pad(s):
    return s + ((BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE))

def encrypt(key, raw):
    raw = _pad(raw)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return base64.b64encode(iv + cipher.encrypt(raw.encode()))

def decrypt(key, enc):
    enc = base64.b64decode(enc)
    iv = enc[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    try:
        return _unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')
    except:
        return ''

if __name__ == "__main__":

    key = os.urandom(BLOCK_SIZE)

    peers = [
                PeerSocket(('localhost', 6000), key),
                PeerSocket(('localhost', 7000), key),
                PeerSocket(('localhost', 8000), key),
                PeerSocket(('localhost', 9000), os.urandom(BLOCK_SIZE)),
                PeerSocket(('localhost', 9100), os.urandom(BLOCK_SIZE))
            ]

    def GREETING_wrapper(node):
        def GREET(sender_addr, message):
            if sender_addr == node.addr:
                return ''

            decrypted = decrypt(node.key, message)

            if not decrypted.startswith(GREETING) and not decrypted.startswith(DELETE):
                print(f'Primary is Traitor, sender addr: {sender_addr}')
                for x in peers:
                    if x.addr not in node.deleted_addrs: 
                        node.send(x.addr, DELETE, encrypt(node.key, DELETE + str(sender_addr)), response)

            if decrypted.startswith(GREETING):
                print(str(sender_addr) + ' said ' + str(decrypt(node.key, message)), " (raw: " , message, " )")

            if decrypted.startswith(DELETE):
                addr = decrypted[len(DELETE)]
                node.counter[addr] += 1 
                if node.counter[addr] == 3:
                    node.deleted_addrs.add(addr)

            return decrypted
        return GREET


    def response(message):
        if len(message) > 0:
            print('Got response ' + message) 

    for x in peers:
        x.on(GREETING, GREETING_wrapper(x))
        x.on(DELETE, GREETING_wrapper(x))


    for _ in range(10):
        main_node = peers[randint(0, len(peers) - 1)]
        print(f'\nMain node: {main_node.addr}')

        # Initialization of GREETINGs
        for x in peers:
            main_node.send(x.addr, GREETING, encrypt(main_node.key, GREETING), response)

        sleep(1)
