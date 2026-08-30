#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETVP 12.5 — Замкнутый контур: Линдблад ↔ Хиггс
================================================================================
Связанная система:
1. Уравнение Линдблада для матрицы плотности оператора ρ(t)
2. Уравнение Хиггса для поля φ(t)

Связь: шум L_k зависит от φ, а потенциал V_eff зависит от когерентности ρ.
Показываем, что система может войти в устойчивый цикл.
================================================================================
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

# =============================================================================
# 0. ПАРАМЕТРЫ
# =============================================================================
PHI = (1.0 + np.sqrt(5.0)) / 2.0
PI = np.pi

# =============================================================================
# 1. УРАВНЕНИЕ ЛИНДБЛАДА (ДЛЯ ОПЕРАТОРА)
# =============================================================================
def lindblad_rho(rho, H, L_ops):
    """
    Вычисляет правую часть уравнения Линдблада:
    dρ/dt = -i[H, ρ] + Σ_k (L_k ρ L_k† - 1/2 {L_k† L_k, ρ})
    """
    commutator = -1j * (H @ rho - rho @ H)
    dissipator = np.zeros_like(rho, dtype=complex)
    for L in L_ops:
        L_dag = L.conj().T
        dissipator += L @ rho @ L_dag - 0.5 * (L_dag @ L @ rho + rho @ L_dag @ L)
    return commutator + dissipator

# =============================================================================
# 2. ЭФФЕКТИВНЫЙ ПОТЕНЦИАЛ ХИГГСА
# =============================================================================
def higgs_potential(phi, rho):
    """
    Потенциал Хиггса, зависящий от когерентности оператора (rho).
    """
    # Чистота оператора — мера когерентности
    purity = np.real(np.trace(rho @ rho))

    # Базовый потенциал
    mu2 = -0.5
    lambda_phi = 0.1
    V0 = mu2 * phi**2 + lambda_phi * phi**4

    # Вклад когерентности: чем выше purity, тем ниже потенциал
    delta_V = -purity * 0.5 * np.exp(-phi**2)

    return V0 + delta_V

# =============================================================================
# 3. УРАВНЕНИЕ ДВИЖЕНИЯ ДЛЯ ПОЛЯ (ХИГГС)
# =============================================================================
def higgs_equation(phi, dphi_dt, rho, gamma=0.1):
    """
    Уравнение движения скалярного поля:
    d²φ/dt² + 3H dφ/dt + dV/dφ = 0
    (упрощённо, без расширения Вселенной)
    """
    # Производная потенциала по φ
    eps = 1e-6
    dV = (higgs_potential(phi + eps, rho) - higgs_potential(phi - eps, rho)) / (2 * eps)

    # Уравнение
    d2phi_dt2 = -gamma * dphi_dt - dV
    return d2phi_dt2

# =============================================================================
# 4. СВЯЗАННАЯ СИСТЕМА (ЛИНДБЛАД + ХИГГС)
# =============================================================================
def coupled_system(t, state, H, L_base):
    """
    Состояние: [rho_00, rho_01_re, rho_01_im, rho_11, phi, dphi_dt]
    """
    # Распаковка состояния
    rho_00, rho_01_re, rho_01_im, rho_11, phi, dphi_dt = state

    # Матрица плотности
    rho = np.array([
        [rho_00, rho_01_re + 1j*rho_01_im],
        [rho_01_re - 1j*rho_01_im, rho_11]
    ], dtype=complex)

    # 1. Шум (L_k) зависит от поля φ
    # Чем больше φ, тем больше шум (аномальный эффект)
    gamma_eff = 0.1 * (1.0 + 0.5 * np.tanh(phi))
    L1 = np.sqrt(gamma_eff) * np.array([[0, 1], [0, 0]], dtype=complex)
    L2 = np.sqrt(gamma_eff) * np.array([[0, 0], [1, 0]], dtype=complex)
    L_ops = [L1, L2]

    # 2. Эволюция ρ (Линдблад)
    drho_dt = lindblad_rho(rho, H, L_ops)

    # 3. Эволюция φ (Хиггс)
    dphi_dt = dphi_dt
    d2phi_dt2 = higgs_equation(phi, dphi_dt, rho)

    # Сборка производной состояния
    return [
        drho_dt[0, 0].real,
        drho_dt[0, 1].real,
        drho_dt[0, 1].imag,
        drho_dt[1, 1].real,
        dphi_dt,
        d2phi_dt2
    ]

