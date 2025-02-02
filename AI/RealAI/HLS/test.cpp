#include <iostream>
#include "hls_stream.h"
#include "ap_axi_sdata.h"
#include "header.h"
#include <stdio.h>

typedef float fixed_point;
typedef hls::axis<fixed_point, 2, 5, 6> axis_float_t;

int main()
{
	hls::stream<axis_float_t> input_stream;
	hls::stream<axis_float_t> output_stream;

	fixed_point input[INPUT + 1] = {1, 1.1035,  1.8167,  0.6777,  1.2907,  1.1758,  1.4840,  1.3372,  1.4948,
	          1.1197,  0.7843,  0.5980,  0.3061,  0.0917, -0.0314, -0.1807, -0.3744,
	         -0.6492, -0.0410,  0.3061,  0.7926,  0.8551,  1.0964,  1.1916,  1.1797,
	          1.0058,  0.6440,  0.4009,  0.5572,  0.7405,  0.7702,  0.7662,  0.8558,
	          0.9167,  0.9421,  0.9217,  0.9532,  0.9528,  0.9433,  0.9110,  0.8862,
	          0.8953,  0.8873,  0.8883,  0.9231,  0.9097,  0.9063,  0.9030,  0.9053,
	          0.9189,  0.9176, -0.6529, -0.2204,  0.4579, -0.0770, -0.1640,  0.4926,
	          0.3067,  0.4036,  0.1775,  0.4077,  0.7333,  1.0142,  0.8956,  0.4656,
	          0.4117,  0.5739, -0.0894,  2.1891, -0.0598,  0.7017,  0.2234,  0.2759,
	          0.1141,  0.1589,  0.6928,  0.8342, -0.3510,  0.1796,  0.2814, -0.0847,
	         -0.2385,  0.2171,  0.4603,  0.5078,  0.4068,  0.4540,  0.4056,  0.4925,
	          0.4106,  0.4119,  0.4848,  0.4830,  0.4613,  0.4715,  0.5259,  0.5827,
	          0.5128,  0.6356,  0.6012,  0.6079, -1.2110,  0.3599,  0.5593,  0.0206,
	          0.2454,  0.1332,  0.0317, -0.0375,  0.4843,  0.3992,  0.1654,  0.1261,
	          0.6120,  1.1939,  1.0934,  0.6786,  0.3504,  2.1729,  2.1115,  1.8649,
	          1.5630,  1.3564,  1.5128,  1.6417,  1.9050, -0.2425, -0.0149, -0.1059,
	          0.0184,  0.0836,  0.1694,  0.2837,  0.3478,  0.4398,  0.4732,  0.4796,
	          0.4531,  0.4143,  0.3265,  0.3377,  0.3544,  0.3441,  0.4474,  0.5210,
	          0.5525,  0.6871,  0.6163,  0.6967,  0.8191,  0.9431, -0.5387,  1.3515,
	         -0.1714, -1.0712, -1.2322, -0.9400, -0.5999, -0.2122, -0.0328,  0.2882,
	          0.6998,  0.2723, -0.4474, -0.7240, -0.5457,  0.2600,  0.8486,  1.3478,
	          0.0416,  0.5675,  0.0612, -0.1885, -0.2877, -0.1351, -0.2490, -0.6336,
	         -0.5617, -0.1960, -0.2109, -0.0782, -0.0699, -0.1530, -0.0971,  0.1047,
	          0.1492,  0.1152,  0.0278,  0.0973,  0.0842,  0.1176,  0.0174, -0.0530,
	         -0.1193, -0.1433, -0.1233, -0.2147, -0.2955, -0.2193, -0.1815, -0.2034,
	         -0.6777, -0.1329,  0.8012,  0.4712,  0.1335, -0.3501, -0.5417, -0.3984,
	         -0.1399,  0.4768,  1.0969,  1.6679,  2.1522,  2.1944,  2.1992,  2.0890,
	          1.8474,  1.6298,  1.2387,  0.8706,  0.5762,  0.2912, -0.0692, -0.4736,
	         -0.9629, -0.8259, -0.8645, -0.5013, -0.2579, -0.0025,  0.2649,  0.3792,
	          0.4324,  0.4357,  0.3935,  0.3268,  0.2139,  0.0756, -0.0797, -0.2556,
	         -0.4071, -0.5487, -0.6408, -0.7306, -0.7834, -0.8458, -0.9854, -1.1245,
	         -1.1079, -1.0966, -0.4330, -0.2729, -0.1073, -0.2323,  0.1133,  0.1652,
	          0.1285,  0.2925,  0.0766,  0.1914,  0.3321,  0.1260,  0.0563,  0.0974,
	          0.2140,  0.0994, -0.4779, -0.6440, -1.1440, -0.6316, -0.3160, -0.0321,
	          0.1947,  0.3663,  0.7598,  1.2573,  0.4065,  0.1331, -0.1584, -0.3245,
	         -0.2930, -0.3187, -0.3654, -0.3223, -0.3028, -0.2553, -0.2279, -0.1338,
	         -0.0433,  0.1409,  0.1959,  0.1768,  0.1880,  0.2776,  0.2708,  0.2991,
	          0.2730,  0.3792,  0.4311,  0.4440};

	axis_float_t input_value;
    for (int i = 0; i < INPUT + 1; ++i) {
     input_value.data = input[i];
     if (i != 300) {
      input_value.last = 0;
     } else {
      input_value.last = 1;
     }
        input_stream.write(input_value);
    }

    predict(input_stream, output_stream);

    axis_float_t out;
    float output_data[LEGOUTPUT];

    for (int j = 0; j < LEGOUTPUT; j++){
    	output_stream.read(out);
    	output_data[j] = out.data;
    }
    int max_idx = 0;
    float max_val = output_data[0];
    printf("value: %f\n", max_val);
    for (int j = 1; j < LEGOUTPUT; j++) {
    	if (output_data[j] > max_val)
    	{
    		max_val = output_data[j];
    		max_idx = j;
    	}
    	printf("value: %f\n", output_data[j]);
    }

    printf("Predicted Number: %d\n", max_idx);
	return 0;
}
