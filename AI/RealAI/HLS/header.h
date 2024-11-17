#ifndef PREDICT_H
#define PREDICT_H

#include <hls_stream.h>
#include <ap_axi_sdata.h>

// Define ap_axis type for use in the function declaration
typedef float fixed_point;
typedef hls::axis<fixed_point, 2, 5, 6> axis_float_t;

#define INPUT 300
#define HIDDEN1 128
#define HIDDEN2 64
#define OUTPUT 11
#define LEGOUTPUT 3

// Declare the predict function (prototyping)
void predict(hls::stream<axis_float_t> &input_stream, hls::stream<axis_float_t> &output_stream);

#endif
