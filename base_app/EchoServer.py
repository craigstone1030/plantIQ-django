from simple_websocket_server import WebSocketServer, WebSocket

websocketServer = None
clients = []

class SocketServer(WebSocket):
    def handle(self):
        print(self.address[0] + u' - ' + self.data)

    def connected(self):
        print(self.address, 'connected')
        # for client in clients:
        #     client.send_message(self.address[0] + u' - connected')
        clients.append(self)

    def handle_close(self):
        clients.remove(self)
        print(self.address, 'closed')
        # for client in clients:
        #     client.send_message(self.address[0] + u' - disconnected')

def initSocketServer(port):
    global websocketServer
    websocketServer = WebSocketServer('', port, SocketServer)
    # server.serve_forever()

def boradcast(data):
    print(len(clients), "broadcast:", data)
    for client in clients:
        client.send_message(data)