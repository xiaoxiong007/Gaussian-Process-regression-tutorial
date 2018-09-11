import numpy as np
from scipy.optimize import minimize
import time
"""
Python Gaussian Process module.
This code is supposed to accompany the tutorial 'An Introduction to Gaussian Processes'
P.L.Green
University of Liverpool
01/09/18
"""

# Kernel function (squared exponential with length-scale L)
def Kernel(squared_distance,L):
    return np.exp(-1/(2*L**2)*squared_distance)

# Function that creates and inverts gram matrix for a squared exponential kernel with length-scale L.
def FindGramMatrix(X,L,Sigma,N):    
    squared_distances = FindSquaredDistances(X)
    K = Kernel(squared_distances,L)
    C = K + Sigma**2*np.identity(N)                   
    InvC = np.linalg.inv(C)
    return K,C,InvC

# Function that finds the squared distances between inputs points (efficiently). 
def FindSquaredDistances(X):
    if np.size(X[0]) == 1:
        Xsq = X**2
        squared_distances = -2*np.outer(X,X) + (Xsq[:,None] + Xsq[None,:])
    else:
        Xsq = np.sum(X**2,1)
        squared_distances = -2.*np.dot(X,X.T) + (Xsq[:,None] + Xsq[None,:])
    return squared_distances

# Returns negative log-likelihood function in a form suitable for scipy.optimize.fmin_bfgs.
def NegLogLikelihoodFun(Theta,a):
    X = a[0]
    Y = a[1]
    N = a[2]
    L = Theta[0]
    Sigma = Theta[1]
    K,C,InvC = FindGramMatrix(X,L,Sigma,N)
    (Sign,LogDetC) = np.linalg.slogdet(C)
    LogDetC = Sign*LogDetC
    return 0.5*LogDetC + 0.5*np.dot(Y,np.dot(InvC,Y))

# Derivative of matrix C w.r.t L (length scale).
def dC_dL_Fun(X,L,K,N):
    squared_distances = FindSquaredDistances(X)
    return np.power(L,-3) * np.multiply(squared_distances,K)

# Derivative of matrix C w.r.t sigma (noise std)
def dC_dSigma_Fun(Sigma, K, N):
    return 2*Sigma*np.eye(N) 

# Derivative of the negative log-likelihood w.r.t hyperparameters in a form suitable for scipy.optimize.fmin_bfgs.
def dNLL_dTheta(Theta,a):
    X = a[0]
    Y = a[1]
    N = a[2]
    L = Theta[0]
    Sigma = Theta[1]
    K,C,InvC = FindGramMatrix(X,L,Sigma,N)
    dC_dL = dC_dL_Fun(X,L,K,N)   # Find dC / dL
    dC_dSigma = dC_dSigma_Fun(Sigma,K,N) # Find dC / dSigma
    dLogL_dL = 0.5*np.trace( np.dot(InvC,dC_dL) ) - 0.5*np.dot(Y,np.dot(InvC,np.dot(dC_dL,np.dot(InvC,Y))))  # Find dlogp / dL
    dLogL_dSigma = 0.5*np.trace( np.dot(InvC,dC_dSigma) ) - 0.5*np.dot(Y,np.dot(InvC,np.dot(dC_dSigma,np.dot(InvC,Y))))     # Find dlogp / dSigma
    Gradient = np.array([dLogL_dL, dLogL_dSigma])  # Gradient vector
    return Gradient

# Update hyperparameters using scipy.minimize
def Train(L0, Sigma0, X, Y, N):
    Theta0 = [L0,Sigma0]
    a = (X,Y,N)    
    b1 = (1e-6,4)
    b2 = (1e-6,1)
    bnds = (b1,b2)
    start_time = time.time()
    sol = minimize(NegLogLikelihoodFun, x0=Theta0, args=(a,), method='SLSQP', jac=dNLL_dTheta, bounds=bnds)
    elapsed_time = time.time() - start_time
    ThetaOpt = sol.x
    L = ThetaOpt[0]
    Sigma = ThetaOpt[1]
    K, C, InvC = FindGramMatrix(X,L,Sigma,N)
    return L, Sigma, K, C, InvC, elapsed_time

# Callback function for the fmin_bfgs optimisation routine
def callbackF(Theta):
    print Theta[0], Theta[1]
       
# GP prediction
def Predict(X, xStar, L, Sigma, Y, K, C, InvC, N):
    if np.size(X[0]) == 1:
        squared_distances = (X-xStar)**2
    else:
        squared_distances = np.sum((X-xStar)**2,1)   
    k = Kernel(squared_distances,L)
    c = 1 + Sigma**2   # Always true for this particular kernel
    yStarMean = np.dot(k,np.dot(InvC,Y))
    yStarStd = np.sqrt( c - np.dot(k,np.dot(InvC,k)) )
    return yStarMean, yStarStd


