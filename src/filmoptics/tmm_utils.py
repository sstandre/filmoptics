# -*- coding: utf-8 -*-
"""
Utilities to calculate RAT of optical stacks with tmm_vec
"""

import numpy as np
from . import tmm_core as tmm
from functools import partial
from scipy.interpolate import interp1d


def cauchy_fn(A,B,C):
    def fn(lams):
        lams = lams*1.0
        return A+B*np.power(10,4)/np.power(lams,2)+C*np.power(10,9)/np.power(lams,4)
    return fn


def constant_fn(val):
    return partial(np.full_like, fill_value=val)

def n_eff(n1,n2,f):
    """
    Modelo de bruggeman. f es la fraccion de la especie 2.
    """
    if f == 0: return n1
    if f == 1: return n2
    e1 = n1**2
    e2 = n2**2
    #f = 1-f2
    omega = (1-f)*(e2-2*e1)+f*(e1-2*e2)
    return (np.sqrt(np.sqrt(omega**2 + 8*e1*e2)-omega))/2


def brugg_fn(n_a, n_b, f_b):
    def fn(lams):
        n1 = n_a(lams)
        n2 = n_b(lams)
        return n_eff(n1, n2, f_b)
    return fn

def load_fn(filename, skiprows=1):
    
    wv, I = np.loadtxt(filename, skiprows=skiprows, unpack=True)
    return interp1d(wv, I,fill_value=(I[0],I[-1]), bounds_error=False)


def load_interp_nk(filename, comments='#', skiprows=1, unit='nm'):
    '''Loads optical data and outputs interpolation functions for n and k. 
    Unit: `nm` or `um`
    '''
    scale = {'nm':1.0, 'um':1000.0}
    
    wv, n, k = np.loadtxt(filename, comments=comments, 
                      skiprows=skiprows, unpack=True)
    
    wv *= scale[unit]
    
    n_fn = interp1d(wv, n, fill_value=(n[0],n[-1]), bounds_error=False)
    k_fn = interp1d(wv, k, fill_value=(k[0],k[-1]), bounds_error=False)
    
    return n_fn, k_fn


def struct2tmm(struct, lams):
    '''Transforms a structure into three lists that can be fed into the 'tmm' package.'''
    n_list = []
    d_list = []
    c_list = []  
    
    for layer in struct:
        d_list.append(float(layer.t.get()))
        n_fn, k_fn = load_interp_nk(layer.indices.get())
        n_list.append(n_fn(lams) + k_fn(lams)*1.0j)
        c_list.append("ic"[layer.c.get()])
   
    return n_list, d_list, c_list


def calculate_RAT(struct, lams, pol='s', th_0=0):
    '''calulate R, T and A of a multilayer.'''
    n_list, d_list, c_list = struct2tmm(struct, lams)
    inc = 'i' in c_list[1:-1] #check if  any of the finite layers is incocherent
    if inc:
        RAT = tmm.inc_tmm(pol, n_list, d_list, c_list, th_0, lams)
    else:
        RAT = tmm.coh_tmm(pol, n_list, d_list, th_0, lams)

    return RAT['R'],  RAT['T']
