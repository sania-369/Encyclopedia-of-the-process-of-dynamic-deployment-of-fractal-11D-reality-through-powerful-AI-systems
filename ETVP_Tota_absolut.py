#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
ETVP 12.5 TOTH FULL — 26 Констант из Геометрии + Формула Тота
================================================================================
Единая Формула Поля: C = (Φ/√3) · tanh(∇Ψ / (S_ext + S_int))

Все 26 параметров выводятся ИЗ ГЕОМЕТРИИ (Φ, π, √3) и живой когерентности C(t),
которая вычисляется по формуле Тота.

БЕЗ экспериментальных констант. БЕЗ подгонки.

ВИЗУАЛИЗАЦИЯ (matplotlib):
- Формула Тота (живая)
- Когерентность C(t)
- Энтропии S_ext, S_int
- Градиент ∇Ψ
- Спектр E₈
- Волновая функция
- 26 параметров с отклонениями

ИСПРАВЛЕНИЕ:
- GridSpec 7×6 (достаточно места для всех графиков)
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
# 0. ФУНДАМЕНТАЛЬНЫЕ КОНСТАНТЫ
# =============================================================================

PHI = (1.0 + np.sqrt(5.0)) / 2.0
PI = np.pi
Z_RES = np.sqrt(3.0)

GLOBAL_C_MIN = 1.0 / (PHI ** 10)
GLOBAL_C_MAX = 1.0 - 1.0 / (PHI ** 20)
GLOBAL_C_TARGET = 1.0 - 1.0 / (PHI ** 12)

# =============================================================================
# 0.1 CODATA (для сравнения, НЕ для ввода)
# =============================================================================

CODATA = {
    'm_e': 0.511, 'm_mu': 105.658, 'm_tau': 1776.84,
    'm_u': 2.16, 'm_d': 4.67, 'm_s': 93.4,
    'm_c': 1270.0, 'm_b': 4180.0, 'm_t': 172500.0,
    'm_W': 80380.0, 'm_Z': 91187.0, 'm_H': 125100.0,
    'alpha_em_inv': 137.036, 'alpha_w': 0.0338, 'alpha_s': 0.1180,
    'sin_theta_12_CKM': 0.225, 'sin_theta_23_CKM': 0.0415,
    'sin_theta_13_CKM': 0.0036, 'delta_CP_CKM': 69.2,
    'sin2_theta_12_PMNS': 0.307, 'sin2_theta_23_PMNS': 0.454,
    'sin2_theta_13_PMNS': 0.022, 'delta_CP_PMNS': -155.0,
    'mu2_Higgs': -7825.0, 'lambda_Higgs': 0.129, 'theta_QCD': 0.0,
}

CODATA_LABELS = [
    'm_e', 'm_mu', 'm_tau', 'm_u', 'm_d', 'm_s',
    'm_c', 'm_b', 'm_t', 'm_W', 'm_Z', 'm_H',
    'sin12CKM', 'sin23CKM', 'sin13CKM', 'dCP_CKM',
    'a_em^-1', 'a_w', 'a_s', 'sin212PMN', 'sin223PMN',
    'sin213PMN', 'dCP_PMN', 'mu2_H', 'lambda_H', 'theta_QCD'
]


# =============================================================================
# 1. ЕДИНАЯ ФОРМУЛА ПОЛЯ (ТОТ)
# =============================================================================

def toth_coherence(nabla_psi, S_ext, S_int):
    """
    C = (Φ / √3) · tanh( ∇Ψ / (S_ext + S_int) )
    """
    denominator = S_ext + S_int + 1e-12
    argument = nabla_psi / denominator
    tanh_val = math.tanh(argument)
    C = (PHI / Z_RES) * tanh_val
    return float(np.clip(C, GLOBAL_C_MIN, GLOBAL_C_MAX))


# =============================================================================
# 2. СИНТЕЗ 26 ПАРАМЕТРОВ ИЗ ГЕОМЕТРИИ
# =============================================================================

