from pynq import Overlay, allocate
from pynq import PL 
import numpy as np
import pandas as pd
import time
from sklearn.preprocessing import StandardScaler
from ast import literal_eval
from scipy.special import softmax

PL.reset()

scaler_time = time.time()
print("Setting up")

scaler = StandardScaler()
# # Set up scaler using .csv (very long)
# file_path = '/home/xilinx/IP/combined_2.csv'
# df = pd.read_csv(file_path, converters={'ax': literal_eval, 'ay': literal_eval, 'az': literal_eval,
#                                         'gx': literal_eval, 'gy': literal_eval, 'gz': literal_eval})

# # Combine ax, ay, az, gx, gy, gz columns into a single feature list
# X_combined = [ax + ay + az + gx + gy + gz for ax, ay, az, gx, gy, gz in zip(df['ax'], df['ay'], df['az'], 
#                                                                              df['gx'], df['gy'], df['gz'])]

# # Pad sequences to the max length
# max_length = max(len(sequence) for sequence in X_combined)
# X_padded = np.array([np.pad(sequence, (0, max_length - len(sequence)), 'constant') for sequence in X_combined])

# # Reshape to fit input requirements of the model
# X_padded = X_padded.reshape((X_padded.shape[0], -1))
# scaler.fit(X_padded)

