# NUS_CG4002_Capstone_B08

# Hardware/Software AI

Steps for generating gesture inferencing AI

1. Create a .csv file for the trained dataset. Currently using: `data/latest2/combined_3.csv` and `data/leg/combined_leg.csv`
2. Run the training AI using `RealMLP.py`. Altering the file_path according to the desired dataset accordingly, and the accuracies and confusion matries would be printed.
3. Under the `weights_biases` folder, the respective weights and biases would be updated after running the training.
4. Manually transfer the trained weights and biases into the `HLS/prediction.cpp` and export the RTL to get the IP block.
5. Use the IP block to generate the bitstream using vivado.
6. The .bit and .hwh will be generated and transfer that into the ultra96 board using scp.
7. The `AI50Class.py` and `LegAIClass.py` within the `bitstream` folder are classes that instantiates the model and can be inferenced through the `predict()` method.
8. Examples of using the classes can be seen by running the `test.py` file also in the `bitstream` folder.
9. In the actual system, the classes are utilized by `PredictionService.py` under `ext comms`.
