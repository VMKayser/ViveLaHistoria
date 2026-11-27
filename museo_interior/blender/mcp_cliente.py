"""Cliente ligero para enviar scripts y capturar vistas desde Blender MCP (localhost:9876)."""

import json
import os
import socket
import sys


def call_mcp(req_type: str, params: dict | None = None, host: str = "127.0.0.1", port: int = 9876) -> dict:
    payload = json.dumps({"type": req_type, "params": params or {}}).encode("utf-8")
    with socket.create_connection((host, port), timeout=240) as sock:
        sock.sendall(payload)
        chunks = []
        while True:
            data = sock.recv(65536)
            if not data:
                break
            chunks.append(data)
            try:
                return json.loads(b"".join(chunks).decode("utf-8"))
            except json.JSONDecodeError:
                continue
    raise RuntimeError("La conexion con Blender MCP se cerro sin respuesta JSON completa.")


def run_file_in_blender(script_path: str, extra_args: list[str] | None = None) -> dict:
    abs_path = os.path.abspath(script_path).replace("\\", "/")
    argv_list = [abs_path] + (extra_args or [])
    code = (
        f"import runpy, sys\n"
        f"sys.argv = {argv_list!r}\n"
        f"runpy.run_path({abs_path!r}, run_name='__main__')\n"
    )
    return call_mcp("execute_code", {"code": code})


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "run" and len(sys.argv) >= 3:
        res = run_file_in_blender(sys.argv[2], sys.argv[3:])
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif len(sys.argv) >= 2 and sys.argv[1] == "info":
        res = call_mcp("get_scene_info")
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print("Uso: python mcp_cliente.py [info | run <script.py>]")
