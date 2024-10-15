from pynq import Overlay, allocate
from pynq import PL
import numpy as np

PL.reset()
overlay = Overlay("/home/xilinx/IP/design_3.bit")

print(overlay.ip_dict.keys())

# DMA objects
dma = overlay.axi_dma_0
hls = overlay.predict_0
register_map = hls.register_map
print(register_map)