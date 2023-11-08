from videotools import db
from videotools.models import MediaObj
from videotools.logger import logg
from videotools.config import DirConfig, OtherConfig


def add_to_db(media):
    print(f'### write to db')
    found_in_db = MediaObj.query.filter_by(src_filename_extension=f'{media.src_filename_extension}').first()
    if found_in_db == None:
        db.session.add(media)
        db.session.commit()
        logg(6, f'File added to DB ({media.src_filename_extension})')
    else:
        db.session.merge(media)
        db.session.commit()
    db.session.close()


def delete_from_db(media):
    print(f'### remove from db')
    found_in_db = MediaObj.query.filter_by(src_filename_extension=f'{media.src_filename_extension}').first()
    if found_in_db != None:
        db.session.delete(found_in_db)
        db.session.commit()
        logg(6, f'File removed from DB ({media.src_filename_extension})')
    db.session.close()


def check_db(src_filename_extension, src_size):
    found_in_db = MediaObj.query.filter_by(src_filename_extension=f'{src_filename_extension}').first()
    db.session.close()
    if found_in_db != None:
        if found_in_db.src_size == src_size:
            logg(6, f'Media file found in DB ({src_filename_extension})')
            return found_in_db
        else:
            return None
    else:
        return None


def recreate_database():
    logg(3, f'Recreate database ({DirConfig.d_conf}database.sqlite)')
    db.drop_all()
    db.create_all()
    db.session.close()
