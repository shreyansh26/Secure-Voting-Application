import socket
import time
import json
import sys
from Crypto.Random.random import getrandbits
from Crypto.Util.number import inverse
from math import gcd

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("localhost", 8080))

def print_options():
	print("Choose an option from below -")
	print("1. Register voter")
	print("2. Cast vote")
	print("3. View Results")

def blindingfactor(N):
    r = getrandbits(512) * (N-1)
    while (gcd(r, N) != 1):
        r = r+1
    return r

def blind(msg, e, n):
    r = blindingfactor(n)
    blindmsg = (pow(r, e, n) * msg) % n
    print("Blinded Message "+str(blindmsg))
    return (r, blindmsg)

def unblind(bsm, r, e, n):
	ubsm = (bsm * inverse(r, n)) % n
	print("Unblinded Signed Message "+str(ubsm))
	return ubsm

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
		r, blindMessage = blind(vote, voterE, voterN)
		payload = '{"choice": "vote", "vote": "' + str(blindMessage) + '", "e": "' + str(voterE) + '", "N": "' + str(voterN) + '"}'
		client_socket.sendall(payload.encode())
		recv = client_socket.recv(4096).decode()
		data = json.loads(recv)
		signedBlindMessage = int(data["signedBlindMessage"])
		signedBlindMessage_temp = pow(signedBlindMessage, ctfE, ctfN)
		unBlindedSignedMessage = unblind(signedBlindMessage_temp, r, voterE, voterN)
		payload = '{"unBlindedSignedMessage": "' + str(unBlindedSignedMessage) + '", "r": "' + str(r) + '"}'
		client_socket.sendall(payload.encode())
		recv = client_socket.recv(4096).decode()

		print("voterD", voterD)
		print("voterN", voterN)
		print("ctfE", ctfE)
		print("ctfN", ctfN)
		print(recv)

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