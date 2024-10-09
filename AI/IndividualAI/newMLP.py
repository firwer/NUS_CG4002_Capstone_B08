import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import os

# Custom Dataset Class
class MNISTDataset(Dataset):
    def __init__(self, data, is_test=False):
        if is_test:
            self.X = data.values.astype(np.float32)
            self.X /= 255.0
            self.y = None  # No labels for test data
        else:
            self.X = data.iloc[:, 1:].values.astype(np.float32)
            self.y = data.iloc[:, 0].values.astype(np.int64)
            self.X /= 255.0
    
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        if self.y is not None:
            return torch.tensor(self.X[idx]), torch.tensor(self.y[idx])
        else:
            return torch.tensor(self.X[idx])

# Updated MLP Model
class MLP(nn.Module):
    def __init__(self, input_size=784, hidden_size1=128, hidden_size2=64, output_size=10):
        super(MLP, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size1)
        self.fc2 = nn.Linear(hidden_size1, hidden_size2)
        self.fc3 = nn.Linear(hidden_size2, output_size)
    
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x

# Load the entire dataset
full_data = pd.read_csv("C:/Users/leona/Documents/Capstone/newMLP/train.csv")  # Replace with your CSV file path

# Split into features and labels
dataset = MNISTDataset(full_data, is_test=False)

# Convert to DataFrame to simplify splitting
X = full_data.iloc[:, 1:]
y = full_data.iloc[:, 0]

# First split: train and temp (validation + test)
X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

# Second split: validation and test (50-50 of the temp set)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp)

# Convert splits back to DataFrames for compatibility with MNISTDataset
train_data = pd.DataFrame(np.column_stack((y_train, X_train)), columns=full_data.columns)
val_data = pd.DataFrame(np.column_stack((y_val, X_val)), columns=full_data.columns)
test_data = pd.DataFrame(np.column_stack((y_test, X_test)), columns=full_data.columns)

# Create Datasets
train_dataset = MNISTDataset(train_data)
val_dataset = MNISTDataset(val_data)
test_dataset = MNISTDataset(test_data)

# Create DataLoaders
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

# Model, Loss Function, Optimizer
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = MLP().to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training Loop
epochs = 10
for epoch in range(epochs):
    model.train()
    running_loss = 0.0
    
    # Training phase
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        inputs = inputs.view(inputs.size(0), -1)
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
    
    print(f"Epoch [{epoch+1}/{epochs}], Training Loss: {running_loss/len(train_loader):.4f}")
    
    # Evaluate Training Accuracy
    model.eval()
    correct_train = 0
    total_train = 0
    with torch.no_grad():
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            inputs = inputs.view(inputs.size(0), -1)
            
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            total_train += labels.size(0)
            correct_train += (predicted == labels).sum().item()
    
    print(f"Training Accuracy: {100 * correct_train / total_train:.2f}%")
    
    # Evaluate Validation Accuracy
    correct_val = 0
    total_val = 0
    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            inputs = inputs.view(inputs.size(0), -1)
            
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            total_val += labels.size(0)
            correct_val += (predicted == labels).sum().item()
    
    print(f"Validation Accuracy: {100 * correct_val / total_val:.2f}%")

# Evaluate on Test Data
model.eval()
correct_test = 0
total_test = 0
with torch.no_grad():
    for inputs, labels in test_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        inputs = inputs.view(inputs.size(0), -1)
        
        outputs = model(inputs)
        _, predicted = torch.max(outputs.data, 1)
        total_test += labels.size(0)
        correct_test += (predicted == labels).sum().item()

print(f"Test Accuracy: {100 * correct_test / total_test:.2f}%")

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

# Save Model (optional)
torch.save(model.state_dict(), "mnist_mlp.pth")
