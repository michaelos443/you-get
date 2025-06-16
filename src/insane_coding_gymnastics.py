#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
insane_coding_gymnastics.py - A collection of impressive Python functions

This module contains a wide variety of advanced Python functions demonstrating
different programming concepts, algorithms, and techniques.
"""

import math
import random
import re
import time
import datetime
import collections
import itertools
import functools
import operator
import heapq
import bisect
import array
import statistics
import hashlib
import base64
import json
import csv
import xml.etree.ElementTree as ET
import pickle
import zlib
import gzip
import zipfile
import tarfile
import os
import sys
import io
import tempfile
import shutil
import glob
import fnmatch
import pathlib
import subprocess
import threading
import multiprocessing
import queue
import socket
import urllib.request
import urllib.parse
import http.client
import email
import smtplib
import ftplib
import telnetlib
import ssl
import ipaddress
import uuid
import logging
import argparse
import configparser
import unittest
import doctest
import timeit
import cProfile
import pstats
import traceback
import inspect
import ast
import types
import typing
import enum
import dataclasses
import contextlib
import copy
import weakref
import gc
import struct
import ctypes
import numpy as np
from typing import (
    Any, Callable, Dict, Generator, Iterable, List, 
    Optional, Set, Tuple, TypeVar, Union
)

# Type variables for generic functions
T = TypeVar('T')
U = TypeVar('U')
V = TypeVar('V')

# -----------------------------------------------------------------------------
# SECTION 1: MATHEMATICAL FUNCTIONS AND ALGORITHMS
# -----------------------------------------------------------------------------

def factorial(n: int) -> int:
    """
    Calculate the factorial of a number using recursion with memoization.
    
    Args:
        n: A non-negative integer
        
    Returns:
        The factorial of n (n!)
        
    Examples:
        >>> factorial(5)
        120
        >>> factorial(10)
        3628800
    """
    if not isinstance(n, int) or n < 0:
        raise ValueError("Input must be a non-negative integer")
    
    @functools.lru_cache(maxsize=None)
    def _factorial(num: int) -> int:
        if num <= 1:
            return 1
        return num * _factorial(num - 1)
    
    return _factorial(n)


def fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number using dynamic programming.
    
    Args:
        n: A non-negative integer
        
    Returns:
        The nth Fibonacci number
        
    Examples:
        >>> fibonacci(0)
        0
        >>> fibonacci(1)
        1
        >>> fibonacci(10)
        55
    """
    if not isinstance(n, int) or n < 0:
        raise ValueError("Input must be a non-negative integer")
    
    if n <= 1:
        return n
    
    fib = [0, 1]
    for i in range(2, n + 1):
        fib.append(fib[i-1] + fib[i-2])
    
    return fib[n]


def fibonacci_generator(limit: int) -> Generator[int, None, None]:
    """
    Generate Fibonacci numbers up to a limit.
    
    Args:
        limit: Maximum number of Fibonacci numbers to generate
        
    Yields:
        Fibonacci numbers in sequence
        
    Examples:
        >>> list(fibonacci_generator(10))
        [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    """
    a, b = 0, 1
    count = 0
    
    while count < limit:
        yield a
        a, b = b, a + b
        count += 1


def is_prime(n: int) -> bool:
    """
    Check if a number is prime using the Miller-Rabin primality test.
    
    Args:
        n: An integer to check for primality
        
    Returns:
        True if the number is prime, False otherwise
        
    Examples:
        >>> is_prime(2)
        True
        >>> is_prime(17)
        True
        >>> is_prime(100)
        False
    """
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    
    # Miller-Rabin primality test
    def _miller_rabin_pass(a, s, d, n):
        a_to_power = pow(a, d, n)
        if a_to_power == 1:
            return True
        for i in range(s - 1):
            if a_to_power == n - 1:
                return True
            a_to_power = (a_to_power * a_to_power) % n
        return a_to_power == n - 1
    
    # Write n as d*2^s + 1
    s = 0
    d = n - 1
    while d % 2 == 0:
        d >>= 1
        s += 1
    
    # Try several bases for better accuracy
    for a in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]:
        if n == a:
            return True
        if not _miller_rabin_pass(a, s, d, n):
            return False
    return True


def sieve_of_eratosthenes(limit: int) -> List[int]:
    """
    Find all prime numbers up to a given limit using the Sieve of Eratosthenes.
    
    Args:
        limit: Upper bound for finding primes
        
    Returns:
        A list of all prime numbers up to the limit
        
    Examples:
        >>> sieve_of_eratosthenes(30)
        [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    """
    if limit < 2:
        return []
    
    # Initialize the sieve
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    
    # Mark non-primes using Sieve of Eratosthenes
    for i in range(2, int(math.sqrt(limit)) + 1):
        if sieve[i]:
            # Mark all multiples of i as non-prime
            for j in range(i*i, limit + 1, i):
                sieve[j] = False
    
    # Collect all primes into a list
    return [i for i in range(2, limit + 1) if sieve[i]]


def gcd(a: int, b: int) -> int:
    """
    Calculate the greatest common divisor of two integers using Euclidean algorithm.
    
    Args:
        a: First integer
        b: Second integer
        
    Returns:
        The greatest common divisor of a and b
        
    Examples:
        >>> gcd(48, 18)
        6
        >>> gcd(101, 103)
        1
    """
    while b:
        a, b = b, a % b
    return a


def lcm(a: int, b: int) -> int:
    """
    Calculate the least common multiple of two integers.

    Args:
        a: First integer
        b: Second integer

    Returns:
        The least common multiple of a and b

    Examples:
        >>> lcm(4, 6)
        12
        >>> lcm(21, 6)
        42
    """
    return abs(a * b) // gcd(a, b) if a and b else 0


def extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    """
    Extended Euclidean Algorithm to find gcd(a, b) and coefficients x, y such that ax + by = gcd(a, b).

    Args:
        a: First integer
        b: Second integer

    Returns:
        A tuple (gcd, x, y) where gcd is the greatest common divisor and x, y are coefficients

    Examples:
        >>> extended_gcd(35, 15)
        (5, 1, -2)
        >>> g, x, y = extended_gcd(35, 15)
        >>> 35*x + 15*y == g
        True
    """
    if a == 0:
        return (b, 0, 1)

    gcd, x1, y1 = extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1

    return (gcd, x, y)


def modular_inverse(a: int, m: int) -> Optional[int]:
    """
    Calculate the modular multiplicative inverse of a modulo m.

    Args:
        a: Integer to find the inverse for
        m: Modulus

    Returns:
        The modular inverse if it exists, None otherwise

    Examples:
        >>> modular_inverse(3, 11)
        4
        >>> 3 * 4 % 11
        1
    """
    if gcd(a, m) != 1:
        return None  # Modular inverse doesn't exist

    gcd_val, x, y = extended_gcd(a, m)
    return (x % m + m) % m  # Ensure the result is positive


def chinese_remainder_theorem(remainders: List[int], moduli: List[int]) -> Optional[int]:
    """
    Solve a system of linear congruences using the Chinese Remainder Theorem.

    Args:
        remainders: List of remainders
        moduli: List of moduli

    Returns:
        The solution to the system of congruences, or None if no solution exists

    Examples:
        >>> chinese_remainder_theorem([2, 3, 2], [3, 5, 7])
        23
    """
    if len(remainders) != len(moduli):
        raise ValueError("Number of remainders must equal number of moduli")

    # Check if moduli are pairwise coprime
    for i in range(len(moduli)):
        for j in range(i + 1, len(moduli)):
            if gcd(moduli[i], moduli[j]) != 1:
                return None  # Moduli are not pairwise coprime

    # Calculate product of all moduli
    N = 1
    for m in moduli:
        N *= m

    result = 0
    for i in range(len(moduli)):
        a_i = remainders[i]
        m_i = moduli[i]
        N_i = N // m_i

        # Calculate modular inverse of N_i modulo m_i
        inv = modular_inverse(N_i, m_i)
        if inv is None:
            return None

        result += a_i * N_i * inv

    return result % N


def fast_power(base: int, exponent: int, modulus: Optional[int] = None) -> int:
    """
    Calculate base^exponent (mod modulus) using the fast exponentiation algorithm.

    Args:
        base: Base value
        exponent: Exponent value
        modulus: Optional modulus for modular exponentiation

    Returns:
        base^exponent (mod modulus) if modulus is provided, otherwise base^exponent

    Examples:
        >>> fast_power(2, 10)
        1024
        >>> fast_power(2, 10, 1000)
        24
    """
    if exponent < 0:
        raise ValueError("Exponent must be non-negative")

    result = 1
    base = base if modulus is None else base % modulus

    while exponent > 0:
        # If exponent is odd, multiply result by base
        if exponent & 1:
            result = result * base if modulus is None else (result * base) % modulus

        # Square the base
        base = base * base if modulus is None else (base * base) % modulus

        # Divide exponent by 2
        exponent >>= 1

    return result


def binomial_coefficient(n: int, k: int) -> int:
    """
    Calculate the binomial coefficient C(n, k) using dynamic programming.

    Args:
        n: Total number of items
        k: Number of items to choose

    Returns:
        The binomial coefficient C(n, k)

    Examples:
        >>> binomial_coefficient(5, 2)
        10
        >>> binomial_coefficient(10, 5)
        252
    """
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1

    # Optimize by using symmetry: C(n, k) = C(n, n-k)
    k = min(k, n - k)

    # Initialize the first row of Pascal's triangle
    C = [0] * (k + 1)
    C[0] = 1

    # Build Pascal's triangle
    for i in range(1, n + 1):
        j = min(i, k)
        while j > 0:
            C[j] = C[j] + C[j - 1]
            j -= 1

    return C[k]


def catalan_number(n: int) -> int:
    """
    Calculate the nth Catalan number using the binomial coefficient formula.

    Args:
        n: A non-negative integer

    Returns:
        The nth Catalan number

    Examples:
        >>> [catalan_number(i) for i in range(10)]
        [1, 1, 2, 5, 14, 42, 132, 429, 1430, 4862]
    """
    if n < 0:
        raise ValueError("Input must be a non-negative integer")

    return binomial_coefficient(2*n, n) // (n + 1)


def stirling_number_second_kind(n: int, k: int) -> int:
    """
    Calculate the Stirling number of the second kind S(n, k).

    These numbers count the number of ways to partition a set of n objects into k non-empty subsets.

    Args:
        n: Number of objects
        k: Number of non-empty subsets

    Returns:
        The Stirling number of the second kind S(n, k)

    Examples:
        >>> stirling_number_second_kind(5, 2)
        15
        >>> stirling_number_second_kind(6, 3)
        90
    """
    if k <= 0 or k > n:
        return 0 if k != 0 or n != 0 else 1

    result = 0
    for i in range(k + 1):
        result += (-1)**(k - i) * binomial_coefficient(k, i) * (i**n)

    return result // math.factorial(k)


def bell_number(n: int) -> int:
    """
    Calculate the nth Bell number, which counts the number of partitions of a set with n elements.

    Args:
        n: A non-negative integer

    Returns:
        The nth Bell number

    Examples:
        >>> [bell_number(i) for i in range(10)]
        [1, 1, 2, 5, 15, 52, 203, 877, 4140, 21147]
    """
    if n < 0:
        raise ValueError("Input must be a non-negative integer")

    if n == 0:
        return 1

    # Calculate using Stirling numbers of the second kind
    return sum(stirling_number_second_kind(n, k) for k in range(1, n + 1))


def euler_totient(n: int) -> int:
    """
    Calculate Euler's totient function φ(n), which counts the positive integers up to n that are coprime to n.

    Args:
        n: A positive integer

    Returns:
        The value of φ(n)

    Examples:
        >>> euler_totient(10)
        4
        >>> euler_totient(36)
        12
    """
    if n <= 0:
        raise ValueError("Input must be a positive integer")

    result = n  # Initialize result as n

    # Consider all prime factors of n and subtract their multiples
    p = 2
    while p * p <= n:
        # Check if p is a prime factor
        if n % p == 0:
            # If yes, then update n and result
            while n % p == 0:
                n //= p
            result -= result // p
        p += 1

    # If n has a prime factor greater than sqrt(n)
    if n > 1:
        result -= result // n

    return result


def mobius_function(n: int) -> int:
    """
    Calculate the Möbius function μ(n).

    μ(n) = 1 if n is a square-free positive integer with an even number of prime factors.
    μ(n) = −1 if n is a square-free positive integer with an odd number of prime factors.
    μ(n) = 0 if n has a squared prime factor.

    Args:
        n: A positive integer

    Returns:
        The value of μ(n)

    Examples:
        >>> mobius_function(1)
        1
        >>> mobius_function(6)
        1
        >>> mobius_function(10)
        1
        >>> mobius_function(30)
        -1
    """
    if n <= 0:
        raise ValueError("Input must be a positive integer")

    if n == 1:
        return 1

    # Count the number of prime factors
    p_count = 0

    # Check if n has any squared prime factor
    p = 2
    while p * p <= n:
        if n % p == 0:
            n //= p
            p_count += 1

            # If p divides n more than once, μ(n) = 0
            if n % p == 0:
                return 0
        else:
            p += 1

    # If n > 1, it's a prime factor
    if n > 1:
        p_count += 1

    # Return 1 if p_count is even, -1 if odd
    return 1 if p_count % 2 == 0 else -1


# -----------------------------------------------------------------------------
# SECTION 2: NUMERICAL METHODS AND LINEAR ALGEBRA
# -----------------------------------------------------------------------------

def newton_raphson(f: Callable[[float], float],
                  df: Callable[[float], float],
                  x0: float,
                  tol: float = 1e-10,
                  max_iter: int = 100) -> float:
    """
    Find the root of a function using the Newton-Raphson method.

    Args:
        f: The function for which to find the root
        df: The derivative of the function
        x0: Initial guess
        tol: Tolerance for convergence
        max_iter: Maximum number of iterations

    Returns:
        The approximate root of the function

    Examples:
        >>> def f(x): return x**2 - 2
        >>> def df(x): return 2*x
        >>> abs(newton_raphson(f, df, 1.5) - math.sqrt(2)) < 1e-10
        True
    """
    x = x0
    for i in range(max_iter):
        fx = f(x)
        if abs(fx) < tol:
            return x

        dfx = df(x)
        if dfx == 0:
            raise ValueError("Derivative is zero, cannot continue")

        x = x - fx / dfx

    raise ValueError(f"Failed to converge after {max_iter} iterations")


def secant_method(f: Callable[[float], float],
                 x0: float,
                 x1: float,
                 tol: float = 1e-10,
                 max_iter: int = 100) -> float:
    """
    Find the root of a function using the secant method.

    Args:
        f: The function for which to find the root
        x0: First initial guess
        x1: Second initial guess
        tol: Tolerance for convergence
        max_iter: Maximum number of iterations

    Returns:
        The approximate root of the function

    Examples:
        >>> def f(x): return x**2 - 2
        >>> abs(secant_method(f, 1.0, 2.0) - math.sqrt(2)) < 1e-10
        True
    """
    f_x0 = f(x0)
    f_x1 = f(x1)

    for i in range(max_iter):
        if abs(f_x1) < tol:
            return x1

        if f_x1 == f_x0:
            raise ValueError("Division by zero in secant method")

        x_new = x1 - f_x1 * (x1 - x0) / (f_x1 - f_x0)
        x0, x1 = x1, x_new
        f_x0, f_x1 = f_x1, f(x1)

    raise ValueError(f"Failed to converge after {max_iter} iterations")


