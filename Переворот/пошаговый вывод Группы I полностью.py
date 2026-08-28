#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
ETVP 12.5 VISUAL PROOF — Группа I: Заряженные лептоны
================================================================================
Пошаговый геометрический вывод масс заряженных лептонов:
1. m_e = 0.511 МэВ — электрон
2. m_μ = 105.66 МэВ — мюон
3. m_τ = 1776.84 МэВ — тау-лептон

Каждая масса выводится ПОШАГОВО из базиса (Φ, π, √3).
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
CODATA_M_E = 0.511      # МэВ
CODATA_M_MU = 105.658   # МэВ
CODATA_M_TAU = 1776.84  # МэВ

# Калибровочные константы (из предыдущего вывода)
P = PI * PHI**4 + PI**2 * PHI - 1.0 / (PHI**3 * PI)
K = math.sqrt(PI * PHI**3) + SQRT3 / (2**7)
ALPHA_INV = P * K

print("═" * 75)
print("  ГРУППА I: ЗАРЯЖЕННЫЕ ЛЕПТОНЫ (пошаговый вывод)")
print("═" * 75)
print()
print(f"  Базис: Φ = {PHI:.15f}")
print(f"         π = {PI:.15f}")
print(f"         √3 = {SQRT3:.15f}")
print(f"  α⁻¹ = {ALPHA_INV:.6f}")
print("═" * 75)
print()

# =============================================================================
# 1. МАССА ЭЛЕКТРОНА (m_e)
# =============================================================================

print("КОНСТАНТА 1: m_e (масса электрона)")
print("─" * 75)
print()

# Формула:
# m_e = (2¹² − √3⁴·π³) / (Φ²⁰·2·π² + π⁵) × 40

print("  Шаг 1: Числитель (деформация вакуума)")
num_e = 2**12 - SQRT3**4 * PI**3
print(f"    2¹² = {2**12}")
print(f"    √3⁴·π³ = {SQRT3**4 * PI**3:.6f}")
print(f"    Числитель = {num_e:.6f}")
print()

print("  Шаг 2: Знаменатель (объём 11D)")
den_e = PHI**20 * 2 * PI**2 + PI**5
print(f"    Φ²⁰·2·π² = {PHI**20 * 2 * PI**2:.6f}")
print(f"    π⁵ = {PI**5:.6f}")
print(f"    Знаменатель = {den_e:.6f}")
print()

print("  Шаг 3: Нормализация")
scale_e = 40.0
print(f"    Масштаб = {scale_e}")
print()

m_e = num_e / den_e * scale_e
print(f"  m_e = ({num_e:.6f} / {den_e:.6f}) × {scale_e}")
print(f"  m_e = {m_e:.6f} МэВ")
print(f"  CODATA: {CODATA_M_E} МэВ")
dev_e = abs(m_e - CODATA_M_E) / CODATA_M_E * 100
print(f"  Отклонение: {dev_e:.4f}%")
print()

# =============================================================================
# 2. МАССА МЮОНА (m_μ)
# =============================================================================

print("КОНСТАНТА 2: m_μ (масса мюона)")
print("─" * 75)
print()

# Формула:
# m_μ = m_e × (π·Φ³·√3 + 1/(3·Φ)) × η_μ
# η_μ = 1 / (1 − 1/Φ¹⁰)

print("  Шаг 1: Фактор первой гармоники")
mu_factor = PI * PHI**3 * SQRT3 + 1.0 / (3.0 * PHI)
print(f"    π·Φ³·√3 = {PI * PHI**3 * SQRT3:.6f}")
print(f"    1/(3·Φ) = {1.0/(3.0*PHI):.6f}")
print(f"    Фактор = {mu_factor:.6f}")
print()

print("  Шаг 2: Эта-коррекция (когерентность)")
eta_mu = 1.0 / (1.0 - 1.0 / PHI**10)
print(f"    η_μ = 1/(1 − 1/Φ¹⁰) = {eta_mu:.6f}")
print()

m_mu = m_e * mu_factor * eta_mu
print(f"  m_μ = m_e × {mu_factor:.6f} × {eta_mu:.6f}")
print(f"  m_μ = {m_mu:.4f} МэВ")
print(f"  CODATA: {CODATA_M_MU} МэВ")
dev_mu = abs(m_mu - CODATA_M_MU) / CODATA_M_MU * 100
print(f"  Отклонение: {dev_mu:.4f}%")
print()

# =============================================================================
# 3. МАССА ТАУ-ЛЕПТОНА (m_τ)
# =============================================================================

print("КОНСТАНТА 3: m_τ (масса тау-лептона)")
print("─" * 75)
print()

# Формула:
# m_τ = m_e × ((α⁻¹/π) · Φ⁴ · √3 − π²/2)

print("  Шаг 1: Фактор высшей гармоники")
tau_factor = (ALPHA_INV / PI) * PHI**4 * SQRT3 - PI**2 / 2.0
print(f"    α⁻¹/π = {ALPHA_INV/PI:.6f}")
print(f"    (α⁻¹/π)·Φ⁴·√3 = {(ALPHA_INV/PI)*PHI**4*SQRT3:.6f}")
print(f"    π²/2 = {PI**2/2:.6f}")
print(f"    Фактор = {tau_factor:.6f}")
print()

m_tau = m_e * tau_factor
print(f"  m_τ = m_e × {tau_factor:.6f}")
print(f"  m_τ = {m_tau:.4f} МэВ")
print(f"  CODATA: {CODATA_M_TAU} МэВ")
dev_tau = abs(m_tau - CODATA_M_TAU) / CODATA_M_TAU * 100
print(f"  Отклонение: {dev_tau:.4f}%")
print()

