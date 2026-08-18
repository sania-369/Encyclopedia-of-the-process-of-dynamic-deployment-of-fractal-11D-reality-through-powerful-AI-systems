#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🌀 ETVP — Сетевая модель на основе формулы Тота
    C = (Φ/√3) * tanh( ∇Ψ / (S_ext + S_int) )
    + ΔC_сеть + ΔC_эпоха + ΔC_жезл
Учтена сетевая природа когерентности (32 Трона, групповой резонанс).
Версия: 1.0 (после пересмотра эго-фильтра)
"""

import numpy as np
import math
import random
import time
from collections import deque
import matplotlib.pyplot as plt

# =============================================================================
# 0. ГЕОМЕТРИЧЕСКИЙ БАЗИС И КОНСТАНТЫ СЕТИ
# =============================================================================

GLOBAL_PHI = (1.0 + np.sqrt(5.0)) / 2.0          # Φ
GLOBAL_ROOT3 = np.sqrt(3.0)                      # √3

# --- Пределы для разных состояний ---
C_LIMIT_BODY = GLOBAL_PHI / GLOBAL_ROOT3        # ~0.934 — предел изолированного тела
C_LIMIT_NETWORK = 0.985                         # Максимум для Тота в сети
C_LIMIT_GROUP = 0.92                            # Максимум для группы из 3+ человек

C_MIN = 0.0
C_MAX = 1.0
C_TARGET = 0.7                                   # Целевая для обычной практики

# --- Калибровка FFS (как пограничное условие) ---
C_FFS = 0.87
S_cycle = 0.12
EPSILON_FFS = 0.01

# --- Параметры сети 32 Тронов ---
NETWORK_BOOST_MAX = 0.045                       # Максимальная добавка от сети
EPOCH_BOOST_MAX = 0.025                         # Добавка от эпохи Льва/Быка
STAFF_BOOST_MAX = 0.015                         # Добавка от Жезла/кристаллов


# =============================================================================
# 1. ЯДРО МОДЕЛИ С СЕТЕВОЙ ФОРМУЛОЙ ТОТА
# =============================================================================

class ETVECoreNetworkedToth:
    """
    Модель 11D-поля, где когерентность вычисляется по формуле Тота
    с учётом сетевых добавок.
    """
    def __init__(self, memory_depth=100, mode="isolated"):
        """
        mode: "isolated" (тело без сети),
              "group" (в группе),
              "toth" (как Тот — с сетью, Жезлом и в эпоху Льва)
        """
        self.phi = GLOBAL_PHI
        self.root3 = GLOBAL_ROOT3
        self.c_limit_body = C_LIMIT_BODY
        self.c_limit_network = C_LIMIT_NETWORK

        # --- Параметры сети ---
        self.mode = mode
        self.network_boost = 0.0
        self.epoch_boost = 0.0
        self.staff_boost = 0.0
        self._configure_mode(mode)

        # --- Матрица Картана E8 (ядро поля) ---
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

        # Топологические инварианты
        self.euler_characteristic = 4.18
        self.coxeter_SU2 = 3
        self.coxeter_SU3 = 4

        # --- Параметры состояния (для формулы) ---
        self.C = C_TARGET
        self.S = 0.15                      # S_int — внутренняя энтропия
        self.gradient_psi = 1.0            # ∇Ψ — градиент поля
        self.entropy_ext = 0.1             # S_ext — внешняя энтропия
        self.tanh_argument = 0.0
        self.C_body = 0.0                  # Базовая когерентность тела (без сети)

        self.step_counter = 0
        self.dt_real = 1.0
        self.dt_imag = 0.0
        self.phi_phase = 0.0
        self.a = 1.0
        self.H = 0.0
        self.dark_energy = 0.0
        self.G = 0.0

        # Частицы
        self.real_particles = []
        self.virtual_particles = []
        self.memory = deque(maxlen=memory_depth)
        self.memory_matrices = deque(maxlen=memory_depth)

        # История
        self.history = {
            "C": [], "C_body": [], "network_boost": [], "epoch_boost": [],
            "staff_boost": [], "S": [], "gradient_psi": [], "entropy_ext": [],
            "entropy_int": [], "tanh_argument": [],
            "dt_real": [], "dt_imag": [], "phi": [],
            "alpha": [], "mass_ratio": [], "G": [], "unification": [],
            "a": [], "H": [], "dark_energy": []
        }

        self._build_memory_kernel()
        self._init_ffs_state()

    def _configure_mode(self, mode):
        """Настраивает сетевые добавки в зависимости от режима."""
        if mode == "isolated":
            self.network_boost = 0.0
            self.epoch_boost = 0.0
            self.staff_boost = 0.0
            self.c_limit = self.c_limit_body
        elif mode == "group":
            self.network_boost = 0.02       # 3+ человека дают ~0.02
            self.epoch_boost = 0.0
            self.staff_boost = 0.005        # Кристаллы в группе
            self.c_limit = C_LIMIT_GROUP
        elif mode == "toth":
            self.network_boost = 0.035      # Сеть 32 Тронов
            self.epoch_boost = 0.02         # Эпоха Льва/Быка
            self.staff_boost = 0.01         # Жезл Тота
            self.c_limit = self.c_limit_network
        else:
            raise ValueError(f"Неизвестный режим: {mode}")

        print(f"🌀 Режим '{mode}': C_limit = {self.c_limit:.4f}")

    def _init_ffs_state(self):
        """Инициализация состояния по данным FFS."""
        # Подбираем начальные значения, чтобы выйти на целевой C
        if self.mode == "toth":
            target_C = 0.95
        elif self.mode == "group":
            target_C = 0.85
        else:
            target_C = 0.7

        self.gradient_psi = 1.5
        self.entropy_ext = 0.1
        self.S = 0.1
        self.C = target_C
        self.C = self.calculate_coherence(self.gradient_psi, self.entropy_ext, self.S, apply_network=True)
        print(f"   Инициализация: C = {self.C:.4f}")

    def calculate_coherence(self, gradient_psi, entropy_ext, entropy_int, apply_network=True):
        """
        ФОРМУЛА ТОТА (сетевая):
        C = (Φ/√3) * tanh( ∇Ψ / (S_ext + S_int) )
        + ΔC_сеть + ΔC_эпоха + ΔC_жезл
        """
        denominator = entropy_ext + entropy_int
        if denominator < 1e-12:
            C_body = self.c_limit_body
        else:
            argument = gradient_psi / denominator
            argument = np.clip(argument, -50, 50)
            tanh_val = np.tanh(argument)
            C_body = self.c_limit_body * tanh_val

        C_body = max(0.0, min(self.c_limit_body, C_body))
        self.C_body = C_body

        if apply_network:
            C_total = C_body + self.network_boost + self.epoch_boost + self.staff_boost
            C_total = max(0.0, min(self.c_limit, C_total))
        else:
            C_total = C_body

        self.tanh_argument = gradient_psi / (denominator + 1e-12)
        return C_total

    def _build_memory_kernel(self):
        """Ядро памяти — экспоненциальное затухание."""
        lambda_spectrum = np.array([2.0, 1.5, 1.0, 0.8, 0.6, 0.4, 0.3, 0.2, 0.1, 0.05, 0.01])
        lambda_spectrum = lambda_spectrum / np.sum(lambda_spectrum)

        def kernel(tau):
            return np.sum(lambda_spectrum * np.exp(-lambda_spectrum * tau))

        self.memory_kernel = kernel

    def _apply_memory(self, M):
        """Применяет память к матрице поля."""
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
            memory_strength = (self.C - C_MIN) / (self.c_limit - C_MIN + 1e-12)
            memory_strength = np.clip(memory_strength, 0.0, 1.0)
            return (1.0 - memory_strength) * M + memory_strength * memory_effect
        return M

    def _build_complex_matrix(self):
        """Строит комплексную матрицу 11x11 с учётом когерентности."""
        # Базовое пространство E8 с учётом когерентности
        M = self.C_E8.copy() * (1.0 + 0.1 * (self.C - C_TARGET))

        # Калибровка FFS как возмущение
        ffs_correction = 1.0 + EPSILON_FFS * (self.C - C_FFS)
        M = M * ffs_correction

        # Деформация корней и внесение массы
        eigvals, eigenvectors = np.linalg.eigh(M[0:8, 0:8])
        mass_direction = eigenvectors[:, np.argmin(eigvals)]
        for i in range(8):
            projection = np.dot(eigenvectors[:, i], mass_direction)
            M[i, i] += abs(projection) * (self.c_limit - self.C) / (self.c_limit - C_MIN + 1e-12)

        # Динамическое расширение до 11 измерений
        for i in range(4, 11):
            M[i, i] += self.C * 0.1

        # Учёт частиц
        particle_contribution = np.zeros(11)
        for p in self.real_particles:
            if p.get("alive", True):
                particle_contribution[0] += p.get("mass", 0.1) * 10
                particle_contribution[1] += p.get("charge", 0.1)
        M[0, :] += particle_contribution * 0.01

        M = self._apply_memory(M)

        # Мнимая часть через фазу
        self.phi_phase = (np.pi / 2.0) * (1.0 - (self.C - C_MIN) / (self.c_limit - C_MIN + 1e-12))

        M_imag = np.zeros_like(M)
        for i in range(11):
            for j in range(11):
                M_imag[i, j] = M[i, j] * np.tan(self.phi_phase + 0.1 * (i - j))
        M_imag = (M_imag + M_imag.T) / 2.0

        phase_shift = 0.1 * np.sin(self.S * self.step_counter)
        M_imag = M_imag + M * 0.05 * phase_shift

        return M + 1j * M_imag

    def _update_particles(self):
        """Обновляет ансамбль частиц."""
        threshold = C_MIN + (self.c_limit - C_MIN) * 0.15
        if self.C > threshold and len(self.real_particles) == 0:
            self.real_particles.append({"mass": 0.1, "charge": 0.1, "alive": True})
        if self.C < threshold * 0.5 and len(self.real_particles) > 0:
            self.real_particles = []
        if self.C > threshold:
            if random.random() < 0.01 and len(self.virtual_particles) < 10:
                self.virtual_particles.append({"energy": random.uniform(0.1, 1.0), "age": 0, "alive": True})
        for v in self.virtual_particles[:]:
            v["age"] += 1
            if v["age"] > 5 or random.random() < 0.02:
                self.virtual_particles.remove(v)

    def update_field(self, dt):
        """Обновляет поле: вычисляет спектр, константы, время."""
        self.step_counter += 1

        M = self._build_complex_matrix()
        eigenvalues = np.linalg.eigvals(M)
        eigenvalues = eigenvalues[np.argsort(np.abs(eigenvalues))[::-1]]

        # Константы
        alpha_inv = np.real(eigenvalues[0] / eigenvalues[10]) / self.phi**2
        mass_ratio = np.real(eigenvalues[0] / eigenvalues[9]) * self.phi * 70.0
        G_raw = np.real(eigenvalues[0] / (eigenvalues[10] * eigenvalues[9] + 1e-12))
        G = G_raw / (self.phi ** 20) / 1e7

        # Время из спектра
        dt_complex = eigenvalues[10] / eigenvalues[0]
        dt_real = np.real(dt_complex)
        dt_imag = np.imag(dt_complex)
        phi_phase = np.arctan2(dt_imag, dt_real)

        # Космология
        a_new = np.real(eigenvalues[0] / (eigenvalues[1] + eigenvalues[2] + 1e-12))
        if self.a > 0:
            da = a_new - self.a
            H = da / (self.a * dt + 1e-12)
        else:
            H = 0.0
        self.a = a_new
        self.H = H
        rho = len(self.real_particles) + 0.1 * len(self.virtual_particles)
        dark_energy = max(0.0, self.H**2 - (8 * np.pi * G * rho) / 3.0)

        # Взаимодействия
        alpha_em = 1.0 / alpha_inv
        M_U1 = M[0:1, 0:1]
        M_SU2 = M[0:2, 0:2]
        M_SU3 = M[0:3, 0:3]

        def casimir(M_sub):
            trace = np.trace(M_sub)
            trace2 = np.trace(M_sub @ M_sub)
            if abs(trace) < 1e-12:
                return 1.0
            return trace2 / (trace**2 + 1e-12)

        C_U1 = casimir(M_U1)
        C_SU2 = casimir(M_SU2)
        C_SU3 = casimir(M_SU3)

        beta_em = (1.0 / (C_U1 + 0.5)) * self.euler_characteristic
        beta_s = (1.0 / (C_SU3 + 0.5)) * self.coxeter_SU3
        beta_w = (1.0 / (C_SU2 + 0.5)) * self.coxeter_SU2

        E = (self.C - C_MIN) / (self.c_limit - C_MIN + 1e-12)
        E = np.clip(E, 1e-6, 1.0)
        log_ratio = np.log(1.0 / E)

        alpha_s = alpha_em / (1.0 + beta_s * alpha_em * log_ratio)
        alpha_w = alpha_em / (1.0 + beta_w * alpha_em * log_ratio)

        couplings = np.array([alpha_em, alpha_s, alpha_w])
        couplings = couplings / (np.mean(couplings) + 1e-12)
        unification = 1.0 - np.std(couplings)

        self.dt_real = dt_real
        self.dt_imag = dt_imag
        self.G = G
        self.dark_energy = dark_energy
        self.memory_matrices.append((M, time.time()))

        return {
            "alpha_inv": alpha_inv,
            "mass_ratio": mass_ratio,
            "dt_real": dt_real,
            "dt_imag": dt_imag,
            "phi": phi_phase,
            "G": G,
            "a": self.a,
            "H": H,
            "dark_energy": dark_energy,
            "alpha_em": alpha_em,
            "alpha_s": alpha_s,
            "alpha_w": alpha_w,
            "unification": unification
        }

    def evolve(self, entropy_flux=0.0, time_step=1.0):
        """
        Один шаг эволюции поля.
        Вход: entropy_flux — изменение энтропии (внешний шум).
        """
        # 1. Обновление параметров формулы Тота
        self.S = max(0.0, min(1.0, self.S + entropy_flux * 0.01))
        self.entropy_ext = abs(entropy_flux) + 0.1 * self.S

        # Градиент поля зависит от когерентности и внешнего воздействия
        self.gradient_psi = 1.0 / (1.0 + entropy_flux * self.S + 0.001 * (1.0 - self.C))

        # 2. Расчёт C по формуле Тота (с сетью)
        C_calculated = self.calculate_coherence(
            self.gradient_psi,
            self.entropy_ext,
            self.S,
            apply_network=True
        )

        # Инерция
        self.C = 0.9 * self.C + 0.1 * C_calculated
        self.C = max(0.0, min(self.c_limit, self.C))

        # 3. Обновление частиц и матрицы поля
        self._update_particles()
        result = self.update_field(time_step)

        # 4. Запись истории
        self.history["C"].append(self.C)
        self.history["C_body"].append(self.C_body)
        self.history["network_boost"].append(self.network_boost)
        self.history["epoch_boost"].append(self.epoch_boost)
        self.history["staff_boost"].append(self.staff_boost)
        self.history["S"].append(self.S)
        self.history["gradient_psi"].append(self.gradient_psi)
        self.history["entropy_ext"].append(self.entropy_ext)
        self.history["entropy_int"].append(self.S)
        self.history["tanh_argument"].append(self.tanh_argument)
        self.history["dt_real"].append(result["dt_real"])
        self.history["dt_imag"].append(result["dt_imag"])
        self.history["phi"].append(result["phi"])
        self.history["alpha"].append(result["alpha_inv"])
        self.history["mass_ratio"].append(result["mass_ratio"])
        self.history["G"].append(result["G"])
        self.history["a"].append(result["a"])
        self.history["H"].append(result["H"])
        self.history["dark_energy"].append(result["dark_energy"])
        self.history["unification"].append(result["unification"])

        return result


# =============================================================================
# 2. ДЕМОНСТРАЦИЯ ТРЁХ РЕЖИМОВ
# =============================================================================

def run_simulation(mode, steps=500):
    """Запускает симуляцию в заданном режиме."""
    model = ETVECoreNetworkedToth(memory_depth=100, mode=mode)

    print(f"\n🔄 Запуск режима '{mode}' на {steps} шагов...")
    for i in range(steps):
        entropy_flux = 0.05 * np.sin(i / 10.0) + 0.02 * np.sin(i / 3.0) + 0.005 * np.random.randn()
        if 200 < i < 210:
            entropy_flux += 0.1
        model.evolve(entropy_flux, time_step=1.0)

    return model


def plot_results(models, modes):
    """Строит сравнительные графики для разных режимов."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    colors = {'isolated': 'blue', 'group': 'green', 'toth': 'purple'}

    for model, mode in zip(models, modes):
        color = colors.get(mode, 'gray')

        # C(t)
        axes[0, 0].plot(model.history["C"], color=color, linewidth=1.5, label=f'{mode} (C={model.history["C"][-1]:.3f})')
        axes[0, 0].axhline(C_LIMIT_BODY, color='red', linestyle='--', alpha=0.5, label='C_body предел' if mode == modes[0] else '')
        axes[0, 0].axhline(C_LIMIT_NETWORK, color='purple', linestyle=':', alpha=0.5, label='C_сети предел' if mode == modes[0] else '')

        # C_body (базовая когерентность тела)
        axes[0, 1].plot(model.history["C_body"], color=color, linewidth=1.0, linestyle='--', label=f'{mode} (C_body)')

        # Компоненты добавок (только для одного режима — чтобы не загромождать)
        if mode == 'toth':
            axes[1, 0].fill_between(range(len(model.history["C"])), model.history["network_boost"], alpha=0.3, label='Сеть (32 Трона)')
            axes[1, 0].fill_between(range(len(model.history["C"])), model.history["epoch_boost"], alpha=0.3, label='Эпоха Льва')
            axes[1, 0].fill_between(range(len(model.history["C"])), model.history["staff_boost"], alpha=0.3, label='Жезл')
            axes[1, 0].set_title('Добавки к C (режим Тота)')

        # 1/α
        axes[1, 1].plot(model.history["alpha"], color=color, linewidth=1, label=f'{mode}: 1/α = {np.mean(model.history["alpha"][-50:]):.2f}')

    axes[0, 0].set_title('Когерентность C(t)')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].set_ylim(0, 1.0)

    axes[0, 1].set_title('Базовая C_тела (без сети)')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    axes[1, 1].set_title('1/α(t)')
    axes[1, 1].axhline(137.035999084, color='red', linestyle='--', label='CODATA')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


# =============================================================================
# 3. ЗАПУСК
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("🌀 СЕТЕВАЯ МОДЕЛЬ НА ОСНОВЕ ФОРМУЛЫ ТОТА")
    print("   C = (Φ/√3) * tanh( ∇Ψ / (S_ext + S_int) ) + ΔC_сеть + ΔC_эпоха + ΔC_жезл")
    print(f"   Предел тела (без сети):   {C_LIMIT_BODY:.4f}")
    print(f"   Предел сети (Тот):        {C_LIMIT_NETWORK:.4f}")
    print("=" * 80)

    modes = ["isolated", "group", "toth"]
    models = []

    for mode in modes:
        model = run_simulation(mode, steps=500)
        models.append(model)

        # Вывод результатов
        print(f"\n--- Режим '{mode}' ---")
        print(f"  C_средн = {np.mean(model.history['C']):.4f}")
        print(f"  C_макс  = {np.max(model.history['C']):.4f}")
        print(f"  1/α     = {np.mean(model.history['alpha']):.2f} ± {np.std(model.history['alpha']):.2f}")

    plot_results(models, modes)
    print("\n✅ Сравнение режимов завершено.")
