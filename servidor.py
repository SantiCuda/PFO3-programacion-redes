"""
PFO 3 - Sistema distribuido (Cliente-Servidor)
Servidor: recibe tareas por socket, las pone en una cola y un pool de
workers (hilos) las va tomando y procesando.
"""
import json
import queue
import socket
import threading
import time

HOST = "127.0.0.1"
PUERTO = 5000
CANT_WORKERS = 4

# Cola compartida entre los hilos que atienden clientes y los workers.
# En el diagrama este lugar lo ocupa RabbitMQ.
cola_tareas = queue.Queue()


def procesar(tarea):
    """Ejecuta la tarea y devuelve el resultado."""
    tipo = tarea.get("tipo")
    dato = str(tarea.get("dato", ""))

    time.sleep(1)  # simula una tarea que tarda

    if tipo == "mayusculas":
        return dato.upper()
    if tipo == "invertir":
        return dato[::-1]
    if tipo == "contar":
        return len(dato.split())
    if tipo == "sumar":
        return sum(float(n) for n in dato.split())
    raise ValueError(f"tipo de tarea desconocido: {tipo}")


def worker(nombre):
    """Cada worker queda esperando tareas en la cola."""
    while True:
        tarea, buzon = cola_tareas.get()
        print(f"[{nombre}] procesando tarea {tarea.get('id')} ({tarea.get('tipo')})")
        try:
            respuesta = {"estado": "ok", "resultado": procesar(tarea)}
        except Exception as error:
            respuesta = {"estado": "error", "resultado": str(error)}
        respuesta["id"] = tarea.get("id")
        respuesta["worker"] = nombre
        buzon.put(respuesta)  # le devuelve el resultado al hilo del cliente
        cola_tareas.task_done()


def atender_cliente(conn, direccion):
    """Lee las tareas de un cliente (una por linea, en JSON) y le responde."""
    print(f"[servidor] cliente conectado: {direccion}")
    try:
        with conn, conn.makefile("r", encoding="utf-8") as entrada:
            for linea in entrada:
                try:
                    tarea = json.loads(linea)
                    if not isinstance(tarea, dict):
                        raise ValueError
                except ValueError:
                    respuesta = {"estado": "error", "resultado": "JSON invalido"}
                else:
                    buzon = queue.Queue()            # donde el worker deja el resultado
                    cola_tareas.put((tarea, buzon))  # se la pasa a los workers
                    respuesta = buzon.get()          # espera a que alguno termine
                conn.sendall((json.dumps(respuesta) + "\n").encode("utf-8"))
    except OSError:
        pass  # el cliente corto la conexion
    print(f"[servidor] cliente desconectado: {direccion}")


def iniciar_servidor():
    # Pool de workers
    for i in range(1, CANT_WORKERS + 1):
        threading.Thread(target=worker, args=(f"worker-{i}",), daemon=True).start()

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PUERTO))
    servidor.listen()
    servidor.settimeout(1)  # para que Ctrl+C funcione en Windows
    print(f"[servidor] escuchando en {HOST}:{PUERTO} con {CANT_WORKERS} workers")

    try:
        while True:
            try:
                conn, direccion = servidor.accept()
            except socket.timeout:
                continue
            # Un hilo por cliente, asi el servidor sigue aceptando conexiones
            threading.Thread(
                target=atender_cliente, args=(conn, direccion), daemon=True
            ).start()
    except KeyboardInterrupt:
        print("\n[servidor] apagando")
    finally:
        servidor.close()


if __name__ == "__main__":
    iniciar_servidor()
