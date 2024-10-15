from pynq import Overlay

# Load the overlay
overlay = Overlay("/home/xilinx/IP/design_2.bit")

# DMA objects
dma = overlay.axi_dma_0