# Set up scaler by hard coding
scaler.mean_ = np.array([-1200.6229090909092, -1216.780909090909, -1340.8034545454545, -1253.9825454545455, -1092.1376363636364, -909.2118181818182, -764.29, -628.6796363636364, -509.21145454545456, -429.73745454545457, -374.51654545454545, -337.1127272727273, -323.3738181818182, -324.41236363636364, -340.8752727272727, -363.2590909090909, -387.5978181818182, -409.57563636363636, -435.2570909090909, -459.59054545454546, -474.01, -485.7450909090909, -495.94036363636366, -506.92927272727275, -519.5476363636363, -528.1336363636364, -534.7007272727272, -531.7036363636364, -516.4261818181818, -490.57418181818184, -461.50981818181816, -429.79345454545455, -401.724, -378.0109090909091, -360.18363636363637, -345.598, -334.8632727272727, -329.6645454545455, -328.2510909090909, -328.6050909090909, -333.0805454545455, -339.58454545454543, -347.15945454545454, -355.67581818181816, -365.714, -374.11, -377.5178181818182, -381.29236363636363, -383.5096363636364, -386.35927272727275, 489.45363636363635, 299.54836363636366, 291.2438181818182, 261.9687272727273, 177.36545454545455, 47.88290909090909, 15.556545454545455, 52.60418181818182, 79.95763636363637, 89.54636363636364, 99.29054545454545, 105.75927272727273, 106.19163636363636, 115.23963636363636, 125.63327272727273, 134.8798181818182, 141.36545454545455, 146.91872727272727, 157.53727272727272, 174.61618181818181, 195.54563636363636, 205.69763636363638, 207.61472727272727, 209.352, 210.0901818181818, 207.58963636363637, 195.25618181818183, 184.52854545454545, 183.65254545454545, 176.79127272727274, 164.55854545454545, 164.01781818181817, 157.45909090909092, 148.416, 143.17163636363637, 141.43763636363636, 142.83145454545453, 147.3421818181818, 152.24581818181818, 156.51309090909092, 163.53781818181818, 171.84963636363636, 182.14163636363637, 192.87236363636364, 206.724, 220.82636363636362, 231.88709090909092, 237.99654545454544, 242.12836363636364, 244.84727272727272, 217.85763636363637, -199.66945454545456, -195.59072727272726, -158.1749090909091, -122.99763636363636, -63.09981818181818, -14.217454545454546, -6.164, -16.532363636363637, -29.97490909090909, -52.80509090909091, -74.60672727272727, -96.87490909090909, -119.80963636363636, -136.51127272727274, -145.5029090909091, -148.19054545454546, -149.996, -148.3249090909091, -144.576, -147.4289090909091, -150.57018181818182, -156.32036363636362, -158.72072727272726, -155.636, -142.1690909090909, -124.82436363636364, -103.99945454545454, -75.01763636363637, -48.88909090909091, -25.96090909090909, -5.372909090909091, 4.6356363636363636, 9.010909090909092, 10.129090909090909, 10.795818181818182, 10.959090909090909, 10.647454545454545, 8.963090909090909, 7.027454545454545, 5.986, 2.838, 0.88, -3.2892727272727273, -5.274363636363637, -6.786181818181818, -9.328, -10.870909090909091, -8.333454545454545, -6.023272727272727, -1891.2998181818182, -190.24254545454545, -717.7750909090909, -1085.9836363636364, -919.8258181818181, -316.9116363636364, 234.902, -84.63818181818182, -6.057636363636363, 432.5209090909091, 690.7294545454546, 829.0916363636363, 998.5294545454545, 1060.1941818181817, 941.3750909090909, 774.4529090909091, 615.322, 465.3429090909091, 386.89036363636365, 222.7058181818182, -94.53072727272728, -420.0527272727273, -514.11, -491.66818181818184, -542.1912727272727, -679.7674545454546, -786.4185454545454, -734.4403636363636, -676.2250909090909, -765.2423636363636, -727.0278181818181, -587.1209090909091, -589.2425454545455, -497.68690909090907, -292.5650909090909, -155.56418181818182, -27.643818181818183, 60.07963636363636, 102.2549090909091, 200.6878181818182, 382.9087272727273, 549.8470909090909, 721.5556363636364, 845.9345454545454, 926.5709090909091, 932.1674545454546, 874.7450909090909, 840.8825454545455, 853.2134545454545, 904.3181818181819, -1150.5516363636364, -59.48890909090909, 777.2292727272727, 500.1932727272727, -350.2790909090909, -870.8374545454545, -1242.7143636363637, -1721.5507272727273, -2256.688727272727, -2874.3327272727274, -3335.4065454545453, -3479.9192727272725, -3314.0445454545456, -2966.8854545454546, -2480.627090909091, -2004.247090909091, -1609.0467272727274, -1205.4312727272727, -810.4703636363637, -408.54836363636366, -18.111272727272727, 527.2385454545455, 1140.138, 1763.9576363636363, 2382.4725454545455, 2817.3654545454547, 3056.5532727272725, 3112.2052727272726, 3054.8830909090907, 2795.422727272727, 2479.0796363636364, 2104.8105454545453, 1703.6003636363637, 1336.3750909090909, 1037.9901818181818, 851.9767272727273, 729.4547272727273, 571.4005454545454, 442.28763636363635, 342.21363636363634, 255.96218181818182, 144.77581818181818, 63.64381818181818, -19.834, -54.35618181818182, -120.92618181818182, -154.68545454545455, -113.53163636363637, -10.044545454545455, 61.463454545454546, 1954.5996363636364, 3195.469818181818, 2997.7472727272725, 3187.572181818182, 3913.4625454545453, 4274.6367272727275, 3714.9394545454547, 2649.755818181818, 2077.5801818181817, 1800.1232727272727, 1509.3941818181818, 1159.2194545454545, 766.558, 332.44254545454544, -111.68472727272727, -501.59654545454543, -863.8265454545455, -1189.0649090909092, -1439.7418181818182, -1602.2585454545454, -1635.2712727272726, -1558.6678181818181, -1477.0972727272726, -1383.1714545454545, -1308.3532727272727, -1193.2563636363636, -1078.2861818181818, -1030.297090909091, -979.662, -864.0967272727273, -808.7350909090909, -762.1630909090909, -742.6021818181819, -735.8609090909091, -766.9365454545455, -853.4130909090909, -1005.4963636363636, -1210.2994545454546, -1459.8449090909091, -1700.0047272727272, -1934.8685454545455, -2121.778909090909, -2308.4249090909093, -2490.2807272727273, -2639.950909090909, -2770.953636363636, -2841.104363636364, -2864.654727272727, -2823.7412727272726, -2737.5565454545454])
scaler.scale_ = np.array([814.7473143043082, 1115.9020731714145, 1117.0988663444562, 1109.845661696368, 1080.7824617385734, 1008.4789922751648, 833.6232977953962, 681.6479912041068, 593.5564387775169, 531.4368192815265, 504.24826127511346, 494.53505402165183, 499.0602841030917, 513.9635527861826, 537.9731883209404, 558.9994336955101, 573.0950935488671, 586.3453229400625, 609.8285855241988, 630.3325880990953, 638.5024397262431, 642.742241651483, 644.4817997908752, 654.740885526077, 669.3757344814602, 674.520842022795, 667.8509620617028, 650.3636203802076, 616.4236248540029, 576.4894774303916, 538.2611019789589, 512.1247638052781, 485.33001799750053, 470.4796622684818, 465.0058264595427, 461.2983081730016, 459.04198801438463, 458.33950221253, 458.0334156613971, 454.9996332181244, 456.21522817801775, 461.80055114073286, 462.9926465464279, 463.2811059043601, 463.80501058134786, 454.49066046009665, 435.8555468070954, 418.1077885989937, 397.18654341603457, 377.4827254511353, 999.1016302092477, 932.293620753313, 776.7581114115276, 688.9496422580323, 617.2045927827066, 602.872219024511, 549.745587011824, 467.63063810191466, 433.43533126308483, 392.68150387658557, 374.7774451611525, 357.9959830341156, 352.1948422561971, 349.4110478971645, 342.10391491769997, 331.6428905148697, 324.9182015764922, 328.2118608103038, 337.33225686233214, 356.5079503792353, 379.3247444281807, 402.0405864109814, 415.7869739983972, 422.3338736394152, 418.11449699156856, 408.52031056869237, 393.64047787977967, 368.93471866944446, 359.6884118775232, 343.9754014410941, 325.7476826536885, 321.75269618247825, 303.0098035604107, 292.3532110904704, 282.5252233229553, 267.8407150831094, 258.9262621457962, 251.21850250829928, 247.8126123629483, 240.0516891525485, 235.58461021421797, 234.66703942134012, 231.42888664880246, 232.87269186843196, 228.60074008947257, 237.10150537357038, 243.89230443092728, 236.17030177948197, 229.00512712611817, 226.84937722442038, 1212.0526671372047, 904.7830193998165, 865.1967954514587, 750.9272977444086, 639.1854556556235, 611.6254192648281, 601.7999963630878, 550.1799841162725, 509.50582889685165, 480.2438181017959, 452.2322916895816, 434.99273062914324, 422.05260420461883, 410.0071754780699, 399.2089792898613, 397.5836531652984, 408.6268118085175, 418.16736621335957, 437.9128639741969, 470.68296089676505, 493.295700956786, 505.3584995570106, 499.068984030951, 486.98583422314937, 474.84328271584906, 465.36527642183756, 454.8647819727756, 441.7165024596171, 443.1095746466152, 432.18814134281286, 422.09513115484754, 399.9601116846655, 378.0733300240895, 354.10179105229963, 329.22305407662026, 306.8734662850231, 292.9857191044875, 275.95698327962884, 267.7895101168609, 255.97122453842857, 251.20978336550837, 243.61790449875326, 239.8886403767764, 235.85812791402284, 235.3728998787297, 237.51996300782764, 237.6598586551795, 234.9277971654093, 232.40752078441253, 225.86776140077734, 10839.860481143362, 11062.686127440391, 10460.266213306128, 9644.068535148488, 9003.188118187853, 8470.234799611864, 8343.721219654024, 7657.145667390238, 6889.052031009115, 6545.285966259097, 6424.631954303664, 6180.293107962603, 5994.39538969874, 6158.318971700187, 6068.927066881346, 5939.183362731445, 5915.09587529673, 5851.986637517729, 5831.601931683629, 5783.251490672546, 5977.892636582751, 5936.7476529694295, 5720.233231965442, 5599.7055882906225, 5513.053457597131, 5523.517488004008, 5687.141371942149, 5861.7483509683325, 5739.405387689839, 5651.678072153421, 5533.003866004999, 5376.015554032481, 5113.80763630896, 4857.105754493903, 4512.208499730022, 4369.635836508446, 4044.769251789944, 4005.723107190031, 3906.589484462417, 3910.5867219634792, 3948.2255551802523, 4049.9515945570506, 4241.7898700254, 4243.761775775587, 4383.787125458482, 4408.898444092657, 4359.483979776796, 4366.819153657481, 4216.703440698766, 4216.342476972641, 14445.183909350866, 14944.61472875653, 15757.778073053927, 15344.406241076678, 14290.622028491254, 13186.393283096359, 11735.269610415391, 10092.192290144128, 8711.583661926565, 8059.793736985275, 7870.4198754457575, 7940.009362441909, 8176.469113833301, 8519.554596123788, 8934.319193131441, 9362.388681753131, 9715.219064773759, 9968.91863787392, 10177.678675291581, 10234.93619460625, 10200.766339481992, 10175.673588506199, 10131.031693674096, 10321.509332396674, 10515.062265798018, 10624.5559105947, 10656.266823640266, 10665.385699314227, 10521.962741841317, 10082.548044509782, 9647.971972399371, 9059.17292179678, 8499.087313177677, 8042.385524154177, 7636.684589954541, 7283.630610635431, 6905.017655032767, 6545.35470791861, 6300.3200579445165, 6133.629085504053, 5985.308335038291, 5814.9867995564155, 5751.735154814976, 5650.401186262498, 5693.648971924609, 5735.9772019648035, 5674.255644348856, 5515.050792043283, 5378.303618396043, 5177.103042500167, 13034.074750231306, 14434.08354696357, 14975.453307017948, 14304.493287027184, 12916.210979296073, 11522.699132078205, 10320.336637751509, 9280.175890878785, 8020.187040072861, 6935.611711193192, 6431.682327176265, 6320.156124856959, 6528.3331109653745, 6924.322159550659, 7383.715267820083, 7774.0693194483465, 8133.644166239671, 8340.568055646914, 8425.193148100327, 8384.699533450515, 8304.460381848052, 8114.509548704638, 7863.012990161413, 7663.384307961616, 7702.885702320697, 7815.888086252443, 7971.164110279572, 8111.39634041964, 8076.890680348576, 7834.135339914575, 7565.244258882237, 7194.72796502231, 6865.584811289829, 6582.728304345816, 6319.125875206227, 6013.90555413728, 5801.25879560835, 5698.649662504557, 5705.291744730697, 5769.763002788014, 5828.267128556373, 5909.796180105675, 6036.107983852253, 6145.472080432376, 6195.015198965069, 6203.92448428893, 6129.048659800232, 6025.884590985595, 5864.39764906276, 5726.689119130368])

