import sqlalchemy

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref

from configparser import ConfigParser
from lib.constants import VT_PROCESSOR_VERSION, VT_HOME

import os

Base = declarative_base()

class Hit(Base):
    __tablename__ = "hunting"

    id = Column(Integer, primary_key=True)
    md5 = Column(String, ForeignKey('download.md5'))
    sha1 = Column(String)
    sha256 = Column(String)
    rule = Column(String)
    created_at = Column(DateTime)
    first_source = Column(String)
    first_country = Column(String)
    file_type = Column(String)
    first_source_type = Column(String)
    orig_file_name = Column(String)
    raw_email_html = Column(Text)
    email_archive = Column(String)
    score = Column(Integer)

    download = relationship("Download", backref=backref('hits', order_by=id))

    def __repr__(self):
        return "<Hit(%d, %s, %s)>" % (self.id, self.md5, self.download)

class Download(Base):
    __tablename__ = "download"

    id = Column(Integer, primary_key=True)
    md5 = Column(String)
    sha1 = Column(String)
    score = Column(Integer)
    # 0 = Not Reviewed
    # 1 = Download
    # 2 = Downloaded, Awaiting Processing
    # 3 = Processing
    # 4 = Processed
    # 5 = Do Not Download
    # 6 = Error Downloading
    process_state = Column(Integer)


    def __repr__(self):
        return "<Download(%d, %s, %s, %d)>" % (self.id, self.md5, self.sha1, self.process_state)

try:
    config = ConfigParser()
    config.read(os.path.join(VT_HOME, "etc", "vt.ini"))
except ImportError:
    raise SystemExit('vt.ini was not found or was not accessible.')

engine = create_engine("sqlite:///{0}".format(config.get("locations", "sqlite_db")))
Base.metadata.create_all(engine)
sess = sessionmaker(bind=engine)()


if __name__ == "__main__":
    results =  sess.query(Hit).all()
    print results
    results[0].md5 = "1"
    sess.commit()
    results =  sess.query(Hit).all()
    print results
