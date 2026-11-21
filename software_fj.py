# -*- coding: utf-8 -*-
"""
SOFTWARE FJ - Sistema integral de gestión de clientes, servicios y reservas
===========================================================================
Programación orientada a objetos (sin bases de datos).

Principios aplicados:
  * Abstracción     -> EntidadBase y Servicio son clases abstractas (ABC).
  * Herencia        -> Cliente, Reserva y los servicios heredan de EntidadBase / Servicio.
  * Polimorfismo    -> cada servicio sobrescribe calcular_subtotal(), describir()
                       y validar_parametros().
  * Encapsulación   -> atributos privados (__x) con propiedades que validan.
  * Excepciones     -> jerarquía propia, try/except/else/finally y encadenamiento
                       (raise ... from ...).
  * Persistencia    -> SOLO un archivo de logs (software_fj.log); los datos viven
                       en objetos y listas en memoria.

Nota sobre la sobrecarga: Python no tiene sobrecarga "clásica" como Java, así que se
simula con parámetros opcionales, valores por defecto y **kwargs (calcular_costo).
"""

import itertools            # Generador de identificadores únicos
import logging              # Registro de eventos y errores en archivo
import math                 # Para detectar valores no finitos (nan / inf)
import re                   # Expresiones regulares para validar datos
from abc import ABC, abstractmethod   # Clases abstractas
from enum import Enum                 # Estados de la reserva

# ---------------------------------------------------------------------------
# 1. CONFIGURACIÓN DEL LOG (único archivo que usa el sistema)
# ---------------------------------------------------------------------------
ARCHIVO_LOG = "software_fj.log"

logger = logging.getLogger("SoftwareFJ")          # Logger propio del sistema
logger.setLevel(logging.DEBUG)                    # Registra todos los niveles
if not logger.handlers:                           # Evita duplicar handlers al reimportar
    _handler = logging.FileHandler(ARCHIVO_LOG, mode="w", encoding="utf-8")
    _handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")
    )
    logger.addHandler(_handler)


def registrar_error(contexto, error):
    """Escribe un error en el log incluyendo la causa original (cadena de excepciones)."""
    mensaje = f"{contexto} -> {type(error).__name__}: {error}"
    causa = error.__cause__          # Excepción encadenada con 'raise ... from ...'
    while causa is not None:         # Recorre toda la cadena de causas
        mensaje += f" | causa: {type(causa).__name__}: {causa}"
        causa = causa.__cause__
    logger.error(mensaje)


# ---------------------------------------------------------------------------
# 2. EXCEPCIONES PERSONALIZADAS
# ---------------------------------------------------------------------------
class SoftwareFJError(Exception):
    """Excepción base de todo el sistema."""


class ParametroFaltanteError(SoftwareFJError):
    """Se omitió un parámetro obligatorio."""


class ClienteInvalidoError(SoftwareFJError):
    """Datos de cliente inválidos."""


class ServicioInvalidoError(SoftwareFJError):
    """Datos o parámetros de servicio inválidos."""


class ServicioNoDisponibleError(SoftwareFJError):
    """El servicio no está disponible para ser reservado."""


class ReservaInvalidaError(SoftwareFJError):
    """La reserva no pudo crearse o procesarse."""


class OperacionNoPermitidaError(SoftwareFJError):
    """La operación no es válida para el estado actual del objeto."""


class CalculoInconsistenteError(SoftwareFJError):
    """El cálculo de costos produjo un resultado incoherente."""


# ---------------------------------------------------------------------------
# 3. CLASE ABSTRACTA GENERAL
# ---------------------------------------------------------------------------
class EntidadBase(ABC):
    """Representa cualquier entidad del sistema (cliente, servicio, reserva)."""

    _contador = itertools.count(1)   # Contador compartido para generar IDs únicos

    def __init__(self):
        self.__id = next(EntidadBase._contador)   # ID privado, solo lectura

    @property
    def id(self):
        """Identificador único (solo lectura)."""
        return self.__id

    @abstractmethod
    def describir(self):
        """Cada entidad debe poder describirse como texto."""

    def __str__(self):
        return self.describir()