print(f"Scaler time: {((time.time() - scaler_time) * 1000):.4f} ms\n")

# Load the overlay
overlay = Overlay("/home/xilinx/IP/design_4.bit")
# DMA objects
dma = overlay.axi_dma_0
dma_send = dma.sendchannel
dma_recv = dma.recvchannel
# HLS object
hls = overlay.predict_0
CONTROL_REGISTER = 0x0
hls.write(CONTROL_REGISTER, 0x81)  # Starts the HLS IP


# List of hard-coded input data for testing
input_data_list = [
   #basket
   {
       'ax': [-1870, -3117, 0, -1725, -1828, -1828, -1828, -1828, -1828, -1828, -1240, -1078, -1056, -982, -868, -758, -667, -504, -448, -355, -206, -49, 39, 109, 88, 111, 108, -1, -99, -192, -300, -335, -374, -806, -1201, -801, -542, -350, -239, -126, -97, -86, -79, -66, -34, -14, 22, 36, 16, -8],
       'ay': [-151, -579, 0, 772, 129, 129, 129, 129, 129, 129, 137, 262, 420, 390, 461, 382, 314, 242, 145, 68, -77, -251, -382, -456, -362, -229, -165, -112, -59, 8, 98, 75, -80, -168, -745, -342, 243, -109, -299, -176, -108, -138, -86, -30, -25, -63, -125, -146, -85, -37],
       'az': [-1477, -1595, 0, 859, 619, 619, 619, 619, 619, 619, 449, 429, 528, 446, 339, 255, 19, -161, -374, -647, -848, -1006, -1069, -996, -880, -753, -642, -653, -477, -416, -335, -262, -145, -160, 776, 1229, 1114, 715, 581, 509, 488, 503, 496, 443, 374, 323, 283, 245, 179, 123],
       'gx': [-7523, -9907, 0, -3564, -7668, -7668, -7668, -7668, -7668, -7668, 4956, 5113, 3592, 2881, 2080, -823, -3180, -4358, -3396, -2639, 145, 1580, 161, -239, 1477, 1522, 1599, 1002, -431, 187, -1404, -6316, -9900, -13842, -3527, 3641, 262, -1564, 2245, 2412, -1849, -2546, -862, 76, 718, 1804, 4123, 6826, 8457, 9470],
       'gy': [25000, 25000, 0, 21893, -5829, -5829, -5829, -5829, -5829, -5829, -25000, -25000, -25000, -25000, -25000, -25000, -25000, -25000, -25000, -25000, -19470, -12949, -6954, -1033, 3574, 6527, 8770, 11057, 14386, 17638, 22202, 25000, 25000, 25000, 25000, 21552, 1918, -6567, -6805, -3303, -1146, -1108, -2301, -4055, -5314, -6123, -6492, -6723, -6936, -6865],
       'gz': [-14651, -16055, 0, -14263, 976, 976, 976, 976, 976, 976, 8913, 9678, 10546, 10861, 11781, 13059, 13178, 12285, 13324, 12775, 12592, 10952, 7471, 2889, -1978, -4869, -6067, -6436, -6742, -6513, -5137, -3133, 281, 2050, -4821, -13415, -4630, 6730, 8004, 3022, -583, -1586, -1189, 389, 1775, 2659, 4089, 4911, 4242, 3128]
   },
   #bowling
   {
       'ax': [-1441, -2094, -3384, -3735, -3257, -2508, -1924, -1690, -1563, -1207, -856, -694, -561, -440, -349, -264, -226, -281, -373, -525, -749, -1089, -1375, -1807, -2484, -3089, -3093, -2498, -1849, -1298, -890, -650, -478, -392, -287, -185, -122, -65, -46, 11, -12, -73, -72, -156, -227, -251, -376, -424, -552, -729],
       'ay': [-407, -314, -508, -342, -69, 193, 327, 191, -116, -8, 118, 88, 93, 114, 168, 217, 185, 152, 190, 189, 126, 159, 26, 45, 68, 100, 110, -31, 15, 68, 86, 62, 63, 62, 6, -7, 54, 18, 17, 61, 135, 202, 168, 228, 291, 298, 374, 454, 395, 374],
       'az': [453, 144, -1026, -1114, -1039, -788, -381, 138, 10, -171, -232, -219, -163, -213, -315, -388, -462, -449, -407, -381, -386, -474, -601, -674, -783, -889, -725, -494, -90, 22, -56, -50, -70, -66, -78, -69, -47, -56, -89, -103, -114, -125, -133, -133, -151, -166, -208, -171, -145, -172],
       'gx': [7455, 5481, 3527, 10094, 4187, -4425, 2701, 109, -1415, 2405, 2819, 2252, 1828, 590, 605, -398, -1487, -1038, -387, -2387, -3475, -4193, -3460, -1100, -426, 76, -665, 1890, 2616, -1207, -4015, -5141, -5368, -6004, -6604, -5383, -5440, -6861, -6443, -4526, -2426, -2654, -2579, -1272, -1905, -2315, -2951, -5250, -6102, -2927],
       'gy': [-8874, -25000, -25000, -25000, -25000, -25000, -19806, -12050, -14402, -16079, -12754, -9229, -7528, -7206, -6214, -4968, -1123, 3111, 7238, 10809, 13609, 14963, 15815, 23423, 25000, 25000, 25000, 25000, 24779, 15518, 7533, 4673, 5574, 6002, 5068, 4021, 3444, 1876, -711, -2045, -2639, -3199, -3366, -4216, -5230, -5633, -6444, -6026, -4280, -5417],
       'gz': [-4662, 344, -129, -2536, -5365, -11799, -8430, -4362, -5153, -6189, -5001, -3474, -3027, -2515, -1252, 116, 1571, 2716, 3792, 4208, 4597, 6218, 8432, 9647, 9920, 9626, 8401, 8025, 5761, 2439, 2340, 2399, 1930, 1950, 1779, 1264, 640, -176, -971, -1869, -2973, -4170, -5080, -6505, -8357, -9330, -10750, -13420, -14516, -14394]
   },
   #reload
   {
       'ax': [929, 2388, 763, 470, 279, 257, 257, 257, 384, 384, 165, 145, 42, -24, -205, -171, -228, -234, -114, -14, -48, -5, -23, -6, 3, -15, -13, -5, -9, 6, 19, 0, -1, 23, 11, 29, 34, 29, 46, 43, 16, 6, 25, 27, 17, 7, 14, 10, 13, 16],
       'ay': [-84, -1161, -568, -217, 19, 311, 311, 311, 53, 53, 256, 326, 513, 380, 607, 498, 500, 801, 656, 435, 558, 563, 546, 534, 574, 545, 520, 520, 497, 497, 495, 496, 510, 494, 477, 472, 500, 491, 476, 482, 474, 475, 482, 452, 496, 510, 511, 506, 519, 509],
       'az': [-235, -255, 344, 452, 422, 318, 318, 318, 180, 180, 222, 175, 241, 128, 82, 3, -41, 23, -25, -67, -5, 8, 26, -23, -50, -47, -48, -48, -61, -69, -69, -48, -45, -62, -56, -56, -48, -36, -51, -58, -59, -64, -64, -62, -53, -47, -53, -63, -64, -70],
       'gx': [-8354, 8476, -836, -6861, 4249, 7772, 7772, 7772, 11615, 11615, 16171, 17553, 12662, 9521, 8574, 1686, 5140, 3830, -1464, 378, 2945, 1481, 1196, 997, 604, 223, 167, 341, 501, 12, -50, 336, 20, -184, -20, 446, 383, -135, -85, 175, -164, 52, -276, -12, 283, -70, 54, 30, 348, 521],
       'gy': [-10312, 473, 4694, -997, -2565, -4788, -4788, -4788, -1699, -1699, 306, -170, 693, -1026, -2850, -2577, -663, -1022, -2175, -660, 352, 318, -202, -797, -582, -194, -390, -321, -163, -238, 300, 447, -280, -321, 123, 32, 172, -125, -364, -51, 55, -161, -48, 43, -26, -305, -280, -29, 6, 307],
       'gz': [7473, 16858, 316, -10143, -3334, 286, 286, 286, 923, 923, -773, -2120, -7091, -7676, -5670, -6913, -7036, -5287, -1533, -1038, -1614, -157, 199, -276, -24, 454, 306, 598, 803, 389, 454, 599, 469, 737, 700, 357, 247, 156, -119, -67, -58, -80, 23, -304, -582, -421, -427, -546, -404, -222]
   },
   #volley
   {
       'ax': [-678, -241, -230, -196, -91, -100, -138, -142, -217, -423, -585, -729, -957, -1211, -1320, -1402, -1309, -1099, -1004, -982, -991, -1030, -1061, -1098, -1187, -1173, -1054, -935, -788, -631, -493, -428, -327, -259, -157, -124, -115, -142, -176, -201, -318, -331, -328, -408, -509, -564, -763, -836, -895, -901],
       'ay': [157, -49, 171, -111, -223, -203, -278, -396, -363, -274, -269, -253, -212, -233, -23, 164, 353, 288, 260, 445, 624, 582, 339, 245, 121, -30, -107, -270, -342, -389, -368, -352, -280, -252, -177, -122, -98, -29, -55, 46, 66, -1, 15, 33, -40, 9, 7, 97, 156, 131],
       'az': [933, 6, -93, -58, 33, 97, 116, 79, 49, 35, -3, -18, -26, -108, -224, -269, -358, -322, -218, -284, -364, -289, -240, -313, -343, -297, -239, -179, -129, -90, -48, -2, 40, 28, 4, -8, 19, 19, 22, 86, 126, 111, 60, 46, 40, 70, 85, 86, 69, 60],
       'gx': [-5208, 10215, 3291, -3450, -1668, -865, -2384, -2925, -1361, -714, -762, 73, 909, 3509, 5597, 5249, 4210, 1217, 1712, 2787, 3125, 748, -1136, -1786, -2958, -3198, -3778, -4087, -3423, -4057, -3578, -3024, -2507, -1577, -992, -987, -484, 91, 342, -1364, -2720, -3375, -3431, -4528, -3261, -1510, 328, 483, -1648, -2467],
       'gy': [-3859, -1966, 921, 756, 593, 450, -1290, -2555, -1978, -1805, -2456, -1670, -522, -377, -455, -260, -2701, -3253, -1860, -1029, 1130, 2452, 1969, 2527, 3473, 3989, 4010, 4186, 3781, 3050, 2730, 1733, -212, -1336, -978, 254, 1029, 1017, 785, 399, -2020, -4224, -4708, -3767, -3148, -1831, -939, -2190, -3011, -3334],
       'gz': [9458, 10419, 7287, 3388, 2253, 1484, -550, -3978, -7455, -9782, -12395, -15255, -17563, -19762, -20825, -18987, -13039, -8590, -6186, -4635, -1532, 3537, 6829, 8587, 10862, 12778, 13557, 13902, 13068, 11378, 9449, 8188, 7263, 6384, 4346, 1821, 468, -680, -1553, -1586, -1268, -2117, -2611, -3627, -5175, -7430, -9506, -10625, -11217, -10853]
   },
   #rainbomb
   {
       'ax': [-2504, -3128, -3408, -1592, -1200, -1073, -782, -530, -425, -357, -359, -315, -314, -270, -261, -264, -290, -309, -305, -308, -290, -244, -273, -508, -905, -1632, -1686, -1036, -406, -261, 3, 22, -82, -60, -128, -131, -128, -159, -143, -227, -265, -203, -406, -439, -519, -774, -822, -864, -958, -891],
       'ay': [312, 258, -673, 270, -105, 183, 148, -161, -204, -221, -298, -349, -431, -493, -581, -624, -550, -487, -377, -318, -232, -214, -104, 19, 37, -67, -51, -354, -5, 89, -206, -159, -110, -38, 45, 5, -5, -5, 2, 84, 79, 94, 198, 216, 206, 284, 371, 386, 357, 476],
       'az': [-70, -214, -689, -819, -621, -680, -635, -685, -585, -466, -411, -388, -484, -589, -693, -792, -799, -811, -844, -825, -828, -857, -839, -755, -622, -363, 814, 1397, 1077, 780, 489, 494, 482, 397, 365, 245, 178, 143, 114, 133, 105, 108, 159, 149, 206, 211, 173, 166, 145, 157],
       'gx': [-12720, -13727, 7447, 2836, -2713, 6534, -688, -828, 1563, 1297, 1409, 1166, 1625, 1229, -448, -1283, -1990, -3036, -2839, -2396, -3246, -2750, -1603, -680, -3805, -9409, -21521, -25000, -5037, 2943, 4183, 4540, 2851, 3732, 2179, 1158, 3848, 6528, 9073, 8938, 8183, 9103, 6064, 4696, 5867, 6872, 6822, 5881, 6942, 8590],
       'gy': [-25000, -25000, -25000, -25000, -25000, -22259, -16924, -11129, -6552, -3891, -2898, -3342, -4013, -3776, -2597, -851, 1768, 3530, 5800, 8811, 11619, 16008, 21736, 25000, 25000, 25000, 25000, 25000, 2104, -3526, -398, 3899, 4857, 2183, 828, -150, -611, 199, 1075, 2403, 2867, 4456, 5893, 6111, 8404, 8548, 6434, 5968, 6360, 5197],
       'gz': [14419, 11910, 15684, 22456, 14831, 12478, 15876, 15279, 12899, 10338, 7712, 5412, 3128, 1007, -1049, -4636, -8153, -10225, -12873, -13731, -14147, -15723, -17044, -17299, -15940, -15681, -14072, -15161, -7055, 3889, 7683, 3887, 1497, 1319, 708, 1014, 1968, 2217, 2190, 577, -1500, -3269, -6635, -9218, -9498, -10910, -12619, -12420, -12276, -11221]
   },
   #shield
   {
       'ax': [-870, -1211, -1978, -2966, -2560, -1745, -1098, -841, -999, -295, 115, 296, 281, 194, 195, 358, 328, 315, 329, 338, 358, 365, 354, 359, 348, 339, 353, 355, 338, 333, 337, 338, 345, 349, 331, 331, 334, 319, 287, 263, 182, 3, -173, -296, -383, -478, -646, -833, -920, -1070],
       'ay': [1451, 1669, 1533, 1770, 649, -152, -83, -154, -234, -316, 123, -85, 73, 36, 20, 272, 115, 139, 162, 155, 242, 182, 241, 202, 173, 202, 204, 202, 200, 193, 180, 196, 196, 185, 180, 180, 177, 169, 147, 131, 11, -257, -400, -360, -142, 41, 177, 342, 467, 569],
       'az': [-771, -1178, -1329, -770, -266, 78, 114, 215, 754, 412, 3, -108, 84, 315, 339, 203, 214, 265, 280, 264, 274, 298, 305, 295, 295, 279, 266, 287, 302, 320, 315, 287, 293, 298, 305, 303, 291, 301, 312, 307, 331, 332, 251, 88, -64, -111, -90, -93, -54, -48],
       'gx': [2734, 6028, 6888, 1372, -6861, -7222, -4062, -5838, -9517, -5703, -1591, -3283, -159, -4220, 793, 40, -920, -344, -666, -447, 578, 84, 362, -298, 212, -249, 9, 246, -152, -131, 40, 186, -480, -241, -65, 67, -323, -103, -130, 311, 52, 426, 79, 679, 1582, 2827, 3332, 4941, 5274, 6015],
       'gy': [-3094, -431, 19942, 25000, 25000, 22225, 17416, 16679, 13661, 2190, -537, 1480, 2361, 3912, 43, -466, 701, 343, 244, 116, 299, 527, 381, 267, 211, 196, 261, 664, 656, 215, 148, 6, 131, 318, 344, -48, -49, 57, -124, -518, -669, -1458, -3259, -5664, -6079, -4366, -2417, -2281, -1834, -703],
       'gz': [8436, 22963, 25000, 25000, 25000, 25000, 19266, 14587, 9875, 5639, 4641, 3234, 2500, 1638, 887, 817, 541, 327, -83, -660, -361, -315, -371, -37, -113, -142, -70, -77, -27, 65, -2, 31, 27, -161, -177, -162, -183, -247, -363, -747, -1494, -3861, -7692, -12406, -16904, -20004, -21870, -24552, -24678, -23794]
   },
   #logout
   {
       'ax': [-2106, -2301, -2315, -1956, -1500, -1143, -829, -532, -353, -283, -289, -279, -316, -388, -495, -661, -908, -1188, -1732, -1897, -1839, -1516, -1138, -1120, -1086, -1010, -920, -722, -501, -317, -221, -163, -91, -79, -118, -174, -225, -284, -443, -642, -965, -1371, -1781, -2271, -2099, -1728, -1257, -1165, -1101, -907],
       'ay': [1236, 1393, 1166, 658, 299, -33, -372, -589, -641, -680, -671, -603, -501, -428, -412, -369, -329, 58, 89, 344, 1296, 1073, 1321, 1492, 1555, 1336, 910, 574, 280, 50, -97, -205, -326, -370, -325, -252, -263, -270, -199, -147, -166, 6, 82, 254, 652, 738, 613, 202, 62, 168],
       'az': [-309, -157, -4, 172, 233, 199, 83, -26, -107, -156, -205, -237, -236, -231, -323, -368, -446, -533, -473, -563, -795, -970, -841, -601, -409, -270, -171, -145, -126, -73, -7, 33, 16, -18, -27, -25, -47, -70, -53, -65, -128, -219, -273, -320, -313, -196, -165, -53, -1, -23],
       'gx': [23178, 13109, -705, -5795, -7377, -9097, -6974, -2773, -871, 920, 3979, 7595, 9002, 6864, 5701, 5816, 8539, 10769, 6651, 6279, -17531, -25000, -19792, -9445, -12721, -20616, -24712, -25000, -25000, -23681, -19804, -16496, -12804, -7088, -3211, -2305, -1754, 173, 2091, 2462, 5244, 9939, 11468, 14057, 3955, -6521, -7714, -32, 6402, 8973],
       'gy': [14326, 22564, 23677, 18314, 12045, 5027, 260, -2475, -3663, -4087, -4958, -5387, -5514, -5693, -6323, -6828, -7962, -8686, -9508, -12693, -9765, -5012, 1945, 11281, 13652, 11858, 5909, -1683, -6131, -6546, -5664, -5769, -5541, -4581, -2940, -2858, -2950, -2118, -1033, -503, -660, -1481, -1373, -2201, -3738, 1872, 3080, 4540, 4538, 4096],
       'gz': [25000, 25000, 25000, 25000, 25000, 25000, 25000, 19420, 11616, 5048, -750, -7232, -11870, -15970, -20597, -25000, -25000, -25000, -25000, -25000, -25000, -25000, -14746, -1707, 4950, 11033, 17381, 19299, 19060, 16450, 13283, 9179, 4846, -369, -4821, -8249, -11559, -15140, -18815, -23139, -25000, -25000, -25000, -25000, -25000, -25000, -18650, -5284, -4506, -8913]
   },
   #stationary
   {
       'ax': [-1173, -1173, -1173, -303, -359, -511, -487, -426, -417, -436, -436, -425, -425, -435, -436, -437, -443, -442, -435, -433, -431, -430, -436, -428, -427, -436, -437, -432, -431, -433, -439, -437, -428, -432, -432, -428, -428, -433, -433, -436, -440, -435, -438, -445, -439, -430, -438, -432, -432, -427],
       'ay': [-75, -75, -75, 89, 144, 261, 247, 197, 173, 226, 262, 249, 222, 219, 216, 216, 221, 217, 211, 222, 230, 232, 231, 231, 234, 233, 230, 224, 219, 220, 228, 232, 232, 234, 233, 229, 226, 233, 237, 234, 244, 250, 258, 281, 298, 298, 298, 314, 336, 342],
       'az': [1675, 1675, 1675, -284, -135, 98, -5, -114, -103, -64, -61, -84, -77, -62, -69, -54, -50, -56, -63, -60, -67, -73, -68, -72, -75, -66, -61, -68, -63, -64, -64, -65, -71, -65, -67, -66, -60, -54, -59, -48, -44, -43, -30, -31, -34, -21, -11, -2, -2, 0],
       'gx': [-2464, -2464, -2464, -1981, 859, 560, 112, -598, -27, 679, 496, -232, -323, -147, 77, -24, 12, 67, 210, 234, 225, 248, 140, 143, 235, 110, 64, -35, -15, 126, 161, 41, -96, -86, -143, -180, -150, 32, -28, -54, -88, -166, -261, -232, -40, 295, 498, -423, -2245, -3684],
       'gy': [6232, 6232, 6232, -1239, 2130, 488, -417, -872, 24, 207, -45, -151, -81, -166, -210, 28, -83, -40, 9, -27, 0, 111, 54, 19, 128, 70, -83, -157, -18, 14, -64, -141, -238, -299, -315, -210, -119, -93, -145, -227, -515, -816, -1116, -1464, -1725, -1735, -1673, -2032, -2612, -3154],
       'gz': [-5203, -5203, -5203, 711, 390, -65, 446, 71, 30, 320, 395, 80, 73, 244, 403, 67, 41, 164, 113, 38, 83, 161, 41, 39, 95, -7, 6, 34, 19, 66, 106, 115, 83, 210, 164, 72, 66, 122, 169, 107, 209, 436, 762, 1304, 1957, 2410, 2249, 1765, 1538, 1645]
   },
   #shake
   {
       'ax': [338, 349, 195, -128, -300, -2, 0, 156, 271, 248, -219, -89, 180, 131, -161, 66, 327, -16, -16, -41, -41, -131, 46, 204, 147, -142, -142, -10, -39, -117, 7, 201, 103, -85, -193, -134, -103, -162, -166, -78, -12, -13, -24, -64, -19, 10, -79, -205, -148, -95],
       'ay': [-875, 701, 746, 607, 1289, 519, 0, -249, 464, 881, 576, 939, 405, 214, -157, 215, 688, 734, 734, 699, 699, 179, -31, 413, 577, 621, 621, 462, 236, -39, -2, 287, 361, 284, 753, 736, 707, 342, 97, 259, 392, 428, 338, 521, 474, 582, 488, 346, 302, 376],
       'az': [347, -217, -45, 81, 333, 59, 0, 134, -251, -326, 106, 308, -68, -58, 319, 116, -177, -4, -4, 144, 144, 426, 329, 11, 4, 114, 114, -1, 266, 445, 311, 94, 106, 177, 269, 98, 133, 386, 460, 325, 211, 173, 179, 211, 42, -5, 144, 323, 342, 291],
       'gx': [7319, 25000, 25000, 19580, -7923, -25000, 0, 8420, 25000, 25000, 21378, -12539, -25000, -25000, -17181, 25000, 25000, 25000, 25000, -25000, -25000, -22211, 13080, 25000, 25000, 14588, 14588, -25000, -25000, -9032, 13758, 25000, 23289, 16332, 2232, -19891, -25000, -18803, 711, 16621, 22587, 20207, 13756, 2507, -14318, -20630, -18337, -8450, 4408, 10477],
       'gy': [-15034, 14583, 18903, 18539, 1628, -11869, 0, -9821, 13301, 25000, 17337, 2105, -11441, -17200, -14138, 5014, 15608, 12871, 12871, -7470, -7470, -12640, -3556, 7683, 13769, 9038, 9038, -4851, -6302, -6048, -1956, 7173, 13324, 12598, 1264, -7749, -8686, -4544, -136, 3209, 7145, 8292, 4926, -2108, -6344, -7004, -3128, 269, 2665, 4577],
       'gz': [-1945, 11626, 11188, 9012, -488, -18869, 0, 587, 14986, 18150, 9805, -8920, -25000, -25000, -15397, 14412, 18568, 12807, 12807, -13612, -13612, -13857, 5793, 14014, 13573, 4953, 4953, -21338, -17510, -4789, 7741, 14975, 15039, 10522, -2806, -17379, -20787, -12791, 3695, 13054, 17146, 16991, 12410, 1305, -11178, -18073, -15568, -4710, 4966, 8597]
   },
   #gun raise
   {
       'ax': [-2078, -2188, -1974, -1101, -605, -275, -252, -173, -90, -63, 37, 82, 100, 142, 144, 138, 135, 118, 103, 110, 104, 100, 109, 97, 95, 102, 103, 71, 51, 98, 132, 141, 138, 113, 81, 78, 85, 100, 104, 105, 93, 87, 86, 98, 117, 116, 101, 78, 84, 112],
       'ay': [1318, 1036, 437, -580, -766, -484, -148, 3, 116, 245, 383, 428, 445, 509, 491, 503, 543, 534, 532, 470, 459, 491, 481, 499, 510, 498, 440, 397, 556, 676, 550, 463, 462, 499, 520, 534, 521, 474, 435, 437, 443, 430, 459, 471, 472, 471, 427, 447, 581, 558],
       'az': [-693, -747, -147, 163, 277, 94, -5, -56, -21, -3, -74, -82, -74, -87, -94, -93, -91, -82, -70, -43, -19, -19, -38, -37, -32, -25, -18, -40, -97, -122, -69, -27, -55, -101, -127, -138, -119, -88, -70, -76, -89, -104, -110, -117, -117, -106, -105, -136, -154, -109],
       'gx': [7140, -66, -11484, -9690, -4230, -1327, -253, 1485, 764, 808, 1431, 764, 1695, 1543, 679, 921, 113, -679, -1373, -1752, -621, 74, 228, 511, 363, 419, 751, 1394, 1902, 782, -1017, -181, 567, 489, 93, 214, 121, -66, 78, 165, -44, 137, 457, 148, 90, 4, 457, 984, 995, -704],
       'gy': [2723, 19840, 17822, 8917, 1747, -321, -865, 83, 1190, 287, -506, -13, -248, -99, 428, 410, 639, 742, 905, 1083, 751, 263, 381, 345, 190, 292, 135, -599, -1030, -296, 296, 57, -754, -922, -972, -805, -215, 7, -209, -526, -440, -383, -366, -282, -13, 57, -105, -535, -173, 588],
       'gz': [25000, 25000, 25000, 24036, 18622, 10100, 6740, 3574, 135, -1124, -1480, -2092, -1760, -1712, -1612, -1586, -1490, -1340, -923, -874, -1067, -811, -703, -669, -290, 216, 608, -508, -2323, -1026, -49, 351, 508, 479, 420, 482, 682, 600, 564, 298, 160, -6, -78, 32, 210, 383, 403, -792, -1411, -325]
   },
   #gun drop
   {
       'ax': [-1586, 0, -2250, -1668, -1166, -721, -588, -595, -553, -470, -427, -418, -449, -482, -517, -540, -524, -486, -459, -457, -462, -467, -470, -467, -466, -463, -482, -495, -492, -459, -437, -444, -458, -479, -491, -496, -488, -467, -450, -448, -463, -481, -499, -485, -459, -456, -461, -461, -465, -475],
       'ay': [104, 0, 1198, 1242, 1009, 1031, 749, 528, 393, 323, 270, 231, 202, 168, 150, 110, 67, 45, 49, 48, 40, 47, 59, 73, 97, 123, 139, 161, 178, 189, 194, 179, 156, 148, 159, 161, 155, 157, 142, 127, 118, 116, 125, 136, 132, 119, 109, 109, 121, 137],
       'az': [-530, 0, -368, -209, -291, -241, -80, 41, 67, 3, -69, -98, -85, -56, -34, -22, -11, -6, 2, 10, 6, 0, 3, -3, 4, 0, -6, -3, -2, 0, 1, 12, 11, 3, 1, 2, -2, -9, -16, -15, -18, -21, -18, -7, 0, 9, 9, 1, 0, 0],
       'gx': [16036, 0, 161, -4390, -160, 5694, 6508, 5607, 4491, 2748, 280, -916, -590, 722, 1516, 1680, 1566, 1228, 538, -442, -997, -1227, -1337, -1194, -988, -1063, -785, -587, -283, 349, 489, 198, -131, -40, 126, 89, 109, 205, 242, 399, 297, 56, -68, -242, -288, -301, -90, 232, 119, -190],
       'gy': [-5587, 0, -4099, -7079, -7843, -3358, 2428, 3807, 1404, -1573, -2708, -1994, -680, 251, 486, 446, 594, 653, 524, 427, 196, 44, 22, 86, 39, -45, -94, -60, -20, 19, 108, 62, -116, -80, -77, -96, -61, -128, -155, -149, -131, -79, 31, 202, 232, 231, 74, -96, -80, 10],
       'gz': [-25000, 0, -25000, -22698, -15440, -8144, -730, 1754, 2097, 1882, 1357, 804, 1134, 2375, 3162, 3730, 3911, 3303, 2616, 1853, 1240, 589, -47, -627, -1039, -1467, -1601, -1715, -1631, -1110, -445, -138, -91, -205, -132, 39, 105, 325, 572, 734, 629, 355, 143, 108, 216, 226, 172, 82, -170, -370]
   },
   #fake
   {
      'ax': [-1000]*50, 
      'ay': [-1000]*50,
      'az': [-1000]*50,
      'gx': [-1000]*50,
      'gy': [-1000]*50,
      'gz': [-1000]*50,
   },
]

