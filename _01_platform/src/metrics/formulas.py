"""Canonical metric functions. Do not add unresolved public names here."""
import math

def leverage(I, R):
    if I <= 0: return None
    return R / I

def yield_metric(I, O, R):
    if I <= 0: return None
    return (R * O) / (I * I)

def token_snr(I, O):
    if I + O <= 0: return None
    return O / (I + O)

def log_leverage(I, R):
    L = leverage(I, R)
    if L is None or L <= 0: return None
    return math.log10(L)

def construction(R, W):
    if R <= 0: return None
    return W / R
