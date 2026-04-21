"""
Archivo: arithmetic.py
Descripción: Programa que realiza operaciones aritméticas básicas (suma, resta, multiplicación y división).
Uso:
    python arithmetic.py
El programa pedirá al usuario dos números y la operación a realizar.
"""

import sys

# --------------------------------------------
# Funciones de operaciones aritméticas básicas
# --------------------------------------------

def suma(a: float, b: float) -> float:
    """Devuelve la suma de a y b."""
    return a + b

def resta(a: float, b: float) -> float:
    """Devuelve la diferencia entre a y b."""
    return a - b

def multiplicacion(a: float, b: float) -> float:
    """Devuelve el producto de a y b."""
    return a * b

def division(a: float, b: float) -> float:
    """Devuelve la división de a entre b.

    Si b es cero se lanza ZeroDivisionError con un mensaje claro.
    """
    if b == 0:
        raise ZeroDivisionError("No se puede dividir por cero.")
    return a / b

# --------------------------------------------
# Función principal que maneja la interacción con el usuario
# --------------------------------------------

def main() -> None:
    """Punto de entrada del programa.

    1. Solicita al usuario dos números (convertidos a float).
    2. Muestra un menú con las operaciones disponibles.
    3. Ejecuta la operación seleccionada y muestra el resultado.
    4. Maneja errores comunes como valores no numéricos o división por cero.
    """
    print("Operaciones aritméticas básicas")

    # Entrada de números con manejo de excepción para valores inválidos
    try:
        num1 = float(input("Ingrese el primer número: "))
        num2 = float(input("Ingrese el segundo número: "))
    except ValueError:
        print("Entrada inválida. Por favor ingrese números.")
        sys.exit(1)

    # Menú de opciones
    print("\nSeleccione la operación:\n")
    print("  1) Suma")
    print("  2) Resta")
    print("  3) Multiplicación")
    print("  4) División")
    opcion = input("Opción (1-4): ")

    # Selección y ejecución de la operación elegida
    try:
        if opcion == "1":
            resultado = suma(num1, num2)
            op_str = '+'
        elif opcion == "2":
            resultado = resta(num1, num2)
            op_str = '-'
        elif opcion == "3":
            resultado = multiplicacion(num1, num2)
            op_str = '*'
        elif opcion == "4":
            resultado = division(num1, num2)
            op_str = '/'
        else:
            print("Opción no válida.")
            sys.exit(1)
    except ZeroDivisionError as e:
        # Manejo de la excepción específica de división por cero
        print(e)
        sys.exit(1)

    # Mostrar el resultado al usuario
    print(f"\nResultado: {num1} {op_str} {num2} = {resultado}")

# Se ejecuta solo si se llama directamente desde la línea de comandos
if __name__ == "__main__":
    main()
