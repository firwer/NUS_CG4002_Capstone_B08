# overlay.py
from pynq import Overlay, allocate
from pynq import PL
import numpy as np
from sklearn.preprocessing import StandardScaler
import pandas as pd
from ast import literal_eval


class AIInference:
    def __init__(self):
        PL.reset()
        self.overlay = Overlay("/home/xilinx/IP/design_3.bit")
        self.dma = self.overlay.axi_dma_0
        self.dma_send = self.dma.sendchannel
        self.dma_recv = self.dma.recvchannel
        self.hls = self.overlay.predict_0
        self.hls.write(0x0, 0x81)  # Start the HLS IP

        # Load and fit the scaler
        df = pd.read_csv('/home/xilinx/IP/combined_2.csv', converters={
            'ax': literal_eval, 'ay': literal_eval, 'az': literal_eval,
            'gx': literal_eval, 'gy': literal_eval, 'gz': literal_eval
        })
        X_combined = [ax + ay + az + gx + gy + gz for ax, ay, az, gx, gy, gz in zip(
            df['ax'], df['ay'], df['az'], df['gx'], df['gy'], df['gz'])]
        max_length = max(len(seq) for seq in X_combined)
        X_padded = np.array([np.pad(seq, (0, max_length - len(seq)), 'constant') for seq in X_combined])
        X_padded = X_padded.reshape((X_padded.shape[0], -1))

        self.scaler = StandardScaler()
        self.scaler.fit(X_padded)

    def predict(self, combined_input):
        # Pad the input
        padded_input = np.pad(combined_input, (0, 360 - len(combined_input)), 'constant')
        scaled_input = self.scaler.transform([padded_input])

        # Allocate buffers
        input_buffer = allocate(shape=(360,), dtype=np.float32)
        output_buffer = allocate(shape=(7,), dtype=np.float32)

        # Fill the input buffer
        input_buffer[:] = scaled_input[0]

        # Perform DMA transfer
        self.dma_send.transfer(input_buffer)
        self.dma_recv.transfer(output_buffer)
        self.dma_send.wait()
        self.dma_recv.wait()

        # Get the prediction
        predicted_label = int(np.argmax(output_buffer))

        # Clean up
        input_buffer.close()
        output_buffer.close()

        return predicted_label
