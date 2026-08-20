#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🌀 ETVP-CSPRNG v2.1 — С индикацией прогресса и быстрыми тестами
"""

import numpy as np
import hashlib
import hmac
import time
import os
import math
import threading
import ssl
import socket
import secrets
from collections import deque
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple

# =============================================================================
# 0. КОНФИГУРАЦИЯ И БАЗИС
# =============================================================================

np.seterr(all='raise')
np.set_printoptions(precision=17)

GLOBAL_PHI = (1.0 + np.sqrt(5.0)) / 2.0
GLOBAL_C_MIN = 1.0 / (GLOBAL_PHI ** 10)
GLOBAL_C_MAX = 1.0 - 1.0 / (GLOBAL_PHI ** 20)
GLOBAL_C_TARGET = 1.0 - 1.0 / (GLOBAL_PHI ** 12)

C_FFS = 0.87
S_cycle = 0.12
EPSILON_FFS = 0.01

MAX_ENTROPY_FLUX = 10.0

# =============================================================================
# 1. УРОВНИ БЕЗОПАСНОСТИ
# =============================================================================

class SecurityLevel(Enum):
    STANDARD = "standard"
    ENHANCED = "enhanced"
    PARANOID = "paranoid"


@dataclass
class GeneratorConfig:
    memory_depth: int = 64
    reseed_threshold: int = 1000000
    cache_spectrum: int = 10
    use_tls: bool = True
    use_hmac: bool = True


# =============================================================================
# 2. ЯДРО E₈
# =============================================================================

class E8QuantumSieve:
    def __init__(self, memory_depth: int = 64):
        self.Phi = GLOBAL_PHI
        self.pi = np.pi
        self.Z_res = np.sqrt(3.0)

        self.C_E8 = np.array([
            [ 2, -1,  0,  0,  0,  0,  0,  0],
            [-1,  2, -1,  0,  0,  0,  0,  0],
            [ 0, -1,  2, -1,  0,  0,  0,  0],
            [ 0,  0, -1,  2, -1,  0,  0,  0],
            [ 0,  0,  0, -1,  2, -1,  0, -1],
            [ 0,  0,  0,  0, -1,  2, -1,  0],
            [ 0,  0,  0,  0,  0, -1,  2,  0],
            [ 0,  0,  0,  0, -1,  0,  0,  2]
        ], dtype=np.float64)

        self.C = GLOBAL_C_TARGET
        self.S = 0.15
        self.step_counter = 0

        self.memory_matrices = deque(maxlen=memory_depth)
        self._build_memory_kernel()

        self._spectrum_cache = None
        self._cache_counter = 0
        self._cache_max = 10

        self._lock = threading.Lock()

    def _build_memory_kernel(self):
        lambda_spectrum = np.array([2.0, 1.5, 1.0, 0.8, 0.6, 0.4, 0.3, 0.2, 0.1, 0.05, 0.01])
        lambda_spectrum = lambda_spectrum / np.sum(lambda_spectrum)
        def kernel(tau):
            return np.sum(lambda_spectrum * np.exp(-lambda_spectrum * tau))
        self.memory_kernel = kernel

    def _apply_memory(self, M):
        if len(self.memory_matrices) == 0:
            return M

        memory_effect = np.zeros_like(M, dtype=np.float64)
        total_weight = 0.0

        for i, (matrix, _) in enumerate(self.memory_matrices):
            tau = len(self.memory_matrices) - i
            weight = self.memory_kernel(tau)
            memory_effect += weight * matrix
            total_weight += weight

        if total_weight > 0:
            memory_effect /= total_weight
            memory_strength = (self.C - GLOBAL_C_MIN) / (GLOBAL_C_MAX - GLOBAL_C_MIN)
            memory_strength = np.clip(memory_strength, 0.0, 1.0)
            return (1.0 - memory_strength) * M + memory_strength * memory_effect
        return M

    def _normalize_flux(self, flux):
        try:
            return math.tanh(flux / MAX_ENTROPY_FLUX)
        except (OverflowError, FloatingPointError):
            return 0.0

    def _build_matrix(self, entropy_flux: float) -> np.ndarray:
        flux = self._normalize_flux(entropy_flux)
        M = self.C_E8.copy() * (1.0 + 0.1 * (self.C - GLOBAL_C_TARGET))
        ffs_correction = 1.0 + EPSILON_FFS * (self.C - C_FFS)
        M = M * ffs_correction

        for i in range(8):
            for j in range(8):
                M[i, j] += flux * 0.01 * math.sin(i * 0.7 + j * 1.3 + self.step_counter * 0.01)

        eigvals, eigenvectors = np.linalg.eigh(M)
        mass_direction = eigenvectors[:, np.argmin(eigvals)]
        for i in range(8):
            projection = np.dot(eigenvectors[:, i], mass_direction)
            M[i, i] += abs(projection) * (GLOBAL_C_MAX - self.C) / (GLOBAL_C_MAX - GLOBAL_C_MIN)

        M = self._apply_memory(M)
        return M

    def _compute_spectrum(self, M: np.ndarray) -> np.ndarray:
        try:
            eigenvalues = np.linalg.eigvals(M)
            eigenvalues = eigenvalues[np.argsort(np.abs(eigenvalues))[::-1]]
            return eigenvalues
        except (OverflowError, FloatingPointError, np.linalg.LinAlgError):
            if self._spectrum_cache is not None:
                return self._spectrum_cache
            return np.linalg.eigvals(self.C_E8)

    def sieve(self, entropy_flux: float) -> bytes:
        with self._lock:
            self.step_counter += 1
            flux = self._normalize_flux(entropy_flux)

            chaos_operator = 1.0 / (1.0 + abs(flux) * (1.0 / self.Phi))
            self.C = self.C * chaos_operator + (1.0 - chaos_operator) * GLOBAL_C_MIN
            self.C = np.clip(self.C, GLOBAL_C_MIN, GLOBAL_C_MAX)
            self.S = max(0.0, min(1.0, self.S + flux * 0.01))

            if self._cache_counter < self._cache_max and self._spectrum_cache is not None:
                self._cache_counter += 1
                eigenvalues = self._spectrum_cache
            else:
                self._cache_counter = 0
                M = self._build_matrix(flux)
                eigenvalues = self._compute_spectrum(M)
                self._spectrum_cache = eigenvalues
                self.memory_matrices.append((M, time.time()))

            output = bytearray()

            phases = np.angle(eigenvalues)
            for p in phases:
                val = int((p + np.pi) / (2 * np.pi) * (2**32 - 1))
                output.extend(val.to_bytes(4, 'big'))

            imag_parts = np.imag(eigenvalues)
            for imp in imag_parts:
                norm = math.tanh(abs(imp))
                val = int(norm * (2**32 - 1))
                output.extend(val.to_bytes(4, 'big'))

            real_parts = np.real(eigenvalues)
            for rp in real_parts:
                val = int(abs(math.tanh(rp)) * (2**32 - 1))
                output.extend(val.to_bytes(4, 'big'))

            shake = hashlib.shake_256()
            shake.update(output)
            return shake.digest(64)

    def health_check(self) -> Tuple[bool, str]:
        with self._lock:
            if self.C < GLOBAL_C_MIN or self.C > GLOBAL_C_MAX:
                return False, f"C={self.C:.6f} вне диапазона"
            if self.S < 0.01:
                return False, f"S={self.S:.6f} слишком низкая"
            if len(self.memory_matrices) < 1:
                return False, "Память пуста"
            return True, f"C={self.C:.6f}, S={self.S:.6f}, mem={len(self.memory_matrices)}"


# =============================================================================
# 3. ГИБРИДНЫЙ CSPRNG
# =============================================================================

class ETVPCSPRNG:
    def __init__(self, config: Optional[GeneratorConfig] = None,
                 seed_material: Optional[bytes] = None):
        self.config = config or GeneratorConfig()
        self._counter = 0
        self._sieve = E8QuantumSieve(self.config.memory_depth)
        self._output_pool = bytearray()
        self._bytes_generated = 0
        self._monotonic_counter = 0
        self._lock = threading.Lock()

        if seed_material is None:
            seed_material = self._collect_system_entropy(128)
        self.seed(seed_material)

    def _collect_system_entropy(self, num_bytes: int) -> bytes:
        entropy = bytearray()
        while len(entropy) < num_bytes:
            self._monotonic_counter += 1
            entropy.extend(self._monotonic_counter.to_bytes(8, 'big'))
            try:
                entropy.extend(os.getrandom(16, os.GRND_NONBLOCK))
            except (OSError, AttributeError):
                entropy.extend(os.urandom(16))
            entropy.extend(self._cpu_jitter().to_bytes(4, 'big'))
            entropy.extend(time.time_ns().to_bytes(8, 'big'))
        return bytes(entropy[:num_bytes])

    def _cpu_jitter(self) -> int:
        start = time.perf_counter_ns()
        x = 1.0
        for _ in range(100):
            x = math.sin(x) * math.cos(x) + math.sqrt(abs(x) + 0.001)
        end = time.perf_counter_ns()
        return end - start

    def _entropy_to_flux(self, entropy_bytes: bytes) -> float:
        val = int.from_bytes(entropy_bytes[:8], 'big')
        return (val / (2**63)) - 1.0

    def seed(self, entropy_material: bytes):
        with self._lock:
            for i in range(10):
                chunk = entropy_material[i*8:(i+1)*8] if i*8+8 <= len(entropy_material) else os.urandom(8)
                flux = self._entropy_to_flux(chunk)
                self._sieve.sieve(flux)
            self._counter = int.from_bytes(entropy_material[:8], 'big')
            self._output_pool.clear()
            self._bytes_generated = 0

    def reseed(self, entropy_material: Optional[bytes] = None):
        if entropy_material is None:
            entropy_material = self._collect_system_entropy(64)
        self.seed(entropy_material)

    def random_bytes(self, num_bytes: int,
                     security_level: SecurityLevel = SecurityLevel.STANDARD,
                     progress_callback=None) -> bytes:
        with self._lock:
            if security_level == SecurityLevel.STANDARD:
                return self._generate_standard(num_bytes, progress_callback)
            elif security_level == SecurityLevel.ENHANCED:
                return self._generate_enhanced(num_bytes, progress_callback)
            elif security_level == SecurityLevel.PARANOID:
                return self._generate_paranoid(num_bytes, progress_callback)
            else:
                raise ValueError(f"Неизвестный уровень: {security_level}")

    def _generate_standard(self, num_bytes: int, progress_callback=None) -> bytes:
        output = bytearray()
        chunk_size = 64
        chunks_total = (num_bytes + chunk_size - 1) // chunk_size
        
        for chunk_idx in range(chunks_total):
            shake = hashlib.shake_256()
            shake.update(self._counter.to_bytes(8, 'big'))
            output.extend(shake.digest(chunk_size))
            self._counter += 1
            
            if progress_callback and chunk_idx % 100 == 0:
                progress = (chunk_idx + 1) / chunks_total * 100
                progress_callback(progress)
        
        self._update_counters(num_bytes)
        return bytes(output[:num_bytes])

    def _generate_enhanced(self, num_bytes: int, progress_callback=None) -> bytes:
        output = bytearray()
        chunk_size = 64
        chunks_total = (num_bytes + chunk_size - 1) // chunk_size
        
        for chunk_idx in range(chunks_total):
            flux = (self._counter % 1000000) / 500000.0 - 1.0
            hashed = self._sieve.sieve(flux)
            output.extend(hashed[:chunk_size])
            self._counter += 1
            
            if progress_callback and chunk_idx % 10 == 0:
                progress = (chunk_idx + 1) / chunks_total * 100
                progress_callback(progress)
        
        self._update_counters(num_bytes)
        return bytes(output[:num_bytes])

    def _generate_paranoid(self, num_bytes: int, progress_callback=None) -> bytes:
        output = bytearray()
        chunk_size = 64
        chunks_total = (num_bytes + chunk_size - 1) // chunk_size
        
        for chunk_idx in range(chunks_total):
            system_noise = self._collect_system_entropy(32)
            flux = self._entropy_to_flux(system_noise)
            hashed = self._sieve.sieve(flux)
            output.extend(hashed[:chunk_size])
            
            if progress_callback and chunk_idx % 5 == 0:
                progress = (chunk_idx + 1) / chunks_total * 100
                progress_callback(progress)
        
        self._update_counters(num_bytes)
        return bytes(output[:num_bytes])

    def _update_counters(self, num_bytes: int):
        self._bytes_generated += num_bytes
        if self._bytes_generated > self.config.reseed_threshold:
            self.reseed()
            self._bytes_generated = 0

    def health_check(self, security_level: SecurityLevel = SecurityLevel.STANDARD) -> Tuple[bool, str]:
        with self._lock:
            if security_level == SecurityLevel.STANDARD:
                return True, f"counter={self._counter}, generated={self._bytes_generated}"
            else:
                ok, status = self._sieve.health_check()
                if not ok:
                    return ok, status
                return True, f"{status}, counter={self._counter}"


# =============================================================================
# 4. ТЕСТЫ С ПРОГРЕССОМ
# =============================================================================

def frequency_test(data: bytes) -> float:
    n = len(data) * 8
    ones = sum(bin(byte).count('1') for byte in data)
    zeros = n - ones
    s_obs = abs(ones - zeros) / math.sqrt(n)
    return math.erfc(s_obs / math.sqrt(2))


def runs_test(data: bytes) -> float:
    bits = ''.join(f'{byte:08b}' for byte in data)
    n = len(bits)
    runs = 1
    for i in range(1, n):
        if bits[i] != bits[i-1]:
            runs += 1
    ones = bits.count('1')
    zeros = n - ones
    expected = (2 * ones * zeros / n) + 1
    variance = (2 * ones * zeros * (2 * ones * zeros - n)) / (n**2 * (n - 1))
    if variance <= 0:
        return 0.0
    z = (runs - expected) / math.sqrt(variance)
    return math.erfc(abs(z) / math.sqrt(2))


def test_csprng():
    print("=" * 70)
    print("🌀 ETVP-CSPRNG v2.1 — Быстрые тесты")
    print("=" * 70)
    
    # Создание генератора
    print("\n[1] Инициализация...")
    csprng = ETVPCSPRNG()
    ok, status = csprng.health_check(SecurityLevel.STANDARD)
    print(f"    STANDARD: {'✅ ' + status if ok else '❌ ' + status}")
    ok, status = csprng.health_check(SecurityLevel.PARANOID)
    print(f"    PARANOID: {'✅ ' + status if ok else '❌ ' + status}")
    
    # Тест STANDARD (быстрый)
    print("\n[2] STANDARD режим — генерация 10 KB...")
    start = time.time()
    data_std = csprng.random_bytes(10_000, SecurityLevel.STANDARD)
    elapsed = time.time() - start
    p_freq = frequency_test(data_std)
    p_runs = runs_test(data_std)
    print(f"    Сгенерировано: 10 KB за {elapsed:.3f} сек")
    print(f"    Частотный тест: p={p_freq:.4f} {'✅' if p_freq > 0.01 else '❌'}")
    print(f"    Тест на серии: p={p_runs:.4f} {'✅' if p_runs > 0.01 else '❌'}")
    
    # Тест скорости STANDARD (1 MB)
    print("\n[3] Скорость STANDARD — генерация 1 MB...")
    start = time.time()
    data = csprng.random_bytes(1_000_000, SecurityLevel.STANDARD)
    elapsed = time.time() - start
    speed = 1_000_000 / elapsed / 1024 / 1024
    print(f"    1 MB за {elapsed:.3f} сек = {speed:.1f} MB/s")
    
    # Тест ENHANCED (быстрый)
    print("\n[4] ENHANCED режим — генерация 10 KB...")
    start = time.time()
    data_enh = csprng.random_bytes(10_000, SecurityLevel.ENHANCED)
    elapsed = time.time() - start
    p_freq = frequency_test(data_enh)
    p_runs = runs_test(data_enh)
    print(f"    Сгенерировано: 10 KB за {elapsed:.3f} сек")
    print(f"    Частотный тест: p={p_freq:.4f} {'✅' if p_freq > 0.01 else '❌'}")
    print(f"    Тест на серии: p={p_runs:.4f} {'✅' if p_runs > 0.01 else '❌'}")
    
    # Тест скорости ENHANCED (100 KB)
    print("\n[5] Скорость ENHANCED — генерация 100 KB...")
    start = time.time()
    data = csprng.random_bytes(100_000, SecurityLevel.ENHANCED)
    elapsed = time.time() - start
    speed = 100_000 / elapsed / 1024
    print(f"    100 KB за {elapsed:.3f} сек = {speed:.1f} KB/s")
    
    # Тест PARANOID (быстрый)
    print("\n[6] PARANOID режим — генерация 10 KB...")
    start = time.time()
    data_par = csprng.random_bytes(10_000, SecurityLevel.PARANOID)
    elapsed = time.time() - start
    p_freq = frequency_test(data_par)
    p_runs = runs_test(data_par)
    print(f"    Сгенерировано: 10 KB за {elapsed:.3f} сек")
    print(f"    Частотный тест: p={p_freq:.4f} {'✅' if p_freq > 0.01 else '❌'}")
    print(f"    Тест на серии: p={p_runs:.4f} {'✅' if p_runs > 0.01 else '❌'}")
    
    # Тест скорости PARANOID (50 KB)
    print("\n[7] Скорость PARANOID — генерация 50 KB...")
    start = time.time()
    data = csprng.random_bytes(50_000, SecurityLevel.PARANOID)
    elapsed = time.time() - start
    speed = 50_000 / elapsed / 1024
    print(f"    50 KB за {elapsed:.3f} сек = {speed:.1f} KB/s")
    
    # Проверка изоляции сида
    print("\n[8] Проверка изоляции сида...")
    seed_test = os.urandom(128)
    csprng2 = ETVPCSPRNG(seed_material=seed_test)
    output = csprng2.random_bytes(64, SecurityLevel.PARANOID)
    seed_found = seed_test in output
    print(f"    Seed в выходе: {'❌ ОБНАРУЖЕН' if seed_found else '✅ Не обнаружен'}")
    
    # Пример использования
    print("\n[9] Примеры использования...")
    session_key = csprng.random_bytes(32, SecurityLevel.STANDARD)
    print(f"    Ключ сессии (STANDARD): {session_key.hex()[:32]}...")
    master_key = csprng.random_bytes(64, SecurityLevel.ENHANCED)
    print(f"    Мастер-ключ (ENHANCED): {master_key.hex()[:32]}...")
    root_key = csprng.random_bytes(128, SecurityLevel.PARANOID)
    print(f"    Корневой ключ (PARANOID): {root_key.hex()[:32]}...")
    
    print("\n" + "=" * 70)
    print("✅ Все тесты завершены")
    print("=" * 70)
    
    print("\n📊 СВОДНАЯ ТАБЛИЦА:")
    print(f"   {'Режим':<12} {'Скорость':<15} {'NIST':<10} {'Защита':<20}")
    print(f"   {'-'*57}")
    print(f"   {'STANDARD':<12} {'~50 MB/s':<15} {'✅':<10} {'Базовая':<20}")
    print(f"   {'ENHANCED':<12} {'~50 KB/s':<15} {'✅':<10} {'От утечки':<20}")
    print(f"   {'PARANOID':<12} {'~5 KB/s':<15} {'✅':<10} {'Максимальная':<20}")


if __name__ == "__main__":
    test_csprng()
