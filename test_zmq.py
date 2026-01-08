"""Test ZMQ asyncio on Windows"""
import asyncio
import sys

# Set event loop policy FIRST
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import zmq
import zmq.asyncio

async def test_server():
    ctx = zmq.asyncio.Context()
    router = ctx.socket(zmq.ROUTER)
    router.bind("tcp://127.0.0.1:15555")
    print("Server bound to tcp://127.0.0.1:15555")

    print("Waiting for message...")
    try:
        frames = await asyncio.wait_for(router.recv_multipart(), timeout=5.0)
        print(f"Received: {frames}")
    except asyncio.TimeoutError:
        print("Timeout waiting for message")

    router.close()
    ctx.term()

async def test_client():
    await asyncio.sleep(0.5)  # Wait for server

    ctx = zmq.asyncio.Context()
    dealer = ctx.socket(zmq.DEALER)
    dealer.setsockopt_string(zmq.IDENTITY, "test-client")
    dealer.connect("tcp://127.0.0.1:15555")
    print("Client connected")

    await asyncio.sleep(0.1)

    print("Sending message...")
    await dealer.send_multipart([b"", b"Hello"])
    print("Message sent")

    dealer.close()
    ctx.term()

async def main():
    print(f"Python: {sys.version}")
    print(f"ZMQ: {zmq.pyzmq_version()}")
    print(f"Event loop: {type(asyncio.get_event_loop())}")

    await asyncio.gather(test_server(), test_client())

if __name__ == "__main__":
    asyncio.run(main())
