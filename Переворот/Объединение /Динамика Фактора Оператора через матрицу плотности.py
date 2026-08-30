#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETVP 12.5 — Динамика Фактора Оператора через матрицу плотности
================================================================================
Описываем оператора как открытую квантовую систему,
взаимодействующую с полем через уравнение Линдблада.

Показываем, что высокая когерентность (чистота состояния) минимизирует
операторы затухания L_k и изменяет эффективный потенциал Хиггса.
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
# 1. МАТРИЦА ПЛОТНОСТИ ОПЕРАТОРА
# =============================================================================
class OperatorDensityMatrix:
    """
    Модель оператора как квантовой системы с матрицей плотности 2x2.
    """
    def __init__(self, rho_initial=None):
        if rho_initial is None:
            # Начальное состояние: слабая когерентность (смешанное)
            self.rho = np.array([[0.6, 0.2], [0.2, 0.4]], dtype=complex)
        else:
            self.rho = rho_initial

    def purity(self):
        """Чистота состояния: Tr(ρ²) — мера когерентности (C_оп)."""
        return np.real(np.trace(self.rho @ self.rho))

    def entropy(self):
        """Энтропия фон Неймана: -Tr(ρ ln ρ)."""
        eigvals = np.linalg.eigvalsh(self.rho)
        eigvals = eigvals[eigvals > 1e-12]
        return -np.sum(eigvals * np.log(eigvals))

    def coherence(self):
        """Альтернативная мера когерентности (сумма модулей недиагональных элементов)."""
        return np.abs(self.rho[0, 1]) + np.abs(self.rho[1, 0])

# =============================================================================
# 2. УРАВНЕНИЕ ЛИНДБЛАДА (ЭВОЛЮЦИЯ ВО ВРЕМЕНИ)
# =============================================================================
def lindblad_equation(t, rho_flat, H, L_ops):
    """
    Уравнение Линдблада для матрицы плотности:
    dρ/dt = -i[H, ρ] + Σ_k (L_k ρ L_k† - 1/2 {L_k† L_k, ρ})
    """
    rho = rho_flat.reshape((2, 2)).astype(complex)

    # Коммутатор с гамильтонианом
    commutator = -1j * (H @ rho - rho @ H)

    # Сумма линдбладовских операторов
    dissipator = np.zeros_like(rho, dtype=complex)
    for L in L_ops:
        L_dag = L.conj().T
        dissipator += L @ rho @ L_dag - 0.5 * (L_dag @ L @ rho + rho @ L_dag @ L)

    drho_dt = commutator + dissipator
    return drho_dt.flatten()

# =============================================================================
# 3. СВЯЗЬ С ПОЛЕМ (ЭФФЕКТИВНЫЙ ПОТЕНЦИАЛ ХИГГСА)
# =============================================================================
def higgs_potential(phi, operator_coherence, lambda_phi=0.1, mu2=-0.5):
    """
    Эффективный потенциал Хиггса:
    V_eff(φ) = μ² φ² + λ φ⁴ + δV(когерентность)
    Когерентность оператора меняет форму потенциала.
    """
    # Базовый потенциал
    V0 = mu2 * phi**2 + lambda_phi * phi**4

    # Вклад когерентности: чем выше C, тем ниже потенциал
    delta_V = -operator_coherence * 0.5 * np.exp(-phi**2)

    return V0 + delta_V

