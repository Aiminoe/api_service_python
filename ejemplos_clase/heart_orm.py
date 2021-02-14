#!/usr/bin/env python
'''
Heart DB manager
---------------------------
Autor: Inove Coding School
Version: 1.1

Descripcion:
Programa creado para administrar la base de datos de registro
de pulsaciones de personas
'''

__author__ = "Inove Coding School"
__email__ = "alumnos@inove.com.ar"
__version__ = "1.1"

import os
import sqlite3
from datetime import datetime, timedelta

import sqlalchemy
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import func

from config import config
# Obtener la path de ejecución actual del script
script_path = os.path.dirname(os.path.realpath(__file__))

# Obtener los parámetros del archivo de configuración
config_path_name = os.path.join(script_path, 'config.ini')
db = config('db', config_path_name)

base = declarative_base()
# Crear el motor (engine) de la base de datos
engine = sqlalchemy.create_engine(f"sqlite:///{db['database']}")


class HeartRate(base):
    __tablename__ = "heartrate"
    id = Column(Integer, primary_key=True)
    time = Column(DateTime)
    name = Column(String)
    value = Column(Integer)
    
    def __repr__(self):
        return f"Paciente {self.name} ritmo cardíaco {self.value}"


def create_schema():
    # Borrar todos las tablas existentes en la base de datos
    # Esta linea puede comentarse sino se eliminar los datos
    base.metadata.drop_all(engine)

    # Crear las tablas
    base.metadata.create_all(engine)


def insert(time, name, heartrate):
    # Crear la session
    Session = sessionmaker(bind=engine)
    session = Session()

    # Crear un nuevo registro de pulsaciones
    pulsaciones = HeartRate(time=time, name=name, value=heartrate)

    # Agregar el registro de pulsaciones a la DB
    session.add(pulsaciones)
    session.commit()


def report(limit=0, offset=0):
    # Crear la session
    Session = sessionmaker(bind=engine)
    session = Session()

    json_result_list = []

    # Obtener el ultimo registor de cada paciente
    # y ademas la cantidad (count) de registros por paciente
    # Esta forma de realizar el count es más avanzada pero más óptima
    # porque de lo contrario debería realizar una query + count  por persona
    # with_entities --> especificamos que queremos que devuelva la query,
    # por defecto retorna un objeto HeartRate, nosotros estamos solicitando
    # que además devuelva la cantidad de veces que se repite cada nombre
    query = session.query(HeartRate).with_entities(HeartRate, func.count(HeartRate.name))

    # Agrupamos por paciente (name) para que solo devuelva
    # un valor por paciente
    query = query.group_by(HeartRate.name)

    # Ordenamos por fecha para obtener el ultimo registro
    query = query.order_by(HeartRate.time)

    if limit > 0:
        query = query.limit(limit)
        if offset > 0:
            query = query.offset(offset)

    for result in query:
        pulsaciones = result[0]
        cantidad = result[1]
        json_result = {}
        json_result['time'] = pulsaciones.time.strftime("%Y-%m-%d %H:%M:%S.%f")
        json_result['name'] = pulsaciones.name
        json_result['last_heartrate'] = pulsaciones.value
        json_result['records'] = cantidad
        json_result_list.append(json_result)

    return json_result_list


def chart(name):
    # Crear la session
    Session = sessionmaker(bind=engine)
    session = Session()

    # Obtener los últimos 250 registros del paciente
    # ordenado por fecha, obteniedo los últimos 250 registros
    query = session.query(HeartRate).filter(HeartRate.name == name).order_by(HeartRate.time.desc())
    query = query.limit(250)
    query_results = query.all()

    if query_results is None or len(query_results) == 0:
        # No data register
        # Bug a proposito dejado para poner a prueba el traceback
        # ya que el sistema espera una tupla
        return []

    # De los resultados obtenidos tomamos el tiempo y las puslaciones pero
    # en el orden inverso, para tener del más viejo a la más nuevo registro
    time = [x.time.strftime("%Y-%m-%d %H:%M:%S.%f") for x in reversed(query_results)]
    heartrate = [x.value for x in reversed(query_results)]

    return time, heartrate

if __name__ == '__main__':
    #insert(datetime.now(), 'Ana', 20)
    #report()
    chart('Hernan')