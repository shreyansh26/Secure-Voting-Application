import socket
import sys
from Crypto.Util.number import inverse, getPrime
import random
from math import gcd
import json

host = 'localhost'
port = 8080
address = (host, port)

voted = False
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(address)
server_socket.listen(5)

# Can be multithreaded
print("Listening for client . . .")
conn, address = server_socket.accept()
print("Connected to client at ", address)

privKeys = []
publicKeys = []
votesTally = {}
factors = {}

# Keys for the CTF
ctf_p = getPrime(1024)
ctf_q = getPrime(1024)
ctf_phi = (ctf_p-1) * (ctf_q-1)
ctf_n = ctf_p*ctf_q
ctf_found = False
while not ctf_found:
	ctf_e = random.randint(2, ctf_phi-1)
	if gcd(ctf_e, ctf_phi) == 1:
		ctf_found = True

ctf_d = inverse(ctf_e, ctf_phi)

voterE = None
voterD = None
voterN = None

while True:
	output = conn.recv(4096)
	data = output.strip()
	data = data.decode()
	if data == "disconnect":
		conn.close()
		sys.exit("Received disconnect message. Shutting down.")
		conn.send("dack")

	try:  
		data = json.loads(data)
		if data["choice"] == "register":
			if not(voterE is None or voterE is None or voterD is None):
				conn.sendall(b"Voter already registered!")
				continue
			p = getPrime(1024)
			q = getPrime(1024)
			phi = (p-1) * (q-1)
			n = p*q
			found = False
			while not found:
				e = random.randint(2, phi-1)
				if gcd(e, phi) == 1:
					found = True

			d = inverse(e, phi)
			factors[n] = (p, q)
			voterE = e
			voterD = d
			voterN = n
			ctfE = ctf_e
			ctfN = ctf_n
			payload = '{"voterE": "' + str(voterE) + '", "voterD": "' + str(voterD) + '", "voterN": "' + str(voterN) + '", "ctfE": "' + str(ctf_e) + '", "ctfN": "' + str(ctf_n) + '"}'
			conn.sendall(payload.encode())
			privKeys.append((voterD, voterN))
			publicKeys.append((voterE, voterN))
			print("Voter registered!")

		elif data["choice"] == "vote":
			print("Vote received")
			print(data)
			message = int(data["vote"])
			e = int(data["e"])
			N = int(data["N"])
			if (e, N) in publicKeys:
				f1, f2 = factors[N]
				d = inverse(e, (f1-1)*(f2-1))
				decMessage = pow(message, ctf_d, ctf_n)
				vote_val = pow(decMessage, voterE, voterN)
				if voted:
					conn.sendall(b"You have already voted!")
					continue
				if vote_val >= 1 and vote_val <= 10:
					if vote_val in votesTally.keys():
						votesTally[vote_val] += 1
					else:
						votesTally[vote_val] = 1
					conn.sendall(b"Vote registered!")
					voted = True
				else:
					conn.sendall(b"Vote value not legit or corrupted")
			else:
				conn.sendall(b"Voter not registered!")

		elif data["choice"] == "results":
			data_string = json.dumps(votesTally)
			conn.sendall(data_string.encode())

	except Exception as e:
		print(e)