# ---------------------------------------------------------------------------
# 4. CLIENTE (encapsulación + validaciones robustas)
# ---------------------------------------------------------------------------
class Cliente(EntidadBase):
    """Cliente de Software FJ. Todos sus datos son privados y validados."""

    _REGEX_CORREO = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")

    def __init__(self, nombre=None, documento=None, correo=None, telefono=None):
        # Se validan los datos ANTES de llamar a super() para no gastar IDs en clientes inválidos
        for campo, valor in (("nombre", nombre), ("documento", documento),
                             ("correo", correo), ("telefono", telefono)):
            if valor is None:
                raise ParametroFaltanteError(f"Falta el parámetro obligatorio '{campo}'.")
        self.nombre = nombre          # Pasa por el setter (valida)
        self.documento = documento
        self.correo = correo
        self.telefono = telefono
        super().__init__()

    # --- Propiedades con validación (encapsulación) ---
    @property
    def nombre(self):
        return self.__nombre

    @nombre.setter
    def nombre(self, valor):
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise ClienteInvalidoError("El nombre debe ser texto de al menos 3 caracteres.")
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]+", valor.strip()):
            raise ClienteInvalidoError("El nombre solo puede contener letras y espacios.")
        self.__nombre = valor.strip().title()

    @property
    def documento(self):
        return self.__documento

    @documento.setter
    def documento(self, valor):
        try:
            texto = str(valor).strip()
            if not texto.isdigit():
                raise ValueError(f"'{valor}' contiene caracteres no numéricos")
            if not 5 <= len(texto) <= 12:
                raise ValueError("longitud fuera del rango 5-12 dígitos")
        except ValueError as error:
            # Encadenamiento: la causa original queda ligada a la excepción personalizada
            raise ClienteInvalidoError("Documento inválido.") from error
        self.__documento = texto

    @property
    def correo(self):
        return self.__correo

    @correo.setter
    def correo(self, valor):
        if not isinstance(valor, str) or not self._REGEX_CORREO.match(valor.strip()):
            raise ClienteInvalidoError(f"Correo electrónico inválido: {valor!r}.")
        self.__correo = valor.strip().lower()

    @property
    def telefono(self):
        return self.__telefono

    @telefono.setter
    def telefono(self, valor):
        texto = str(valor).strip()
        if not (texto.isdigit() and 7 <= len(texto) <= 10):
            raise ClienteInvalidoError(f"Teléfono inválido: {valor!r} (7 a 10 dígitos).")
        self.__telefono = texto

    def describir(self):
        return f"Cliente #{self.id}: {self.nombre} | Doc: {self.documento} | {self.correo}"


