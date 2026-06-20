"""
Sistema de mensajes programados para ToDus.
Permite enviar mensajes con delay, diarios o por intervalo.
"""

import time
import threading
import logging
import heapq
from datetime import datetime, timedelta
from typing import Callable, Optional, Union, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("todus.scheduler")


class ScheduleType(Enum):
    """Tipos de programación disponibles."""
    DELAY = "delay"
    DAILY = "daily"
    INTERVAL = "interval"
    CRON = "cron"  # Para futura expansión


@dataclass(order=True)
class ScheduledTask:
    """Tarea programada en la cola de prioridad."""
    next_run: float
    priority: int
    task_id: str
    client: Any
    to_phone: str
    body: str
    schedule_type: ScheduleType
    interval: Optional[float] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    max_runs: Optional[int] = None
    run_count: int = 0
    callback: Optional[Callable] = None
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)

    def __lt__(self, other):
        """Para el heap queue (prioridad por next_run)."""
        if self.next_run == other.next_run:
            return self.priority < other.priority
        return self.next_run < other.next_run


class ToDusScheduler:
    """
    Sistema de mensajes programados para ToDus.
    
    Ejemplo:
        scheduler = ToDusScheduler(client)
        scheduler.send_later("5351234567", "Hola en 5 minutos", delay=300)
        scheduler.schedule_daily("5351234567", "Buenos días!", hour=8, minute=0)
        scheduler.schedule_interval("5351234567", "¿Sigues ahí?", interval=3600)
        scheduler.start()  # Inicia el thread de procesamiento
    """

    def __init__(self, client, check_interval: float = 1.0):
        """
        Args:
            client: Instancia de ToDusClient2
            check_interval: Intervalo de verificación de tareas (segundos)
        """
        self.client = client
        self.check_interval = check_interval
        self._tasks: List[ScheduledTask] = []  # Heap queue
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._next_id = 0
        self._task_counter = 0

    def _generate_task_id(self) -> str:
        """Genera un ID único para cada tarea."""
        self._task_counter += 1
        return f"task_{self._task_counter}_{int(time.time())}"

    def _calculate_next_run(self, schedule_type: ScheduleType, **kwargs) -> float:
        """Calcula el próximo timestamp de ejecución."""
        now = time.time()
        
        if schedule_type == ScheduleType.DELAY:
            delay = kwargs.get("delay", 0)
            return now + delay
            
        elif schedule_type == ScheduleType.DAILY:
            hour = kwargs.get("hour", 0)
            minute = kwargs.get("minute", 0)
            now_dt = datetime.now()
            target = datetime(
                now_dt.year, now_dt.month, now_dt.day,
                hour, minute, 0, 0
            )
            if target <= now_dt:
                target += timedelta(days=1)
            return target.timestamp()
            
        elif schedule_type == ScheduleType.INTERVAL:
            interval = kwargs.get("interval", 60)
            return now + interval
            
        return now + 60  # fallback

    def _run_task(self, task: ScheduledTask) -> bool:
        """Ejecuta una tarea programada."""
        try:
            # Enviar mensaje
            self.client.send_message(task.to_phone, task.body)
            logger.debug(f"Tarea {task.task_id} enviada a {task.to_phone}")
            
            # Incrementar contador de ejecuciones
            task.run_count += 1
            
            # Llamar callback si existe
            if task.callback:
                try:
                    task.callback(task.to_phone, task.body, task.run_count, *task.args, **task.kwargs)
                except Exception as e:
                    logger.error(f"Error en callback de {task.task_id}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error enviando tarea {task.task_id}: {e}")
            return False

    def _reschedule_task(self, task: ScheduledTask) -> bool:
        """
        Reprograma una tarea si debe repetirse.
        Retorna True si se reprogramó, False si terminó.
        """
        # Verificar si tiene máximo de ejecuciones
        if task.max_runs is not None and task.run_count >= task.max_runs:
            logger.debug(f"Tarea {task.task_id} completó {task.run_count} ejecuciones, finalizada")
            return False
        
        # Calcular próxima ejecución según el tipo
        if task.schedule_type == ScheduleType.DELAY:
            # Las tareas con delay se ejecutan una sola vez
            return False
            
        elif task.schedule_type == ScheduleType.DAILY:
            next_run = self._calculate_next_run(
                ScheduleType.DAILY,
                hour=task.hour,
                minute=task.minute
            )
            task.next_run = next_run
            return True
            
        elif task.schedule_type == ScheduleType.INTERVAL:
            next_run = self._calculate_next_run(
                ScheduleType.INTERVAL,
                interval=task.interval
            )
            task.next_run = next_run
            return True
            
        return False

    def send_later(self, to_phone: str, body: str, delay: float,
                   callback: Optional[Callable] = None,
                   *args, **kwargs) -> str:
        """
        Envía un mensaje después de un tiempo determinado.
        
        Args:
            to_phone: Número de teléfono destino
            body: Contenido del mensaje
            delay: Tiempo de espera en segundos
            callback: Función a llamar después de enviar (opcional)
        
        Returns:
            ID de la tarea programada
        """
        task_id = self._generate_task_id()
        next_run = self._calculate_next_run(ScheduleType.DELAY, delay=delay)
        
        task = ScheduledTask(
            next_run=next_run,
            priority=0,
            task_id=task_id,
            client=self.client,
            to_phone=to_phone,
            body=body,
            schedule_type=ScheduleType.DELAY,
            max_runs=1,
            callback=callback,
            args=args,
            kwargs=kwargs
        )
        
        with self._lock:
            heapq.heappush(self._tasks, task)
            
        logger.info(f"Tarea {task_id} programada en {delay}s para {to_phone}")
        return task_id

    def schedule_daily(self, to_phone: str, body: str,
                       hour: int = 0, minute: int = 0,
                       max_runs: Optional[int] = None,
                       callback: Optional[Callable] = None,
                       *args, **kwargs) -> str:
        """
        Programa un mensaje para enviarse todos los días a una hora específica.
        
        Args:
            to_phone: Número de teléfono destino
            body: Contenido del mensaje
            hour: Hora del día (0-23)
            minute: Minuto (0-59)
            max_runs: Máximo de ejecuciones (None = infinito)
            callback: Función a llamar después de cada envío
        
        Returns:
            ID de la tarea programada
        """
        task_id = self._generate_task_id()
        next_run = self._calculate_next_run(ScheduleType.DAILY, hour=hour, minute=minute)
        
        task = ScheduledTask(
            next_run=next_run,
            priority=0,
            task_id=task_id,
            client=self.client,
            to_phone=to_phone,
            body=body,
            schedule_type=ScheduleType.DAILY,
            hour=hour,
            minute=minute,
            max_runs=max_runs,
            callback=callback,
            args=args,
            kwargs=kwargs
        )
        
        with self._lock:
            heapq.heappush(self._tasks, task)
            
        logger.info(f"Tarea diaria {task_id} programada a las {hour:02d}:{minute:02d} para {to_phone}")
        return task_id

    def schedule_interval(self, to_phone: str, body: str,
                          interval: float,
                          max_runs: Optional[int] = None,
                          callback: Optional[Callable] = None,
                          *args, **kwargs) -> str:
        """
        Programa un mensaje para enviarse cada cierto intervalo.
        
        Args:
            to_phone: Número de teléfono destino
            body: Contenido del mensaje
            interval: Intervalo en segundos
            max_runs: Máximo de ejecuciones (None = infinito)
            callback: Función a llamar después de cada envío
        
        Returns:
            ID de la tarea programada
        """
        task_id = self._generate_task_id()
        next_run = self._calculate_next_run(ScheduleType.INTERVAL, interval=interval)
        
        task = ScheduledTask(
            next_run=next_run,
            priority=0,
            task_id=task_id,
            client=self.client,
            to_phone=to_phone,
            body=body,
            schedule_type=ScheduleType.INTERVAL,
            interval=interval,
            max_runs=max_runs,
            callback=callback,
            args=args,
            kwargs=kwargs
        )
        
        with self._lock:
            heapq.heappush(self._tasks, task)
            
        logger.info(f"Tarea por intervalo {task_id} programada cada {interval}s para {to_phone}")
        return task_id

    def cancel_task(self, task_id: str) -> bool:
        """Cancela una tarea programada por su ID."""
        with self._lock:
            for i, task in enumerate(self._tasks):
                if task.task_id == task_id:
                    # Eliminar la tarea del heap
                    self._tasks[i] = self._tasks[-1]
                    self._tasks.pop()
                    heapq.heapify(self._tasks)
                    logger.info(f"Tarea {task_id} cancelada")
                    return True
        logger.warning(f"Tarea {task_id} no encontrada")
        return False

    def list_tasks(self) -> List[Dict[str, Any]]:
        """Lista todas las tareas programadas."""
        tasks = []
        with self._lock:
            for task in self._tasks:
                tasks.append({
                    "id": task.task_id,
                    "to": task.to_phone,
                    "body": task.body[:50] + "..." if len(task.body) > 50 else task.body,
                    "type": task.schedule_type.value,
                    "next_run": datetime.fromtimestamp(task.next_run).isoformat(),
                    "run_count": task.run_count,
                    "max_runs": task.max_runs or "∞",
                })
        return tasks

    def _worker(self):
        """Bucle principal del scheduler."""
        logger.info("Scheduler iniciado")
        
        while self._running:
            try:
                now = time.time()
                task_to_run = None
                
                with self._lock:
                    if self._tasks and self._tasks[0].next_run <= now:
                        task_to_run = heapq.heappop(self._tasks)
                
                if task_to_run:
                    # Ejecutar tarea
                    success = self._run_task(task_to_run)
                    
                    # Reprogramar si corresponde
                    if success and self._reschedule_task(task_to_run):
                        with self._lock:
                            heapq.heappush(self._tasks, task_to_run)
                
                # Esperar hasta la próxima tarea o el intervalo de verificación
                with self._lock:
                    if self._tasks:
                        next_wait = max(0, self._tasks[0].next_run - time.time())
                    else:
                        next_wait = self.check_interval
                
                time.sleep(min(next_wait, self.check_interval))
                
            except Exception as e:
                logger.error(f"Error en worker del scheduler: {e}")
                time.sleep(self.check_interval)

    def start(self):
        """Inicia el scheduler en un thread separado."""
        if self._running:
            logger.warning("Scheduler ya está en ejecución")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        logger.info("Scheduler iniciado en thread separado")

    def stop(self):
        """Detiene el scheduler."""
        if not self._running:
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("Scheduler detenido")

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del scheduler."""
        with self._lock:
            return {
                "running": self._running,
                "pending_tasks": len(self._tasks),
                "next_task": self._tasks[0].next_run if self._tasks else None,
                "next_task_eta": max(0, self._tasks[0].next_run - time.time()) if self._tasks else None
            }


# Compatibilidad: Añadir propiedades a ToDusClient2
def patch_client():
    """Parchea ToDusClient2 para añadir el scheduler."""
    from .client import ToDusClient2
    
    original_init = ToDusClient2.__init__
    
    def __init__(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self._scheduler = None
    
    def _get_scheduler(self):
        if self._scheduler is None:
            from .scheduler import ToDusScheduler
            self._scheduler = ToDusScheduler(self)
            self._scheduler.start()
        return self._scheduler
    
    ToDusClient2.__init__ = __init__
    ToDusClient2.scheduler = property(_get_scheduler)
    ToDusClient2.send_later = lambda self, *a, **k: self.scheduler.send_later(*a, **k)
    ToDusClient2.schedule_daily = lambda self, *a, **k: self.scheduler.schedule_daily(*a, **k)
    ToDusClient2.schedule_interval = lambda self, *a, **k: self.scheduler.schedule_interval(*a, **k)
    ToDusClient2.cancel_task = lambda self, *a, **k: self.scheduler.cancel_task(*a, **k)
    ToDusClient2.list_tasks = lambda self, *a, **k: self.scheduler.list_tasks(*a, **k)
    ToDusClient2.stop_scheduler = lambda self: self.scheduler.stop()