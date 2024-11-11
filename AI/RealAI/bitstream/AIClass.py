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

        print("Setting up")

        self.scaler = StandardScaler()

      #   # Set up scaler using .csv (very long)
      #   file_path = '/home/xilinx/IP/combined_2.csv'
      #   df = pd.read_csv(file_path, converters={'ax': literal_eval, 'ay': literal_eval, 'az': literal_eval,
      #                                           'gx': literal_eval, 'gy': literal_eval, 'gz': literal_eval})

      #   # Combine ax, ay, az, gx, gy, gz columns into a single feature list
      #   X_combined = [ax + ay + az + gx + gy + gz for ax, ay, az, gx, gy, gz in zip(df['ax'], df['ay'], df['az'], 
      #                                                                                df['gx'], df['gy'], df['gz'])]

      #   # Pad sequences to the max length
      #   max_length = max(len(sequence) for sequence in X_combined)
      #   X_padded = np.array([np.pad(sequence, (0, max_length - len(sequence)), 'constant') for sequence in X_combined])
      #   X_padded = X_padded.reshape((X_padded.shape[0], -1))
      #   # Scale features and store scaler
      #   self.scaler.fit(X_padded)

        # Set up scaler by hard coding
        self.scaler.mean_ = np.array([-1200.6229090909092, -1216.780909090909, -1340.8034545454545, -1253.9825454545455, -1092.1376363636364, -909.2118181818182, -764.29, -628.6796363636364, -509.21145454545456, -429.73745454545457, -374.51654545454545, -337.1127272727273, -323.3738181818182, -324.41236363636364, -340.8752727272727, -363.2590909090909, -387.5978181818182, -409.57563636363636, -435.2570909090909, -459.59054545454546, -474.01, -485.7450909090909, -495.94036363636366, -506.92927272727275, -519.5476363636363, -528.1336363636364, -534.7007272727272, -531.7036363636364, -516.4261818181818, -490.57418181818184, -461.50981818181816, -429.79345454545455, -401.724, -378.0109090909091, -360.18363636363637, -345.598, -334.8632727272727, -329.6645454545455, -328.2510909090909, -328.6050909090909, -333.0805454545455, -339.58454545454543, -347.15945454545454, -355.67581818181816, -365.714, -374.11, -377.5178181818182, -381.29236363636363, -383.5096363636364, -386.35927272727275, 489.45363636363635, 299.54836363636366, 291.2438181818182, 261.9687272727273, 177.36545454545455, 47.88290909090909, 15.556545454545455, 52.60418181818182, 79.95763636363637, 89.54636363636364, 99.29054545454545, 105.75927272727273, 106.19163636363636, 115.23963636363636, 125.63327272727273, 134.8798181818182, 141.36545454545455, 146.91872727272727, 157.53727272727272, 174.61618181818181, 195.54563636363636, 205.69763636363638, 207.61472727272727, 209.352, 210.0901818181818, 207.58963636363637, 195.25618181818183, 184.52854545454545, 183.65254545454545, 176.79127272727274, 164.55854545454545, 164.01781818181817, 157.45909090909092, 148.416, 143.17163636363637, 141.43763636363636, 142.83145454545453, 147.3421818181818, 152.24581818181818, 156.51309090909092, 163.53781818181818, 171.84963636363636, 182.14163636363637, 192.87236363636364, 206.724, 220.82636363636362, 231.88709090909092, 237.99654545454544, 242.12836363636364, 244.84727272727272, 217.85763636363637, -199.66945454545456, -195.59072727272726, -158.1749090909091, -122.99763636363636, -63.09981818181818, -14.217454545454546, -6.164, -16.532363636363637, -29.97490909090909, -52.80509090909091, -74.60672727272727, -96.87490909090909, -119.80963636363636, -136.51127272727274, -145.5029090909091, -148.19054545454546, -149.996, -148.3249090909091, -144.576, -147.4289090909091, -150.57018181818182, -156.32036363636362, -158.72072727272726, -155.636, -142.1690909090909, -124.82436363636364, -103.99945454545454, -75.01763636363637, -48.88909090909091, -25.96090909090909, -5.372909090909091, 4.6356363636363636, 9.010909090909092, 10.129090909090909, 10.795818181818182, 10.959090909090909, 10.647454545454545, 8.963090909090909, 7.027454545454545, 5.986, 2.838, 0.88, -3.2892727272727273, -5.274363636363637, -6.786181818181818, -9.328, -10.870909090909091, -8.333454545454545, -6.023272727272727, -1891.2998181818182, -190.24254545454545, -717.7750909090909, -1085.9836363636364, -919.8258181818181, -316.9116363636364, 234.902, -84.63818181818182, -6.057636363636363, 432.5209090909091, 690.7294545454546, 829.0916363636363, 998.5294545454545, 1060.1941818181817, 941.3750909090909, 774.4529090909091, 615.322, 465.3429090909091, 386.89036363636365, 222.7058181818182, -94.53072727272728, -420.0527272727273, -514.11, -491.66818181818184, -542.1912727272727, -679.7674545454546, -786.4185454545454, -734.4403636363636, -676.2250909090909, -765.2423636363636, -727.0278181818181, -587.1209090909091, -589.2425454545455, -497.68690909090907, -292.5650909090909, -155.56418181818182, -27.643818181818183, 60.07963636363636, 102.2549090909091, 200.6878181818182, 382.9087272727273, 549.8470909090909, 721.5556363636364, 845.9345454545454, 926.5709090909091, 932.1674545454546, 874.7450909090909, 840.8825454545455, 853.2134545454545, 904.3181818181819, -1150.5516363636364, -59.48890909090909, 777.2292727272727, 500.1932727272727, -350.2790909090909, -870.8374545454545, -1242.7143636363637, -1721.5507272727273, -2256.688727272727, -2874.3327272727274, -3335.4065454545453, -3479.9192727272725, -3314.0445454545456, -2966.8854545454546, -2480.627090909091, -2004.247090909091, -1609.0467272727274, -1205.4312727272727, -810.4703636363637, -408.54836363636366, -18.111272727272727, 527.2385454545455, 1140.138, 1763.9576363636363, 2382.4725454545455, 2817.3654545454547, 3056.5532727272725, 3112.2052727272726, 3054.8830909090907, 2795.422727272727, 2479.0796363636364, 2104.8105454545453, 1703.6003636363637, 1336.3750909090909, 1037.9901818181818, 851.9767272727273, 729.4547272727273, 571.4005454545454, 442.28763636363635, 342.21363636363634, 255.96218181818182, 144.77581818181818, 63.64381818181818, -19.834, -54.35618181818182, -120.92618181818182, -154.68545454545455, -113.53163636363637, -10.044545454545455, 61.463454545454546, 1954.5996363636364, 3195.469818181818, 2997.7472727272725, 3187.572181818182, 3913.4625454545453, 4274.6367272727275, 3714.9394545454547, 2649.755818181818, 2077.5801818181817, 1800.1232727272727, 1509.3941818181818, 1159.2194545454545, 766.558, 332.44254545454544, -111.68472727272727, -501.59654545454543, -863.8265454545455, -1189.0649090909092, -1439.7418181818182, -1602.2585454545454, -1635.2712727272726, -1558.6678181818181, -1477.0972727272726, -1383.1714545454545, -1308.3532727272727, -1193.2563636363636, -1078.2861818181818, -1030.297090909091, -979.662, -864.0967272727273, -808.7350909090909, -762.1630909090909, -742.6021818181819, -735.8609090909091, -766.9365454545455, -853.4130909090909, -1005.4963636363636, -1210.2994545454546, -1459.8449090909091, -1700.0047272727272, -1934.8685454545455, -2121.778909090909, -2308.4249090909093, -2490.2807272727273, -2639.950909090909, -2770.953636363636, -2841.104363636364, -2864.654727272727, -2823.7412727272726, -2737.5565454545454])
        self.scaler.scale_ = np.array([814.7473143043082, 1115.9020731714145, 1117.0988663444562, 1109.845661696368, 1080.7824617385734, 1008.4789922751648, 833.6232977953962, 681.6479912041068, 593.5564387775169, 531.4368192815265, 504.24826127511346, 494.53505402165183, 499.0602841030917, 513.9635527861826, 537.9731883209404, 558.9994336955101, 573.0950935488671, 586.3453229400625, 609.8285855241988, 630.3325880990953, 638.5024397262431, 642.742241651483, 644.4817997908752, 654.740885526077, 669.3757344814602, 674.520842022795, 667.8509620617028, 650.3636203802076, 616.4236248540029, 576.4894774303916, 538.2611019789589, 512.1247638052781, 485.33001799750053, 470.4796622684818, 465.0058264595427, 461.2983081730016, 459.04198801438463, 458.33950221253, 458.0334156613971, 454.9996332181244, 456.21522817801775, 461.80055114073286, 462.9926465464279, 463.2811059043601, 463.80501058134786, 454.49066046009665, 435.8555468070954, 418.1077885989937, 397.18654341603457, 377.4827254511353, 999.1016302092477, 932.293620753313, 776.7581114115276, 688.9496422580323, 617.2045927827066, 602.872219024511, 549.745587011824, 467.63063810191466, 433.43533126308483, 392.68150387658557, 374.7774451611525, 357.9959830341156, 352.1948422561971, 349.4110478971645, 342.10391491769997, 331.6428905148697, 324.9182015764922, 328.2118608103038, 337.33225686233214, 356.5079503792353, 379.3247444281807, 402.0405864109814, 415.7869739983972, 422.3338736394152, 418.11449699156856, 408.52031056869237, 393.64047787977967, 368.93471866944446, 359.6884118775232, 343.9754014410941, 325.7476826536885, 321.75269618247825, 303.0098035604107, 292.3532110904704, 282.5252233229553, 267.8407150831094, 258.9262621457962, 251.21850250829928, 247.8126123629483, 240.0516891525485, 235.58461021421797, 234.66703942134012, 231.42888664880246, 232.87269186843196, 228.60074008947257, 237.10150537357038, 243.89230443092728, 236.17030177948197, 229.00512712611817, 226.84937722442038, 1212.0526671372047, 904.7830193998165, 865.1967954514587, 750.9272977444086, 639.1854556556235, 611.6254192648281, 601.7999963630878, 550.1799841162725, 509.50582889685165, 480.2438181017959, 452.2322916895816, 434.99273062914324, 422.05260420461883, 410.0071754780699, 399.2089792898613, 397.5836531652984, 408.6268118085175, 418.16736621335957, 437.9128639741969, 470.68296089676505, 493.295700956786, 505.3584995570106, 499.068984030951, 486.98583422314937, 474.84328271584906, 465.36527642183756, 454.8647819727756, 441.7165024596171, 443.1095746466152, 432.18814134281286, 422.09513115484754, 399.9601116846655, 378.0733300240895, 354.10179105229963, 329.22305407662026, 306.8734662850231, 292.9857191044875, 275.95698327962884, 267.7895101168609, 255.97122453842857, 251.20978336550837, 243.61790449875326, 239.8886403767764, 235.85812791402284, 235.3728998787297, 237.51996300782764, 237.6598586551795, 234.9277971654093, 232.40752078441253, 225.86776140077734, 10839.860481143362, 11062.686127440391, 10460.266213306128, 9644.068535148488, 9003.188118187853, 8470.234799611864, 8343.721219654024, 7657.145667390238, 6889.052031009115, 6545.285966259097, 6424.631954303664, 6180.293107962603, 5994.39538969874, 6158.318971700187, 6068.927066881346, 5939.183362731445, 5915.09587529673, 5851.986637517729, 5831.601931683629, 5783.251490672546, 5977.892636582751, 5936.7476529694295, 5720.233231965442, 5599.7055882906225, 5513.053457597131, 5523.517488004008, 5687.141371942149, 5861.7483509683325, 5739.405387689839, 5651.678072153421, 5533.003866004999, 5376.015554032481, 5113.80763630896, 4857.105754493903, 4512.208499730022, 4369.635836508446, 4044.769251789944, 4005.723107190031, 3906.589484462417, 3910.5867219634792, 3948.2255551802523, 4049.9515945570506, 4241.7898700254, 4243.761775775587, 4383.787125458482, 4408.898444092657, 4359.483979776796, 4366.819153657481, 4216.703440698766, 4216.342476972641, 14445.183909350866, 14944.61472875653, 15757.778073053927, 15344.406241076678, 14290.622028491254, 13186.393283096359, 11735.269610415391, 10092.192290144128, 8711.583661926565, 8059.793736985275, 7870.4198754457575, 7940.009362441909, 8176.469113833301, 8519.554596123788, 8934.319193131441, 9362.388681753131, 9715.219064773759, 9968.91863787392, 10177.678675291581, 10234.93619460625, 10200.766339481992, 10175.673588506199, 10131.031693674096, 10321.509332396674, 10515.062265798018, 10624.5559105947, 10656.266823640266, 10665.385699314227, 10521.962741841317, 10082.548044509782, 9647.971972399371, 9059.17292179678, 8499.087313177677, 8042.385524154177, 7636.684589954541, 7283.630610635431, 6905.017655032767, 6545.35470791861, 6300.3200579445165, 6133.629085504053, 5985.308335038291, 5814.9867995564155, 5751.735154814976, 5650.401186262498, 5693.648971924609, 5735.9772019648035, 5674.255644348856, 5515.050792043283, 5378.303618396043, 5177.103042500167, 13034.074750231306, 14434.08354696357, 14975.453307017948, 14304.493287027184, 12916.210979296073, 11522.699132078205, 10320.336637751509, 9280.175890878785, 8020.187040072861, 6935.611711193192, 6431.682327176265, 6320.156124856959, 6528.3331109653745, 6924.322159550659, 7383.715267820083, 7774.0693194483465, 8133.644166239671, 8340.568055646914, 8425.193148100327, 8384.699533450515, 8304.460381848052, 8114.509548704638, 7863.012990161413, 7663.384307961616, 7702.885702320697, 7815.888086252443, 7971.164110279572, 8111.39634041964, 8076.890680348576, 7834.135339914575, 7565.244258882237, 7194.72796502231, 6865.584811289829, 6582.728304345816, 6319.125875206227, 6013.90555413728, 5801.25879560835, 5698.649662504557, 5705.291744730697, 5769.763002788014, 5828.267128556373, 5909.796180105675, 6036.107983852253, 6145.472080432376, 6195.015198965069, 6203.92448428893, 6129.048659800232, 6025.884590985595, 5864.39764906276, 5726.689119130368])

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
      #print(f"Predicted Gesture: {max_idx}")
      print(f"Inference time: {((time.time() - start_time) * 1000):.4f} ms\n")

      # Clean up
      input_buffer.close()
      output_buffer.close()
      return max_idx