# ---------------------------------------------------------------------------
# 5. SERVICIO ABSTRACTO + 3 SERVICIOS ESPECIALIZADOS
# ---------------------------------------------------------------------------
class Servicio(EntidadBase, ABC):
    """Clase abstracta de la que heredan todos los servicios de Software FJ."""

    MAX_HORAS = 24   # Límite máximo de duración de una reserva

    def __init__(self, nombre=None, tarifa_hora=None, disponible=True):
        if nombre is None or tarifa_hora is None:
            raise ParametroFaltanteError("Un servicio requiere 'nombre' y 'tarifa_hora'.")
        if not isinstance(nombre, str) or not nombre.strip():
            raise ServicioInvalidoError("El nombre del servicio no puede estar vacío.")
        if isinstance(tarifa_hora, bool) or not isinstance(tarifa_hora, (int, float)) \
                or tarifa_hora <= 0:
            raise ServicioInvalidoError(f"Tarifa por hora inválida: {tarifa_hora!r}.")
        self._nombre = nombre.strip()
        self._tarifa_hora = float(tarifa_hora)
        self._disponible = bool(disponible)
        super().__init__()

    # --- Solo lectura / control de disponibilidad ---
    @property
    def nombre(self):
        return self._nombre

    @property
    def tarifa_hora(self):
        return self._tarifa_hora

    @property
    def disponible(self):
        return self._disponible

    @disponible.setter
    def disponible(self, valor):
        self._disponible = bool(valor)

    # --- Métodos abstractos: cada servicio los sobrescribe (polimorfismo) ---
    @abstractmethod
    def calcular_subtotal(self, horas, **parametros):
        """Costo base del servicio sin impuestos ni descuentos."""

    @abstractmethod
    def describir(self):
        """Descripción textual del servicio."""

    def validar_parametros(self, horas, **parametros):
        """Validación común (duración). Las subclases la extienden con super()."""
        if isinstance(horas, bool) or not isinstance(horas, (int, float)):
            raise ServicioInvalidoError(f"Las horas deben ser numéricas, se recibió {horas!r}.")
        if not 0 < horas <= self.MAX_HORAS:
            raise ServicioInvalidoError(f"Las horas deben estar entre 0 y {self.MAX_HORAS}.")

    # --- MÉTODO SOBRECARGADO (simulado con parámetros opcionales) ---
    def calcular_costo(self, horas, impuesto=0.0, descuento=0.0, **parametros):
        """
        Variantes de uso:
          calcular_costo(2)                       -> solo subtotal
          calcular_costo(2, 0.19)                 -> subtotal + IVA
          calcular_costo(2, 0.19, 0.10)           -> subtotal - descuento + IVA
          calcular_costo(2, descuento=0.10)       -> solo descuento
        """
        if not (isinstance(impuesto, (int, float)) and 0 <= impuesto <= 1):
            raise CalculoInconsistenteError(f"Impuesto fuera de rango (0-1): {impuesto!r}.")
        if not (isinstance(descuento, (int, float)) and 0 <= descuento <= 1):
            raise CalculoInconsistenteError(f"Descuento fuera de rango (0-1): {descuento!r}.")
        subtotal = self.calcular_subtotal(horas, **parametros)   # Polimorfismo
        total = subtotal * (1 - descuento) * (1 + impuesto)
        if not math.isfinite(total) or total <= 0:
            raise CalculoInconsistenteError(f"Costo total incoherente: {total!r}.")
        return round(total, 2)

    def calcular_costo_con_iva(self, horas, **parametros):
        """Variante de conveniencia: aplica el IVA estándar del 19 %."""
        return self.calcular_costo(horas, impuesto=0.19, **parametros)


class ReservaSala(Servicio):
    """Servicio: reserva de salas de reuniones."""

    def __init__(self, nombre=None, tarifa_hora=None, capacidad=None, disponible=True):
        if not isinstance(capacidad, int) or isinstance(capacidad, bool) or capacidad <= 0:
            raise ServicioInvalidoError(f"Capacidad de sala inválida: {capacidad!r}.")
        self._capacidad = capacidad
        super().__init__(nombre, tarifa_hora, disponible)

    def validar_parametros(self, horas, **parametros):
        super().validar_parametros(horas)                 # Validación heredada
        asistentes = parametros.get("asistentes", 1)
        if not isinstance(asistentes, int) or not 1 <= asistentes <= self._capacidad:
            raise ServicioInvalidoError(
                f"Asistentes ({asistentes!r}) exceden la capacidad de la sala ({self._capacidad}).")

    def calcular_subtotal(self, horas, **parametros):
        return self.tarifa_hora * horas                   # Tarifa plana por hora

    def describir(self):
        return (f"[Sala] {self.nombre} | capacidad {self._capacidad} | "
                f"${self.tarifa_hora:,.0f}/h")


class AlquilerEquipo(Servicio):
    """Servicio: alquiler de equipos (portátiles, proyectores, etc.)."""

    def __init__(self, nombre=None, tarifa_hora=None, stock=None, disponible=True):
        if not isinstance(stock, int) or isinstance(stock, bool) or stock < 0:
            raise ServicioInvalidoError(f"Stock inválido: {stock!r}.")
        self._stock = stock
        super().__init__(nombre, tarifa_hora, disponible)

    def validar_parametros(self, horas, **parametros):
        super().validar_parametros(horas)
        cantidad = parametros.get("cantidad", 1)
        if not isinstance(cantidad, int) or not 1 <= cantidad <= self._stock:
            raise ServicioInvalidoError(
                f"Cantidad ({cantidad!r}) no válida; stock disponible: {self._stock}.")

    def calcular_subtotal(self, horas, **parametros):
        return self.tarifa_hora * horas * parametros.get("cantidad", 1)   # Por unidad

    def describir(self):
        return f"[Equipo] {self.nombre} | stock {self._stock} | ${self.tarifa_hora:,.0f}/h c/u"


