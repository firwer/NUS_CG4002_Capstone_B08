import pandas as pd 
from ast import literal_eval
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import os

# Load and preprocess the dataset
file_path = 'data/combined_2.csv'
df = pd.read_csv(file_path, converters={'ax': literal_eval, 'ay': literal_eval, 'az': literal_eval,
                                        'gx': literal_eval, 'gy': literal_eval, 'gz': literal_eval})

# Combine ax, ay, az, gx, gy, gz columns into a single feature list
X_combined = [ax + ay + az + gx + gy + gz for ax, ay, az, gx, gy, gz in zip(df['ax'], df['ay'], df['az'], 
                                                                             df['gx'], df['gy'], df['gz'])]

# Pad sequences to the max length
max_length = max(len(sequence) for sequence in X_combined)
X_padded = np.array([np.pad(sequence, (0, max_length - len(sequence)), 'constant') for sequence in X_combined])

# Reshape to fit input requirements of the model
X_padded = X_padded.reshape((X_padded.shape[0], -1))

# Encode the gesture labels
gesture_encoder = LabelEncoder()    
gestures_encoded = gesture_encoder.fit_transform(df['gesture'])
y = torch.tensor(gestures_encoded, dtype=torch.long)

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_padded)
X_scaled = torch.tensor(X_scaled, dtype=torch.float32)

# Define MLP model for gesture classification
class GestureMLP(nn.Module):
    def __init__(self, input_size, num_classes=7):  # 7 classes for the 7 gestures
        super(GestureMLP, self).__init__()
        self.fc1 = nn.Linear(input_size, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, num_classes)
        self.dropout = nn.Dropout(0.5)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x

