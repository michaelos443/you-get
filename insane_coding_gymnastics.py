#!/usr/bin/env python3
"""
Insane Coding Gymnastics - A collection of impressive Python functions
demonstrating advanced programming techniques, algorithms, and data structures.
"""

import asyncio
import functools
import hashlib
import heapq
import inspect
import itertools
import math
import multiprocessing
import numpy as np
import random
import re
import struct
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import (
    Any, Callable, Dict, Generator, Generic, Iterable, List, Optional,
    Set, Tuple, Type, TypeVar, Union, Protocol, runtime_checkable
)


# Type variables for generic programming
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


# ============================================================================
# ADVANCED DATA STRUCTURES
# ============================================================================

class TrieNode:
    """Node for Trie data structure"""
    def __init__(self):
        self.children: Dict[str, TrieNode] = {}
        self.is_end_of_word: bool = False
        self.frequency: int = 0


class Trie:
    """Advanced Trie implementation with frequency tracking"""
    
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word: str) -> None:
        """Insert a word into the trie"""
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        node.frequency += 1
    
    def search(self, word: str) -> bool:
        """Search for a word in the trie"""
        node = self._find_node(word)
        return node is not None and node.is_end_of_word
    
    def starts_with(self, prefix: str) -> bool:
        """Check if any word starts with given prefix"""
        return self._find_node(prefix) is not None
    
    def _find_node(self, prefix: str) -> Optional[TrieNode]:
        """Find node corresponding to prefix"""
        node = self.root
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        return node
    
    def auto_complete(self, prefix: str, max_suggestions: int = 5) -> List[str]:
        """Get autocomplete suggestions for a prefix"""
        node = self._find_node(prefix)
        if not node:
            return []
        
        suggestions = []
        self._dfs_words(node, prefix, suggestions, max_suggestions)
        return sorted(suggestions, key=lambda x: x[1], reverse=True)[:max_suggestions]
    
    def _dfs_words(self, node: TrieNode, current_word: str, 
                   suggestions: List[Tuple[str, int]], max_suggestions: int) -> None:
        """DFS to find all words from a node"""
        if node.is_end_of_word:
            suggestions.append((current_word, node.frequency))
        
        if len(suggestions) >= max_suggestions * 2:  # Early termination
            return
        
        for char, child_node in node.children.items():
            self._dfs_words(child_node, current_word + char, suggestions, max_suggestions)


class SkipListNode(Generic[K, V]):
    """Node for Skip List data structure"""
    def __init__(self, key: K, value: V, level: int):
        self.key = key
        self.value = value
        self.forward: List[Optional['SkipListNode[K, V]']] = [None] * (level + 1)


class SkipList(Generic[K, V]):
    """Probabilistic data structure for fast search, insertion, and deletion"""
    
    def __init__(self, max_level: int = 16, p: float = 0.5):
        self.max_level = max_level
        self.p = p
        self.level = 0
        self.header = SkipListNode[K, V](None, None, max_level)
    
    def random_level(self) -> int:
        """Generate random level for new node"""
        level = 0
        while random.random() < self.p and level < self.max_level:
            level += 1
        return level
    
    def insert(self, key: K, value: V) -> None:
        """Insert key-value pair into skip list"""
        update = [None] * (self.max_level + 1)
        current = self.header
        
        # Find position to insert
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
            update[i] = current
        
        current = current.forward[0]
        
        # Update value if key exists
        if current and current.key == key:
            current.value = value
            return
        
        # Insert new node
        new_level = self.random_level()
        if new_level > self.level:
            for i in range(self.level + 1, new_level + 1):
                update[i] = self.header
            self.level = new_level
        
        new_node = SkipListNode(key, value, new_level)
        for i in range(new_level + 1):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node
    
    def search(self, key: K) -> Optional[V]:
        """Search for key in skip list"""
        current = self.header
        
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
        
        current = current.forward[0]
        if current and current.key == key:
            return current.value
        return None
    
    def delete(self, key: K) -> bool:
        """Delete key from skip list"""
        update = [None] * (self.max_level + 1)
        current = self.header
        
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
            update[i] = current
        
        current = current.forward[0]
        
        if current and current.key == key:
            for i in range(self.level + 1):
                if update[i].forward[i] != current:
                    break
                update[i].forward[i] = current.forward[i]
            
            while self.level > 0 and self.header.forward[self.level] is None:
                self.level -= 1
            return True
        
        return False


class BPlusTreeNode:
    """Node for B+ Tree implementation"""
    def __init__(self, is_leaf: bool = False, order: int = 3):
        self.is_leaf = is_leaf
        self.keys: List[Any] = []
        self.values: List[Any] = []
        self.children: List['BPlusTreeNode'] = []
        self.next: Optional['BPlusTreeNode'] = None  # For leaf nodes
        self.order = order
    
    @property
    def is_full(self) -> bool:
        return len(self.keys) >= self.order - 1


class BPlusTree:
    """B+ Tree implementation for efficient range queries"""
    
    def __init__(self, order: int = 3):
        self.root = BPlusTreeNode(is_leaf=True, order=order)
        self.order = order
    
    def insert(self, key: Any, value: Any) -> None:
        """Insert key-value pair into B+ tree"""
        if self.root.is_full:
            new_root = BPlusTreeNode(order=self.order)
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root
        
        self._insert_non_full(self.root, key, value)
    
    def _insert_non_full(self, node: BPlusTreeNode, key: Any, value: Any) -> None:
        """Insert into a non-full node"""
        i = len(node.keys) - 1
        
        if node.is_leaf:
            node.keys.append(None)
            node.values.append(None)
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                node.values[i + 1] = node.values[i]
                i -= 1
            node.keys[i + 1] = key
            node.values[i + 1] = value
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            
            if node.children[i].is_full:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            
            self._insert_non_full(node.children[i], key, value)
    
    def _split_child(self, parent: BPlusTreeNode, index: int) -> None:
        """Split a full child node"""
        order = self.order
        child = parent.children[index]
        new_child = BPlusTreeNode(is_leaf=child.is_leaf, order=order)
        
        mid_index = order // 2
        
        if child.is_leaf:
            new_child.keys = child.keys[mid_index:]
            new_child.values = child.values[mid_index:]
            child.keys = child.keys[:mid_index]
            child.values = child.values[:mid_index]
            
            new_child.next = child.next
            child.next = new_child
            
            parent.keys.insert(index, new_child.keys[0])
        else:
            new_child.keys = child.keys[mid_index + 1:]
            child.keys = child.keys[:mid_index]
            
            new_child.children = child.children[mid_index + 1:]
            child.children = child.children[:mid_index + 1]
            
            parent.keys.insert(index, child.keys[mid_index])
        
        parent.children.insert(index + 1, new_child)
    
    def search(self, key: Any) -> Optional[Any]:
        """Search for a key in the B+ tree"""
        return self._search_helper(self.root, key)
    
    def _search_helper(self, node: BPlusTreeNode, key: Any) -> Optional[Any]:
        """Helper function for searching"""
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        
        if node.is_leaf:
            if i < len(node.keys) and node.keys[i] == key:
                return node.values[i]
            return None
        else:
            if i < len(node.keys) and node.keys[i] == key:
                i += 1
            return self._search_helper(node.children[i], key)
    
    def range_query(self, start_key: Any, end_key: Any) -> List[Tuple[Any, Any]]:
        """Perform range query on B+ tree"""
        result = []
        leaf = self._find_leaf(self.root, start_key)
        
        while leaf:
            for i, key in enumerate(leaf.keys):
                if start_key <= key <= end_key:
                    result.append((key, leaf.values[i]))
                elif key > end_key:
                    return result
            leaf = leaf.next
        
        return result
    
    def _find_leaf(self, node: BPlusTreeNode, key: Any) -> BPlusTreeNode:
        """Find leaf node that should contain the key"""
        if node.is_leaf:
            return node
        
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        
        return self._find_leaf(node.children[i], key)


class FenwickTree:
    """Binary Indexed Tree for efficient range sum queries"""
    
    def __init__(self, n: int):
        self.n = n
        self.tree = [0] * (n + 1)
    
    def update(self, i: int, delta: int) -> None:
        """Add delta to element at index i"""
        i += 1  # 1-indexed
        while i <= self.n:
            self.tree[i] += delta
            i += i & (-i)
    
    def query(self, i: int) -> int:
        """Get sum of elements from 0 to i"""
        i += 1  # 1-indexed
        s = 0
        while i > 0:
            s += self.tree[i]
            i -= i & (-i)
        return s
    
    def range_query(self, left: int, right: int) -> int:
        """Get sum of elements from left to right"""
        return self.query(right) - (self.query(left - 1) if left > 0 else 0)


class SegmentTree:
    """Segment Tree for efficient range queries and updates"""
    
    def __init__(self, arr: List[int], func: Callable[[int, int], int] = min):
        self.n = len(arr)
        self.func = func
        self.tree = [0] * (4 * self.n)
        self.lazy = [0] * (4 * self.n)
        self._build(arr, 0, 0, self.n - 1)
    
    def _build(self, arr: List[int], node: int, start: int, end: int) -> None:
        """Build segment tree"""
        if start == end:
            self.tree[node] = arr[start]
        else:
            mid = (start + end) // 2
            self._build(arr, 2 * node + 1, start, mid)
            self._build(arr, 2 * node + 2, mid + 1, end)
            self.tree[node] = self.func(self.tree[2 * node + 1], self.tree[2 * node + 2])
    
    def _push(self, node: int, start: int, end: int) -> None:
        """Push lazy propagation"""
        if self.lazy[node] != 0:
            self.tree[node] += self.lazy[node]
            if start != end:
                self.lazy[2 * node + 1] += self.lazy[node]
                self.lazy[2 * node + 2] += self.lazy[node]
            self.lazy[node] = 0
    
    def update_range(self, left: int, right: int, val: int) -> None:
        """Update range [left, right] by adding val"""
        self._update_range(0, 0, self.n - 1, left, right, val)
    
    def _update_range(self, node: int, start: int, end: int, 
                      left: int, right: int, val: int) -> None:
        """Helper for range update"""
        self._push(node, start, end)
        
        if start > right or end < left:
            return
        
        if start >= left and end <= right:
            self.lazy[node] += val
            self._push(node, start, end)
            return
        
        mid = (start + end) // 2
        self._update_range(2 * node + 1, start, mid, left, right, val)
        self._update_range(2 * node + 2, mid + 1, end, left, right, val)
        
        self._push(2 * node + 1, start, mid)
        self._push(2 * node + 2, mid + 1, end)
        self.tree[node] = self.func(self.tree[2 * node + 1], self.tree[2 * node + 2])
    
    def query_range(self, left: int, right: int) -> int:
        """Query range [left, right]"""
        return self._query_range(0, 0, self.n - 1, left, right)
    
    def _query_range(self, node: int, start: int, end: int, 
                     left: int, right: int) -> int:
        """Helper for range query"""
        if start > right or end < left:
            return float('inf') if self.func == min else float('-inf')
        
        self._push(node, start, end)
        
        if start >= left and end <= right:
            return self.tree[node]
        
        mid = (start + end) // 2
        left_result = self._query_range(2 * node + 1, start, mid, left, right)
        right_result = self._query_range(2 * node + 2, mid + 1, end, left, right)
        
        return self.func(left_result, right_result)


# ============================================================================
# MACHINE LEARNING ALGORITHMS FROM SCRATCH
# ============================================================================

class NeuralNetwork:
    """Multi-layer perceptron implementation from scratch"""

    def __init__(self, layer_sizes: List[int], learning_rate: float = 0.01):
        self.layer_sizes = layer_sizes
        self.learning_rate = learning_rate
        self.weights = []
        self.biases = []

        # Initialize weights and biases
        for i in range(len(layer_sizes) - 1):
            w = np.random.randn(layer_sizes[i], layer_sizes[i + 1]) * 0.1
            b = np.zeros((1, layer_sizes[i + 1]))
            self.weights.append(w)
            self.biases.append(b)

    def sigmoid(self, x: 'np.ndarray') -> 'np.ndarray':
        """Sigmoid activation function"""
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

    def sigmoid_derivative(self, x: 'np.ndarray') -> 'np.ndarray':
        """Derivative of sigmoid function"""
        return x * (1 - x)

    def relu(self, x: 'np.ndarray') -> 'np.ndarray':
        """ReLU activation function"""
        return np.maximum(0, x)

    def relu_derivative(self, x: 'np.ndarray') -> 'np.ndarray':
        """Derivative of ReLU function"""
        return (x > 0).astype(float)

    def forward_propagation(self, X: 'np.ndarray') -> List['np.ndarray']:
        """Forward propagation through the network"""
        activations = [X]

        for i in range(len(self.weights)):
            z = np.dot(activations[-1], self.weights[i]) + self.biases[i]
            if i < len(self.weights) - 1:
                a = self.relu(z)
            else:
                a = self.sigmoid(z)
            activations.append(a)

        return activations

    def backward_propagation(self, X: 'np.ndarray', y: 'np.ndarray',
                           activations: List['np.ndarray']) -> None:
        """Backward propagation to update weights"""
        m = X.shape[0]

        # Calculate output layer error
        delta = activations[-1] - y

        # Backpropagate through layers
        for i in range(len(self.weights) - 1, -1, -1):
            # Calculate gradients
            dW = np.dot(activations[i].T, delta) / m
            db = np.sum(delta, axis=0, keepdims=True) / m

            # Update weights and biases
            self.weights[i] -= self.learning_rate * dW
            self.biases[i] -= self.learning_rate * db

            # Calculate error for previous layer
            if i > 0:
                delta = np.dot(delta, self.weights[i].T)
                if i < len(self.weights) - 1:
                    delta *= self.relu_derivative(activations[i])

    def train(self, X: 'np.ndarray', y: 'np.ndarray', epochs: int = 1000) -> List[float]:
        """Train the neural network"""
        losses = []

        for epoch in range(epochs):
            # Forward propagation
            activations = self.forward_propagation(X)

            # Calculate loss
            loss = np.mean((activations[-1] - y) ** 2)
            losses.append(loss)

            # Backward propagation
            self.backward_propagation(X, y, activations)

            if epoch % 100 == 0:
                print(f"Epoch {epoch}, Loss: {loss:.4f}")

        return losses

    def predict(self, X: 'np.ndarray') -> 'np.ndarray':
        """Make predictions"""
        activations = self.forward_propagation(X)
        return activations[-1]


