from datetime import datetime
from os import stat
from sqlalchemy import create_engine, func, desc, delete
from sqlalchemy_utils import database_exists
from config import DATABASE_URI
from models import Base, Command, Segment, Simulation, Trajectory
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from distutils import util
from pandas import DataFrame

import pandas as pd

engine = create_engine(DATABASE_URI)

Session = sessionmaker(bind=engine)


@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def recreate_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def create_database():
    if not database_exists(DATABASE_URI):
        Base.metadata.create_all(engine)


def add_command(type, body):
    command = Command(
        time=datetime.now(),
        processed=False,
        command_type=type,
        command_body=body
    )
    with session_scope() as s:
        s.add(command)
        return command


def get_latest_command():
    with Session() as s:
        command = s.query(Command).filter(
            Command.processed == False).order_by(Command.time).first()
        return command


def get_commands():
    with Session() as s:
        commands = s.query(Command).filter(
            Command.processed == False).order_by(Command.time).all()
        return commands


def clear_commands():
    with Session() as s:
        s.query(Command).delete()
        s.commit()
    s.flush()


def add_simulation(begin, end, gui):

    simulation = Simulation(
        start_time=datetime.now(),
        begin=int(begin),
        end=int(end),
        gui_enabled=util.strtobool(gui),
        status=0,
        total_steps=int(end) - int(begin)
    )
    with session_scope() as s:
        s.add(simulation)
        s.flush()
        return simulation.id

#########ُSEGMENTS###############


def add_segments(simulation_id, segments: DataFrame):
    with session_scope() as s:
        for index in segments.index:
            new_segment = Segment(
                simulation_id=simulation_id,
                virtual_vehicle_id=segments.at[index, 'virtual_vehicle_id'],
                vehicle_id=segments.at[index, 'vehicle_id'],
                departure_address=segments.at[index, 'departure'],
                destination_address=segments.at[index, 'destination'],
                begin_time=int(segments.at[index, 'begin_time']),
                sequence_number=int(segments.at[index, 'sequence_number']),
                status=0
            )
            s.add(new_segment)
        s.flush()


def add_segment(vehicle_id, begin, departure, destination):
    with Session() as s:
        simulation_id = s.query(func.max(Simulation.id)).first()
        last_sequence = s.query(Segment).filter(
            Segment.simulation_id == simulation_id[0] and Segment.vehicle_id == vehicle_id).order_by(desc(Segment.sequence_number)).limit(1).first()

        if last_sequence:
            last_step = last_sequence.sequence_number + 1
        else:
            last_step = 0

        new_segment = Segment(
            simulation_id=simulation_id[0],
            virtual_vehicle_id=f"sv_{vehicle_id}#{last_step + 1}",
            vehicle_id=vehicle_id,
            departure_address=departure,
            destination_address=destination,
            begin_time=begin,
            sequence_number=last_step + 1,
            status=0
        )
        s.add(new_segment)
        s.commit()
    s.flush()


def delete_segment(vehicle_id, destination):
    with Session() as s:
        simulation_id = s.query(func.max(Simulation.id)).first()

        segment = s.query(Segment).filter(
            Segment.vehicle_id == vehicle_id and Segment.simulation_id == simulation_id[0] and Segment.destination_address == destination).first()

        if segment:
            s.delete(segment)
            s.commit()
    s.flush()


def get_segments(simulation_id):
    with Session() as s:
        segments = s.query(Segment).filter(
            Segment.simulation_id == simulation_id).all()
        return segments


def update_segment(id, status):
    with Session() as s:
        segment = s.query(Segment).get(id)
        segment.status = status
        s.commit()


def import_segments(segments):
    if not segments:
        return

    with Session() as s:
        simulation_id = s.query(func.max(Simulation.id)).first()
        if simulation_id:
            simulation_id = simulation_id[0]
        else:
            raise Exception(
                'No Simulation Id found in the database. Atleast ONE simulation_id must exist.')
        s.flush()

    segments = pd.DataFrame(list(segments), columns=[
        'vehicle_id', 'sequence_number', 'begin_time', 'departure', 'destination', 'simulation_id', 'virtual_vehicle_id'])

    groups = segments.groupby('vehicle_id')
    for vehicle_id, group in groups:
        group.sort_values(by='sequence_number',
                          ascending=True, inplace=True)
        sorted_segments = pd.DataFrame(group)

        for index in sorted_segments.index:
            if (index > 0):
                if sorted_segments.at[index, 'departure'] != sorted_segments.at[(index - 1), 'destination']:
                    raise Exception(
                        'segments departure and destinations should follow a chained address. Each departure must be the destination of previous segment.')

            sorted_segments.at[index, 'simulation_id'] = simulation_id
            sorted_segments.at[index,
                               'virtual_vehicle_id'] = f"sv_{vehicle_id}#{sorted_segments['sequence_number'][index]}"

        add_segments(simulation_id, sorted_segments)


def add_trajectory(simulation_id, vehicle_id, latitude, longitude, step):
    trajectory = Trajectory(
        simulation_id=simulation_id,
        vehicle_id=vehicle_id,
        latitude=latitude,
        longitude=longitude,
        timestamp=step
    )
    with session_scope() as s:
        s.add(trajectory)


if __name__ == '__main__':
    # delete_segment('17', "2132 tupper, montreal")
    # add_segment(1, 32000, "176 Peel, montreal", "2132 tupper, montreal")
    recreate_database()
    # add_command('test_command', 'test_body')
    # a = get_latest_command()
    # print(a.command_body)
