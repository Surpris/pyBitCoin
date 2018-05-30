#-*- coding: utf-8 -*-

"""
blockchain.py   

Reference: <https://qiita.com/hidehiro98/items/841ece65d896aeaa8a2a>   

# Blockchain as an API
Flask を用いて、HTTPリクエストを使ってWebでブロックチェーンを通信できるようにする。   
実装するのは次の３つ。   

* ブロックへの新しいトランザクションを作るための/transactions/new
* サーバーに対して新しいブロックを採掘するように伝える/mine
* フルブロックチェーンを返す/chain

## Transaction endpoint
トランザクションのリクエストはつぎのようなもの。   
```json
{
 "sender": "my address",
 "recipient": "someone else's address",
 "amount": 5
}
```

## Endpoint of mining
マイニングのエンドポイントでは次の作業が行われる。   

1. プルーフ・オブ・ワークを計算する
2. 1コインを採掘者に与えるトランザクションを加えることで、採掘者（この場合は我々）に利益を与える
3. チェーンに新しいブロックを加えることで、新しいブロックを採掘する

# APIをたたく
`curl` か `Postman` を使うと、手軽にAPIをたたける。   

# Consensus
ブロックチェーンで重要な考え方である `コンセンサス` を扱う。
"""

import hashlib
import json
from textwrap import dedent
from time import time
from uuid import uuid4 # uuid = Universally Unique IDentifier

from flask import Flask, jsonify, request
from blockchain import Blockchain # chapter 1 で実装したもの


# ノードを作る
# Flaskについて詳しくはこちらを参照のこと 
# http://flask.pocoo.org/docs/0.12/quickstart/#a-minimal-application
app = Flask(__name__)

# このノードのグローバルにユニークなアドレスを作る
node_identifier = str(uuid4()).replace('-', '')

# ブロックチェーンクラスをインスタンス化する
blockchain = Blockchain()

# メソッドはPOSTで/transactions/newエンドポイントを作る。メソッドはPOSTなのでデータを送信する
@app.route('/transactions/new', methods=['POST'])
def new_transactions():
    values = request.get_json()
    print(values)

    # POSTされたデータに必要なデータがあるかを確認
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # 新しいトランザクションを作る
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message':'トランザクションはブロック {} に追加されました'.format(index)}
    return jsonify(response), 201

# メソッドはGETで/mineエンドポイントを作る
@app.route('/mine', methods=['GET'])
def mine():
    # 次のプルーフを見つけるためプルーフ・オブ・ワークアルゴリズムを使用する
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # プルーフを見つけたことに対する報酬を得る
    # 送信者は、採掘者が新しいコインを採掘したことを表すために"0"とする
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # チェーンに新しいブロックを加えることで、新しいブロックを採掘する
    block = blockchain.new_block(proof)

    response = {
        'message': '新しいブロックを採掘しました',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

# メソッドはGETで、フルのブロックチェーンをリターンする/chainエンドポイントを作る
@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_node():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: 有効ではないノードのリストです", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': '新しいノードが追加されました',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'チェーンが置き換えられました',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'チェーンが確認されました',
            'chain': blockchain.chain
        }

    return jsonify(response), 200
    
# localhost:5000でサーバーを起動する
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)