# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, TIMESTAMP, DECIMAL
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class Command(Base):
    __tablename__ = 'command'
    id = Column(Integer, primary_key=True)
    time = Column(DateTime(timezone=True))
    processed = Column(Boolean)
    message = Column(String)
    command_type = Column(String)
    command_body = Column(String)

    # def __repr__(self):
    #     return "<Command(id='{}', time='{}', processed={}, command_type={})>"\
    #         .format(self.id, self.time, self.processed, self.command_type)


class Simulation(Base):
    __tablename__ = 'simulation'
    id = Column(Integer, primary_key=True)
    start_time = Column(DateTime)
    begin = Column(Integer)
    end = Column(Integer)
    status = Column(Integer)  # 0: Started, 1: Finished, 2: Terminated
    gui_enabled = Column(Boolean)
    total_steps = Column(Integer)
    segments = relationship("Segment")


class Segment(Base):
    __tablename__ = 'segment'
    id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey("simulation.id"))
    virtual_vehicle_id = Column(String)
    vehicle_id = Column(String)
    departure_address = Column(String)
    destination_address = Column(String)
    begin_time = Column(Integer)
    sequence_number = Column(Integer)
    status = Column(Integer)  # 0: unprocessed, 1: processed, 2: passed
    simulation = relationship("Simulation", back_populates="segments")


class Trajectory(Base):
    __tablename__ = 'trajectory'
    id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey("simulation.id"))
    simulation = relationship("Simulation")
    vehicle_id = Column(String)
    timestamp = Column(Integer)
    latitude = Column(DECIMAL(asdecimal=True, precision=16, scale=14))
    longitude = Column(DECIMAL(asdecimal=True, precision=16, scale=14))
