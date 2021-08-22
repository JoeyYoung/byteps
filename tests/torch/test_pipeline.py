# Copyright 2021 Bytedance Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import torch
import math, sys
import numpy as np
from torch.nn.modules import linear
import torch.optim as optim
import byteps.torch as bps
from utils import LinearRegression, check_weight, check_grad

# initialization
bps.init()
rank, size = bps.rank(), bps.size()
print(f"running on rank={rank}")

device_id = bps.local_rank()

# prepare raw data
x_np = np.array([1.0, 1.0, 1.0], dtype=np.float)
w_np = np.array([1.0, 1.0, 1.0], dtype=np.float)
y_np = np.array([2.0], dtype=np.float)
learning_rate = 0.01

# define numpy model
linear_regression = LinearRegression(weight=w_np, lr=learning_rate)

# move tensor to GPU
x = torch.from_numpy(x_np).type(torch.float32).to(device_id)
y = torch.from_numpy(y_np).type(torch.float32).to(device_id)

# Use the nn package to define our model and loss function.
model = torch.nn.Linear(3, 1, bias=False).cuda()
with torch.no_grad():
    model.weight.fill_(1.0)

loss_fn = torch.nn.MSELoss(reduction='sum')

optimizer = optim.SGD(model.parameters(), lr=learning_rate)
optimizer = bps.DistributedOptimizer(optimizer,
                                     named_parameters=model.named_parameters(),
                                     staleness=1)

print(f'x = {x}, y = {y}, x.dtype = {x.dtype}, y.dtype = {y.dtype}')

iteration = 20
for i in range(iteration):
    optimizer.zero_grad()
    linear_regression.zero_grad()

    y_pred = model(x)
    loss = loss_fn(y_pred, y)

    loss.backward()
    linear_regression.backward(x_np, y_np)

    check_weight(model, linear_regression, rank, i)
    optimizer.step()
    linear_regression.step(should_skip=(i == 0))
    check_grad(model, linear_regression, rank, i)

print('All good!')
