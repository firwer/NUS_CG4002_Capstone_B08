#include <iostream>
#include "hls_stream.h"
#include "ap_axi_sdata.h"
#include "header.h"
#include <stdio.h>

typedef ap_axis<32, 2, 5, 6> axis_t;

int main()
{
	axis_t read_output;
	hls::stream<axis_t> input_stream;
	hls::stream<axis_t> output_stream;
	float input[784] = {
		    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
		    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
		    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
		    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
		    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
		    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 10, 17, 17, 17, 17, 81,
		    180, 180, 35, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 139, 253, 253, 253,
		    253, 253, 253, 253, 48, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 60, 228, 253, 253,
		    253, 253, 253, 253, 253, 207, 197, 46, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 213, 253,
		    253, 253, 253, 253, 253, 253, 253, 253, 253, 223, 52, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
		    66, 231, 253, 253, 253, 108, 40, 40, 115, 244, 253, 253, 134, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
		    0, 0, 0, 63, 114, 114, 114, 37, 0, 0, 0, 205, 253, 253, 253, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
		    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 57, 253, 253, 253, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
		    0, 0, 0, 0, 0, 0, 0, 0, 0, 42, 253, 253, 253, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
		    0, 0, 0, 0, 0, 0, 0, 95, 253, 253, 253, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
		    0, 0, 0, 0, 0, 205, 253, 253, 253, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
		    61, 99, 96, 0, 0, 45, 224, 253, 253, 195, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 11, 25, 105, 83, 189,
		    189, 228, 253, 251, 189, 189, 218, 253, 253, 210, 27, 0, 0, 0, 0, 0, 0, 0, 0, 0, 42, 116, 173,
		    253, 253, 253, 253, 253, 253, 253, 253, 253, 253, 253, 221, 116, 7, 0, 0, 0, 0, 0, 0, 0, 0, 118,
		    253, 253, 253, 253, 245, 212, 222, 253, 253, 253, 253, 253, 253, 253, 253, 253, 160, 15, 0, 0,
		    0, 0, 0, 0, 0, 0, 254, 253, 253, 253, 189, 99, 0, 32, 202, 253, 253, 253, 240, 122, 122, 190,
		    253, 253, 253, 174, 0, 0, 0, 0, 0, 0, 0, 0, 255, 253, 253, 253, 238, 222, 222, 222, 241, 253,
		    253, 230, 70, 0, 0, 17, 175, 229, 253, 253, 0, 0, 0, 0, 0, 0, 0, 0, 158, 253, 253, 253, 253, 253,
		    253, 253, 253, 205, 106, 65, 0, 0, 0, 0, 0, 62, 244, 157, 0, 0, 0, 0, 0, 0, 0, 6, 26, 179, 179,
		    179, 179, 179, 30, 15, 10, 0, 0, 0, 0, 0, 0, 0, 0, 14, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
		    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
		};

    for (int i = 0; i < 784; ++i) {
     axis_t input_value;

     input_value.data = input[i];

     if (i != 143) {
      input_value.last = 0;
     } else {
      input_value.last = 1;
     }
        input_stream.write(input_value);

    }

    predict(input_stream, output_stream);
    read_output = output_stream.read();
    printf("Predicted Number: %d\n", (int)read_output.data);
	return 0;
}