def bisection_method(f: Callable[[float], float],
                    a: float,
                    b: float,
                    tol: float = 1e-10,
                    max_iter: int = 100) -> float:
    """
    Find the root of a function using the bisection method.

    Args:
        f: The function for which to find the root
        a: Lower bound of the interval
        b: Upper bound of the interval
        tol: Tolerance for convergence
        max_iter: Maximum number of iterations

    Returns:
        The approximate root of the function

    Examples:
        >>> def f(x): return x**2 - 2
        >>> abs(bisection_method(f, 0, 2) - math.sqrt(2)) < 1e-10
        True
    """
    f_a = f(a)
    f_b = f(b)

    if f_a * f_b > 0:
        raise ValueError("Function must have opposite signs at interval endpoints")

    for i in range(max_iter):
        c = (a + b) / 2
        f_c = f(c)

        if abs(f_c) < tol or (b - a) / 2 < tol:
            return c

        if f_c * f_a < 0:
            b, f_b = c, f_c
        else:
            a, f_a = c, f_c

    raise ValueError(f"Failed to converge after {max_iter} iterations")


def trapezoidal_rule(f: Callable[[float], float],
                    a: float,
                    b: float,
                    n: int = 1000) -> float:
    """
    Approximate the definite integral of a function using the trapezoidal rule.

    Args:
        f: The function to integrate
        a: Lower bound of integration
        b: Upper bound of integration
        n: Number of intervals

    Returns:
        The approximate value of the definite integral

    Examples:
        >>> def f(x): return x**2
        >>> abs(trapezoidal_rule(f, 0, 1, 1000) - 1/3) < 1e-4
        True
    """
    if n <= 0:
        raise ValueError("Number of intervals must be positive")

    h = (b - a) / n
    result = (f(a) + f(b)) / 2

    for i in range(1, n):
        result += f(a + i * h)

    return result * h


def simpson_rule(f: Callable[[float], float],
                a: float,
                b: float,
                n: int = 1000) -> float:
    """
    Approximate the definite integral of a function using Simpson's rule.

    Args:
        f: The function to integrate
        a: Lower bound of integration
        b: Upper bound of integration
        n: Number of intervals (must be even)

    Returns:
        The approximate value of the definite integral

    Examples:
        >>> def f(x): return x**2
        >>> abs(simpson_rule(f, 0, 1, 1000) - 1/3) < 1e-6
        True
    """
    if n <= 0 or n % 2 != 0:
        raise ValueError("Number of intervals must be positive and even")

    h = (b - a) / n
    result = f(a) + f(b)

    # Sum for odd indices
    for i in range(1, n, 2):
        result += 4 * f(a + i * h)

    # Sum for even indices
    for i in range(2, n, 2):
        result += 2 * f(a + i * h)

    return result * h / 3


def romberg_integration(f: Callable[[float], float],
                       a: float,
                       b: float,
                       max_iter: int = 10,
                       tol: float = 1e-10) -> float:
    """
    Approximate the definite integral of a function using Romberg integration.

    Args:
        f: The function to integrate
        a: Lower bound of integration
        b: Upper bound of integration
        max_iter: Maximum number of iterations
        tol: Tolerance for convergence

    Returns:
        The approximate value of the definite integral

    Examples:
        >>> def f(x): return x**2
        >>> abs(romberg_integration(f, 0, 1, 6) - 1/3) < 1e-10
        True
    """
    R = [[0] * (max_iter + 1) for _ in range(max_iter + 1)]

    # Initial trapezoidal approximation with n=1
    h = b - a
    R[1][1] = h * (f(a) + f(b)) / 2

    for i in range(2, max_iter + 1):
        # Compute R[i][1] using trapezoidal rule with 2^(i-1) intervals
        h = h / 2
        sum_f = 0
        for k in range(1, 2**(i-2) + 1):
            sum_f += f(a + (2*k - 1) * h)

        R[i][1] = R[i-1][1] / 2 + h * sum_f

        # Compute R[i][j] using Richardson extrapolation
        for j in range(2, i + 1):
            R[i][j] = R[i][j-1] + (R[i][j-1] - R[i-1][j-1]) / (4**(j-1) - 1)

        # Check for convergence
        if i > 1 and abs(R[i][i] - R[i-1][i-1]) < tol:
            return R[i][i]

    return R[max_iter][max_iter]


def gauss_legendre_quadrature(f: Callable[[float], float],
                             a: float,
                             b: float,
                             n: int = 5) -> float:
    """
    Approximate the definite integral of a function using Gauss-Legendre quadrature.

    Args:
        f: The function to integrate
        a: Lower bound of integration
        b: Upper bound of integration
        n: Number of quadrature points

    Returns:
        The approximate value of the definite integral

    Examples:
        >>> def f(x): return x**2
        >>> abs(gauss_legendre_quadrature(f, 0, 1, 5) - 1/3) < 1e-10
        True
    """
    # Predefined weights and points for n=5
    if n == 5:
        weights = [0.2369268850561891, 0.4786286704993665, 0.5688888888888889,
                  0.4786286704993665, 0.2369268850561891]
        points = [-0.9061798459386640, -0.5384693101056831, 0.0000000000000000,
                 0.5384693101056831, 0.9061798459386640]
    else:
        # For simplicity, only n=5 is implemented
        # In a real implementation, we would compute weights and points for any n
        raise ValueError("Only n=5 is implemented for Gauss-Legendre quadrature")

    # Transform from [-1, 1] to [a, b]
    result = 0
    for i in range(n):
        x = ((b - a) * points[i] + (b + a)) / 2
        result += weights[i] * f(x)

    return result * (b - a) / 2


def monte_carlo_integration(f: Callable[[float], float],
                           a: float,
                           b: float,
                           n: int = 100000) -> Tuple[float, float]:
    """
    Approximate the definite integral of a function using Monte Carlo integration.

    Args:
        f: The function to integrate
        a: Lower bound of integration
        b: Upper bound of integration
        n: Number of random points

    Returns:
        A tuple containing the approximate value of the integral and its standard error

    Examples:
        >>> def f(x): return x**2
        >>> result, error = monte_carlo_integration(f, 0, 1, 100000)
        >>> abs(result - 1/3) < 0.01
        True
    """
    # Generate random points in [a, b]
    points = [random.uniform(a, b) for _ in range(n)]

    # Evaluate function at each point
    values = [f(x) for x in points]

    # Calculate mean and standard deviation
    mean = sum(values) / n
    variance = sum((v - mean)**2 for v in values) / (n - 1) if n > 1 else 0
    std_dev = math.sqrt(variance)

    # Calculate integral and error
    integral = (b - a) * mean
    error = (b - a) * std_dev / math.sqrt(n)

    return integral, error


def gaussian_elimination(A: List[List[float]], b: List[float]) -> List[float]:
    """
    Solve a system of linear equations Ax = b using Gaussian elimination.

    Args:
        A: Coefficient matrix
        b: Right-hand side vector

    Returns:
        Solution vector x

    Examples:
        >>> A = [[2, 1, -1], [-3, -1, 2], [-2, 1, 2]]
        >>> b = [8, -11, -3]
        >>> gaussian_elimination(A, b)
        [2.0, 3.0, -1.0]
    """
    n = len(A)
    if n == 0 or len(A[0]) != n or len(b) != n:
        raise ValueError("Invalid input dimensions")

    # Create augmented matrix [A|b]
    augmented = [row[:] + [b[i]] for i, row in enumerate(A)]

    # Forward elimination
    for i in range(n):
        # Find pivot
        max_row = i
        for j in range(i + 1, n):
            if abs(augmented[j][i]) > abs(augmented[max_row][i]):
                max_row = j

        # Swap rows
        if max_row != i:
            augmented[i], augmented[max_row] = augmented[max_row], augmented[i]

        # Check for singular matrix
        if abs(augmented[i][i]) < 1e-10:
            raise ValueError("Matrix is singular or nearly singular")

        # Eliminate below
        for j in range(i + 1, n):
            factor = augmented[j][i] / augmented[i][i]
            for k in range(i, n + 1):
                augmented[j][k] -= factor * augmented[i][k]

    # Back substitution
    x = [0] * n
    for i in range(n - 1, -1, -1):
        x[i] = augmented[i][n]
        for j in range(i + 1, n):
            x[i] -= augmented[i][j] * x[j]
        x[i] /= augmented[i][i]

    return x


def lu_decomposition(A: List[List[float]]) -> Tuple[List[List[float]], List[List[float]]]:
    """
    Compute the LU decomposition of a square matrix.

    Args:
        A: Square matrix to decompose

    Returns:
        A tuple (L, U) where L is lower triangular and U is upper triangular

    Examples:
        >>> A = [[2, -1, 0], [-1, 2, -1], [0, -1, 2]]
        >>> L, U = lu_decomposition(A)
        >>> all(abs(sum(L[i][k] * U[k][j] - A[i][j] for k in range(len(A)))) < 1e-10 for i in range(len(A)) for j in range(len(A)))
        True
    """
    n = len(A)
    if n == 0 or any(len(row) != n for row in A):
        raise ValueError("Input must be a square matrix")

    # Create copies to avoid modifying the input
    L = [[0.0] * n for _ in range(n)]
    U = [[0.0] * n for _ in range(n)]

    # Initialize L's diagonal to 1
    for i in range(n):
        L[i][i] = 1.0

    # Perform LU decomposition
    for i in range(n):
        # Upper triangular matrix
        for j in range(i, n):
            U[i][j] = A[i][j] - sum(L[i][k] * U[k][j] for k in range(i))

        # Lower triangular matrix
        for j in range(i + 1, n):
            if abs(U[i][i]) < 1e-10:
                raise ValueError("Matrix is singular or nearly singular")
            L[j][i] = (A[j][i] - sum(L[j][k] * U[k][i] for k in range(i))) / U[i][i]

    return L, U


def solve_lu(L: List[List[float]], U: List[List[float]], b: List[float]) -> List[float]:
    """
    Solve a system of linear equations Ax = b using LU decomposition.

    Args:
        L: Lower triangular matrix from LU decomposition
        U: Upper triangular matrix from LU decomposition
        b: Right-hand side vector

    Returns:
        Solution vector x

    Examples:
        >>> A = [[2, -1, 0], [-1, 2, -1], [0, -1, 2]]
        >>> b = [1, 0, 0]
        >>> L, U = lu_decomposition(A)
        >>> x = solve_lu(L, U, b)
        >>> all(abs(sum(A[i][j] * x[j] for j in range(len(x))) - b[i]) < 1e-10 for i in range(len(b)))
        True
    """
    n = len(L)
    if n == 0 or len(U) != n or len(b) != n:
        raise ValueError("Invalid input dimensions")

    # Forward substitution to solve Ly = b
    y = [0] * n
    for i in range(n):
        y[i] = b[i] - sum(L[i][j] * y[j] for j in range(i))

    # Back substitution to solve Ux = y
    x = [0] * n
    for i in range(n - 1, -1, -1):
        if abs(U[i][i]) < 1e-10:
            raise ValueError("Matrix is singular or nearly singular")
        x[i] = (y[i] - sum(U[i][j] * x[j] for j in range(i + 1, n))) / U[i][i]

    return x


def matrix_inverse(A: List[List[float]]) -> List[List[float]]:
    """
    Compute the inverse of a square matrix using LU decomposition.

    Args:
        A: Square matrix to invert

    Returns:
        The inverse of matrix A

    Examples:
        >>> A = [[4, 7], [2, 6]]
        >>> A_inv = matrix_inverse(A)
        >>> all(abs(sum(A[i][k] * A_inv[k][j] - (1 if i == j else 0) for k in range(len(A)))) < 1e-10 for i in range(len(A)) for j in range(len(A)))
        True
    """
    n = len(A)
    if n == 0 or any(len(row) != n for row in A):
        raise ValueError("Input must be a square matrix")

    # Compute LU decomposition
    try:
        L, U = lu_decomposition(A)
    except ValueError:
        raise ValueError("Matrix is singular and cannot be inverted")

    # Compute inverse by solving n systems of equations
    A_inv = [[0.0] * n for _ in range(n)]
    for j in range(n):
        # Create unit vector e_j
        e = [1.0 if i == j else 0.0 for i in range(n)]

        # Solve Ax = e_j
        x = solve_lu(L, U, e)

        # Store the solution as the jth column of A_inv
        for i in range(n):
            A_inv[i][j] = x[i]

    return A_inv


def determinant(A: List[List[float]]) -> float:
    """
    Compute the determinant of a square matrix using LU decomposition.

    Args:
        A: Square matrix

    Returns:
        The determinant of matrix A

    Examples:
        >>> A = [[1, 2, 3], [4, 5, 6], [7, 8, 10]]
        >>> abs(determinant(A) - 3) < 1e-10
        True
    """
    n = len(A)
    if n == 0 or any(len(row) != n for row in A):
        raise ValueError("Input must be a square matrix")

    try:
        L, U = lu_decomposition(A)
    except ValueError:
        return 0.0  # Singular matrix has determinant 0

    # Determinant is the product of diagonal elements of U
    det = 1.0
    for i in range(n):
        det *= U[i][i]

    return det


def qr_decomposition(A: List[List[float]]) -> Tuple[List[List[float]], List[List[float]]]:
    """
    Compute the QR decomposition of a matrix using the Gram-Schmidt process.

    Args:
        A: Matrix to decompose

    Returns:
        A tuple (Q, R) where Q is orthogonal and R is upper triangular

    Examples:
        >>> A = [[12, -51, 4], [6, 167, -68], [-4, 24, -41]]
        >>> Q, R = qr_decomposition(A)
        >>> all(abs(sum(Q[i][k] * R[k][j] - A[i][j] for k in range(min(len(A), len(A[0]))))) < 1e-10 for i in range(len(A)) for j in range(len(A[0])))
        True
    """
    m = len(A)
    if m == 0:
        raise ValueError("Input matrix cannot be empty")

    n = len(A[0])
    if any(len(row) != n for row in A):
        raise ValueError("Input matrix must have consistent row lengths")

    # Create copies to avoid modifying the input
    Q = [[0.0] * n for _ in range(m)]
    R = [[0.0] * n for _ in range(n)]

    # Gram-Schmidt process
    for j in range(n):
        # Copy the jth column of A to v
        v = [A[i][j] for i in range(m)]

        for i in range(j):
            # Compute dot product of A[:, j] and Q[:, i]
            R[i][j] = sum(A[k][j] * Q[k][i] for k in range(m))

            # Subtract the projection
            for k in range(m):
                v[k] -= R[i][j] * Q[k][i]

        # Compute the norm of v
        norm_v = math.sqrt(sum(v[i]**2 for i in range(m)))

        # Check for linear dependence
        if norm_v < 1e-10:
            for i in range(m):
                Q[i][j] = 0.0
        else:
            # Normalize v and store in Q[:, j]
            for i in range(m):
                Q[i][j] = v[i] / norm_v

            R[j][j] = norm_v

    return Q, R