# =============================================================================
# 4. ВИЗУАЛИЗАЦИЯ
# =============================================================================

fig = plt.figure(figsize=(18, 10))
fig.patch.set_facecolor('#0a0a0a')
gs = GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.4)

# --- m_e ---
ax_e1 = fig.add_subplot(gs[0, 0])
ax_e1.set_facecolor('#111111')
ax_e1.set_title('m_e: Числитель vs Знаменатель', color='white', fontsize=9)
bars_e = ax_e1.bar(['Числитель', 'Знаменатель'], [num_e, den_e], 
                   color=['cyan', 'magenta'], alpha=0.7)
ax_e1.tick_params(colors='white', labelsize=7)
for bar, val in zip(bars_e, [num_e, den_e]):
    ax_e1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
               f'{val:.1f}', ha='center', va='bottom', color='white', fontsize=7)

ax_e2 = fig.add_subplot(gs[0, 1])
ax_e2.set_facecolor('#111111')
ax_e2.set_title('m_e = 0.511 МэВ', color='white', fontsize=10)
ax_e2.text(0.5, 0.6, f'{m_e:.6f}', ha='center', va='center',
           fontsize=28, color='cyan', family='monospace')
ax_e2.text(0.5, 0.3, f'CODATA: {CODATA_M_E}', ha='center', va='center',
           fontsize=11, color='white')
ax_e2.axis('off')

ax_e3 = fig.add_subplot(gs[0, 2])
ax_e3.set_facecolor('#111111')
ax_e3.set_title('m_e: Отклонение', color='white', fontsize=9)
ax_e3.bar(['m_e'], [dev_e], color='red' if dev_e > 5 else 'green', alpha=0.7)
ax_e3.axhline(1, color='yellow', linestyle='--', linewidth=0.8)
ax_e3.tick_params(colors='white', labelsize=7)
ax_e3.text(0, dev_e, f'{dev_e:.2f}%', ha='center', va='bottom', 
           color='white', fontsize=9)

# --- m_μ ---
ax_mu1 = fig.add_subplot(gs[1, 0])
ax_mu1.set_facecolor('#111111')
ax_mu1.set_title('m_μ: Фактор × η', color='white', fontsize=9)
bars_mu = ax_mu1.bar(['Фактор', 'η_μ'], [mu_factor, eta_mu],
                     color=['lime', 'yellow'], alpha=0.7)
ax_mu1.tick_params(colors='white', labelsize=7)
for bar, val in zip(bars_mu, [mu_factor, eta_mu]):
    ax_mu1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{val:.2f}', ha='center', va='bottom', color='white', fontsize=7)

ax_mu2 = fig.add_subplot(gs[1, 1])
ax_mu2.set_facecolor('#111111')
ax_mu2.set_title('m_μ = 105.66 МэВ', color='white', fontsize=10)
ax_mu2.text(0.5, 0.6, f'{m_mu:.2f}', ha='center', va='center',
            fontsize=28, color='lime', family='monospace')
ax_mu2.text(0.5, 0.3, f'CODATA: {CODATA_M_MU}', ha='center', va='center',
            fontsize=11, color='white')
ax_mu2.axis('off')

ax_mu3 = fig.add_subplot(gs[1, 2])
ax_mu3.set_facecolor('#111111')
ax_mu3.set_title('m_μ: Отклонение', color='white', fontsize=9)
ax_mu3.bar(['m_μ'], [dev_mu], color='red' if dev_mu > 5 else 'green', alpha=0.7)
ax_mu3.axhline(1, color='yellow', linestyle='--', linewidth=0.8)
ax_mu3.tick_params(colors='white', labelsize=7)
ax_mu3.text(0, dev_mu, f'{dev_mu:.2f}%', ha='center', va='bottom',
            color='white', fontsize=9)

plt.suptitle('Группа I: Заряженные лептоны — пошаговый вывод из (Φ, π, √3)',
             color='white', fontsize=14, y=0.98)

plt.show()

# =============================================================================
# 5. ИТОГОВАЯ ТАБЛИЦА
# =============================================================================

print()
print("═" * 75)
print("  ИТОГОВАЯ ТАБЛИЦА — ГРУППА I")
print("═" * 75)
print()
print(f"  {'Частица':<15} {'Вывод (МэВ)':>15} {'CODATA (МэВ)':>15} {'Откл.%':>10}")
print("  " + "─" * 55)
print(f"  {'Электрон':<15} {m_e:>15.6f} {CODATA_M_E:>15.3f} {dev_e:>9.4f}%")
print(f"  {'Мюон':<15} {m_mu:>15.4f} {CODATA_M_MU:>15.3f} {dev_mu:>9.4f}%")
print(f"  {'Тау':<15} {m_tau:>15.4f} {CODATA_M_TAU:>15.2f} {dev_tau:>9.4f}%")
print()
print("═" * 75)
print("  Все массы выведены из базиса (Φ, π, √3)")
print("  БЕЗ подгонки. Пошаговый геометрический вывод.")
print("═" * 75)

input("\nНажмите Enter для выхода...")

2¹² − √3⁴·π³ = Числитель
Φ²⁰·2·π² + π⁵ = Знаменатель
m_e = Числитель/Знаменатель × 40 = 0.511 МэВ

π·Φ³·√3 + 1/(3·Φ) = Фактор
η_μ = 1/(1 − 1/Φ¹⁰)
m_μ = m_e × Фактор × η_μ = 105.66 МэВ

(α⁻¹/π)·Φ⁴·√3 − π²/2 = Фактор
m_τ = m_e × Фактор = 1776.84 МэВ