class KMeans:
    """K-Means clustering implementation from scratch"""

    def __init__(self, n_clusters: int = 3, max_iters: int = 100, tol: float = 1e-4):
        self.n_clusters = n_clusters
        self.max_iters = max_iters
        self.tol = tol
        self.centroids = None
        self.labels = None

    def fit(self, X: 'np.ndarray') -> 'KMeans':
        """Fit K-Means to data"""
        n_samples, n_features = X.shape

        # Initialize centroids randomly
        idx = np.random.choice(n_samples, self.n_clusters, replace=False)
        self.centroids = X[idx]

        for _ in range(self.max_iters):
            # Assign points to nearest centroid
            distances = self._calculate_distances(X)
            new_labels = np.argmin(distances, axis=1)

            # Update centroids
            new_centroids = np.zeros_like(self.centroids)
            for k in range(self.n_clusters):
                cluster_points = X[new_labels == k]
                if len(cluster_points) > 0:
                    new_centroids[k] = cluster_points.mean(axis=0)
                else:
                    new_centroids[k] = self.centroids[k]

            # Check convergence
            if np.allclose(self.centroids, new_centroids, atol=self.tol):
                break

            self.centroids = new_centroids
            self.labels = new_labels

        return self

    def _calculate_distances(self, X: 'np.ndarray') -> 'np.ndarray':
        """Calculate distances from points to centroids"""
        distances = np.zeros((X.shape[0], self.n_clusters))
        for k in range(self.n_clusters):
            distances[:, k] = np.linalg.norm(X - self.centroids[k], axis=1)
        return distances

    def predict(self, X: 'np.ndarray') -> 'np.ndarray':
        """Predict cluster labels for new data"""
        distances = self._calculate_distances(X)
        return np.argmin(distances, axis=1)

    def fit_predict(self, X: 'np.ndarray') -> 'np.ndarray':
        """Fit and return labels"""
        self.fit(X)
        return self.labels


class DecisionTreeNode:
    """Node for decision tree"""
    def __init__(self):
        self.feature = None
        self.threshold = None
        self.left = None
        self.right = None
        self.value = None
        self.is_leaf = False


class DecisionTree:
    """Decision tree implementation for classification"""

    def __init__(self, max_depth: int = 10, min_samples_split: int = 2):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.root = None

    def fit(self, X: 'np.ndarray', y: 'np.ndarray') -> 'DecisionTree':
        """Fit decision tree to data"""
        self.root = self._build_tree(X, y, depth=0)
        return self

    def _build_tree(self, X: 'np.ndarray', y: 'np.ndarray', depth: int) -> DecisionTreeNode:
        """Recursively build decision tree"""
        n_samples, n_features = X.shape
        n_classes = len(np.unique(y))

        # Create leaf node if stopping criteria met
        if (depth >= self.max_depth or n_samples < self.min_samples_split or
            n_classes == 1):
            node = DecisionTreeNode()
            node.is_leaf = True
            node.value = self._most_common_label(y)
            return node

        # Find best split
        best_feature, best_threshold = self._find_best_split(X, y)

        if best_feature is None:
            node = DecisionTreeNode()
            node.is_leaf = True
            node.value = self._most_common_label(y)
            return node

        # Create internal node
        node = DecisionTreeNode()
        node.feature = best_feature
        node.threshold = best_threshold

        # Split data
        left_idx = X[:, best_feature] <= best_threshold
        right_idx = ~left_idx

        # Recursively build subtrees
        node.left = self._build_tree(X[left_idx], y[left_idx], depth + 1)
        node.right = self._build_tree(X[right_idx], y[right_idx], depth + 1)

        return node

    def _find_best_split(self, X: 'np.ndarray', y: 'np.ndarray') -> Tuple[Optional[int], Optional[float]]:
        """Find best feature and threshold to split on"""
        n_samples, n_features = X.shape
        best_gini = float('inf')
        best_feature = None
        best_threshold = None

        for feature in range(n_features):
            thresholds = np.unique(X[:, feature])

            for threshold in thresholds:
                left_idx = X[:, feature] <= threshold
                right_idx = ~left_idx

                if np.sum(left_idx) == 0 or np.sum(right_idx) == 0:
                    continue

                # Calculate Gini impurity
                gini = self._calculate_gini(y[left_idx], y[right_idx])

                if gini < best_gini:
                    best_gini = gini
                    best_feature = feature
                    best_threshold = threshold

        return best_feature, best_threshold

    def _calculate_gini(self, left_y: 'np.ndarray', right_y: 'np.ndarray') -> float:
        """Calculate weighted Gini impurity"""
        n_left = len(left_y)
        n_right = len(right_y)
        n_total = n_left + n_right

        gini_left = self._gini_impurity(left_y)
        gini_right = self._gini_impurity(right_y)

        weighted_gini = (n_left / n_total) * gini_left + (n_right / n_total) * gini_right
        return weighted_gini

    def _gini_impurity(self, y: 'np.ndarray') -> float:
        """Calculate Gini impurity for a set of labels"""
        _, counts = np.unique(y, return_counts=True)
        probabilities = counts / len(y)
        gini = 1 - np.sum(probabilities ** 2)
        return gini

    def _most_common_label(self, y: 'np.ndarray') -> int:
        """Get most common label"""
        values, counts = np.unique(y, return_counts=True)
        return values[np.argmax(counts)]

    def predict(self, X: 'np.ndarray') -> 'np.ndarray':
        """Make predictions"""
        predictions = []
        for sample in X:
            predictions.append(self._predict_sample(sample, self.root))
        return np.array(predictions)

    def _predict_sample(self, sample: 'np.ndarray', node: DecisionTreeNode) -> int:
        """Predict single sample"""
        if node.is_leaf:
            return node.value

        if sample[node.feature] <= node.threshold:
            return self._predict_sample(sample, node.left)
        else:
            return self._predict_sample(sample, node.right)


# ============================================================================
# CRYPTOGRAPHIC FUNCTIONS
# ============================================================================