class AsesoriaEspecializada(Servicio):
    """Servicio: asesorías con consultores de distinto nivel."""

    _NIVELES = {"junior": 1.0, "senior": 1.5, "experto": 2.0}   # Multiplicador por nivel

    def __init__(self, nombre=None, tarifa_hora=None, nivel=None, disponible=True):
        if nivel not in self._NIVELES:
            raise ServicioInvalidoError(
                f"Nivel {nivel!r} no válido. Opciones: {', '.join(self._NIVELES)}.")
        self._nivel = nivel
        super().__init__(nombre, tarifa_hora, disponible)

    def validar_parametros(self, horas, **parametros):
        super().validar_parametros(horas)
        if horas < 1:
            raise ServicioInvalidoError("Una asesoría dura mínimo 1 hora.")

    def calcular_subtotal(self, horas, **parametros):
        return self.tarifa_hora * horas * self._NIVELES[self._nivel]

    def describir(self):
        return f"[Asesoría] {self.nombre} | nivel {self._nivel} | ${self.tarifa_hora:,.0f}/h base"


# ---------------------------------------------------------------------------
# 6. RESERVA
# ---------------------------------------------------------------------------
class EstadoReserva(Enum):
    PENDIENTE = "Pendiente"
    CONFIRMADA = "Confirmada"
    CANCELADA = "Cancelada"
    PROCESADA = "Procesada"
    FALLIDA = "Fallida"


class Reserva(EntidadBase):
    """Integra cliente, servicio, duración y estado."""

    def __init__(self, cliente=None, servicio=None, horas=None, **parametros):
        if cliente is None or servicio is None or horas is None:
            raise ParametroFaltanteError("Reserva requiere cliente, servicio y horas.")
        if not isinstance(cliente, Cliente) or not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("Cliente o servicio no son objetos válidos.")
        try:
            servicio.validar_parametros(horas, **parametros)
        except ServicioInvalidoError as error:
            # Encadenamiento: se traduce el error de servicio a error de reserva
            raise ReservaInvalidaError("Parámetros de reserva inválidos.") from error
        self.cliente = cliente
        self.servicio = servicio
        self.horas = horas
        self.parametros = parametros
        self.__estado = EstadoReserva.PENDIENTE
        self.costo_final = None
        super().__init__()

    @property
    def estado(self):
        return self.__estado

    def confirmar(self):
        """PENDIENTE -> CONFIRMADA (requiere servicio disponible)."""
        if self.__estado is not EstadoReserva.PENDIENTE:
            raise OperacionNoPermitidaError(
                f"No se puede confirmar una reserva en estado {self.__estado.value}.")
        if not self.servicio.disponible:
            raise ServicioNoDisponibleError(f"'{self.servicio.nombre}' no está disponible.")
        self.__estado = EstadoReserva.CONFIRMADA
        logger.info(f"Reserva #{self.id} confirmada.")

    def cancelar(self):
        """Cancela la reserva si aún no fue procesada ni cancelada."""
        if self.__estado in (EstadoReserva.CANCELADA, EstadoReserva.PROCESADA):
            raise OperacionNoPermitidaError(
                f"No se puede cancelar una reserva en estado {self.__estado.value}.")
        self.__estado = EstadoReserva.CANCELADA
        logger.info(f"Reserva #{self.id} cancelada.")

    def procesar(self, impuesto=0.19, descuento=0.0):
        """CONFIRMADA -> PROCESADA, calculando el costo. Usa try/except/else/finally."""
        if self.__estado is not EstadoReserva.CONFIRMADA:
            raise OperacionNoPermitidaError(
                f"Solo se procesan reservas confirmadas (estado actual: {self.__estado.value}).")
        try:
            costo = self.servicio.calcular_costo(
                self.horas, impuesto, descuento, **self.parametros)
        except CalculoInconsistenteError as error:
            self.__estado = EstadoReserva.FALLIDA
            raise ReservaInvalidaError(
                f"No se pudo procesar la reserva #{self.id}.") from error   # Encadenamiento
        else:
            # Solo se ejecuta si NO hubo excepción
            self.costo_final = costo
            self.__estado = EstadoReserva.PROCESADA
            logger.info(f"Reserva #{self.id} procesada. Costo final: ${costo:,.2f}")
            return costo
        finally:
            # Siempre se ejecuta, haya o no error
            logger.debug(f"Fin de procesamiento de reserva #{self.id} "
                         f"(estado: {self.__estado.value}).")

    def describir(self):
        costo = f"${self.costo_final:,.2f}" if self.costo_final else "sin calcular"
        return (f"Reserva #{self.id} | {self.cliente.nombre} | {self.servicio.nombre} | "
                f"{self.horas} h | {self.__estado.value} | {costo}")


