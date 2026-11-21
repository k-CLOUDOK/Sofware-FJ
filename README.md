# Software FJ

Sistema integral orientado a objetos para gestionar **clientes, servicios y reservas** de la empresa Software FJ, que ofrece reservas de salas, alquiler de equipos y asesorías especializadas.

Proyecto académico de Ingeniería de Sistemas, Universidad Nacional Abierta y a Distancia (UNAD).

> **Sin bases de datos:** toda la información vive en objetos y listas en memoria. El único archivo que escribe el sistema es el registro de eventos y errores (`software_fj.log`).

---

## Características

- **Abstracción:** `EntidadBase` y `Servicio` son clases abstractas (`ABC`).
- **Herencia:** `Cliente`, `Reserva` y los servicios heredan de `EntidadBase`; los tres servicios especializados heredan de `Servicio`.
- **Polimorfismo:** cada servicio sobrescribe `calcular_subtotal()`, `describir()` y `validar_parametros()`.
- **Encapsulación:** atributos privados con propiedades (`@property`) que validan cada dato.
- **Sobrecarga (simulada):** `calcular_costo(horas, impuesto=0.0, descuento=0.0, **parametros)` ofrece varias variantes con parámetros opcionales, ya que Python no tiene sobrecarga clásica.
- **Manejo de excepciones:** excepciones personalizadas, `try/except`, `try/except/else`, `try/except/finally` y encadenamiento con `raise ... from ...`.
- **Estabilidad:** ante cualquier error el sistema lo registra en el log y continúa funcionando.

## Estructura del proyecto

```
software-fj/
├── software_fj.py     # Código fuente completo (clases, excepciones y simulación)
├── software_fj.log    # Registro de eventos y errores generado al ejecutar
└── README.md
```

## Requisitos

- Python 3.8 o superior.
- No requiere instalar librerías externas (solo módulos de la biblioteca estándar).

## Cómo ejecutarlo

1. Clona el repositorio:

   ```bash
   git clone <URL-DEL-REPOSITORIO>
   cd software-fj
   ```

2. Ejecuta el programa:

   ```bash
   python software_fj.py
   ```

   En algunos sistemas el comando es `python3 software_fj.py`.

3. Revisa el archivo `software_fj.log`, que se crea (o se sobrescribe) en cada ejecución.

## Arquitectura

```
EntidadBase (ABC)
├── Cliente
├── Servicio (ABC)
│   ├── ReservaSala
│   ├── AlquilerEquipo
│   └── AsesoriaEspecializada
└── Reserva

GestorSoftwareFJ  → administra las listas de clientes, servicios y reservas
```

| Clase | Responsabilidad |
|---|---|
| `EntidadBase` | Clase abstracta general: ID único y `describir()` obligatorio. |
| `Cliente` | Datos personales encapsulados con validación de nombre, documento, correo y teléfono. |
| `Servicio` | Clase abstracta con disponibilidad, validación de horas y cálculo de costo con impuestos y descuentos. |
| `ReservaSala` | Sala con capacidad; valida el número de asistentes. |
| `AlquilerEquipo` | Equipo con stock; el costo depende de la cantidad de unidades. |
| `AsesoriaEspecializada` | Asesoría por nivel (`junior`, `senior`, `experto`) con multiplicador de tarifa. |
| `Reserva` | Integra cliente, servicio, duración y estado; implementa `confirmar()`, `cancelar()` y `procesar()`. |
| `GestorSoftwareFJ` | Ejecuta las operaciones de forma protegida, registra los errores y mantiene el sistema activo. |

### Estados de una reserva

`PENDIENTE` → `CONFIRMADA` → `PROCESADA`
También puede pasar a `CANCELADA` (antes de ser procesada) o `FALLIDA` (si el cálculo del costo es inconsistente).

## Excepciones personalizadas

Todas heredan de `SoftwareFJError`:

| Excepción | Cuándo se lanza |
|---|---|
| `ParametroFaltanteError` | Falta un parámetro obligatorio. |
| `ClienteInvalidoError` | Datos de cliente inválidos (correo, documento, etc.). |
| `ServicioInvalidoError` | Datos o parámetros de servicio inválidos. |
| `ServicioNoDisponibleError` | Se intenta confirmar una reserva de un servicio no disponible. |
| `ReservaInvalidaError` | La reserva no puede crearse o procesarse. |
| `OperacionNoPermitidaError` | La operación no es válida para el estado actual. |
| `CalculoInconsistenteError` | El costo calculado es incoherente (por ejemplo, total igual a cero). |

## Ejemplos de cálculo de costos

```python
sala.calcular_costo(2)                 # Solo subtotal
sala.calcular_costo(2, 0.19)           # Con IVA del 19 %
sala.calcular_costo(2, 0.19, 0.10)     # Con IVA y descuento del 10 %
sala.calcular_costo_con_iva(2)         # Atajo con IVA estándar
equipo.calcular_costo(2, cantidad=3)   # Equipo: 3 unidades durante 2 horas
```

## Simulación incluida

Al ejecutar el programa se simulan más de 20 operaciones, entre válidas e inválidas:

- Clientes: registro correcto, correo mal formado y documento faltante.
- Servicios: creación correcta, tarifa negativa y nivel de asesoría inválido.
- Reservas: exitosas, con horas inválidas, con cantidad mayor al stock, con servicio no disponible, con descuento del 100 % (cálculo inconsistente), sin cliente, cancelar una reserva ya procesada y procesar una reserva sin confirmar.

Ejemplo de líneas del log:

```
ERROR | Registrar cliente -> ClienteInvalidoError: Correo electrónico inválido: 'luis-correo.com'.
ERROR | Reserva #7 (procesar) -> ReservaInvalidaError: No se pudo procesar la reserva #7. | causa: CalculoInconsistenteError: Costo total incoherente: 0.0.
```

## Integrantes

| Nombre | Aporte |
|---|---|
| Keller González Ortiz | _Completo_ |

## Información académica

- **Universidad:** Universidad Nacional Abierta y a Distancia – UNAD
- **Programa:** Ingeniería de Sistemas
- **Curso:** Programacion 213023
- **Tutor:** Juan Pablo Zambrano
- **Fecha:** Noviembre de 2026
