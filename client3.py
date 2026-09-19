import socket
import json

class Client:
    def __init__(self,host='127.0.0.1', port=31337):
        self.host= host
        self.port= port

    def send_request(self,action, key=None, value=None, keys=None, items=None, ttl=None):
        request = {'action': action}
        if key is not None:
            request['key'] = key
        if value is not None:
            request['value'] = value
        if keys is not None:
            request['keys'] = keys
        if items is not None:
            request['items']= items
        if ttl is not None:
            request['ttl'] = ttl

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((self.host, self.port))
            client_socket.send(json.dumps(request).encode('utf-8'))
            response = client_socket.recv(1024).decode('utf-8')
            return json.loads(response)

    def run(self):
        print("currently in client - enter 'bye' to quit:c")
        while True:
            command = input("\nenter command (example - SET key value, GET key, DELETE key, EXISTS key, EXPIRE key ttl_seconds, FLUSH, MSET key1=value1,key2=value2, MGET key1,key2): ")
            if command.lower()== 'bye':
                break

            parts = command.split()
            action= parts[0].upper()

            if action == 'SET':
                key= parts[1]
                value = parts[2]
                response = self.send_request(action,key=key, value=value)
            elif action == 'GET':
                key = parts[1]
                response = self.send_request(action,key=key)
            elif action == 'DELETE' or action == 'DEL':
                key= parts[1]
                response = self.send_request(action, key=key)
            elif action == 'EXISTS':
                key = parts[1]
                response = self.send_request(action, key=key)
            elif action == 'EXPIRE':
                key = parts[1]
                ttl = int(parts[2])
                response = self.send_request(action, key=key, ttl=ttl)
            elif action == 'FLUSH':
                response = self.send_request(action)
            elif action== 'MSET':
                items = dict(item.split('=') for item in parts[1].split(','))
                response = self.send_request(action,items=items)
            elif action == 'MGET':
                keys = parts[1].split(',')
                response = self.send_request(action,keys=keys)
            else:
                response= 'Unknown command'

            print(f'response: {response}')

if __name__ == '__main__':
    client= Client()
    client.run()
