"""
PFO 3 - Sistema distribuido (Cliente-Servidor)
Cliente: envia tareas al servidor por socket y muestra los resultados.

Uso:
    python cliente.py          -> menu interactivo
    python cliente.py demo     -> varios clientes a la vez (prueba de carga)
"""
import json
import socket
import sys
import threading
import time

HOST = "127.0.0.1"
PUERTO = 5000

TIPOS = {
    "1": ("mayusculas", "Texto a pasar a mayusculas"),
    "2": ("invertir", "Texto a invertir"),
    "3": ("contar", "Texto para contar palabras"),
    "4": ("sumar", "Numeros separados por espacio"),
}


def enviar_tarea(conn, entrada, tarea):
    """Manda una tarea (JSON en una linea) y espera la respuesta."""
    conn.sendall((json.dumps(tarea) + "\n").encode("utf-8"))
    linea = entrada.readline()
    if not linea:
        raise ConnectionError("el servidor cerro la conexion")
    return json.loads(linea)


def menu():
    with socket.create_connection((HOST, PUERTO)) as conn, \
            conn.makefile("r", encoding="utf-8") as entrada:
        print(f"Conectado a {HOST}:{PUERTO}")
        numero = 0
        while True:
            print("\n1) Mayusculas  2) Invertir  3) Contar palabras  4) Sumar  0) Salir")
            opcion = input("Opcion: ").strip()
            if opcion == "0":
                break
            if opcion not in TIPOS:
                print("Opcion invalida")
                continue
            tipo, texto = TIPOS[opcion]
            dato = input(f"{texto}: ")
            numero += 1
            respuesta = enviar_tarea(conn, entrada, {"id": numero, "tipo": tipo, "dato": dato})
            print(f"-> [{respuesta['estado']}] {respuesta['resultado']} "
                  f"(resuelto por {respuesta['worker']})")


def cliente_demo(nombre, tareas):
    with socket.create_connection((HOST, PUERTO)) as conn, \
            conn.makefile("r", encoding="utf-8") as entrada:
        for i, (tipo, dato) in enumerate(tareas, start=1):
            tarea = {"id": f"{nombre}-{i}", "tipo": tipo, "dato": dato}
            respuesta = enviar_tarea(conn, entrada, tarea)
            print(f"{tarea['id']}: {tipo}({dato!r}) = {respuesta['resultado']} "
                  f"[{respuesta['worker']}]")


def demo():
    """Lanza 4 clientes al mismo tiempo, cada uno con 2 tareas."""
    tareas = [("mayusculas", "hola mundo"), ("sumar", "10 20 30")]
    inicio = time.time()
    hilos = []
    for n in range(1, 5):
        hilo = threading.Thread(target=cliente_demo, args=(f"cliente{n}", tareas))
        hilo.start()
        hilos.append(hilo)
    for hilo in hilos:
        hilo.join()
    print(f"\n8 tareas resueltas en {time.time() - inicio:.1f} s "
          f"(una sola atras de la otra tardarian 8 s)")


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "demo":
            demo()
        else:
            menu()
    except ConnectionRefusedError:
        print("No se pudo conectar: el servidor esta corriendo?")
    except (ConnectionError, KeyboardInterrupt) as error:
        print(f"\nConexion terminada. {error}")
