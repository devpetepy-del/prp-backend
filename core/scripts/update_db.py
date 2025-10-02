import models
from app.database import engine

models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)