def eigenvalues_power_method(A: List[List[float]],
                           max_iter: int = 100,
                           tol: float = 1e-10) -> Tuple[float, List[float]]:
    """
    Compute the dominant eigenvalue and eigenvector of a matrix using the power method.

    Args:
        A: Square matrix
        max_iter: Maximum number of iterations
        tol: Tolerance for convergence

    Returns:
        A tuple (eigenvalue, eigenvector) containing the dominant eigenvalue and its corresponding eigenvector

    Examples:
        >>> A = [[2, 1], [1, 2]]
        >>> eigenvalue, eigenvector = eigenvalues_power_method(A)
        >>> abs(eigenvalue - 3) < 1e-6
        True
    """
    n = len(A)
    if n == 0 or any(len(row) != n for row in A):
        raise ValueError("Input must be a square matrix")

    # Initialize a random vector
    x = [random.random() for _ in range(n)]

    # Normalize the vector
    norm_x = math.sqrt(sum(x[i]**2 for i in range(n)))
    x = [x[i] / norm_x for i in range(n)]

    lambda_old = 0

    for _ in range(max_iter):
        # Compute Ax
        y = [sum(A[i][j] * x[j] for j in range(n)) for i in range(n)]

        # Compute the Rayleigh quotient
        lambda_new = sum(x[i] * y[i] for i in range(n))

        # Normalize y to get the new x
        norm_y = math.sqrt(sum(y[i]**2 for i in range(n)))
        x = [y[i] / norm_y for i in range(n)]

        # Check for convergence
        if abs(lambda_new - lambda_old) < tol:
            return lambda_new, x

        lambda_old = lambda_new

    return lambda_old, x


def eigenvalues_qr_algorithm(A: List[List[float]],
                           max_iter: int = 100,
                           tol: float = 1e-10) -> List[float]:
    """
    Compute all eigenvalues of a matrix using the QR algorithm.

    Args:
        A: Square matrix
        max_iter: Maximum number of iterations
        tol: Tolerance for convergence

    Returns:
        A list of eigenvalues

    Examples:
        >>> A = [[2, 1], [1, 2]]
        >>> eigenvalues = eigenvalues_qr_algorithm(A)
        >>> sorted([round(ev, 6) for ev in eigenvalues])
        [1.0, 3.0]
    """
    n = len(A)
    if n == 0 or any(len(row) != n for row in A):
        raise ValueError("Input must be a square matrix")

    # Create a copy of A to avoid modifying the input
    A_k = [row[:] for row in A]

    for _ in range(max_iter):
        # Compute QR decomposition
        Q, R = qr_decomposition(A_k)

        # Compute A_{k+1} = RQ
        A_next = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                A_next[i][j] = sum(R[i][k] * Q[k][j] for k in range(n))

        # Check for convergence
        converged = True
        for i in range(1, n):
            for j in range(i):
                if abs(A_next[i][j]) > tol:
                    converged = False
                    break
            if not converged:
                break

        if converged:
            # Extract eigenvalues from the diagonal
            return [A_next[i][i] for i in range(n)]

        A_k = A_next

    # If not converged, return the diagonal elements as approximations
    return [A_k[i][i] for i in range(n)]


def jacobi_eigenvalue_method(A: List[List[float]],
                           max_iter: int = 100,
                           tol: float = 1e-10) -> Tuple[List[float], List[List[float]]]:
    """
    Compute all eigenvalues and eigenvectors of a symmetric matrix using the Jacobi eigenvalue method.

    Args:
        A: Symmetric square matrix
        max_iter: Maximum number of iterations
        tol: Tolerance for convergence

    Returns:
        A tuple (eigenvalues, eigenvectors) containing the eigenvalues and corresponding eigenvectors

    Examples:
        >>> A = [[2, 1], [1, 2]]
        >>> eigenvalues, eigenvectors = jacobi_eigenvalue_method(A)
        >>> sorted([round(ev, 6) for ev in eigenvalues])
        [1.0, 3.0]
    """
    n = len(A)
    if n == 0 or any(len(row) != n for row in A):
        raise ValueError("Input must be a square matrix")

    # Check if A is symmetric
    for i in range(n):
        for j in range(i + 1, n):
            if abs(A[i][j] - A[j][i]) > tol:
                raise ValueError("Input matrix must be symmetric")

    # Create a copy of A to avoid modifying the input
    A_k = [row[:] for row in A]

    # Initialize eigenvectors as the identity matrix
    V = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

    for _ in range(max_iter):
        # Find the largest off-diagonal element
        p, q = 0, 1
        max_val = abs(A_k[p][q])

        for i in range(n):
            for j in range(i + 1, n):
                if abs(A_k[i][j]) > max_val:
                    max_val = abs(A_k[i][j])
                    p, q = i, j

        # Check for convergence
        if max_val < tol:
            # Extract eigenvalues from the diagonal
            eigenvalues = [A_k[i][i] for i in range(n)]
            return eigenvalues, V

        # Compute the Jacobi rotation
        if abs(A_k[p][p] - A_k[q][q]) < tol:
            theta = math.pi / 4
        else:
            theta = 0.5 * math.atan2(2 * A_k[p][q], A_k[q][q] - A_k[p][p])

        c = math.cos(theta)
        s = math.sin(theta)

        # Apply the Jacobi rotation
        A_new = [row[:] for row in A_k]

        # Update the pth and qth rows and columns
        for i in range(n):
            if i != p and i != q:
                A_new[i][p] = c * A_k[i][p] + s * A_k[i][q]
                A_new[p][i] = A_new[i][p]

                A_new[i][q] = -s * A_k[i][p] + c * A_k[i][q]
                A_new[q][i] = A_new[i][q]

        A_new[p][p] = c**2 * A_k[p][p] + 2 * c * s * A_k[p][q] + s**2 * A_k[q][q]
        A_new[q][q] = s**2 * A_k[p][p] - 2 * c * s * A_k[p][q] + c**2 * A_k[q][q]
        A_new[p][q] = 0
        A_new[q][p] = 0

        # Update eigenvectors
        for i in range(n):
            v_ip = V[i][p]
            v_iq = V[i][q]
            V[i][p] = c * v_ip + s * v_iq
            V[i][q] = -s * v_ip + c * v_iq

        A_k = A_new

    # If not converged, return the current approximations
    eigenvalues = [A_k[i][i] for i in range(n)]
    return eigenvalues, V


# -----------------------------------------------------------------------------
# SECTION 3: DATA STRUCTURES AND ALGORITHMS
# -----------------------------------------------------------------------------

class Node:
    """A node in a linked list, tree, or graph."""

    def __init__(self, value: Any, next_node: Optional['Node'] = None):
        self.value = value
        self.next = next_node

    def __repr__(self) -> str:
        return f"Node({self.value})"


class LinkedList:
    """A singly linked list implementation."""

    def __init__(self, values: Optional[Iterable[Any]] = None):
        """
        Initialize a linked list, optionally with initial values.

        Args:
            values: Optional iterable of values to initialize the list with
        """
        self.head = None
        self.tail = None
        self.size = 0

        if values:
            for value in values:
                self.append(value)

    def append(self, value: Any) -> None:
        """
        Append a value to the end of the list.

        Args:
            value: Value to append
        """
        new_node = Node(value)

        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node

        self.size += 1

    def prepend(self, value: Any) -> None:
        """
        Prepend a value to the beginning of the list.

        Args:
            value: Value to prepend
        """
        new_node = Node(value, self.head)
        self.head = new_node

        if self.tail is None:
            self.tail = new_node

        self.size += 1

    def insert(self, index: int, value: Any) -> None:
        """
        Insert a value at a specific index.

        Args:
            index: Index at which to insert the value
            value: Value to insert

        Raises:
            IndexError: If the index is out of bounds
        """
        if index < 0 or index > self.size:
            raise IndexError("Index out of bounds")

        if index == 0:
            self.prepend(value)
            return

        if index == self.size:
            self.append(value)
            return

        current = self.head
        for _ in range(index - 1):
            current = current.next

        new_node = Node(value, current.next)
        current.next = new_node
        self.size += 1

    def remove(self, value: Any) -> bool:
        """
        Remove the first occurrence of a value from the list.

        Args:
            value: Value to remove

        Returns:
            True if the value was found and removed, False otherwise
        """
        if self.head is None:
            return False

        if self.head.value == value:
            self.head = self.head.next
            self.size -= 1

            if self.head is None:
                self.tail = None

            return True

        current = self.head
        while current.next and current.next.value != value:
            current = current.next

        if current.next:
            if current.next == self.tail:
                self.tail = current

            current.next = current.next.next
            self.size -= 1
            return True

        return False

    def pop(self, index: int = -1) -> Any:
        """
        Remove and return the value at the specified index.

        Args:
            index: Index of the value to remove (default: -1, which removes the last element)

        Returns:
            The removed value

        Raises:
            IndexError: If the list is empty or the index is out of bounds
        """
        if self.head is None:
            raise IndexError("Cannot pop from an empty list")

        if index < 0:
            index = self.size + index

        if index < 0 or index >= self.size:
            raise IndexError("Index out of bounds")

        if index == 0:
            value = self.head.value
            self.head = self.head.next
            self.size -= 1

            if self.head is None:
                self.tail = None

            return value

        current = self.head
        for _ in range(index - 1):
            current = current.next

        value = current.next.value

        if current.next == self.tail:
            self.tail = current

        current.next = current.next.next
        self.size -= 1

        return value

    def __len__(self) -> int:
        return self.size

    def __iter__(self) -> Generator[Any, None, None]:
        current = self.head
        while current:
            yield current.value
            current = current.next

    def __repr__(self) -> str:
        return f"LinkedList({list(self)})"


class DoublyLinkedNode:
    """A node in a doubly linked list."""

    def __init__(self, value: Any,
                prev_node: Optional['DoublyLinkedNode'] = None,
                next_node: Optional['DoublyLinkedNode'] = None):
        self.value = value
        self.prev = prev_node
        self.next = next_node

    def __repr__(self) -> str:
        return f"DoublyLinkedNode({self.value})"


class DoublyLinkedList:
    """A doubly linked list implementation."""

    def __init__(self, values: Optional[Iterable[Any]] = None):
        """
        Initialize a doubly linked list, optionally with initial values.

        Args:
            values: Optional iterable of values to initialize the list with
        """
        self.head = None
        self.tail = None
        self.size = 0

        if values:
            for value in values:
                self.append(value)

    def append(self, value: Any) -> None:
        """
        Append a value to the end of the list.

        Args:
            value: Value to append
        """
        new_node = DoublyLinkedNode(value, self.tail)

        if self.head is None:
            self.head = new_node
        else:
            self.tail.next = new_node

        self.tail = new_node
        self.size += 1

    def prepend(self, value: Any) -> None:
        """
        Prepend a value to the beginning of the list.

        Args:
            value: Value to prepend
        """
        new_node = DoublyLinkedNode(value, None, self.head)

        if self.head:
            self.head.prev = new_node

        self.head = new_node

        if self.tail is None:
            self.tail = new_node

        self.size += 1

    def insert(self, index: int, value: Any) -> None:
        """
        Insert a value at a specific index.

        Args:
            index: Index at which to insert the value
            value: Value to insert

        Raises:
            IndexError: If the index is out of bounds
        """
        if index < 0 or index > self.size:
            raise IndexError("Index out of bounds")

        if index == 0:
            self.prepend(value)
            return

        if index == self.size:
            self.append(value)
            return

        if index <= self.size // 2:
            # Start from the head
            current = self.head
            for _ in range(index - 1):
                current = current.next

            new_node = DoublyLinkedNode(value, current, current.next)
            current.next.prev = new_node
            current.next = new_node
        else:
            # Start from the tail
            current = self.tail
            for _ in range(self.size - index):
                current = current.prev

            new_node = DoublyLinkedNode(value, current.prev, current)
            current.prev.next = new_node
            current.prev = new_node

        self.size += 1

    def remove(self, value: Any) -> bool:
        """
        Remove the first occurrence of a value from the list.

        Args:
            value: Value to remove

        Returns:
            True if the value was found and removed, False otherwise
        """
        if self.head is None:
            return False

        if self.head.value == value:
            self.head = self.head.next

            if self.head:
                self.head.prev = None
            else:
                self.tail = None

            self.size -= 1
            return True

        current = self.head
        while current and current.value != value:
            current = current.next

        if current:
            if current == self.tail:
                self.tail = current.prev
                self.tail.next = None
            else:
                current.prev.next = current.next
                current.next.prev = current.prev

            self.size -= 1
            return True

        return False

    def pop(self, index: int = -1) -> Any:
        """
        Remove and return the value at the specified index.

        Args:
            index: Index of the value to remove (default: -1, which removes the last element)

        Returns:
            The removed value

        Raises:
            IndexError: If the list is empty or the index is out of bounds
        """
        if self.head is None:
            raise IndexError("Cannot pop from an empty list")

        if index < 0:
            index = self.size + index

        if index < 0 or index >= self.size:
            raise IndexError("Index out of bounds")

        if index == 0:
            value = self.head.value
            self.head = self.head.next

            if self.head:
                self.head.prev = None
            else:
                self.tail = None

            self.size -= 1
            return value

        if index == self.size - 1:
            value = self.tail.value
            self.tail = self.tail.prev
            self.tail.next = None
            self.size -= 1
            return value

        if index <= self.size // 2:
            # Start from the head
            current = self.head
            for _ in range(index):
                current = current.next
        else:
            # Start from the tail
            current = self.tail
            for _ in range(self.size - index - 1):
                current = current.prev

        value = current.value
        current.prev.next = current.next
        current.next.prev = current.prev
        self.size -= 1

        return value

    def __len__(self) -> int:
        return self.size

    def __iter__(self) -> Generator[Any, None, None]:
        current = self.head
        while current:
            yield current.value
            current = current.next

    def __repr__(self) -> str:
        return f"DoublyLinkedList({list(self)})"


class TreeNode:
    """A node in a binary tree."""

    def __init__(self, value: Any,
                left: Optional['TreeNode'] = None,
                right: Optional['TreeNode'] = None):
        self.value = value
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f"TreeNode({self.value})"