# Allocate input and output buffers

data_size = 300
input_buffer = allocate(shape=(300,), dtype=np.float32)
output_buffer = allocate(shape=(11,), dtype=np.float32)

# Process each set of inputs
for index, hard_coded_data in enumerate(input_data_list):
    # Combine and preprocess inputs
    combined_input = hard_coded_data['ax'] + hard_coded_data['ay'] + hard_coded_data['az'] + \
                     hard_coded_data['gx'] + hard_coded_data['gy'] + hard_coded_data['gz']

    padded_input = np.pad(combined_input, (0, data_size - len(combined_input)), 'constant')

    # Reshape padded_input to be 2D for StandardScaler
    # padded_input_reshaped = padded_input.reshape(-1, 1)  # Reshape to 2D with one column

    # Fit and transform using StandardScaler
    scaled_input = scaler.transform([padded_input]) 

    # Fill the input buffer
    for i in range(data_size):
        input_buffer[i] = scaled_input[0][i]
    #print(input_buffer)
    # DMA transfer for inference
    start_time = time.time()
    dma_send.transfer(input_buffer)
    dma_recv.transfer(output_buffer)
    dma_send.wait()
    dma_recv.wait()
    
    # Output the result from DMA
    print(f"Float values:{output_buffer}")
    max_idx = 0
    max_val = output_buffer[0]
    for i in range(1, 11):
        if output_buffer[i] > max_val:
            max_val = output_buffer[i]  
            max_idx = i
    
    # Apply softmax to calculate confidence
    probabilities = softmax(output_buffer)
    max_idx = np.argmax(probabilities)
    confidence = probabilities[max_idx]

    gesture_mapping = ['basket', 'bowl', 'invalid', 'invalid', 'logout', 'bomb', 'reload', 'invalid', 'shield', 'invalid', 'volley']
    predicted_gesture = gesture_mapping[max_idx]
    
    if confidence < 0.9:
        predicted_gesture = 'invalid'

    print(f"Predicted Gesture: {predicted_gesture} with confidence: {confidence:.2f}")


    #print("Input Buffer (Sent Data):", input_buffer)
    #print(f"Predicted Gesture: {max_idx}")
    print(f"Inference time: {((time.time() - start_time) * 1000):.4f} ms\n")

# Clean up
input_buffer.close()
output_buffer.close()
