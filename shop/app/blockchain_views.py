from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from web3 import Web3
from django.views.decorators.csrf import csrf_exempt
from .models import Product, User, Loan, Sale, CompanyWallet
import json

# Blockchain setup
web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))  # Update with your provider
contract_address = "0x0fC5025C764cE34df352757e82f7B5c4Df39A836"  # Replace with your deployed contract address
contract_abi = [
    {
        "inputs": [],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "buyer",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "productId",
                "type": "uint256"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "price",
                "type": "uint256"
            }
        ],
        "name": "ProductBought",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "sender",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "receiver",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256"
            }
        ],
        "name": "PaymentMade",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "user",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "balance",
                "type": "uint256"
            }
        ],
        "name": "BalanceChecked",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "user",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256"
            }
        ],
        "name": "FundsDeposited",
        "type": "event"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "depositFunds",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "_name",
                "type": "string"
            },
            {
                "internalType": "uint256",
                "name": "_price",
                "type": "uint256"
            }
        ],
        "name": "addProduct",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "_productId",
                "type": "uint256"
            }
        ],
        "name": "buyProduct",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "_to",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "_amount",
                "type": "uint256"
            }
        ],
        "name": "makePayment",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "checkBalance",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]



contract = web3.eth.contract(address=contract_address, abi=contract_abi)

# ---------------------------- Render Payment Page ---------------------------- #
def payment_page(request):
    return render(request, 'payment.html')

# ---------------------------- Check Balance ---------------------------- #
    
# ---------------------------- Make Payment ---------------------------- #
@csrf_exempt
def make_transaction(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            sender_address = Web3.to_checksum_address(data.get("sender"))
            receiver_address = Web3.to_checksum_address(data.get("receiver"))
            amount = int(data.get("amount"))

            # Get nonce
            nonce = web3.eth.get_transaction_count(sender_address)

            # Build the transaction
            tx = contract.functions.makePayment(receiver_address, amount).build_transaction({
                'from': sender_address,
                'gas': 2000000,
                'gasPrice': web3.to_wei(50, 'gwei'),
                'nonce': nonce,
            })

            # Sign the transaction (Replace with actual private key handling)
            private_key = "0xYourPrivateKey"  # Replace with actual key securely
            signed_tx = web3.eth.account.sign_transaction(tx, private_key)

            # Send transaction
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

            return JsonResponse({"message": "Transaction initiated", "tx_hash": web3.to_hex(tx_hash)})

        except Exception as e:
            return JsonResponse({"error": f"Failed to make payment: {str(e)}"}, status=500)

# ---------------------------- Buy Product ---------------------------- #
@csrf_exempt
def buy_product(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            buyer_address = data.get("buyer")
            product_id = int(data.get("product_id"))

            if not buyer_address or not Web3.is_address(buyer_address):
                return JsonResponse({"error": "Invalid buyer address"}, status=400)

            checksum_address = Web3.to_checksum_address(buyer_address)
            nonce = web3.eth.get_transaction_count(checksum_address)

            # Build transaction
            tx = contract.functions.buyProduct(product_id).build_transaction({
                'from': checksum_address,
                'gas': 2000000,
                'gasPrice': web3.to_wei(50, 'gwei'),
                'nonce': nonce,
            })

            private_key = "0xYourPrivateKey"  # Replace securely
            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

            return JsonResponse({"message": "Purchase initiated", "tx_hash": web3.to_hex(tx_hash)})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)