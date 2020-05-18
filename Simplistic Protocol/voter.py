import socket
import time
import json
import sys

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("localhost", 8080))

def print_options():
	print("Choose an option from below -")
	print("1. Register voter")
	print("2. Cast vote")
	print("3. View Results")

while True:
	print_options()
	choice = int(input())
	if choice == 1:
		payload = '{"choice": "register"}'
		client_socket.sendall(payload.encode())
		recv = client_socket.recv(4096).decode()
		if "Voter" in recv:
			print("Voter already registered")
			continue
		data = json.loads(recv)
		print(data)
		voterE = int(data["voterE"])
		voterD = int(data["voterD"])
		voterN = int(data["voterN"])
		ctfE = int(data["ctfE"])
		ctfN = int(data["ctfN"])

	elif choice == 2:
		print("Enter candidate id")
		vote = int(input())
		# Sign using voter's private key
		signedMessage = pow(vote, voterD, voterN)
		# Encrypt using CTF's public key
		encMesage = pow(signedMessage, ctfE, ctfN)
		payload = '{"choice": "vote", "vote": "' + str(encMesage) + '", "e": "' + str(voterE) + '", "N": "' + str(voterN) + '"}'
		client_socket.sendall(payload.encode())
		recv = client_socket.recv(4096)
		print(recv.decode())

	elif choice == 3:
		payload = '{"choice": "results"}'
		client_socket.sendall(payload.encode())
		recv = client_socket.recv(4096)
		print(recv.decode())

	else:
		dmsg = b"disconnect"
		print("Disconnecting")
		client_socket.send(dmsg)
		client_socket.close()
		sys.exit()