# Initialize and set up the model
input_size = X_scaled.shape[1]
model = GestureMLP(input_size=input_size, num_classes=len(gesture_encoder.classes_))
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Split the data into train, validation, and test sets (60% train, 20% validation, 20% test)
X_train, X_temp, y_train, y_temp = train_test_split(X_scaled, y, test_size=0.4, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

# Datasets and DataLoaders
train_dataset = torch.utils.data.TensorDataset(X_train, y_train)
val_dataset = torch.utils.data.TensorDataset(X_val, y_val)
test_dataset = torch.utils.data.TensorDataset(X_test, y_test)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

# Training loop
num_epochs = 10
for epoch in range(num_epochs):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for X_batch, y_batch in train_loader:
        optimizer.zero_grad()
        outputs = model(X_batch)
        loss = criterion(outputs, y_batch)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()

        # Calculate training accuracy
        _, predicted = torch.max(outputs, 1)
        total += y_batch.size(0)
        correct += (predicted == y_batch).sum().item()

    train_accuracy = correct / total
    print(f"Epoch {epoch + 1}/{num_epochs}, Loss: {running_loss / len(train_loader)}, Accuracy: {train_accuracy * 100:.2f}%")

    # Validate the model
    model.eval()
    val_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for X_batch, y_batch in val_loader:
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            val_loss += loss.item()

            # Calculate validation accuracy
            _, predicted = torch.max(outputs, 1)
            total += y_batch.size(0)
            correct += (predicted == y_batch).sum().item()

    val_accuracy = correct / total
    print(f"Validation Loss: {val_loss / len(val_loader)}, Validation Accuracy: {val_accuracy * 100:.2f}%")

# Test the model on the test set
test_loss = 0.0
correct = 0
total = 0

with torch.no_grad():
    for X_batch, y_batch in test_loader:
        outputs = model(X_batch)
        loss = criterion(outputs, y_batch)
        test_loss += loss.item()

        # Calculate test accuracy
        _, predicted = torch.max(outputs, 1)
        total += y_batch.size(0)
        correct += (predicted == y_batch).sum().item()

test_accuracy = correct / total
print(f"Test Loss: {test_loss / len(test_loader)}, Test Accuracy: {test_accuracy * 100:.2f}%")

# Save Weights and Biases
save_dir = "weights_biases"
os.makedirs(save_dir, exist_ok=True)

def save_weights_biases(model, save_dir):
    for name, param in model.named_parameters():
        if param.requires_grad:
            file_name = os.path.join(save_dir, f"{name}.txt")
            with open(file_name, 'w') as f:
                # Write the header
                f.write(f"Layer: {name}\n")
                f.write(f"Shape: {param.shape}\n")
                f.write("Values:\n")
                # Write the values
                values = param.cpu().detach().numpy()
                
                if len(values.shape) == 1:  # 1D array (biases)
                    formatted_values = ", ".join(f"{v:.6f}" for v in values)
                    f.write(f"{{{formatted_values}}}")
                else:  # 2D array (weights)
                    f.write("{\n")
                    for row in values:
                        formatted_row = ", ".join(f"{v:.6f}" for v in row)
                        f.write(f"  {{{formatted_row}}},\n")
                    f.write("}")

save_weights_biases(model, save_dir)
print(f"Weights and biases saved to {save_dir}")

# Load the new dataset
debug_file_path = 'data/latest/red_debug_leo_my_data.csv'
debug_df = pd.read_csv(debug_file_path, converters={
    'ax': literal_eval, 'ay': literal_eval, 'az': literal_eval, 
    'gx': literal_eval, 'gy': literal_eval, 'gz': literal_eval
})

# Process each row in the debug dataset
predicted_gestures = []
model.eval()  # Set model to evaluation mode

for idx, row in debug_df.iterrows():
    # Combine ax, ay, az, gx, gy, gz columns into a single feature list
    combined_input = row['ax'] + row['ay'] + row['az'] + row['gx'] + row['gy'] + row['gz']
    
    # Pad sequences to the max length
    padded_input = np.pad(combined_input, (0, max_length - len(combined_input)), 'constant')
    
    # Scale the input
    scaled_input = scaler.transform([padded_input])  # Convert to 2D array for scaler
    
    # Convert to tensor
    tensor_input = torch.tensor(scaled_input, dtype=torch.float32)
    torch.set_printoptions(sci_mode=False, precision=4)
    print(tensor_input)
    # Predict using the model
    with torch.no_grad():
        output = model(tensor_input)
        _, predicted_class = torch.max(output, 1)
    
    # Decode the predicted class
    predicted_gesture = gesture_encoder.inverse_transform([predicted_class.item()])
    predicted_gestures.append(predicted_gesture[0])

# Print predicted gestures in sequence
for idx, gesture in enumerate(predicted_gestures):
    print(f"Gesture {idx + 1}: {gesture}")
    

array = [[    0.8467,      0.5934,      0.1193,     -0.4841,     -0.7397,
             -0.6132,     -0.2122,     -0.0915,      0.0555,      0.3275,
              0.5734,      0.6128,      0.6848,      0.7406,      0.5952,
              0.5137,      0.4098,      0.3145,      0.2701,      0.2187,
              0.3575,      0.4377,      0.4365,      0.3804,      0.2599,
              0.2324,      0.3056,      0.4266,      0.5967,      0.6837,
              0.8167,      0.8373,      0.8557,      0.9365,      0.7739,
              0.8101,      0.5906,      0.4764,      0.1072,     -0.3892,
             -0.9015,     -1.5025,     -1.4693,     -1.4773,     -1.7120,
             -1.2733,     -0.9836,     -0.4495,     -0.5647,     -0.5471,
             -0.0592,      0.1818,     -0.0545,     -0.1130,     -0.2203,
             -0.2505,     -0.2429,     -0.3004,     -0.3744,     -0.4147,
              1.2624,      2.0612,      1.8464,      1.5021,      0.8507,
             -0.6759,     -1.3360,     -0.7976,     -0.8781,     -1.0312,
             -0.9162,     -0.6929,     -0.4565,     -0.5358,     -0.5117,
             -0.2536,     -0.1445,      0.3312,      1.0354,      0.9996,
              2.3631,      2.4496,      1.9861,      1.7285,      1.1537,
              0.5502,      0.0815,     -0.2681,     -0.4278,     -0.5149,
             -0.3071,     -0.5303,     -0.5833,     -0.6783,     -0.8451,
             -0.6116,     -0.8309,     -0.7965,     -0.8246,      0.1698,
             -0.4974,      1.4708,      1.7444,      1.2308,      2.0363,
              1.5203,      1.4497,      1.7256,      0.0953,      1.1515,
              1.0886,     -0.4693,     -0.8166,     -0.0786,     -0.6256,
             -1.5067,     -1.4533,     -1.3690,     -1.0537,     -0.6556,
              0.2014,      0.6941,      0.7355,      0.5210,      0.1715,
              0.0967,     -0.0306,     -0.1950,     -0.1828,     -0.1063,
             -0.0241,      0.0841,     -0.0137,     -0.1012,      0.1322,
              0.4202,      0.5705,      0.8059,      0.9349,      1.2809,
              1.3727,      1.6480,      2.0215,      2.1632,      1.9136,
              1.3616,      1.0293,      0.8171,      0.5193,      0.1967,
              0.0861,      0.0570,      0.0023,      0.0289,      0.0551,
              0.0118,      0.0804,      0.2042,      0.4677,      0.8207,
              0.6337,      0.4133,     -0.5286,      0.2884,      1.5460,
              1.2925,      2.0659,      2.0479,      2.6209,      2.2949,
              1.5360,      1.4659,      1.7657,      1.4975,      1.2237,
              1.0669,      0.8816,      0.8364,      0.8779,      0.9787,
              0.1124,      0.4669,      0.9121,      0.8343,      0.5896,
              0.0590,     -0.1294,     -0.2951,     -0.6888,     -0.8154,
             -0.7747,     -0.6123,     -0.8936,     -1.1913,     -0.6651,
             -0.4398,      0.3049,      0.4349,      1.0017,      0.3015,
              1.1965,      0.6780,     -0.0252,      0.0274,      0.0265,
              0.1112,      0.0986,     -0.0064,     -0.3403,      0.0629,
              0.1079,     -0.1477,     -0.3103,     -0.5393,     -0.3891,
             -0.4979,     -0.7759,     -0.7600,     -0.6278,     -0.5843,
             -0.7608,     -1.0321,     -3.2254,     -4.2025,     -2.9364,
             -2.0785,     -1.3801,     -1.5836,     -0.5427,      0.9201,
              0.1450,     -0.4947,      0.4227,      0.9223,     -0.5156,
             -0.5131,      0.1476,      0.5260,      1.0610,      1.4454,
              0.0922,     -0.2041,     -0.1244,     -0.1020,      0.1974,
              0.3336,      0.3908,      0.5730,      0.7355,      0.7359,
              0.7682,      0.7329,      0.5973,      0.6693,      0.8496,
              0.9265,      0.8799,      0.8365,      0.6695,      0.6835,
              0.3525,      0.3225,      0.1290,     -0.0753,     -0.5007,
             -0.7390,     -0.8515,     -0.9307,     -0.9811,     -0.9280,
             -0.7819,     -0.6900,     -0.6086,     -0.4800,     -0.5351,
             -0.5572,     -0.4750,     -0.5269,     -0.4806,     -1.0276,
             -1.2358,     -1.7372,     -1.6969,      0.3143,      0.6626,
              0.5130,      1.3022,      0.9121,      1.1318,      0.4178,
             -0.0245,      0.2570,      0.1127,     -0.3650,     -0.4467,
             -0.3923,     -0.3568,     -0.2355,      0.0844,      0.1618,
             -0.3467,      0.5354,      1.1786,      1.6682,      1.7813,
              1.8614,      1.3527,      0.8305,      0.7812,      0.5832,
              0.3568,      0.2042,      0.2053,      0.2343,      0.0130,
             -0.1353,     -0.3507,     -0.4038,     -0.4626,     -0.2930,
             -0.1405,      0.3944,      0.9024,      1.0574,      1.2929,
              1.4101,      1.3469,      1.1307,      0.9220,      0.5804,
              0.4706,      0.4495,      0.3501,      0.2649,      0.0382,
             -0.1351,     -0.2763,     -0.5894,     -1.1209,     -1.2594,
             -1.7104,     -1.8693,     -1.4653,     -1.7458,     -1.3913,
             -0.9375,     -0.8180,     -0.2898,     -0.4238,     -0.4722,
              0.1653,      0.4027,     -0.0790,     -0.0001,      0.6505,
              0.6199,      0.4067,      0.2739,     -0.0744,      0.0350]]

tensor_input = torch.tensor(array, dtype=torch.float32)

with torch.no_grad():
    output = model(tensor_input)
    _, predicted_class = torch.max(output, 1)

# Decode the predicted class
predicted_gesture = gesture_encoder.inverse_transform([predicted_class.item()])
predicted_gestures.append(predicted_gesture[0])
print(predicted_class.item())
print(gesture_encoder.classes_)