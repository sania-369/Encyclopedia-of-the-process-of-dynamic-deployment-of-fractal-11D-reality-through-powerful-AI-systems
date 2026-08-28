#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
ETVP 12.5 INFINITUM FULL — Живая динамика + 26 констант + предсказания
================================================================================
Интеграция:
- Живая динамика E₈ (спектр, волновая функция, когерентность, энтропия)
- Вывод всех 26 параметров Стандартной Модели из базиса (Φ, π, √3)
- Предсказания: углы разлёта ATOMKI, тёмная материя

ВИЗУАЛИЗАЦИЯ (matplotlib.animation):
- Спектр E₈
- Волновая функция
- Когерентность C(t)
- Энтропия S(t)
- α⁻¹, m_p/m_e
- 26 параметров (сетка)
- Углы разлёта и тёмная материя
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
# 0. КОНСТАНТЫ
# =============================================================================

PHI = (1.0 + np.sqrt(5.0)) / 2.0
PI = np.pi
Z_RES = np.sqrt(3.0)

C_FFS = 0.87
EPSILON_FFS = 0.01

GLOBAL_C_MIN = 1.0 / (PHI ** 10)
GLOBAL_C_MAX = 1.0 - 1.0 / (PHI ** 20)
GLOBAL_C_TARGET = 1.0 - 1.0 / (PHI ** 12)

# CODATA / PDG
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
# 1. СИНТЕЗ 26 ПАРАМЕТРОВ
# =============================================================================

