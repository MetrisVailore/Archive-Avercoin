from AverCoin.blockchain import transaction
from Cryptodome.PublicKey import RSA
import time
private1 = RSA.generate(2048)
public1 = private1.publickey().exportKey('DER').hex()

tx1 = transaction.createTransaction(
            outputAddresses=[public1],
            outputAmounts=[int(1)],
            timestamp=time.time(),
            previousTransactionHashes=["a15d96f79c1d7175c7d5197133a6d9187d3ae3fe988665329b6ef728b9d4cab5"],
            previousOutputIndices=[1],
            privateKeys=[private1]
        )

tx2 = transaction.createTransaction(
            outputAddresses=[public1],
            outputAmounts=[int(1)],
            timestamp=time.time(),
            previousTransactionHashes=[tx1.hash],
            previousOutputIndices=[1],
            privateKeys=[private1]
        )

print(tx1)
print(tx2)
test_name = [tx1, tx2]
print(f"\n {test_name} \n")
print(type(test_name))