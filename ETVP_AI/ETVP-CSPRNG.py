#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
ETVP 12.5 VISUAL v2 — Unified Field Computation with REALITY NOISE
================================================================================
Интеграция динамического графического вывода через matplotlib.animation.
Визуализация: спектр, волновая функция, когерентность, энтропия, константы.

ДОБАВЛЕНО:
- Шум реальности в каждом шаге (time.time_ns + CPU jitter)
- Живой хаос вселенной (без np.random.seed)
- Динамическая энтропия от системного шума
================================================================================
"""

import numpy as np
from scipy.linalg import expm
import time
import math
import os
from collections import deque

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.gridspec import GridSpec

# =============================================================================
# 0. КОНСТАНТЫ
# =============================================================================

GLOBAL_PHI = (1.0 + np.sqrt(5.0)) / 2.0
GLOBAL_PI = np.pi

C_FFS = 0.87
S_CYCLE = 0.12
EPSILON_FFS = 0.01

GLOBAL_C_MIN = 1.0 / (GLOBAL_PHI ** 10)
GLOBAL_C_MAX = 1.0 - 1.0 / (GLOBAL_PHI ** 20)
GLOBAL_C_TARGET = 1.0 - 1.0 / (GLOBAL_PHI ** 12)


# =============================================================================
# 1. ШУМ РЕАЛЬНОСТИ
# =============================================================================

class RealityNoise:
    """
    Сбор шума реальности из системы.
    """
    
    def __init__(self):
        self._counter = 0
    
    def get_flux(self):
        """
        Собирает шум реальности и преобразует в поток.
        """
        self._counter += 1
        
        # 1. Наносекундный таймер
        t_ns = time.time_ns()
        
        # 2. CPU jitter
        cpu_jitter = self._cpu_jitter()
        
        # 3. Системная энтропия
        os_entropy = int.from_bytes(os.urandom(4), 'big')
        
        # Комбинируем
        combined = (t_ns ^ cpu_jitter ^ os_entropy ^ (self._counter * 2654435761))
        
        # Нормализуем в [-1, 1]
        flux = (combined % 2000000000) / 1000000000.0 - 1.0
        
        return flux
    
    def _cpu_jitter(self):
        """Микроскопический джиттер CPU."""
        start = time.perf_counter_ns()
        x = 1.0
        for _ in range(100):
            x = math.sin(x) * math.cos(x) + math.sqrt(abs(x) + 0.001)
        end = time.perf_counter_ns()
        return end - start


# =============================================================================
# 2. ОСНОВНОЙ КЛАСС С ВИЗУАЛИЗАЦИЕЙ
# =============================================================================

class ETVP125Visual:
    """
    ETVP 12.5 с динамической визуализацией и шумом реальности.
    """
    
    def __init__(self, dim=11, memory_depth=64):
        self.dim = dim
        self.Phi = GLOBAL_PHI
        self.pi = GLOBAL_PI
        
        self.C = GLOBAL_C_TARGET
        self.S = 0.15
        self.step_counter = 0
        
        self.C_E8 = self._build_cartan_e8()
        
        # Живой хаос (без seed)
        self.psi_t = (np.random.rand(self.dim) + 1j * np.random.rand(self.dim))
        self.psi_t /= np.linalg.norm(self.psi_t)
        
        self.memory_matrices = deque(maxlen=memory_depth)
        
        # Шум реальности
        self.reality_noise = RealityNoise()
        
        self.history = {
            'dt': [], 'C': [], 'S': [], 
            'alpha_inv': [], 'mass_ratio': [], 'G': [],
            'eigenvalues': [], 'psi': [], 'noise': []
        }
    
    def _build_cartan_e8(self):
        return np.array([
            [ 2, -1,  0,  0,  0,  0,  0,  0],
            [-1,  2, -1,  0,  0,  0,  0,  0],
            [ 0, -1,  2, -1,  0,  0,  0,  0],
            [ 0,  0, -1,  2, -1,  0,  0,  0],
            [ 0,  0,  0, -1,  2, -1,  0, -1],
            [ 0,  0,  0,  0, -1,  2, -1,  0],
            [ 0,  0,  0,  0,  0, -1,  2,  0],
            [ 0,  0,  0,  0, -1,  0,  0,  2]
        ], dtype=np.float64)
    
    def _normalize_flux(self, flux):
        try:
            return math.tanh(flux / 10.0)
        except:
            return 0.0
    
    def _z_damping(self, C):
        E = (C - GLOBAL_C_MIN) / (GLOBAL_C_MAX - GLOBAL_C_MIN + 1e-12)
        E_limited = math.tanh(E) * 0.5 + 0.5
        return GLOBAL_C_MIN + E_limited * (GLOBAL_C_MAX - GLOBAL_C_MIN)
    
    def _build_hamiltonian(self, flux=0.0, reality_flux=0.0):
        # Реальная часть
        M = np.zeros((self.dim, self.dim), dtype=np.float64)
        M[0:8, 0:8] = self.C_E8.copy()
        
        ffs_correction = 1.0 + EPSILON_FFS * (self.C - C_FFS)
        M = M * ffs_correction
        M = M * (1.0 + 0.1 * (self.C - GLOBAL_C_TARGET))
        
        # Деформация от энтропийного потока
        i_idx = np.arange(self.dim)[:, None]
        j_idx = np.arange(self.dim)[None, :]
        deformation = flux * 0.01 * np.sin(i_idx * 0.7 + j_idx * 1.3 + self.step_counter * 0.01)
        M = M + deformation
        
        # ДОБАВЛЕНО: Деформация от шума реальности
        reality_deformation = reality_flux * 0.005 * np.sin(i_idx * 1.1 + j_idx * 1.7 + self.step_counter * 0.05)
        M = M + reality_deformation
        
        # Массовые поправки
        eigvals, eigvecs = np.linalg.eigh(M[0:8, 0:8])
        mass_direction = eigvecs[:, np.argmin(eigvals)]
        for i in range(8):
            projection = np.dot(eigvecs[:, i], mass_direction)
            M[i, i] += abs(projection) * (GLOBAL_C_MAX - self.C) / (GLOBAL_C_MAX - GLOBAL_C_MIN)
        
        for i in range(4, self.dim):
            M[i, i] += self.C * 0.1
        
        # Мнимая часть
        Z_damping = np.tanh(8.0 * self.S) * 0.5 + 0.5
        self.phi = (self.pi / 2.0) * (1.0 - (self.C - GLOBAL_C_MIN) / (GLOBAL_C_MAX - GLOBAL_C_MIN))
        
        M_imag = np.zeros((self.dim, self.dim), dtype=np.float64)
        for i in range(self.dim):
            for j in range(self.dim):
                geom_factor = np.tan(self.phi + 0.1 * (i - j) + reality_flux * 0.001)
                M_imag[i, j] = M[i, j] * geom_factor * Z_damping
        
        M_imag = (M_imag + M_imag.T) / 2.0
        
        phase_shift = 0.1 * np.sin(self.S * self.step_counter + flux + reality_flux)
        M_imag = M_imag + M * 0.05 * phase_shift
        
        # Стохастический шум от реальности
        stochastic_noise = np.random.randn(self.dim, self.dim) * 0.01 * self.S
        reality_noise_matrix = np.random.randn(self.dim, self.dim) * 0.005 * abs(reality_flux)
        M_imag += stochastic_noise + reality_noise_matrix
        
        return M + 1j * M_imag
    
    def evolve_step(self, external_entropy_flux=0.0):
        self.step_counter += 1
        flux = self._normalize_flux(external_entropy_flux)
        
        # ДОБАВЛЕНО: Шум реальности в каждом шаге
        reality_flux = self.reality_noise.get_flux()
        
        # Комбинированный поток
        combined_flux = flux + 0.3 * reality_flux
        
        # Обновление энтропии
        self.S += combined_flux * 0.01
        self.S = np.clip(self.S, 0.001, 1.0)
        
        # Обновление когерентности
        chaos_op = 1.0 / (1.0 + abs(combined_flux) * (1.0 / self.Phi))
        self.C = self.C * chaos_op + (1.0 - chaos_op) * GLOBAL_C_MIN
        self.C = self._z_damping(self.C)
        
        # Гамильтониан с шумом реальности
        H = self._build_hamiltonian(flux, reality_flux)
        
        eigenvalues = np.linalg.eigvals(H)
        eigenvalues = eigenvalues[np.argsort(np.abs(eigenvalues))[::-1]]
        
        spectral_gap = np.abs(eigenvalues[0]) - np.abs(eigenvalues[-1])
        
        if spectral_gap < 1e-9 or np.isnan(spectral_gap):
            dt = 1e-6
        else:
            dt_ratio = np.imag(eigenvalues[-1] / eigenvalues[0])
            dt_gap = 1.0 / spectral_gap
            dt = dt_ratio if abs(dt_ratio) > 1e-9 else dt_gap
        
        U = expm(-1j * H * dt)
        self.psi_t = U @ self.psi_t
        
        norm = np.vdot(self.psi_t, self.psi_t).real
        if norm > 1e-12:
            self.psi_t /= np.sqrt(norm)
        
        alpha_inv = np.real(eigenvalues[0] / eigenvalues[-1]) / self.Phi**2
        mass_ratio = np.real(eigenvalues[0] / eigenvalues[-2]) * self.Phi * 70.0
        G = np.real(eigenvalues[0] / (eigenvalues[-1] * eigenvalues[-2] + 1e-12)) / (self.Phi**20) / 1e7
        
        # Сохранение
        self.history['dt'].append(dt)
        self.history['C'].append(self.C)
        self.history['S'].append(self.S)
        self.history['alpha_inv'].append(alpha_inv)
        self.history['mass_ratio'].append(mass_ratio)
        self.history['G'].append(G)
        self.history['eigenvalues'].append(eigenvalues.copy())
        self.history['psi'].append(self.psi_t.copy())
        self.history['noise'].append(reality_flux)
        
        return dt, alpha_inv, mass_ratio, G


# =============================================================================
# 2. ВИЗУАЛИЗАЦИЯ (с шумом)
# =============================================================================

class ETVPVisualizer:
    """
    Динамическая визуализация ETVP 12.5 с шумом реальности.
    """
    
    def __init__(self, model):
        self.model = model
        
        self.fig = plt.figure(figsize=(16, 14))
        self.fig.patch.set_facecolor('#0a0a0a')
        
        gs = GridSpec(4, 3, figure=self.fig, hspace=0.4, wspace=0.35)
        
        # Верхние графики
        self.ax_spec = self.fig.add_subplot(gs[0, 0])
        self.ax_C = self.fig.add_subplot(gs[0, 1])
        self.ax_noise = self.fig.add_subplot(gs[0, 2])  # НОВЫЙ: график шума
        self.ax_psi = self.fig.add_subplot(gs[1, 0])
        self.ax_S = self.fig.add_subplot(gs[1, 1])
        self.ax_alpha = self.fig.add_subplot(gs[1, 2])
        self.ax_phase = self.fig.add_subplot(gs[2, 0])
        self.ax_mass = self.fig.add_subplot(gs[2, 1])
        self.ax_matrix = self.fig.add_subplot(gs[2, 2])
        
        # Настройка
        for ax in [self.ax_spec, self.ax_C, self.ax_noise, self.ax_psi,
                   self.ax_S, self.ax_alpha, self.ax_phase, self.ax_mass, self.ax_matrix]:
            ax.set_facecolor('#111111')
            ax.tick_params(colors='white', labelsize=8)
            for spine in ax.spines.values():
                spine.set_color('#333333')
    
    def _update(self, frame):
        shock = 0.8 if frame == 50 else 0.0
        self.model.evolve_step(shock)
        
        hist = self.model.history
        
        eigenvalues = hist['eigenvalues'][-1]
        psi = hist['psi'][-1]
        C_vals = hist['C']
        S_vals = hist['S']
        alpha_vals = hist['alpha_inv']
        mass_vals = hist['mass_ratio']
        noise_vals = hist['noise']
        
        x = np.arange(len(C_vals))
        
        # Спектр
        self.ax_spec.clear()
        self.ax_spec.set_facecolor('#111111')
        self.ax_spec.set_title('Eigenvalue Spectrum (Re)', color='white', fontsize=10)
        self.ax_spec.bar(range(len(eigenvalues)), np.real(eigenvalues), color='cyan', alpha=0.7)
        self.ax_spec.tick_params(colors='white', labelsize=8)
        
        # Когерентность
        self.ax_C.clear()
        self.ax_C.set_facecolor('#111111')
        self.ax_C.set_title('Coherence C(t)', color='white', fontsize=10)
        self.ax_C.plot(x, C_vals, color='cyan', linewidth=1.5)
        self.ax_C.axhline(GLOBAL_C_TARGET, color='yellow', linestyle='--', linewidth=0.8)
        self.ax_C.set_ylim(GLOBAL_C_MIN, GLOBAL_C_MAX)
        self.ax_C.tick_params(colors='white', labelsize=8)
        
        # НОВЫЙ: Шум реальности
        self.ax_noise.clear()
        self.ax_noise.set_facecolor('#111111')
        self.ax_noise.set_title('Reality Noise (flux)', color='white', fontsize=10)
        self.ax_noise.plot(x, noise_vals, color='magenta', linewidth=1)
        self.ax_noise.axhline(0, color='white', linewidth=0.5)
        self.ax_noise.set_ylim(-1.5, 1.5)
        self.ax_noise.tick_params(colors='white', labelsize=8)
        
        # Волновая функция
        self.ax_psi.clear()
        self.ax_psi.set_facecolor('#111111')
        self.ax_psi.set_title('Wavefunction |ψ|²', color='white', fontsize=10)
        self.ax_psi.bar(range(len(psi)), np.abs(psi)**2, color='lime', alpha=0.7)
        self.ax_psi.tick_params(colors='white', labelsize=8)
        
        # Энтропия
        self.ax_S.clear()
        self.ax_S.set_facecolor('#111111')
        self.ax_S.set_title('Entropy S(t)', color='white', fontsize=10)
        self.ax_S.plot(x, S_vals, color='orange', linewidth=1.5)
        self.ax_S.set_ylim(0, 1)
        self.ax_S.tick_params(colors='white', labelsize=8)
        
        # α⁻¹
        self.ax_alpha.clear()
        self.ax_alpha.set_facecolor('#111111')
        self.ax_alpha.set_title('1/α', color='white', fontsize=10)
        self.ax_alpha.plot(x, alpha_vals, color='yellow', linewidth=1.5)
        self.ax_alpha.axhline(137.035999084, color='red', linestyle='--', linewidth=0.8)
        self.ax_alpha.tick_params(colors='white', labelsize=8)
        
        # Фаза
        self.ax_phase.clear()
        self.ax_phase.set_facecolor('#111111')
        self.ax_phase.set_title('Wavefunction Phase', color='white', fontsize=10)
        phases = np.angle(psi)
        theta = np.linspace(0, 2*np.pi, 100)
        self.ax_phase.plot(np.cos(theta), np.sin(theta), color='#333333', linewidth=0.5)
        self.ax_phase.scatter(np.cos(phases), np.sin(phases), c=np.abs(psi), cmap='plasma', s=100)
        self.ax_phase.set_xlim(-1.2, 1.2)
        self.ax_phase.set_ylim(-1.2, 1.2)
        self.ax_phase.set_aspect('equal')
        self.ax_phase.tick_params(colors='white', labelsize=8)
        
        # Массы
        self.ax_mass.clear()
        self.ax_mass.set_facecolor('#111111')
        self.ax_mass.set_title('m_p/m_e', color='white', fontsize=10)
        self.ax_mass.plot(x, mass_vals, color='springgreen', linewidth=1.5)
        self.ax_mass.axhline(1836.15267343, color='red', linestyle='--', linewidth=0.8)
        self.ax_mass.tick_params(colors='white', labelsize=8)
        
        # Матрица
        self.ax_matrix.clear()
        self.ax_matrix.set_facecolor('#111111')
        self.ax_matrix.set_title('Hamiltonian Re(M)', color='white', fontsize=10)
        H = self.model._build_hamiltonian(0, self.model.reality_noise.get_flux())
        self.ax_matrix.imshow(np.real(H), cmap='viridis', aspect='auto')
        self.ax_matrix.tick_params(colors='white', labelsize=8)
        
        self.fig.canvas.draw_idle()
        return []
    
    def run(self, steps=200, interval=50):
        print("Запуск визуализации с шумом реальности...")
        print("Закройте окно для завершения.")
        print("=" * 70)
        
        anim = animation.FuncAnimation(
            self.fig, self._update, frames=steps,
            interval=interval, blit=False, repeat=False
        )
        
        plt.show()
        
        print("\n" + "=" * 70)
        print("ФИНАЛЬНЫЙ ОТЧЁТ:")
        hist = self.model.history
        print(f"Средняя C: {np.mean(hist['C']):.4f}")
        print(f"Средняя α⁻¹: {np.mean(hist['alpha_inv']):.4f} (CODATA: 137.036)")
        print(f"Средняя m_p/m_e: {np.mean(hist['mass_ratio']):.2f} (CODATA: 1836.15)")
        print(f"Шум реальности: {np.std(hist['noise']):.4f} (σ)")
        print("=" * 70)
        
        return anim


# =============================================================================
# 3. ЗАПУСК
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ETVP 12.5 VISUAL v2 — Динамика с шумом реальности")
    print("=" * 70)
    
    model = ETVP125Visual(dim=11)
    viz = ETVPVisualizer(model)
    viz.run(steps=200, interval=50)