# ---------------------------------------------------------------------------
# 7. GESTOR (listas internas + operaciones "a prueba de fallos")
# ---------------------------------------------------------------------------
class GestorSoftwareFJ:
    """Administra las listas de clientes, servicios y reservas sin detenerse ante errores."""

    def __init__(self):
        self.clientes = []
        self.servicios = []
        self.reservas = []

    def _ejecutar(self, contexto, accion):
        """Ejecuta 'accion' protegida: registra el error y devuelve None si falla."""
        try:
            resultado = accion()
        except SoftwareFJError as error:          # Errores propios del dominio
            registrar_error(contexto, error)
            print(f"   [ERROR CONTROLADO] {contexto}: {error}")
            return None
        except Exception as error:                # Cualquier error inesperado
            registrar_error(f"{contexto} (inesperado)", error)
            print(f"   [ERROR INESPERADO] {contexto}: {error}")
            return None
        else:
            logger.info(f"{contexto} -> OK")
            print(f"   [OK] {contexto}")
            return resultado
        finally:
            logger.debug(f"Operación finalizada: {contexto}")

    def registrar_cliente(self, **datos):
        cliente = self._ejecutar("Registrar cliente", lambda: Cliente(**datos))
        if cliente:
            self.clientes.append(cliente)
        return cliente

    def crear_servicio(self, clase, **datos):
        servicio = self._ejecutar(f"Crear servicio {clase.__name__}", lambda: clase(**datos))
        if servicio:
            self.servicios.append(servicio)
        return servicio

    def crear_reserva(self, cliente, servicio, horas, **parametros):
        reserva = self._ejecutar(
            "Crear reserva", lambda: Reserva(cliente, servicio, horas, **parametros))
        if reserva:
            self.reservas.append(reserva)
        return reserva

    def ejecutar_reserva(self, reserva, accion, **kwargs):
        """Ejecuta 'confirmar', 'cancelar' o 'procesar' sobre una reserva de forma segura."""
        if reserva is None:
            return self._ejecutar(f"Reserva ({accion})", lambda: (_ for _ in ()).throw(
                ReservaInvalidaError("La reserva no existe (None).")))
        return self._ejecutar(f"Reserva #{reserva.id} ({accion})",
                              lambda: getattr(reserva, accion)(**kwargs))


