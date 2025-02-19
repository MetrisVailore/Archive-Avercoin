from asyncpg import UniqueViolationError
from fastapi import FastAPI, Body, Query
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse

from asyncio import gather
from httpx import TimeoutException
from icecream import ic
from starlette.background import BackgroundTasks, BackgroundTask
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from AverCoin.node.database import Database
from AverCoin.node.nodes_manager import NodesManager, NodeInterface
import AverCoin.blockchain.block as block
from settings import *

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
Database.init()
NodesManager.init()
started = False
is_syncing = False
self_url = None

print = ic

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Geth-like RPC method: eth_blockNumber
@app.get("/eth_blockNumber")
async def eth_block_number(request: Request):
    try:
        # Use Database to retrieve the latest block number instead of Web3
        latest_block = await Database.get_latest_block_number()
        return JSONResponse(content={"jsonrpc": "2.0", "id": 1, "result": hex(latest_block)})
    except Exception as e:
        print(e)
        return JSONResponse(content={"jsonrpc": "2.0", "id": 1, "error": "Could not retrieve block number"})

# Geth-like RPC method: eth_getBlockByNumber
@app.get("/eth_getBlockByNumber")
async def eth_get_block_by_number(request: Request, block_number: str, full_transactions: bool = False):
    try:
        block_info = await Database.get_block_by_number(int(block_number, 16), full_transactions)
        return JSONResponse(content={
            "jsonrpc": "2.0", "id": 1, "result": block_info
        })
    except Exception as e:
        print(e)
        return JSONResponse(content={"jsonrpc": "2.0", "id": 1, "error": "Could not retrieve block by number"})

# Geth-like RPC method: eth_getBlockByHash
@app.get("/eth_getBlockByHash")
async def eth_get_block_by_hash(request: Request, block_hash: str, full_transactions: bool = False):
    try:
        block_info = await Database.get_block_by_hash(block_hash, full_transactions)
        return JSONResponse(content={
            "jsonrpc": "2.0", "id": 1, "result": block_info
        })
    except Exception as e:
        print(e)
        return JSONResponse(content={"jsonrpc": "2.0", "id": 1, "error": "Could not retrieve block by hash"})

# Geth-like RPC method: eth_getTransactionByHash
@app.get("/eth_getTransactionByHash")
async def eth_get_transaction_by_hash(request: Request, tx_hash: str):
    try:
        # Retrieve transaction from the database
        tx = await Database.get_transaction(tx_hash)
        if tx is None:
            return JSONResponse(content={"jsonrpc": "2.0", "id": 1, "result": None})
        return JSONResponse(content={
            "jsonrpc": "2.0", "id": 1, "result": tx
        })
    except Exception as e:
        print(e)
        return JSONResponse(content={"jsonrpc": "2.0", "id": 1, "error": "Could not retrieve transaction"})

# Geth-like RPC method: eth_getTransactionReceipt
@app.get("/eth_getTransactionReceipt")
async def eth_get_transaction_receipt(request: Request, tx_hash: str):
    try:
        # Retrieve transaction receipt from the database
        receipt = await Database.get_transaction_receipt(tx_hash)
        if receipt is None:
            return JSONResponse(content={"jsonrpc": "2.0", "id": 1, "result": None})
        return JSONResponse(content={
            "jsonrpc": "2.0", "id": 1, "result": receipt
        })
    except Exception as e:
        print(e)
        return JSONResponse(content={"jsonrpc": "2.0", "id": 1, "error": "Could not retrieve transaction receipt"})

# Example of additional block and transaction management via the database (similar to Ethereum-like RPC)
@app.get("/get_block")
@limiter.limit("30/minute")
async def get_block(request: Request, block_hash: str):
    try:
        block_return = await Database.get_block(block_hash)
        if block_return is not None:
            return {'ok': True, 'result': block_return}
        else:
            return {'ok': False, 'error': 'Block not found'}
    except:
        return {'ok': False, 'error': 'Block not found'}

@app.get("/get_transaction")
@limiter.limit("2/second")
async def get_transaction(request: Request, tx_hash: str):
    try:
        tx = await Database.get_transaction(tx_hash)
        if tx is None:
            return {'ok': False, 'error': 'Transaction not found'}
        return {'ok': True, 'result': tx}
    except Exception as err:
        print(err)
        return {'ok': False, 'error': 'Transaction not found'}

# Continue with other methods for blocks, transactions, etc., as per your original needs

@app.get("/get_pending_transactions")
async def get_blocks(request: Request):
    transactions = await Database.get_pending_transactions()
    return {'ok': True, 'result': transactions}


@app.get("/get_block")
@limiter.limit("30/minute")
async def get_block(request: Request, block_hash: str):
    try:
        block_return = await Database.get_block(block_hash)
        if block_return is not None:
            return {'ok': True, 'result': block_return}
        else:
            return {'ok': False, 'error': 'Block not found'}
    except:
        return {'ok': False, 'error': 'Block not found'}


@app.get("/get_json_blocks")
@limiter.limit("35/minute")
async def get_json_blocks(request: Request):
    try:
        Chain = Database.import_blocks()
        return Chain.blocks
    except Exception as err:
        print(err)
        return {'ok': False, 'error': 'Error is occurred'}


@app.get("/get_last_index")
async def get_last_index(request: Request):
    try:
        Chain = Database.import_blocks()
        return len(Chain.blocks)-1
    except:
        return {'ok': False}


@app.get("/get_last_hash")
@limiter.limit("30/minute")
async def get_last_hash(request: Request):
    try:
        Chain = Database.import_blocks()
        hashes = []
        for blocks in Chain.blocks:
            hashes.append(blocks)
        return hashes[-1]
    except:
        return {'ok': False}


@app.get("/get_blocks")
@limiter.limit("10/minute")
async def get_blocks(request: Request, offset: int, limit: int = Query(default=..., le=1000)):
    blocks = await Database.get_blocks(offset, limit)
    return {'ok': True, 'result': blocks}
