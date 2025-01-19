import hashlib, random
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_OAEP
from ecdsa import SigningKey, SECP256k1
from hashlib import sha256

P = 2 ** 256 - 2 ** 32 - 2 ** 9 - 2 ** 8 - 2 ** 7 - 2 ** 6 - 2 ** 4 - 1
G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
        0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


class AverWallet:
    def __init__(self):
        self.Wallet = self.Wallet()

    class Wallet():
        def __init__(self):
            self.addresses = []

        def ripemd160(self, x):
            d = hashlib.new("ripemd160")
            d.update(x)
            return d

        def point_add(self, p, q):
            xp, yp = p
            xq, yq = q

            if p == q:
                l = pow(2 * yp % P, P - 2, P) * (3 * xp * xp) % P
            else:
                l = pow(xq - xp, P - 2, P) * (yq - yp) % P

            xr = (l ** 2 - xp - xq) % P
            yr = (l * xp - l * xr - yp) % P

            return xr, yr

        def point_mul(self, p, d):
            n = p
            q = None

            for i in range(256):
                if d & (1 << i):
                    if q is None:
                        q = n
                    else:
                        q = self.point_add(q, n)

                n = self.point_add(n, n)

            return q

        def point_bytes(self, p):
            x, y = p
            return b"\x04" + x.to_bytes(32, "big") + y.to_bytes(32, "big")

        def b58_encode(self, d):
            out = ""
            p = 0
            x = 0

            while d[0] == 0:
                out += "1"
                d = d[1:]

            for i, v in enumerate(d[::-1]):
                x += v * (256 ** i)

            while x > 58 ** (p + 1):
                p += 1

            while p >= 0:
                a, x = divmod(x, 58 ** p)
                out += B58[a]
                p -= 1

            return out

        def make_address(self, privkey):
            q = self.point_mul(G, int.from_bytes(privkey, "big"))
            hash160 = self.ripemd160(sha256(self.point_bytes(q)).digest()).digest()
            addr = b"\x00" + hash160
            checksum = sha256(sha256(addr).digest()).digest()[:4]
            addr += checksum

            wif = b"\x80" + privkey
            checksum = sha256(sha256(wif).digest()).digest()[:4]
            wif += checksum

            addr = self.b58_encode(addr)
            wif = self.b58_encode(wif)

            return addr, wif

        def generate_keys(self):
            private_key = SigningKey.generate(curve=SECP256k1, hashfunc=sha256)
            public_key = private_key.get_verifying_key()
            # sig = private_key.sign(b"message")
            # print(public_key.verify(sig, b"message"))
            return public_key, private_key

        def importKey(self, externKey):
            return RSA.importKey(externKey)

        def getpublickey(self, priv_key):
            return priv_key.publickey()

        def encrypt(self, message, pub_key):
            # RSA encryption protocol according to PKCS#1 OAEP
            cipher = PKCS1_OAEP.new(pub_key)
            return cipher.encrypt(message)

        def decrypt(self, ciphertext, priv_key):
            # RSA encryption protocol according to PKCS#1 OAEP
            cipher = PKCS1_OAEP.new(priv_key)
            return cipher.decrypt(ciphertext)

        def sign(self, message, private_key):
            sig = private_key.sign(message)
            return sig

        def verify(self, message, signature, pub_key):
            return pub_key.verify(signature, message)
