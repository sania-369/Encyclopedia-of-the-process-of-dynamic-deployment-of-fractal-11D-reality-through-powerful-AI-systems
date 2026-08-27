#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
ETVP 12.5 TOTH — Единая Формула Поля из Книги Тота
================================================================================
C = (Φ / √3) · tanh( ∇Ψ / (S_ext + S_int) )

Все параметры выводятся из этой формулы.
Живая динамика + ASCII-визуализация + matplotlib.

БЕЗ экспериментальных констант. Только геометрия и формула Тота.
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

# ANSI-цвета
GREEN = '\033[92m'
YELLOW = '\033[93m'
ORANGE = '\033[91m'
RED = '\033[31m'
RESET = '\033[0m'
CYAN = '\033[96m'


# =============================================================================
# 1. ЕДИНАЯ ФОРМУЛА ПОЛЯ (ТОТ)
# =============================================================================

def toth_coherence(nabla_psi, S_ext, S_int):
    """
    C = (Φ / √3) · tanh( ∇Ψ / (S_ext + S_int) )
    
    Args:
        nabla_psi: градиент плотности реальности
        S_ext: внешняя энтропия
        S_int: внутренняя энтропия
    
    Returns:
        C: когерентность
    """
    denominator = S_ext + S_int + 1e-12
    argument = nabla_psi / denominator
    tanh_val = math.tanh(argument)
    C = (PHI / Z_RES) * tanh_val
    
    # Ограничение через Z-принцип
    return np.clip(C, GLOBAL_C_MIN, GLOBAL_C_MAX)


def toth_nabla_psi(C, S_ext, S_int):
    """
    Обратная формула: ∇Ψ = (S_ext + S_int) · arctanh(C · √3 / Φ)
    """
    arg = C * Z_RES / PHI
    arg = np.clip(arg, -0.999, 0.999)
    return (S_ext + S_int) * math.atanh(arg)


# =============================================================================
# 2. ЖИВАЯ ДИНАМИКА НА ОСНОВЕ ФОРМУЛЫ ТОТА
# =============================================================================