class BinarySearchTree:
    """A binary search tree implementation."""

    def __init__(self):
        """Initialize an empty binary search tree."""
        self.root = None
        self.size = 0

    def insert(self, value: Any) -> None:
        """
        Insert a value into the binary search tree.

        Args:
            value: Value to insert
        """
        self.root = self._insert_recursive(self.root, value)
        self.size += 1

    def _insert_recursive(self, node: Optional[TreeNode], value: Any) -> TreeNode:
        """
        Recursively insert a value into the binary search tree.

        Args:
            node: Current node being considered
            value: Value to insert

        Returns:
            The updated node
        """
        if node is None:
            return TreeNode(value)

        if value < node.value:
            node.left = self._insert_recursive(node.left, value)
        elif value > node.value:
            node.right = self._insert_recursive(node.right, value)

        return node

    def search(self, value: Any) -> bool:
        """
        Search for a value in the binary search tree.

        Args:
            value: Value to search for

        Returns:
            True if the value is found, False otherwise
        """
        return self._search_recursive(self.root, value)

    def _search_recursive(self, node: Optional[TreeNode], value: Any) -> bool:
        """
        Recursively search for a value in the binary search tree.

        Args:
            node: Current node being considered
            value: Value to search for

        Returns:
            True if the value is found, False otherwise
        """
        if node is None:
            return False

        if value == node.value:
            return True

        if value < node.value:
            return self._search_recursive(node.left, value)

        return self._search_recursive(node.right, value)

    def delete(self, value: Any) -> bool:
        """
        Delete a value from the binary search tree.

        Args:
            value: Value to delete

        Returns:
            True if the value was found and deleted, False otherwise
        """
        if not self.search(value):
            return False

        self.root = self._delete_recursive(self.root, value)
        self.size -= 1
        return True

    def _delete_recursive(self, node: Optional[TreeNode], value: Any) -> Optional[TreeNode]:
        """
        Recursively delete a value from the binary search tree.

        Args:
            node: Current node being considered
            value: Value to delete

        Returns:
            The updated node
        """
        if node is None:
            return None

        if value < node.value:
            node.left = self._delete_recursive(node.left, value)
        elif value > node.value:
            node.right = self._delete_recursive(node.right, value)
        else:
            # Node with only one child or no child
            if node.left is None:
                return node.right
            elif node.right is None:
                return node.left

            # Node with two children: Get the inorder successor (smallest in the right subtree)
            node.value = self._min_value(node.right)

            # Delete the inorder successor
            node.right = self._delete_recursive(node.right, node.value)

        return node

    def _min_value(self, node: TreeNode) -> Any:
        """
        Find the minimum value in a subtree.

        Args:
            node: Root of the subtree

        Returns:
            The minimum value in the subtree
        """
        current = node
        while current.left:
            current = current.left

        return current.value

    def inorder_traversal(self) -> List[Any]:
        """
        Perform an inorder traversal of the binary search tree.

        Returns:
            A list of values in inorder traversal order
        """
        result = []
        self._inorder_recursive(self.root, result)
        return result

    def _inorder_recursive(self, node: Optional[TreeNode], result: List[Any]) -> None:
        """
        Recursively perform an inorder traversal of the binary search tree.

        Args:
            node: Current node being considered
            result: List to store the traversal result
        """
        if node:
            self._inorder_recursive(node.left, result)
            result.append(node.value)
            self._inorder_recursive(node.right, result)

    def preorder_traversal(self) -> List[Any]:
        """
        Perform a preorder traversal of the binary search tree.

        Returns:
            A list of values in preorder traversal order
        """
        result = []
        self._preorder_recursive(self.root, result)
        return result

    def _preorder_recursive(self, node: Optional[TreeNode], result: List[Any]) -> None:
        """
        Recursively perform a preorder traversal of the binary search tree.

        Args:
            node: Current node being considered
            result: List to store the traversal result
        """
        if node:
            result.append(node.value)
            self._preorder_recursive(node.left, result)
            self._preorder_recursive(node.right, result)

    def postorder_traversal(self) -> List[Any]:
        """
        Perform a postorder traversal of the binary search tree.

        Returns:
            A list of values in postorder traversal order
        """
        result = []
        self._postorder_recursive(self.root, result)
        return result

    def _postorder_recursive(self, node: Optional[TreeNode], result: List[Any]) -> None:
        """
        Recursively perform a postorder traversal of the binary search tree.

        Args:
            node: Current node being considered
            result: List to store the traversal result
        """
        if node:
            self._postorder_recursive(node.left, result)
            self._postorder_recursive(node.right, result)
            result.append(node.value)

    def __len__(self) -> int:
        return self.size

    def __repr__(self) -> str:
        return f"BinarySearchTree({self.inorder_traversal()})"


class AVLNode(TreeNode):
    """A node in an AVL tree."""

    def __init__(self, value: Any,
                left: Optional['AVLNode'] = None,
                right: Optional['AVLNode'] = None):
        super().__init__(value, left, right)
        self.height = 1

    def __repr__(self) -> str:
        return f"AVLNode({self.value}, height={self.height})"


class AVLTree:
    """An AVL tree implementation (self-balancing binary search tree)."""

    def __init__(self):
        """Initialize an empty AVL tree."""
        self.root = None
        self.size = 0

    def _height(self, node: Optional[AVLNode]) -> int:
        """
        Get the height of a node.

        Args:
            node: Node to get the height of

        Returns:
            The height of the node, or 0 if the node is None
        """
        return node.height if node else 0

    def _balance_factor(self, node: AVLNode) -> int:
        """
        Calculate the balance factor of a node.

        Args:
            node: Node to calculate the balance factor of

        Returns:
            The balance factor of the node
        """
        return self._height(node.left) - self._height(node.right)

    def _update_height(self, node: AVLNode) -> None:
        """
        Update the height of a node.

        Args:
            node: Node to update the height of
        """
        node.height = 1 + max(self._height(node.left), self._height(node.right))

    def _right_rotate(self, y: AVLNode) -> AVLNode:
        """
        Perform a right rotation on a node.

        Args:
            y: Node to rotate

        Returns:
            The new root of the rotated subtree
        """
        x = y.left
        T2 = x.right

        # Perform rotation
        x.right = y
        y.left = T2

        # Update heights
        self._update_height(y)
        self._update_height(x)

        return x

    def _left_rotate(self, x: AVLNode) -> AVLNode:
        """
        Perform a left rotation on a node.

        Args:
            x: Node to rotate

        Returns:
            The new root of the rotated subtree
        """
        y = x.right
        T2 = y.left

        # Perform rotation
        y.left = x
        x.right = T2

        # Update heights
        self._update_height(x)
        self._update_height(y)

        return y

    def insert(self, value: Any) -> None:
        """
        Insert a value into the AVL tree.

        Args:
            value: Value to insert
        """
        self.root = self._insert_recursive(self.root, value)
        self.size += 1

    def _insert_recursive(self, node: Optional[AVLNode], value: Any) -> AVLNode:
        """
        Recursively insert a value into the AVL tree.

        Args:
            node: Current node being considered
            value: Value to insert

        Returns:
            The updated node
        """
        # Perform standard BST insert
        if node is None:
            return AVLNode(value)

        if value < node.value:
            node.left = self._insert_recursive(node.left, value)
        elif value > node.value:
            node.right = self._insert_recursive(node.right, value)
        else:
            # Duplicate values are not allowed
            return node

        # Update height of current node
        self._update_height(node)

        # Get the balance factor
        balance = self._balance_factor(node)

        # Left Left Case
        if balance > 1 and value < node.left.value:
            return self._right_rotate(node)

        # Right Right Case
        if balance < -1 and value > node.right.value:
            return self._left_rotate(node)

        # Left Right Case
        if balance > 1 and value > node.left.value:
            node.left = self._left_rotate(node.left)
            return self._right_rotate(node)

        # Right Left Case
        if balance < -1 and value < node.right.value:
            node.right = self._right_rotate(node.right)
            return self._left_rotate(node)

        return node

    def delete(self, value: Any) -> bool:
        """
        Delete a value from the AVL tree.

        Args:
            value: Value to delete

        Returns:
            True if the value was found and deleted, False otherwise
        """
        if not self.search(value):
            return False

        self.root = self._delete_recursive(self.root, value)
        self.size -= 1
        return True

    def _delete_recursive(self, node: Optional[AVLNode], value: Any) -> Optional[AVLNode]:
        """
        Recursively delete a value from the AVL tree.

        Args:
            node: Current node being considered
            value: Value to delete

        Returns:
            The updated node
        """
        if node is None:
            return None

        if value < node.value:
            node.left = self._delete_recursive(node.left, value)
        elif value > node.value:
            node.right = self._delete_recursive(node.right, value)
        else:
            # Node with only one child or no child
            if node.left is None:
                return node.right
            elif node.right is None:
                return node.left

            # Node with two children: Get the inorder successor (smallest in the right subtree)
            node.value = self._min_value(node.right)

            # Delete the inorder successor
            node.right = self._delete_recursive(node.right, node.value)

        # If the tree had only one node, return
        if node is None:
            return None

        # Update height of current node
        self._update_height(node)

        # Get the balance factor
        balance = self._balance_factor(node)

        # Left Left Case
        if balance > 1 and self._balance_factor(node.left) >= 0:
            return self._right_rotate(node)

        # Left Right Case
        if balance > 1 and self._balance_factor(node.left) < 0:
            node.left = self._left_rotate(node.left)
            return self._right_rotate(node)

        # Right Right Case
        if balance < -1 and self._balance_factor(node.right) <= 0:
            return self._left_rotate(node)

        # Right Left Case
        if balance < -1 and self._balance_factor(node.right) > 0:
            node.right = self._right_rotate(node.right)
            return self._left_rotate(node)

        return node

    def _min_value(self, node: AVLNode) -> Any:
        """
        Find the minimum value in a subtree.

        Args:
            node: Root of the subtree

        Returns:
            The minimum value in the subtree
        """
        current = node
        while current.left:
            current = current.left

        return current.value

    def search(self, value: Any) -> bool:
        """
        Search for a value in the AVL tree.

        Args:
            value: Value to search for

        Returns:
            True if the value is found, False otherwise
        """
        return self._search_recursive(self.root, value)

    def _search_recursive(self, node: Optional[AVLNode], value: Any) -> bool:
        """
        Recursively search for a value in the AVL tree.

        Args:
            node: Current node being considered
            value: Value to search for

        Returns:
            True if the value is found, False otherwise
        """
        if node is None:
            return False

        if value == node.value:
            return True

        if value < node.value:
            return self._search_recursive(node.left, value)

        return self._search_recursive(node.right, value)

    def inorder_traversal(self) -> List[Any]:
        """
        Perform an inorder traversal of the AVL tree.

        Returns:
            A list of values in inorder traversal order
        """
        result = []
        self._inorder_recursive(self.root, result)
        return result

    def _inorder_recursive(self, node: Optional[AVLNode], result: List[Any]) -> None:
        """
        Recursively perform an inorder traversal of the AVL tree.

        Args:
            node: Current node being considered
            result: List to store the traversal result
        """
        if node:
            self._inorder_recursive(node.left, result)
            result.append(node.value)
            self._inorder_recursive(node.right, result)

    def __len__(self) -> int:
        return self.size

    def __repr__(self) -> str:
        return f"AVLTree({self.inorder_traversal()})"


class Heap:
    """A binary heap implementation (min-heap by default)."""

    def __init__(self, values: Optional[Iterable[Any]] = None, max_heap: bool = False):
        """
        Initialize a binary heap, optionally with initial values.

        Args:
            values: Optional iterable of values to initialize the heap with
            max_heap: If True, create a max-heap; otherwise, create a min-heap
        """
        self.heap = []
        self.max_heap = max_heap

        if values:
            for value in values:
                self.push(value)

    def push(self, value: Any) -> None:
        """
        Push a value onto the heap.

        Args:
            value: Value to push
        """
        self.heap.append(value)
        self._sift_up(len(self.heap) - 1)

    def pop(self) -> Any:
        """
        Pop the smallest (or largest) value from the heap.

        Returns:
            The smallest (or largest) value in the heap

        Raises:
            IndexError: If the heap is empty
        """
        if not self.heap:
            raise IndexError("Cannot pop from an empty heap")

        if len(self.heap) == 1:
            return self.heap.pop()

        root = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._sift_down(0)

        return root

    def peek(self) -> Any:
        """
        Peek at the smallest (or largest) value in the heap without removing it.

        Returns:
            The smallest (or largest) value in the heap

        Raises:
            IndexError: If the heap is empty
        """
        if not self.heap:
            raise IndexError("Cannot peek at an empty heap")

        return self.heap[0]

    def _sift_up(self, index: int) -> None:
        """
        Sift up a value in the heap.

        Args:
            index: Index of the value to sift up
        """
        parent = (index - 1) // 2

        if index > 0:
            if self.max_heap:
                if self.heap[parent] < self.heap[index]:
                    self.heap[parent], self.heap[index] = self.heap[index], self.heap[parent]
                    self._sift_up(parent)
            else:
                if self.heap[parent] > self.heap[index]:
                    self.heap[parent], self.heap[index] = self.heap[index], self.heap[parent]
                    self._sift_up(parent)

    def _sift_down(self, index: int) -> None:
        """
        Sift down a value in the heap.

        Args:
            index: Index of the value to sift down
        """
        smallest = index
        left = 2 * index + 1
        right = 2 * index + 2

        if self.max_heap:
            if left < len(self.heap) and self.heap[left] > self.heap[smallest]:
                smallest = left

            if right < len(self.heap) and self.heap[right] > self.heap[smallest]:
                smallest = right
        else:
            if left < len(self.heap) and self.heap[left] < self.heap[smallest]:
                smallest = left

            if right < len(self.heap) and self.heap[right] < self.heap[smallest]:
                smallest = right

        if smallest != index:
            self.heap[index], self.heap[smallest] = self.heap[smallest], self.heap[index]
            self._sift_down(smallest)

    def heapify(self, values: Iterable[Any]) -> None:
        """
        Heapify an iterable of values.

        Args:
            values: Iterable of values to heapify
        """
        self.heap = list(values)

        for i in range(len(self.heap) // 2 - 1, -1, -1):
            self._sift_down(i)

    def __len__(self) -> int:
        return len(self.heap)

    def __bool__(self) -> bool:
        return bool(self.heap)

    def __repr__(self) -> str:
        return f"{'Max' if self.max_heap else 'Min'}Heap({self.heap})"


class PriorityQueue:
    """A priority queue implementation using a binary heap."""

    def __init__(self, max_priority: bool = False):
        """
        Initialize an empty priority queue.

        Args:
            max_priority: If True, higher values have higher priority; otherwise, lower values have higher priority
        """
        self.heap = Heap(max_heap=max_priority)

    def enqueue(self, item: Any, priority: Any) -> None:
        """
        Enqueue an item with a priority.

        Args:
            item: Item to enqueue
            priority: Priority of the item
        """
        self.heap.push((priority, item))

    def dequeue(self) -> Any:
        """
        Dequeue the item with the highest priority.

        Returns:
            The item with the highest priority

        Raises:
            IndexError: If the priority queue is empty
        """
        if not self.heap:
            raise IndexError("Cannot dequeue from an empty priority queue")

        priority, item = self.heap.pop()
        return item

    def peek(self) -> Any:
        """
        Peek at the item with the highest priority without removing it.

        Returns:
            The item with the highest priority

        Raises:
            IndexError: If the priority queue is empty
        """
        if not self.heap:
            raise IndexError("Cannot peek at an empty priority queue")

        priority, item = self.heap.peek()
        return item

    def __len__(self) -> int:
        return len(self.heap)

    def __bool__(self) -> bool:
        return bool(self.heap)

    def __repr__(self) -> str:
        return f"PriorityQueue({self.heap})"


class DisjointSet:
    """A disjoint-set (union-find) data structure implementation."""

    def __init__(self, n: int):
        """
        Initialize a disjoint-set data structure with n elements.

        Args:
            n: Number of elements
        """
        self.parent = list(range(n))
        self.rank = [0] * n
        self.size = [1] * n
        self.count = n

    def find(self, x: int) -> int:
        """
        Find the representative (root) of the set containing x.

        Args:
            x: Element to find the representative of

        Returns:
            The representative of the set containing x
        """
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]

    def union(self, x: int, y: int) -> bool:
        """
        Union the sets containing x and y.

        Args:
            x: First element
            y: Second element

        Returns:
            True if the sets were merged, False if they were already in the same set
        """
        root_x = self.find(x)
        root_y = self.find(y)

        if root_x == root_y:
            return False

        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
            self.size[root_y] += self.size[root_x]
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
            self.size[root_x] += self.size[root_y]
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
            self.size[root_x] += self.size[root_y]

        self.count -= 1
        return True

    def connected(self, x: int, y: int) -> bool:
        """
        Check if x and y are in the same set.

        Args:
            x: First element
            y: Second element

        Returns:
            True if x and y are in the same set, False otherwise
        """
        return self.find(x) == self.find(y)

    def get_size(self, x: int) -> int:
        """
        Get the size of the set containing x.

        Args:
            x: Element to get the set size of

        Returns:
            The size of the set containing x
        """
        return self.size[self.find(x)]

    def __len__(self) -> int:
        return self.count

    def __repr__(self) -> str:
        sets = {}
        for i in range(len(self.parent)):
            root = self.find(i)
            if root not in sets:
                sets[root] = []
            sets[root].append(i)

        return f"DisjointSet({list(sets.values())})"


