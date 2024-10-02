#ifndef PREDICT_H
#define PREDICT_H

#include <hls_stream.h>
#include <ap_axi_sdata.h>

// Define ap_axis type for use in the function declaration
typedef ap_axis<32, 2, 5, 6> axis_t;

// Declare the predict function (prototyping)
void predict(hls::stream<axis_t> &input_stream, hls::stream<axis_t> &output_stream);

#endif
