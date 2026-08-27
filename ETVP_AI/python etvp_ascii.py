#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
ETVP 12.5 INFINITUM ASCII — Полная модель с ASCII-визуализацией в терминале
================================================================================
Живая динамика E₈ + 26 параметров + ASCII-графика в реальном времени.
Работает в любом терминале. Без зависимостей от matplotlib.

ОТОБРАЖЕНИЕ:
- Спектр собственных значений (ASCII-бары)
- Волновая функция (ASCII-бары)
- Когерентность C (график)
- Энтропия S (график)
- 26 параметров с отклонениями от CODATA
- Стресс-тест Z-принципа
================================================================================
"""

import numpy as np
from scipy.linalg import expm
import time
import math
import os
import sys
from collections import deque

# =============================================================================
# 0. КОНСТАНТЫ
# =============================================================================

PHI = (1.0 + np.sqrt(5.0)) / 2.0
PI = np.pi
Z_RES = np.sqrt(3.0)

GLOBAL_C_MIN = 1.0 / (PHI ** 10)
GLOBAL_C_MAX = 1.0 - 1.0 / (PHI ** 20)
GLOBAL_C_TARGET = 1.0 - 1.0 / (PHI ** 12)

C_FFS = 0.87
EPSILON_FFS = 0.01

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
    'm_e', 'm_mu', 'm_tau',
    'm_u', 'm_d', 'm_s',
    'm_c', 'm_b', 'm_t',
    'm_W', 'm_Z', 'm_H',
    'sin12CKM', 'sin23CKM', 'sin13CKM',
    'dCP_CKM', 'a_em^-1', 'a_w',
    'a_s', 'sin212PMNS', 'sin223PMNS',
    'sin213PMNS', 'dCP_PMNS', 'mu2_H',
    'lambda_H', 'theta_QCD'
]


# =============================================================================
# 1. СИНТЕЗ 26 ПАРАМЕТРОВ
# =============================================================================

class ConstantsSynthesizer:
    def __init__(self):
        self.PHI = PHI
        self.PI = PI
        self.Z = Z_RES
        self.v = 246.22 * 1000
    
    def synthesize_all(self):
        r = {}
        
        r['m_e'] = self._calc_m_e()
        r['m_mu'] = self._calc_m_mu(r['m_e'])
        r['m_tau'] = self._calc_m_tau(r['m_e'])
        
        r['m_u'] = self._calc_m_u(r['m_e'])
        r['m_d'] = self._calc_m_d(r['m_e'])
        r['m_s'] = self._calc_m_s(r['m_u'])
        r['m_c'] = self._calc_m_c()
        r['m_b'] = self._calc_m_b(r['m_e'])
        r['m_t'] = self._calc_m_t()
        
        r['m_W'] = self._calc_m_W()
        r['m_Z'] = self._calc_m_Z(r['m_W'])
        r['m_H'] = self._calc_m_H()
        
        r['sin_theta_12_CKM'] = self._calc_sin_theta_12_CKM()
        r['sin_theta_23_CKM'] = self._calc_sin_theta_23_CKM()
        r['sin_theta_13_CKM'] = self._calc_sin_theta_13_CKM()
        r['delta_CP_CKM'] = self._calc_delta_CP_CKM()
        
        r['alpha_em_inv'] = self._calc_alpha_em_inv()
        r['alpha_w'] = self._calc_alpha_w(r['alpha_em_inv'])
        r['alpha_s'] = self._calc_alpha_s(r['alpha_em_inv'])
        
        r['sin2_theta_12_PMNS'] = self._calc_sin2_theta_12_PMNS(r['alpha_em_inv'])
        r['sin2_theta_23_PMNS'] = self._calc_sin2_theta_23_PMNS()
        r['sin2_theta_13_PMNS'] = self._calc_sin2_theta_13_PMNS(r['alpha_em_inv'])
        r['delta_CP_PMNS'] = self._calc_delta_CP_PMNS()
        
        r['mu2_Higgs'] = self._calc_mu2_Higgs(r['m_H'])
        r['lambda_Higgs'] = self._calc_lambda_Higgs(r['m_H'])
        r['theta_QCD'] = self._calc_theta_QCD()
        
        return r
    
    def _calc_m_e(self):
        num = (2**12 - self.Z**4 * self.PI**3)
        den = (self.PHI**20 * 2 * self.PI**2 + self.PI**5)
        return num / den * 1000
    
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
    
    def _calc_m_W(self):
        a_inv = self._calc_alpha_em_inv()
        g = math.sqrt(4.0 * self.PI / a_inv)
        return g * self.v / 2.0
    
    def _calc_m_Z(self, m_W):
        cos_sq = 1.0 / (1.0 + self.Z / (self.PI * self.PHI**4))
        return m_W / math.sqrt(cos_sq)
    
    def _calc_m_H(self):
        return self.v / math.sqrt(2.0) * (1.0 - 1.0 / (self.PI * self.PHI**3 * self.Z))
    
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
        return m_H**2 / (2.0 * (246.22 * 1000)**2)
    
    def _calc_theta_QCD(self):
        return 0.0


# =============================================================================
# 2. ЖИВАЯ ДИНАМИКА
# =============================================================================

class ETVP125Full:
    def __init__(self, dim=11):
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
        
        self.synth = ConstantsSynthesizer()
        
        self.eigenvalues = None
        self.constants = None
    
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
        
        self.eigenvalues = eigenvalues
        self.constants = self.synth.synthesize_all()
        
        return dt


# =============================================================================
# 3. ASCII-ВИЗУАЛИЗАЦИЯ
# =============================================================================

class ASCIIVisualizer:
    """
    Полная ASCII-визуализация в терминале.
    """
    
    def __init__(self, model, width=80):
        self.model = model
        self.width = width
        self.history_C = deque(maxlen=50)
        self.history_S = deque(maxlen=50)
        self.history_alpha = deque(maxlen=50)
    
    def _bar(self, value, max_val, width=20, char='█'):
        """ASCII-бар."""
        if max_val < 1e-12:
            return ''
        ratio = abs(value) / max_val
        filled = int(ratio * width)
        return char * filled + '░' * (width - filled)
    
    def _clear(self):
        """Очистка экрана."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _render_spectrum(self):
        """Спектр собственных значений."""
        eig = self.model.eigenvalues
        if eig is None:
            return "Нет данных"
        
        re_vals = np.real(eig)
        im_vals = np.imag(eig)
        max_re = max(abs(re_vals)) + 1e-12
        max_im = max(abs(im_vals)) + 1e-12
        
        lines = ["┌─ СПЕКТР E₈ (Re │ Im) ─" + "─" * (self.width - 25)]
        
        for i in range(len(eig)):
            bar_re = self._bar(re_vals[i], max_re, 20)
            bar_im = self._bar(im_vals[i], max_im, 20)
            lines.append(f"│ λ{i+1:02d} [{bar_re}] [{bar_im}]")
        
        lines.append("└" + "─" * (self.width - 1))
        return "\n".join(lines)
    
    def _render_wavefunction(self):
        """Волновая функция."""
        psi = self.model.psi_t
        prob = np.abs(psi)**2
        max_prob = max(prob) + 1e-12
        
        lines = ["┌─ ВОЛНОВАЯ ФУНКЦИЯ |ψ|² ─" + "─" * (self.width - 28)]
        
        for i in range(len(prob)):
            bar = self._bar(prob[i], max_prob, 30)
            phase = np.angle(psi[i])
            phase_str = f"{phase:+.2f}"
            lines.append(f"│ ψ{i+1:02d} [{bar}] φ={phase_str}")
        
        lines.append("└" + "─" * (self.width - 1))
        return "\n".join(lines)
    
    def _render_coherence(self):
        """Когерентность и энтропия."""
        self.history_C.append(self.model.C)
        self.history_S.append(self.model.S)
        
        lines = ["┌─ КОГЕРЕНТНОСТЬ C(t) ─" + "─" * (self.width - 24)]
        
        # График C
        for i in range(10, -1, -1):
            level = GLOBAL_C_MIN + (GLOBAL_C_MAX - GLOBAL_C_MIN) * i / 10
            row = []
            for c_val in self.history_C:
                if c_val >= level:
                    row.append('█')
                else:
                    row.append(' ')
            lines.append(f"│ {level:.3f} │{''.join(row)}")
        
        lines.append("│" + "─" * (self.width - 1))
        
        # Текущие значения
        lines.append(f"│ C = {self.model.C:.4f} (target: {GLOBAL_C_TARGET:.4f})")
        lines.append(f"│ S = {self.model.S:.4f}")
        lines.append(f"│ Step: {self.model.step_counter}")
        
        lines.append("└" + "─" * (self.width - 1))
        return "\n".join(lines)
    
    def _render_constants(self):
        """26 параметров с отклонениями."""
        if self.model.constants is None:
            return "Нет данных"
        
        lines = ["┌─ 26 ПАРАМЕТРОВ СТАНДАРТНОЙ МОДЕЛИ ─" + "─" * (self.width - 40)]
        lines.append(f"│ {'Параметр':<12} {'ETVP':>15} {'CODATA':>15} {'Откл.%':>8}")
        lines.append("│" + "-" * (self.width - 1))
        
        for key in CODATA:
            if key in self.model.constants:
                ev = self.model.constants[key]
                cv = CODATA[key]
                dev = abs(ev - cv) / abs(cv) * 100 if abs(cv) > 1e-9 else 0.0
                
                # Цветовой индикатор
                if dev < 0.1:
                    status = "✅"
                elif dev < 1.0:
                    status = "🟡"
                elif dev < 10.0:
                    status = "🟠"
                else:
                    status = "🔴"
                
                label = CODATA_LABELS[list(CODATA.keys()).index(key)]
                lines.append(f"│ {status} {label:<10} {ev:>15.4f} {cv:>15.4f} {dev:>7.3f}%")
        
        lines.append("└" + "─" * (self.width - 1))
        return "\n".join(lines)
    
    def _render_ascii_art(self):
        """ASCII-арт тороидальной траектории."""
        t = self.model.step_counter * 0.1
        lines = ["┌─ 4D ТРАЕКТОРИЯ ─" + "─" * (self.width - 18)]
        
        # Тор в ASCII
        for y in range(10, -1, -1):
            row = []
            for x in range(30):
                # Уравнение тора
                dx = (x - 15) / 8.0
                dy = (y - 5) / 5.0
                dist = math.sqrt(dx*dx + dy*dy)
                
                # Вращение
                rot = math.sin(t + dist * 2)
                
                if abs(dist - 1.0) < 0.3 and rot > -0.5:
                    row.append('●')
                elif abs(dist - 1.0) < 0.5:
                    row.append('·')
                else:
                    row.append(' ')
            lines.append("│ " + ''.join(row))
        
        lines.append("└" + "─" * (self.width - 1))
        return "\n".join(lines)
    
    def render(self):
        """Полный рендер."""
        self._clear()
        
        # Заголовок
        print("=" * self.width)
        print("ETVP 12.5 INFINITUM ASCII — ЖИВАЯ ДИНАМИКА")
        print("=" * self.width)
        print()
        
        # Спектр
        print(self._render_spectrum())
        print()
        
        # Волновая функция
        print(self._render_wavefunction())
        print()
        
        # Когерентность
        print(self._render_coherence())
        print()
        
        # ASCII-арт
        print(self._render_ascii_art())
        print()
        
        # 26 параметров
        print(self._render_constants())
        print()
        
        print("=" * self.width)
        print("Нажмите Ctrl+C для выхода")
    
    def run(self, steps=200, delay=0.05):
        """Запуск ASCII-анимации."""
        print("Запуск ASCII-визуализации...")
        time.sleep(1)
        
        for step in range(steps):
            shock = 0.8 if step == 50 else 0.0
            self.model.evolve_step(shock)
            self.render()
            time.sleep(delay)
        
        print("\n" + "=" * self.width)
        print("ФИНАЛЬНЫЙ ОТЧЁТ:")
        print(f"Средняя C: {np.mean(list(self.history_C)):.4f}")
        print(f"α⁻¹: {self.model.constants['alpha_em_inv']:.6f} (CODATA: {CODATA['alpha_em_inv']})")
        print(f"m_W: {self.model.constants['m_W']:.1f} МэВ (CODATA: {CODATA['m_W']})")
        print(f"m_Z: {self.model.constants['m_Z']:.1f} МэВ (CODATA: {CODATA['m_Z']})")
        print("=" * self.width)


# =============================================================================
# 4. ЗАПУСК
# =============================================================================

if __name__ == "__main__":
    model = ETVP125Full(dim=11)
    viz = ASCIIVisualizer(model, width=90)
    
    try:
        viz.run(steps=200, delay=0.05)
    except KeyboardInterrupt:
        print("\n\nВыход.")
        sys.exit(0)