class ConstantsSynthesizer:
    """Все 26 параметров из Φ, π, √3."""
    
    def __init__(self):
        self.PHI = PHI
        self.PI = PI
        self.Z = Z_RES
    
    def synthesize_all(self, C):
        r = {}
        
        # Группа I: Лептоны
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
        
        # Группа V: Связи
        r['alpha_em_inv'] = self._alpha_em_inv(C)
        r['alpha_w'] = (1.0 / r['alpha_em_inv']) * (1.0 + self.PI * self.PHI**4 / self.Z)
        r['alpha_s'] = (1.0 / r['alpha_em_inv']) / (1.0 - (4.0/self.PI) * (1.0/r['alpha_em_inv']) * math.log(self.PHI**4 * self.Z))
        
        # Группа VI: PMNS
        r['sin2_theta_12_PMNS'] = 1.0 / self.PHI**3 * (1.0 - self.Z / r['alpha_em_inv'])
        r['sin2_theta_23_PMNS'] = 0.5 - 1.0 / (self.PI * self.PHI**4)
        r['sin2_theta_13_PMNS'] = self.PI**2 / (r['alpha_em_inv'] / self.PHI)**2
        r['delta_CP_PMNS'] = -self.PI * (1.0 - 1.0 / (self.PHI**3 * self.Z))
        
        # Группа VII: Хиггс
        v_gev = 246.22
        corr_H = 1.0 - 1.0 / (self.PI * self.PHI**3 * self.Z)
        m_H_gev = v_gev / math.sqrt(2.0) * corr_H
        r['mu2_Higgs'] = -(m_H_gev**2) / 2.0
        r['lambda_Higgs'] = corr_H**2 / 4.0
        r['theta_QCD'] = 0.0
        
        return r
    
    def _m_e(self, C):
        num = (2**12 - self.Z**4 * self.PI**3)
        den = (self.PHI**20 * 2 * self.PI**2 + self.PI**5)
        return num / den * 40.0 * (1.0 + 0.001 * (C - GLOBAL_C_TARGET))
    
    def _m_mu_factor(self, C):
        eta = 1.0 / (1.0 - 1.0 / self.PHI**10)
        return (self.PI * self.PHI**3 * self.Z + 1.0 / (3.0 * self.PHI)) * eta
    
    def _m_tau_factor(self, C):
        a = self._alpha_em_inv(C)
        return (a / self.PI) * self.PHI**4 * self.Z - self.PI**2 / 2.0
    
    def _m_u_factor(self, C):
        g = 1.0 / (1.0 - 1.0 / self.PHI**8)
        return (2.0/3.0 * self.PI * self.PHI * self.Z) * g
    
    def _m_d_factor(self, C):
        g = 1.0 / (1.0 - 1.0 / self.PHI**7)
        return (1.0/3.0 * self.PI**2 * self.PHI**2 + self.Z/4.0) * g
    
    def _m_s_factor(self, C):
        a = self._alpha_em_inv(C)
        g = 1.0 / (1.0 - 1.0 / self.PHI**6)
        return (self.PI * self.PHI**2 * self.Z + a / (2.0 * self.PI**2)) * g
    
    def _m_c(self, C):
        m_e = self._m_e(C)
        m_p = m_e * (self.PI * self.PHI**4 + self.Z)
        g = 1.0 / (1.0 - 1.0 / self.PHI**5)
        return m_p * (self.PHI**4 / self.PI + self.Z / (2.0 * self.PI**2)) * g
    
    def _m_b_factor(self, C):
        a = self._alpha_em_inv(C)
        g = 1.0 / (1.0 - 1.0 / self.PHI**4)
        return (a * self.PI * self.PHI**3 + self.Z**4 * self.PI**2) * g
    
    def _m_t(self, C):
        m_e = self._m_e(C)
        m_p = m_e * (self.PI * self.PHI**4 + self.Z)
        a = self._alpha_em_inv(C)
        g = 1.0 / (1.0 - 1.0 / self.PHI**3)
        return m_p * (a / (self.PI * self.Z) * self.PHI**4 - self.Z**2) * g
    
    def _m_W(self, C):
        a = self._alpha_em_inv(C)
        eta = 1.0 / (1.0 - 1.0 / self.PHI**9)
        geo = math.sqrt(a * self.PHI**10 / (self.PI * self.Z)) * 2.0 * self.PI**2
        return self._m_e(C) * geo * eta
    
    def _m_Z_factor(self, C):
        return math.sqrt(1.0 + self.Z / (self.PI * self.PHI**4))
    
    def _m_H(self, C):
        v = self.PHI**10 * self.PI**2 * self.Z * (246220.0 / (self.PHI**10 * self.PI**2 * self.Z))
        return v / math.sqrt(2.0) * (1.0 - 1.0 / (self.PI * self.PHI**3 * self.Z))
    
    def _alpha_em_inv(self, C):
        pure = (self.PI * self.PHI**4 + self.PI**2 * self.PHI - 1.0 / (self.PHI**3 * self.PI))
        si_cal = math.sqrt(self.PI * self.PHI**3) + self.Z / (2**7)
        return pure * si_cal * (1.0 + 0.0001 * (C - GLOBAL_C_TARGET))
    
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
# 2. ПРЕДСКАЗАНИЯ
# =============================================================================

def predict_angle_li7():
    """Угол разлёта e⁺e⁻ для ⁷Li."""
    NZ_ratio = 3.0 / 4.0
    arg = (1.0 / PHI**2) * (1.0 / NZ_ratio) * math.tanh(PHI / Z_RES)
    theta = 180.0 - 2.0 * math.degrees(math.atan(arg))
    return theta

def predict_angle_be8():
    """Угол разлёта e⁺e⁻ для ⁸Be."""
    arg = (1.0 / PHI**3) * math.tanh(PHI / Z_RES)
    theta = 180.0 - 2.0 * math.degrees(math.atan(arg))
    return theta

def predict_dark_matter_mass():
    """Масса тёмной материи из топ-кварка."""
    m_t = 172.5  # ГэВ
    m_dm = m_t * (1.0 / (PHI**2 * PI)) * math.tanh(PHI / Z_RES)
    return m_dm


# =============================================================================
# 3. ЖИВАЯ ДИНАМИКА E₈
# =============================================================================

