# from http://docs.sqlalchemy.org/en/latest/orm/tutorial.html

# this code itself is intended to be copy and pasted into an interactive python session
# and is where I was getting my basic understanding and intro to sqlalchemy

import sqlalchemy
#
from sqlalchemy import create_engine
engine = create_engine('sqlite:///:memory:', echo=True)
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
from sqlalchemy import Column, Integer, String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
#
class User(Base):
    __tablename__ = 'users'
    #
    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    password = Column(String)
    #
    # relationship() and relation() are synonyms
    # first arg is class
    # backref is attribute added to "Address" class pointing back to this record
    # cascade options allows garbage collects children of dead parents
    # the relationship thing manages to automagically workout the reference based on 
    #     ForeignKey() sitting in Address, can be explicitly set with foreign_keys=[key])
    addresses = relationship("Address", backref='user', cascade="all, delete, delete-orphan")
    #    
    def __init__(self, name, fullname, password):
        self.name = name
        self.fullname = fullname
        self.password = password
    #   
    def __repr__(self):
       return "<User('%s','%s', '%s')>" % (self.name, self.fullname, self.password)


class Address(Base):
    __tablename__ = 'addresses'
    id = Column(Integer, primary_key=True)
    email_address = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    #   
    def __init__(self, email_address):
        self.email_address = email_address
    #    
    def __repr__(self):
        return "<Address('%s')>" % self.email_address



from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.create_all(engine) 
# drop_all() will remove the tables



ed_user = User('ed', 'Ed Jones', 'edspassword')
session.add(ed_user)

session.add_all([
    User('wendy', 'Wendy Williams', 'foobar'),
    User('mary', 'Mary Contrary', 'xxg527'),
    User('fred', 'Fred Flinstone', 'blah')])

ed_user.password = 'f8s7ccs'


session.dirty

session.new  

session.commit()

jack = User('jack', 'Jack Bean', 'gjffdd')
jack.addresses = [
                Address(email_address='jack@google.com'),
                Address(email_address='j25@yahoo.com')]

session.add(jack)

session.commit()

# lazy load
jack = session.query(User).filter_by(name='jack').one()
jack
jack.addresses

# eager load
from sqlalchemy.orm import subqueryload
jack = session.query(User).\
                options(subqueryload(User.addresses)).\
                filter_by(name='jack').one() 

jack
jack.addresses

session.delete(jack)
session.query(User).filter_by(name='jack').count() 


# this shows 0 because addresses in User contains cascade=...
session.query(Address).filter(
    Address.email_address.in_(['jack@google.com', 'j25@yahoo.com'])
 ).count() 