class RSA:
    """Simple RSA implementation for educational purposes"""

    def __init__(self, key_size: int = 1024):
        self.key_size = key_size
        self.public_key = None
        self.private_key = None

    def generate_prime(self, bits: int) -> int:
        """Generate a prime number with specified bit length"""
        while True:
            num = random.getrandbits(bits)
            if self.is_prime(num):
                return num

    def is_prime(self, n: int, k: int = 5) -> bool:
        """Miller-Rabin primality test"""
        if n < 2:
            return False
        if n == 2 or n == 3:
            return True
        if n % 2 == 0:
            return False

        # Write n-1 as 2^r * d
        r, d = 0, n - 1
        while d % 2 == 0:
            r += 1
            d //= 2

        # Witness loop
        for _ in range(k):
            a = random.randrange(2, n - 1)
            x = pow(a, d, n)

            if x == 1 or x == n - 1:
                continue

            for _ in range(r - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False

        return True

    def gcd(self, a: int, b: int) -> int:
        """Euclidean algorithm for GCD"""
        while b:
            a, b = b, a % b
        return a

    def mod_inverse(self, a: int, m: int) -> int:
        """Extended Euclidean algorithm for modular inverse"""
        if self.gcd(a, m) != 1:
            raise ValueError("Modular inverse does not exist")

        # Extended Euclidean algorithm
        old_r, r = a, m
        old_s, s = 1, 0

        while r != 0:
            quotient = old_r // r
            old_r, r = r, old_r - quotient * r
            old_s, s = s, old_s - quotient * s

        return old_s % m

    def generate_keypair(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """Generate RSA public and private key pair"""
        # Generate two large primes
        p = self.generate_prime(self.key_size // 2)
        q = self.generate_prime(self.key_size // 2)

        n = p * q
        phi = (p - 1) * (q - 1)

        # Choose e (commonly 65537)
        e = 65537
        while self.gcd(e, phi) != 1:
            e += 2

        # Calculate d (private exponent)
        d = self.mod_inverse(e, phi)

        self.public_key = (n, e)
        self.private_key = (n, d)

        return self.public_key, self.private_key

    def encrypt(self, message: int, public_key: Tuple[int, int]) -> int:
        """Encrypt message using public key"""
        n, e = public_key
        if message >= n:
            raise ValueError("Message too large for key size")
        return pow(message, e, n)

    def decrypt(self, ciphertext: int, private_key: Tuple[int, int]) -> int:
        """Decrypt ciphertext using private key"""
        n, d = private_key
        return pow(ciphertext, d, n)

    def sign(self, message: int, private_key: Tuple[int, int]) -> int:
        """Sign message using private key"""
        return self.decrypt(message, private_key)

    def verify(self, message: int, signature: int, public_key: Tuple[int, int]) -> bool:
        """Verify signature using public key"""
        return self.encrypt(signature, public_key) == message


class AES:
    """Simplified AES implementation for educational purposes"""

    # AES S-box
    S_BOX = [
        0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
        0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
        0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
        0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
        0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
        0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
        0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
        0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
        0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
        0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
        0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
        0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
        0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
        0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
        0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
        0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16
    ]

    def __init__(self, key: bytes):
        if len(key) not in [16, 24, 32]:
            raise ValueError("Key must be 16, 24, or 32 bytes")
        self.key = key
        self.rounds = {16: 10, 24: 12, 32: 14}[len(key)]
        self.round_keys = self._key_expansion()

    def _key_expansion(self) -> List[List[int]]:
        """Expand the key for all rounds"""
        key_words = []
        for i in range(0, len(self.key), 4):
            key_words.append(list(self.key[i:i+4]))

        # Simplified key expansion (not complete AES)
        for i in range(len(key_words), 4 * (self.rounds + 1)):
            temp = key_words[i - 1][:]
            if i % len(key_words) == 0:
                # RotWord and SubWord
                temp = temp[1:] + temp[:1]
                temp = [self.S_BOX[b] for b in temp]
                # XOR with Rcon
                temp[0] ^= 1 << ((i // len(key_words) - 1) % 8)

            key_words.append([a ^ b for a, b in zip(key_words[i - len(key_words)], temp)])

        # Group into round keys
        round_keys = []
        for i in range(0, len(key_words), 4):
            round_keys.append(key_words[i:i+4])

        return round_keys

    def _sub_bytes(self, state: List[List[int]]) -> None:
        """SubBytes transformation"""
        for i in range(4):
            for j in range(4):
                state[i][j] = self.S_BOX[state[i][j]]

    def _shift_rows(self, state: List[List[int]]) -> None:
        """ShiftRows transformation"""
        for i in range(1, 4):
            state[i] = state[i][i:] + state[i][:i]

    def _mix_columns(self, state: List[List[int]]) -> None:
        """MixColumns transformation (simplified)"""
        for j in range(4):
            col = [state[i][j] for i in range(4)]
            state[0][j] = self._gmul(2, col[0]) ^ self._gmul(3, col[1]) ^ col[2] ^ col[3]
            state[1][j] = col[0] ^ self._gmul(2, col[1]) ^ self._gmul(3, col[2]) ^ col[3]
            state[2][j] = col[0] ^ col[1] ^ self._gmul(2, col[2]) ^ self._gmul(3, col[3])
            state[3][j] = self._gmul(3, col[0]) ^ col[1] ^ col[2] ^ self._gmul(2, col[3])

    def _gmul(self, a: int, b: int) -> int:
        """Galois field multiplication"""
        p = 0
        for _ in range(8):
            if b & 1:
                p ^= a
            hi_bit = a & 0x80
            a <<= 1
            if hi_bit:
                a ^= 0x1b
            b >>= 1
        return p & 0xff

    def encrypt_block(self, plaintext: bytes) -> bytes:
        """Encrypt a single 16-byte block"""
        if len(plaintext) != 16:
            raise ValueError("Block must be 16 bytes")

        # Convert to state array
        state = [[plaintext[i + 4*j] for j in range(4)] for i in range(4)]

        # Initial round key addition
        for i in range(4):
            for j in range(4):
                state[i][j] ^= self.round_keys[0][j][i]

        # Main rounds
        for round_num in range(1, self.rounds):
            self._sub_bytes(state)
            self._shift_rows(state)
            self._mix_columns(state)

            # Add round key
            for i in range(4):
                for j in range(4):
                    state[i][j] ^= self.round_keys[round_num][j][i]

        # Final round (no MixColumns)
        self._sub_bytes(state)
        self._shift_rows(state)

        # Add final round key
        for i in range(4):
            for j in range(4):
                state[i][j] ^= self.round_keys[self.rounds][j][i]

        # Convert state to bytes
        ciphertext = bytes([state[i][j] for j in range(4) for i in range(4)])
        return ciphertext


class SHA256:
    """SHA-256 implementation from scratch"""

    def __init__(self):
        # Initial hash values (first 32 bits of fractional parts of square roots of first 8 primes)
        self.h = [
            0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
            0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
        ]

        # Constants (first 32 bits of fractional parts of cube roots of first 64 primes)
        self.k = [
            0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
            0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
            0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
            0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
            0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
            0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
            0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
            0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
        ]

    def _rotr(self, n: int, b: int) -> int:
        """Right rotate n by b bits"""
        return ((n >> b) | (n << (32 - b))) & 0xffffffff

    def _ch(self, x: int, y: int, z: int) -> int:
        """Choice function"""
        return (x & y) ^ (~x & z)

    def _maj(self, x: int, y: int, z: int) -> int:
        """Majority function"""
        return (x & y) ^ (x & z) ^ (y & z)

    def _sigma0(self, x: int) -> int:
        """Sigma0 function"""
        return self._rotr(x, 2) ^ self._rotr(x, 13) ^ self._rotr(x, 22)

    def _sigma1(self, x: int) -> int:
        """Sigma1 function"""
        return self._rotr(x, 6) ^ self._rotr(x, 11) ^ self._rotr(x, 25)

    def _gamma0(self, x: int) -> int:
        """Gamma0 function"""
        return self._rotr(x, 7) ^ self._rotr(x, 18) ^ (x >> 3)

    def _gamma1(self, x: int) -> int:
        """Gamma1 function"""
        return self._rotr(x, 17) ^ self._rotr(x, 19) ^ (x >> 10)

    def _pad_message(self, message: bytes) -> bytes:
        """Pad message to multiple of 512 bits"""
        msg_len = len(message)
        message += b'\x80'
        message += b'\x00' * ((55 - msg_len) % 64)
        message += struct.pack('>Q', msg_len * 8)
        return message

    def _process_block(self, block: bytes) -> None:
        """Process a single 512-bit block"""
        # Break block into 16 32-bit words
        w = list(struct.unpack('>16I', block))

        # Extend to 64 words
        for i in range(16, 64):
            w.append((self._gamma1(w[i-2]) + w[i-7] + self._gamma0(w[i-15]) + w[i-16]) & 0xffffffff)

        # Initialize working variables
        a, b, c, d, e, f, g, h = self.h

        # Main loop
        for i in range(64):
            t1 = (h + self._sigma1(e) + self._ch(e, f, g) + self.k[i] + w[i]) & 0xffffffff
            t2 = (self._sigma0(a) + self._maj(a, b, c)) & 0xffffffff
            h = g
            g = f
            f = e
            e = (d + t1) & 0xffffffff
            d = c
            c = b
            b = a
            a = (t1 + t2) & 0xffffffff

        # Update hash values
        self.h[0] = (self.h[0] + a) & 0xffffffff
        self.h[1] = (self.h[1] + b) & 0xffffffff
        self.h[2] = (self.h[2] + c) & 0xffffffff
        self.h[3] = (self.h[3] + d) & 0xffffffff
        self.h[4] = (self.h[4] + e) & 0xffffffff
        self.h[5] = (self.h[5] + f) & 0xffffffff
        self.h[6] = (self.h[6] + g) & 0xffffffff
        self.h[7] = (self.h[7] + h) & 0xffffffff

    def hash(self, message: bytes) -> bytes:
        """Compute SHA-256 hash of message"""
        # Reset hash values
        self.h = [
            0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
            0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
        ]

        # Pad message
        padded = self._pad_message(message)

        # Process each 512-bit block
        for i in range(0, len(padded), 64):
            self._process_block(padded[i:i+64])

        # Return final hash
        return struct.pack('>8I', *self.h)


# ============================================================================
# ADVANCED MATHEMATICAL COMPUTATIONS
# ============================================================================

class ComplexNumber:
    """Complex number implementation with advanced operations"""

    def __init__(self, real: float, imag: float = 0):
        self.real = real
        self.imag = imag

    def __repr__(self) -> str:
        if self.imag >= 0:
            return f"{self.real} + {self.imag}i"
        else:
            return f"{self.real} - {-self.imag}i"

    def __add__(self, other: 'ComplexNumber') -> 'ComplexNumber':
        return ComplexNumber(self.real + other.real, self.imag + other.imag)

    def __sub__(self, other: 'ComplexNumber') -> 'ComplexNumber':
        return ComplexNumber(self.real - other.real, self.imag - other.imag)

    def __mul__(self, other: 'ComplexNumber') -> 'ComplexNumber':
        real = self.real * other.real - self.imag * other.imag
        imag = self.real * other.imag + self.imag * other.real
        return ComplexNumber(real, imag)

    def __truediv__(self, other: 'ComplexNumber') -> 'ComplexNumber':
        denominator = other.real ** 2 + other.imag ** 2
        real = (self.real * other.real + self.imag * other.imag) / denominator
        imag = (self.imag * other.real - self.real * other.imag) / denominator
        return ComplexNumber(real, imag)

    def conjugate(self) -> 'ComplexNumber':
        """Return complex conjugate"""
        return ComplexNumber(self.real, -self.imag)

    def magnitude(self) -> float:
        """Return magnitude (absolute value)"""
        return math.sqrt(self.real ** 2 + self.imag ** 2)

    def phase(self) -> float:
        """Return phase angle in radians"""
        return math.atan2(self.imag, self.real)

    def to_polar(self) -> Tuple[float, float]:
        """Convert to polar form (r, theta)"""
        return self.magnitude(), self.phase()

    @staticmethod
    def from_polar(r: float, theta: float) -> 'ComplexNumber':
        """Create complex number from polar form"""
        return ComplexNumber(r * math.cos(theta), r * math.sin(theta))

    def exp(self) -> 'ComplexNumber':
        """Complex exponential e^z"""
        exp_real = math.exp(self.real)
        return ComplexNumber(
            exp_real * math.cos(self.imag),
            exp_real * math.sin(self.imag)
        )

    def log(self) -> 'ComplexNumber':
        """Complex natural logarithm"""
        return ComplexNumber(math.log(self.magnitude()), self.phase())

    def pow(self, n: 'ComplexNumber') -> 'ComplexNumber':
        """Complex power z^n"""
        if self.real == 0 and self.imag == 0:
            return ComplexNumber(0, 0)
        log_z = self.log()
        return (log_z * n).exp()


class Matrix:
    """Matrix implementation with advanced operations"""

    def __init__(self, data: List[List[float]]):
        self.data = data
        self.rows = len(data)
        self.cols = len(data[0]) if data else 0

        # Validate rectangular matrix
        for row in data:
            if len(row) != self.cols:
                raise ValueError("All rows must have the same length")

    def __repr__(self) -> str:
        return '\n'.join([' '.join(f'{val:8.3f}' for val in row) for row in self.data])

    def __add__(self, other: 'Matrix') -> 'Matrix':
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError("Matrices must have same dimensions for addition")

        result = [[self.data[i][j] + other.data[i][j]
                  for j in range(self.cols)]
                 for i in range(self.rows)]
        return Matrix(result)

    def __sub__(self, other: 'Matrix') -> 'Matrix':
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError("Matrices must have same dimensions for subtraction")

        result = [[self.data[i][j] - other.data[i][j]
                  for j in range(self.cols)]
                 for i in range(self.rows)]
        return Matrix(result)

    def __mul__(self, other: Union['Matrix', float]) -> 'Matrix':
        if isinstance(other, (int, float)):
            # Scalar multiplication
            result = [[self.data[i][j] * other
                      for j in range(self.cols)]
                     for i in range(self.rows)]
            return Matrix(result)

        # Matrix multiplication
        if self.cols != other.rows:
            raise ValueError("Invalid dimensions for matrix multiplication")

        result = [[sum(self.data[i][k] * other.data[k][j]
                      for k in range(self.cols))
                  for j in range(other.cols)]
                 for i in range(self.rows)]
        return Matrix(result)

    def transpose(self) -> 'Matrix':
        """Return transpose of matrix"""
        result = [[self.data[i][j] for i in range(self.rows)]
                 for j in range(self.cols)]
        return Matrix(result)

    def determinant(self) -> float:
        """Calculate determinant using LU decomposition"""
        if self.rows != self.cols:
            raise ValueError("Determinant only defined for square matrices")

        if self.rows == 1:
            return self.data[0][0]

        if self.rows == 2:
            return self.data[0][0] * self.data[1][1] - self.data[0][1] * self.data[1][0]

        # LU decomposition
        L, U, swaps = self._lu_decomposition()

        # Determinant is product of diagonal elements of U
        det = 1.0
        for i in range(self.rows):
            det *= U.data[i][i]

        # Account for row swaps
        return det * (-1) ** swaps

    def _lu_decomposition(self) -> Tuple['Matrix', 'Matrix', int]:
        """Perform LU decomposition with partial pivoting"""
        n = self.rows
        L = [[0.0] * n for _ in range(n)]
        U = [row[:] for row in self.data]  # Copy of matrix
        swaps = 0

        for i in range(n):
            # Partial pivoting
            max_row = i
            for k in range(i + 1, n):
                if abs(U[k][i]) > abs(U[max_row][i]):
                    max_row = k

            if max_row != i:
                U[i], U[max_row] = U[max_row], U[i]
                swaps += 1
                # Swap L rows (only the computed part)
                for j in range(i):
                    L[i][j], L[max_row][j] = L[max_row][j], L[i][j]

            L[i][i] = 1.0

            for j in range(i + 1, n):
                if U[i][i] == 0:
                    raise ValueError("Matrix is singular")
                L[j][i] = U[j][i] / U[i][i]
                for k in range(i + 1, n):
                    U[j][k] -= L[j][i] * U[i][k]
                U[j][i] = 0

        return Matrix(L), Matrix(U), swaps

    def inverse(self) -> 'Matrix':
        """Calculate matrix inverse using Gauss-Jordan elimination"""
        if self.rows != self.cols:
            raise ValueError("Inverse only defined for square matrices")

        n = self.rows
        # Create augmented matrix [A | I]
        augmented = [row[:] + [1.0 if i == j else 0.0 for j in range(n)]
                    for i, row in enumerate(self.data)]

        # Forward elimination
        for i in range(n):
            # Find pivot
            max_row = i
            for k in range(i + 1, n):
                if abs(augmented[k][i]) > abs(augmented[max_row][i]):
                    max_row = k

            augmented[i], augmented[max_row] = augmented[max_row], augmented[i]

            if augmented[i][i] == 0:
                raise ValueError("Matrix is singular")

            # Scale pivot row
            pivot = augmented[i][i]
            for j in range(2 * n):
                augmented[i][j] /= pivot

            # Eliminate column
            for k in range(n):
                if k != i:
                    factor = augmented[k][i]
                    for j in range(2 * n):
                        augmented[k][j] -= factor * augmented[i][j]

        # Extract inverse from augmented matrix
        inverse = [[augmented[i][j + n] for j in range(n)] for i in range(n)]
        return Matrix(inverse)

    def eigenvalues(self, max_iterations: int = 100, tolerance: float = 1e-10) -> List[float]:
        """Calculate eigenvalues using QR algorithm"""
        if self.rows != self.cols:
            raise ValueError("Eigenvalues only defined for square matrices")

        A = Matrix([row[:] for row in self.data])

        for _ in range(max_iterations):
            Q, R = self._qr_decomposition(A)
            A_new = R * Q

            # Check convergence
            if self._is_upper_triangular(A_new, tolerance):
                break

            A = A_new

        # Eigenvalues are diagonal elements
        return [A.data[i][i] for i in range(self.rows)]

    def _qr_decomposition(self, A: 'Matrix') -> Tuple['Matrix', 'Matrix']:
        """QR decomposition using Gram-Schmidt process"""
        n = A.rows
        Q = [[0.0] * n for _ in range(n)]
        R = [[0.0] * n for _ in range(n)]

        for j in range(n):
            # Copy column j of A
            v = [A.data[i][j] for i in range(n)]

            # Orthogonalize against previous columns
            for i in range(j):
                R[i][j] = sum(Q[k][i] * A.data[k][j] for k in range(n))
                for k in range(n):
                    v[k] -= R[i][j] * Q[k][i]

            # Normalize
            R[j][j] = math.sqrt(sum(v[k] ** 2 for k in range(n)))
            if R[j][j] > 0:
                for k in range(n):
                    Q[k][j] = v[k] / R[j][j]

        return Matrix([[Q[i][j] for j in range(n)] for i in range(n)]), Matrix(R)

    def _is_upper_triangular(self, A: 'Matrix', tolerance: float) -> bool:
        """Check if matrix is upper triangular within tolerance"""
        for i in range(1, A.rows):
            for j in range(i):
                if abs(A.data[i][j]) > tolerance:
                    return False
        return True

    @staticmethod
    def identity(n: int) -> 'Matrix':
        """Create n×n identity matrix"""
        data = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        return Matrix(data)

    @staticmethod
    def zeros(rows: int, cols: int) -> 'Matrix':
        """Create matrix of zeros"""
        return Matrix([[0.0] * cols for _ in range(rows)])

    @staticmethod
    def random(rows: int, cols: int, min_val: float = 0, max_val: float = 1) -> 'Matrix':
        """Create matrix with random values"""
        data = [[random.uniform(min_val, max_val) for _ in range(cols)]
                for _ in range(rows)]
        return Matrix(data)


class FFT:
    """Fast Fourier Transform implementation"""

    @staticmethod
    def fft(x: List[complex]) -> List[complex]:
        """Compute FFT of input signal"""
        n = len(x)

        # Base case
        if n <= 1:
            return x

        # Ensure n is power of 2
        if n & (n - 1) != 0:
            raise ValueError("Input length must be a power of 2")

        # Divide
        even = FFT.fft([x[i] for i in range(0, n, 2)])
        odd = FFT.fft([x[i] for i in range(1, n, 2)])

        # Conquer
        t = []
        for k in range(n // 2):
            w = complex(math.cos(-2 * math.pi * k / n),
                       math.sin(-2 * math.pi * k / n))
            t.append(even[k] + w * odd[k])

        for k in range(n // 2):
            w = complex(math.cos(-2 * math.pi * k / n),
                       math.sin(-2 * math.pi * k / n))
            t.append(even[k] - w * odd[k])

        return t

    @staticmethod
    def ifft(x: List[complex]) -> List[complex]:
        """Compute inverse FFT"""
        n = len(x)

        # Conjugate input
        x_conj = [complex(val.real, -val.imag) for val in x]

        # Apply FFT
        result = FFT.fft(x_conj)

        # Conjugate output and scale
        return [complex(val.real / n, -val.imag / n) for val in result]

    @staticmethod
    def convolve(a: List[float], b: List[float]) -> List[float]:
        """Compute convolution using FFT"""
        # Pad to next power of 2
        n = 1
        while n < len(a) + len(b) - 1:
            n *= 2

        # Pad inputs
        a_padded = a + [0] * (n - len(a))
        b_padded = b + [0] * (n - len(b))

        # Convert to complex
        a_complex = [complex(val, 0) for val in a_padded]
        b_complex = [complex(val, 0) for val in b_padded]

        # FFT
        a_fft = FFT.fft(a_complex)
        b_fft = FFT.fft(b_complex)

        # Multiply in frequency domain
        product = [a_fft[i] * b_fft[i] for i in range(n)]

        # Inverse FFT
        result = FFT.ifft(product)

        # Extract real part and trim
        return [val.real for val in result[:len(a) + len(b) - 1]]


# ============================================================================
# GRAPH ALGORITHMS
# ============================================================================

class Graph:
    """Graph implementation with various algorithms"""

    def __init__(self, directed: bool = False):
        self.adjacency_list: Dict[Any, List[Tuple[Any, float]]] = defaultdict(list)
        self.directed = directed
        self.vertices: Set[Any] = set()

    def add_edge(self, u: Any, v: Any, weight: float = 1.0) -> None:
        """Add edge to graph"""
        self.adjacency_list[u].append((v, weight))
        self.vertices.add(u)
        self.vertices.add(v)

        if not self.directed:
            self.adjacency_list[v].append((u, weight))

    def dijkstra(self, start: Any) -> Dict[Any, float]:
        """Dijkstra's shortest path algorithm"""
        distances = {vertex: float('inf') for vertex in self.vertices}
        distances[start] = 0

        # Priority queue: (distance, vertex)
        pq = [(0, start)]
        visited = set()

        while pq:
            current_dist, u = heapq.heappop(pq)

            if u in visited:
                continue

            visited.add(u)

            for v, weight in self.adjacency_list[u]:
                distance = current_dist + weight

                if distance < distances[v]:
                    distances[v] = distance
                    heapq.heappush(pq, (distance, v))

        return distances

    def bellman_ford(self, start: Any) -> Tuple[Dict[Any, float], bool]:
        """Bellman-Ford algorithm for shortest paths with negative edges"""
        distances = {vertex: float('inf') for vertex in self.vertices}
        distances[start] = 0

        # Relax edges V-1 times
        for _ in range(len(self.vertices) - 1):
            for u in self.adjacency_list:
                for v, weight in self.adjacency_list[u]:
                    if distances[u] != float('inf') and distances[u] + weight < distances[v]:
                        distances[v] = distances[u] + weight

        # Check for negative cycles
        for u in self.adjacency_list:
            for v, weight in self.adjacency_list[u]:
                if distances[u] != float('inf') and distances[u] + weight < distances[v]:
                    return distances, True  # Negative cycle exists

        return distances, False

    def floyd_warshall(self) -> Dict[Tuple[Any, Any], float]:
        """Floyd-Warshall algorithm for all-pairs shortest paths"""
        # Initialize distances
        distances = {}
        vertices_list = list(self.vertices)

        for i in vertices_list:
            for j in vertices_list:
                if i == j:
                    distances[(i, j)] = 0
                else:
                    distances[(i, j)] = float('inf')

        # Set edge weights
        for u in self.adjacency_list:
            for v, weight in self.adjacency_list[u]:
                distances[(u, v)] = weight

        # Dynamic programming
        for k in vertices_list:
            for i in vertices_list:
                for j in vertices_list:
                    distances[(i, j)] = min(
                        distances[(i, j)],
                        distances[(i, k)] + distances[(k, j)]
                    )

        return distances

    def prim_mst(self) -> List[Tuple[Any, Any, float]]:
        """Prim's algorithm for minimum spanning tree"""
        if not self.vertices:
            return []

        mst = []
        visited = set()

        # Start from arbitrary vertex
        start = next(iter(self.vertices))
        visited.add(start)

        # Priority queue: (weight, u, v)
        edges = []
        for v, weight in self.adjacency_list[start]:
            heapq.heappush(edges, (weight, start, v))

        while edges and len(visited) < len(self.vertices):
            weight, u, v = heapq.heappop(edges)

            if v in visited:
                continue

            visited.add(v)
            mst.append((u, v, weight))

            # Add new edges
            for next_v, next_weight in self.adjacency_list[v]:
                if next_v not in visited:
                    heapq.heappush(edges, (next_weight, v, next_v))

        return mst

    def kruskal_mst(self) -> List[Tuple[Any, Any, float]]:
        """Kruskal's algorithm for minimum spanning tree"""
        # Get all edges
        edges = []
        seen = set()

        for u in self.adjacency_list:
            for v, weight in self.adjacency_list[u]:
                if (u, v) not in seen and (v, u) not in seen:
                    edges.append((weight, u, v))
                    seen.add((u, v))

        # Sort edges by weight
        edges.sort()

        # Union-Find data structure
        parent = {v: v for v in self.vertices}
        rank = {v: 0 for v in self.vertices}

        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            px, py = find(x), find(y)
            if px == py:
                return False

            if rank[px] < rank[py]:
                parent[px] = py
            elif rank[px] > rank[py]:
                parent[py] = px
            else:
                parent[py] = px
                rank[px] += 1
            return True

        mst = []
        for weight, u, v in edges:
            if union(u, v):
                mst.append((u, v, weight))

        return mst

    def topological_sort(self) -> List[Any]:
        """Topological sort using DFS"""
        if not self.directed:
            raise ValueError("Topological sort only works on directed graphs")

        visited = set()
        stack = []

        def dfs(v):
            visited.add(v)
            for neighbor, _ in self.adjacency_list[v]:
                if neighbor not in visited:
                    dfs(neighbor)
            stack.append(v)

        for vertex in self.vertices:
            if vertex not in visited:
                dfs(vertex)

        return stack[::-1]

    def strongly_connected_components(self) -> List[Set[Any]]:
        """Find strongly connected components using Kosaraju's algorithm"""
        if not self.directed:
            raise ValueError("SCC only works on directed graphs")

        # First DFS to get finish times
        visited = set()
        finish_order = []

        def dfs1(v):
            visited.add(v)
            for neighbor, _ in self.adjacency_list[v]:
                if neighbor not in visited:
                    dfs1(neighbor)
            finish_order.append(v)

        for vertex in self.vertices:
            if vertex not in visited:
                dfs1(vertex)

        # Create transpose graph
        transpose = Graph(directed=True)
        for u in self.adjacency_list:
            for v, weight in self.adjacency_list[u]:
                transpose.add_edge(v, u, weight)

        # Second DFS on transpose graph
        visited.clear()
        sccs = []

        def dfs2(v, scc):
            visited.add(v)
            scc.add(v)
            for neighbor, _ in transpose.adjacency_list[v]:
                if neighbor not in visited:
                    dfs2(neighbor, scc)

        for vertex in reversed(finish_order):
            if vertex not in visited:
                scc = set()
                dfs2(vertex, scc)
                sccs.append(scc)

        return sccs

    def max_flow(self, source: Any, sink: Any) -> float:
        """Ford-Fulkerson algorithm for maximum flow"""
        # Create residual graph
        residual = defaultdict(lambda: defaultdict(float))

        for u in self.adjacency_list:
            for v, capacity in self.adjacency_list[u]:
                residual[u][v] = capacity

        def bfs_path(source, sink):
            """Find augmenting path using BFS"""
            parent = {source: None}
            visited = {source}
            queue = deque([source])

            while queue:
                u = queue.popleft()

                for v in residual[u]:
                    if v not in visited and residual[u][v] > 0:
                        visited.add(v)
                        parent[v] = u
                        queue.append(v)

                        if v == sink:
                            # Reconstruct path
                            path = []
                            current = sink
                            while current is not None:
                                path.append(current)
                                current = parent[current]
                            return path[::-1]

            return None

        max_flow_value = 0

        while True:
            path = bfs_path(source, sink)
            if not path:
                break

            # Find minimum capacity along path
            flow = float('inf')
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                flow = min(flow, residual[u][v])

            # Update residual capacities
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                residual[u][v] -= flow
                residual[v][u] += flow

            max_flow_value += flow

        return max_flow_value


# ============================================================================
# STRING PROCESSING AND PATTERN MATCHING
# ============================================================================

class StringAlgorithms:
    """Collection of advanced string algorithms"""

    @staticmethod
    def kmp_search(text: str, pattern: str) -> List[int]:
        """Knuth-Morris-Pratt string matching algorithm"""
        if not pattern:
            return []

        # Build failure function
        failure = [0] * len(pattern)
        j = 0

        for i in range(1, len(pattern)):
            while j > 0 and pattern[i] != pattern[j]:
                j = failure[j - 1]

            if pattern[i] == pattern[j]:
                j += 1

            failure[i] = j

        # Search for pattern
        matches = []
        j = 0

        for i in range(len(text)):
            while j > 0 and text[i] != pattern[j]:
                j = failure[j - 1]

            if text[i] == pattern[j]:
                j += 1

            if j == len(pattern):
                matches.append(i - len(pattern) + 1)
                j = failure[j - 1]

        return matches

    @staticmethod
    def rabin_karp_search(text: str, pattern: str, prime: int = 101) -> List[int]:
        """Rabin-Karp string matching with rolling hash"""
        if not pattern or len(pattern) > len(text):
            return []

        pattern_len = len(pattern)
        text_len = len(text)
        pattern_hash = 0
        text_hash = 0
        h = 1
        matches = []

        # Calculate h = pow(256, pattern_len - 1) % prime
        for _ in range(pattern_len - 1):
            h = (h * 256) % prime

        # Calculate initial hash values
        for i in range(pattern_len):
            pattern_hash = (256 * pattern_hash + ord(pattern[i])) % prime
            text_hash = (256 * text_hash + ord(text[i])) % prime

        # Slide pattern over text
        for i in range(text_len - pattern_len + 1):
            if pattern_hash == text_hash:
                # Check characters one by one
                if text[i:i + pattern_len] == pattern:
                    matches.append(i)

            # Calculate hash for next window
            if i < text_len - pattern_len:
                text_hash = (256 * (text_hash - ord(text[i]) * h) + ord(text[i + pattern_len])) % prime

                # Handle negative hash
                if text_hash < 0:
                    text_hash += prime

        return matches

    @staticmethod
    def z_algorithm(s: str) -> List[int]:
        """Z-algorithm for pattern matching preprocessing"""
        n = len(s)
        z = [0] * n
        z[0] = n

        left = right = 0

        for i in range(1, n):
            if i > right:
                left = right = i
                while right < n and s[right - left] == s[right]:
                    right += 1
                z[i] = right - left
                right -= 1
            else:
                k = i - left
                if z[k] < right - i + 1:
                    z[i] = z[k]
                else:
                    left = i
                    while right < n and s[right - left] == s[right]:
                        right += 1
                    z[i] = right - left
                    right -= 1

        return z

    @staticmethod
    def manacher_algorithm(s: str) -> str:
        """Find longest palindromic substring using Manacher's algorithm"""
        # Preprocess string
        processed = '#'.join('^{}$'.format(s))
        n = len(processed)
        p = [0] * n
        center = right = 0

        for i in range(1, n - 1):
            mirror = 2 * center - i

            if i < right:
                p[i] = min(right - i, p[mirror])

            # Expand around center
            while processed[i + p[i] + 1] == processed[i - p[i] - 1]:
                p[i] += 1

            # Update center and right
            if i + p[i] > right:
                center, right = i, i + p[i]

        # Find longest palindrome
        max_len = 0
        center_index = 0

        for i in range(1, n - 1):
            if p[i] > max_len:
                max_len = p[i]
                center_index = i

        start = (center_index - max_len) // 2
        return s[start:start + max_len]

    @staticmethod
    def suffix_array(s: str) -> List[int]:
        """Build suffix array using O(n log n) algorithm"""
        n = len(s)
        suffixes = [(s[i:], i) for i in range(n)]
        suffixes.sort()
        return [suffix[1] for suffix in suffixes]

    @staticmethod
    def lcp_array(s: str, suffix_array: List[int]) -> List[int]:
        """Build LCP (Longest Common Prefix) array"""
        n = len(s)
        rank = [0] * n
        lcp = [0] * n

        # Build rank array
        for i in range(n):
            rank[suffix_array[i]] = i

        h = 0
        for i in range(n):
            if rank[i] > 0:
                j = suffix_array[rank[i] - 1]
                while i + h < n and j + h < n and s[i + h] == s[j + h]:
                    h += 1
                lcp[rank[i]] = h
                if h > 0:
                    h -= 1

        return lcp


# ============================================================================
# CONCURRENT PROGRAMMING UTILITIES
# ============================================================================

class ThreadSafeQueue(Generic[T]):
    """Thread-safe queue implementation"""

    def __init__(self, maxsize: int = 0):
        self.queue: deque[T] = deque()
        self.maxsize = maxsize
        self.mutex = threading.Lock()
        self.not_empty = threading.Condition(self.mutex)
        self.not_full = threading.Condition(self.mutex)

    def put(self, item: T, block: bool = True, timeout: Optional[float] = None) -> None:
        """Put item into queue"""
        with self.not_full:
            if self.maxsize > 0:
                if not block:
                    if len(self.queue) >= self.maxsize:
                        raise Exception("Queue is full")
                elif timeout is None:
                    while len(self.queue) >= self.maxsize:
                        self.not_full.wait()
                else:
                    deadline = time.time() + timeout
                    while len(self.queue) >= self.maxsize:
                        remaining = deadline - time.time()
                        if remaining <= 0:
                            raise Exception("Timeout")
                        self.not_full.wait(remaining)

            self.queue.append(item)
            self.not_empty.notify()

    def get(self, block: bool = True, timeout: Optional[float] = None) -> T:
        """Get item from queue"""
        with self.not_empty:
            if not block:
                if not self.queue:
                    raise Exception("Queue is empty")
            elif timeout is None:
                while not self.queue:
                    self.not_empty.wait()
            else:
                deadline = time.time() + timeout
                while not self.queue:
                    remaining = deadline - time.time()
                    if remaining <= 0:
                        raise Exception("Timeout")
                    self.not_empty.wait(remaining)

            item = self.queue.popleft()
            self.not_full.notify()
            return item

    def qsize(self) -> int:
        """Get queue size"""
        with self.mutex:
            return len(self.queue)

    def empty(self) -> bool:
        """Check if queue is empty"""
        with self.mutex:
            return len(self.queue) == 0

    def full(self) -> bool:
        """Check if queue is full"""
        with self.mutex:
            return self.maxsize > 0 and len(self.queue) >= self.maxsize


class AsyncRateLimiter:
    """Asynchronous rate limiter using token bucket algorithm"""

    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens, blocking if necessary"""
        async with self.lock:
            while tokens > self.tokens:
                # Update token count
                now = time.time()
                elapsed = now - self.last_update
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                self.last_update = now

                if tokens > self.tokens:
                    # Calculate wait time
                    wait_time = (tokens - self.tokens) / self.rate
                    await asyncio.sleep(wait_time)

            self.tokens -= tokens

    async def try_acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens without blocking"""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            if tokens <= self.tokens:
                self.tokens -= tokens
                return True
            return False


class ParallelMapReduce:
    """Parallel MapReduce implementation"""

    @staticmethod
    def map_reduce(data: List[Any],
                   map_func: Callable[[Any], List[Tuple[Any, Any]]],
                   reduce_func: Callable[[Any, List[Any]], Any],
                   num_workers: Optional[int] = None) -> Dict[Any, Any]:
        """Execute MapReduce operation in parallel"""

        if num_workers is None:
            num_workers = multiprocessing.cpu_count()

        # Split data into chunks
        chunk_size = max(1, len(data) // num_workers)
        chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

        # Map phase
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            map_results = list(executor.map(ParallelMapReduce._map_chunk,
                                           chunks,
                                           [map_func] * len(chunks)))

        # Shuffle phase
        shuffled = defaultdict(list)
        for chunk_result in map_results:
            for key, value in chunk_result:
                shuffled[key].append(value)

        # Reduce phase
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(reduce_func, key, values): key
                      for key, values in shuffled.items()}

            results = {}
            for future in futures:
                key = futures[future]
                results[key] = future.result()

        return results

    @staticmethod
    def _map_chunk(chunk: List[Any], map_func: Callable) -> List[Tuple[Any, Any]]:
        """Process a chunk in map phase"""
        results = []
        for item in chunk:
            results.extend(map_func(item))
        return results


# ============================================================================
# FUNCTIONAL PROGRAMMING UTILITIES
# ============================================================================

class Monad(Generic[T]):
    """Base monad implementation"""

    def __init__(self, value: T):
        self.value = value

    def bind(self, func: Callable[[T], 'Monad[V]']) -> 'Monad[V]':
        """Monadic bind operation"""
        raise NotImplementedError

    def map(self, func: Callable[[T], V]) -> 'Monad[V]':
        """Functor map operation"""
        return self.bind(lambda x: self.__class__(func(x)))

    @classmethod
    def pure(cls, value: T) -> 'Monad[T]':
        """Wrap value in monad"""
        return cls(value)


class Maybe(Monad[Optional[T]]):
    """Maybe monad for handling optional values"""

    def bind(self, func: Callable[[T], 'Maybe[V]']) -> 'Maybe[V]':
        if self.value is None:
            return Maybe(None)
        return func(self.value)

    def or_else(self, default: T) -> T:
        """Get value or default"""
        return self.value if self.value is not None else default

    @classmethod
    def nothing(cls) -> 'Maybe[T]':
        """Create empty Maybe"""
        return cls(None)

    @classmethod
    def just(cls, value: T) -> 'Maybe[T]':
        """Create Maybe with value"""
        return cls(value)


class Either(Generic[T, V]):
    """Either monad for error handling"""

    def __init__(self, left: Optional[T] = None, right: Optional[V] = None):
        if (left is None) == (right is None):
            raise ValueError("Either must have exactly one value")
        self.left = left
        self.right = right

    def is_left(self) -> bool:
        """Check if this is a Left value"""
        return self.left is not None

    def is_right(self) -> bool:
        """Check if this is a Right value"""
        return self.right is not None

    def bind(self, func: Callable[[V], 'Either[T, K]']) -> 'Either[T, K]':
        """Bind operation for Either"""
        if self.is_left():
            return Either(left=self.left)
        return func(self.right)

    def map(self, func: Callable[[V], K]) -> 'Either[T, K]':
        """Map over Right value"""
        if self.is_left():
            return Either(left=self.left)
        return Either(right=func(self.right))

    def map_left(self, func: Callable[[T], K]) -> 'Either[K, V]':
        """Map over Left value"""
        if self.is_right():
            return Either(right=self.right)
        return Either(left=func(self.left))

    @classmethod
    def left(cls, value: T) -> 'Either[T, V]':
        """Create Left value"""
        return cls(left=value)

    @classmethod
    def right(cls, value: V) -> 'Either[T, V]':
        """Create Right value"""
        return cls(right=value)


def compose(*functions: Callable) -> Callable:
    """Compose multiple functions"""
    def inner(x):
        for func in reversed(functions):
            x = func(x)
        return x
    return inner


def curry(func: Callable) -> Callable:
    """Curry a function"""
    @functools.wraps(func)
    def curried(*args, **kwargs):
        if len(args) + len(kwargs) >= func.__code__.co_argcount:
            return func(*args, **kwargs)
        return lambda *more_args, **more_kwargs: curried(
            *(args + more_args), **{**kwargs, **more_kwargs}
        )
    return curried


class Pipe:
    """Pipe for function chaining"""

    def __init__(self, value: Any):
        self.value = value

    def __or__(self, func: Callable) -> 'Pipe':
        """Use | operator for piping"""
        return Pipe(func(self.value))

    def __rshift__(self, func: Callable) -> 'Pipe':
        """Use >> operator for piping"""
        return Pipe(func(self.value))

    def get(self) -> Any:
        """Get the final value"""
        return self.value


def memoize(maxsize: Optional[int] = None) -> Callable:
    """Advanced memoization decorator with LRU cache"""
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_order = deque()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key = (args, tuple(sorted(kwargs.items())))

            if key in cache:
                # Move to end (most recently used)
                cache_order.remove(key)
                cache_order.append(key)
                return cache[key]

            # Compute result
            result = func(*args, **kwargs)

            # Add to cache
            cache[key] = result
            cache_order.append(key)

            # Evict if necessary
            if maxsize and len(cache) > maxsize:
                oldest = cache_order.popleft()
                del cache[oldest]

            return result

        wrapper.cache_info = lambda: {
            'hits': sum(1 for k in cache_order if k in cache),
            'misses': len(cache_order) - len(cache),
            'maxsize': maxsize,
            'currsize': len(cache)
        }

        wrapper.cache_clear = lambda: (cache.clear(), cache_order.clear())

        return wrapper

    return decorator


# ============================================================================
# ADVANCED DECORATORS AND METACLASSES
# ============================================================================

def retry(max_attempts: int = 3,
         delay: float = 1.0,
         backoff: float = 2.0,
         exceptions: Tuple[Type[Exception], ...] = (Exception,)) -> Callable:
    """Retry decorator with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise

                    print(f"Attempt {attempt} failed: {e}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff

            return None

        return wrapper
    return decorator


def timeout(seconds: float) -> Callable:
    """Timeout decorator using threading"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]

            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(seconds)

            if thread.is_alive():
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")

            if exception[0]:
                raise exception[0]

            return result[0]

        return wrapper
    return decorator


def synchronized(lock: Optional[threading.Lock] = None) -> Callable:
    """Synchronization decorator for thread safety"""
    if lock is None:
        lock = threading.Lock()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_types(func: Callable) -> Callable:
    """Decorator to validate function argument types using type hints"""
    sig = inspect.signature(func)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        for param_name, param_value in bound.arguments.items():
            param = sig.parameters[param_name]
            if param.annotation != param.empty:
                expected_type = param.annotation

                # Handle Optional types
                if hasattr(expected_type, '__origin__') and expected_type.__origin__ is Union:
                    if type(None) in expected_type.__args__:
                        if param_value is None:
                            continue
                        expected_type = tuple(t for t in expected_type.__args__ if t != type(None))

                if not isinstance(param_value, expected_type):
                    raise TypeError(
                        f"Argument '{param_name}' must be {expected_type}, "
                        f"got {type(param_value)}"
                    )

        return func(*args, **kwargs)

    return wrapper


class Singleton(type):
    """Singleton metaclass"""
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


class AutoProperty(type):
    """Metaclass that automatically creates properties for private attributes"""

    def __new__(mcs, name, bases, namespace):
        # Find private attributes
        for attr_name, attr_value in list(namespace.items()):
            if attr_name.startswith('_') and not attr_name.startswith('__'):
                # Create property
                public_name = attr_name[1:]

                def make_property(attr):
                    def getter(self):
                        return getattr(self, attr)

                    def setter(self, value):
                        setattr(self, attr, value)

                    return property(getter, setter)

                namespace[public_name] = make_property(attr_name)

        return super().__new__(mcs, name, bases, namespace)


class Immutable(type):
    """Metaclass for creating immutable classes"""

    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        instance.__frozen = True
        return instance

    def __new__(mcs, name, bases, namespace):
        def __setattr__(self, key, value):
            if hasattr(self, '__frozen') and self.__frozen:
                raise AttributeError(f"Cannot modify immutable instance of {name}")
            super(cls, self).__setattr__(key, value)

        namespace['__setattr__'] = __setattr__
        cls = super().__new__(mcs, name, bases, namespace)
        return cls


# ============================================================================
# SCIENTIFIC COMPUTING FUNCTIONS
# ============================================================================

class NumericalIntegration:
    """Numerical integration methods"""

    @staticmethod
    def trapezoidal(f: Callable[[float], float], a: float, b: float, n: int = 1000) -> float:
        """Trapezoidal rule for numerical integration"""
        h = (b - a) / n
        result = 0.5 * (f(a) + f(b))

        for i in range(1, n):
            x = a + i * h
            result += f(x)

        return result * h

    @staticmethod
    def simpson(f: Callable[[float], float], a: float, b: float, n: int = 1000) -> float:
        """Simpson's rule for numerical integration"""
        if n % 2 != 0:
            n += 1

        h = (b - a) / n
        result = f(a) + f(b)

        for i in range(1, n):
            x = a + i * h
            if i % 2 == 0:
                result += 2 * f(x)
            else:
                result += 4 * f(x)

        return result * h / 3

    @staticmethod
    def monte_carlo(f: Callable[[float], float], a: float, b: float,
                   n_samples: int = 10000) -> float:
        """Monte Carlo integration"""
        total = 0

        for _ in range(n_samples):
            x = random.uniform(a, b)
            total += f(x)

        return (b - a) * total / n_samples

    @staticmethod
    def adaptive_simpson(f: Callable[[float], float], a: float, b: float,
                        tol: float = 1e-6, max_depth: int = 10) -> float:
        """Adaptive Simpson's rule"""
        def simpson_step(a, b):
            c = (a + b) / 2
            h = b - a
            return h / 6 * (f(a) + 4 * f(c) + f(b))

        def adaptive_simpson_recursive(a, b, tol, whole, depth):
            c = (a + b) / 2
            left = simpson_step(a, c)
            right = simpson_step(c, b)

            if depth <= 0 or abs(left + right - whole) <= 15 * tol:
                return left + right + (left + right - whole) / 15

            return (adaptive_simpson_recursive(a, c, tol/2, left, depth-1) +
                   adaptive_simpson_recursive(c, b, tol/2, right, depth-1))

        whole = simpson_step(a, b)
        return adaptive_simpson_recursive(a, b, tol, whole, max_depth)


class DifferentialEquations:
    """Numerical methods for solving differential equations"""

    @staticmethod
    def euler_method(f: Callable[[float, float], float], y0: float,
                    t0: float, t_end: float, h: float = 0.01) -> List[Tuple[float, float]]:
        """Euler's method for solving ODEs"""
        t = t0
        y = y0
        solution = [(t, y)]

        while t < t_end:
            y = y + h * f(t, y)
            t = t + h
            solution.append((t, y))

        return solution

    @staticmethod
    def runge_kutta_4(f: Callable[[float, float], float], y0: float,
                     t0: float, t_end: float, h: float = 0.01) -> List[Tuple[float, float]]:
        """Fourth-order Runge-Kutta method"""
        t = t0
        y = y0
        solution = [(t, y)]

        while t < t_end:
            k1 = h * f(t, y)
            k2 = h * f(t + h/2, y + k1/2)
            k3 = h * f(t + h/2, y + k2/2)
            k4 = h * f(t + h, y + k3)

            y = y + (k1 + 2*k2 + 2*k3 + k4) / 6
            t = t + h
            solution.append((t, y))

        return solution

    @staticmethod
    def adams_bashforth_4(f: Callable[[float, float], float], y0: float,
                         t0: float, t_end: float, h: float = 0.01) -> List[Tuple[float, float]]:
        """Fourth-order Adams-Bashforth method"""
        # Use RK4 for initial values
        rk4_steps = DifferentialEquations.runge_kutta_4(f, y0, t0, t0 + 3*h, h)
        solution = rk4_steps[:]

        # History of f values
        f_history = [f(t, y) for t, y in rk4_steps]

        t = t0 + 3*h
        y = rk4_steps[-1][1]

        while t < t_end:
            # Adams-Bashforth formula
            y_new = y + h/24 * (55*f_history[-1] - 59*f_history[-2] +
                               37*f_history[-3] - 9*f_history[-4])
            t = t + h

            solution.append((t, y_new))
            f_history.append(f(t, y_new))
            f_history.pop(0)
            y = y_new

        return solution


class Optimization:
    """Optimization algorithms"""

    @staticmethod
    def gradient_descent(f: Callable[[np.ndarray], float],
                        grad_f: Callable[[np.ndarray], np.ndarray],
                        x0: np.ndarray, learning_rate: float = 0.01,
                        max_iters: int = 1000, tol: float = 1e-6) -> Tuple[np.ndarray, List[float]]:
        """Gradient descent optimization"""
        x = x0.copy()
        history = [f(x)]

        for _ in range(max_iters):
            grad = grad_f(x)
            x_new = x - learning_rate * grad

            if np.linalg.norm(x_new - x) < tol:
                break

            x = x_new
            history.append(f(x))

        return x, history

    @staticmethod
    def newton_method(f: Callable[[float], float],
                     df: Callable[[float], float],
                     x0: float, tol: float = 1e-6,
                     max_iters: int = 100) -> Tuple[float, int]:
        """Newton's method for finding roots"""
        x = x0

        for i in range(max_iters):
            fx = f(x)
            if abs(fx) < tol:
                return x, i

            dfx = df(x)
            if abs(dfx) < 1e-10:
                raise ValueError("Derivative too small")

            x = x - fx / dfx

        raise ValueError("Failed to converge")

    @staticmethod
    def golden_section_search(f: Callable[[float], float],
                            a: float, b: float,
                            tol: float = 1e-6) -> float:
        """Golden section search for finding minimum"""
        phi = (1 + math.sqrt(5)) / 2
        resphi = 2 - phi

        # Initial points
        x1 = a + resphi * (b - a)
        x2 = b - resphi * (b - a)
        f1 = f(x1)
        f2 = f(x2)

        while abs(b - a) > tol:
            if f1 < f2:
                b = x2
                x2 = x1
                f2 = f1
                x1 = a + resphi * (b - a)
                f1 = f(x1)
            else:
                a = x1
                x1 = x2
                f1 = f2
                x2 = b - resphi * (b - a)
                f2 = f(x2)

        return (a + b) / 2

    @staticmethod
    def simulated_annealing(f: Callable[[np.ndarray], float],
                          x0: np.ndarray, temp: float = 1000,
                          cooling_rate: float = 0.95,
                          min_temp: float = 1e-3,
                          step_size: float = 0.1) -> Tuple[np.ndarray, float]:
        """Simulated annealing optimization"""
        current = x0.copy()
        current_cost = f(current)
        best = current.copy()
        best_cost = current_cost

        while temp > min_temp:
            # Generate neighbor
            neighbor = current + np.random.normal(0, step_size, size=current.shape)
            neighbor_cost = f(neighbor)

            # Accept or reject
            delta = neighbor_cost - current_cost
            if delta < 0 or random.random() < math.exp(-delta / temp):
                current = neighbor
                current_cost = neighbor_cost

                if current_cost < best_cost:
                    best = current.copy()
                    best_cost = current_cost

            # Cool down
            temp *= cooling_rate

        return best, best_cost


class Statistics:
    """Advanced statistical functions"""

    @staticmethod
    def bootstrap(data: List[float], statistic: Callable[[List[float]], float],
                 n_bootstrap: int = 1000, confidence: float = 0.95) -> Dict[str, float]:
        """Bootstrap resampling for confidence intervals"""
        n = len(data)
        bootstrap_stats = []

        for _ in range(n_bootstrap):
            # Resample with replacement
            resample = [data[random.randint(0, n-1)] for _ in range(n)]
            bootstrap_stats.append(statistic(resample))

        bootstrap_stats.sort()
        alpha = 1 - confidence
        lower_idx = int(alpha / 2 * n_bootstrap)
        upper_idx = int((1 - alpha / 2) * n_bootstrap)

        return {
            'estimate': statistic(data),
            'lower': bootstrap_stats[lower_idx],
            'upper': bootstrap_stats[upper_idx],
            'std_error': np.std(bootstrap_stats)
        }

    @staticmethod
    def permutation_test(group1: List[float], group2: List[float],
                        statistic: Callable[[List[float], List[float]], float],
                        n_permutations: int = 1000) -> float:
        """Permutation test for hypothesis testing"""
        observed_stat = statistic(group1, group2)
        combined = group1 + group2
        n1 = len(group1)

        extreme_count = 0
        for _ in range(n_permutations):
            # Shuffle and split
            random.shuffle(combined)
            perm_group1 = combined[:n1]
            perm_group2 = combined[n1:]

            perm_stat = statistic(perm_group1, perm_group2)
            if abs(perm_stat) >= abs(observed_stat):
                extreme_count += 1

        return extreme_count / n_permutations

    @staticmethod
    def kernel_density_estimation(data: List[float], x: float,
                                bandwidth: float = 1.0,
                                kernel: str = 'gaussian') -> float:
        """Kernel density estimation"""
        n = len(data)

        if kernel == 'gaussian':
            kernel_func = lambda u: (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * u**2)
        elif kernel == 'epanechnikov':
            kernel_func = lambda u: 0.75 * (1 - u**2) if abs(u) <= 1 else 0
        else:
            raise ValueError(f"Unknown kernel: {kernel}")

        density = 0
        for xi in data:
            u = (x - xi) / bandwidth
            density += kernel_func(u)

        return density / (n * bandwidth)


# ============================================================================
# ADVANCED ALGORITHMS AND DATA PROCESSING
# ============================================================================

class BloomFilter:
    """Probabilistic data structure for membership testing"""

    def __init__(self, size: int = 1000000, num_hash_functions: int = 7):
        self.size = size
        self.num_hash_functions = num_hash_functions
        self.bit_array = [False] * size
        self.num_elements = 0

    def _hash(self, item: str, seed: int) -> int:
        """Generate hash value with seed"""
        h = hashlib.md5(f"{item}{seed}".encode()).hexdigest()
        return int(h, 16) % self.size

    def add(self, item: str) -> None:
        """Add item to bloom filter"""
        for i in range(self.num_hash_functions):
            index = self._hash(item, i)
            self.bit_array[index] = True
        self.num_elements += 1

    def contains(self, item: str) -> bool:
        """Check if item might be in the set"""
        for i in range(self.num_hash_functions):
            index = self._hash(item, i)
            if not self.bit_array[index]:
                return False
        return True

    def false_positive_probability(self) -> float:
        """Calculate theoretical false positive probability"""
        if self.num_elements == 0:
            return 0

        # Formula: (1 - e^(-k*n/m))^k
        k = self.num_hash_functions
        n = self.num_elements
        m = self.size

        return (1 - math.exp(-k * n / m)) ** k


class CountMinSketch:
    """Probabilistic data structure for frequency estimation"""

    def __init__(self, width: int = 1000, depth: int = 5):
        self.width = width
        self.depth = depth
        self.table = [[0] * width for _ in range(depth)]

    def _hash(self, item: str, row: int) -> int:
        """Hash function for given row"""
        h = hashlib.md5(f"{item}{row}".encode()).hexdigest()
        return int(h, 16) % self.width

    def update(self, item: str, count: int = 1) -> None:
        """Update count for item"""
        for row in range(self.depth):
            col = self._hash(item, row)
            self.table[row][col] += count

    def estimate(self, item: str) -> int:
        """Estimate count for item"""
        min_count = float('inf')

        for row in range(self.depth):
            col = self._hash(item, row)
            min_count = min(min_count, self.table[row][col])

        return int(min_count)


class HyperLogLog:
    """Probabilistic cardinality estimation"""

    def __init__(self, precision: int = 14):
        self.precision = precision
        self.m = 2 ** precision
        self.registers = [0] * self.m
        self.alpha = self._get_alpha()

    def _get_alpha(self) -> float:
        """Get alpha constant based on precision"""
        if self.precision >= 16:
            return 0.7213 / (1 + 1.079 / self.m)
        elif self.precision >= 7:
            return 0.7213 / (1 + 1.079 / self.m)
        elif self.precision >= 6:
            return 0.709
        elif self.precision >= 5:
            return 0.697
        else:
            return 0.673

    def _hash(self, item: str) -> int:
        """Hash item to 64-bit integer"""
        # Get the first 16 characters of the SHA-256 hash
        h = hashlib.sha256(item.encode()).hexdigest()
        return int(h[:16], 16)

    def _leading_zeros(self, bits: int) -> int:
        """Count leading zeros in binary representation"""
        if bits == 0:
            return 64

        count = 0
        mask = 1 << 63

        while (bits & mask) == 0 and count < 64:
            count += 1
            mask >>= 1

        return count

    def add(self, item: str) -> None:
        """Add item to HyperLogLog"""
        hash_val = self._hash(item)

        # Use first precision bits as bucket index
        j = hash_val & ((1 << self.precision) - 1)

        # Count leading zeros in remaining bits
        w = hash_val >> self.precision
        leading_zeros = self._leading_zeros(w) + 1

        # Update register
        self.registers[j] = max(self.registers[j], leading_zeros)

    def cardinality(self) -> int:
        """Estimate cardinality"""
        # Harmonic mean
        raw_estimate = self.alpha * (self.m ** 2) / sum(2 ** (-x) for x in self.registers)

        # Apply bias correction for small cardinalities
        if raw_estimate <= 2.5 * self.m:
            zeros = self.registers.count(0)
            if zeros != 0:
                return int(self.m * math.log(self.m / zeros))

        # Apply correction for large cardinalities
        if raw_estimate <= (1/30) * (1 << 32):
            return int(raw_estimate)
        else:
            return int(-1 * (1 << 32) * math.log(1 - raw_estimate / (1 << 32)))


class LRUCache(Generic[K, V]):
    """Least Recently Used cache implementation"""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache: Dict[K, 'LRUCache.Node'] = {}
        self.head = self.Node()
        self.tail = self.Node()
        self.head.next = self.tail
        self.tail.prev = self.head

    class Node:
        def __init__(self, key: Optional[K] = None, value: Optional[V] = None):
            self.key = key
            self.value = value
            self.prev: Optional['LRUCache.Node'] = None
            self.next: Optional['LRUCache.Node'] = None

    def _add_to_head(self, node: 'Node') -> None:
        """Add node right after head"""
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def _remove_node(self, node: 'Node') -> None:
        """Remove node from linked list"""
        node.prev.next = node.next
        node.next.prev = node.prev

    def _move_to_head(self, node: 'Node') -> None:
        """Move node to head (mark as recently used)"""
        self._remove_node(node)
        self._add_to_head(node)

    def get(self, key: K) -> Optional[V]:
        """Get value from cache"""
        if key in self.cache:
            node = self.cache[key]
            self._move_to_head(node)
            return node.value
        return None

    def put(self, key: K, value: V) -> None:
        """Put key-value pair in cache"""
        if key in self.cache:
            node = self.cache[key]
            node.value = value
            self._move_to_head(node)
        else:
            node = self.Node(key, value)
            self.cache[key] = node
            self._add_to_head(node)

            if len(self.cache) > self.capacity:
                # Remove least recently used
                lru = self.tail.prev
                self._remove_node(lru)
                del self.cache[lru.key]


class ConsistentHashing:
    """Consistent hashing for distributed systems"""

    def __init__(self, num_virtual_nodes: int = 150):
        self.num_virtual_nodes = num_virtual_nodes
        self.ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []
        self.nodes: Set[str] = set()

    def _hash(self, key: str) -> int:
        """Hash function"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, node: str) -> None:
        """Add node to the ring"""
        self.nodes.add(node)

        for i in range(self.num_virtual_nodes):
            virtual_key = f"{node}:{i}"
            hash_val = self._hash(virtual_key)
            self.ring[hash_val] = node
            self.sorted_keys.append(hash_val)

        self.sorted_keys.sort()

    def remove_node(self, node: str) -> None:
        """Remove node from the ring"""
        if node not in self.nodes:
            return

        self.nodes.remove(node)

        for i in range(self.num_virtual_nodes):
            virtual_key = f"{node}:{i}"
            hash_val = self._hash(virtual_key)
            del self.ring[hash_val]
            self.sorted_keys.remove(hash_val)

    def get_node(self, key: str) -> Optional[str]:
        """Get node responsible for key"""
        if not self.ring:
            return None

        hash_val = self._hash(key)

        # Binary search for the first node with hash >= key hash
        idx = self._binary_search(hash_val)

        if idx == len(self.sorted_keys):
            idx = 0

        return self.ring[self.sorted_keys[idx]]

    def _binary_search(self, target: int) -> int:
        """Binary search for position in sorted keys"""
        left, right = 0, len(self.sorted_keys)

        while left < right:
            mid = (left + right) // 2
            if self.sorted_keys[mid] < target:
                left = mid + 1
            else:
                right = mid

        return left


class TimeSeries:
    """Time series data structure with various operations"""

    def __init__(self):
        self.data: List[Tuple[datetime, float]] = []

    def add_point(self, timestamp: datetime, value: float) -> None:
        """Add data point"""
        self.data.append((timestamp, value))
        self.data.sort(key=lambda x: x[0])

    def resample(self, interval: timedelta,
                aggregation: str = 'mean') -> List[Tuple[datetime, float]]:
        """Resample time series to fixed intervals"""
        if not self.data:
            return []

        start_time = self.data[0][0]
        end_time = self.data[-1][0]

        resampled = []
        current_time = start_time

        while current_time <= end_time:
            next_time = current_time + interval

            # Get points in current interval
            points = [(t, v) for t, v in self.data
                     if current_time <= t < next_time]

            if points:
                values = [v for _, v in points]

                if aggregation == 'mean':
                    agg_value = sum(values) / len(values)
                elif aggregation == 'sum':
                    agg_value = sum(values)
                elif aggregation == 'min':
                    agg_value = min(values)
                elif aggregation == 'max':
                    agg_value = max(values)
                else:
                    raise ValueError(f"Unknown aggregation: {aggregation}")

                resampled.append((current_time, agg_value))

            current_time = next_time

        return resampled

    def moving_average(self, window_size: int) -> List[Tuple[datetime, float]]:
        """Calculate moving average"""
        if len(self.data) < window_size:
            return []

        result = []

        for i in range(window_size - 1, len(self.data)):
            window_sum = sum(v for _, v in self.data[i - window_size + 1:i + 1])
            avg = window_sum / window_size
            result.append((self.data[i][0], avg))

        return result

    def exponential_smoothing(self, alpha: float = 0.3) -> List[Tuple[datetime, float]]:
        """Exponential smoothing"""
        if not self.data:
            return []

        result = [(self.data[0][0], self.data[0][1])]

        for i in range(1, len(self.data)):
            smoothed = alpha * self.data[i][1] + (1 - alpha) * result[-1][1]
            result.append((self.data[i][0], smoothed))

        return result

    def detect_anomalies(self, threshold: float = 3.0) -> List[Tuple[datetime, float]]:
        """Detect anomalies using z-score"""
        if len(self.data) < 2:
            return []

        values = [v for _, v in self.data]
        mean = sum(values) / len(values)
        std = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))

        if std == 0:
            return []

        anomalies = []
        for timestamp, value in self.data:
            z_score = abs((value - mean) / std)
            if z_score > threshold:
                anomalies.append((timestamp, value))

        return anomalies


# ============================================================================
# COMPUTATIONAL GEOMETRY
# ============================================================================

class Point2D:
    """2D point for computational geometry"""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return f"Point({self.x}, {self.y})"

    def distance_to(self, other: 'Point2D') -> float:
        """Euclidean distance to another point"""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def __eq__(self, other: 'Point2D') -> bool:
        return self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        return hash((self.x, self.y))


class ConvexHull:
    """Convex hull algorithms"""

    @staticmethod
    def graham_scan(points: List[Point2D]) -> List[Point2D]:
        """Graham scan algorithm for convex hull"""
        if len(points) < 3:
            return points

        # Find the bottom-most point (and left-most if tie)
        start = min(points, key=lambda p: (p.y, p.x))

        # Sort points by polar angle with respect to start point
        def polar_angle(p: Point2D) -> float:
            dx = p.x - start.x
            dy = p.y - start.y
            return math.atan2(dy, dx)

        sorted_points = sorted(points, key=lambda p: (polar_angle(p), p.distance_to(start)))

        # Build convex hull
        hull = [sorted_points[0], sorted_points[1]]

        for i in range(2, len(sorted_points)):
            # Remove points that make clockwise turn
            while len(hull) > 1 and ConvexHull._ccw(hull[-2], hull[-1], sorted_points[i]) <= 0:
                hull.pop()
            hull.append(sorted_points[i])

        return hull

    @staticmethod
    def _ccw(p1: Point2D, p2: Point2D, p3: Point2D) -> float:
        """Counter-clockwise test"""
        return (p2.x - p1.x) * (p3.y - p1.y) - (p2.y - p1.y) * (p3.x - p1.x)

    @staticmethod
    def jarvis_march(points: List[Point2D]) -> List[Point2D]:
        """Jarvis march (gift wrapping) algorithm"""
        if len(points) < 3:
            return points

        # Find leftmost point
        start = min(points, key=lambda p: p.x)
        hull = [start]
        current = start

        while True:
            next_point = points[0]

            for point in points[1:]:
                if point == current:
                    continue

                # Check if point is more counter-clockwise
                cross = ConvexHull._ccw(current, next_point, point)
                if next_point == current or cross > 0 or (cross == 0 and
                    current.distance_to(point) > current.distance_to(next_point)):
                    next_point = point

            current = next_point

            if current == start:
                break

            hull.append(current)

        return hull


class LineSegment:
    """Line segment for computational geometry"""

    def __init__(self, p1: Point2D, p2: Point2D):
        self.p1 = p1
        self.p2 = p2

    def intersects(self, other: 'LineSegment') -> bool:
        """Check if two line segments intersect"""
        def orientation(p: Point2D, q: Point2D, r: Point2D) -> int:
            val = (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)
            if val == 0:
                return 0  # Collinear
            return 1 if val > 0 else 2  # Clockwise or Counterclockwise

        def on_segment(p: Point2D, q: Point2D, r: Point2D) -> bool:
            return (q.x <= max(p.x, r.x) and q.x >= min(p.x, r.x) and
                   q.y <= max(p.y, r.y) and q.y >= min(p.y, r.y))

        o1 = orientation(self.p1, self.p2, other.p1)
        o2 = orientation(self.p1, self.p2, other.p2)
        o3 = orientation(other.p1, other.p2, self.p1)
        o4 = orientation(other.p1, other.p2, self.p2)

        # General case
        if o1 != o2 and o3 != o4:
            return True

        # Special cases (collinear points)
        if o1 == 0 and on_segment(self.p1, other.p1, self.p2):
            return True
        if o2 == 0 and on_segment(self.p1, other.p2, self.p2):
            return True
        if o3 == 0 and on_segment(other.p1, self.p1, other.p2):
            return True
        if o4 == 0 and on_segment(other.p1, self.p2, other.p2):
            return True

        return False


class VoronoiDiagram:
    """Simplified Voronoi diagram computation"""

    @staticmethod
    def compute_voronoi_cells(points: List[Point2D],
                            bounds: Tuple[float, float, float, float]) -> Dict[Point2D, List[Point2D]]:
        """Compute Voronoi cells using brute force (for small datasets)"""
        min_x, min_y, max_x, max_y = bounds
        cells = {point: [] for point in points}

        # Sample grid points
        resolution = 100
        for i in range(resolution):
            for j in range(resolution):
                x = min_x + (max_x - min_x) * i / (resolution - 1)
                y = min_y + (max_y - min_y) * j / (resolution - 1)
                sample = Point2D(x, y)

                # Find nearest point
                nearest = min(points, key=lambda p: sample.distance_to(p))
                cells[nearest].append(sample)

        return cells


# ============================================================================
# ADVANCED PATTERN MATCHING AND REGULAR EXPRESSIONS
# ============================================================================

class RegexEngine:
    """Simple regex engine implementation"""

    @staticmethod
    def match(pattern: str, text: str) -> bool:
        """Match pattern against text (simplified)"""
        def match_here(pattern: str, text: str) -> bool:
            if not pattern:
                return True

            if len(pattern) > 1 and pattern[1] == '*':
                return match_star(pattern[0], pattern[2:], text)

            if pattern[0] == '$' and len(pattern) == 1:
                return not text

            if text and (pattern[0] == '.' or pattern[0] == text[0]):
                return match_here(pattern[1:], text[1:])

            return False

        def match_star(c: str, pattern: str, text: str) -> bool:
            # Match 0 or more occurrences of c
            if match_here(pattern, text):
                return True

            while text and (c == '.' or c == text[0]):
                text = text[1:]
                if match_here(pattern, text):
                    return True

            return False

        if pattern and pattern[0] == '^':
            return match_here(pattern[1:], text)

        # Try to match at each position
        while text:
            if match_here(pattern, text):
                return True
            text = text[1:]

        return match_here(pattern, text)


class AhoCorasick:
    """Aho-Corasick algorithm for multiple pattern matching"""

    def __init__(self):
        self.goto = defaultdict(dict)
        self.failure = {}
        self.output = defaultdict(list)
        self.state_count = 0

    def add_pattern(self, pattern: str) -> None:
        """Add pattern to the automaton"""
        state = 0

        for char in pattern:
            if char not in self.goto[state]:
                self.state_count += 1
                self.goto[state][char] = self.state_count
            state = self.goto[state][char]

        self.output[state].append(pattern)

    def build_failure_function(self) -> None:
        """Build failure function for the automaton"""
        queue = deque()

        # Initialize failure function for depth 1
        for char, state in self.goto[0].items():
            self.failure[state] = 0
            queue.append(state)

        # BFS to build failure function
        while queue:
            r = queue.popleft()

            for char, s in self.goto[r].items():
                queue.append(s)
                state = self.failure[r]

                while state != 0 and char not in self.goto[state]:
                    state = self.failure[state]

                self.failure[s] = self.goto[state].get(char, 0)
                self.output[s].extend(self.output[self.failure[s]])

    def search(self, text: str) -> List[Tuple[int, str]]:
        """Search for all patterns in text"""
        matches = []
        state = 0

        for i, char in enumerate(text):
            while state != 0 and char not in self.goto[state]:
                state = self.failure[state]

            state = self.goto[state].get(char, 0)

            for pattern in self.output[state]:
                matches.append((i - len(pattern) + 1, pattern))

        return matches


class BoyerMoore:
    """Boyer-Moore string matching algorithm"""

    def __init__(self, pattern: str):
        self.pattern = pattern
        self.bad_char_table = self._build_bad_char_table()
        self.good_suffix_table = self._build_good_suffix_table()

    def _build_bad_char_table(self) -> Dict[str, int]:
        """Build bad character table"""
        table = {}
        for i in range(len(self.pattern)):
            table[self.pattern[i]] = i
        return table

    def _build_good_suffix_table(self) -> List[int]:
        """Build good suffix table"""
        m = len(self.pattern)
        table = [0] * m

        # Simplified version
        for i in range(m):
            table[i] = m

        return table

    def search(self, text: str) -> List[int]:
        """Search for pattern in text"""
        matches = []
        m = len(self.pattern)
        n = len(text)

        i = 0
        while i <= n - m:
            j = m - 1

            while j >= 0 and self.pattern[j] == text[i + j]:
                j -= 1

            if j < 0:
                matches.append(i)
                i += self.good_suffix_table[0]
            else:
                bad_char_shift = j - self.bad_char_table.get(text[i + j], -1)
                good_suffix_shift = self.good_suffix_table[j]
                i += max(bad_char_shift, good_suffix_shift)

        return matches


# ============================================================================
# ADVANCED UTILITY FUNCTIONS
# ============================================================================

class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance"""

    def __init__(self, failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 expected_exception: Type[Exception] = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = 'HALF_OPEN'
                else:
                    raise Exception("Circuit breaker is OPEN")

            try:
                result = func(*args, **kwargs)
                if self.state == 'HALF_OPEN':
                    self.state = 'CLOSED'
                    self.failure_count = 0
                return result

            except self.expected_exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = 'OPEN'

                raise e

        return wrapper


class ObjectPool(Generic[T]):
    """Object pool for resource management"""

    def __init__(self, create_func: Callable[[], T],
                 reset_func: Optional[Callable[[T], None]] = None,
                 max_size: int = 10):
        self.create_func = create_func
        self.reset_func = reset_func
        self.max_size = max_size
        self.pool: List[T] = []
        self.in_use: Set[T] = set()
        self.lock = threading.Lock()

    def acquire(self) -> T:
        """Acquire object from pool"""
        with self.lock:
            if self.pool:
                obj = self.pool.pop()
            else:
                obj = self.create_func()

            self.in_use.add(obj)
            return obj

    def release(self, obj: T) -> None:
        """Release object back to pool"""
        with self.lock:
            if obj in self.in_use:
                self.in_use.remove(obj)

                if self.reset_func:
                    self.reset_func(obj)

                if len(self.pool) < self.max_size:
                    self.pool.append(obj)

    @contextmanager
    def get_object(self):
        """Context manager for object acquisition"""
        obj = self.acquire()
        try:
            yield obj
        finally:
            self.release(obj)


class EventBus:
    """Simple event bus implementation"""

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.lock = threading.Lock()

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to event type"""
        with self.lock:
            self.subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from event type"""
        with self.lock:
            if handler in self.subscribers[event_type]:
                self.subscribers[event_type].remove(handler)

    def publish(self, event_type: str, data: Any) -> None:
        """Publish event to all subscribers"""
        with self.lock:
            handlers = self.subscribers[event_type][:]

        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                print(f"Error in event handler: {e}")


class LazyProperty:
    """Lazy property decorator"""

    def __init__(self, func: Callable):
        self.func = func
        self.name = func.__name__

    def __get__(self, obj: Any, type: Any = None) -> Any:
        if obj is None:
            return self

        value = self.func(obj)
        setattr(obj, self.name, value)
        return value


class RateLimitedQueue:
    """Queue with rate limiting"""

    def __init__(self, rate: float, burst: int = 1):
        self.rate = rate  # items per second
        self.burst = burst
        self.queue: deque = deque()
        self.tokens = burst
        self.last_update = time.time()
        self.lock = threading.Lock()

    def put(self, item: Any) -> None:
        """Put item in queue"""
        with self.lock:
            self.queue.append(item)

    def get(self) -> Optional[Any]:
        """Get item from queue with rate limiting"""
        with self.lock:
            # Update tokens
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now

            # Check if we can consume
            if self.tokens >= 1 and self.queue:
                self.tokens -= 1
                return self.queue.popleft()

            return None


# ============================================================================
# ADVANCED DATA VALIDATION AND SERIALIZATION
# ============================================================================

class Validator:
    """Data validation framework"""

    def __init__(self):
        self.rules = []

    def add_rule(self, rule: Callable[[Any], bool],
                error_message: str = "Validation failed") -> 'Validator':
        """Add validation rule"""
        self.rules.append((rule, error_message))
        return self

    def validate(self, value: Any) -> Tuple[bool, List[str]]:
        """Validate value against all rules"""
        errors = []

        for rule, error_message in self.rules:
            try:
                if not rule(value):
                    errors.append(error_message)
            except Exception as e:
                errors.append(f"Validation error: {str(e)}")

        return len(errors) == 0, errors

    @staticmethod
    def email() -> 'Validator':
        """Email validator"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return Validator().add_rule(
            lambda x: isinstance(x, str) and re.match(pattern, x) is not None,
            "Invalid email format"
        )

    @staticmethod
    def range(min_val: float, max_val: float) -> 'Validator':
        """Range validator"""
        return Validator().add_rule(
            lambda x: min_val <= x <= max_val,
            f"Value must be between {min_val} and {max_val}"
        )

    @staticmethod
    def length(min_len: int, max_len: int) -> 'Validator':
        """Length validator"""
        return Validator().add_rule(
            lambda x: min_len <= len(x) <= max_len,
            f"Length must be between {min_len} and {max_len}"
        )


class JSONEncoder:
    """Custom JSON encoder with advanced features"""

    def __init__(self, indent: int = 2, sort_keys: bool = False):
        self.indent = indent
        self.sort_keys = sort_keys
        self.type_handlers = {
            datetime: lambda x: x.isoformat(),
            set: list,
            frozenset: list,
            bytes: lambda x: x.decode('utf-8', errors='replace'),
        }

    def add_type_handler(self, type_: Type, handler: Callable) -> None:
        """Add custom type handler"""
        self.type_handlers[type_] = handler

    def encode(self, obj: Any, current_indent: int = 0) -> str:
        """Encode object to JSON string"""
        if obj is None:
            return "null"
        elif isinstance(obj, bool):
            return "true" if obj else "false"
        elif isinstance(obj, (int, float)):
            return str(obj)
        elif isinstance(obj, str):
            return self._encode_string(obj)
        elif isinstance(obj, dict):
            return self._encode_dict(obj, current_indent)
        elif isinstance(obj, (list, tuple)):
            return self._encode_list(obj, current_indent)
        else:
            # Check custom handlers
            for type_, handler in self.type_handlers.items():
                if isinstance(obj, type_):
                    return self.encode(handler(obj), current_indent)

            # Try to convert to dict
            if hasattr(obj, '__dict__'):
                return self.encode(obj.__dict__, current_indent)

            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def _encode_string(self, s: str) -> str:
        """Encode string with proper escaping"""
        escaped = s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        escaped = escaped.replace('\r', '\\r').replace('\t', '\\t')
        return f'"{escaped}"'

    def _encode_dict(self, d: dict, current_indent: int) -> str:
        """Encode dictionary"""
        if not d:
            return "{}"

        items = []
        indent_str = " " * (current_indent + self.indent)

        keys = sorted(d.keys()) if self.sort_keys else d.keys()

        for key in keys:
            key_str = self._encode_string(str(key))
            value_str = self.encode(d[key], current_indent + self.indent)
            items.append(f"{indent_str}{key_str}: {value_str}")

        return "{\n" + ",\n".join(items) + "\n" + " " * current_indent + "}"

    def _encode_list(self, lst: list, current_indent: int) -> str:
        """Encode list"""
        if not lst:
            return "[]"

        items = []
        indent_str = " " * (current_indent + self.indent)

        for item in lst:
            item_str = self.encode(item, current_indent + self.indent)
            items.append(f"{indent_str}{item_str}")

        return "[\n" + ",\n".join(items) + "\n" + " " * current_indent + "]"


class BinarySerializer:
    """Binary serialization with custom protocol"""

    TYPE_NULL = 0x00
    TYPE_BOOL = 0x01
    TYPE_INT = 0x02
    TYPE_FLOAT = 0x03
    TYPE_STRING = 0x04
    TYPE_LIST = 0x05
    TYPE_DICT = 0x06

    @staticmethod
    def serialize(obj: Any) -> bytes:
        """Serialize object to bytes"""
        if obj is None:
            return bytes([BinarySerializer.TYPE_NULL])

        elif isinstance(obj, bool):
            return bytes([BinarySerializer.TYPE_BOOL, 1 if obj else 0])

        elif isinstance(obj, int):
            return bytes([BinarySerializer.TYPE_INT]) + struct.pack('>q', obj)

        elif isinstance(obj, float):
            return bytes([BinarySerializer.TYPE_FLOAT]) + struct.pack('>d', obj)

        elif isinstance(obj, str):
            encoded = obj.encode('utf-8')
            length = len(encoded)
            return (bytes([BinarySerializer.TYPE_STRING]) +
                   struct.pack('>I', length) + encoded)

        elif isinstance(obj, list):
            result = bytes([BinarySerializer.TYPE_LIST])
            result += struct.pack('>I', len(obj))
            for item in obj:
                result += BinarySerializer.serialize(item)
            return result

        elif isinstance(obj, dict):
            result = bytes([BinarySerializer.TYPE_DICT])
            result += struct.pack('>I', len(obj))
            for key, value in obj.items():
                result += BinarySerializer.serialize(str(key))
                result += BinarySerializer.serialize(value)
            return result

        else:
            raise TypeError(f"Cannot serialize type {type(obj)}")

    @staticmethod
    def deserialize(data: bytes, offset: int = 0) -> Tuple[Any, int]:
        """Deserialize object from bytes"""
        if offset >= len(data):
            raise ValueError("Unexpected end of data")

        type_byte = data[offset]
        offset += 1

        if type_byte == BinarySerializer.TYPE_NULL:
            return None, offset

        elif type_byte == BinarySerializer.TYPE_BOOL:
            return data[offset] != 0, offset + 1

        elif type_byte == BinarySerializer.TYPE_INT:
            value = struct.unpack('>q', data[offset:offset + 8])[0]
            return value, offset + 8

        elif type_byte == BinarySerializer.TYPE_FLOAT:
            value = struct.unpack('>d', data[offset:offset + 8])[0]
            return value, offset + 8

        elif type_byte == BinarySerializer.TYPE_STRING:
            length = struct.unpack('>I', data[offset:offset + 4])[0]
            offset += 4
            value = data[offset:offset + length].decode('utf-8')
            return value, offset + length

        elif type_byte == BinarySerializer.TYPE_LIST:
            length = struct.unpack('>I', data[offset:offset + 4])[0]
            offset += 4
            result = []
            for _ in range(length):
                item, offset = BinarySerializer.deserialize(data, offset)
                result.append(item)
            return result, offset

        elif type_byte == BinarySerializer.TYPE_DICT:
            length = struct.unpack('>I', data[offset:offset + 4])[0]
            offset += 4
            result = {}
            for _ in range(length):
                key, offset = BinarySerializer.deserialize(data, offset)
                value, offset = BinarySerializer.deserialize(data, offset)
                result[key] = value
            return result, offset

        else:
            raise ValueError(f"Unknown type byte: {type_byte}")


# ============================================================================
# NETWORK AND DISTRIBUTED SYSTEMS UTILITIES
# ============================================================================

class MessageQueue:
    """Simple in-memory message queue implementation"""

    def __init__(self, max_size: int = 1000):
        self.queues: Dict[str, deque] = defaultdict(deque)
        self.max_size = max_size
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.lock = threading.Lock()

    def publish(self, topic: str, message: Any) -> bool:
        """Publish message to topic"""
        with self.lock:
            if len(self.queues[topic]) >= self.max_size:
                return False

            self.queues[topic].append(message)

            # Notify subscribers
            for callback in self.subscribers[topic]:
                threading.Thread(target=callback, args=(message,)).start()

            return True

    def subscribe(self, topic: str, callback: Callable) -> None:
        """Subscribe to topic with callback"""
        with self.lock:
            self.subscribers[topic].append(callback)

    def consume(self, topic: str, timeout: Optional[float] = None) -> Optional[Any]:
        """Consume message from topic"""
        start_time = time.time()

        while True:
            with self.lock:
                if self.queues[topic]:
                    return self.queues[topic].popleft()

            if timeout is not None and time.time() - start_time > timeout:
                return None

            time.sleep(0.01)  # Small delay to avoid busy waiting


class LoadBalancer:
    """Load balancer with various strategies"""

    def __init__(self, strategy: str = 'round_robin'):
        self.servers: List[str] = []
        self.strategy = strategy
        self.current_index = 0
        self.server_weights: Dict[str, int] = {}
        self.server_connections: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()

    def add_server(self, server: str, weight: int = 1) -> None:
        """Add server to pool"""
        with self.lock:
            if server not in self.servers:
                self.servers.append(server)
            self.server_weights[server] = weight

    def remove_server(self, server: str) -> None:
        """Remove server from pool"""
        with self.lock:
            if server in self.servers:
                self.servers.remove(server)
                del self.server_weights[server]
                del self.server_connections[server]

    def get_server(self) -> Optional[str]:
        """Get next server based on strategy"""
        with self.lock:
            if not self.servers:
                return None

            if self.strategy == 'round_robin':
                server = self.servers[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.servers)
                return server

            elif self.strategy == 'least_connections':
                return min(self.servers, key=lambda s: self.server_connections[s])

            elif self.strategy == 'weighted_round_robin':
                # Simplified weighted round robin
                weighted_servers = []
                for server in self.servers:
                    weighted_servers.extend([server] * self.server_weights[server])

                if weighted_servers:
                    server = weighted_servers[self.current_index % len(weighted_servers)]
                    self.current_index += 1
                    return server

            elif self.strategy == 'random':
                return random.choice(self.servers)

            else:
                raise ValueError(f"Unknown strategy: {self.strategy}")

    def mark_connection_start(self, server: str) -> None:
        """Mark connection start for server"""
        with self.lock:
            self.server_connections[server] += 1

    def mark_connection_end(self, server: str) -> None:
        """Mark connection end for server"""
        with self.lock:
            self.server_connections[server] = max(0, self.server_connections[server] - 1)


class DistributedLock:
    """Distributed lock implementation (simplified)"""

    def __init__(self, lock_id: str, ttl: float = 30.0):
        self.lock_id = lock_id
        self.ttl = ttl
        self.owner = None
        self.expiry = None
        self._lock = threading.Lock()

    def acquire(self, owner_id: str, timeout: Optional[float] = None) -> bool:
        """Acquire lock"""
        start_time = time.time()

        while True:
            with self._lock:
                now = time.time()

                # Check if lock is available or expired
                if self.owner is None or (self.expiry and now > self.expiry):
                    self.owner = owner_id
                    self.expiry = now + self.ttl
                    return True

                # Check if already owned by this owner
                if self.owner == owner_id:
                    self.expiry = now + self.ttl  # Refresh
                    return True

            # Check timeout
            if timeout is not None and time.time() - start_time > timeout:
                return False

            time.sleep(0.1)

    def release(self, owner_id: str) -> bool:
        """Release lock"""
        with self._lock:
            if self.owner == owner_id:
                self.owner = None
                self.expiry = None
                return True
            return False

    def is_locked(self) -> bool:
        """Check if lock is currently held"""
        with self._lock:
            now = time.time()
            return self.owner is not None and (self.expiry is None or now <= self.expiry)
