import asyncio
import cv2
import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.signaling import TcpSocketSignaling
import av
import random

class BouncingBallTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.width = 640
        self.height = 480
        self.ball_radius = 20
        self.ball_pos = [self.width // 2, self.height // 2]
        self.ball_velocity = [random.randint(1, 5), random.randint(1, 5)]

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        # Create a blank image
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Update ball position
        for i in range(2):
            self.ball_pos[i] += self.ball_velocity[i]
            if self.ball_pos[i] < self.ball_radius or self.ball_pos[i] > (self.width if i == 0 else self.height) - self.ball_radius:
                self.ball_velocity[i] = -random.randint(1, 5)

        if self.ball_pos[0] <= self.ball_radius: self.ball_velocity[0] = random.randint(1, 5)
        elif self.ball_pos[0] >= self.width - self.ball_radius: self.ball_velocity[0] = -1*random.randint(1, 5)

        if self.ball_pos[1] <= self.ball_radius: self.ball_velocity[1] = random.randint(1, 5)
        elif self.ball_pos[1] >= self.width - self.ball_radius: self.ball_velocity[1] = -1*random.randint(1, 5)

        # Draw the ball
        cv2.circle(frame, tuple(self.ball_pos), self.ball_radius, (0, 255, 0), -1)

        # Create a video frame
        video_frame = av.VideoFrame.from_ndarray(frame, format='bgr24')
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame

async def run_server():
    signaling = TcpSocketSignaling('localhost', 1234)
    await signaling.connect()

    pc = RTCPeerConnection()
    pc.addTrack(BouncingBallTrack())

    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    await signaling.send(pc.localDescription)

    answer = await signaling.receive()
    await pc.setRemoteDescription(answer)

    # Wait for the connection to be established
    while pc.iceConnectionState != 'connected':
        await asyncio.sleep(1)

    print("Connection established")

    # Keep the server running
    await pc.close()

if __name__ == '__main__':
    asyncio.run(run_server())