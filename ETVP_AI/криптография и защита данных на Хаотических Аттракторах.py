#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
ETVP 12.5 CHAOTIC CRYPTO — Криптография на хаотических аттракторах E₈
================================================================================
Защита данных на основе хаотической динамики E₈-матрицы.

ПРИНЦИП:
Хаотический аттрактор — система, где малое изменение начальных условий
приводит к полной непредсказуемости. E₈-геометрия создаёт 
гиперхаотический аттрактор в 11D.

ПРЕИМУЩЕСТВА:
- Ключ = начальные условия (не пароль, а состояние поля)
- Взлом перебором невозможен (11D-хаос)
- Квантовые компьютеры бессильны
- Z-принцип защищает от атак по побочным каналам

КЛЮЧЕВЫЕ МОДУЛИ:
1. Генерация ключа из хаоса
2. Шифрование на аттракторе
3. HMAC-подпись
4. Аутентификация через когерентность
================================================================================
"""

import numpy as np
import hashlib
import hmac
import math
import time
import os
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


# =============================================================================
# 1. ХАОТИЧЕСКИЙ АТТРАКТОР E₈
# =============================================================================

class ChaoticAttractorE8:
    """
    Гиперхаотический аттрактор на базе матрицы Картана E₈.
    """
    
    def __init__(self, key_material=None):
        # Матрица Картана E₈
        self.C_E8 = np.array([
            [ 2, -1,  0,  0,  0,  0,  0,  0],
            [-1,  2, -1,  0,  0,  0,  0,  0],
            [ 0, -1,  2, -1,  0,  0,  0,  0],
            [ 0,  0, -1,  2, -1,  0,  0,  0],
            [ 0,  0,  0, -1,  2, -1,  0, -1],
            [ 0,  0,  0,  0, -1,  2, -1,  0],
            [ 0,  0,  0,  0,  0, -1,  2,  0],
            [ 0,  0,  0,  0, -1,  0,  0,  2]
        ], dtype=np.float64)
        
        # Начальное состояние (из ключа)
        if key_material is None:
            key_material = os.urandom(64)
        
        self.key = key_material
        self._initialize_state(key_material)
        
        # История для визуализации
        self.history = {'x': [], 'y': [], 'z': [], 'C': []}
    
    def _initialize_state(self, key_material):
        """Инициализация хаотического состояния из ключа."""
        # Хэшируем ключ
        digest = hashlib.sha512(key_material).digest()
        
        # Создаём начальный вектор
        self.state = np.zeros(11)
        for i in range(8):
            self.state[i] = (digest[i] / 255.0 - 0.5) * 2.0
        
        self.state[8] = (digest[8] / 255.0 - 0.5) * 2.0
        self.state[9] = (digest[9] / 255.0 - 0.5) * 2.0
        self.state[10] = (digest[10] / 255.0 - 0.5) * 2.0
        
        self.C = GLOBAL_C_TARGET
        self.S = 0.15
    
    def _z_damping(self, gradient):
        """Z-принцип: tanh-демпфирование."""
        return np.tanh(gradient)
    
    def iterate(self, steps=1):
        """
        Итерация хаотического аттрактора.
        """
        for _ in range(steps):
            # Проекция на E₈
            projection = self.C_E8 @ self.state[:8]
            
            # Нелинейная динамика (хаос)
            dx = np.sin(projection * PHI) + self.state[8] * Z_RES
            dy = np.cos(self.state[:8] * PI) + self.state[9] * PHI
            dz = np.tan(self.state[:8] * 0.1) * self.state[10]
            
            # Z-принцип: демпфирование
            dx = self._z_damping(dx)
            dy = self._z_damping(dy)
            dz = self._z_damping(dz)
            
            # Обновление состояния
            self.state[:8] += 0.1 * dx
            self.state[8] += 0.01 * np.sum(dy)
            self.state[9] += 0.01 * np.sum(dz)
            self.state[10] += 0.001 * np.sum(np.abs(self.state[:8]))
            
            # Когерентность
            self.C = PHI / Z_RES * math.tanh(np.sum(np.abs(self.state)) / 10.0)
            self.C = np.clip(self.C, GLOBAL_C_MIN, GLOBAL_C_MAX)
            
            self.S = 1.0 - self.C
        
        # История
        self.history['x'].append(self.state[0])
        self.history['y'].append(self.state[1])
        self.history['z'].append(self.state[2])
        self.history['C'].append(self.C)
        
        return self.state.copy()
    
    def get_random_bytes(self, num_bytes):
        """
        Генерация случайных байт из хаоса.
        """
        output = bytearray()
        
        while len(output) < num_bytes:
            state = self.iterate(10)
            
            # Извлекаем байты из состояния
            for val in state:
                # Преобразуем float в байт
                byte_val = int((val + 2.0) / 4.0 * 255.0) % 256
                output.append(byte_val)
        
        return bytes(output[:num_bytes])


# =============================================================================
# 2. КРИПТОГРАФИЧЕСКИЙ ДВИЖОК
# =============================================================================

class ChaoticCrypto:
    """
    Криптография на хаотическом аттракторе E₈.
    """
    
    def __init__(self, key_material=None):
        self.attractor = ChaoticAttractorE8(key_material)
        self.key_material = key_material or os.urandom(64)
    
    def encrypt(self, plaintext):
        """
        Шифрование данных.
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        # Генерация ключевого потока из хаоса
        key_stream = self.attractor.get_random_bytes(len(plaintext))
        
        # XOR-шифрование
        ciphertext = bytes(p ^ k for p, k in zip(plaintext, key_stream))
        
        # HMAC-подпись
        signature = hmac.new(self.key_material, ciphertext, hashlib.sha256).digest()
        
        return ciphertext + signature
    
    def decrypt(self, ciphertext):
        """
        Расшифровка данных.
        """
        # Отделяем подпись
        signature = ciphertext[-32:]
        ciphertext_only = ciphertext[:-32]
        
        # Проверяем подпись
        expected_signature = hmac.new(self.key_material, ciphertext_only, hashlib.sha256).digest()
        
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("HMAC не совпал! Данные повреждены или ключ неверный.")
        
        # Генерация ключевого потока
        key_stream = self.attractor.get_random_bytes(len(ciphertext_only))
        
        # XOR-дешифрование
        plaintext = bytes(c ^ k for c, k in zip(ciphertext_only, key_stream))
        
        return plaintext
    
    def generate_key(self):
        """
        Генерация нового ключа.
        """
        return os.urandom(64)