class Trie:
    """A trie (prefix tree) implementation."""

    def __init__(self):
        """Initialize an empty trie."""
        self.root = {}
        self.end_symbol = '*'

    def insert(self, word: str) -> None:
        """
        Insert a word into the trie.

        Args:
            word: Word to insert
        """
        node = self.root
        for char in word:
            if char not in node:
                node[char] = {}
            node = node[char]
        node[self.end_symbol] = True

    def search(self, word: str) -> bool:
        """
        Search for a word in the trie.

        Args:
            word: Word to search for

        Returns:
            True if the word is in the trie, False otherwise
        """
        node = self.root
        for char in word:
            if char not in node:
                return False
            node = node[char]

        return self.end_symbol in node

    def starts_with(self, prefix: str) -> bool:
        """
        Check if there is any word in the trie that starts with the given prefix.

        Args:
            prefix: Prefix to check

        Returns:
            True if there is any word in the trie that starts with the given prefix, False otherwise
        """
        node = self.root
        for char in prefix:
            if char not in node:
                return False
            node = node[char]

        return True

    def get_words_with_prefix(self, prefix: str) -> List[str]:
        """
        Get all words in the trie that start with the given prefix.

        Args:
            prefix: Prefix to search for

        Returns:
            A list of words in the trie that start with the given prefix
        """
        node = self.root
        for char in prefix:
            if char not in node:
                return []
            node = node[char]

        words = []
        self._collect_words(node, prefix, words)
        return words

    def _collect_words(self, node: Dict[str, Any], prefix: str, words: List[str]) -> None:
        """
        Recursively collect all words in the trie that start with the given prefix.

        Args:
            node: Current node in the trie
            prefix: Current prefix
            words: List to store the words
        """
        if self.end_symbol in node:
            words.append(prefix)

        for char in node:
            if char != self.end_symbol:
                self._collect_words(node[char], prefix + char, words)

    def delete(self, word: str) -> bool:
        """
        Delete a word from the trie.

        Args:
            word: Word to delete

        Returns:
            True if the word was found and deleted, False otherwise
        """
        if not self.search(word):
            return False

        self._delete_recursive(self.root, word, 0)
        return True

    def _delete_recursive(self, node: Dict[str, Any], word: str, index: int) -> bool:
        """
        Recursively delete a word from the trie.

        Args:
            node: Current node in the trie
            word: Word to delete
            index: Current index in the word

        Returns:
            True if the node should be deleted, False otherwise
        """
        if index == len(word):
            del node[self.end_symbol]
            return len(node) == 0

        char = word[index]
        should_delete_node = self._delete_recursive(node[char], word, index + 1)

        if should_delete_node:
            del node[char]
            return len(node) == 0

        return False

    def __repr__(self) -> str:
        return f"Trie({self.get_words_with_prefix('')})"


class Graph:
    """A graph implementation using an adjacency list."""

    def __init__(self, directed: bool = False, weighted: bool = False):
        """
        Initialize an empty graph.

        Args:
            directed: If True, the graph is directed; otherwise, it is undirected
            weighted: If True, the graph is weighted; otherwise, it is unweighted
        """
        self.adjacency_list = {}
        self.directed = directed
        self.weighted = weighted

    def add_vertex(self, vertex: Any) -> None:
        """
        Add a vertex to the graph.

        Args:
            vertex: Vertex to add
        """
        if vertex not in self.adjacency_list:
            self.adjacency_list[vertex] = {}

    def add_edge(self, source: Any, destination: Any, weight: float = 1.0) -> None:
        """
        Add an edge to the graph.

        Args:
            source: Source vertex
            destination: Destination vertex
            weight: Weight of the edge (default: 1.0)
        """
        self.add_vertex(source)
        self.add_vertex(destination)

        if self.weighted:
            self.adjacency_list[source][destination] = weight
        else:
            self.adjacency_list[source][destination] = 1

        if not self.directed:
            if self.weighted:
                self.adjacency_list[destination][source] = weight
            else:
                self.adjacency_list[destination][source] = 1

    def remove_vertex(self, vertex: Any) -> None:
        """
        Remove a vertex from the graph.

        Args:
            vertex: Vertex to remove
        """
        if vertex not in self.adjacency_list:
            return

        # Remove all edges to this vertex
        for v in self.adjacency_list:
            if vertex in self.adjacency_list[v]:
                del self.adjacency_list[v][vertex]

        # Remove the vertex itself
        del self.adjacency_list[vertex]

    def remove_edge(self, source: Any, destination: Any) -> None:
        """
        Remove an edge from the graph.

        Args:
            source: Source vertex
            destination: Destination vertex
        """
        if source in self.adjacency_list and destination in self.adjacency_list[source]:
            del self.adjacency_list[source][destination]

        if not self.directed:
            if destination in self.adjacency_list and source in self.adjacency_list[destination]:
                del self.adjacency_list[destination][source]

    def get_vertices(self) -> List[Any]:
        """
        Get all vertices in the graph.

        Returns:
            A list of all vertices in the graph
        """
        return list(self.adjacency_list.keys())

    def get_edges(self) -> List[Tuple[Any, Any, float]]:
        """
        Get all edges in the graph.

        Returns:
            A list of tuples (source, destination, weight) representing all edges in the graph
        """
        edges = []
        for source in self.adjacency_list:
            for destination, weight in self.adjacency_list[source].items():
                if self.directed or source <= destination:  # Avoid duplicates in undirected graphs
                    edges.append((source, destination, weight))

        return edges

    def get_neighbors(self, vertex: Any) -> Dict[Any, float]:
        """
        Get all neighbors of a vertex.

        Args:
            vertex: Vertex to get neighbors of

        Returns:
            A dictionary mapping neighbors to edge weights
        """
        if vertex in self.adjacency_list:
            return self.adjacency_list[vertex]
        return {}

    def has_vertex(self, vertex: Any) -> bool:
        """
        Check if the graph has a vertex.

        Args:
            vertex: Vertex to check

        Returns:
            True if the graph has the vertex, False otherwise
        """
        return vertex in self.adjacency_list

    def has_edge(self, source: Any, destination: Any) -> bool:
        """
        Check if the graph has an edge.

        Args:
            source: Source vertex
            destination: Destination vertex

        Returns:
            True if the graph has the edge, False otherwise
        """
        return (source in self.adjacency_list and
                destination in self.adjacency_list[source])

    def get_edge_weight(self, source: Any, destination: Any) -> Optional[float]:
        """
        Get the weight of an edge.

        Args:
            source: Source vertex
            destination: Destination vertex

        Returns:
            The weight of the edge, or None if the edge does not exist
        """
        if self.has_edge(source, destination):
            return self.adjacency_list[source][destination]
        return None

    def breadth_first_search(self, start: Any) -> List[Any]:
        """
        Perform a breadth-first search starting from a vertex.

        Args:
            start: Starting vertex

        Returns:
            A list of vertices in breadth-first order
        """
        if start not in self.adjacency_list:
            return []

        visited = set()
        queue = collections.deque([start])
        result = []

        visited.add(start)

        while queue:
            vertex = queue.popleft()
            result.append(vertex)

            for neighbor in self.adjacency_list[vertex]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return result

    def depth_first_search(self, start: Any) -> List[Any]:
        """
        Perform a depth-first search starting from a vertex.

        Args:
            start: Starting vertex

        Returns:
            A list of vertices in depth-first order
        """
        if start not in self.adjacency_list:
            return []

        visited = set()
        result = []

        def dfs(vertex):
            visited.add(vertex)
            result.append(vertex)

            for neighbor in self.adjacency_list[vertex]:
                if neighbor not in visited:
                    dfs(neighbor)

        dfs(start)
        return result

    def __len__(self) -> int:
        return len(self.adjacency_list)

    def __repr__(self) -> str:
        return f"Graph(vertices={self.get_vertices()}, edges={self.get_edges()})"


def dijkstra(graph: Graph, start: Any) -> Tuple[Dict[Any, float], Dict[Any, Any]]:
    """
    Find the shortest paths from a starting vertex to all other vertices in a weighted graph.

    Args:
        graph: Graph to search
        start: Starting vertex

    Returns:
        A tuple (distances, predecessors) where distances maps each vertex to its shortest distance
        from the start vertex, and predecessors maps each vertex to its predecessor in the shortest path

    Raises:
        ValueError: If the graph is not weighted or the start vertex is not in the graph
    """
    if not graph.weighted:
        raise ValueError("Dijkstra's algorithm requires a weighted graph")

    if start not in graph.adjacency_list:
        raise ValueError("Start vertex not in graph")

    # Initialize distances and predecessors
    distances = {vertex: float('infinity') for vertex in graph.adjacency_list}
    distances[start] = 0
    predecessors = {vertex: None for vertex in graph.adjacency_list}

    # Priority queue for vertices to visit
    pq = [(0, start)]

    # Set of visited vertices
    visited = set()

    while pq:
        # Get the vertex with the smallest distance
        current_distance, current_vertex = heapq.heappop(pq)

        # If we've already visited this vertex, skip it
        if current_vertex in visited:
            continue

        # Mark the vertex as visited
        visited.add(current_vertex)

        # If the current distance is greater than the known distance, skip it
        if current_distance > distances[current_vertex]:
            continue

        # Check all neighbors of the current vertex
        for neighbor, weight in graph.adjacency_list[current_vertex].items():
            # Calculate the distance to the neighbor through the current vertex
            distance = current_distance + weight

            # If this path is shorter than the known path, update it
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                predecessors[neighbor] = current_vertex
                heapq.heappush(pq, (distance, neighbor))

    return distances, predecessors


def bellman_ford(graph: Graph, start: Any) -> Tuple[Dict[Any, float], Dict[Any, Any]]:
    """
    Find the shortest paths from a starting vertex to all other vertices in a weighted graph,
    even if the graph contains negative edge weights.

    Args:
        graph: Graph to search
        start: Starting vertex

    Returns:
        A tuple (distances, predecessors) where distances maps each vertex to its shortest distance
        from the start vertex, and predecessors maps each vertex to its predecessor in the shortest path

    Raises:
        ValueError: If the graph is not weighted, the start vertex is not in the graph,
                   or the graph contains a negative cycle
    """
    if not graph.weighted:
        raise ValueError("Bellman-Ford algorithm requires a weighted graph")

    if start not in graph.adjacency_list:
        raise ValueError("Start vertex not in graph")

    # Initialize distances and predecessors
    distances = {vertex: float('infinity') for vertex in graph.adjacency_list}
    distances[start] = 0
    predecessors = {vertex: None for vertex in graph.adjacency_list}

    # Relax edges repeatedly
    for _ in range(len(graph.adjacency_list) - 1):
        for source, destination, weight in graph.get_edges():
            if distances[source] != float('infinity') and distances[source] + weight < distances[destination]:
                distances[destination] = distances[source] + weight
                predecessors[destination] = source

    # Check for negative cycles
    for source, destination, weight in graph.get_edges():
        if distances[source] != float('infinity') and distances[source] + weight < distances[destination]:
            raise ValueError("Graph contains a negative cycle")

    return distances, predecessors


def floyd_warshall(graph: Graph) -> Dict[Any, Dict[Any, float]]:
    """
    Find the shortest paths between all pairs of vertices in a weighted graph.

    Args:
        graph: Graph to search

    Returns:
        A dictionary mapping each vertex to a dictionary mapping each other vertex to the shortest distance

    Raises:
        ValueError: If the graph is not weighted or the graph contains a negative cycle
    """
    if not graph.weighted:
        raise ValueError("Floyd-Warshall algorithm requires a weighted graph")

    # Initialize distances
    distances = {}
    for vertex in graph.adjacency_list:
        distances[vertex] = {}
        for other_vertex in graph.adjacency_list:
            if vertex == other_vertex:
                distances[vertex][other_vertex] = 0
            elif graph.has_edge(vertex, other_vertex):
                distances[vertex][other_vertex] = graph.get_edge_weight(vertex, other_vertex)
            else:
                distances[vertex][other_vertex] = float('infinity')

    # Update distances
    for k in graph.adjacency_list:
        for i in graph.adjacency_list:
            for j in graph.adjacency_list:
                if distances[i][k] + distances[k][j] < distances[i][j]:
                    distances[i][j] = distances[i][k] + distances[k][j]

    # Check for negative cycles
    for vertex in graph.adjacency_list:
        if distances[vertex][vertex] < 0:
            raise ValueError("Graph contains a negative cycle")

    return distances


def prim(graph: Graph) -> List[Tuple[Any, Any, float]]:
    """
    Find a minimum spanning tree of a weighted undirected graph using Prim's algorithm.

    Args:
        graph: Graph to find a minimum spanning tree of

    Returns:
        A list of edges (source, destination, weight) in the minimum spanning tree

    Raises:
        ValueError: If the graph is not weighted or not undirected
    """
    if not graph.weighted:
        raise ValueError("Prim's algorithm requires a weighted graph")

    if graph.directed:
        raise ValueError("Prim's algorithm requires an undirected graph")

    if not graph.adjacency_list:
        return []

    # Start with an arbitrary vertex
    start = next(iter(graph.adjacency_list))

    # Set of vertices in the minimum spanning tree
    mst_vertices = {start}

    # Edges in the minimum spanning tree
    mst_edges = []

    # Priority queue for edges
    pq = []

    # Add all edges from the start vertex to the priority queue
    for neighbor, weight in graph.adjacency_list[start].items():
        heapq.heappush(pq, (weight, start, neighbor))

    while pq and len(mst_vertices) < len(graph.adjacency_list):
        # Get the edge with the smallest weight
        weight, source, destination = heapq.heappop(pq)

        # If the destination is already in the MST, skip this edge
        if destination in mst_vertices:
            continue

        # Add the destination to the MST
        mst_vertices.add(destination)

        # Add the edge to the MST
        mst_edges.append((source, destination, weight))

        # Add all edges from the destination to the priority queue
        for neighbor, weight in graph.adjacency_list[destination].items():
            if neighbor not in mst_vertices:
                heapq.heappush(pq, (weight, destination, neighbor))

    return mst_edges


