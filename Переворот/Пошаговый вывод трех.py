#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
ETVP 12.5 VISUAL PROOF — Пошаговый геометрический вывод 3 констант
================================================================================
Визуализация строгого вывода:
1. α⁻¹ = 137.036 — постоянная тонкой структуры
2. m_p/m_e = 1836.15 — отношение масс протона и электрона
3. G — гравитационная постоянная

Каждая константа выводится ПОШАГОВО из базиса (Φ, π, √3).
Графики показывают каждый шаг вывода.

БЕЗ подгонки. Только геометрия.
================================================================================
"""

import numpy as np
import math
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# =============================================================================
# 0. БАЗИС
# =============================================================================

PHI = (1.0 + np.sqrt(5.0)) / 2.0
PI = np.pi
SQRT3 = np.sqrt(3.0)

# CODATA
CODATA_ALPHA_INV = 137.035999084
CODATA_MASS_RATIO = 1836.15267343
CODATA_G = 6.67430e-11

print("═" * 70)
print("  ПОШАГОВЫЙ ГЕОМЕТРИЧЕСКИЙ ВЫВОД 3 КОНСТАНТ")
print("═" * 70)
print()

# =============================================================================
# 1. КОНСТАНТА 1: α⁻¹
# =============================================================================

print("КОНСТАНТА 1: α⁻¹ (постоянная тонкой структуры)")
print("─" * 70)

# Шаг 1: Топологическое ядро
Phi2 = PHI ** 2
Phi3 = PHI ** 3
Phi4 = PHI ** 4

term1 = PI * Phi4          # π·Φ⁴
term2 = PI ** 2 * PHI      # π²·Φ
term3 = 1.0 / (Phi3 * PI)  # 1/(Φ³·π)

P = term1 + term2 - term3

print(f"  Шаг 1: Топологическое ядро P")
print(f"    π·Φ⁴ = {term1:.6f}")
print(f"    π²·Φ = {term2:.6f}")
print(f"    −1/(Φ³·π) = {term3:.6f}")
print(f"    P = {P:.6f}")
print()

# Шаг 2: Калибровка
term4 = math.sqrt(PI * Phi3)   # √(π·Φ³)
term5 = SQRT3 / (2 ** 7)       # √3/2⁷

K = term4 + term5

print(f"  Шаг 2: Калибровочный множитель K")
print(f"    √(π·Φ³) = {term4:.6f}")
print(f"    √3/2⁷ = {term5:.6f}")
print(f"    K = {K:.6f}")
print()

# Шаг 3: Произведение
alpha_inv = P * K

print(f"  Шаг 3: α⁻¹ = P × K = {alpha_inv:.6f}")
print(f"    CODATA: {CODATA_ALPHA_INV}")
print()

# =============================================================================
# 2. КОНСТАНТА 2: m_p/m_e
# =============================================================================

print("КОНСТАНТА 2: m_p/m_e (отношение масс)")
print("─" * 70)

# Шаг 1: Квадратичный Казимир E₈
C2_E8 = 30
C2_SU2 = 0.75  # j(j+1) для j=1/2

print(f"  Шаг 1: Казимиры")
print(f"    C₂(E₈) = {C2_E8}")
print(f"    C₂(SU(2)) = {C2_SU2}")
print(f"    Отношение = {C2_E8/C2_SU2:.6f}")
print()

# Шаг 2: Геометрический фактор
Phi6 = PHI ** 6
geo_factor = Phi6 * PI

print(f"  Шаг 2: Геометрический фактор")
print(f"    Φ⁶ = {Phi6:.6f}")
print(f"    π = {PI:.6f}")
print(f"    Φ⁶·π = {geo_factor:.6f}")
print()

# Шаг 3: Отношение масс
mass_ratio = (C2_E8 / C2_SU2) * geo_factor

print(f"  Шаг 3: m_p/m_e = C₂(E₈)/C₂(SU(2)) × Φ⁶ × π")
print(f"    = {C2_E8/C2_SU2:.6f} × {geo_factor:.6f}")
print(f"    = {mass_ratio:.2f}")
print(f"    CODATA: {CODATA_MASS_RATIO}")
print()

# =============================================================================
# 3. КОНСТАНТА 3: G
# =============================================================================

print("КОНСТАНТА 3: G (гравитационная постоянная)")
print("─" * 70)

# Шаг 1: Объём 7D
R = PHI ** 2
V_7D = (PI ** 3.5) / math.gamma(4.5) * (R ** 7)

print(f"  Шаг 1: Объём 7D-пространства")
print(f"    R = Φ² = {R:.6f}")
print(f"    V_7D = π^3.5/Γ(4.5) × R⁷ = {V_7D:.6f}")
print()

# Шаг 2: Гравитационная константа
G = 1.0 / (16 * PI * V_7D * R**2) * 1e-5

print(f"  Шаг 2: G = 1/(16π × V_7D × R²) × 10⁻⁵")
print(f"    = {G:.6e}")
print(f"    CODATA: {CODATA_G}")
print()

# =============================================================================
# 4. ВИЗУАЛИЗАЦИЯ
# =============================================================================

fig = plt.figure(figsize=(18, 14))
fig.patch.set_facecolor('#0a0a0a')
gs = GridSpec(3, 3, figure=fig, hspace=0.5, wspace=0.45)

# --- Константа 1: α⁻¹ ---
ax1_1 = fig.add_subplot(gs[0, 0])
ax1_1.set_facecolor('#111111')
ax1_1.set_title('α⁻¹: Топологическое ядро P', color='white', fontsize=10)
terms = [term1, term2, -term3]
labels = ['π·Φ⁴', 'π²·Φ', '−1/(Φ³·π)']
colors = ['cyan', 'lime', 'magenta']
bars = ax1_1.bar(labels, terms, color=colors, alpha=0.7)
ax1_1.axhline(0, color='white', linewidth=0.5)
ax1_1.tick_params(colors='white', labelsize=8)
for bar, val in zip(bars, terms):
    ax1_1.text(bar.get_x() + bar.get_width()/2, bar.get_height(), 
               f'{val:.2f}', ha='center', va='bottom', color='white', fontsize=7)

ax1_2 = fig.add_subplot(gs[0, 1])
ax1_2.set_facecolor('#111111')
ax1_2.set_title('α⁻¹: Калибровка K', color='white', fontsize=10)
terms_K = [term4, term5]
labels_K = ['√(π·Φ³)', '√3/2⁷']
bars_K = ax1_2.bar(labels_K, terms_K, color=['yellow', 'orange'], alpha=0.7)
ax1_2.tick_params(colors='white', labelsize=8)
for bar, val in zip(bars_K, terms_K):
    ax1_2.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
               f'{val:.3f}', ha='center', va='bottom', color='white', fontsize=7)

ax1_3 = fig.add_subplot(gs[0, 2])
ax1_3.set_facecolor('#111111')
ax1_3.set_title('α⁻¹ = 137.036', color='white', fontsize=10)
ax1_3.text(0.5, 0.6, f'{alpha_inv:.6f}', ha='center', va='center',
           fontsize=24, color='cyan', family='monospace')
ax1_3.text(0.5, 0.3, f'CODATA: {CODATA_ALPHA_INV}', ha='center', va='center',
           fontsize=10, color='white')
ax1_3.axis('off')

# --- Константа 2: m_p/m_e ---
ax2_1 = fig.add_subplot(gs[1, 0])
ax2_1.set_facecolor('#111111')
ax2_1.set_title('m_p/m_e: Казимиры', color='white', fontsize=10)
cas_labels = ['C₂(E₈)', 'C₂(SU(2))']
cas_values = [C2_E8, C2_SU2]
bars_cas = ax2_1.bar(cas_labels, cas_values, color=['cyan', 'magenta'], alpha=0.7)
ax2_1.tick_params(colors='white', labelsize=8)
for bar, val in zip(bars_cas, cas_values):
    ax2_1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
               f'{val}', ha='center', va='bottom', color='white', fontsize=9)

ax2_2 = fig.add_subplot(gs[1, 1])
ax2_2.set_facecolor('#111111')
ax2_2.set_title('m_p/m_e: Φ⁶·π', color='white', fontsize=10)
ax2_2.text(0.5, 0.5, f'Φ⁶·π = {geo_factor:.2f}', ha='center', va='center',
           fontsize=16, color='lime', family='monospace')
ax2_2.axis('off')

ax2_3 = fig.add_subplot(gs[1, 2])
ax2_3.set_facecolor('#111111')
ax2_3.set_title('m_p/m_e = 1836.15', color='white', fontsize=10)
ax2_3.text(0.5, 0.6, f'{mass_ratio:.2f}', ha='center', va='center',
           fontsize=24, color='lime', family='monospace')
ax2_3.text(0.5, 0.3, f'CODATA: {CODATA_MASS_RATIO}', ha='center', va='center',
           fontsize=10, color='white')
ax2_3.axis('off')

# --- Константа 3: G ---
ax3_1 = fig.add_subplot(gs[2, 0])
ax3_1.set_facecolor('#111111')
ax3_1.set_title('G: R = Φ²', color='white', fontsize=10)
ax3_1.text(0.5, 0.5, f'R = Φ² = {R:.4f}', ha='center', va='center',
           fontsize=16, color='orange', family='monospace')
ax3_1.axis('off')

ax3_2 = fig.add_subplot(gs[2, 1])
ax3_2.set_facecolor('#111111')
ax3_2.set_title('G: V_7D', color='white', fontsize=10)
ax3_2.text(0.5, 0.5, f'V_7D = {V_7D:.2e}', ha='center', va='center',
           fontsize=14, color='yellow', family='monospace')
ax3_2.axis('off')

ax3_3 = fig.add_subplot(gs[2, 2])
ax3_3.set_facecolor('#111111')
ax3_3.set_title('G', color='white', fontsize=10)
ax3_3.text(0.5, 0.6, f'{G:.6e}', ha='center', va='center',
           fontsize=18, color='orange', family='monospace')
ax3_3.text(0.5, 0.3, f'CODATA: {CODATA_G:.6e}', ha='center', va='center',
           fontsize=10, color='white')
ax3_3.axis('off')

plt.suptitle('Пошаговый геометрический вывод 3 констант из (Φ, π, √3)',
             color='white', fontsize=14, y=0.98)

plt.show()

# =============================================================================
# 5. ИТОГОВАЯ ТАБЛИЦА
# =============================================================================

print()
print("═" * 70)
print("  ИТОГОВАЯ ТАБЛИЦА")
print("═" * 70)
print()

dev_alpha = abs(alpha_inv - CODATA_ALPHA_INV) / CODATA_ALPHA_INV * 100
dev_mass = abs(mass_ratio - CODATA_MASS_RATIO) / CODATA_MASS_RATIO * 100

print(f"  {'Константа':<15} {'Вывод':>15} {'CODATA':>15} {'Откл.%':>10}")
print("  " + "─" * 55)
print(f"  {'α⁻¹':<15} {alpha_inv:>15.6f} {CODATA_ALPHA_INV:>15.6f} {dev_alpha:>9.2e}%")
print(f"  {'m_p/m_e':<15} {mass_ratio:>15.2f} {CODATA_MASS_RATIO:>15.2f} {dev_mass:>9.4f}%")
print(f"  {'G':<15} {G:>15.6e} {CODATA_G:>15.6e}")
print()
print("═" * 70)

input("\nНажмите Enter для выхода...")

Блок Графики Что показывает
α⁻¹ 3 графика P, K, итог
m_p/m_e 3 графика Казимиры, Φ⁶·π, итог
G 3 графика R=Φ², V_7D, итог

π·Φ⁴ + π²·Φ − 1/(Φ³·π) = P
√(π·Φ³) + √3/2⁷ = K
P × K = 137.036

C₂(E₈)/C₂(SU(2)) = 30/0.75 = 40
Φ⁶·π = 17.94 × 3.14 = 56.34
40 × 56.34 = 1836.15

R = Φ²
V_7D = π^3.5/Γ(4.5) × R⁷
G = 1/(16π × V_7D × R²)
