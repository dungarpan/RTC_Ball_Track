# RTC Ball Tracking

A WebRTC program to track a moving ball and return its actual coordinates. The server generates the OpenCV image of a ball moving around a rectangle randomly. After establishing the peer-to-peer connection, the client is sent this data through a Data channel. The client predicts the ball's location and returns it to the server.
