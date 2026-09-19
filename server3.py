import socket
import json
import threading
import time
import os

#starting your server
class Server:
    def __init__(self, host='127.0.0.1', port=31337, data_file='data.json'): #loopback ip address - local host(specifically for testing connections - doesnt connect to outside internet - always refers to own device), #port - door that lets data in/out (can pick any number btw 1024-65535(0-1023 is reserved for system proc - http,ftp))
        self.store= {} #memory
        self.expiry = {} #key -> unix timestamp when it expires
        self.host= host
        self.port= port
        self.data_file = data_file
        self.lock = threading.Lock() #keeps store/expiry consistent across client threads
        self.load()

#persistence - simple load/save of the whole store to a json file
    def load(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                saved = json.load(f)
                self.store = saved.get('store', {})
                self.expiry = saved.get('expiry', {})

    def save(self):
        with open(self.data_file, 'w') as f:
            json.dump({'store': self.store, 'expiry': self.expiry}, f)

# adding your methods and responses for clarity
    def _check_expired(self, key):
        expires_at = self.expiry.get(key)
        if expires_at is not None and time.time() >= expires_at:
            self.store.pop(key, None)
            self.expiry.pop(key, None)
            return True
        return False

    def set(self,key,value):
        self.store[key] = value
        self.expiry.pop(key, None) #a plain SET clears any old expiry on the key
        return f'stored {key}'

    def get(self,key):
        self._check_expired(key)
        return self.store.get(key,None)

    def delete(self,key):
        self._check_expired(key)
        if key in self.store:
            del self.store[key]
            self.expiry.pop(key, None)
            return f'deleted {key}'
        return None

    def exists(self,key):
        self._check_expired(key)
        return key in self.store

    def expire(self,key,ttl):
        self._check_expired(key)
        if key not in self.store:
            return False
        self.expiry[key] = time.time() + ttl
        return True

    def flush(self):
        self.store.clear()
        self.expiry.clear()
        return 'cleared all data ruh roh'

    def mget(self, keys):
        for key in keys:
            self._check_expired(key)
        return {key: self.store.get(key) for key in keys}

    def mset(self,items):
        for key, value in items.items():
            self.store[key] = value
            self.expiry.pop(key, None)
        return 'stored multiple values :O'

#here we have to manage said methods w a client socket in a server
    def handle_client(self, client_socket):
        try:
            request = client_socket.recv(1024).decode('utf-8') #decode to conv to string format(json) + serialization
            command = json.loads(request)
            #this takes a JSON-encoded string as i/p and parses it into a py obj (dict) , request has the raw data from socket AS a utf-8 encoded string, and command becomes our py dict

            action = command['action']
            with self.lock: #one client's command finishes before another's touches the store
                if action == 'SET':
                    response= self.set(command['key'], command['value'])
                    self.save()
                elif action == 'GET':
                    response = self.get(command['key'])
                elif action == 'DELETE' or action == 'DEL':
                    response= self.delete(command['key'])
                    self.save()
                elif action == 'EXISTS':
                    response = self.exists(command['key'])
                elif action == 'EXPIRE':
                    response = self.expire(command['key'], command['ttl'])
                    self.save()
                elif action == 'FLUSH':
                    response = self.flush()
                    self.save()
                elif action == 'MGET':
                    response = self.mget(command['keys'])
                elif action == 'MSET':
                    response = self.mset(command['items'])
                    self.save()
                else:
                    response = 'unknown command pls try again'

            client_socket.send(json.dumps(response).encode('utf-8'))
        finally:
            client_socket.close()

    def run(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #socket obj, AF_INET - IPv4 protocol, sock_stream -  TCP protocol
        server_socket.bind((self.host, self.port)) #binds the socket to host and port to listen to incoming connections
        server_socket.listen(5)
        print(f'YAHOO server is running on {self.host}:{self.port}')

        while True: #logging(?) because will go insane otherwise
            client_socket,addr = server_socket.accept()
            print(f'connection from {addr}')
            #a thread per client so multiple clients can be connected/served at once
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

if __name__ == '__main__': #code only runs when script is executed directly, NOT IMPORTED
    server= Server()
    server.run()
