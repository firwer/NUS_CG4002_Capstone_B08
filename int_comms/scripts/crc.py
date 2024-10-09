def generate_crc8_table(poly):
    table = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
            crc &= 0xFF  # Ensure crc is 8-bit
        table.append(crc)
    return table

# Example: Using the standard CRC-8 polynomial (0x07)
crc8_poly = 0x07
crc8_table = generate_crc8_table(crc8_poly)

# Print the generated lookup table
print(", ".join(f"0x{val:02X}" for val in crc8_table))
