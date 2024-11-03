from AI50Class import AI

AImodel = AI()
basket_input = [-1870, -3117, 0, -1725, -1828, -1828, -1828, -1828, -1828, -1828, -1240, -1078, -1056, -982, -868, -758, -667, -504, -448, -355, -206, -49, 39, 109, 88, 111, 108, -1, -99, -192, -300, -335, -374, -806, -1201, -801, -542, -350, -239, -126, -97, -86, -79, -66, -34, -14, 22, 36, 16, -8,
               -151, -579, 0, 772, 129, 129, 129, 129, 129, 129, 137, 262, 420, 390, 461, 382, 314, 242, 145, 68, -77, -251, -382, -456, -362, -229, -165, -112, -59, 8, 98, 75, -80, -168, -745, -342, 243, -109, -299, -176, -108, -138, -86, -30, -25, -63, -125, -146, -85, -37,
               -1477, -1595, 0, 859, 619, 619, 619, 619, 619, 619, 449, 429, 528, 446, 339, 255, 19, -161, -374, -647, -848, -1006, -1069, -996, -880, -753, -642, -653, -477, -416, -335, -262, -145, -160, 776, 1229, 1114, 715, 581, 509, 488, 503, 496, 443, 374, 323, 283, 245, 179, 123,
               -7523, -9907, 0, -3564, -7668, -7668, -7668, -7668, -7668, -7668, 4956, 5113, 3592, 2881, 2080, -823, -3180, -4358, -3396, -2639, 145, 1580, 161, -239, 1477, 1522, 1599, 1002, -431, 187, -1404, -6316, -9900, -13842, -3527, 3641, 262, -1564, 2245, 2412, -1849, -2546, -862, 76, 718, 1804, 4123, 6826, 8457, 9470,
               25000, 25000, 0, 21893, -5829, -5829, -5829, -5829, -5829, -5829, -25000, -25000, -25000, -25000, -25000, -25000, -25000, -25000, -25000, -25000, -19470, -12949, -6954, -1033, 3574, 6527, 8770, 11057, 14386, 17638, 22202, 25000, 25000, 25000, 25000, 21552, 1918, -6567, -6805, -3303, -1146, -1108, -2301, -4055, -5314, -6123, -6492, -6723, -6936, -6865,
               -14651, -16055, 0, -14263, 976, 976, 976, 976, 976, 976, 8913, 9678, 10546, 10861, 11781, 13059, 13178, 12285, 13324, 12775, 12592, 10952, 7471, 2889, -1978, -4869, -6067, -6436, -6742, -6513, -5137, -3133, 281, 2050, -4821, -13415, -4630, 6730, 8004, 3022, -583, -1586, -1189, 389, 1775, 2659, 4089, 4911, 4242, 3128]

stationary_input = [-1173, -1173, -1173, -303, -359, -511, -487, -426, -417, -436, -436, -425, -425, -435, -436, -437, -443, -442, -435, -433, -431, -430, -436, -428, -427, -436, -437, -432, -431, -433, -439, -437, -428, -432, -432, -428, -428, -433, -433, -436, -440, -435, -438, -445, -439, -430, -438, -432, -432, -427,
                     -75, -75, -75, 89, 144, 261, 247, 197, 173, 226, 262, 249, 222, 219, 216, 216, 221, 217, 211, 222, 230, 232, 231, 231, 234, 233, 230, 224, 219, 220, 228, 232, 232, 234, 233, 229, 226, 233, 237, 234, 244, 250, 258, 281, 298, 298, 298, 314, 336, 342,
                     1675, 1675, 1675, -284, -135, 98, -5, -114, -103, -64, -61, -84, -77, -62, -69, -54, -50, -56, -63, -60, -67, -73, -68, -72, -75, -66, -61, -68, -63, -64, -64, -65, -71, -65, -67, -66, -60, -54, -59, -48, -44, -43, -30, -31, -34, -21, -11, -2, -2, 0,
                     -2464, -2464, -2464, -1981, 859, 560, 112, -598, -27, 679, 496, -232, -323, -147, 77, -24, 12, 67, 210, 234, 225, 248, 140, 143, 235, 110, 64, -35, -15, 126, 161, 41, -96, -86, -143, -180, -150, 32, -28, -54, -88, -166, -261, -232, -40, 295, 498, -423, -2245, -3684,
                     6232, 6232, 6232, -1239, 2130, 488, -417, -872, 24, 207, -45, -151, -81, -166, -210, 28, -83, -40, 9, -27, 0, 111, 54, 19, 128, 70, -83, -157, -18, 14, -64, -141, -238, -299, -315, -210, -119, -93, -145, -227, -515, -816, -1116, -1464, -1725, -1735, -1673, -2032, -2612, -3154,
                     -5203, -5203, -5203, 711, 390, -65, 446, 71, 30, 320, 395, 80, 73, 244, 403, 67, 41, 164, 113, 38, 83, 161, 41, 39, 95, -7, 6, 34, 19, 66, 106, 115, 83, 210, 164, 72, 66, 122, 169, 107, 209, 436, 762, 1304, 1957, 2410, 2249, 1765, 1538, 1645]

low_confidence_input = [-1000] * 300

prediction = AImodel.predict(basket_input, 1)   
print(f"Output: {prediction}")

prediction = AImodel.predict(stationary_input, 2)
print(f"Output: {prediction}")

prediction = AImodel.predict(low_confidence_input, 1)
print(f"Output: {prediction}")