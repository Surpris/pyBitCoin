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


# Step 4: Consensus
ブロックチェーンは非中央集権的でなくてはならない。   
ブロックチェーンを利用するすべての人が同じチェーンを反映しているということをどう確認するか、
それがブロックチェーンにおけるコンセンサスの問題である。   

## Register a new node
コンセンサスアルゴリズムを実装する前に、ネットワーク上にある他のノードを知る方法を作る。   
それぞれのノードがネットワーク上の他のノードのリストを持っていなければならない。   
なのでいくつかのエンドポイントが追加で必要となる。   

* URLの形での新しいノードのリストを受け取るための/nodes/register
* あらゆるコンフリクトを解消することで、ノードが正しいチェーンを持っていることを確認するための/nodes/resolve

## Implement consensus algorithm
以前言及したとおり、コンフリクトはあるノードが他のノードと異なったチェーンを持っているときに発生する。   
これを解決するために、最も長いチェーンが信頼できるというルールを作る。   
別の言葉で言うと、ネットワーク上で最も長いチェーンは事実上正しいものといえる。   
このアルゴリズムを使って、ネットワーク上のノード間でコンセンサスに到達する。
"""

import time
import json
import hashlib
from urllib.parse import urlparse
import requests

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set() # 同じノードを追加しても一度しか出現しないことを保証

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

    def register_node(self, address):
        """register_node(address) -> None
        ノードリストに新しいノードを加える
        :param address: <str> ノードのアドレス 例: 'http://192.168.0.5:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
    
    def valid_chain(self, chain):
        """valid_chain(data) -> bool
        ブロックチェーンが正しいかを確認する

        :param chain: <list> ブロックチェーン
        :return: <bool> True であれば正しく、 False であればそうではない
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print('{}'.format(last_block))
            print('{}'.format(block))
            print("\n--------------\n")

            # ブロックのハッシュが正しいかを確認
            if block['previous_hash'] != self.hash(last_block):
                return False

            # プルーフ・オブ・ワークが正しいかを確認
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """resolve_conflict() -> bool
        これがコンセンサスアルゴリズムだ。
        ネットワーク上の最も長いチェーンで自らのチェーンを
        置き換えることでコンフリクトを解消する。
        :return: <bool> 自らのチェーンが置き換えられると True 、そうでなれけば False
        """

        neighbours = self.nodes
        new_chain = None

        # 自らのチェーンより長いチェーンを探す必要がある
        max_length = len(self.chain)

        # 他のすべてのノードのチェーンを確認
        for node in neighbours:
            response = requests.get('http://{}/chain'.format(node))

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # そのチェーンがより長いか、有効かを確認
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # もし自らのチェーンより長く、かつ有効なチェーンを見つけた場合それで置き換える
        if new_chain:
            self.chain = new_chain
            return True

        return False

if __name__ == "__main__":
    blockchain = Blockchain()
    last_proof = 100
    st = time.time()
    print(blockchain.proof_of_work(last_proof))
    print("elapsed:", time.time() - st)