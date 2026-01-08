"""Test ZMQ client in separate process"""
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import zmq
import zmq.asyncio

async def main():
    print(f"Event loop: {type(asyncio.get_event_loop()).__name__}")

    ctx = zmq.asyncio.Context()
    dealer = ctx.socket(zmq.DEALER)
    dealer.setsockopt_string(zmq.IDENTITY, "test-worker")
    dealer.connect("tcp://127.0.0.1:15556")
    print("Client connected to tcp://127.0.0.1:15556")

    await asyncio.sleep(0.5)

    print("Sending message...")
    await dealer.send_multipart([b"", b'{"type": "REGISTER", "batch_id": "test-worker"}'])
    print("Message sent, waiting for ACK...")

    frames = await dealer.recv_multipart()
    print(f"Received ACK: {frames}")

    dealer.close()
    ctx.term()

if __name__ == "__main__":
    asyncio.run(main())
