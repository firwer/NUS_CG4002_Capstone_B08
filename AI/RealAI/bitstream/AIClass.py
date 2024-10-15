from pynq import Overlay, allocate
from pynq import PL 
import numpy as np
import pandas as pd
import time
from sklearn.preprocessing import StandardScaler
from ast import literal_eval

class AI:
    def __init__(self):
        PL.reset()
        scaler_time = time.time()

        # Load and preprocess the dataset
        file_path = '/home/xilinx/IP/combined_2.csv'
        df = pd.read_csv(file_path, converters={'ax': literal_eval, 'ay': literal_eval, 'az': literal_eval,
                                                'gx': literal_eval, 'gy': literal_eval, 'gz': literal_eval})

        # Combine ax, ay, az, gx, gy, gz columns into a single feature list
        X_combined = [ax + ay + az + gx + gy + gz for ax, ay, az, gx, gy, gz in zip(df['ax'], df['ay'], df['az'], 
                                                                                     df['gx'], df['gy'], df['gz'])]

        # Pad sequences to the max length
        max_length = max(len(sequence) for sequence in X_combined)
        X_padded = np.array([np.pad(sequence, (0, max_length - len(sequence)), 'constant') for sequence in X_combined])
        X_padded = X_padded.reshape((X_padded.shape[0], -1))
        
        # Scale features and store scaler
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X_padded)
        print(f"Scaler time: {((time.time() - scaler_time) * 1000):.4f} ms\n")

        # Load the overlay
        overlay = Overlay("/home/xilinx/IP/design_3.bit")

        # DMA objects
        self.dma = overlay.axi_dma_0
        self.dma_send = self.dma.sendchannel
        self.dma_recv = self.dma.recvchannel

        # HLS object
        self.hls = overlay.predict_0
        CONTROL_REGISTER = 0x0
        self.hls.write(CONTROL_REGISTER, 0x81)  # Starts the HLS IP

    def predict(self, input):
      input_buffer = allocate(shape=(360,), dtype=np.float32)
      output_buffer = allocate(shape=(7,), dtype=np.float32)
      padded_input = np.pad(input, (0, 360 - len(input)), 'constant')
      
      # Use the stored scaler to transform the input
      scaled_input = self.scaler.transform([padded_input])
      for i in range(360):
         input_buffer[i] = scaled_input[0][i]
       
      start_time = time.time()
      self.dma_send.transfer(input_buffer)
      self.dma_recv.transfer(output_buffer)
      self.dma_send.wait()
      self.dma_recv.wait()
   
      # Output the result from DMA
      print(f"Float values:{output_buffer}")
      max_idx = 0
      max_val = output_buffer[0]
      for i in range(1, 7):
         if output_buffer[i] > max_val:
            max_val = output_buffer[i]  
            max_idx = i

       #print("Input Buffer (Sent Data):", input_buffer)
      print(f"Predicted Gesture: {max_idx}")
      print(f"Inference time: {((time.time() - start_time) * 1000):.4f} ms\n")

      # Clean up
      input_buffer.close()
      output_buffer.close()

