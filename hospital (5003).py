import datetime
import hashlib
import json
from flask import Flask, jsonify, request, render_template, url_for, redirect
import requests
from uuid import uuid4
from urllib.parse import urlparse

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_block(proof = 1, previous_hash = '0', name = '', curp = '')
        self.nodes = set()
        self.total_citas = 0

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        max_citas = self.total_citas
        for node in network:
            try:
                response = requests.get(f'http://{node}/get_chain')
                if response.status_code == 200:
                    r = response.json()
                    length = r['length']
                    chain = r['chain']
                    total_citas = r['cont_citas']
                    if length > max_length and self.is_chain_valid(chain):
                        max_length = length
                        longest_chain = chain
                        max_citas = total_citas
                    elif length == max_length and total_citas > max_citas and self.is_chain_valid(chain):
                        longest_chain = chain
                        max_citas = total_citas

            except requests.exceptions.RequestException:
                print(f"El nodo {node} esta desconectado")



        if longest_chain:
            self.chain = longest_chain
            self.total_citas = max_citas
            return True
        return False

    def none_repited(self, new_block):
        block_index = 1
        while block_index < len(self.chain):
            block = self.chain[block_index]
            if(block['curp'] == new_block['curp']):
                return False
            block_index += 1
        return True

    def create_block(self, proof, previous_hash, name, curp):
        citas = []
        block = {'index': len(self.chain)+1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'citas': citas,
                 'name': name,
                 'curp' : curp}
        if self.none_repited(block):
            self.chain.append(block)
            return True
        else:
            return False

    def add_cita(self, curp, date):

        block_index = 1
        while block_index < len(self.chain):
            block = self.chain[block_index]
            if (block['curp'] == curp):
                block['citas'].append({
                    'fecha':date
                })
                self.total_citas += 1
                return True
            block_index += 1
        return False


    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operatio = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operatio[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True



app = Flask(__name__)

node_addres = str(uuid4()).replace('-','')

blockchain = Blockchain()

@app.route('/mine_block', methods=['POST', 'GET'])
def mine_block():
    if request.method == 'POST':
        previous_block = blockchain.get_previous_block()
        previous_proof = previous_block['proof']
        proof = blockchain.proof_of_work(previous_proof)
        previous_hash = blockchain.hash(previous_block)
        name = request.form['nombre']
        curp= request.form['curp']
        valid = blockchain.create_block(proof, previous_hash, name, curp)

        if(valid):
            return redirect(url_for('home'))
        else:
            return redirect(url_for('error'))


@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain':blockchain.chain,
                'length':len(blockchain.chain),
                'cont_citas':blockchain.total_citas}
    return jsonify(response), 200


@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid=blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message':'Todo good, todo verde'}
    else:
        response = {'message': 'No chavo, no esta bien'}

    return jsonify(response), 200


@app.route('/add_cita', methods=['GET', 'POST'])
def add_cita():
    if request.method == 'POST':
        fecha = request.form['fecha']
        curp = request.form['curp']
        valid = blockchain.add_cita(curp, fecha)
        if valid:
            return redirect(url_for('home'))
        else:
            return redirect(url_for('error2'))


@app.route('/connect_node', methods = ['GET'])
def connect_node():
    json = {"nodes": ["http://127.0.0.1:5000",
                      "http://127.0.0.1:5001",
                      "http://127.0.0.1:5002",
                      "http://127.0.0.1:5004"]}
    nodes = json.get('nodes')
    if nodes is None:
        return 'No node', 401
    for node in nodes:
        blockchain.add_node(node)
    return redirect(url_for('home'))


@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message':'Los nodos tenian diferentes cadenas, por lo que sa cambio a la mas larga',
                    'new_chain':blockchain.chain}
    else:
        response = {'message': 'Todo bien, la cadena es la mas larga',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200


@app.route('/home', methods=['GET'])
def home():
    blockchain.replace_chain()
    return render_template('index.html')


@app.route('/')
def root():
    return redirect(url_for('connect_node'))


@app.route('/Registro')
def registro():
    blockchain.replace_chain()
    return render_template('Registro.html')

@app.route('/Consulta')
def consulta():
    blockchain.replace_chain()
    return render_template('Consulta.html')

@app.route('/error')
def error():
    return render_template('errorCurpRep.html')

@app.route('/error2')
def error2():
    return render_template('errorCurpNotFound.html')

app.run(host='0.0.0.0', port='5003')