# ---------------------------------------------------------------------------
# 8. SIMULACIÓN: 10+ OPERACIONES (válidas e inválidas)
# ---------------------------------------------------------------------------
def simular():
    g = GestorSoftwareFJ()
    print("=" * 70)
    print(" SOFTWARE FJ - SIMULACIÓN DE OPERACIONES")
    print("=" * 70)

    print("\n--- CLIENTES ---")
    c1 = g.registrar_cliente(nombre="Ana Pérez", documento="1052300123",
                             correo="ana@correo.com", telefono="3101234567")        # 1 válido
    g.registrar_cliente(nombre="Luis Gómez", documento="987654321",
                        correo="luis-correo.com", telefono="3209876543")            # 2 correo inválido
    g.registrar_cliente(nombre="Marta Ruiz", correo="marta@correo.com",
                        telefono="3001112233")                                      # 3 falta documento
    c2 = g.registrar_cliente(nombre="Carlos Díaz", documento="80123456",
                             correo="carlos@correo.com", telefono="3157778899")     # 4 válido

    print("\n--- SERVICIOS ---")
    sala = g.crear_servicio(ReservaSala, nombre="Sala Ejecutiva", tarifa_hora=50000,
                            capacidad=10)                                           # 5 válido
    g.crear_servicio(ReservaSala, nombre="Sala Rota", tarifa_hora=-100, capacidad=5)  # 6 tarifa negativa
    equipo = g.crear_servicio(AlquilerEquipo, nombre="Portátil Pro", tarifa_hora=8000,
                              stock=3)                                              # 7 válido
    g.crear_servicio(AsesoriaEspecializada, nombre="Asesoría Cloud", tarifa_hora=90000,
                     nivel="maestro")                                               # 8 nivel inválido
    asesoria = g.crear_servicio(AsesoriaEspecializada, nombre="Asesoría Cloud",
                                tarifa_hora=90000, nivel="senior")                  # 9 válido

    print("\n--- RESERVAS ---")
    r1 = g.crear_reserva(c1, sala, 3, asistentes=8)                                 # 10 válida
    g.ejecutar_reserva(r1, "confirmar")
    g.ejecutar_reserva(r1, "procesar", impuesto=0.19, descuento=0.10)               # 11 procesada
    g.ejecutar_reserva(r1, "cancelar")                                              # 12 cancelar procesada (error)

    g.crear_reserva(c2, sala, -2)                                                   # 13 horas inválidas
    g.crear_reserva(c2, equipo, 2, cantidad=5)                                      # 14 excede stock

    r2 = g.crear_reserva(c2, equipo, 4, cantidad=2)                                 # 15 válida
    equipo.disponible = False                                                       # el equipo deja de estar disponible
    g.ejecutar_reserva(r2, "confirmar")                                             # 16 servicio no disponible
    equipo.disponible = True
    g.ejecutar_reserva(r2, "confirmar")
    g.ejecutar_reserva(r2, "procesar", impuesto=0.19, descuento=1.0)                # 17 cálculo inconsistente

    g.crear_reserva(None, asesoria, 2)                                              # 18 sin cliente
    r3 = g.crear_reserva(c1, asesoria, 2)                                           # 19 válida
    g.ejecutar_reserva(r3, "procesar")                                              # 20 procesar sin confirmar
    g.ejecutar_reserva(r3, "cancelar")                                              # 21 cancelación válida

    print("\n--- DEMOSTRACIÓN DE SOBRECARGA (calcular_costo) ---")
    print(f"   Sala 2 h, solo subtotal      : ${sala.calcular_costo(2):,.2f}")
    print(f"   Sala 2 h, con IVA 19 %       : ${sala.calcular_costo(2, 0.19):,.2f}")
    print(f"   Sala 2 h, IVA y desc. 10 %   : ${sala.calcular_costo(2, 0.19, 0.10):,.2f}")
    print(f"   Sala 2 h, método con IVA     : ${sala.calcular_costo_con_iva(2):,.2f}")
    print(f"   Equipo 2 h x 3 unidades      : ${equipo.calcular_costo(2, cantidad=3):,.2f}")

    print("\n--- POLIMORFISMO: describir() ---")
    for servicio in g.servicios:
        print("  ", servicio.describir())

    print("\n--- RESUMEN FINAL ---")
    print(f"   Clientes: {len(g.clientes)} | Servicios: {len(g.servicios)} | "
          f"Reservas: {len(g.reservas)}")
    for reserva in g.reservas:
        print("  ", reserva.describir())
    print(f"\nEl sistema siguió funcionando ante todos los errores. Revisa '{ARCHIVO_LOG}'.")


if __name__ == "__main__":
    simular()
