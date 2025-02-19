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


async def propagate(path: str, args: dict, ignore_url=None, nodes: list = None):
    global self_url
    self_node = NodeInterface(self_url or '')
    ignore_node = NodeInterface(ignore_url or '')
    aws = []
    for node_url in nodes or NodesManager.get_propagate_nodes():
        node_interface = NodeInterface(node_url)
        if node_interface.base_url == self_node.base_url or node_interface.base_url == ignore_node.base_url:
            continue
        aws.append(node_interface.request(path, args, self_node.url))
    for response in await gather(*aws, return_exceptions=True):
        print('node response: ', response)


@app.exception_handler(Exception)
async def exception_handler(request: Request, e: Exception):
    return JSONResponse(
        status_code=500,
        content={"ok": False, "error": f"Uncaught {type(e).__name__} exception"},
    )


@app.get("/add_node")
@limiter.limit("10/minute")
async def add_node(request: Request, url: str, background_tasks: BackgroundTasks):
    nodes = NodesManager.get_nodes()
    url = url.strip('/')
    if url == self_url:
        return {'ok': False, 'error': 'Recursively adding node'}
    if url in nodes:
        return {'ok': False, 'error': 'Node already present'}
    else:
        try:
            assert await NodesManager.is_node_working(url)
            background_tasks.add_task(propagate, 'add_node', {'url': url}, url)
            NodesManager.add_node(url)
            return {'ok': True, 'result': 'Node added'}
        except Exception as e:
            print(e)
            return {'ok': False, 'error': 'Could not add node'}


@app.get("/get_nodes")
async def get_nodes():
    return {'ok': True, 'result': NodesManager.get_recent_nodes()[:100]}


@app.get("/get_difficulty")
@limiter.limit("2/second")
async def get_difficulty(request: Request, block_hash: str):
    try:
        diff = Database.get_difficulty(block_hash)
        return {'ok': True, 'result': f"{diff}"}
    except Exception as err:
        print(err)
        return {'ok': False, 'result': f"Block is not in the chain"}

@app.get("/eth_blockNumber")
async def eth_block_number(request: Request):
    try:
        Chain = Database.import_blocks()
        return JSONResponse(content={"jsonrpc": "2.0", "id": 1, "result": hex(len(Chain.blocks)-1)})
    except Exception as e:
        print(e)
        return JSONResponse(content={"jsonrpc": "2.0", "id": 1, "error": "Could not retrieve block number"})
        
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

@app.get("/add_block")
@limiter.limit("30/minute")
async def add_new_block(request: Request, new_block: str):
    try:
        add_block_try = Database.add_block(block.createFromJSON(new_block))
        if add_block_try:
            return {'ok': True, 'result': "Block added"}
        elif add_block_try is False:
            return {'ok': False, 'result': 'Transaction not created'}
    except Exception as err:
        print(err)
        return {'ok': False, 'result': f'Block not added {err}'}
    return {'ok': True, 'result': "Block added"}


@app.get("/add_transaction")
@limiter.limit("2/second")
async def add_transaction(request: Request, pending_transaction: str):
    try:
        tx = Database.add_pending_transactions(pending_transaction_file, pending_transaction)
    except Exception as err:
        print(err)
        return {'ok': False, 'result': 'Transaction not created'}
    if tx[0] is False:
        return {'ok': False, 'result': 'Transaction not created'}
    if tx[0] is True:
        return {'ok': True, 'result': "Transaction added to pending transactions"}


@app.get("/get_transaction")
@limiter.limit("2/second")
async def get_transaction(request: Request, tx_hash: str):
    tx = await Database.get_transaction(tx_hash)
    if tx is None:
        return {'ok': False, 'error': 'Transaction not found'}
    return {'ok': True, 'result': tx}


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