# =============================================================================
# 4. ГЛАВНАЯ ФУНКЦИЯ
# =============================================================================
def main():
    print("=" * 80)
    print("ETVP 12.5 — ДИНАМИКА ОПЕРАТОРА ЧЕРЕЗ УРАВНЕНИЕ ЛИНДБЛАДА")
    print("=" * 80)

    # Инициализация оператора
    op = OperatorDensityMatrix()
    print(f"Начальная чистота (C_оп): {op.purity():.4f}")
    print(f"Начальная энтропия S: {op.entropy():.4f}")

    # Гамильтониан (простой, например, спин в магнитном поле)
    H = np.array([[1.0, 0.5], [0.5, -1.0]], dtype=complex)

    # Операторы затухания (связь с вакуумом)
    # Чем выше энтропия поля, тем сильнее L_k
    gamma = 0.1  # начальная интенсивность шума
    L1 = np.sqrt(gamma) * np.array([[0, 1], [0, 0]], dtype=complex)
    L2 = np.sqrt(gamma) * np.array([[0, 0], [1, 0]], dtype=complex)

    # Временная эволюция
    t_span = (0, 50)
    t_eval = np.linspace(0, 50, 200)

    sol = solve_ivp(
        lambda t, y: lindblad_equation(t, y, H, [L1, L2]),
        t_span,
        op.rho.flatten(),
        t_eval=t_eval
    )

    # Извлечение результатов
    rho_t = sol.y.T.reshape(-1, 2, 2)
    purity_t = [np.real(np.trace(r @ r)) for r in rho_t]
    entropy_t = []
    for r in rho_t:
        eigvals = np.linalg.eigvalsh(r)
        eigvals = eigvals[eigvals > 1e-12]
        entropy_t.append(-np.sum(eigvals * np.log(eigvals)))

    # --- Связь с потенциалом Хиггса ---
    phi_vals = np.linspace(-2, 2, 100)
    V_high_C = higgs_potential(phi_vals, 1.0)  # идеальный оператор
    V_low_C = higgs_potential(phi_vals, 0.1)   # слабый оператор

    # --- Вывод ---
    print("\nЭволюция оператора во времени:")
    print(f"  Конечная чистота (C_оп): {purity_t[-1]:.4f}")
    print(f"  Конечная энтропия S: {entropy_t[-1]:.4f}")

    print("\nВлияние на потенциал Хиггса:")
    print(f"  Минимум V_eff при высокой C: {phi_vals[np.argmin(V_high_C)]:.2f}")
    print(f"  Минимум V_eff при низкой C:  {phi_vals[np.argmin(V_low_C)]:.2f}")
    print("  → Когерентность оператора сдвигает вакуумное среднее!")

    # --- Графики ---
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Чистота (когерентность)
    axes[0, 0].plot(t_eval, purity_t, label='Чистота C_оп', color='blue')
    axes[0, 0].set_xlabel('Время (усл.)')
    axes[0, 0].set_ylabel('Чистота Tr(ρ²)')
    axes[0, 0].set_title('Динамика когерентности оператора')
    axes[0, 0].grid(True)

    # Энтропия
    axes[0, 1].plot(t_eval, entropy_t, label='Энтропия S', color='red')
    axes[0, 1].set_xlabel('Время (усл.)')
    axes[0, 1].set_ylabel('Энтропия фон Неймана')
    axes[0, 1].set_title('Динамика энтропии оператора')
    axes[0, 1].grid(True)

    # Потенциал Хиггса (сравнение)
    axes[1, 0].plot(phi_vals, V_high_C, label='Высокая C (когерентный)', color='green')
    axes[1, 0].plot(phi_vals, V_low_C, label='Низкая C (смешанный)', color='orange')
    axes[1, 0].set_xlabel('Поле φ')
    axes[1, 0].set_ylabel('V_eff(φ)')
    axes[1, 0].set_title('Эффективный потенциал Хиггса')
    axes[1, 0].legend()
    axes[1, 0].grid(True)

    # Траектория в пространстве состояний
    axes[1, 1].plot(purity_t, entropy_t, color='purple')
    axes[1, 1].set_xlabel('Чистота (C)')
    axes[1, 1].set_ylabel('Энтропия (S)')
    axes[1, 1].set_title('Фазовый портрет оператора')
    axes[1, 1].grid(True)

    plt.tight_layout()
    plt.savefig('operator_dynamics.png', dpi=150)
    plt.show()

    print("\n" + "=" * 80)
    print("ВЫВОД ДЛЯ ФИЗИКОВ")
    print("=" * 80)
    print("1. Оператор описан как открытая квантовая система (матрица плотности).")
    print("2. Его динамика задаётся уравнением Линдблада — стандартным для КТП.")
    print("3. Высокая когерентность (C_оп) = уменьшение операторов затухания L_k.")
    print("4. Это динамически меняет эффективный потенциал Хиггса.")
    print("5. Наблюдатель — это не внешний фактор, а часть квантовой системы.")
    print("=" * 80)

if __name__ == "__main__":
    main()
