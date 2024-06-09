'''

Implementing Gradient Descent with Momentum.

'''

import numpy as np
import pandas as pd
import pickle
import sys

def load_model(file):
    with open(file) as f:
        return pickle.load(f)

def save_model(file, w1, b1, w2, b2, w3, b3):
    with open(file) as f:
        pickle.dump((w1, b1, w2, b2, w3, b3), f)

def init_params():
    w1 = np.random.randn(32, 784) * np.sqrt(1/784)
    b1 = np.zeros((32, 1))
    w2 = np.random.randn(10 , 32) * np.sqrt(1/32)
    b2 = np.zeros((10, 1))
    return w1, b1, w2, b2

def leaky_relu(z):
    return np.where(z > 0, z, (.01 * z))

def leaky_relu_deriv(z):
    return np.where(z>0, 1, .1)

def softmax(z):
    eps = 1e-6
    return np.exp(z + eps) / np.sum(np.exp(z + eps), axis = 0, keepdims=True)

def forward(x, w1, b1, w2, b2):
    z1 = np.dot(w1, x) + b1
    a1 = leaky_relu(z1)
    z2 = np.dot(w2, a1) + b2
    #print(f"Z2: {np.max(z2)}")
    try:
        a2 = softmax(z2)
    except RuntimeWarning:
        sys.exit("overflow!")
    return z1, a1, z2, a2

def one_hot(y):
    one_hot_y = np.zeros((np.max(y)+1, y.size)) #10, 60000
    one_hot_y[y, np.arange(y.size)] = 1
    return one_hot_y

def cat_cross(one_hot_y, w1, w2, a, lambd):
    fronorm = (lambd * (np.sum(np.square(w1)) / 60000) + (np.sum(np.square(w2)) / 60000))
    eps = 1e-10
    l = (-np.sum(one_hot_y * np.log(a + eps))) / 60000
    reg_l = l + fronorm
    return reg_l

def accuracy(y, a2):
    pred = np.argmax(a2, axis = 0)
    acc = np.sum(pred == y) / 60000 * 100
    return acc


def backward(x, one_hot_y, w2, w1, a2, a1, z2, z1, lambd):
    dz2 = a2 - one_hot_y
    dw2 = (np.dot(dz2, a1.T) + (2 * lambd * w2)) / 60000
    db2 = np.sum(dz2, axis = 1, keepdims=True) / 60000
    dz1 = np.dot(w2.T, dz2) * leaky_relu_deriv(z1)
    dw1 = (np.dot(dz1, x.T)  +  (2 * lambd * w1)) / 60000
    db1 = np.sum(dz1, axis=1, keepdims=True) / 60000
    return dw2, db2, dw1, db1

def momentum(beta, dw1, db1, dw2, db2, vdw1, vdb1, vdw2, vdb2):

    '''
    
    Computing the exponentially weighted averages of the derivatives of the loss.
    Or essentially adding 'momentum'
    
    '''

    vdw1 = (beta * vdw1) + ((1 - beta) * dw1)
    vdb1 = (beta * vdb1) + ((1 - beta) * db1)
    vdw2 = (beta * vdw2) + ((1 - beta) * dw2)
    vdb2 = (beta * vdb2) + ((1 - beta) * db2)
    return vdw1, vdb1, vdw2, vdb2


def update_momentum(w1, b1, w2, b2, vdw1, vdb1, vdw2, vdb2, alpha):
    w1 = w1 - alpha * vdw1
    b1 = b1 - alpha * vdb1
    w2 = w2 - alpha * vdw2
    b2 = b2 - alpha * vdb2
    return w1, b1, w2, b2

def gradient_descent_momentum(x, y, w1, b1, w2, b2, epochs, alpha, beta, lambd, file):
    one_hot_y = one_hot(y)

    '''
    
    Initializing terms for computing Exponentially weighted averages

    '''

    vdw1 = 0
    vdb1 = 0
    vdw2 = 0
    vdb2 = 0
    for epoch in range(epochs):
        z1, a1, z2, a2 = forward(x, w1, b1, w2, b2)

        l = cat_cross(one_hot_y, w1, w2, a2, lambd)
        acc = accuracy(y, a2)

        dw2, db2, dw1, db1 = backward(x, one_hot_y, w2, w1, a2, a1, z2, z1, lambd)

        vdw1, vdb1, vdw2, vdb2 = momentum(beta, dw1, db1, dw2, db2, vdw1, vdb1, vdw2, vdb2)

        w1, b1, w2, b2 = update_momentum(w1, b1, w2, b2, vdw1, vdb1, vdw2, vdb2, alpha)


        if epoch % 5 == 0:
            print(f"epoch: {epoch}")
            print(f"loss: {l}")
            print(f"acc: {acc}%")
            print(f"Z2: {np.max(z2)}\n") # to ensure lack of exploding gradients.

    save_model(file, w1, b1, w2, b2)
    return w1, b1, w2, b2
    
def model(x, y, epochs, alpha, beta, lambd, file):
    try:
        w1, b1, w2, b2 = load_model(file)
        print("found model! initializing model params!")

    except FileNotFoundError:
        print("model not found! initializing new params!")
        w1, b1, w2, b2= init_params()
    
    w1, b1, w2, b2 = gradient_descent_momentum(x, y, w1, b1, w2, b2, epochs, alpha, beta, lambd,file)
    return w1, b1, w2, b2

if __name__ == "__main__":

    data = np.array(pd.read_csv('data/fashion-mnist_train.csv'))

    X_train = data[:, 1:786].T / 255 #784, 60000
    Y_train = data[:, 0].reshape(1, -1) #1, 60000

    file = '../models/BatchNN.pkl'

    w1, b1, w2, b2 = model(X_train, Y_train, epochs = 250, alpha = .1, beta = .7, lambd = 10, file = file)