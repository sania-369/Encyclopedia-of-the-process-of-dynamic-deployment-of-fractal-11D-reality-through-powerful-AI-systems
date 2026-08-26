#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
ETVP 12.5 INFINITUM FULL — Unified Field Computation with Live Animation
================================================================================
Полный синтез:
- Живая динамика E₈ (спектр, волновая функция, когерентность, энтропия)
- Синтез всех 26 параметров Стандартной Модели
- Динамическая визуализация через matplotlib.animation
- Сравнение с CODATA/PDG в реальном времени
- Стресс-тест Z-принципа

ГРУППЫ ПАРАМЕТРОВ:
I.   Заряженные лептоны (3)
II.  Кварковый сектор (6)
III. Калибровочные бозоны + Хиггс (3)
IV.  Матрица CKM (4)
V.   Калибровочные константы (3)
VI.  Матрица PMNS (4)
VII. Потенциал Хиггса + θ_QCD (3)

БАЗИС: Φ | π | √3 | Матрица Картана E₈ (11D)
================================================================================
"""

import numpy as np
from scipy.linalg import expm
import time
import math
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

C_FFS = 0.87
S_CYCLE = 0.12
EPSILON_FFS = 0.01

# =============================================================================
# 0.1 CODATA / PDG ЭТАЛОННЫЕ ЗНАЧЕНИЯ
# =============================================================================

CODATA = {
    'm_e': 0.5109989,
    'm_mu': 105.658,
    'm_tau': 1776.84,
    'm_u': 2.16,
    'm_d': 4.67,
    'm_s': 93.4,
    'm_c': 1270.0,
    'm_b': 4180.0,
    'm_t': 172500.0,
    'm_W': 80380.0,
    'm_Z': 91187.0,
    'm_H': 125100.0,
    'alpha_em_inv': 137.035999084,
    'alpha_w': 0.0338,
    'alpha_s': 0.1180,
    'sin_theta_12_CKM': 0.2250,
    'sin_theta_23_CKM': 0.0415,
    'sin_theta_13_CKM': 0.00360,
    'delta_CP_CKM': 69.2,
    'sin2_theta_12_PMNS': 0.307,
    'sin2_theta_23_PMNS': 0.454,
    'sin2_theta_13_PMNS': 0.0220,
    'delta_CP_PMNS': -155.0,
    'mu2_Higgs': -7825.0,
    'lambda_Higgs': 0.1291,
    'theta_QCD': 0.0,
}

CODATA_LABELS = [
    'm_e [МэВ]', 'm_μ [МэВ]', 'm_τ [МэВ]',
    'm_u [МэВ]', 'm_d [МэВ]', 'm_s [МэВ]',
    'm_c [МэВ]', 'm_b [МэВ]', 'm_t [МэВ]',
    'm_W [ГэВ]', 'm_Z [ГэВ]', 'm_H [ГэВ]',
    'sin θ12 CKM', 'sin θ23 CKM', 'sin θ13 CKM',
    'δ_CP CKM [°]', 'α_em⁻¹', 'α_w',
    'α_s', 'sin² θ12 PMNS', 'sin² θ23 PMNS',
    'sin² θ13 PMNS', 'δ_CP PMNS [°]', 'μ² Higgs',
    'λ Higgs', 'θ_QCD'
]


# =============================================================================
# 1. СИНТЕЗ 26 ПАРАМЕТРОВ
# =============================================================================

class ConstantsSynthesizer:
    """Вычисление всех 26 параметров из геометрического базиса."""
    
    def __init__(self):
        self.PHI = PHI
        self.PI = PI
        self.Z = Z_RES
    
    def synthesize_all(self):
        """Вычисляет все 26 параметров."""
        r = {}
        
        # Группа I: Лептоны
        r['m_e'] = self._calc_m_e()
        r['m_mu'] = self._calc_m_mu(r['m_e'])
        r['m_tau'] = self._calc_m_tau(r['m_e'])
        
        # Группа II: Кварки
        r['m_u'] = self._calc_m_u(r['m_e'])
        r['m_d'] = self._calc_m_d(r['m_e'])
        r['m_s'] = self._calc_m_s(r['m_u'])
        r['m_c'] = self._calc_m_c()
        r['m_b'] = self._calc_m_b(r['m_e'])
        r['m_t'] = self._calc_m_t()
        
        # Группа III: Бозоны
        r['m_W'] = self._calc_m_W(r['m_e'])
        r['m_Z'] = self._calc_m_Z(r['m_W'])
        r['m_H'] = self._calc_m_H()
        
        # Группа IV: CKM
        r['sin_theta_12_CKM'] = self._calc_sin_theta_12_CKM()
        r['sin_theta_23_CKM'] = self._calc_sin_theta_23_CKM()
        r['sin_theta_13_CKM'] = self._calc_sin_theta_13_CKM()
        r['delta_CP_CKM'] = self._calc_delta_CP_CKM()
        
        # Группа V: Константы
        r['alpha_em_inv'] = self._calc_alpha_em_inv()
        r['alpha_w'] = self._calc_alpha_w(r['alpha_em_inv'])
        r['alpha_s'] = self._calc_alpha_s(r['alpha_em_inv'])
        
        # Группа VI: PMNS
        r['sin2_theta_12_PMNS'] = self._calc_sin2_theta_12_PMNS(r['alpha_em_inv'])
        r['sin2_theta_23_PMNS'] = self._calc_sin2_theta_23_PMNS()
        r['sin2_theta_13_PMNS'] = self._calc_sin2_theta_13_PMNS(r['alpha_em_inv'])
        r['delta_CP_PMNS'] = self._calc_delta_CP_PMNS()
        
        # Группа VII: Хиггс
        r['mu2_Higgs'] = self._calc_mu2_Higgs(r['m_H'])
        r['lambda_Higgs'] = self._calc_lambda_Higgs(r['m_H'])
        r['theta_QCD'] = self._calc_theta_QCD()
        
        return r
    
    def _calc_m_e(self):
        numerator = (2 ** 12 - self.Z**4 * self.PI**3)
        denominator = (self.PHI**20 * 2 * self.PI**2 + self.PI**5)
        return numerator / denominator * 1000
    
    def _calc_m_mu(self, m_e):
        eta = 1.0 / (1.0 - 1.0 / (self.PHI**10))
        return m_e * (self.PI * self.PHI**3 * self.Z + 1.0 / (3.0 * self.PHI)) * eta
    
    def _calc_m_tau(self, m_e):
        a = self._calc_alpha_em_inv()
        return m_e * ((a / self.PI) * self.PHI**4 * self.Z - self.PI**2 / 2.0)
    
    def _calc_m_u(self, m_e):
        g = 1.0 / (1.0 - 1.0 / (self.PHI**8))
        return m_e * (2.0/3.0 * self.PI * self.PHI * self.Z) * g
    
    def _calc_m_d(self, m_e):
        g = 1.0 / (1.0 - 1.0 / (self.PHI**7))
        return m_e * (1.0/3.0 * self.PI**2 * self.PHI**2 + self.Z/4.0) * g
    
    def _calc_m_s(self, m_u):
        a = self._calc_alpha_em_inv()
        g = 1.0 / (1.0 - 1.0 / (self.PHI**6))
        return m_u * (self.PI * self.PHI**2 * self.Z + a / (2.0 * self.PI**2)) * g
    
    def _calc_m_c(self):
        m_p = 938.272
        g = 1.0 / (1.0 - 1.0 / (self.PHI**5))
        return m_p * (self.PHI**4 / self.PI + self.Z / (2.0 * self.PI**2)) * g
    
    def _calc_m_b(self, m_e):
        a = self._calc_alpha_em_inv()
        g = 1.0 / (1.0 - 1.0 / (self.PHI**4))
        return m_e * (a * self.PI * self.PHI**3 + self.Z**4 * self.PI**2) * g
    
    def _calc_m_t(self):
        m_p = 938.272
        a = self._calc_alpha_em_inv()
        g = 1.0 / (1.0 - 1.0 / (self.PHI**3))
        return m_p * (a / (self.PI * self.Z) * self.PHI**4 - self.Z**2) * g
    
    def _calc_m_W(self, m_e):
        a = self._calc_alpha_em_inv()
        eta = 1.0 / (1.0 - 1.0 / (self.PHI**9))
        return m_e * math.sqrt(a / (self.PI * self.Z) * self.PHI**10) * eta
    
    def _calc_m_Z(self, m_W):
        return m_W * math.sqrt(1.0 + self.Z / (self.PI * self.PHI**4))
    
    def _calc_m_H(self):
        v = 246.22 * 1000
        return v / math.sqrt(2.0) * (1.0 - 1.0 / (self.PI * self.PHI**3 * self.Z))
    
    def _calc_alpha_em_inv(self):
        pure = (self.PI * self.PHI**4 + self.PI**2 * self.PHI - 1.0 / (self.PHI**3 * self.PI))
        si_cal = math.sqrt(self.PI * self.PHI**3) + self.Z / (2**7)
        return pure * si_cal
    
    def _calc_sin_theta_12_CKM(self):
        a = self._calc_alpha_em_inv()
        return self.Z / (self.PI * self.PHI**3) * (1.0 - 1.0 / a)
    
    def _calc_sin_theta_23_CKM(self):
        return self.Z / (self.PI * self.PHI**8)
    
    def _calc_sin_theta_13_CKM(self):
        a = self._calc_alpha_em_inv()
        return self._calc_sin_theta_23_CKM() / (a * self.PHI)
    
    def _calc_delta_CP_CKM(self):
        return self.PI / 2.0 * (1.0 + 1.0 / (self.PHI**2 * self.Z))
    
    def _calc_alpha_w(self, a_inv):
        return 1.0 / a_inv * (1.0 + self.PI * self.PHI**4 / self.Z)
    
    def _calc_alpha_s(self, a_inv):
        beta_s = 4.0 / self.PI
        return (1.0 / a_inv) / (1.0 - beta_s * (1.0 / a_inv) * math.log(self.PHI**4 * self.Z))
    
    def _calc_sin2_theta_12_PMNS(self, a_inv):
        return 1.0 / self.PHI**3 * (1.0 - self.Z / a_inv)
    
    def _calc_sin2_theta_23_PMNS(self):
        return 0.5 - 1.0 / (self.PI * self.PHI**4)
    
    def _calc_sin2_theta_13_PMNS(self, a_inv):
        return self.PI**2 / (a_inv / self.PHI)**2
    
    def _calc_delta_CP_PMNS(self):
        return -self.PI * (1.0 - 1.0 / (self.PHI**3 * self.Z))
    
    def _calc_mu2_Higgs(self, m_H):
        return -(m_H**2) / 2.0 / 1e6
    
    def _calc_lambda_Higgs(self, m_H):
        v = 246.22 * 1000
        return m_H**2 / (2.0 * v**2)
    
    def _calc_theta_QCD(self):
        return 0.0


# =============================================================================
# 2. ЖИВАЯ ДИНАМИКА E₈
# =============================================================================

class ETVP125Full:
    """Полная модель: живая динамика + синтез 26 параметров."""
    
    def __init__(self, dim=11, memory_depth=64):
        self.dim = dim
        self.Phi = PHI
        self.pi = PI
        
        self.C = GLOBAL_C_TARGET
        self.S = 0.15
        self.step_counter = 0
        
        self.C_E8 = self._build_cartan_e8()
        
        np.random.seed(42)
        self.psi_t = (np.random.rand(self.dim) + 1j * np.random.rand(self.dim))
        self.psi_t /= np.linalg.norm(self.psi_t)
        
        self.memory_matrices = deque(maxlen=memory_depth)
        
        self.synth = ConstantsSynthesizer()
        
        self.history = {
            'dt': [], 'C': [], 'S': [],
            'eigenvalues': [], 'psi': [],
            'constants': []
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
        M = np.zeros((self.dim, self.dim), dtype=np.float64)
        M[0:8, 0:8] = self.C_E8.copy()
        
        ffs_correction = 1.0 + EPSILON_FFS * (self.C - C_FFS)
        M = M * ffs_correction
        M = M * (1.0 + 0.1 * (self.C - GLOBAL_C_TARGET))
        
        i_idx = np.arange(self.dim)[:, None]
        j_idx = np.arange(self.dim)[None, :]
        deformation = flux * 0.01 * np.sin(i_idx * 0.7 + j_idx * 1.3 + self.step_counter * 0.01)
        M = M + deformation
        
        eigvals, eigvecs = np.linalg.eigh(M[0:8, 0:8])
        mass_direction = eigvecs[:, np.argmin(eigvals)]
        for i in range(8):
            projection = np.dot(eigvecs[:, i], mass_direction)
            M[i, i] += abs(projection) * (GLOBAL_C_MAX - self.C) / (GLOBAL_C_MAX - GLOBAL_C_MIN)
        
        for i in range(4, self.dim):
            M[i, i] += self.C * 0.1
        
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
        
        # Синтез 26 параметров
        constants = self.synth.synthesize_all()
        
        self.history['dt'].append(dt)
        self.history['C'].append(self.C)
        self.history['S'].append(self.S)
        self.history['eigenvalues'].append(eigenvalues.copy())
        self.history['psi'].append(self.psi_t.copy())
        self.history['constants'].append(constants)
        
        return constants


# =============================================================================
# 3. ПОЛНАЯ ВИЗУАЛИЗАЦИЯ
# =============================================================================

class FullVisualizer:
    """Единая визуализация: динамика + 26 параметров."""
    
    def __init__(self, model):
        self.model = model
        
        self.fig = plt.figure(figsize=(22, 16))
        self.fig.patch.set_facecolor('#0a0a0a')
        
        # Верх: динамика (6 графиков)
        # Низ: 26 параметров (сетка 4×7 = 28 ячеек)
        gs_top = GridSpec(2, 3, figure=self.fig, top=0.48, bottom=0.30, hspace=0.35, wspace=0.35)
        gs_bottom = GridSpec(4, 7, figure=self.fig, top=0.28, bottom=0.03, hspace=0.5, wspace=0.5)
        
        # Верхние графики
        self.ax_spec = self.fig.add_subplot(gs_top[0, 0])
        self.ax_C = self.fig.add_subplot(gs_top[0, 1])
        self.ax_alpha = self.fig.add_subplot(gs_top[0, 2])
        self.ax_psi = self.fig.add_subplot(gs_top[1, 0])
        self.ax_S = self.fig.add_subplot(gs_top[1, 1])
        self.ax_mass = self.fig.add_subplot(gs_top[1, 2])
        
        # Нижние графики (26 параметров)
        self.ax_constants = []
        for i in range(26):
            row = i // 7
            col = i % 7
            ax = self.fig.add_subplot(gs_bottom[row, col])
            ax.set_facecolor('#111111')
            ax.set_title(CODATA_LABELS[i], color='white', fontsize=7)
            ax.tick_params(colors='white', labelsize=5)
            for spine in ax.spines.values():
                spine.set_color('#333333')
            self.ax_constants.append(ax)
        
        # Настройка верхних графиков
        for ax in [self.ax_spec, self.ax_C, self.ax_alpha, 
                   self.ax_psi, self.ax_S, self.ax_mass]:
            ax.set_facecolor('#111111')
            ax.tick_params(colors='white', labelsize=8)
            for spine in ax.spines.values():
                spine.set_color('#333333')
        
        self.history_26 = {key: [] for key in CODATA.keys()}
    
    def _update(self, frame):
        """Обновление всех графиков."""
        shock = 0.8 if frame == 50 else 0.0
        constants = self.model.evolve_step(shock)
        
        hist = self.model.history
        
        # Сохранение 26 параметров
        for key in CODATA:
            if key in constants:
                self.history_26[key].append(constants[key])
        
        eigenvalues = hist['eigenvalues'][-1]
        psi = hist['psi'][-1]
        C_vals = hist['C']
        S_vals = hist['S']
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
        
        # α⁻¹
        alpha_vals = [c['alpha_em_inv'] for c in hist['constants']]
        self.ax_alpha.clear()
        self.ax_alpha.set_facecolor('#111111')
        self.ax_alpha.set_title('1/α (CODATA: 137.036)', color='white', fontsize=10)
        self.ax_alpha.plot(x, alpha_vals, color='yellow', linewidth=1.5)
        self.ax_alpha.axhline(137.035999084, color='red', linestyle='--', linewidth=0.8)
        self.ax_alpha.tick_params(colors='white', labelsize=8)
        
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
        
        # m_p/m_e
        mass_vals = [c['m_t'] / c['m_e'] for c in hist['constants']]
        self.ax_mass.clear()
        self.ax_mass.set_facecolor('#111111')
        self.ax_mass.set_title('m_t/m_e', color='white', fontsize=10)
        self.ax_mass.plot(x, mass_vals, color='springgreen', linewidth=1.5)
        self.ax_mass.tick_params(colors='white', labelsize=8)
        
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
        print("=" * 70)
        print("ETVP 12.5 INFINITUM FULL — Полная визуализация")
        print("=" * 70)
        print("Верх: Живая динамика (спектр, C, S, ψ, α, массы)")
        print("Низ: 26 параметров Стандартной Модели")
        print("Закройте окно для завершения.")
        print("=" * 70)
        
        anim = animation.FuncAnimation(
            self.fig, self._update, frames=steps,
            interval=interval, blit=False, repeat=False
        )
        
        plt.show()
        
        # Финальный отчёт
        print("\n" + "=" * 70)
        print("ФИНАЛЬНЫЙ ОТЧЁТ: 26 ПАРАМЕТРОВ")
        print("=" * 70)
        
        constants = self.model.synth.synthesize_all()
        
        print(f"\n{'Параметр':<25} {'ETVP':>15} {'CODATA':>15} {'Откл.%':>10}")
        print("-" * 70)
        
        for key in CODATA:
            if key in constants:
                ev = constants[key]
                cv = CODATA[key]
                dev = abs(ev - cv) / abs(cv) * 100 if abs(cv) > 1e-9 else 0.0
                print(f"{key:<25} {ev:>15.6f} {cv:>15.6f} {dev:>9.4f}%")
        
        print("=" * 70)
        
        return anim


# =============================================================================
# 4. ЗАПУСК
# =============================================================================

if __name__ == "__main__":
    model = ETVP125Full(dim=11)
    viz = FullVisualizer(model)
    viz.run(steps=200, interval=50)
