"""Test ZMQ server in separate process"""
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import zmq
import zmq.asyncio

async def main():
    print(f"Event loop: {type(asyncio.get_event_loop()).__name__}")

    ctx = zmq.asyncio.Context()
    router = ctx.socket(zmq.ROUTER)
    router.bind("tcp://127.0.0.1:15556")
    print("Server bound to tcp://127.0.0.1:15556")
    print("Waiting for messages (Ctrl+C to stop)...")

    while True:
        try:
            # Try NOBLOCK first
            try:
                frames = await router.recv_multipart(flags=zmq.NOBLOCK)
                print(f"Received: {frames}")

                # Send ACK
                identity = frames[0]
                await router.send_multipart([identity, b"", b'{"status": "ok"}'])
                print("ACK sent")
            except zmq.Again:
                await asyncio.sleep(0.05)
        except KeyboardInterrupt:
            break

    router.close()
    ctx.term()

if __name__ == "__main__":
    asyncio.run(main())
