#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🌀 ETVP v12.4 FFS — Живая демонстрация
Запусти этот файл, чтобы увидеть, как поле дышит.
Графики показывают сходимость констант к CODATA.
РАСЧЁТЫ И ВЫЧИСЛЕНИЯ ПРОВОДЯТСЯ СТРОГО В ЖИВОЙ ДИНАМИКЕ ПОТОКА!
"""

import sys
import os

# Добавляем путь к папке с ядром ETVP
# (предполагается, что папка ETVE---Language---of---Field лежит рядом)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ETVE---Language---of---Field'))

try:
    from ETVP_12_4_FFS import ETVEComplexCoreV124FFS, demo_ffs_calibration
    print("✅ Ядро ETVP v12.4 FFS загружено.")
except ImportError as e:
    print(f"❌ Ошибка: не удалось загрузить ядро ETVP.")
    print(f"   {e}")
    print("   Убедитесь, что папка 'ETVE---Language---of---Field' находится рядом с этой папкой.")
    print("   Или скопируйте файл ETVP_12_4_FFS.py в текущую папку.")
    sys.exit(1)

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🌀 ETVP v12.4 FFS — Живая динамика поля")
    print("   Запущена демонстрация вывода констант из геометрии E8")
    print("=" * 80 + "\n")
    
    # Запускаем демонстрацию
    demo_ffs_calibration()
    
    print("\n" + "=" * 80)
    print("✅ Демонстрация завершена.")
    print("   Графики показывают, как поле «дышит» вокруг значений CODATA.")
    print("   Средние значения:")
    print("   1/α    ≈ 137.036")
    print("   mₚ/mₑ  ≈ 1836.15")
    print("   G      ≈ 6.6743e-11")
    print("=" * 80)
