from typing import Dict, List
from celery import Celery
from models.Producto import Producto
from models.Carrito import Carrito
from models.Venta import Venta
from models.Producto import Producto
from email.mime.text import MIMEText
import smtplib
import redis
import json


celery = Celery('tasks', broker='amqp://admin:admin@localhost:5672/',backend='rpc://')

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

@celery.task
def send_carrito(data:Dict):

    carrito = Carrito(numero=data['numero'], productos=data['productos'])

    products_seleccionados = []
    subtotal = 0.0
    productos = carrito.productos

    for producto in productos:

        product = Producto(name=producto.name, stock=producto.stock, price=producto.price)

        if product.stock > 0:
            products_seleccionados.append(product)
            subtotal += product.stock
        else:
            print("El producto %s no tiene stock para hacer la venta " % (product.name))


    venta = Venta(numero = carrito.numero ,productos = products_seleccionados, subtotal=subtotal, iva=0.15, total=( subtotal * 0.15) + subtotal )

    result = celery.send_task("tasks.send_ventas", args=[venta.dict()], queue="ventas")

    print("El id del resultado de envio a la cola de ventas es => %s"%(result.id))


@celery.task
def send_ventas(data:Dict):

    json_data = json.dumps(data)

    redis_client.set(data['numero'], json_data)

    print("La venta se ha generado correctamente :)")


@celery.task
def operacion(x: int, y: int):
    print(f"La multiplicación de {x} x {y} es {x*y}")
    
    

@celery.task
def send_producto(data: Dict):
    producto = Producto(**data)
    if producto.stock > 0:
        print("Aplica para la venta")
    else:
        print("No aplica para la venta")

@celery.task
def send_tienda(data: Dict):
    carrito = Carrito(**data)
    #print(f"apica para el carrito {carrito.numero}")
    productos = []
    for producto in carrito.productos:
        #inicializar el objeto productos
        product = Producto(name=producto.name, stock=producto.stock, price=producto.price)
        if product.stock > 0:
            productos.append(product)
        else:
            print("El producto %s no tiene stock para hacer la venta" %(product.name))
    
    #inicializar venta (objeto venta)
    venta = Venta(numero=carrito.numero, productos=productos, subtotal=10, iva=0.15, total=30)
    result = celery.send_task("tasks.send_compra", args=[venta.dict()], queue="compra")
    print("El id del resultado de envio a la cola de ventas es => %s" %(result.id))
    
@celery.task
def send_compra(data: Dict):
    venta = Venta(numero=data["numero"], productos=data["productos"], subtotal=data["subtotal"], iva=0, total=data["total"])
    print(f"La venta {venta.numero} se generó correctamente")
    celery.send_task("tasks.send_reporte", args=[data, "Su venta se generó correctamente"], queue="reportes")

@celery.task
def send_reporte(data: Dict, mensaje: str):
    #opt 1 : envia un mensaje a correo electrónico    
    #opt 2: envio de mensaje a redis
    json_data = json.dumps(data)
    redis_client.set(data['numero'], json_data)
    print(mensaje)