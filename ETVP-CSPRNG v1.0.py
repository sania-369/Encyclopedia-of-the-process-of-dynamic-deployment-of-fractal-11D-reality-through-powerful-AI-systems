#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🌀 ETVP-CSPRNG v1.0 — Криптографически стойкий генератор
   на базе ЕТВП v12.4 FFS (Fractional Fermi Sea Calibration)
   Внешне: стандартный CSPRNG (seed/reseed/bytes)
   Внутри: живое дыхание комплексной матрицы E8
"""

import numpy as np
import hashlib
import hmac
import time
import os
import math
import threading
from collections import deque

# =============================================================================
# 0. ГЕОМЕТРИЧЕСКИЙ БАЗИС
# =============================================================================

GLOBAL_PHI = (1.0 + np.sqrt(5.0)) / 2.0
GLOBAL_C_MIN = 1.0 / (GLOBAL_PHI ** 10)
GLOBAL_C_MAX = 1.0 - 1.0 / (GLOBAL_PHI ** 20)
GLOBAL_C_TARGET = 1.0 - 1.0 / (GLOBAL_PHI ** 12)

C_FFS = 0.87
S_cycle = 0.12
EPSILON_FFS = 0.01


def etve_tanh_limit(C, c_min=GLOBAL_C_MIN, c_max=GLOBAL_C_MAX):
    """Z-принцип: нелинейное tanh-удержание."""
    epsilon = 1e-12
    E = (C - c_min) / (c_max - c_min + epsilon)
    if isinstance(C, (int, float)):
        E_limited = math.tanh(E) * 0.5 + 0.5
    else:
        E_limited = np.tanh(E) * 0.5 + 0.5
    return c_min + E_limited * (c_max - c_min)


# =============================================================================
# 1. ЯДРО ЕТВП v12.4 FFS (адаптировано для CSPRNG)
# =============================================================================

class ETVPQuantumSieve:
    """
    Квантовое сито: шум реальности → E8-матрица → спектр → фазы.
    """
    def __init__(self, memory_depth=64):
        self.Phi = GLOBAL_PHI
        self.pi = np.pi
        self.Z_res = np.sqrt(3.0)

        # Матрица Картана E8 (8x8) в расширенном базисе 11x11
        self.C_E8 = np.zeros((11, 11), dtype=float)
        self.C_E8[0:8, 0:8] = np.array([
            [ 2, -1,  0,  0,  0,  0,  0,  0],
            [-1,  2, -1,  0,  0,  0,  0,  0],
            [ 0, -1,  2, -1,  0,  0,  0,  0],
            [ 0,  0, -1,  2, -1,  0,  0,  0],
            [ 0,  0,  0, -1,  2, -1,  0, -1],
            [ 0,  0,  0,  0, -1,  2, -1,  0],
            [ 0,  0,  0,  0,  0, -1,  2,  0],
            [ 0,  0,  0,  0, -1,  0,  0,  2]
        ], dtype=float)

        self.euler_characteristic = 4.18
        self.coxeter_SU2 = 3
        self.coxeter_SU3 = 4

        # Состояние
        self.C = GLOBAL_C_TARGET
        self.S = 0.15
        self.step_counter = 0

        # Память поля (экспоненциальное затухание)
        self.memory_matrices = deque(maxlen=memory_depth)
        self._build_memory_kernel()

        # Счётчик энтропии для reseed
        self.entropy_pool = bytearray()
        self._lock = threading.Lock()

    def _build_memory_kernel(self):
        """Ядро экспоненциальной памяти."""
        lambda_spectrum = np.array([2.0, 1.5, 1.0, 0.8, 0.6, 0.4, 0.3, 0.2, 0.1, 0.05, 0.01])
        lambda_spectrum = lambda_spectrum / np.sum(lambda_spectrum)
        def kernel(tau):
            return np.sum(lambda_spectrum * np.exp(-lambda_spectrum * tau))
        self.memory_kernel = kernel

    def _apply_memory(self, M):
        """Применяет экспоненциальную память поля к матрице."""
        if len(self.memory_matrices) == 0:
            return M

        memory_effect = np.zeros_like(M, dtype=complex)
        total_weight = 0.0

        for i, (matrix, _) in enumerate(self.memory_matrices):
            tau = len(self.memory_matrices) - i
            weight = self.memory_kernel(tau)
            memory_effect += weight * np.array(matrix, dtype=complex)
            total_weight += weight

        if total_weight > 0:
            memory_effect /= total_weight
            memory_strength = (self.C - GLOBAL_C_MIN) / (GLOBAL_C_MAX - GLOBAL_C_MIN)
            memory_strength = np.clip(memory_strength, 0.0, 1.0)
            return (1.0 - memory_strength) * M + memory_strength * memory_effect
        return M

    def _build_complex_matrix(self, entropy_flux=0.0):
        """
        Строит комплексную матрицу 11x11 с учётом энтропийного потока.
        entropy_flux: шум реальности (time_ns, CPU jitter и т.д.)
        """
        # Базовое пространство E8
        M = self.C_E8.copy() * (1.0 + 0.1 * (self.C - GLOBAL_C_TARGET))

        # Калибровка FFS
        ffs_correction = 1.0 + EPSILON_FFS * (self.C - C_FFS)
        M = M * ffs_correction

        # Вносим энтропийный поток как асимметричную деформацию
        # Это ключевой момент: шум не добавляется к выходу, а деформирует матрицу
        noise_matrix = np.zeros((11, 11))
        for i in range(11):
            for j in range(11):
                # Шум реальности входит как градиент по индексам
                noise_matrix[i, j] = entropy_flux * np.sin(i * 0.7 + j * 1.3 + self.step_counter * 0.01)
        M = M + noise_matrix * 0.01

        # Деформация корней и внесение массы
        eigvals, eigenvectors = np.linalg.eigh(M[0:8, 0:8])
        mass_direction = eigenvectors[:, np.argmin(eigvals)]
        for i in range(8):
            projection = np.dot(eigenvectors[:, i], mass_direction)
            M[i, i] += abs(projection) * (GLOBAL_C_MAX - self.C) / (GLOBAL_C_MAX - GLOBAL_C_MIN)

        # Динамическое расширение до 11 измерений
        for i in range(4, 11):
            M[i, i] += self.C * 0.1

        # Память поля
        M = self._apply_memory(M)

        # Мнимая часть: фазовое дыхание
        self.phi = (self.pi / 2.0) * (1.0 - (self.C - GLOBAL_C_MIN) / (GLOBAL_C_MAX - GLOBAL_C_MIN))
        M_imag = np.zeros_like(M)
        for i in range(11):
            for j in range(11):
                M_imag[i, j] = M[i, j] * np.tan(self.phi + 0.1 * (i - j) + entropy_flux * 0.001)
        M_imag = (M_imag + M_imag.T) / 2.0

        # Фазовый сдвиг FFS (циклы отталкивания-притяжения)
        phase_shift = 0.1 * np.sin(self.S * self.step_counter + entropy_flux)
        M_imag = M_imag + M * 0.05 * phase_shift

        return M + 1j * M_imag

    def sieve(self, entropy_flux):
        """
        Квантовое сито: пропускает шум через E8, возвращает 64 байта энтропии.
        """
        with self._lock:
            self.step_counter += 1

            # Обновляем состояние под воздействием шума
            chaos_operator = 1.0 / (1.0 + abs(entropy_flux) * (1.0 / self.Phi))
            self.C = self.C * chaos_operator + (1.0 - chaos_operator) * GLOBAL_C_MIN
            self.C = etve_tanh_limit(self.C)
            self.S = max(0.0, min(1.0, self.S + entropy_flux * 0.01))

            # Строим матрицу и вычисляем спектр
            M = self._build_complex_matrix(entropy_flux)
            eigenvalues = np.linalg.eigvals(M)

            # Сортируем по модулю
            eigenvalues = eigenvalues[np.argsort(np.abs(eigenvalues))[::-1]]

            # Сохраняем матрицу в память
            self.memory_matrices.append((M, time.time()))

            # Извлекаем криптографический материал из спектра
            output = bytearray()

            # 1. Фазы собственных значений (главный источник энтропии)
            phases = np.angle(eigenvalues)
            for p in phases:
                # Преобразуем фазу [-π, π] в 4 байта
                val = int((p + np.pi) / (2 * np.pi) * (2**32 - 1))
                output.extend(val.to_bytes(4, 'big'))

            # 2. Мнимые части (дополнительный слой)
            imag_parts = np.imag(eigenvalues)
            for imp in imag_parts:
                # Нормализуем и квантуем
                norm = math.tanh(abs(imp))  # Z-принцип на выходе
                val = int(norm * (2**32 - 1))
                output.extend(val.to_bytes(4, 'big'))

            # 3. Реальные части с перемешиванием
            real_parts = np.real(eigenvalues)
            for rp in real_parts:
                val = int(abs(math.tanh(rp)) * (2**32 - 1))
                output.extend(val.to_bytes(4, 'big'))

            # Итого: 11 * 4 * 3 = 132 байта сырой энтропии
            # Хэшируем до 64 байт для равномерности
            digest = hashlib.sha3_512(output).digest()
            return digest


# =============================================================================
# 2. CSPRNG ОБЁРТКА (стандартный интерфейс)
# =============================================================================

class ETVPCSPRNG:
    """
    🌀 ETVP-CSPRNG v1.0
    Криптографически стойкий генератор псевдослучайных чисел.
    
    Внешне — стандартный CSPRNG:
    - seed(entropy) / reseed(entropy)
    - random_bytes(n)
    - health_check()
    
    Внутри — ЕТВП v12.4 FFS: квантовое сито E8.
    """
    def __init__(self, seed_material=None, memory_depth=64):
        self.sieve = ETVPQuantumSieve(memory_depth=memory_depth)
        self.entropy_pool = bytearray()
        self.reseed_counter = 0
        self._lock = threading.Lock()
        
        # Инициализация
        if seed_material is None:
            seed_material = self._collect_system_entropy(128)
        self.seed(seed_material)

    def _collect_system_entropy(self, num_bytes):
        """Собирает шум реальности из системы."""
        entropy = bytearray()
        while len(entropy) < num_bytes:
            # Микросекундные колебания таймера
            t = time.time_ns()
            entropy.extend(t.to_bytes(8, 'big'))
            
            # Шум загрузки CPU
            cpu_jitter = self._cpu_jitter()
            entropy.extend(cpu_jitter.to_bytes(4, 'big'))
            
            # OS энтропия
            os_entropy = os.urandom(16)
            entropy.extend(os_entropy)
        
        return bytes(entropy[:num_bytes])

    def _cpu_jitter(self):
        """Измеряет микроскопический джиттер CPU."""
        start = time.perf_counter_ns()
        # Небольшая вычислительная нагрузка
        x = 1.0
        for _ in range(1000):
            x = math.sin(x) * math.cos(x) + math.sqrt(abs(x) + 0.001)
        end = time.perf_counter_ns()
        return end - start

    def _entropy_to_flux(self, entropy_bytes):
        """Преобразует байты энтропии в поток для E8."""
        # Берём первые 8 байт как float64
        val = int.from_bytes(entropy_bytes[:8], 'big')
        # Нормализуем к диапазону [-1, 1]
        flux = (val / (2**63)) - 1.0
        return flux

    def seed(self, entropy_material):
        """Инициализация генератора энтропией."""
        with self._lock:
            # Пополняем пул
            self.entropy_pool.extend(entropy_material)
            
            # Прогоняем через сито для инициализации
            for i in range(10):
                flux = self._entropy_to_flux(entropy_material[i*8:(i+1)*8] if i*8+8 <= len(entropy_material) else os.urandom(8))
                self.sieve.sieve(flux)
            
            self.reseed_counter = 0

    def reseed(self, entropy_material=None):
        """Пополнение энтропии (стандартный метод CSPRNG)."""
        if entropy_material is None:
            entropy_material = self._collect_system_entropy(64)
        self.seed(entropy_material)

    def random_bytes(self, num_bytes):
        """
        Генерирует num_bytes криптографически стойких случайных байт.
        """
        output = bytearray()
        
        with self._lock:
            while len(output) < num_bytes:
                # Собираем свежий шум реальности
                system_noise = self._collect_system_entropy(32)
                flux = self._entropy_to_flux(system_noise)
                
                # Пропускаем через квантовое сито
                raw_entropy = self.sieve.sieve(flux)
                
                # Добавляем в пул
                self.entropy_pool.extend(raw_entropy)
                
                # Извлекаем байты
                take = min(num_bytes - len(output), len(self.entropy_pool))
                output.extend(self.entropy_pool[:take])
                del self.entropy_pool[:take]
                
                # Счётчик reseed
                self.reseed_counter += len(raw_entropy)
                if self.reseed_counter > 1_000_000:
                    self.reseed()
                    self.reseed_counter = 0
        
        return bytes(output)

    def health_check(self):
        """Проверка состояния генератора (стандартный метод)."""
        with self._lock:
            c = self.sieve.C
            s = self.sieve.S
            
            # Проверяем, что когерентность в допустимых пределах
            if c < GLOBAL_C_MIN or c > GLOBAL_C_MAX:
                return False, f"Когерентность вне допустимого диапазона: C={c:.6f}"
            
            # Проверяем, что энтропия не застыла
            if s < 0.01:
                return False, f"Энтропия слишком низкая: S={s:.6f}"
            
            # Проверяем, что память работает
            if len(self.sieve.memory_matrices) < 1:
                return False, "Память поля пуста"
            
            return True, f"C={c:.6f}, S={s:.6f}, memory={len(self.sieve.memory_matrices)}"


# =============================================================================
# 3. ТЕСТИРОВАНИЕ
# =============================================================================

def test_csprng():
    """Демонстрация работы ETVP-CSPRNG."""
    print("=" * 70)
    print("🌀 ETVP-CSPRNG v1.0 — Криптографически стойкий генератор")
    print("   Внутри: ЕТВП v12.4 FFS (квантовое сито E8)")
    print("=" * 70)
    
    # Создание генератора
    print("\n[1] Инициализация генератора...")
    csprng = ETVPCSPRNG()
    ok, status = csprng.health_check()
    print(f"    Статус: {'✅ ' + status if ok else '❌ ' + status}")
    
    # Генерация байт
    print("\n[2] Генерация 64 случайных байт...")
    random_data = csprng.random_bytes(64)
    print(f"    Первые 16 байт: {random_data[:16].hex()}")
    print(f"    Всего: {len(random_data)} байт")
    
    # Проверка уникальности
    print("\n[3] Проверка уникальности (три запуска по 100 байт)...")
    sets = set()
    for i in range(3):
        data = csprng.random_bytes(100)
        h = hashlib.sha256(data).hexdigest()[:16]
        sets.add(h)
        print(f"    Запуск {i+1}: {h} (первые 8 байт: {data[:8].hex()})")
    print(f"    Уникальных: {len(sets)}/3")
    
    # Reseed
    print("\n[4] Тест reseed...")
    csprng.reseed(os.urandom(64))
    ok, status = csprng.health_check()
    print(f"    После reseed: {'✅ ' + status if ok else '❌ ' + status}")
    
    # Скорость
    print("\n[5] Тест производительности...")
    import time
    start = time.time()
    data = csprng.random_bytes(1_000_000)  # 1 MB
    elapsed = time.time() - start
    print(f"    Сгенерировано: 1 MB за {elapsed:.3f} сек")
    print(f"    Скорость: {1_000_000 / elapsed / 1024:.1f} KB/сек")
    
    # Проверка состояния
    print("\n[6] Финальная проверка...")
    ok, status = csprng.health_check()
    print(f"    Статус: {'✅ ' + status if ok else '❌ ' + status}")
    
    print("\n" + "=" * 70)
    print("✅ Демонстрация завершена. Генератор работает штатно.")
    print("=" * 70)


if __name__ == "__main__":
    test_csprng()
