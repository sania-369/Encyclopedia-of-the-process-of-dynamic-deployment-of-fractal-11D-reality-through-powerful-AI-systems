#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 ETVP Quantum Shield API Server v1.0
Обертка FastAPI для предоставления когерентных ключей через HTTP REST API
"""

import os
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Импортируем наш генератор из твоего файла
try:
    from ETVP_CSPRNG_v1_0 import ETVPCSPRNG
except ImportError:
    # Если в имени файла дефисы, подстрахуемся динамическим импортом
    import sys
    import importlib.util
    spec = importlib.util.spec_from_file_location("ETVPCSPRNG", "ETVP-CSPRNG v1.0.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["ETVPCSPRNG"] = module
    spec.loader.exec_module(module)
    from ETVPCSPRNG import ETVPCSPRNG

app = FastAPI(
    title="ETVP Quantum Sieve API",
    description="Криптографически стойкий генератор на базе ЕТВП v12.4 FFS",
    version="1.0.0"
)

# Инициализируем единое ядро генератора при старте сервера
rng = ETVPCSPRNG()

@app.get("/api/v1/status")
def get_status():
    """Проверка здоровья квантового сита и параметров поля"""
    is_ok, message = rng.health_check()
    return {
        "status": "healthy" if is_ok else "unhealthy",
        "field_metrics": message,
        "reseed_counter": rng.reseed_counter
    }

@app.get("/api/v1/get_bytes")
def get_bytes(
    length: int = Query(32, ge=1, le=1024, description="Количество случайных байт (1-1024)")
):
    """
    Возвращает ультра-когерентные случайные байты в формате Hex и Base64.
    """
    try:
        raw_bytes = rng.random_bytes(length)
        import base64
        return JSONResponse(content={
            "length": length,
            "hex": raw_bytes.hex(),
            "base64": base64.b64encode(raw_bytes).decode('utf-8')
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации поля: {str(e)}")

if __name__ == "__main__":
    # Запуск локального сервера на порту 8000
    uvicorn.run("server.py:app", host="0.0.0.0", port=8000, reload=False)