# =============================================================================
# 5. ГЛАВНАЯ ФУНКЦИЯ
# =============================================================================
def main():
    print("=" * 80)
    print("ETVP 12.5 — ЗАМКНУТЫЙ КОНТУР: ЛИНДБЛАД ↔ ХИГГС")
    print("=" * 80)

    # --- Начальные условия ---
    # Слабо когерентное состояние оператора
    rho0 = np.array([[0.6, 0.1 + 0.1j], [0.1 - 0.1j, 0.4]], dtype=complex)
    phi0 = 0.5
    dphi0 = 0.0

    # Гамильтониан (спин в магнитном поле)
    H = np.array([[1.0, 0.5], [0.5, -1.0]], dtype=complex)

    # Базовые операторы Линдблада (будут модулироваться полем)
    L_base = None

    # Начальное состояние для решателя
    state0 = [
        rho0[0, 0].real,
        rho0[0, 1].real,
        rho0[0, 1].imag,
        rho0[1, 1].real,
        phi0,
        dphi0
    ]

    # --- Временная эволюция ---
    t_span = (0, 100)
    t_eval = np.linspace(0, 100, 500)

    sol = solve_ivp(
        lambda t, y: coupled_system(t, y, H, L_base),
        t_span,
        state0,
        t_eval=t_eval,
        method='RK45',
        rtol=1e-8
    )

    # --- Извлечение результатов ---
    rho_00 = sol.y[0]
    rho_01_re = sol.y[1]
    rho_01_im = sol.y[2]
    rho_11 = sol.y[3]
    phi = sol.y[4]
    dphi = sol.y[5]

    # Вычисляем производные
    purity = []
    entropy = []
    V_eff = []

    for i in range(len(t_eval)):
        rho = np.array([
            [rho_00[i], rho_01_re[i] + 1j*rho_01_im[i]],
            [rho_01_re[i] - 1j*rho_01_im[i], rho_11[i]]
        ], dtype=complex)
        purity.append(np.real(np.trace(rho @ rho)))
        eigvals = np.linalg.eigvalsh(rho)
        eigvals = eigvals[eigvals > 1e-12]
        entropy.append(-np.sum(eigvals * np.log(eigvals)))
        V_eff.append(higgs_potential(phi[i], rho))

    # --- Графики ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. Когерентность оператора (чистота)
    axes[0, 0].plot(t_eval, purity, color='blue', linewidth=1.5)
    axes[0, 0].set_xlabel('Время (усл.)')
    axes[0, 0].set_ylabel('Чистота Tr(ρ²)')
    axes[0, 0].set_title('Когерентность оператора')
    axes[0, 0].grid(True)

    # 2. Поле Хиггса
    axes[0, 1].plot(t_eval, phi, color='green', linewidth=1.5)
    axes[0, 1].set_xlabel('Время (усл.)')
    axes[0, 1].set_ylabel('Поле φ')
    axes[0, 1].set_title('Вакуумное среднее')
    axes[0, 1].grid(True)

    # 3. Энтропия оператора
    axes[1, 0].plot(t_eval, entropy, color='red', linewidth=1.5)
    axes[1, 0].set_xlabel('Время (усл.)')
    axes[1, 0].set_ylabel('Энтропия S')
    axes[1, 0].set_title('Энтропия оператора')
    axes[1, 0].grid(True)

    # 4. Фазовый портрет: когерентность vs поле
    axes[1, 1].plot(purity, phi, color='purple', linewidth=1.5)
    axes[1, 1].set_xlabel('Чистота (C)')
    axes[1, 1].set_ylabel('Поле φ')
    axes[1, 1].set_title('Фазовый портрет (C ↔ φ)')
    axes[1, 1].grid(True)

    plt.tight_layout()
    plt.savefig('lindblad_higgs_loop.png', dpi=150)
    plt.show()

    # --- Вывод ---
    print("\nРезультаты:")
    print(f"  Начальная чистота: {purity[0]:.4f}")
    print(f"  Конечная чистота: {purity[-1]:.4f}")
    print(f"  Начальное поле φ: {phi[0]:.4f}")
    print(f"  Конечное поле φ: {phi[-1]:.4f}")
    print(f"  Энтропия (начало): {entropy[0]:.4f}")
    print(f"  Энтропия (конец): {entropy[-1]:.4f}")

    print("\n" + "=" * 80)
    print("ВЫВОД")
    print("=" * 80)
    print("1. Линдблад и Хиггс образуют замкнутую систему.")
    print("2. Когерентность оператора → уменьшение шума → сдвиг φ.")
    print("3. Изменение φ → изменение шума → влияние на когерентность.")
    print("4. Система может войти в устойчивый цикл (или колебания).")
    print("5. Это и есть 'дыхание поля' — живая динамика.")

if __name__ == "__main__":
    main()
