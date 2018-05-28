#-*- coding: utf-8 -*-

"""
blockchain.py   

Reference: <https://qiita.com/hidehiro98/items/841ece65d896aeaa8a2a>   

# Step 1: Construct blockchain
## Write Blockchain class
ここで考えるBlockchainの設計図は次のようになっている。   

```python:blockchain.py
class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

    def new_block(self):
        # 新しいブロックを作り、チェーンに加える
        pass

    def new_transaction(self):
        # 新しいトランザクションをリストに加える
        pass

    @staticmethod
    def hash(block):
        # ブロックをハッシュ化する
        pass

    @property
    def last_block(self):
        # チェーンの最後のブロックをリターンする
        pass
```

## Structure of a block
それぞれのブロックは次のものを持っている。   

* インデックス
* タイムスタンプ（UNIXタイム）
* トランザクションのリスト
* プルーフ（詳細は後ほど）
* それまでの全てのブロックから生成されるハッシュ

blockの例：   
```json
block = {
    'index': 1,
    'timestamp': 1506057125.900785,
    'transactions': [
        {
            'sender': "8527147fe1f5426f9dd545de4b27ee00",
            'recipient': "a77f5cdfa2934df3954a5c7c7da5df1f",
            'amount': 5,
        }
    ],
    'proof': 324984774000,
    'previous_hash': "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
}
```
Blockはそれまでのblockのhash値を持っているがゆえに不変である。   
つまりblockのどれかのhashが改変されると、それまでのblockのhash値が不正となる。   

## Add a transaction to block
new_transaction()メソッドは、新しいトランザクションをリストに加えた後、
そのトランザクションが加えられるブロック（次に採掘されるブロック）のインデックスをリターンする。   

## Create a new block
Blockchainがインスタンス化されるとき、ジェネシスブロック（先祖を持たないブロック）とともにシードする必要がある。   
それと同時に、ジェネシスブロックにプルーフ（マイニングまたはプルーフ・オブ・ワークの結果）も加える必要がある。   

## Implement the proof-of-work method

"""

import time
import json
import hashlib

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # ジェネシスブロックを作る
        self.new_block(proof=100, previous_hash=1)

    def new_block(self, proof, previous_hash=None):
        """new_block(self, proof, previous_hash=None) -> block
        ブロックチェーンに新しいブロックを作る。
        blockも辞書形式で与える。

        :param proof: <int> プルーフ・オブ・ワークアルゴリズムから得られるプルーフ
        :param previous_hash: (オプション) <str> 前のブロックのハッシュ
        :return: <dict> 新しいブロック
        """

        block = {
            'index': len(self.chain) + 1, 
            'timestamp': time.time(), 
            'transactions': self.current_transactions, 
            'proof': proof, 
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # 現在のトランザクションリストをリセット
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """new_transaction(self, sender, recipient, amount) -> address of the last block
        次に採掘されるブロックに加える新しいトランザクションを作る。
        トランザクションは辞書形式で与えればよいみたい。

        :param sender: <str> 送信者のアドレス
        :param recipient: <str> 受信者のアドレス
        :param amount: <int> 量
        :return: <int> このトランザクションを含むブロックのアドレス
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """hash(block) -> hash(hex)
        ブロックの　SHA-256　ハッシュを作る
        :param block: <dict> ブロック
        :return: <str>
        """

        # 必ずディクショナリ（辞書型のオブジェクト）がソートされている必要がある。
        # そうでないと、一貫性のないハッシュとなってしまう
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        # チェーンの最後のブロックをリターンする
        return self.chain[-1]
    
    def proof_of_work(self, last_proof):
        """proof_of_work(self, last_proof) -> proof (integer)
        シンプルなプルーフ・オブ・ワークのアルゴリズム:   
        * hash(pp') の最初の4つが0となるような p' を探す
             + p は1つ前のブロックのプルーフ (last_proof)
             + p' は新しいブロックのプルーフ (prorf)

        :param last_proof: <int>
        :return: <int>
        """

        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """valid_proof(last_proof, proof) -> bool
        プルーフが正しいかを確認する: hash(last_proof, proof)の最初の4つが0となっているか？
        :param last_proof: <int> 前のプルーフ
        :param proof: <int> 現在のプルーフ
        :return: <bool> 正しければ true 、そうでなれけば false
        """

        guess = '{0}{1}'.format(last_proof, proof).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        return guess_hash[:4] == "0000"

if __name__ == "__main__":
    blockchain = Blockchain()
    last_proof = 100
    st = time.time()
    print(blockchain.proof_of_work(last_proof))
    print("elapsed:", time.time() - st)