class ETVP125Toth:
    """
    Живая модель на основе Единой Формулы Поля.
    """
    
    def __init__(self, dim=11):
        self.dim = dim
        self.Phi = PHI
        self.pi = PI
        self.Z = Z_RES
        
        self.C = GLOBAL_C_TARGET
        self.S_ext = 0.10  # Внешняя энтропия
        self.S_int = 0.05  # Внутренняя энтропия
        self.nabla_psi = 0.0
        
        self.step_counter = 0
        
        # Матрица Картана E₈
        self.C_E8 = self._build_cartan_e8()
        
        # Живой хаос
        self.psi_t = (np.random.rand(self.dim) + 1j * np.random.rand(self.dim))
        self.psi_t /= np.linalg.norm(self.psi_t)
        
        self.eigenvalues = None
        self.dt = 0.0
        self.history = {
            'C': [], 'S_ext': [], 'S_int': [], 
            'nabla_psi': [], 'dt': [], 'alpha_inv': []
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
        """
        Гамильтониан, зависящий от ∇Ψ из формулы Тота.
        """
        M = np.zeros((self.dim, self.dim), dtype=np.float64)
        M[0:8, 0:8] = self.C_E8.copy()
        
        # Когерентность из формулы Тота
        self.C = toth_coherence(self.nabla_psi, self.S_ext, self.S_int)
        
        # Влияние когерентности на матрицу
        M = M * (1.0 + 0.1 * (self.C - GLOBAL_C_TARGET))
        
        # Деформация от градиента Ψ
        i_idx = np.arange(self.dim)[:, None]
        j_idx = np.arange(self.dim)[None, :]
        deformation = self.nabla_psi * 0.01 * np.sin(i_idx * 0.7 + j_idx * 1.3)
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
        self.phi = (self.pi / 2.0) * (1.0 - (self.C - GLOBAL_C_MIN) / (GLOBAL_C_MAX - GLOBAL_C_MIN))
        
        M_imag = np.zeros((self.dim, self.dim), dtype=np.float64)
        for i in range(self.dim):
            for j in range(self.dim):
                geom_factor = np.tan(self.phi + 0.1 * (i - j) + reality_flux * 0.0001)
                M_imag[i, j] = M[i, j] * geom_factor
        
        M_imag = (M_imag + M_imag.T) / 2.0
        
        # Шум реальности
        reality_noise = np.random.randn(self.dim, self.dim) * 0.0005 * abs(reality_flux)
        M_imag += reality_noise
        
        return M + 1j * M_imag
    
    def evolve_step(self, reality_flux=0.0):
        """
        Один шаг эволюции на основе формулы Тота.
        """
        self.step_counter += 1
        
        # 1. Обновление энтропий
        self.S_ext += reality_flux * 0.001
        self.S_ext = np.clip(self.S_ext, 0.001, 0.5)
        
        self.S_int = 0.05 * (1.0 + 0.5 * math.sin(self.step_counter * 0.1))
        self.S_int = np.clip(self.S_int, 0.001, 0.5)
        
        # 2. Вычисление градиента Ψ из спектра
        if self.eigenvalues is not None:
            # ∇Ψ = разность между первым и последним собственными значениями
            self.nabla_psi = np.real(self.eigenvalues[0] - self.eigenvalues[-1]) * 0.01
        else:
            self.nabla_psi = 0.5
        
        # 3. Когерентность по формуле Тота
        self.C = toth_coherence(self.nabla_psi, self.S_ext, self.S_int)
        
        # 4. Гамильтониан
        H = self._build_hamiltonian(reality_flux)
        
        # 5. Спектр
        eigenvalues = np.linalg.eigvals(H)
        eigenvalues = eigenvalues[np.argsort(np.abs(eigenvalues))[::-1]]
        
        spectral_gap = np.abs(eigenvalues[0]) - np.abs(eigenvalues[-1])
        
        if spectral_gap < 1e-9 or np.isnan(spectral_gap):
            dt = 1e-6
        else:
            dt_ratio = np.imag(eigenvalues[-1] / eigenvalues[0])
            dt_gap = 1.0 / spectral_gap
            dt = dt_ratio if abs(dt_ratio) > 1e-9 else dt_gap
        
        # 6. Эволюция волновой функции
        U = expm(-1j * H * dt)
        self.psi_t = U @ self.psi_t
        
        norm = np.vdot(self.psi_t, self.psi_t).real
        if norm > 1e-12:
            self.psi_t /= np.sqrt(norm)
        
        # 7. α⁻¹ из спектра
        alpha_inv = np.real(eigenvalues[0] / eigenvalues[-1]) / self.Phi**2
        
        # Сохранение
        self.eigenvalues = eigenvalues
        self.dt = dt
        self.history['C'].append(self.C)
        self.history['S_ext'].append(self.S_ext)
        self.history['S_int'].append(self.S_int)
        self.history['nabla_psi'].append(self.nabla_psi)
        self.history['dt'].append(dt)
        self.history['alpha_inv'].append(alpha_inv)
        
        return self.C, alpha_inv, dt
    
    def get_toth_formula_text(self):
        """Текущее состояние формулы Тота."""
        return (f"C = (Φ/√3) · tanh(∇Ψ / (S_ext + S_int))\n"
                f"C = ({PHI:.4f}/{Z_RES:.4f}) · tanh({self.nabla_psi:.4f} / ({self.S_ext:.4f} + {self.S_int:.4f}))\n"
                f"C = {PHI/Z_RES:.4f} · tanh({self.nabla_psi / (self.S_ext + self.S_int):.4f})\n"
                f"C = {self.C:.6f}")


# =============================================================================
# 3. ШУМ РЕАЛЬНОСТИ
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
# 4. ASCII-ВИЗУАЛИЗАЦИЯ
# =============================================================================

class ASCIIVisualizer:
    def __init__(self, model, width=80):
        self.model = model
        self.width = width
        self.history_C = deque(maxlen=50)
        self.history_nabla = deque(maxlen=50)
    
    def _bar(self, value, max_val, width=40, char='█'):
        if max_val < 1e-12:
            return ''
        ratio = abs(value) / max_val
        ratio = max(0.0, min(1.0, ratio))
        filled = int(ratio * width)
        return char * filled + '·' * (width - filled)
    
    def _clear(self):
        if os.name == 'nt':
            os.system('cls')
        else:
            sys.stdout.write('\033[2J\033[H')
            sys.stdout.flush()
    
    def render(self, step=None, total=None):
        self._clear()
        
        print("═" * self.width)
        print(f"{CYAN}  ETVP 12.5 TOTH — Единая Формула Поля{RESET}")
        print("═" * self.width)
        
        if step is not None:
            print(f"  ШАГ: {step + 1} / {total}")
            print("─" * self.width)
        
        print()
        
        # Формула
        print(f"{CYAN}┌─ ЕДИНАЯ ФОРМУЛА ПОЛЯ ──────────────────────────────────┐{RESET}")
        print(f"│ C = (Φ/√3) · tanh(∇Ψ / (S_ext + S_int))")
        print(f"│")
        print(f"│ Φ = {PHI:.6f}")
        print(f"│ √3 = {Z_RES:.6f}")
        print(f"│ ∇Ψ = {self.model.nabla_psi:.6f}")
        print(f"│ S_ext = {self.model.S_ext:.6f}")
        print(f"│ S_int = {self.model.S_int:.6f}")
        print(f"│")
        print(f"│ {GREEN}C = {self.model.C:.6f}{RESET}")
        print(f"{CYAN}└──────────────────────────────────────────────────────────┘{RESET}")
        print()
        
        # Когерентность
        self.history_C.append(self.model.C)
        print(f"{CYAN}┌─ КОГЕРЕНТНОСТЬ C(t) ────────────────────────────────────┐{RESET}")
        bar_width = 50
        for i in range(8, -1, -1):
            level = GLOBAL_C_MIN + (GLOBAL_C_MAX - GLOBAL_C_MIN) * i / 8
            row = []
            for c_val in self.history_C:
                row.append('█' if c_val >= level else ' ')
            print(f"│ {level:.3f} │{''.join(row):<{bar_width}}│")
        print(f"{CYAN}└──────────────────────────────────────────────────────────┘{RESET}")
        print()
        
        # Градиент Ψ
        self.history_nabla.append(self.model.nabla_psi)
        print(f"{CYAN}┌─ ГРАДИЕНТ ∇Ψ ───────────────────────────────────────────┐{RESET}")
        bar_width = 50
        max_nabla = max(abs(max(self.history_nabla)), 1e-12)
        bar = self._bar(self.model.nabla_psi, max_nabla, bar_width)
        print(f"│ ∇Ψ = {self.model.nabla_psi:+.6f}")
        print(f"│ [{bar}]")
        print(f"{CYAN}└──────────────────────────────────────────────────────────┘{RESET}")
        print()
        
        # Энтропии
        print(f"{CYAN}┌─ ЭНТРОПИИ ──────────────────────────────────────────────┐{RESET}")
        bar_ext = self._bar(self.model.S_ext, 0.5, 30)
        bar_int = self._bar(self.model.S_int, 0.5, 30)
        print(f"│ S_ext = {self.model.S_ext:.6f} [{bar_ext}]")
        print(f"│ S_int = {self.model.S_int:.6f} [{bar_int}]")
        print(f"{CYAN}└──────────────────────────────────────────────────────────┘{RESET}")
        print()
        
        # dt и α⁻¹
        print(f"{CYAN}┌─ ПАРАМЕТРЫ ─────────────────────────────────────────────┐{RESET}")
        print(f"│ dt = {self.model.dt:.6e}")
        print(f"│ α⁻¹ = {self.model.history['alpha_inv'][-1]:.6f}" if self.model.history['alpha_inv'] else "│ α⁻¹ = —")
        print(f"│ Шаг: {self.model.step_counter}")
        print(f"{CYAN}└──────────────────────────────────────────────────────────┘{RESET}")
        print()
        
        print("═" * self.width)
    
    def run(self, steps=200, mode='auto', delay=0.2):
        noise = RealityNoise()
        
        print("Запуск ETVP 12.5 TOTH...")
        time.sleep(1)
        
        for step in range(steps):
            reality_flux = noise.get_flux()
            self.model.evolve_step(reality_flux)
            
            if mode == 'auto':
                self.render(step, steps)
                time.sleep(delay)
            elif mode == 'step':
                self.render(step, steps)
                user_input = input().strip().lower()
                if user_input == 'q':
                    break
                elif user_input == 'auto':
                    mode = 'auto'
        
        print("\n" + "═" * self.width)
        print("  ФИНАЛЬНЫЙ ОТЧЁТ:")
        print(f"  Средняя C: {np.mean(self.history_C):.6f}")
        print(f"  Средняя ∇Ψ: {np.mean(self.history_nabla):.6f}")
        print(f"  Шагов: {self.model.step_counter}")
        print("═" * self.width)


# =============================================================================
# 5. ЗАПУСК
# =============================================================================

if __name__ == "__main__":
    model = ETVP125Toth(dim=11)
    viz = ASCIIVisualizer(model, width=80)
    
    try:
        viz.run(steps=200, mode='auto', delay=0.2)
    except KeyboardInterrupt:
        print("\n\nВыход.")
        sys.exit(0)
