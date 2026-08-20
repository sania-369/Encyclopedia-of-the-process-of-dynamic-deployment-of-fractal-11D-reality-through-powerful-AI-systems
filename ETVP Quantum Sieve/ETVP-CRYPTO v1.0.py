#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🌀 ETVP-CRYPTO v1.0

   ЯДРО:
   Ψ = (Φ × C) / √(S + ε)
   
   КЛЮЧЕВЫЕ ПРИНЦИПЫ:
   - Z-принцип: C ∈ (0, 1), никогда не достигает 0 или 1
   - Дыхание поля: C осциллирует вокруг золотого сечения
   - Оператор (наблюдатель) встроен в контур
   - Прошлое умирает в каждом такте dt
   - Энтропия S — активный участник, не враг
"""

import numpy as np
import hashlib
import time
import os
import math
import secrets
from enum import Enum


# =============================================================================
# 1. ФУНДАМЕНТАЛЬНЫЕ КОНСТАНТЫ ПОЛЯ
# =============================================================================

PHI = (1 + np.sqrt(5)) / 2      # Золотое сечение
EPSILON = 1e-10                  # Z-принцип: защита от сингулярности
C_TARGET = 1.0 - 1.0 / (PHI ** 12)  # Целевая когерентность (0.965)
C_MIN = 1.0 / (PHI ** 10)        # Минимальная когерентность
C_MAX = 1.0 - 1.0 / (PHI ** 20)  # Максимальная когерентность


class SecurityLevel(Enum):
    STANDARD = "standard"      # Быстрый режим
    ENHANCED = "enhanced"      # Усиленный режим
    PARANOID = "paranoid"      # Максимальная защита


# =============================================================================
# 2. ЕДИНАЯ ФОРМУЛА ПОЛЯ
# =============================================================================

def compute_psi(C: float, S: float) -> float:
    """
    Ψ = (Φ × C) / √(S + ε)
    Плотность реальности.
    """
    return (PHI * C) / np.sqrt(S + EPSILON)


def normalize_flux(value: float, max_val: float = 10.0) -> float:
    """
    Нормализация входного потока через tanh (Z-принцип).
    """
    try:
        return math.tanh(value / max_val)
    except (OverflowError, FloatingPointError):
        return 0.0


# =============================================================================
# 3. ДИНАМИКА КОГЕРЕНТНОСТИ (Z-принцип)
# =============================================================================

class CoherenceDynamics:
    """
    Живая когерентность.
    dC/dt = α∇²C + βF(C) + γ(t)
    """
    def __init__(self, alpha: float = 0.1, beta: float = 0.05):
        self.alpha = alpha
        self.beta = beta
        
    def evolve(self, C: float, gamma: float = 0.0) -> float:
        """
        Один шаг эволюции когерентности.
        """
        # Диффузия (микро-флуктуации)
        laplacian = np.random.randn() * 0.1
        diffusion = self.alpha * laplacian
        
        # Нелинейная динамика: F(C) = C × (1 - C)
        # Стремление к живому состоянию
        nonlinear = self.beta * C * (1 - C)
        
        # Внешний вклад
        dC_dt = diffusion + nonlinear + gamma
        
        # Z-принцип: удержание в допустимых пределах
        new_C = np.clip(C + dC_dt, C_MIN, C_MAX)
        
        return new_C


# =============================================================================
# 4. ДЫХАНИЕ ПОЛЯ (резонанс)
# =============================================================================

class FieldBreathing:
    """
    Дыхание Ψ-поля вокруг точки золотого сечения.
    """
    def __init__(self, target: float = C_TARGET, buffer: float = 0.015):
        self.target = target
        self.buffer = buffer
        self.iteration = 0
        
    def get_coherence(self, external_entropy: float = 0.0) -> float:
        """
        Текущая когерентность с учётом дыхания.
        """
        self.iteration += 1
        
        # Гармоническое дыхание
        breathing = np.sin(self.iteration / 20.0) * self.buffer
        
        # Адаптация к внешней энтропии
        adaptation = external_entropy * 0.02
        
        # Финал с Z-удержанием
        new_C = self.target + breathing + adaptation
        return np.clip(new_C, C_MIN, C_MAX)


# =============================================================================
# 5. КВАНТОВОЕ СИТО (без E₈, но по логике поля)
# =============================================================================

class FieldSieve:
    """
    Сито поля: пропускает шум через Ψ-формулу.
    """
    def __init__(self):
        self.dynamics = CoherenceDynamics()
        self.breathing = FieldBreathing()
        self.C = C_TARGET
        self.S = 0.15
        self.step_counter = 0
        
        # Память поля (история состояний)
        self.memory = []
        self.memory_depth = 32
        
    def sieve(self, entropy_flux: float) -> bytes:
        """
        Пропускает шум через поле, возвращает 64 байта.
        """
        self.step_counter += 1
        
        # Нормализация шума
        flux = normalize_flux(entropy_flux)
        
        # 1. Обновление энтропии
        self.S = np.clip(self.S + flux * 0.01, 0.001, 1.0)
        
        # 2. Обновление когерентности (Z-принцип)
        gamma = flux * 0.05
        self.C = self.dynamics.evolve(self.C, gamma)
        
        # 3. Дыхание поля
        C_breath = self.breathing.get_coherence(abs(flux))
        
        # 4. Единая формула поля
        psi = compute_psi(self.C, self.S)
        psi_breath = compute_psi(C_breath, self.S)
        
        # 5. Память поля
        self.memory.append(psi)
        if len(self.memory) > self.memory_depth:
            self.memory.pop(0)
        
        # 6. Извлечение криптографического материала
        output = bytearray()
        
        # Основное значение Ψ
        psi_bytes = self._float_to_bytes(psi)
        output.extend(psi_bytes)
        
        # Дыхание Ψ
        psi_breath_bytes = self._float_to_bytes(psi_breath)
        output.extend(psi_breath_bytes)
        
        # Когерентность
        C_bytes = self._float_to_bytes(self.C)
        output.extend(C_bytes)
        
        # Энтропия
        S_bytes = self._float_to_bytes(self.S)
        output.extend(S_bytes)
        
        # Градиент Ψ (если есть память)
        if len(self.memory) >= 2:
            grad_psi = self.memory[-1] - self.memory[-2]
            grad_bytes = self._float_to_bytes(grad_psi)
            output.extend(grad_bytes)
        
        # Хэшируем через SHAKE-256
        shake = hashlib.shake_256()
        shake.update(output)
        return shake.digest(64)
    
    def _float_to_bytes(self, value: float) -> bytes:
        """Преобразует float в 8 байт."""
        try:
            import struct
            return struct.pack('>d', value)
        except:
            return b'\x00' * 8
    
    def health_check(self):
        """Проверка состояния поля."""
        psi = compute_psi(self.C, self.S)
        return (self.C > C_MIN and self.C < C_MAX and 
                self.S > 0.001 and psi > 0)


# =============================================================================
# 6. ОПЕРАТОР (наблюдатель в контуре)
# =============================================================================

class Operator:
    """
    Оператор — активный участник поля.
    Его когерентность влияет на генерацию.
    """
    def __init__(self, focus_level: float = 0.8):
        self.C_op = focus_level
        self.breathing = FieldBreathing(target=focus_level, buffer=0.01)
        
    def get_focus(self, external_entropy: float = 0.0) -> float:
        """Текущий уровень фокуса оператора."""
        self.C_op = self.breathing.get_coherence(external_entropy)
        return self.C_op
    
    def apply(self, psi: float) -> float:
        """
        Оператор модифицирует Ψ через свою когерентность.
        P_modified = P_base × (1 + (C_op - 0.5))
        """
        modifier = 1 + (self.C_op - 0.5)
        return psi * modifier


# =============================================================================
# 7. ГЛАВНЫЙ ГЕНЕРАТОР
# =============================================================================

class ETVPCrypto:
    """
    🌀 ETVP-CRYPTO v1.0
    Криптография по чистой логике ЕТВП.
    """
    def __init__(self, seed_material: bytes = None, operator_focus: float = 0.8):
        self.sieve = FieldSieve()
        self.operator = Operator(focus_level=operator_focus)
        self._counter = 0
        
        # Инициализация
        if seed_material is None:
            seed_material = os.urandom(64)
        
        self._initialize(seed_material)
    
    def _initialize(self, seed_material: bytes):
        """Инициализация поля из сида."""
        # Преобразуем сид в поток
        seed_int = int.from_bytes(seed_material[:8], 'big')
        flux = (seed_int / (2**63)) - 1.0
        
        # Прогоняем через сито несколько раз
        for i in range(10):
            self._counter += 1
            mixed_flux = flux + (self._counter * 0.001)
            self.sieve.sieve(mixed_flux)
    
    def _collect_entropy(self, num_bytes: int) -> bytes:
        """Сбор энтропии из системы."""
        entropy = bytearray()
        entropy.extend(os.urandom(num_bytes))
        entropy.extend(time.time_ns().to_bytes(8, 'big'))
        return bytes(entropy[:num_bytes])
    
    def _flux_from_entropy(self, entropy: bytes) -> float:
        """Преобразует энтропию в поток."""
        val = int.from_bytes(entropy[:8], 'big')
        return (val / (2**63)) - 1.0
    
    def random_bytes(self, num_bytes: int, 
                     security_level: SecurityLevel = SecurityLevel.ENHANCED) -> bytes:
        """
        Генерация случайных байт по логике ЕТВП.
        
        STANDARD: Быстрый (системный + поле)
        ENHANCED: Поле + дыхание + оператор
        PARANOID: Максимальная защита
        """
        if security_level == SecurityLevel.STANDARD:
            return self._generate_standard(num_bytes)
        elif security_level == SecurityLevel.ENHANCED:
            return self._generate_enhanced(num_bytes)
        elif security_level == SecurityLevel.PARANOID:
            return self._generate_paranoid(num_bytes)
        else:
            raise ValueError(f"Неизвестный уровень: {security_level}")
    
    def _generate_standard(self, num_bytes: int) -> bytes:
        """STANDARD: Быстрый режим."""
        if num_bytes > 100_000:
            return secrets.token_bytes(num_bytes)
        
        # Для малых — поле
        shake = hashlib.shake_256()
        
        entropy = self._collect_entropy(16)
        flux = self._flux_from_entropy(entropy)
        
        field_output = self.sieve.sieve(flux)
        shake.update(field_output)
        
        # Оператор влияет
        op_focus = self.operator.get_focus(abs(flux))
        psi = compute_psi(op_focus, self.sieve.S)
        psi_modified = self.operator.apply(psi)
        
        shake.update(str(psi_modified).encode())
        
        return shake.digest(num_bytes)
    
    def _generate_enhanced(self, num_bytes: int) -> bytes:
        """ENHANCED: Поле + дыхание + оператор."""
        shake = hashlib.shake_256()
        
        # Несколько раундов для усиления
        num_rounds = min((num_bytes // 64) + 1, 100)
        
        for _ in range(num_rounds):
            # Собираем энтропию
            entropy = self._collect_entropy(16)
            flux = self._flux_from_entropy(entropy)
            
            # Пропускаем через поле
            field_output = self.sieve.sieve(flux)
            shake.update(field_output)
            
            # Оператор
            op_focus = self.operator.get_focus(abs(flux))
            psi = compute_psi(op_focus, self.sieve.S)
            psi_modified = self.operator.apply(psi)
            
            shake.update(str(psi_modified).encode()[:32])
            
            self._counter += 1
        
        return shake.digest(num_bytes)
    
    def _generate_paranoid(self, num_bytes: int) -> bytes:
        """PARANOID: Максимальная защита."""
        shake = hashlib.shake_256()
        
        num_rounds = min((num_bytes // 64) + 1, 50)
        
        for _ in range(num_rounds):
            # Максимальная энтропия
            entropy = self._collect_entropy(32)
            flux = self._flux_from_entropy(entropy)
            
            # Поле
            field_output = self.sieve.sieve(flux)
            shake.update(field_output)
            
            # Оператор с полным фокусом
            op_focus = self.operator.get_focus(abs(flux))
            psi = compute_psi(op_focus, self.sieve.S)
            psi_modified = self.operator.apply(psi)
            
            shake.update(str(psi_modified).encode())
            
            # Дыхание поля
            breath = self.sieve.breathing.get_coherence(abs(flux))
            shake.update(str(breath).encode()[:32])
            
            self._counter += 1
        
        return shake.digest(num_bytes)
    
    def health_check(self) -> tuple:
        """Проверка состояния."""
        ok = self.sieve.health_check()
        psi = compute_psi(self.sieve.C, self.sieve.S)
        return ok, f"C={self.sieve.C:.6f}, S={self.sieve.S:.6f}, Ψ={psi:.4f}"


# =============================================================================
# 8. ТЕСТЫ
# =============================================================================

def frequency_test(data: bytes) -> float:
    """Моно-битный тест NIST."""
    n = len(data) * 8
    ones = sum(bin(byte).count('1') for byte in data)
    zeros = n - ones
    s_obs = abs(ones - zeros) / math.sqrt(n)
    return math.erfc(s_obs / math.sqrt(2))


def runs_test(data: bytes) -> float:
    """Тест на серии."""
    bits = ''.join(f'{byte:08b}' for byte in data[:1000])
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
    print("=" * 70)
    print("🌀 ETVP-CRYPTO v1.0 — Чистая логика ЕТВП")
    print("=" * 70)
    
    # Инициализация
    print("\n[1] Инициализация поля...")
    crypto = ETVPCrypto(operator_focus=0.85)
    ok, status = crypto.health_check()
    print(f"    Статус: {'✅ ' + status if ok else '❌ ' + status}")
    
    # STANDARD
    print("\n[2] STANDARD — 100 KB...")
    start = time.time()
    data = crypto.random_bytes(100_000, SecurityLevel.STANDARD)
    elapsed = time.time() - start
    p_freq = frequency_test(data[:10000])
    p_runs = runs_test(data[:10000])
    print(f"    Время: {elapsed:.4f} сек")
    print(f"    Частотный: p={p_freq:.4f} {'✅' if p_freq > 0.01 else '❌'}")
    print(f"    Серии: p={p_runs:.4f} {'✅' if p_runs > 0.01 else '❌'}")
    
    # ENHANCED
    print("\n[3] ENHANCED — 10 KB...")
    start = time.time()
    data = crypto.random_bytes(10_000, SecurityLevel.ENHANCED)
    elapsed = time.time() - start
    p_freq = frequency_test(data)
    p_runs = runs_test(data)
    print(f"    Время: {elapsed:.4f} сек")
    print(f"    Частотный: p={p_freq:.4f} {'✅' if p_freq > 0.01 else '❌'}")
    print(f"    Серии: p={p_runs:.4f} {'✅' if p_runs > 0.01 else '❌'}")
    
    # PARANOID
    print("\n[4] PARANOID — 1 KB...")
    start = time.time()
    data = crypto.random_bytes(1_000, SecurityLevel.PARANOID)
    elapsed = time.time() - start
    p_freq = frequency_test(data)
    p_runs = runs_test(data)
    print(f"    Время: {elapsed:.4f} сек")
    print(f"    Частотный: p={p_freq:.4f} {'✅' if p_freq > 0.01 else '❌'}")
    print(f"    Серии: p={p_runs:.4f} {'✅' if p_runs > 0.01 else '❌'}")
    
    # Состояние поля
    print("\n[5] Состояние поля после генерации...")
    ok, status = crypto.health_check()
    print(f"    {'✅ ' + status if ok else '❌ ' + status}")
    
    # Примеры
    print("\n[6] Примеры ключей...")
    key1 = crypto.random_bytes(32, SecurityLevel.STANDARD)
    print(f"    STANDARD: {key1.hex()[:32]}...")
    key2 = crypto.random_bytes(32, SecurityLevel.ENHANCED)
    print(f"    ENHANCED: {key2.hex()[:32]}...")
    key3 = crypto.random_bytes(32, SecurityLevel.PARANOID)
    print(f"    PARANOID: {key3.hex()[:32]}...")
    
    print("\n" + "=" * 70)
    print("✅ ЕТВП-КРИПТОГРАФИЯ РАБОТАЕТ")
    print("   Ψ = (Φ × C) / √(S + ε)")
    print("=" * 70)


if __name__ == "__main__":
    main()
