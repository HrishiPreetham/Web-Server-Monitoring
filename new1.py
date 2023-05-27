from gmail import email_alert
import platform
import subprocess
import socket
import ssl
from datetime import datetime
import pickle
context = ssl.create_default_context()


class Server():
    def __init__(self, name, port, connection, priority):
        self.name = name
        self.port = port
        self.connection = connection.lower()
        self.priority = priority.lower()

        self.history = []
        self.alert = False

    def check_connection(self):
        msg = ""
        success = False
        now = datetime.now()

        try:
            if self.connection == "plain":
                socket.create_connection((self.name, self.port), timeout=10)
                msg = f"{self.name} is up. On port {self.port} with {self.connection}"
                success = True
                self.alert = False
            elif self.connection == "ssl":
                with socket.create_connection((self.name, self.port), timeout=10) as sock:
                    context = ssl.create_default_context()
                    with context.wrap_socket(sock, server_hostname=self.name) as ssock:
                        msg = f"{self.name} is up. On port {self.port} with ssl"
                        success = True
            elif self.connection=="ping":
                if self.ping():
                    msg = f"{self.name} is up. On port {self.port} with {self.connection}"
                    success = True
                    self.alert = False
        except socket.timeout:
            msg = f"server: {self.name} timeout. On port {self.port}"
        except (ConnectionRefusedError, ConnectionResetError) as e:
            msg = f"server: {self.name} {e}"
        except Exception as e:
            msg = f"server: {self.name} {str(e)}"

        if success == False and self.alert == False:
            # Send Alert
            self.alert = True
            email_alert(self.name, f"{msg}\n{now}", "glpreetham@gmail.com")

        self.create_history(msg, success, now)

    def create_history(self, msg, success, now):
        history_max = 100
        self.history.append((msg, success, now))

        while len(self.history) > history_max:
            self.history.pop(0)

    def ping(self):
        try:
            output = subprocess.check_output("ping -{} 1 {}".format('n' if platform.system().lower(
            ) == "windows" else 'c', self.name), shell=True, universal_newlines=True)
            if 'unreachable' in output:
                return False
            else:
                return True
        except Exception:
            return False


if __name__ == "__main__":
    try:
        servers = pickle.load(open("servers.pickle", "rb"))
    except:
        servers = [
            Server("reddit.com", 80, "plain", "high"),
            Server("pesuacademy.com", 80, "plain", "high"),
            Server("smtp.gmail.com", 465, "ssl", "high"),
            Server("192.168.0.121", 80, "ping", "high"),
            Server("yahoo.com", 80, "plain", "high")
        ]
        servers.pop(3)
    for server in servers:
        server.check_connection()
        print(len(server.history))
        print(server.history[-1])

    pickle.dump(servers, open("servers.pickle", "wb"))