def kruskal(graph: Graph) -> List[Tuple[Any, Any, float]]:
    """
    Find a minimum spanning tree of a weighted undirected graph using Kruskal's algorithm.

    Args:
        graph: Graph to find a minimum spanning tree of

    Returns:
        A list of edges (source, destination, weight) in the minimum spanning tree

    Raises:
        ValueError: If the graph is not weighted or not undirected
    """
    if not graph.weighted:
        raise ValueError("Kruskal's algorithm requires a weighted graph")

    if graph.directed:
        raise ValueError("Kruskal's algorithm requires an undirected graph")

    if not graph.adjacency_list:
        return []

    # Get all edges and sort them by weight
    edges = graph.get_edges()
    edges.sort(key=lambda x: x[2])

    # Initialize disjoint set
    vertices = graph.get_vertices()
    vertex_to_index = {vertex: i for i, vertex in enumerate(vertices)}
    ds = DisjointSet(len(vertices))

    # Edges in the minimum spanning tree
    mst_edges = []

    for source, destination, weight in edges:
        source_index = vertex_to_index[source]
        destination_index = vertex_to_index[destination]

        # If adding this edge doesn't create a cycle, add it to the MST
        if not ds.connected(source_index, destination_index):
            ds.union(source_index, destination_index)
            mst_edges.append((source, destination, weight))

            # If we've added enough edges, we're done
            if len(mst_edges) == len(vertices) - 1:
                break

    return mst_edges


def topological_sort(graph: Graph) -> List[Any]:
    """
    Perform a topological sort of a directed acyclic graph.

    Args:
        graph: Graph to sort

    Returns:
        A list of vertices in topological order

    Raises:
        ValueError: If the graph is not directed or contains a cycle
    """
    if not graph.directed:
        raise ValueError("Topological sort requires a directed graph")

    # Initialize in-degree of all vertices
    in_degree = {vertex: 0 for vertex in graph.adjacency_list}

    # Calculate in-degree of all vertices
    for source in graph.adjacency_list:
        for destination in graph.adjacency_list[source]:
            in_degree[destination] += 1

    # Queue of vertices with in-degree 0
    queue = collections.deque([vertex for vertex, degree in in_degree.items() if degree == 0])

    # Result list
    result = []

    while queue:
        vertex = queue.popleft()
        result.append(vertex)

        for neighbor in graph.adjacency_list[vertex]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # If we haven't visited all vertices, there's a cycle
    if len(result) != len(graph.adjacency_list):
        raise ValueError("Graph contains a cycle")

    return result


def is_bipartite(graph: Graph) -> bool:
    """
    Check if a graph is bipartite (can be colored with two colors such that no adjacent vertices have the same color).

    Args:
        graph: Graph to check

    Returns:
        True if the graph is bipartite, False otherwise
    """
    if not graph.adjacency_list:
        return True

    # Color map: 0 = uncolored, 1 = color 1, -1 = color 2
    color = {vertex: 0 for vertex in graph.adjacency_list}

    # Check each connected component
    for start in graph.adjacency_list:
        if color[start] != 0:
            continue

        # Start BFS from this vertex
        color[start] = 1
        queue = collections.deque([start])

        while queue:
            vertex = queue.popleft()

            for neighbor in graph.adjacency_list[vertex]:
                if color[neighbor] == 0:
                    # Color the neighbor with the opposite color
                    color[neighbor] = -color[vertex]
                    queue.append(neighbor)
                elif color[neighbor] == color[vertex]:
                    # If the neighbor has the same color, the graph is not bipartite
                    return False

    return True


def has_cycle(graph: Graph) -> bool:
    """
    Check if a graph has a cycle.

    Args:
        graph: Graph to check

    Returns:
        True if the graph has a cycle, False otherwise
    """
    if graph.directed:
        return has_cycle_directed(graph)
    else:
        return has_cycle_undirected(graph)


def has_cycle_directed(graph: Graph) -> bool:
    """
    Check if a directed graph has a cycle.

    Args:
        graph: Directed graph to check

    Returns:
        True if the graph has a cycle, False otherwise
    """
    # 0 = unvisited, 1 = visiting, 2 = visited
    state = {vertex: 0 for vertex in graph.adjacency_list}

    def dfs(vertex):
        state[vertex] = 1

        for neighbor in graph.adjacency_list[vertex]:
            if state[neighbor] == 0:
                if dfs(neighbor):
                    return True
            elif state[neighbor] == 1:
                return True

        state[vertex] = 2
        return False

    for vertex in graph.adjacency_list:
        if state[vertex] == 0:
            if dfs(vertex):
                return True

    return False


def has_cycle_undirected(graph: Graph) -> bool:
    """
    Check if an undirected graph has a cycle.

    Args:
        graph: Undirected graph to check

    Returns:
        True if the graph has a cycle, False otherwise
    """
    visited = set()

    def dfs(vertex, parent):
        visited.add(vertex)

        for neighbor in graph.adjacency_list[vertex]:
            if neighbor not in visited:
                if dfs(neighbor, vertex):
                    return True
            elif neighbor != parent:
                return True

        return False

    for vertex in graph.adjacency_list:
        if vertex not in visited:
            if dfs(vertex, None):
                return True

    return False


# -----------------------------------------------------------------------------
# SECTION 4: SORTING AND SEARCHING ALGORITHMS
# -----------------------------------------------------------------------------

def bubble_sort(arr: List[Any]) -> List[Any]:
    """
    Sort a list using the bubble sort algorithm.

    Args:
        arr: List to sort

    Returns:
        Sorted list
    """
    result = arr.copy()
    n = len(result)

    for i in range(n):
        # Flag to optimize if no swaps are made in a pass
        swapped = False

        for j in range(0, n - i - 1):
            if result[j] > result[j + 1]:
                result[j], result[j + 1] = result[j + 1], result[j]
                swapped = True

        # If no swaps were made in this pass, the list is sorted
        if not swapped:
            break

    return result


def selection_sort(arr: List[Any]) -> List[Any]:
    """
    Sort a list using the selection sort algorithm.

    Args:
        arr: List to sort

    Returns:
        Sorted list
    """
    result = arr.copy()
    n = len(result)

    for i in range(n):
        # Find the minimum element in the unsorted part
        min_idx = i
        for j in range(i + 1, n):
            if result[j] < result[min_idx]:
                min_idx = j

        # Swap the found minimum element with the first element
        result[i], result[min_idx] = result[min_idx], result[i]

    return result


def insertion_sort(arr: List[Any]) -> List[Any]:
    """
    Sort a list using the insertion sort algorithm.

    Args:
        arr: List to sort

    Returns:
        Sorted list
    """
    result = arr.copy()
    n = len(result)

    for i in range(1, n):
        key = result[i]
        j = i - 1

        # Move elements greater than key one position ahead
        while j >= 0 and result[j] > key:
            result[j + 1] = result[j]
            j -= 1

        result[j + 1] = key

    return result


def merge_sort(arr: List[Any]) -> List[Any]:
    """
    Sort a list using the merge sort algorithm.

    Args:
        arr: List to sort

    Returns:
        Sorted list
    """
    if len(arr) <= 1:
        return arr.copy()

    # Split the list into two halves
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])

    # Merge the two sorted halves
    return _merge(left, right)


def _merge(left: List[Any], right: List[Any]) -> List[Any]:
    """
    Merge two sorted lists.

    Args:
        left: First sorted list
        right: Second sorted list

    Returns:
        Merged sorted list
    """
    result = []
    i = j = 0

    # Compare elements from both lists and add the smaller one to the result
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    # Add any remaining elements
    result.extend(left[i:])
    result.extend(right[j:])

    return result


def quick_sort(arr: List[Any]) -> List[Any]:
    """
    Sort a list using the quick sort algorithm.

    Args:
        arr: List to sort

    Returns:
        Sorted list
    """
    result = arr.copy()
    _quick_sort_helper(result, 0, len(result) - 1)
    return result


def _quick_sort_helper(arr: List[Any], low: int, high: int) -> None:
    """
    Helper function for quick sort.

    Args:
        arr: List to sort
        low: Starting index
        high: Ending index
    """
    if low < high:
        # Partition the array and get the pivot index
        pivot_idx = _partition(arr, low, high)

        # Sort the elements before and after the pivot
        _quick_sort_helper(arr, low, pivot_idx - 1)
        _quick_sort_helper(arr, pivot_idx + 1, high)


def _partition(arr: List[Any], low: int, high: int) -> int:
    """
    Partition the array and return the pivot index.

    Args:
        arr: List to partition
        low: Starting index
        high: Ending index

    Returns:
        Pivot index
    """
    # Choose the rightmost element as the pivot
    pivot = arr[high]

    # Index of the smaller element
    i = low - 1

    for j in range(low, high):
        # If the current element is smaller than or equal to the pivot
        if arr[j] <= pivot:
            # Increment the index of the smaller element
            i += 1
            arr[i], arr[j] = arr[j], arr[i]

    # Place the pivot in its correct position
    arr[i + 1], arr[high] = arr[high], arr[i + 1]

    return i + 1