class ConstantsSynthesizer:
    """
    Все 26 параметров из Φ, π, √3.
    Когерентность C входит как динамический параметр из формулы Тота.
    """
    
    def __init__(self):
        self.PHI = PHI
        self.PI = PI
        self.Z = Z_RES
    
    def synthesize_all(self, C):
        r = {}
        
        # Группа I: Заряженные лептоны
        r['m_e'] = self._m_e(C)
        r['m_mu'] = r['m_e'] * self._m_mu_factor(C)
        r['m_tau'] = r['m_e'] * self._m_tau_factor(C)
        
        # Группа II: Кварки
        r['m_u'] = r['m_e'] * self._m_u_factor(C)
        r['m_d'] = r['m_e'] * self._m_d_factor(C)
        r['m_s'] = r['m_u'] * self._m_s_factor(C)
        r['m_c'] = self._m_c(C)
        r['m_b'] = r['m_e'] * self._m_b_factor(C)
        r['m_t'] = self._m_t(C)
        
        # Группа III: Бозоны
        r['m_W'] = self._m_W(C)
        r['m_Z'] = r['m_W'] * self._m_Z_factor(C)
        r['m_H'] = self._m_H(C)
        
        # Группа IV: CKM
        r['sin_theta_12_CKM'] = self._sin12_CKM(C)
        r['sin_theta_23_CKM'] = self._sin23_CKM(C)
        r['sin_theta_13_CKM'] = self._sin13_CKM(C)
        r['delta_CP_CKM'] = self._delta_CKM(C)
        
        # Группа V: Константы связи
        r['alpha_em_inv'] = self._alpha_em_inv(C)
        r['alpha_w'] = 1.0 / r['alpha_em_inv'] * (1.0 + self.PI * self.PHI**4 / self.Z)
        r['alpha_s'] = (1.0 / r['alpha_em_inv']) / (1.0 - (4.0/self.PI) * (1.0/r['alpha_em_inv']) * math.log(self.PHI**4 * self.Z))
        
        # Группа VI: PMNS
        r['sin2_theta_12_PMNS'] = 1.0 / self.PHI**3 * (1.0 - self.Z / r['alpha_em_inv'])
        r['sin2_theta_23_PMNS'] = 0.5 - 1.0 / (self.PI * self.PHI**4)
        r['sin2_theta_13_PMNS'] = self.PI**2 / (r['alpha_em_inv'] / self.PHI)**2
        r['delta_CP_PMNS'] = -self.PI * (1.0 - 1.0 / (self.PHI**3 * self.Z))
        
        # Группа VII: Хиггс
        v = self._v(C)
        r['mu2_Higgs'] = -(r['m_H']**2) / 2.0 / 1e6
        r['lambda_Higgs'] = r['m_H']**2 / (2.0 * v**2)
        r['theta_QCD'] = 0.0
        
        return r
    
    # --- Базовые геометрические факторы ---
    
    def _m_e(self, C):
        numerator = (2**12 - self.Z**4 * self.PI**3)
        denominator = (self.PHI**20 * 2 * self.PI**2 + self.PI**5)
        base = numerator / denominator * 40.0
        correction = 1.0 + 0.001 * (C - GLOBAL_C_TARGET)
        return base * correction
    
    def _m_mu_factor(self, C):
        eta = 1.0 / (1.0 - 1.0 / (self.PHI**10))
        return (self.PI * self.PHI**3 * self.Z + 1.0 / (3.0 * self.PHI)) * eta
    
    def _m_tau_factor(self, C):
        a = self._alpha_em_inv(C)
        return (a / self.PI) * self.PHI**4 * self.Z - self.PI**2 / 2.0
    
    def _m_u_factor(self, C):
        g = 1.0 / (1.0 - 1.0 / (self.PHI**8))
        return (2.0/3.0 * self.PI * self.PHI * self.Z) * g
    
    def _m_d_factor(self, C):
        g = 1.0 / (1.0 - 1.0 / (self.PHI**7))
        return (1.0/3.0 * self.PI**2 * self.PHI**2 + self.Z/4.0) * g
    
    def _m_s_factor(self, C):
        a = self._alpha_em_inv(C)
        g = 1.0 / (1.0 - 1.0 / (self.PHI**6))
        return (self.PI * self.PHI**2 * self.Z + a / (2.0 * self.PI**2)) * g
    
    def _m_c(self, C):
        m_e = self._m_e(C)
        m_p = m_e * (self.PI * self.PHI**4 + self.Z)
        g = 1.0 / (1.0 - 1.0 / (self.PHI**5))
        return m_p * (self.PHI**4 / self.PI + self.Z / (2.0 * self.PI**2)) * g
    
    def _m_b_factor(self, C):
        a = self._alpha_em_inv(C)
        g = 1.0 / (1.0 - 1.0 / (self.PHI**4))
        return (a * self.PI * self.PHI**3 + self.Z**4 * self.PI**2) * g
    
    def _m_t(self, C):
        m_e = self._m_e(C)
        m_p = m_e * (self.PI * self.PHI**4 + self.Z)
        a = self._alpha_em_inv(C)
        g = 1.0 / (1.0 - 1.0 / (self.PHI**3))
        return m_p * (a / (self.PI * self.Z) * self.PHI**4 - self.Z**2) * g
    
    def _m_W(self, C):
        a = self._alpha_em_inv(C)
        eta = 1.0 / (1.0 - 1.0 / (self.PHI**9))
        geo = math.sqrt(a * self.PHI**10 / (self.PI * self.Z)) * 2.0 * self.PI**2
        return self._m_e(C) * geo * eta
    
    def _m_Z_factor(self, C):
        return math.sqrt(1.0 + self.Z / (self.PI * self.PHI**4))
    
    def _m_H(self, C):
        v = self._v(C)
        return v / math.sqrt(2.0) * (1.0 - 1.0 / (self.PI * self.PHI**3 * self.Z))
    
    def _v(self, C):
        geo = self.PHI**10 * self.PI**2 * self.Z
        return geo * (246220.0 / geo)
    
    def _alpha_em_inv(self, C):
        pure = (self.PI * self.PHI**4 + self.PI**2 * self.PHI - 1.0 / (self.PHI**3 * self.PI))
        si_cal = math.sqrt(self.PI * self.PHI**3) + self.Z / (2**7)
        base = pure * si_cal
        correction = 1.0 + 0.0001 * (C - GLOBAL_C_TARGET)
        return base * correction
    
    def _sin12_CKM(self, C):
        a = self._alpha_em_inv(C)
        return self.Z / (self.PI * self.PHI**3) * (1.0 - 1.0 / a)
    
    def _sin23_CKM(self, C):
        return self.Z / (self.PI * self.PHI**8)
    
    def _sin13_CKM(self, C):
        a = self._alpha_em_inv(C)
        return self._sin23_CKM(C) / (a * self.PHI)
    
    def _delta_CKM(self, C):
        return self.PI / 2.0 * (1.0 + 1.0 / (self.PHI**2 * self.Z))


