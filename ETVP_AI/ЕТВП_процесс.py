#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
ETVP 12.5 VISUAL — Unified Field Computation Framework with Live Animation
================================================================================
Интеграция динамического графического вывода через matplotlib.animation.
Визуализация: спектр, волновая функция, когерентность, энтропия, константы.
================================================================================
"""

import numpy as np
from scipy.linalg import expm
import time
import math
from collections import deque

import matplotlib
matplotlib.use('TkAgg')  # Для интерактивного окна
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
# 1. ОСНОВНОЙ КЛАСС С ВИЗУАЛИЗАЦИЕЙ
# =============================================================================

class ETVP125Visual:
    """
    ETVP 12.5 с динамической визуализацией.
    """
    
    def __init__(self, dim=11, memory_depth=64):
        self.dim = dim
        self.Phi = GLOBAL_PHI
        self.pi = GLOBAL_PI
        
        self.C = GLOBAL_C_TARGET
        self.S = 0.15
        self.step_counter = 0
        
        # Матрица Картана E₈
        self.C_E8 = self._build_cartan_e8()
        
        # Волновая функция
        np.random.seed(42)
        self.psi_t = (np.random.rand(self.dim) + 1j * np.random.rand(self.dim))
        self.psi_t /= np.linalg.norm(self.psi_t)
        
        # Память
        self.memory_matrices = deque(maxlen=memory_depth)
        
        # История для графиков
        self.history = {
            'dt': [], 'C': [], 'S': [], 
            'alpha_inv': [], 'mass_ratio': [], 'G': [],
            'eigenvalues': [], 'psi': []
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
    
    def _build_hamiltonian(self, flux=0.0):
        # Реальная часть
        M = np.zeros((self.dim, self.dim), dtype=np.float64)
        M[0:8, 0:8] = self.C_E8.copy()
        
        ffs_correction = 1.0 + EPSILON_FFS * (self.C - C_FFS)
        M = M * ffs_correction
        M = M * (1.0 + 0.1 * (self.C - GLOBAL_C_TARGET))
        
        # Деформация
        i_idx = np.arange(self.dim)[:, None]
        j_idx = np.arange(self.dim)[None, :]
        deformation = flux * 0.01 * np.sin(i_idx * 0.7 + j_idx * 1.3 + self.step_counter * 0.01)
        M = M + deformation
        
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
                geom_factor = np.tan(self.phi + 0.1 * (i - j))
                M_imag[i, j] = M[i, j] * geom_factor * Z_damping
        
        M_imag = (M_imag + M_imag.T) / 2.0
        
        phase_shift = 0.1 * np.sin(self.S * self.step_counter + flux)
        M_imag = M_imag + M * 0.05 * phase_shift
        
        stochastic_noise = np.random.randn(self.dim, self.dim) * 0.01 * self.S
        M_imag += stochastic_noise
        
        return M + 1j * M_imag
    
    def evolve_step(self, external_entropy_flux=0.0):
        self.step_counter += 1
        flux = self._normalize_flux(external_entropy_flux)
        
        self.S += flux * 0.01
        self.S = np.clip(self.S, 0.001, 1.0)
        
        chaos_op = 1.0 / (1.0 + abs(flux) * (1.0 / self.Phi))
        self.C = self.C * chaos_op + (1.0 - chaos_op) * GLOBAL_C_MIN
        self.C = self._z_damping(self.C)
        
        H = self._build_hamiltonian(flux)
        
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
        
        return dt, alpha_inv, mass_ratio, G


# =============================================================================
# 2. ВИЗУАЛИЗАЦИЯ
# =============================================================================

class ETVPVisualizer:
    """
    Динамическая визуализация ETVP 12.5.
    """
    
    def __init__(self, model):
        self.model = model
        
        # Создание фигуры
        self.fig = plt.figure(figsize=(16, 12))
        self.fig.patch.set_facecolor('#0a0a0a')
        
        gs = GridSpec(3, 3, figure=self.fig, hspace=0.35, wspace=0.35)
        
        # График 1: Спектр собственных значений (реальная часть)
        self.ax_spec = self.fig.add_subplot(gs[0, 0])
        self.ax_spec.set_title('Eigenvalue Spectrum (Real)', color='white', fontsize=10)
        self.ax_spec.set_facecolor('#111111')
        
        # График 2: Спектр собственных значений (мнимая часть)
        self.ax_spec_imag = self.fig.add_subplot(gs[0, 1])
        self.ax_spec_imag.set_title('Eigenvalue Spectrum (Imag)', color='white', fontsize=10)
        self.ax_spec_imag.set_facecolor('#111111')
        
        # График 3: Волновая функция (амплитуда)
        self.ax_psi = self.fig.add_subplot(gs[0, 2])
        self.ax_psi.set_title('Wavefunction |ψ|²', color='white', fontsize=10)
        self.ax_psi.set_facecolor('#111111')
        
        # График 4: Когерентность C
        self.ax_C = self.fig.add_subplot(gs[1, 0])
        self.ax_C.set_title('Coherence C(t)', color='white', fontsize=10)
        self.ax_C.set_facecolor('#111111')
        
        # График 5: Энтропия S
        self.ax_S = self.fig.add_subplot(gs[1, 1])
        self.ax_S.set_title('Entropy S(t)', color='white', fontsize=10)
        self.ax_S.set_facecolor('#111111')
        
        # График 6: α⁻¹
        self.ax_alpha = self.fig.add_subplot(gs[1, 2])
        self.ax_alpha.set_title('1/α (CODATA: 137.036)', color='white', fontsize=10)
        self.ax_alpha.set_facecolor('#111111')
        
        # График 7: Волновая функция (фаза на круге)
        self.ax_phase = self.fig.add_subplot(gs[2, 0])
        self.ax_phase.set_title('Wavefunction Phase', color='white', fontsize=10)
        self.ax_phase.set_facecolor('#111111')
        
        # График 8: m_p/m_e
        self.ax_mass = self.fig.add_subplot(gs[2, 1])
        self.ax_mass.set_title('m_p/m_e (CODATA: 1836.15)', color='white', fontsize=10)
        self.ax_mass.set_facecolor('#111111')
        
        # График 9: Матрица (heatmap)
        self.ax_matrix = self.fig.add_subplot(gs[2, 2])
        self.ax_matrix.set_title('Hamiltonian Re(M)', color='white', fontsize=10)
        self.ax_matrix.set_facecolor('#111111')
        
        # Настройка цветов
        for ax in [self.ax_spec, self.ax_spec_imag, self.ax_psi, 
                   self.ax_C, self.ax_S, self.ax_alpha, 
                   self.ax_phase, self.ax_mass, self.ax_matrix]:
            ax.tick_params(colors='white', labelsize=8)
            for spine in ax.spines.values():
                spine.set_color('#333333')
        
        # Линии для анимации
        self.lines = {}
        
    def _update(self, frame):
        """Обновление всех графиков."""
        # Один шаг эволюции
        shock = 0.8 if frame == 50 else 0.0
        self.model.evolve_step(shock)
        
        hist = self.model.history
        
        # Данные
        eigenvalues = hist['eigenvalues'][-1]
        psi = hist['psi'][-1]
        C_vals = hist['C']
        S_vals = hist['S']
        alpha_vals = hist['alpha_inv']
        mass_vals = hist['mass_ratio']
        
        x = np.arange(len(C_vals))
        
        # График 1: Спектр (реальная часть)
        self.ax_spec.clear()
        self.ax_spec.set_facecolor('#111111')
        self.ax_spec.set_title('Eigenvalue Spectrum (Real)', color='white', fontsize=10)
        re_vals = np.real(eigenvalues)
        self.ax_spec.bar(range(len(re_vals)), re_vals, color='cyan', alpha=0.7)
        self.ax_spec.axhline(0, color='white', linewidth=0.5)
        self.ax_spec.tick_params(colors='white', labelsize=8)
        
        # График 2: Спектр (мнимая часть)
        self.ax_spec_imag.clear()
        self.ax_spec_imag.set_facecolor('#111111')
        self.ax_spec_imag.set_title('Eigenvalue Spectrum (Imag)', color='white', fontsize=10)
        im_vals = np.imag(eigenvalues)
        self.ax_spec_imag.bar(range(len(im_vals)), im_vals, color='magenta', alpha=0.7)
        self.ax_spec_imag.axhline(0, color='white', linewidth=0.5)
        self.ax_spec_imag.tick_params(colors='white', labelsize=8)
        
        # График 3: Волновая функция
        self.ax_psi.clear()
        self.ax_psi.set_facecolor('#111111')
        self.ax_psi.set_title('Wavefunction |ψ|²', color='white', fontsize=10)
        psi_prob = np.abs(psi)**2
        self.ax_psi.bar(range(len(psi_prob)), psi_prob, color='lime', alpha=0.7)
        self.ax_psi.tick_params(colors='white', labelsize=8)
        
        # График 4: Когерентность
        self.ax_C.clear()
        self.ax_C.set_facecolor('#111111')
        self.ax_C.set_title('Coherence C(t)', color='white', fontsize=10)
        self.ax_C.plot(x, C_vals, color='cyan', linewidth=1.5)
        self.ax_C.axhline(GLOBAL_C_TARGET, color='yellow', linestyle='--', linewidth=0.8, label='Target')
        self.ax_C.set_ylim(GLOBAL_C_MIN, GLOBAL_C_MAX)
        self.ax_C.tick_params(colors='white', labelsize=8)
        self.ax_C.legend(facecolor='#111111', edgecolor='none', fontsize=7)
        
        # График 5: Энтропия
        self.ax_S.clear()
        self.ax_S.set_facecolor('#111111')
        self.ax_S.set_title('Entropy S(t)', color='white', fontsize=10)
        self.ax_S.plot(x, S_vals, color='orange', linewidth=1.5)
        self.ax_S.set_ylim(0, 1)
        self.ax_S.tick_params(colors='white', labelsize=8)
        
        # График 6: α⁻¹
        self.ax_alpha.clear()
        self.ax_alpha.set_facecolor('#111111')
        self.ax_alpha.set_title('1/α', color='white', fontsize=10)
        self.ax_alpha.plot(x, alpha_vals, color='yellow', linewidth=1.5)
        self.ax_alpha.axhline(137.035999084, color='red', linestyle='--', linewidth=0.8, label='CODATA')
        self.ax_alpha.tick_params(colors='white', labelsize=8)
        self.ax_alpha.legend(facecolor='#111111', edgecolor='none', fontsize=7)
        
        # График 7: Фаза волновой функции
        self.ax_phase.clear()
        self.ax_phase.set_facecolor('#111111')
        self.ax_phase.set_title('Wavefunction Phase', color='white', fontsize=10)
        phases = np.angle(psi)
        theta = np.linspace(0, 2*np.pi, 100)
        self.ax_phase.plot(np.cos(theta), np.sin(theta), color='#333333', linewidth=0.5)
        self.ax_phase.scatter(np.cos(phases), np.sin(phases), 
                             c=np.abs(psi), cmap='plasma', s=100)
        self.ax_phase.set_xlim(-1.2, 1.2)
        self.ax_phase.set_ylim(-1.2, 1.2)
        self.ax_phase.set_aspect('equal')
        self.ax_phase.tick_params(colors='white', labelsize=8)
        
        # График 8: m_p/m_e
        self.ax_mass.clear()
        self.ax_mass.set_facecolor('#111111')
        self.ax_mass.set_title('m_p/m_e', color='white', fontsize=10)
        self.ax_mass.plot(x, mass_vals, color='springgreen', linewidth=1.5)
        self.ax_mass.axhline(1836.15267343, color='red', linestyle='--', linewidth=0.8, label='CODATA')
        self.ax_mass.tick_params(colors='white', labelsize=8)
        self.ax_mass.legend(facecolor='#111111', edgecolor='none', fontsize=7)
        
        # График 9: Матрица
        self.ax_matrix.clear()
        self.ax_matrix.set_facecolor('#111111')
        self.ax_matrix.set_title('Hamiltonian Re(M)', color='white', fontsize=10)
        H = self.model._build_hamiltonian()
        im = self.ax_matrix.imshow(np.real(H), cmap='viridis', aspect='auto')
        self.ax_matrix.tick_params(colors='white', labelsize=8)
        
        self.fig.canvas.draw_idle()
        
        return []
    
    def run(self, steps=200, interval=50):
        """Запуск анимации."""
        print("Запуск визуализации...")
        print("Закройте окно для завершения.")
        print("=" * 70)
        
        anim = animation.FuncAnimation(
            self.fig,
            self._update,
            frames=steps,
            interval=interval,
            blit=False,
            repeat=False
        )
        
        plt.show()
        
        # Финальный отчёт
        print("\n" + "=" * 70)
        print("ФИНАЛЬНЫЙ ОТЧЁТ:")
        hist = self.model.history
        print(f"Средняя C: {np.mean(hist['C']):.4f}")
        print(f"Средняя α⁻¹: {np.mean(hist['alpha_inv']):.4f} (CODATA: 137.036)")
        print(f"Средняя m_p/m_e: {np.mean(hist['mass_ratio']):.2f} (CODATA: 1836.15)")
        print("=" * 70)
        
        return anim


# =============================================================================
# 3. ЗАПУСК
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ETVP 12.5 VISUAL — Динамическая визуализация")
    print("=" * 70)
    
    # Создание модели
    model = ETVP125Visual(dim=11)
    
    # Создание визуализатора
    viz = ETVPVisualizer(model)
    
    # Запуск анимации
    viz.run(steps=200, interval=50)