def heap_sort(arr: List[Any]) -> List[Any]:
    """
    Sort a list using the heap sort algorithm.

    Args:
        arr: List to sort

    Returns:
        Sorted list
    """
    result = arr.copy()
    n = len(result)

    # Build a max heap
    for i in range(n // 2 - 1, -1, -1):
        _heapify(result, n, i)

    # Extract elements from the heap one by one
    for i in range(n - 1, 0, -1):
        result[0], result[i] = result[i], result[0]
        _heapify(result, i, 0)

    return result


def _heapify(arr: List[Any], n: int, i: int) -> None:
    """
    Heapify a subtree rooted at index i.

    Args:
        arr: List to heapify
        n: Size of the heap
        i: Root index of the subtree to heapify
    """
    largest = i
    left = 2 * i + 1
    right = 2 * i + 2

    # Check if left child exists and is greater than root
    if left < n and arr[left] > arr[largest]:
        largest = left

    # Check if right child exists and is greater than root
    if right < n and arr[right] > arr[largest]:
        largest = right

    # If the largest is not the root
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        _heapify(arr, n, largest)


def counting_sort(arr: List[int], max_val: Optional[int] = None) -> List[int]:
    """
    Sort a list of non-negative integers using the counting sort algorithm.

    Args:
        arr: List of non-negative integers to sort
        max_val: Maximum value in the list (if None, it will be computed)

    Returns:
        Sorted list

    Raises:
        ValueError: If the list contains negative integers
    """
    if not arr:
        return []

    if any(x < 0 for x in arr):
        raise ValueError("Counting sort requires non-negative integers")

    if max_val is None:
        max_val = max(arr)

    # Initialize count array
    count = [0] * (max_val + 1)

    # Count occurrences of each element
    for x in arr:
        count[x] += 1

    # Compute cumulative sum
    for i in range(1, len(count)):
        count[i] += count[i - 1]

    # Build the output array
    result = [0] * len(arr)
    for x in reversed(arr):
        result[count[x] - 1] = x
        count[x] -= 1

    return result


def radix_sort(arr: List[int]) -> List[int]:
    """
    Sort a list of non-negative integers using the radix sort algorithm.

    Args:
        arr: List of non-negative integers to sort

    Returns:
        Sorted list

    Raises:
        ValueError: If the list contains negative integers
    """
    if not arr:
        return []

    if any(x < 0 for x in arr):
        raise ValueError("Radix sort requires non-negative integers")

    # Find the maximum number to know the number of digits
    max_val = max(arr)

    # Do counting sort for every digit
    exp = 1
    while max_val // exp > 0:
        _counting_sort_by_digit(arr, exp)
        exp *= 10

    return arr


def _counting_sort_by_digit(arr: List[int], exp: int) -> None:
    """
    Sort a list of integers based on a specific digit.

    Args:
        arr: List of integers to sort
        exp: Digit place value (1, 10, 100, etc.)
    """
    n = len(arr)
    output = [0] * n
    count = [0] * 10

    # Count occurrences of each digit
    for i in range(n):
        index = (arr[i] // exp) % 10
        count[index] += 1

    # Compute cumulative sum
    for i in range(1, 10):
        count[i] += count[i - 1]

    # Build the output array
    for i in range(n - 1, -1, -1):
        index = (arr[i] // exp) % 10
        output[count[index] - 1] = arr[i]
        count[index] -= 1

    # Copy the output array to arr
    for i in range(n):
        arr[i] = output[i]


def bucket_sort(arr: List[float], num_buckets: int = 10) -> List[float]:
    """
    Sort a list of floating-point numbers in the range [0, 1) using the bucket sort algorithm.

    Args:
        arr: List of floating-point numbers in the range [0, 1) to sort
        num_buckets: Number of buckets to use

    Returns:
        Sorted list

    Raises:
        ValueError: If the list contains numbers outside the range [0, 1)
    """
    if not arr:
        return []

    if any(x < 0 or x >= 1 for x in arr):
        raise ValueError("Bucket sort requires numbers in the range [0, 1)")

    # Create empty buckets
    buckets = [[] for _ in range(num_buckets)]

    # Put elements into buckets
    for x in arr:
        bucket_idx = int(x * num_buckets)
        buckets[bucket_idx].append(x)

    # Sort each bucket
    for i in range(num_buckets):
        buckets[i].sort()

    # Concatenate all buckets
    result = []
    for bucket in buckets:
        result.extend(bucket)

    return result


def binary_search(arr: List[Any], target: Any) -> int:
    """
    Search for a target value in a sorted list using binary search.

    Args:
        arr: Sorted list to search in
        target: Value to search for

    Returns:
        Index of the target if found, -1 otherwise
    """
    left, right = 0, len(arr) - 1

    while left <= right:
        mid = (left + right) // 2

        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1


def binary_search_recursive(arr: List[Any], target: Any, left: int = 0, right: Optional[int] = None) -> int:
    """
    Search for a target value in a sorted list using recursive binary search.

    Args:
        arr: Sorted list to search in
        target: Value to search for
        left: Left index of the search range
        right: Right index of the search range

    Returns:
        Index of the target if found, -1 otherwise
    """
    if right is None:
        right = len(arr) - 1

    if left > right:
        return -1

    mid = (left + right) // 2

    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        return binary_search_recursive(arr, target, mid + 1, right)
    else:
        return binary_search_recursive(arr, target, left, mid - 1)


def interpolation_search(arr: List[int], target: int) -> int:
    """
    Search for a target value in a sorted list of integers using interpolation search.

    Args:
        arr: Sorted list of integers to search in
        target: Value to search for

    Returns:
        Index of the target if found, -1 otherwise
    """
    left, right = 0, len(arr) - 1

    while left <= right and arr[left] <= target <= arr[right]:
        if left == right:
            if arr[left] == target:
                return left
            return -1

        # Calculate the position using interpolation formula
        pos = left + ((target - arr[left]) * (right - left)) // (arr[right] - arr[left])

        if arr[pos] == target:
            return pos
        elif arr[pos] < target:
            left = pos + 1
        else:
            right = pos - 1

    return -1


def jump_search(arr: List[Any], target: Any) -> int:
    """
    Search for a target value in a sorted list using jump search.

    Args:
        arr: Sorted list to search in
        target: Value to search for

    Returns:
        Index of the target if found, -1 otherwise
    """
    n = len(arr)
    if n == 0:
        return -1

    # Finding the block size to be jumped
    step = int(math.sqrt(n))

    # Finding the block where the target may be present
    prev = 0
    while prev < n and arr[min(step, n) - 1] < target:
        prev = step
        step += int(math.sqrt(n))
        if prev >= n:
            return -1

    # Linear search for the target in the block
    while prev < min(step, n):
        if arr[prev] == target:
            return prev
        prev += 1

    return -1


def exponential_search(arr: List[Any], target: Any) -> int:
    """
    Search for a target value in a sorted list using exponential search.

    Args:
        arr: Sorted list to search in
        target: Value to search for

    Returns:
        Index of the target if found, -1 otherwise
    """
    n = len(arr)
    if n == 0:
        return -1

    # If the target is the first element
    if arr[0] == target:
        return 0

    # Find the range for binary search
    i = 1
    while i < n and arr[i] <= target:
        i *= 2

    # Call binary search for the found range
    return binary_search_recursive(arr, target, i // 2, min(i, n - 1))


def ternary_search(arr: List[Any], target: Any) -> int:
    """
    Search for a target value in a sorted list using ternary search.

    Args:
        arr: Sorted list to search in
        target: Value to search for

    Returns:
        Index of the target if found, -1 otherwise
    """
    left, right = 0, len(arr) - 1

    while left <= right:
        # Calculate the two mid points
        mid1 = left + (right - left) // 3
        mid2 = right - (right - left) // 3

        if arr[mid1] == target:
            return mid1
        elif arr[mid2] == target:
            return mid2
        elif target < arr[mid1]:
            right = mid1 - 1
        elif target > arr[mid2]:
            left = mid2 + 1
        else:
            left = mid1 + 1
            right = mid2 - 1

    return -1


# -----------------------------------------------------------------------------
# SECTION 5: STRING ALGORITHMS
# -----------------------------------------------------------------------------

def naive_string_matching(text: str, pattern: str) -> List[int]:
    """
    Find all occurrences of a pattern in a text using the naive string matching algorithm.

    Args:
        text: Text to search in
        pattern: Pattern to search for

    Returns:
        A list of starting indices of all occurrences of the pattern in the text
    """
    n, m = len(text), len(pattern)
    result = []

    # Check for each possible starting position
    for i in range(n - m + 1):
        j = 0

        # Check if the pattern matches at this position
        while j < m and text[i + j] == pattern[j]:
            j += 1

        # If the pattern matches, add the starting index to the result
        if j == m:
            result.append(i)

    return result


def rabin_karp(text: str, pattern: str, prime: int = 101) -> List[int]:
    """
    Find all occurrences of a pattern in a text using the Rabin-Karp algorithm.

    Args:
        text: Text to search in
        pattern: Pattern to search for
        prime: Prime number for hash calculation

    Returns:
        A list of starting indices of all occurrences of the pattern in the text
    """
    n, m = len(text), len(pattern)
    result = []

    if m > n or m == 0:
        return result

    # Hash values
    pattern_hash = 0
    text_hash = 0

    # Hash value of the highest place value
    h = 1

    # Calculate h = pow(256, m-1) % prime
    for i in range(m - 1):
        h = (h * 256) % prime

    # Calculate the hash value of the pattern and the first window of the text
    for i in range(m):
        pattern_hash = (pattern_hash * 256 + ord(pattern[i])) % prime
        text_hash = (text_hash * 256 + ord(text[i])) % prime

    # Slide the pattern over the text
    for i in range(n - m + 1):
        # Check if the hash values match
        if pattern_hash == text_hash:
            # Check if the pattern matches at this position
            j = 0
            while j < m and text[i + j] == pattern[j]:
                j += 1

            # If the pattern matches, add the starting index to the result
            if j == m:
                result.append(i)

        # Calculate the hash value for the next window
        if i < n - m:
            text_hash = ((text_hash - ord(text[i]) * h) * 256 + ord(text[i + m])) % prime

            # Make sure the hash value is positive
            if text_hash < 0:
                text_hash += prime

    return result


def knuth_morris_pratt(text: str, pattern: str) -> List[int]:
    """
    Find all occurrences of a pattern in a text using the Knuth-Morris-Pratt algorithm.

    Args:
        text: Text to search in
        pattern: Pattern to search for

    Returns:
        A list of starting indices of all occurrences of the pattern in the text
    """
    n, m = len(text), len(pattern)
    result = []

    if m > n or m == 0:
        return result

    # Compute the longest proper prefix which is also suffix array
    lps = [0] * m
    _compute_lps_array(pattern, lps)

    i, j = 0, 0
    while i < n:
        if pattern[j] == text[i]:
            i += 1
            j += 1

        if j == m:
            result.append(i - j)
            j = lps[j - 1]
        elif i < n and pattern[j] != text[i]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1

    return result


def _compute_lps_array(pattern: str, lps: List[int]) -> None:
    """
    Compute the longest proper prefix which is also suffix array.

    Args:
        pattern: Pattern to compute the LPS array for
        lps: List to store the LPS array
    """
    m = len(pattern)
    length = 0
    i = 1

    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1


def boyer_moore(text: str, pattern: str) -> List[int]:
    """
    Find all occurrences of a pattern in a text using the Boyer-Moore algorithm.

    Args:
        text: Text to search in
        pattern: Pattern to search for

    Returns:
        A list of starting indices of all occurrences of the pattern in the text
    """
    n, m = len(text), len(pattern)
    result = []

    if m > n or m == 0:
        return result

    # Preprocess the pattern
    bad_char = _preprocess_bad_char(pattern)
    good_suffix = _preprocess_good_suffix(pattern)

    # Search for the pattern
    i = 0
    while i <= n - m:
        j = m - 1

        # Check if the pattern matches at this position
        while j >= 0 and pattern[j] == text[i + j]:
            j -= 1

        # If the pattern matches, add the starting index to the result
        if j < 0:
            result.append(i)
            i += good_suffix[0]
        else:
            i += max(good_suffix[j], j - bad_char.get(text[i + j], -1))

    return result


def _preprocess_bad_char(pattern: str) -> Dict[str, int]:
    """
    Preprocess the pattern for the bad character heuristic.

    Args:
        pattern: Pattern to preprocess

    Returns:
        A dictionary mapping characters to their rightmost occurrence in the pattern
    """
    m = len(pattern)
    bad_char = {}

    for i in range(m):
        bad_char[pattern[i]] = i

    return bad_char


def _preprocess_good_suffix(pattern: str) -> List[int]:
    """
    Preprocess the pattern for the good suffix heuristic.

    Args:
        pattern: Pattern to preprocess

    Returns:
        A list of shift values for each position in the pattern
    """
    m = len(pattern)
    good_suffix = [0] * m

    # Compute the suffix array
    suffix = _compute_suffix_array(pattern)

    # Initialize all shift values to m
    for i in range(m):
        good_suffix[i] = m

    # Case 1: The substring is a suffix of the pattern
    j = 0
    for i in range(m - 1, -1, -1):
        if suffix[i] == i + 1:
            while j < m - 1 - i:
                if good_suffix[j] == m:
                    good_suffix[j] = m - 1 - i
                j += 1

    # Case 2: The substring is not a suffix of the pattern
    for i in range(m - 1):
        good_suffix[m - 1 - suffix[i]] = m - 1 - i

    return good_suffix


def _compute_suffix_array(pattern: str) -> List[int]:
    """
    Compute the suffix array for a pattern.

    Args:
        pattern: Pattern to compute the suffix array for

    Returns:
        A list where suffix[i] is the length of the longest suffix of pattern[0:i+1]
        that is also a suffix of the pattern
    """
    m = len(pattern)
    suffix = [0] * m
    suffix[m - 1] = m

    g, f = m - 1, 0

    for i in range(m - 2, -1, -1):
        if i > g and suffix[i + m - 1 - f] < i - g:
            suffix[i] = suffix[i + m - 1 - f]
        else:
            if i < g:
                g = i
            f = i

            while g >= 0 and pattern[g] == pattern[g + m - 1 - f]:
                g -= 1

            suffix[i] = f - g

    return suffix


def z_algorithm(text: str, pattern: str) -> List[int]:
    """
    Find all occurrences of a pattern in a text using the Z algorithm.

    Args:
        text: Text to search in
        pattern: Pattern to search for

    Returns:
        A list of starting indices of all occurrences of the pattern in the text
    """
    # Concatenate pattern and text with a special character in between
    concat = pattern + "$" + text
    n = len(concat)

    # Compute the Z array
    z = [0] * n
    _compute_z_array(concat, z)

    # Find all occurrences of the pattern in the text
    result = []
    for i in range(len(pattern) + 1, n):
        if z[i] == len(pattern):
            result.append(i - len(pattern) - 1)

    return result


def _compute_z_array(s: str, z: List[int]) -> None:
    """
    Compute the Z array for a string.

    Args:
        s: String to compute the Z array for
        z: List to store the Z array
    """
    n = len(s)
    left, right = 0, 0

    for i in range(1, n):
        if i > right:
            # Compute Z[i] naively
            left = right = i
            while right < n and s[right - left] == s[right]:
                right += 1
            z[i] = right - left
            right -= 1
        else:
            # Use the value of Z[i - left] to compute Z[i]
            k = i - left

            # If Z[k] is less than the remaining window size, use it
            if z[k] < right - i + 1:
                z[i] = z[k]
            else:
                # Otherwise, compute Z[i] naively
                left = i
                while right < n and s[right - left] == s[right]:
                    right += 1
                z[i] = right - left
                right -= 1


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate the Levenshtein distance between two strings.

    Args:
        s1: First string
        s2: Second string

    Returns:
        The Levenshtein distance between the two strings
    """
    m, n = len(s1), len(s2)

    # Create a matrix to store the distances
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Initialize the first row and column
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    # Fill in the rest of the matrix
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j],      # Deletion
                                  dp[i][j - 1],      # Insertion
                                  dp[i - 1][j - 1])  # Substitution

    return dp[m][n]


def longest_common_subsequence(s1: str, s2: str) -> str:
    """
    Find the longest common subsequence of two strings.

    Args:
        s1: First string
        s2: Second string

    Returns:
        The longest common subsequence of the two strings
    """
    m, n = len(s1), len(s2)

    # Create a matrix to store the lengths of LCS
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Fill in the matrix
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    # Reconstruct the LCS
    lcs = []
    i, j = m, n
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            lcs.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] > dp[i][j - 1]:
            i -= 1
        else:
            j -= 1

    return ''.join(reversed(lcs))


def longest_common_substring(s1: str, s2: str) -> str:
    """
    Find the longest common substring of two strings.

    Args:
        s1: First string
        s2: Second string

    Returns:
        The longest common substring of the two strings
    """
    m, n = len(s1), len(s2)

    # Create a matrix to store the lengths of LCS
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Variables to keep track of the maximum length and ending position
    max_length = 0
    end_pos = 0

    # Fill in the matrix
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                if dp[i][j] > max_length:
                    max_length = dp[i][j]
                    end_pos = i
            else:
                dp[i][j] = 0

    # Extract the longest common substring
    return s1[end_pos - max_length:end_pos]


def manacher(s: str) -> str:
    """
    Find the longest palindromic substring in a string using Manacher's algorithm.

    Args:
        s: String to find the longest palindromic substring in

    Returns:
        The longest palindromic substring
    """
    # Preprocess the string
    t = '#' + '#'.join(s) + '#'
    n = len(t)

    # Array to store the length of palindromic substring centered at each position
    p = [0] * n

    # Variables to keep track of the center and right boundary of the rightmost palindrome
    center = right = 0

    for i in range(n):
        # Mirror of i with respect to center
        mirror = 2 * center - i

        # If i is within the right boundary, use the value of the mirror
        if i < right:
            p[i] = min(right - i, p[mirror])

        # Expand around i
        while i + p[i] + 1 < n and i - p[i] - 1 >= 0 and t[i + p[i] + 1] == t[i - p[i] - 1]:
            p[i] += 1

        # Update center and right boundary if needed
        if i + p[i] > right:
            center = i
            right = i + p[i]

    # Find the maximum palindrome length and its center
    max_len = max(p)
    center = p.index(max_len)

    # Extract the longest palindromic substring
    start = (center - max_len) // 2
    return s[start:start + max_len]


def is_palindrome(s: str) -> bool:
    """
    Check if a string is a palindrome.

    Args:
        s: String to check

    Returns:
        True if the string is a palindrome, False otherwise
    """
    # Remove non-alphanumeric characters and convert to lowercase
    s = ''.join(c.lower() for c in s if c.isalnum())

    # Check if the string is equal to its reverse
    return s == s[::-1]


# -----------------------------------------------------------------------------
# SECTION 6: DYNAMIC PROGRAMMING ALGORITHMS
# -----------------------------------------------------------------------------

def fibonacci_dp(n: int) -> int:
    """
    Calculate the nth Fibonacci number using dynamic programming.

    Args:
        n: A non-negative integer

    Returns:
        The nth Fibonacci number

    Examples:
        >>> fibonacci_dp(10)
        55
    """
    if n <= 1:
        return n

    dp = [0] * (n + 1)
    dp[1] = 1

    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]

    return dp[n]


def coin_change(coins: List[int], amount: int) -> int:
    """
    Find the minimum number of coins needed to make up a given amount.

    Args:
        coins: List of coin denominations
        amount: Target amount

    Returns:
        The minimum number of coins needed, or -1 if it's not possible

    Examples:
        >>> coin_change([1, 2, 5], 11)
        3
    """
    # Initialize dp array with a value larger than any possible result
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0

    for coin in coins:
        for i in range(coin, amount + 1):
            dp[i] = min(dp[i], dp[i - coin] + 1)

    return dp[amount] if dp[amount] != float('inf') else -1


def knapsack_01(weights: List[int], values: List[int], capacity: int) -> int:
    """
    Solve the 0/1 knapsack problem.

    Args:
        weights: List of item weights
        values: List of item values
        capacity: Knapsack capacity

    Returns:
        The maximum value that can be put in the knapsack

    Examples:
        >>> knapsack_01([10, 20, 30], [60, 100, 120], 50)
        220
    """
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        for w in range(capacity + 1):
            if weights[i - 1] <= w:
                dp[i][w] = max(values[i - 1] + dp[i - 1][w - weights[i - 1]], dp[i - 1][w])
            else:
                dp[i][w] = dp[i - 1][w]

    return dp[n][capacity]


def longest_increasing_subsequence(arr: List[int]) -> int:
    """
    Find the length of the longest increasing subsequence in an array.

    Args:
        arr: Input array

    Returns:
        The length of the longest increasing subsequence

    Examples:
        >>> longest_increasing_subsequence([10, 22, 9, 33, 21, 50, 41, 60, 80])
        6
    """
    if not arr:
        return 0

    n = len(arr)
    dp = [1] * n

    for i in range(1, n):
        for j in range(i):
            if arr[i] > arr[j]:
                dp[i] = max(dp[i], dp[j] + 1)

    return max(dp)


def edit_distance(s1: str, s2: str) -> int:
    """
    Calculate the minimum number of operations required to convert s1 to s2.

    Args:
        s1: First string
        s2: Second string

    Returns:
        The minimum number of operations (insertions, deletions, substitutions)

    Examples:
        >>> edit_distance("kitten", "sitting")
        3
    """
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j],      # Deletion
                                  dp[i][j - 1],      # Insertion
                                  dp[i - 1][j - 1])  # Substitution

    return dp[m][n]


def matrix_chain_multiplication(dims: List[int]) -> int:
    """
    Find the minimum number of scalar multiplications needed to multiply a chain of matrices.

    Args:
        dims: List of matrix dimensions (e.g., [10, 30, 5, 60] represents matrices of dimensions 10x30, 30x5, 5x60)

    Returns:
        The minimum number of scalar multiplications

    Examples:
        >>> matrix_chain_multiplication([40, 20, 30, 10, 30])
        26000
    """
    n = len(dims) - 1
    dp = [[0] * n for _ in range(n)]

    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            dp[i][j] = float('inf')
            for k in range(i, j):
                cost = dp[i][k] + dp[k + 1][j] + dims[i] * dims[k + 1] * dims[j + 1]
                dp[i][j] = min(dp[i][j], cost)

    return dp[0][n - 1]


def longest_palindromic_subsequence(s: str) -> int:
    """
    Find the length of the longest palindromic subsequence in a string.

    Args:
        s: Input string

    Returns:
        The length of the longest palindromic subsequence

    Examples:
        >>> longest_palindromic_subsequence("bbbab")
        4
    """
    n = len(s)
    dp = [[0] * n for _ in range(n)]

    # All substrings of length 1 are palindromes
    for i in range(n):
        dp[i][i] = 1

    # Fill the dp table
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                dp[i][j] = dp[i + 1][j - 1] + 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])

    return dp[0][n - 1]


def word_break(s: str, word_dict: List[str]) -> bool:
    """
    Determine if a string can be segmented into a space-separated sequence of dictionary words.

    Args:
        s: Input string
        word_dict: Dictionary of words

    Returns:
        True if the string can be segmented, False otherwise

    Examples:
        >>> word_break("leetcode", ["leet", "code"])
        True
    """
    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True

    for i in range(1, n + 1):
        for j in range(i):
            if dp[j] and s[j:i] in word_dict:
                dp[i] = True
                break

    return dp[n]


def maximum_subarray(arr: List[int]) -> int:
    """
    Find the contiguous subarray with the largest sum.

    Args:
        arr: Input array

    Returns:
        The sum of the contiguous subarray with the largest sum

    Examples:
        >>> maximum_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4])
        6
    """
    if not arr:
        return 0

    max_so_far = arr[0]
    max_ending_here = arr[0]

    for i in range(1, len(arr)):
        max_ending_here = max(arr[i], max_ending_here + arr[i])
        max_so_far = max(max_so_far, max_ending_here)

    return max_so_far


def rod_cutting(prices: List[int], n: int) -> int:
    """
    Find the maximum value obtainable by cutting up a rod of length n.

    Args:
        prices: List of prices for each length (prices[i] is the price for a rod of length i+1)
        n: Length of the rod

    Returns:
        The maximum value obtainable

    Examples:
        >>> rod_cutting([1, 5, 8, 9, 10, 17, 17, 20], 8)
        22
    """
    dp = [0] * (n + 1)

    for i in range(1, n + 1):
        max_val = float('-inf')
        for j in range(i):
            max_val = max(max_val, prices[j] + dp[i - j - 1])
        dp[i] = max_val

    return dp[n]


# -----------------------------------------------------------------------------
# SECTION 7: MACHINE LEARNING ALGORITHMS
# -----------------------------------------------------------------------------

class LinearRegression:
    """A simple linear regression implementation."""

    def __init__(self, learning_rate: float = 0.01, n_iterations: int = 1000):
        """
        Initialize a linear regression model.

        Args:
            learning_rate: Learning rate for gradient descent
            n_iterations: Number of iterations for gradient descent
        """
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.weights = None
        self.bias = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Fit the linear regression model to the training data.

        Args:
            X: Training features
            y: Training target values
        """
        n_samples, n_features = X.shape
        self.weights = np.zeros(n_features)
        self.bias = 0

        # Gradient descent
        for _ in range(self.n_iterations):
            y_pred = np.dot(X, self.weights) + self.bias

            # Compute gradients
            dw = (1 / n_samples) * np.dot(X.T, (y_pred - y))
            db = (1 / n_samples) * np.sum(y_pred - y)

            # Update parameters
            self.weights -= self.learning_rate * dw
            self.bias -= self.learning_rate * db

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions using the trained model.

        Args:
            X: Features to make predictions on

        Returns:
            Predicted values
        """
        return np.dot(X, self.weights) + self.bias


class LogisticRegression:
    """A simple logistic regression implementation."""

    def __init__(self, learning_rate: float = 0.01, n_iterations: int = 1000):
        """
        Initialize a logistic regression model.

        Args:
            learning_rate: Learning rate for gradient descent
            n_iterations: Number of iterations for gradient descent
        """
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.weights = None
        self.bias = None

    def _sigmoid(self, z: np.ndarray) -> np.ndarray:
        """
        Compute the sigmoid function.

        Args:
            z: Input values

        Returns:
            Sigmoid of the input values
        """
        return 1 / (1 + np.exp(-z))

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Fit the logistic regression model to the training data.

        Args:
            X: Training features
            y: Training target values (binary)
        """
        n_samples, n_features = X.shape
        self.weights = np.zeros(n_features)
        self.bias = 0

        # Gradient descent
        for _ in range(self.n_iterations):
            # Linear combination
            linear_model = np.dot(X, self.weights) + self.bias
            # Apply sigmoid function
            y_pred = self._sigmoid(linear_model)

            # Compute gradients
            dw = (1 / n_samples) * np.dot(X.T, (y_pred - y))
            db = (1 / n_samples) * np.sum(y_pred - y)

            # Update parameters
            self.weights -= self.learning_rate * dw
            self.bias -= self.learning_rate * db

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions using the trained model.

        Args:
            X: Features to make predictions on

        Returns:
            Predicted class labels (0 or 1)
        """
        linear_model = np.dot(X, self.weights) + self.bias
        y_pred = self._sigmoid(linear_model)
        return np.round(y_pred).astype(int)


class KMeans:
    """A simple K-means clustering implementation."""

    def __init__(self, n_clusters: int = 3, max_iterations: int = 100):
        """
        Initialize a K-means clustering model.

        Args:
            n_clusters: Number of clusters
            max_iterations: Maximum number of iterations
        """
        self.n_clusters = n_clusters
        self.max_iterations = max_iterations
        self.centroids = None

    def fit(self, X: np.ndarray) -> None:
        """
        Fit the K-means clustering model to the data.

        Args:
            X: Data points
        """
        n_samples, n_features = X.shape

        # Initialize centroids randomly
        idx = np.random.choice(n_samples, self.n_clusters, replace=False)
        self.centroids = X[idx]

        # Iterate until convergence or max iterations
        for _ in range(self.max_iterations):
            # Assign clusters
            clusters = self._assign_clusters(X)

            # Update centroids
            old_centroids = self.centroids.copy()
            for i in range(self.n_clusters):
                cluster_points = X[clusters == i]
                if len(cluster_points) > 0:
                    self.centroids[i] = np.mean(cluster_points, axis=0)

            # Check for convergence
            if np.all(old_centroids == self.centroids):
                break

    def _assign_clusters(self, X: np.ndarray) -> np.ndarray:
        """
        Assign each data point to the nearest centroid.

        Args:
            X: Data points

        Returns:
            Cluster assignments for each data point
        """
        distances = np.sqrt(((X - self.centroids[:, np.newaxis])**2).sum(axis=2))
        return np.argmin(distances, axis=0)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict the cluster for each data point.

        Args:
            X: Data points

        Returns:
            Cluster assignments for each data point
        """
        return self._assign_clusters(X)


class DecisionTreeClassifier:
    """A simple decision tree classifier implementation."""

    def __init__(self, max_depth: int = None, min_samples_split: int = 2):
        """
        Initialize a decision tree classifier.

        Args:
            max_depth: Maximum depth of the tree
            min_samples_split: Minimum number of samples required to split a node
        """
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.tree = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Fit the decision tree classifier to the training data.

        Args:
            X: Training features
            y: Training target values
        """
        self.tree = self._grow_tree(X, y)

    def _grow_tree(self, X: np.ndarray, y: np.ndarray, depth: int = 0) -> dict:
        """
        Recursively grow the decision tree.

        Args:
            X: Training features
            y: Training target values
            depth: Current depth of the tree

        Returns:
            A dictionary representing the decision tree
        """
        n_samples, n_features = X.shape
        n_classes = len(np.unique(y))

        # Check stopping criteria
        if (self.max_depth is not None and depth >= self.max_depth) or \
           n_samples < self.min_samples_split or \
           n_classes == 1:
            leaf_value = self._most_common_label(y)
            return {"value": leaf_value}

        # Find the best split
        best_feature, best_threshold = self._best_split(X, y, n_features)

        # Split the data
        left_idx = X[:, best_feature] < best_threshold
        right_idx = ~left_idx

        # Grow the children
        left_tree = self._grow_tree(X[left_idx], y[left_idx], depth + 1)
        right_tree = self._grow_tree(X[right_idx], y[right_idx], depth + 1)

        return {
            "feature": best_feature,
            "threshold": best_threshold,
            "left": left_tree,
            "right": right_tree
        }

    def _best_split(self, X: np.ndarray, y: np.ndarray, n_features: int) -> Tuple[int, float]:
        """
        Find the best feature and threshold for splitting the data.

        Args:
            X: Training features
            y: Training target values
            n_features: Number of features

        Returns:
            A tuple (feature, threshold) representing the best split
        """
        best_gain = -float('inf')
        best_feature = 0
        best_threshold = 0

        for feature in range(n_features):
            thresholds = np.unique(X[:, feature])
            for threshold in thresholds:
                # Split the data
                left_idx = X[:, feature] < threshold
                right_idx = ~left_idx

                if len(y[left_idx]) == 0 or len(y[right_idx]) == 0:
                    continue

                # Compute information gain
                gain = self._information_gain(y, y[left_idx], y[right_idx])

                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature
                    best_threshold = threshold

        return best_feature, best_threshold

    def _information_gain(self, parent: np.ndarray, left: np.ndarray, right: np.ndarray) -> float:
        """
        Compute the information gain of a split.

        Args:
            parent: Parent node target values
            left: Left child node target values
            right: Right child node target values

        Returns:
            Information gain of the split
        """
        n_left = len(left)
        n_right = len(right)
        n_parent = len(parent)

        parent_entropy = self._entropy(parent)
        left_entropy = self._entropy(left)
        right_entropy = self._entropy(right)

        return parent_entropy - (n_left / n_parent) * left_entropy - (n_right / n_parent) * right_entropy

    def _entropy(self, y: np.ndarray) -> float:
        """
        Compute the entropy of a set of target values.

        Args:
            y: Target values

        Returns:
            Entropy of the target values
        """
        _, counts = np.unique(y, return_counts=True)
        probabilities = counts / len(y)
        return -np.sum(probabilities * np.log2(probabilities))

    def _most_common_label(self, y: np.ndarray) -> Any:
        """
        Find the most common label in a set of target values.

        Args:
            y: Target values

        Returns:
            Most common label
        """
        values, counts = np.unique(y, return_counts=True)
        return values[np.argmax(counts)]

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions using the trained model.

        Args:
            X: Features to make predictions on

        Returns:
            Predicted class labels
        """
        return np.array([self._traverse_tree(x, self.tree) for x in X])

    def _traverse_tree(self, x: np.ndarray, node: dict) -> Any:
        """
        Traverse the decision tree to make a prediction.

        Args:
            x: Feature vector
            node: Current node in the tree

        Returns:
            Predicted class label
        """
        if "value" in node:
            return node["value"]

        feature = node["feature"]
        threshold = node["threshold"]

        if x[feature] < threshold:
            return self._traverse_tree(x, node["left"])
        else:
            return self._traverse_tree(x, node["right"])


# -----------------------------------------------------------------------------
# SECTION 8: UTILITY FUNCTIONS
# -----------------------------------------------------------------------------

def timer(func: Callable) -> Callable:
    """
    A decorator that times the execution of a function.

    Args:
        func: Function to time

    Returns:
        Wrapped function that prints the execution time
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} executed in {end_time - start_time:.6f} seconds")
        return result
    return wrapper


def memoize(func: Callable) -> Callable:
    """
    A decorator that memoizes a function.

    Args:
        func: Function to memoize

    Returns:
        Memoized function
    """
    cache = {}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]

    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0) -> Callable:
    """
    A decorator that retries a function if it raises an exception.

    Args:
        max_attempts: Maximum number of attempts
        delay: Delay between attempts in seconds

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        raise e
                    time.sleep(delay)
        return wrapper
    return decorator


def flatten(nested_list: List) -> List:
    """
    Flatten a nested list.

    Args:
        nested_list: Nested list to flatten

    Returns:
        Flattened list
    """
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def chunk(lst: List, size: int) -> List[List]:
    """
    Split a list into chunks of a specified size.

    Args:
        lst: List to split
        size: Chunk size

    Returns:
        List of chunks
    """
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def deep_copy(obj: Any) -> Any:
    """
    Create a deep copy of an object.

    Args:
        obj: Object to copy

    Returns:
        Deep copy of the object
    """
    if isinstance(obj, list):
        return [deep_copy(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: deep_copy(value) for key, value in obj.items()}
    elif isinstance(obj, set):
        return {deep_copy(item) for item in obj}
    elif isinstance(obj, tuple):
        return tuple(deep_copy(item) for item in obj)
    else:
        return obj


def is_prime_optimized(n: int) -> bool:
    """
    Check if a number is prime using an optimized algorithm.

    Args:
        n: Number to check

    Returns:
        True if the number is prime, False otherwise
    """
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False

    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6

    return True


def generate_primes(n: int) -> List[int]:
    """
    Generate a list of prime numbers up to n.

    Args:
        n: Upper bound

    Returns:
        List of prime numbers up to n
    """
    return [i for i in range(2, n + 1) if is_prime_optimized(i)]


def is_anagram(s1: str, s2: str) -> bool:
    """
    Check if two strings are anagrams of each other.

    Args:
        s1: First string
        s2: Second string

    Returns:
        True if the strings are anagrams, False otherwise
    """
    return sorted(s1) == sorted(s2)


def is_palindrome_optimized(s: str) -> bool:
    """
    Check if a string is a palindrome using an optimized algorithm.

    Args:
        s: String to check

    Returns:
        True if the string is a palindrome, False otherwise
    """
    s = ''.join(c.lower() for c in s if c.isalnum())
    left, right = 0, len(s) - 1

    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1

    return True


if __name__ == "__main__":
    print("Welcome to the Insane Coding Gymnastics module!")
    print("This module contains a wide variety of advanced Python functions and algorithms.")
    print("Feel free to explore and use them in your projects.")

    # Example usage
    print("\nExample: Fibonacci sequence")
    print([fibonacci(i) for i in range(10)])

    print("\nExample: Prime numbers up to 20")
    print(sieve_of_eratosthenes(20))

    print("\nExample: GCD and LCM")
    a, b = 48, 18
    print(f"GCD of {a} and {b}: {gcd(a, b)}")
    print(f"LCM of {a} and {b}: {lcm(a, b)}")

    print("\nExample: Sorting algorithms")
    arr = [64, 34, 25, 12, 22, 11, 90]
    print(f"Original array: {arr}")
    print(f"Sorted array (bubble sort): {bubble_sort(arr)}")
    print(f"Sorted array (quick sort): {quick_sort(arr)}")

    print("\nExample: Binary search")
    sorted_arr = [11, 12, 22, 25, 34, 64, 90]
    target = 25
    index = binary_search(sorted_arr, target)
    print(f"Index of {target} in {sorted_arr}: {index}")

    print("\nExample: String matching")
    text = "ABABDABACDABABCABAB"
    pattern = "ABABCABAB"
    print(f"Occurrences of '{pattern}' in '{text}': {naive_string_matching(text, pattern)}")

    print("\nExample: Dynamic programming")
    print(f"Fibonacci(10) using DP: {fibonacci_dp(10)}")

    print("\nDone!")
