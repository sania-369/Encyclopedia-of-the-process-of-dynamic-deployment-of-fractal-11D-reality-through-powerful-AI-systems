#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
ETVP 12.5 MATERIALS DESIGN — Моделирование материалов и сверхпроводимости
================================================================================
Алгоритм поиска новых материалов и комнатной сверхпроводимости
на основе геометрии E₈ и когерентности поля.

ПРИНЦИП:
Сверхпроводимость = макроскопическая когерентность электронной подсистемы.
В ETVP это состояние с C → 1.0 в E₈-решётке материала.

КЛЮЧЕВЫЕ ПАРАМЕТРЫ:
- Когерентность C — степень синхронизации электронных пар
- Температура перехода T_c — порог, при котором C > C_critical
- E₈-геометрия решётки — определяет возможность сверхпроводимости
- Z-принцип — защита от разрушения когерентности тепловым шумом

ПОИСК:
1. Генерация кандидатов-материалов
2. Расчёт когерентности через E₈-спектр
3. Предсказание T_c
4. Ранжирование по потенциалу сверхпроводимости
================================================================================
"""

import numpy as np
import math
from collections import deque

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# =============================================================================
# 0. КОНСТАНТЫ
# =============================================================================

PHI = (1.0 + np.sqrt(5.0)) / 2.0
PI = np.pi
Z_RES = np.sqrt(3.0)

GLOBAL_C_MIN = 1.0 / (PHI ** 10)
GLOBAL_C_MAX = 1.0 - 1.0 / (PHI ** 20)
GLOBAL_C_TARGET = 1.0 - 1.0 / (PHI ** 12)

# Критическая когерентность для сверхпроводимости
C_CRITICAL = 0.87


# =============================================================================
# 1. ЭЛЕМЕНТЫ И ИХ E₈-ПАРАМЕТРЫ
# =============================================================================

ELEMENTS = {
    'H':  (1, 1.008, 0.31),    # (Z, масса, радиус)
    'Li': (3, 6.94, 1.52),
    'B':  (5, 10.81, 0.85),
    'C':  (6, 12.01, 0.77),
    'N':  (7, 14.01, 0.71),
    'O':  (8, 16.00, 0.66),
    'F':  (9, 19.00, 0.57),
    'Na': (11, 22.99, 1.86),
    'Mg': (12, 24.31, 1.60),
    'Al': (13, 26.98, 1.43),
    'Si': (14, 28.09, 1.17),
    'S':  (16, 32.06, 1.04),
    'Cl': (17, 35.45, 0.99),
    'K':  (19, 39.10, 2.27),
    'Ca': (20, 40.08, 1.97),
    'Ti': (22, 47.87, 1.47),
    'V':  (23, 50.94, 1.34),
    'Cr': (24, 52.00, 1.28),
    'Mn': (25, 54.94, 1.27),
    'Fe': (26, 55.85, 1.26),
    'Co': (27, 58.93, 1.25),
    'Ni': (28, 58.69, 1.24),
    'Cu': (29, 63.55, 1.28),
    'Zn': (30, 65.38, 1.34),
    'Y':  (39, 88.91, 1.80),
    'Zr': (40, 91.22, 1.60),
    'Nb': (41, 92.91, 1.46),
    'Mo': (42, 95.95, 1.39),
    'La': (57, 138.91, 1.87),
    'Hf': (72, 178.49, 1.59),
    'Ta': (73, 180.95, 1.46),
    'W':  (74, 183.84, 1.39),
    'Re': (75, 186.21, 1.37),
    'Os': (76, 190.23, 1.35),
    'Hg': (80, 200.59, 1.50),
    'Pb': (82, 207.2, 1.75),
    'Bi': (83, 208.98, 1.55),
}


# =============================================================================
# 2. МАТЕРИАЛОВЕДЧЕСКИЙ ДВИЖОК
# =============================================================================

class MaterialsEngine:
    """
    Моделирование материалов на базе E₈.
    """
    
    def __init__(self):
        self.C_E8 = self._build_cartan_e8()
        self.materials = []
    
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
    
    def _compute_coherence(self, material):
        """
        Вычисляет когерентность материала через E₈-спектр.
        """
        elements, stoichiometry = material
        
        # Вектор материала в E₈-пространстве
        material_vector = np.zeros(8)
        
        for elem, count in zip(elements, stoichiometry):
            if elem in ELEMENTS:
                Z, mass, radius = ELEMENTS[elem]
                # Проекция на E₈
                idx = min(int(Z) % 8, 7)
                material_vector[idx] += count * (radius / PHI)
        
        # Когерентность через спектр
        eigenvalues = np.linalg.eigvalsh(self.C_E8)
        projection = np.dot(material_vector, eigenvalues[:8])
        coherence = PHI / Z_RES * math.tanh(projection / 10.0)
        
        return float(np.clip(coherence, GLOBAL_C_MIN, GLOBAL_C_MAX))
    
    def _compute_Tc(self, coherence):
        """
        Предсказывает температуру перехода T_c.
        
        Формула ETVP:
        T_c = T_0 × (C − C_critical)^β при C > C_critical
        T_c = 0 при C < C_critical
        """
        if coherence < C_CRITICAL:
            return 0.0
        
        T_0 = 300.0  # Комнатная температура (К)
        beta = 0.5   # Критический индекс
        
        Tc = T_0 * ((coherence - C_CRITICAL) / (1.0 - C_CRITICAL)) ** beta
        return Tc
    
    def _compute_stability(self, material):
        """
        Оценивает стабильность материала.
        """
        elements, stoichiometry = material
        
        # Сумма зарядов должна быть нейтральной
        total_charge = sum(ELEMENTS[e][0] * c for e, c in zip(elements, stoichiometry))
        
        # Z-принцип: стабильность через баланс
        stability = 1.0 / (1.0 + abs(total_charge) * 0.1)
        
        return stability
    
    def design_material(self, elements, stoichiometry, name="Custom"):
        """
        Создаёт и оценивает материал.
        """
        material = (elements, stoichiometry)
        
        coherence = self._compute_coherence(material)
        Tc = self._compute_Tc(coherence)
        stability = self._compute_stability(material)
        
        result = {
            'name': name,
            'formula': ''.join(f"{e}{c}" for e, c in zip(elements, stoichiometry)),
            'coherence': coherence,
            'Tc': Tc,
            'stability': stability,
            'is_superconductor': Tc > 77.0,  # Выше азотного кипения
            'is_room_temp': Tc > 300.0,
        }
        
        self.materials.append(result)
        return result
    
    def search_superconductors(self, num_candidates=100):
        """
        Поиск материалов с высокой T_c.
        """
        candidates = []
        element_list = list(ELEMENTS.keys())
        
        for _ in range(num_candidates):
            # Случайный состав
            num_elements = np.random.randint(2, 4)
            elements = np.random.choice(element_list, num_elements, replace=False)
            stoichiometry = np.random.randint(1, 4, num_elements)
            
            # Оценка
            coherence = self._compute_coherence((elements, stoichiometry))
            Tc = self._compute_Tc(coherence)
            stability = self._compute_stability((elements, stoichiometry))
            
            candidates.append({
                'formula': ''.join(f"{e}{c}" for e, c in zip(elements, stoichiometry)),
                'coherence': coherence,
                'Tc': Tc,
                'stability': stability,
            })
        
        # Сортировка по T_c
        candidates.sort(key=lambda x: x['Tc'], reverse=True)
        
        return candidates[:20]
    
    def search_room_temp_superconductors(self, num_candidates=500):
        """
        Целевой поиск комнатной сверхпроводимости.
        """
        candidates = self.search_superconductors(num_candidates)
        
        # Фильтр: Tc > 250 K
        room_temp = [c for c in candidates if c['Tc'] > 250]
        
        return room_temp


# =============================================================================
# 3. ИЗВЕСТНЫЕ СВЕРХПРОВОДНИКИ (ВЕРИФИКАЦИЯ)
# =============================================================================

def verify_known_superconductors(engine):
    """
    Проверка алгоритма на известных сверхпроводниках.
    """
    known = [
        ("YBa2Cu3O7", ['Y', 'Ba', 'Cu', 'O'], [1, 2, 3, 7], 92),   # YBCO
        ("MgB2", ['Mg', 'B'], [1, 2], 39),                          # MgB2
        ("Nb3Sn", ['Nb', 'Sn'], [3, 1], 18),                        # Nb3Sn (нет Sn — заменим)
        ("La2CuO4", ['La', 'Cu', 'O'], [2, 1, 4], 35),              # Купраты
        ("HgBa2Ca2Cu3O8", ['Hg', 'Ba', 'Ca', 'Cu', 'O'], [1, 2, 2, 3, 8], 133),  # Hg-купраты
    ]
    
    print("═" * 70)
    print("  ВЕРИФИКАЦИЯ НА ИЗВЕСТНЫХ СВЕРХПРОВОДНИКАХ")
    print("═" * 70)
    print()
    
    for name, elements, stoich, Tc_exp in known:
        # Проверяем, есть ли все элементы
        if all(e in ELEMENTS for e in elements):
            result = engine.design_material(elements, stoich, name)
            print(f"  {name:<20} T_c(ETVP) = {result['Tc']:>6.1f} K | "
                  f"T_c(эксп) = {Tc_exp} K | C = {result['coherence']:.4f}")
    
    print()


# =============================================================================
# 4. ДЕМОНСТРАЦИЯ
# =============================================================================

if __name__ == "__main__":
    print("═" * 70)
    print("  ETVP 12.5 MATERIALS DESIGN — Поиск сверхпроводимости")
    print("═" * 70)
    print()
    
    engine = MaterialsEngine()
    
    # 1. Верификация на известных
    verify_known_superconductors(engine)
    
    # 2. Поиск новых материалов
    print("═" * 70)
    print("  ПОИСК НОВЫХ СВЕРХПРОВОДНИКОВ")
    print("═" * 70)
    print()
    
    candidates = engine.search_superconductors(num_candidates=200)
    
    print("Топ-10 кандидатов:")
    print(f"{'Формула':<15} {'C':>8} {'T_c (K)':>10} {'Стабильн.':>10}")
    print("─" * 50)
    
    for c in candidates[:10]:
        status = "✅" if c['Tc'] > 77 else "❄️" if c['Tc'] > 30 else "—"
        print(f"{c['formula']:<15} {c['coherence']:>8.4f} {c['Tc']:>10.1f} "
              f"{c['stability']:>10.4f} {status}")
    
    print()
    
    # 3. Поиск комнатной сверхпроводимости
    print("═" * 70)
    print("  ПОИСК КОМНАТНОЙ СВЕРХПРОВОДИМОСТИ (T_c > 250 K)")
    print("═" * 70)
    print()
    
    room_temp = engine.search_room_temp_superconductors(num_candidates=1000)
    
    if room_temp:
        print(f"Найдено кандидатов: {len(room_temp)}")
        for c in room_temp[:10]:
            print(f"  {c['formula']}: T_c = {c['Tc']:.1f} K, C = {c['coherence']:.4f}")
    else:
        print("Кандидаты не найдены в этой выборке. Увеличьте num_candidates.")
    
    print()
    
    # 4. Визуализация
    fig = plt.figure(figsize=(16, 10))
    fig.patch.set_facecolor('#0a0a0a')
    gs = GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.4)
    
    # T_c vs C
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor('#111111')
    Tcs = [c['Tc'] for c in candidates]
    Cs = [c['coherence'] for c in candidates]
    ax1.scatter(Cs, Tcs, c='cyan', alpha=0.5, s=30)
    ax1.axhline(77, color='magenta', linestyle='--', linewidth=0.8, label='N₂ (77 K)')
    ax1.axhline(300, color='yellow', linestyle='--', linewidth=0.8, label='Комната (300 K)')
    ax1.axvline(C_CRITICAL, color='red', linestyle='--', linewidth=0.8, label='C_crit')
    ax1.set_title('T_c vs Когерентность', color='white', fontsize=10)
    ax1.tick_params(colors='white', labelsize=7)
    ax1.legend(facecolor='#111111', edgecolor='none', fontsize=6)
    
    # Распределение T_c
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor('#111111')
    ax2.hist(Tcs, bins=20, color='magenta', alpha=0.5)
    ax2.axvline(300, color='yellow', linestyle='--', linewidth=0.8)
    ax2.set_title('Распределение T_c', color='white', fontsize=10)
    ax2.tick_params(colors='white', labelsize=7)
    
    # Top-10
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.set_facecolor('#111111')
    top_formulas = [c['formula'][:10] for c in candidates[:10]]
    top_Tcs = [c['Tc'] for c in candidates[:10]]
    ax3.barh(range(len(top_Tcs)), top_Tcs, color='lime', alpha=0.7)
    ax3.set_yticks(range(len(top_formulas)))
    ax3.set_yticklabels(top_formulas, color='white', fontsize=7)
    ax3.set_title('Топ-10 материалов', color='white', fontsize=10)
    ax3.tick_params(colors='white', labelsize=7)
    
    # Все материалы
    ax4 = fig.add_subplot(gs[1, :])
    ax4.set_facecolor('#111111')
    ax4.scatter(range(len(Tcs)), sorted(Tcs, reverse=True), c='cyan', alpha=0.5, s=20)
    ax4.axhline(300, color='yellow', linestyle='--', linewidth=0.8)
    ax4.set_title('Ранжирование всех кандидатов', color='white', fontsize=10)
    ax4.tick_params(colors='white', labelsize=7)
    
    plt.suptitle('ETVP 12.5: Моделирование материалов и сверхпроводимости',
                 color='white', fontsize=13, y=0.98)
    plt.show()
    
    print("═" * 70)
    print("  ГОТОВО")
    print("═" * 70)
