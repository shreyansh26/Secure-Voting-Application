import socket
import sys
from Crypto.Util.number import inverse, getPrime
import random
from math import gcd
import json
import _thread


privKeys = []
publicKeys = []
votesTally = {}
factors = {}
voted = {}

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

def signature(msg, d, n):
    coded = pow(msg, d, n)
    print("Blinded Signed Message "+str(coded))
    return coded

def verify(msg, r, e, n):
	ver = pow(msg, e, n)
	print("Message After Verification "+str(ver))
	return ver

def logic(conn, addr):
	global privKeys
	global publicKeys
	global factors
	global votesTally
	global factors
	global ctf_e
	global ctf_d
	global ctf_n
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
					print("ctf_e", ctf_e)
					print("ctf_d", ctf_d)
					print("ctf_n", ctf_n)
					print("voterE", voterE)
					print("voterN", voterN)

					if (d, N) in voted.keys() and voted[(d, N)]:
						conn.sendall(b"You have already voted!")
						continue

					signedBlindMessage_temp = signature(message, d, N)
					signedBlindMessage = pow(signedBlindMessage_temp, ctf_d, ctf_n)
					to_send = '{"signedBlindMessage": "' + str(signedBlindMessage) + '"}'
					conn.sendall(to_send.encode())
					recv = conn.recv(4096).decode()
					data = json.loads(recv)
					unBlindedSignedMessage = int(data["unBlindedSignedMessage"])
					r = int(data["r"])
					vote_val = verify(unBlindedSignedMessage, r, e, N)

					print(vote_val)
					if vote_val >= 1 and vote_val <= 10:
						if vote_val in votesTally.keys():
							votesTally[vote_val] += 1
						else:
							votesTally[vote_val] = 1
						conn.sendall(b"Vote registered!")
						voted[(d, N)] = True
					else:
						conn.sendall(b"Vote value not legit or corrupted")
				else:
					conn.sendall(b"Voter not registered!")

			elif data["choice"] == "results":
				data_string = json.dumps(votesTally)
				conn.sendall(data_string.encode())

		except Exception as e:
			print(e)
			sys.exit()

host = 'localhost'
port = 8080
address = (host, port)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(address)
server_socket.listen(5)

# Can be multithreaded
print("Listening for client . . .")
# conn, address = server_socket.accept()

while True:
	conn, addr = server_socket.accept()
	print("Connected to client at ", addr)
	_thread.start_new_thread(logic, (conn, addr))

server_socket.close()