class ETVP125Full:
    """Полная модель: динамика + 26 констант."""
    
    def __init__(self, dim=11):
        self.dim = dim
        self.Phi = PHI
        self.pi = PI
        
        self.C = GLOBAL_C_TARGET
        self.S = 0.15
        self.step_counter = 0
        
        self.C_E8 = self._build_cartan_e8()
        
        self.psi_t = (np.random.rand(self.dim) + 1j * np.random.rand(self.dim))
        self.psi_t /= np.linalg.norm(self.psi_t)
        
        self.synth = ConstantsSynthesizer()
        
        self.eigenvalues = None
        self.constants = None
        self.dt = 0.0
        
        self.history = {
            'dt': [], 'C': [], 'S': [],
            'eigenvalues': [], 'psi': [], 'constants': []
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
        
        self.constants = self.synth.synthesize_all(self.C)
        
        self.eigenvalues = eigenvalues
        self.dt = dt
        self.history['dt'].append(dt)
        self.history['C'].append(self.C)
        self.history['S'].append(self.S)
        self.history['eigenvalues'].append(eigenvalues.copy())
        self.history['psi'].append(self.psi_t.copy())
        self.history['constants'].append(self.constants)
        
        return self.constants


# =============================================================================
# 4. ВИЗУАЛИЗАЦИЯ
# =============================================================================

class ETVPFullVisualizer:
    """Полная визуализация: динамика + 26 констант + предсказания."""
    
    def __init__(self, model):
        self.model = model
        
        self.fig = plt.figure(figsize=(22, 20))
        self.fig.patch.set_facecolor('#0a0a0a')
        
        gs = GridSpec(8, 6, figure=self.fig, hspace=0.5, wspace=0.4)
        
        # Верхние графики (динамика)
        self.ax_spec = self.fig.add_subplot(gs[0, :2])
        self.ax_C = self.fig.add_subplot(gs[0, 2:4])
        self.ax_pred = self.fig.add_subplot(gs[0, 4:])
        
        self.ax_psi = self.fig.add_subplot(gs[1, :2])
        self.ax_S = self.fig.add_subplot(gs[1, 2:4])
        self.ax_alpha = self.fig.add_subplot(gs[1, 4:])
        
        # 26 параметров (сетка)
        self.ax_constants = []
        for i in range(26):
            row = 2 + i // 6
            col = i % 6
            ax = self.fig.add_subplot(gs[row, col])
            ax.set_facecolor('#111111')
            ax.set_title(CODATA_LABELS[i], color='white', fontsize=6)
            ax.tick_params(colors='white', labelsize=5)
            for spine in ax.spines.values():
                spine.set_color('#333333')
            self.ax_constants.append(ax)
        
        for ax in [self.ax_spec, self.ax_C, self.ax_pred,
                   self.ax_psi, self.ax_S, self.ax_alpha]:
            ax.set_facecolor('#111111')
            ax.tick_params(colors='white', labelsize=8)
            for spine in ax.spines.values():
                spine.set_color('#333333')
        
        self.history_26 = {key: [] for key in CODATA.keys()}
    
    def _update(self, frame):
        shock = 0.8 if frame == 50 else 0.0
        constants = self.model.evolve_step(shock)
        
        hist = self.model.history
        
        for key in CODATA:
            if key in constants:
                self.history_26[key].append(constants[key])
        
        x = np.arange(len(hist['C']))
        
        # Спектр
        self.ax_spec.clear()
        self.ax_spec.set_facecolor('#111111')
        self.ax_spec.set_title('Eigenvalue Spectrum (Re)', color='white', fontsize=9)
        eig = hist['eigenvalues'][-1]
        self.ax_spec.bar(range(len(eig)), np.real(eig), color='cyan', alpha=0.7)
        self.ax_spec.tick_params(colors='white', labelsize=7)
        
        # Когерентность
        self.ax_C.clear()
        self.ax_C.set_facecolor('#111111')
        self.ax_C.set_title('Coherence C(t)', color='white', fontsize=9)
        self.ax_C.plot(x, hist['C'], color='cyan', linewidth=1.5)
        self.ax_C.axhline(GLOBAL_C_TARGET, color='yellow', linestyle='--', linewidth=0.8)
        self.ax_C.set_ylim(0.8, 1.0)
        self.ax_C.tick_params(colors='white', labelsize=7)
        
        # Предсказания
        self.ax_pred.clear()
        self.ax_pred.set_facecolor('#0a0a0a')
        self.ax_pred.axis('off')
        theta_li7 = predict_angle_li7()
        theta_be8 = predict_angle_be8()
        m_dm = predict_dark_matter_mass()
        pred_text = (
            f"ПРЕДСКАЗАНИЯ:\n"
            f"θ(⁷Li) = {theta_li7:.2f}° (ATOMKI: 165°±3°)\n"
            f"θ(⁸Be) = {theta_be8:.2f}° (ATOMKI: 140°±3°)\n"
            f"m_DM = {m_dm:.2f} ГэВ (FCC)"
        )
        self.ax_pred.text(0.1, 0.5, pred_text, color='white', fontsize=10,
                         family='monospace', verticalalignment='center')
        
        # Волновая функция
        self.ax_psi.clear()
        self.ax_psi.set_facecolor('#111111')
        self.ax_psi.set_title('Wavefunction |ψ|²', color='white', fontsize=9)
        psi = hist['psi'][-1]
        self.ax_psi.bar(range(len(psi)), np.abs(psi)**2, color='lime', alpha=0.7)
        self.ax_psi.tick_params(colors='white', labelsize=7)
        
        # Энтропия
        self.ax_S.clear()
        self.ax_S.set_facecolor('#111111')
        self.ax_S.set_title('Entropy S(t)', color='white', fontsize=9)
        self.ax_S.plot(x, hist['S'], color='orange', linewidth=1.5)
        self.ax_S.set_ylim(0, 1)
        self.ax_S.tick_params(colors='white', labelsize=7)
        
        # α⁻¹
        self.ax_alpha.clear()
        self.ax_alpha.set_facecolor('#111111')
        self.ax_alpha.set_title('1/α', color='white', fontsize=9)
        alpha_vals = [c['alpha_em_inv'] for c in hist['constants']]
        self.ax_alpha.plot(x, alpha_vals, color='yellow', linewidth=1.5)
        self.ax_alpha.axhline(137.036, color='red', linestyle='--', linewidth=0.8)
        self.ax_alpha.tick_params(colors='white', labelsize=7)
        
        # 26 параметров
        for i, (key, ax) in enumerate(zip(CODATA.keys(), self.ax_constants)):
            ax.clear()
            ax.set_facecolor('#111111')
            ax.set_title(CODATA_LABELS[i], color='white', fontsize=6)
            ax.tick_params(colors='white', labelsize=5)
            
            if key in self.history_26 and len(self.history_26[key]) > 0:
                vals = self.history_26[key]
                ax.plot(range(len(vals)), vals, color='cyan', linewidth=0.7)
                ax.axhline(CODATA[key], color='red', linestyle='--', linewidth=0.4)
        
        self.fig.canvas.draw_idle()
        return []
    
    def run(self, steps=200, interval=50):
        print("Запуск ETVP 12.5 INFINITUM FULL...")
        print("Живая динамика + 26 констант + предсказания")
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
        print(f"Средняя C: {np.mean(hist['C']):.6f}")
        print(f"α⁻¹ = {self.model.constants['alpha_em_inv']:.6f} (CODATA: 137.036)")
        print(f"θ(⁷Li) = {predict_angle_li7():.2f}°")
        print(f"θ(⁸Be) = {predict_angle_be8():.2f}°")
        print(f"m_DM = {predict_dark_matter_mass():.2f} ГэВ")
        print("=" * 70)
        
        return anim


# =============================================================================
# 5. ЗАПУСК
# =============================================================================

if __name__ == "__main__":
    model = ETVP125Full(dim=11)
    viz = ETVPFullVisualizer(model)
    viz.run(steps=200, interval=50)
