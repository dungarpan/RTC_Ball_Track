import asyncio
import cv2
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.signaling import TcpSocketSignaling
from multiprocessing import Process, Queue, Value
import numpy as np

def process_a(frame_queue, x_value, y_value):
    """Process to handle received frames."""
    while True:
        frame = frame_queue.get()
        if frame is None:
            break

        # Convert frame to HSV color space for color detection
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Define the color range for detecting the ball (green in this case)
        lower_green = np.array([40, 70, 70])
        upper_green = np.array([80, 255, 255])

        # Create a mask for the green color
        mask = cv2.inRange(hsv_frame, lower_green, upper_green)

        # Find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Find the largest contour
            largest_contour = max(contours, key=cv2.contourArea)

            # Get the bounding box of the largest contour
            x, y, w, h = cv2.boundingRect(largest_contour)

            # Calculate the center of the bounding box
            center_x = x + w // 2
            center_y = y + h // 2
            print(center_x,center_y)

            # Update the shared values
            x_value.value = center_x
            y_value.value = center_y

            # Draw the bounding box and center on the frame
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)

        cv2.imshow('Received Video', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()

async def run_client():
    signaling = TcpSocketSignaling('localhost', 1234)
    await signaling.connect()

    pc = RTCPeerConnection()

    frame_queue = Queue()
    x_value = Value('i', 0)
    y_value = Value('i', 0)
    p = Process(target=process_a, args=(frame_queue,x_value,y_value))
    p.start()

    @pc.on('track')
    async def on_track(track):
        print("Track received")
        if track.kind == 'video':
            while True:
                frame = await track.recv()
                img = frame.to_ndarray(format='bgr24')
                frame_queue.put(img)


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