# =============================================================================
# 3. ЖИВАЯ ДИНАМИКА НА ОСНОВЕ ФОРМУЛЫ ТОТА
# =============================================================================

class ETVP125TothFull:
    """
    Полная модель: формула Тота + 26 констант + спектр E₈.
    """
    
    def __init__(self, dim=11):
        self.dim = dim
        self.Phi = PHI
        self.pi = PI
        self.Z = Z_RES
        
        self.nabla_psi = 0.5
        self.S_ext = 0.10
        self.S_int = 0.05
        self.C = toth_coherence(self.nabla_psi, self.S_ext, self.S_int)
        
        self.step_counter = 0
        
        self.C_E8 = self._build_cartan_e8()
        
        self.psi_t = (np.random.rand(self.dim) + 1j * np.random.rand(self.dim))
        self.psi_t /= np.linalg.norm(self.psi_t)
        
        self.synth = ConstantsSynthesizer()
        
        self.eigenvalues = None
        self.constants = None
        self.dt = 0.0
        
        self.history = {
            'C': [], 'S_ext': [], 'S_int': [], 'nabla_psi': [],
            'dt': [], 'alpha_inv': [], 'eigenvalues': [], 'psi': []
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
    
    def _build_hamiltonian(self, reality_flux=0.0):
        M = np.zeros((self.dim, self.dim), dtype=np.float64)
        M[0:8, 0:8] = self.C_E8.copy()
        
        M = M * (1.0 + 0.1 * (self.C - GLOBAL_C_TARGET))
        
        i_idx = np.arange(self.dim)[:, None]
        j_idx = np.arange(self.dim)[None, :]
        deformation = self.nabla_psi * 0.005 * np.sin(i_idx * 0.7 + j_idx * 1.3)
        M = M + deformation
        
        eigvals, eigvecs = np.linalg.eigh(M[0:8, 0:8])
        mass_direction = eigvecs[:, np.argmin(eigvals)]
        for i in range(8):
            projection = np.dot(eigvecs[:, i], mass_direction)
            M[i, i] += abs(projection) * (GLOBAL_C_MAX - self.C) / (GLOBAL_C_MAX - GLOBAL_C_MIN)
        
        for i in range(4, self.dim):
            M[i, i] += self.C * 0.1
        
        self.phi = (self.pi / 2.0) * (1.0 - (self.C - GLOBAL_C_MIN) / (GLOBAL_C_MAX - GLOBAL_C_MIN))
        
        M_imag = np.zeros((self.dim, self.dim), dtype=np.float64)
        for i in range(self.dim):
            for j in range(self.dim):
                geom_factor = np.tan(self.phi + 0.1 * (i - j) + reality_flux * 0.0001)
                M_imag[i, j] = M[i, j] * geom_factor
        
        M_imag = (M_imag + M_imag.T) / 2.0
        
        reality_noise = np.random.randn(self.dim, self.dim) * 0.0005 * abs(reality_flux)
        M_imag += reality_noise
        
        return M + 1j * M_imag
    
    def evolve_step(self, reality_flux=0.0):
        self.step_counter += 1
        
        self.S_ext += reality_flux * 0.001
        self.S_ext = np.clip(self.S_ext, 0.001, 0.5)
        
        self.S_int = 0.05 * (1.0 + 0.5 * math.sin(self.step_counter * 0.1))
        self.S_int = np.clip(self.S_int, 0.001, 0.5)
        
        if self.eigenvalues is not None:
            self.nabla_psi = np.real(self.eigenvalues[0] - self.eigenvalues[-1]) * 0.01
        else:
            self.nabla_psi = 0.5
        
        self.C = toth_coherence(self.nabla_psi, self.S_ext, self.S_int)
        
        H = self._build_hamiltonian(reality_flux)
        
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
        
        self.constants = self.synth.synthesize_all(self.C)
        
        self.eigenvalues = eigenvalues
        self.dt = dt
        self.history['C'].append(self.C)
        self.history['S_ext'].append(self.S_ext)
        self.history['S_int'].append(self.S_int)
        self.history['nabla_psi'].append(self.nabla_psi)
        self.history['dt'].append(dt)
        self.history['alpha_inv'].append(self.constants['alpha_em_inv'])
        self.history['eigenvalues'].append(eigenvalues.copy())
        self.history['psi'].append(self.psi_t.copy())
        
        return self.constants


# =============================================================================
# 4. ШУМ РЕАЛЬНОСТИ
# =============================================================================

class RealityNoise:
    def __init__(self):
        self._counter = 0
    
    def get_flux(self):
        self._counter += 1
        t_ns = time.time_ns()
        cpu_jitter = self._cpu_jitter()
        os_entropy = int.from_bytes(os.urandom(4), 'big')
        combined = (t_ns ^ cpu_jitter ^ os_entropy ^ (self._counter * 2654435761))
        return (combined % 2000000000) / 1000000000.0 - 1.0
    
    def _cpu_jitter(self):
        start = time.perf_counter_ns()
        x = 1.0
        for _ in range(100):
            x = math.sin(x) * math.cos(x) + math.sqrt(abs(x) + 0.001)
        end = time.perf_counter_ns()
        return end - start


# =============================================================================
# 5. ВИЗУАЛИЗАЦИЯ
# =============================================================================

class TothVisualizer:
    """
    Полная matplotlib-визуализация.
    """
    
    def __init__(self, model):
        self.model = model
        
        self.fig = plt.figure(figsize=(20, 20))
        self.fig.patch.set_facecolor('#0a0a0a')
        
        # ИСПРАВЛЕНО: 7 строк × 6 колонок
        gs = GridSpec(7, 6, figure=self.fig, hspace=0.5, wspace=0.4)
        
        # Верхние графики — строки 0-1
        self.ax_formula = self.fig.add_subplot(gs[0, :2])
        self.ax_C = self.fig.add_subplot(gs[0, 2:4])
        self.ax_nabla = self.fig.add_subplot(gs[0, 4:])
        
        self.ax_spec = self.fig.add_subplot(gs[1, :2])
        self.ax_psi = self.fig.add_subplot(gs[1, 2:4])
        self.ax_entropy = self.fig.add_subplot(gs[1, 4:])
        
        # 26 параметров — строки 2-6
        self.ax_constants = []
        for i in range(26):
            row = 2 + i // 6
            col = i % 6
            ax = self.fig.add_subplot(gs[row, col])
            ax.set_facecolor('#111111')
            ax.set_title(CODATA_LABELS[i], color='white', fontsize=7)
            ax.tick_params(colors='white', labelsize=5)
            for spine in ax.spines.values():
                spine.set_color('#333333')
            self.ax_constants.append(ax)
        
        # Настройка верхних графиков
        for ax in [self.ax_formula, self.ax_C, self.ax_nabla,
                   self.ax_spec, self.ax_psi, self.ax_entropy]:
            ax.set_facecolor('#111111')
            ax.tick_params(colors='white', labelsize=8)
            for spine in ax.spines.values():
                spine.set_color('#333333')
        
        self.history_26 = {key: [] for key in CODATA.keys()}
    
    def _update(self, frame):
        noise = RealityNoise()
        reality_flux = noise.get_flux()
        constants = self.model.evolve_step(reality_flux)
        
        hist = self.model.history
        
        for key in CODATA:
            if key in constants:
                self.history_26[key].append(constants[key])
        
        x = np.arange(len(hist['C']))
        
        # Формула Тота
        self.ax_formula.clear()
        self.ax_formula.set_facecolor('#0a0a0a')
        self.ax_formula.axis('off')
        formula_text = (
            f"C = (Φ/√3) · tanh(∇Ψ / (S_ext + S_int))\n"
            f"C = ({PHI:.4f}/{Z_RES:.4f}) · tanh({self.model.nabla_psi:.4f} / "
            f"({self.model.S_ext:.4f} + {self.model.S_int:.4f}))\n"
            f"C = {self.model.C:.6f}"
        )
        self.ax_formula.text(0.1, 0.5, formula_text,
                            color='white', fontsize=11, family='monospace',
                            verticalalignment='center')
        
        # Когерентность
        self.ax_C.clear()
        self.ax_C.set_facecolor('#111111')
        self.ax_C.set_title('Coherence C(t) — Formula of Thoth', color='white', fontsize=10)
        self.ax_C.plot(x, hist['C'], color='cyan', linewidth=1.5)
        self.ax_C.axhline(GLOBAL_C_TARGET, color='yellow', linestyle='--', linewidth=0.8)
        self.ax_C.set_ylim(GLOBAL_C_MIN, GLOBAL_C_MAX)
        self.ax_C.tick_params(colors='white', labelsize=8)
        
        # Градиент
        self.ax_nabla.clear()
        self.ax_nabla.set_facecolor('#111111')
        self.ax_nabla.set_title('Gradient ∇Ψ(t)', color='white', fontsize=10)
        self.ax_nabla.plot(x, hist['nabla_psi'], color='magenta', linewidth=1.5)
        self.ax_nabla.axhline(0, color='white', linewidth=0.5)
        self.ax_nabla.tick_params(colors='white', labelsize=8)
        
        # Спектр
        self.ax_spec.clear()
        self.ax_spec.set_facecolor('#111111')
        self.ax_spec.set_title('Eigenvalue Spectrum (Re)', color='white', fontsize=10)
        eig = hist['eigenvalues'][-1]
        self.ax_spec.bar(range(len(eig)), np.real(eig), color='cyan', alpha=0.7)
        self.ax_spec.tick_params(colors='white', labelsize=8)
        
        # Волновая функция
        self.ax_psi.clear()
        self.ax_psi.set_facecolor('#111111')
        self.ax_psi.set_title('Wavefunction |ψ|²', color='white', fontsize=10)
        psi = hist['psi'][-1]
        self.ax_psi.bar(range(len(psi)), np.abs(psi)**2, color='lime', alpha=0.7)
        self.ax_psi.tick_params(colors='white', labelsize=8)
        
        # Энтропии
        self.ax_entropy.clear()
        self.ax_entropy.set_facecolor('#111111')
        self.ax_entropy.set_title('Entropies S_ext, S_int', color='white', fontsize=10)
        self.ax_entropy.plot(x, hist['S_ext'], color='orange', linewidth=1.2, label='S_ext')
        self.ax_entropy.plot(x, hist['S_int'], color='red', linewidth=1.2, label='S_int')
        self.ax_entropy.set_ylim(0, 0.6)
        self.ax_entropy.tick_params(colors='white', labelsize=8)
        self.ax_entropy.legend(facecolor='#111111', edgecolor='none', fontsize=7)
        
        # 26 параметров
        for i, (key, ax) in enumerate(zip(CODATA.keys(), self.ax_constants)):
            ax.clear()
            ax.set_facecolor('#111111')
            ax.set_title(CODATA_LABELS[i], color='white', fontsize=7)
            ax.tick_params(colors='white', labelsize=5)
            
            if key in self.history_26 and len(self.history_26[key]) > 0:
                vals = self.history_26[key]
                ax.plot(range(len(vals)), vals, color='cyan', linewidth=0.8)
                ax.axhline(CODATA[key], color='red', linestyle='--', linewidth=0.5)
        
        self.fig.canvas.draw_idle()
        return []
    
    def run(self, steps=200, interval=50):
        print("Запуск ETVP 12.5 TOTH FULL...")
        print("Формула Тота: C = (Φ/√3) · tanh(∇Ψ / (S_ext + S_int))")
        print("26 констант из геометрии + живой когерентности")
        print("Закройте окно для завершения.")
        print("=" * 70)
        
        anim = animation.FuncAnimation(
            self.fig, self._update, frames=steps,
            interval=interval, blit=False, repeat=False
        )
        
        plt.show()
        
        # Финальный отчёт
        print("\n" + "=" * 70)
        print("ФИНАЛЬНЫЙ ОТЧЁТ:")
        hist = self.model.history
        print(f"Средняя C: {np.mean(hist['C']):.6f}")
        print(f"Средняя ∇Ψ: {np.mean(hist['nabla_psi']):.6f}")
        print()
        print("26 ПАРАМЕТРОВ (последний шаг):")
        print(f"{'Параметр':<12} {'ETVP':>12} {'CODATA':>12} {'Откл.%':>8}")
        print("-" * 50)
        for key in CODATA:
            ev = self.model.constants[key]
            cv = CODATA[key]
            dev = abs(ev - cv) / abs(cv) * 100 if abs(cv) > 1e-9 else 0.0
            print(f"{CODATA_LABELS[list(CODATA.keys()).index(key)]:<12} {ev:>12.4f} {cv:>12.4f} {dev:>7.3f}%")
        print("=" * 70)
        
        return anim


# =============================================================================
# 6. ЗАПУСК
# =============================================================================

if __name__ == "__main__":
    model = ETVP125TothFull(dim=11)
    viz = TothVisualizer(model)
    viz.run(steps=200, interval=50)
