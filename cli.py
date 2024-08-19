import asyncio
import cv2
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.signaling import TcpSocketSignaling
from multiprocessing import Process, Queue

def process_a(frame_queue):
    """Process to handle received frames."""
    while True:
        frame = frame_queue.get()
        if frame is None:
            break
        cv2.imshow('Received Video', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()

async def run_client():
    signaling = TcpSocketSignaling('localhost', 1234)
    await signaling.connect()

    pc = RTCPeerConnection()

    frame_queue = Queue()
    p = Process(target=process_a, args=(frame_queue,))
    p.start()

    @pc.on('track')
    async def on_track(track):
        print("Track received")
        if track.kind == 'video':
            while True:
                frame = await track.recv()
                img = frame.to_ndarray(format='bgr24')
                frame_queue.put(img)
                #cv2.imshow('Received Video', img)
                #if cv2.waitKey(1) & 0xFF == ord('q'):
                #    break

            #cv2.destroyAllWindows()

    offer = await signaling.receive()
    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    await signaling.send(pc.localDescription)

    # Wait for the connection to be established
    while pc.iceConnectionState != 'connected':
        await asyncio.sleep(1)

    print("Connection established")

    # Keep the client running
    await pc.close()

if __name__ == '__main__':
    asyncio.run(run_client())