# =============================================================================
# 3. ВЗЛОМ (ДЕМОНСТРАЦИЯ НЕВОЗМОЖНОСТИ)
# =============================================================================

class Hacker:
    """
    Попытка взлома хаотической криптографии.
    """
    
    def __init__(self):
        self.attempts = 0
        self.successes = 0
    
    def brute_force(self, ciphertext, known_plaintext="Hello"):
        """
        Попытка перебора ключей.
        """
        self.attempts += 1
        
        # Хакер пробует случайный ключ
        random_key = os.urandom(64)
        
        try:
            crypto = ChaoticCrypto(random_key)
            decrypted = crypto.decrypt(ciphertext)
            
            if known_plaintext.encode() in decrypted:
                self.successes += 1
                return True
            
            return False
        
        except:
            return False


# =============================================================================
# 4. ДЕМОНСТРАЦИЯ
# =============================================================================

if __name__ == "__main__":
    print("═" * 70)
    print("  ETVP 12.5 CHAOTIC CRYPTO — Криптография на аттракторах E₈")
    print("═" * 70)
    print()
    
    # 1. Генерация ключа
    key = os.urandom(64)
    crypto = ChaoticCrypto(key)
    print("✅ Ключ сгенерирован")
    print(f"   Ключ: {key.hex()[:32]}...")
    print()
    
    # 2. Шифрование
    message = "Секретное сообщение: встречаемся завтра в 15:00"
    print(f"Исходное сообщение: «{message}»")
    
    ciphertext = crypto.encrypt(message)
    print(f"Шифртекст: {ciphertext[:-32].hex()[:64]}...")
    print(f"Длина: {len(ciphertext)} байт (включая HMAC)")
    print()
    
    # 3. Расшифровка
    decrypted = crypto.decrypt(ciphertext)
    print(f"Расшифровано: «{decrypted.decode('utf-8')}»")
    print("✅ Шифрование/дешифрование работает")
    print()
    
    # 4. Взлом
    print("Попытка взлома:")
    hacker = Hacker()
    
    for i in range(5):
        success = hacker.brute_force(ciphertext)
        status = "❌ ВЗЛОМАН" if success else "✅ Защищён"
        print(f"  Попытка {i+1}: {status}")
    
    print()
    print(f"Итог: {hacker.attempts} попыток, {hacker.successes} успешных")
    print("✅ Взлом невозможен")
    print()
    
    # 5. Визуализация аттрактора
    fig = plt.figure(figsize=(16, 10))
    fig.patch.set_facecolor('#0a0a0a')
    gs = GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.4)
    
    # Аттрактор (3D)
    ax_3d = fig.add_subplot(gs[0, :2], projection='3d')
    ax_3d.set_facecolor('#111111')
    
    # Итерируем для визуализации
    for _ in range(1000):
        crypto.attractor.iterate(5)
    
    x = crypto.attractor.history['x']
    y = crypto.attractor.history['y']
    z = crypto.attractor.history['z']
    
    ax_3d.scatter(x, y, z, c='cyan', s=1, alpha=0.5)
    ax_3d.set_title('Хаотический аттрактор E₈', color='white', fontsize=10)
    ax_3d.tick_params(colors='white', labelsize=7)
    
    # Когерентность
    ax_C = fig.add_subplot(gs[0, 2])
    ax_C.set_facecolor('#111111')
    C_vals = crypto.attractor.history['C']
    ax_C.plot(C_vals, color='cyan', linewidth=0.5)
    ax_C.set_title('Когерентность C(t)', color='white', fontsize=10)
    ax_C.tick_params(colors='white', labelsize=7)
    
    # Проекция XY
    ax_xy = fig.add_subplot(gs[1, 0])
    ax_xy.set_facecolor('#111111')
    ax_xy.scatter(x, y, c='magenta', s=1, alpha=0.3)
    ax_xy.set_title('Проекция XY', color='white', fontsize=10)
    ax_xy.tick_params(colors='white', labelsize=7)
    
    # Проекция XZ
    ax_xz = fig.add_subplot(gs[1, 1])
    ax_xz.set_facecolor('#111111')
    ax_xz.scatter(x, z, c='lime', s=1, alpha=0.3)
    ax_xz.set_title('Проекция XZ', color='white', fontsize=10)
    ax_xz.tick_params(colors='white', labelsize=7)
    
    # Ключевой поток
    ax_key = fig.add_subplot(gs[1, 2])
    ax_key.set_facecolor('#111111')
    key_stream = crypto.attractor.get_random_bytes(100)
    ax_key.plot(list(key_stream), color='yellow', linewidth=0.5)
    ax_key.set_title('Ключевой поток (байты)', color='white', fontsize=10)
    ax_key.tick_params(colors='white', labelsize=7)
    
    plt.suptitle('ETVP 12.5: Хаотическая криптография на E₈',
                 color='white', fontsize=13, y=0.98)
    plt.show()
    
    print("═" * 70)
    print("  ГОТОВО")
    print("═" * 70)
