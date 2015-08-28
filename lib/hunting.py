import sqlalchemy

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, Date, Boolean, Table
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref

from configparser import ConfigParser
from lib.constants import VT_VERSION, VT_HOME

import os

Base = declarative_base()

DownloadTag = Table('download_tag', Base.metadata,
    Column('tagId', Integer, ForeignKey('tag.id'), primary_key=True),
    Column('downloadId', Integer, ForeignKey('download.id'), primary_key=True)
    )

#VTSampleTag = Table('vt_sample_tag', Base.metadata,
#    Column('tagId', Integer, ForeignKey('vt_tag.id'), primary_key=True),
#    Column('sampleId', Integer, ForeignKey('vt_sample.id'), primary_key=True)
#    )

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
    tags = relationship('Tag', secondary=DownloadTag, backref='download')

    def __repr__(self):
        return "<Download(%d, %s, %s, %d)>" % (self.id, self.md5, self.sha1, self.process_state)


class Tag(Base):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True)
    tag = Column(String)
    downloads = relationship('Download', secondary=DownloadTag, backref='tag')

    def __repr__(self):
        return "<Tag(%d, %s)>" % (self.id, self.tag)


class VTSample(Base):
    __tablename__ = "vt_sample"

    id = Column(Integer, primary_key=True)
    md5 = Column(String)
    sha1 = Column(String)
    sha256 = Column(String)
    size = Column(Integer)
    type = Column(String)
    vhash = Column(String)
    ssdeep = Column(String)
    link = Column(String)
    source_country = Column(String)
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    source_id = Column(String)
    orig_filename = Column(String)
    timestamp = Column(String)
    tags = Column(String)

    #tags = relationship('VTTag', secondary=VTSampleTag, backref='vt_sample')

    def __repr__(self):
        return "<VTSample(%d, %s)>" % (self.id, self.md5)


#class VTTag(Base):
#    __tablename__ = "vt_tag"
#
#    id = Column(Integer, primary_key=True)
#    tag = Column(String)
#    vt_samples = relationship('VTSample', secondary=VTSampleTag, backref='vt_tag')
#
#    def __repr__(self):
#        return "<VTTag(%d, %s)>" % (self.id, self.tag)
#
#
#class VTReport(Base):
#    __tablename__ = "vt_report"
#
#    id = Column(Integer, primary_key=True)
#    sample_id = Column(String, ForeignKey('vt_sample.id'))
#    signature = Column(String)
#    detected = Column(Boolean)
#    vendor_name = Column(String)
#    version = Column(String)
#    date = Column(Date)
#
#    vt_sample = relationship("VTSample", backref=backref('vt_reports', order_by=id))


try:
    config = ConfigParser()
    config.read(os.path.join(VT_HOME, "etc", "vt.ini"))
except ImportError:
    raise SystemExit('vt.ini was not found or was not accessible.')

global engine
engine = create_engine("sqlite:///{0}".format(config.get("locations", "sqlite_db")))
Base.metadata.create_all(engine)
sess = sessionmaker(bind=engine)()


if __name__ == "__main__":
    results =  sess.query(Hit).all()
    print(results)
    results[0].md5 = "1"
    sess.commit()
    results =  sess.query(Hit).all()
    print(results)

def insert_vt_sample(statement):
    engine.execute(
        VTSample.__table__.insert(),
        statement
    )

