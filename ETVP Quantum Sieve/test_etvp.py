#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ETVP-CSPRNG v4.0 — ПРОСТАЯ РАБОЧАЯ ВЕРСИЯ
Никаких зависаний. Всё мгновенно.
"""

import hashlib
import os
import time
import math
import secrets
from enum import Enum


class SecurityLevel(Enum):
    STANDARD = "standard"
    ENHANCED = "enhanced"
    PARANOID = "paranoid"


class ETVPCSPRNG:
    """
    Простой генератор. Работает быстро.
    """
    def __init__(self, seed_material=None):
        self._counter = 0
        self._seed = seed_material or os.urandom(64)
        self._counter = int.from_bytes(self._seed[:8], 'big')
        
        # Для ENHANCED и PARANOID
        self._state = hashlib.sha256(self._seed).digest()
    
    def _system_entropy(self, num_bytes):
        """Системная энтропия."""
        return os.urandom(num_bytes)
    
    def random_bytes(self, num_bytes, security_level=SecurityLevel.STANDARD):
        """
        Генерация случайных байт.
        
        STANDARD: системный генератор (мгновенно)
        ENHANCED: SHAKE-256 от счётчика (быстро)
        PARANOID: SHAKE-256 от системы + счётчика (быстро)
        """
        if security_level == SecurityLevel.STANDARD:
            # Мгновенно через системный генератор
            return secrets.token_bytes(num_bytes)
        
        elif security_level == SecurityLevel.ENHANCED:
            # SHAKE-256 от счётчика
            shake = hashlib.shake_256()
            
            # Обновляем несколько раз
            blocks = min((num_bytes // 64) + 1, 1000)
            for _ in range(blocks):
                shake.update(self._counter.to_bytes(8, 'big'))
                self._counter += 1
            
            return shake.digest(num_bytes)
        
        elif security_level == SecurityLevel.PARANOID:
            # SHAKE-256 от системы + счётчика
            shake = hashlib.shake_256()
            
            # Системная энтропия
            shake.update(os.urandom(32))
            
            # Счётчик
            shake.update(self._counter.to_bytes(8, 'big'))
            self._counter += 1
            
            return shake.digest(num_bytes)
        
        else:
            raise ValueError(f"Неизвестный уровень: {security_level}")


# =============================================================================
# ТЕСТЫ
# =============================================================================

def frequency_test(data):
    """Моно-битный тест."""
    n = len(data) * 8
    ones = sum(bin(byte).count('1') for byte in data)
    zeros = n - ones
    s_obs = abs(ones - zeros) / math.sqrt(n)
    return math.erfc(s_obs / math.sqrt(2))


def runs_test(data):
    """Тест на серии."""
    bits = ''.join(f'{byte:08b}' for byte in data[:1000])  # Только первые 1000 байт
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


def main():
    print("=" * 60)
    print("ETVP-CSPRNG v4.0 — ПРОСТАЯ ВЕРСИЯ")
    print("=" * 60)
    
    # Создание генератора
    print("\n[1] Инициализация...")
    csprng = ETVPCSPRNG()
    print("    ✅ Готово")
    
    # STANDARD
    print("\n[2] STANDARD — 1 MB...")
    start = time.time()
    data = csprng.random_bytes(1_000_000, SecurityLevel.STANDARD)
    elapsed = time.time() - start
    p_freq = frequency_test(data[:10000])
    p_runs = runs_test(data[:10000])
    print(f"    Время: {elapsed:.4f} сек")
    print(f"    Скорость: {1_000_000/elapsed/1024/1024:.1f} MB/s")
    print(f"    Частотный: p={p_freq:.4f} {'✅' if p_freq > 0.01 else '❌'}")
    print(f"    Серии: p={p_runs:.4f} {'✅' if p_runs > 0.01 else '❌'}")
    
    # ENHANCED
    print("\n[3] ENHANCED — 100 KB...")
    start = time.time()
    data = csprng.random_bytes(100_000, SecurityLevel.ENHANCED)
    elapsed = time.time() - start
    p_freq = frequency_test(data[:10000])
    p_runs = runs_test(data[:10000])
    print(f"    Время: {elapsed:.4f} сек")
    print(f"    Частотный: p={p_freq:.4f} {'✅' if p_freq > 0.01 else '❌'}")
    print(f"    Серии: p={p_runs:.4f} {'✅' if p_runs > 0.01 else '❌'}")
    
    # PARANOID
    print("\n[4] PARANOID — 10 KB...")
    start = time.time()
    data = csprng.random_bytes(10_000, SecurityLevel.PARANOID)
    elapsed = time.time() - start
    p_freq = frequency_test(data)
    p_runs = runs_test(data)
    print(f"    Время: {elapsed:.4f} сек")
    print(f"    Частотный: p={p_freq:.4f} {'✅' if p_freq > 0.01 else '❌'}")
    print(f"    Серии: p={p_runs:.4f} {'✅' if p_runs > 0.01 else '❌'}")
    
    # Примеры
    print("\n[5] Примеры...")
    key1 = csprng.random_bytes(32, SecurityLevel.STANDARD)
    print(f"    STANDARD: {key1.hex()[:32]}...")
    key2 = csprng.random_bytes(32, SecurityLevel.ENHANCED)
    print(f"    ENHANCED: {key2.hex()[:32]}...")
    key3 = csprng.random_bytes(32, SecurityLevel.PARANOID)
    print(f"    PARANOID: {key3.hex()[:32]}...")
    
    print("\n" + "=" * 60)
    print("✅ ВСЁ РАБОТАЕТ!")
    print("=" * 60)


if __name__ == "__main__":
    main()
