from flask import render_template, request, Blueprint
from flask_socketio import emit
from videotools import socketio
from videotools.logger import logg
from videotools import utils
from videotools import job
from videotools.dbing import add_to_db
from videotools import last_frame

from videotools import usubtitles
from videotools import utts

from videotools.config import DirConfig, OtherConfig

from videotools.models import MediaObj
from videotools.job import ObjJobList

import json
import os

main = Blueprint('main', __name__)

obj_job_list = ObjJobList()

###############################################################################


def compare_dict(list):
    shared_video_streams = []
    shared_audio_streams = []
    shared_sub_main_streams = []
    shared_sub_additional_streams = []

    shared_info = set(list[0].as_dict().items())
    for index, item in enumerate(list):
        shared_info = shared_info & set(item.as_dict().items())

        current_video_stream = []
        current_audio_stream = []
        current_sub_main_stream = []
        current_sub_additional_stream = []

        if len(item.list_video) > 2:
            for stream in item.list_video[2:-2].split('}, {'):
                json_stream_video = json.loads(f'{{{stream}}}')
                current_video_stream.append(json_stream_video['index'])
        if len(item.list_audio) > 2:
            for stream in item.list_audio[2:-2].split('}, {'):
                json_stream_audio = json.loads(f'{{{stream}}}')
                current_audio_stream.append(json_stream_audio['index'])
        if len(item.list_subtitle_main) > 2:
            for stream in item.list_subtitle_main[2:-2].split('}, {'):
                json_stream_sub_main = json.loads(f'{{{stream}}}')
                current_sub_main_stream.append(json_stream_sub_main['index'])
        if len(item.list_subtitle_additional) > 2:
            for stream in item.list_subtitle_additional[2:-2].split('}, {'):
                json_stream_sub_additional = json.loads(f'{{{stream}}}')
                current_sub_additional_stream.append(json_stream_sub_additional['index'])

        shared_video_streams.append(current_video_stream)
        shared_audio_streams.append(current_audio_stream)
        shared_sub_main_streams.append(current_sub_main_stream)
        shared_sub_additional_streams.append(current_sub_additional_stream)
    
    one_video_stream = shared_video_streams.pop(0)
    for item in shared_video_streams:
        one_video_stream = set(one_video_stream).intersection(item)
    one_audio_stream = shared_audio_streams.pop(0)
    for item in shared_audio_streams:
        one_audio_stream = set(one_audio_stream).intersection(item)
    one_sub_main_stream = shared_sub_main_streams.pop(0)
    for item in shared_sub_main_streams:
        one_sub_main_stream = set(one_sub_main_stream).intersection(item)
    one_sub_additional_stream = shared_sub_additional_streams.pop(0)
    for item in shared_sub_additional_streams:
        one_sub_additional_stream = set(one_sub_additional_stream).intersection(item)

    new_list_video = []
    for item in sorted(one_video_stream):
        new_item = {'index': f'{item}'}
        new_list_video.append(new_item)
    new_list_audio = []
    for item in sorted(one_audio_stream):
        new_item = {'index': f'{item}'}
        new_list_audio.append(new_item)
    new_list_subtitle_main = []
    for item in sorted(one_sub_main_stream):
        new_item = {'index': f'{item}'}
        new_list_subtitle_main.append(new_item)
    new_list_subtitle_additional = []
    for item in sorted(one_sub_additional_stream):
        new_item = {'index': f'{item}'}
        new_list_subtitle_additional.append(new_item)

    empty = MediaObj()

    empty.list_video = json.dumps(new_list_video)
    empty.list_audio = json.dumps(new_list_audio)
    empty.list_subtitle_main = json.dumps(new_list_subtitle_main)
    empty.list_subtitle_additional = json.dumps(new_list_subtitle_additional) 

    empty = empty.as_dict()
    empty.update(shared_info)
    return empty


###############################################################################


@main.route("/")
@main.route("/home")
def home():
    current_data = []
    for media in utils.obj_media_list.return_list():
        current_data.append(media.as_dict())
    return render_template('index.html', data = current_data)


@socketio.on('connect')
def socket_connect():
    #emit('connected', 'Connected - This is message from SRV')
    current_data = []
    for media in utils.obj_media_list.return_list():
        current_data.append(media.as_dict())
    emit('connected', current_data)


@socketio.on('disconnect')
def socket_disconnect():
    emit('disconnected', 'Disonnected - This is message from SRV')


@socketio.on('selected_files')
def selected_files(msg):
    if len(msg) == 0:
        emit('selected_update', None)
    elif len(msg) == 1:
        for media in utils.obj_media_list.return_list():
            if media.src_filename_extension == msg[0]:
                emit('selected_update', media.as_dict())
    else:
        new_list = []
        for item in msg:
            for media in utils.obj_media_list.return_list():
                if item == media.src_filename_extension:
                    new_list.append(media)
        shared_data = compare_dict(new_list)
        emit('selected_update', shared_data)


###############################################################################


@socketio.on('detect_resolution')
def detect_resolution(msg):
    for item in msg["selected_files"]:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                if msg["button"] == 'start':
                    media.real_width = None
                    media.real_height = None
                    media.dst_width = None
                    media.dst_height = None
                    media.dst_bitrate = None
                    media.cut_str = None
                    media.convert_video_state = 'not_converted'
                    media.mux_state = 'not_muxed'
                    obj_job_list.instant_do(media, 'detect_resolution')


@socketio.on('extract_hdrplus')
def extract_hdrplus(msg):
    for item in msg["selected_files"]:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                if msg["button"] == 'start':
                    media.convert_video_state = 'not_converted'
                    media.mux_state = 'not_muxed'
                    obj_job_list.instant_do(media, 'extract_hdrplus')


@socketio.on('extract_audio')
def extract_audio(msg):
    for item in msg["selected_files"]:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                if msg["button"] == 'start':
                    media.convert_audio_state = 'not_converted'
                    media.convert_audio_voiceover_state = 'not_converted'
                    media.create_voiceover_state = 'not_created'
                    media.mux_state = 'not_muxed'
                    obj_job_list.instant_do(media, 'extract_audio')
                elif msg["button"] == 'stop':
                    obj_job_list.stop_job(media, 'extract_audio')


@socketio.on('convert_video')
def convert_video(msg):
    for item in msg['selected_files']:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                if msg['button'] == 'start':
                    media.mux_state = 'not_muxed'
                    obj_job_list.instant_do(media, 'convert_video')
                elif msg['button'] == 'stop':
                    obj_job_list.stop_job(media, 'convert_video')


@socketio.on('convert_audio')
def convert_audio(msg):
    for item in msg['selected_files']:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                if msg['button'] == 'start':
                    media.mux_state = 'not_muxed'
                    obj_job_list.instant_do(media, 'convert_audio')
                elif msg['button'] == 'stop':
                    obj_job_list.stop_job(media, 'convert_audio')


@socketio.on('convert_voiceover_audio')
def convert_voiceover_audio(msg):
    for item in msg['selected_files']:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                if msg['button'] == 'start':
                    media.mux_state = 'not_muxed'
                    obj_job_list.instant_do(media, 'convert_voiceover_audio')
                elif msg['button'] == 'stop':
                    obj_job_list.stop_job(media, 'convert_voiceover_audio')


###############################################################################
###############################################################################
###############################################################################


@socketio.on('set_media_dst')
def set_media_dst(msg):
    for item in msg[0]:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                utils.setup_media_dst(media, msg[1])


@socketio.on('set_video_stream')
def set_video_stream(msg):
    for item in msg[0]:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                if str(media.video_stream) != msg[1]:
                    logg(6, f'Video changed to {msg[1]} ({media.src_filename_extension})')
                    media.convert_video_state = 'not_converted'
                    media.real_width = None
                    media.real_height = None
                    media.dst_width = None
                    media.dst_height = None
                    media.dst_bitrate = None
                    media.cut_str = None
                    media.mux_state = 'not_muxed'
                    utils.setup_sub_lang(media, msg[1])
                    utils.delays_calc(media)
                else:
                    logg(6, f'Video stream already set to {msg[1]} ({media.src_filename_extension})')


@socketio.on('set_audio_stream')
def set_audio_stream(msg):
    for item in msg[0]:
        print(f'######## msg: {msg}')
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                if str(media.audio_stream) != msg[1]:
                    logg(6, f'Audio stream changed to {msg[1]} ({media.src_filename_extension})')
                    media.extract_audio_state = 'not_extracted'
                    media.convert_audio_state = 'not_converted'
                    media.convert_audio_voiceover_state = 'not_converted'
                    media.create_voiceover_state = 'not_created'
                    media.mux_state = 'not_muxed'
                    utils.setup_audio(media, msg[1])
                    utils.delays_calc(media)
                else:
                    logg(6, f'Audio stream already set to {msg[1]} ({media.src_filename_extension})')


@socketio.on('set_subtitle_stream_main')
def set_subtitle_stream_main(msg):
    for item in msg[0]:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                if str(media.subtitle_stream_main) != msg[1]:
                    logg(6, f'Main subtitle stream changed to {msg[1]} ({media.src_filename_extension})')
                    media.subtitle_main_state = 'not_extracted'
                    media.download_voiceover_state = 'not_downloaded'
                    media.create_voiceover_state = 'not_created'
                    media.convert_audio_voiceover_state = 'not_converted'
                    media.mux_state = 'not_muxed'
                    utils.setup_sub_lang(media, msg[1], 'main')
                else:
                    logg(6, f'Main subtitle stream already set to {msg[1]} ({media.src_filename_extension})')


@socketio.on('set_subtitle_stream_additional')
def set_subtitle_stream_additional(msg):
    for item in msg[0]:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                if str(media.subtitle_stream_additional) != msg[1]:
                    logg(6, f'Additional subtitle stream changed to {msg[1]} ({media.src_filename_extension})')
                    media.subtitle_additional_state = 'not_extracted'
                    media.mux_state = 'not_muxed'
                    utils.setup_sub_lang(media, msg[1], 'additional')
                else:
                    logg(6, f'Additional subtitle stream already set to {msg[1]} ({media.src_filename_extension})')


###############################################################################
###############################################################################
###############################################################################


@socketio.on('download_subtitles_main')
def download_subtitles_main(msg):
    for item in msg['selected_files']:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                if msg['button'] == 'start':
                    media.subtitle_main_state = 'downloading'
                    usubtitles.download_subtitles(media, 'main')
                elif msg['button'] == 'stop':
                    pass


@socketio.on('download_subtitles_additional')
def download_subtitles_additional(msg):
    for item in msg['selected_files']:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                if msg['button'] == 'start':
                    media.subtitle_additional_state = 'downloading'
                    usubtitles.download_subtitles(media, 'additional')
                elif msg['button'] == 'stop':
                    pass


@socketio.on('extract_subtitles')
def extract_subtitles(msg):
    for item in msg["selected_files"]:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                if msg["button"] == 'start':
                    if media.subtitle_stream_main != None or media.subtitle_stream_additional != None:
                        media.mux_state = 'not_muxed'
                    if media.subtitle_stream_main != None:
                        media.download_voiceover_state = 'not_downloaded'
                        media.create_voiceover_state = 'not_created'
                        media.convert_audio_voiceover_state = 'not_converted'
                    obj_job_list.instant_do(media, 'extract_subtitles')
                elif msg["button"] == 'stop':
                    obj_job_list.stop_job(media, 'extract_subtitles')


@socketio.on('sub_time_drift')
def sub_time_drift(msg):
    for item in msg["selected_files"]:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                if msg["button"] == 'backward':
                    time_drift = -abs(float(msg["time_drift"]))
                elif msg["button"] == 'forward':
                    time_drift = float(msg["time_drift"])
                
                if msg["lang"] == 'main':
                    file_path = f'{media.directory}/{media.src_filename}.srt'
                elif msg["lang"] == 'additional':
                    file_path = f'{media.directory}/{media.src_filename}.{OtherConfig.lang_additional}.srt'
                
                if os.path.isfile(file_path):
                    usubtitles.subtitle_process(media, msg["lang"], time_drift)
                    if msg["lang"] == 'main':
                        media.download_voiceover_state = 'not_downloaded'
                        media.create_voiceover_state = 'not_created'
                        media.convert_audio_voiceover_state = 'not_converted'
                    media.mux_state = 'not_muxed'
                else:
                    if msg["lang"] == 'main':
                        logger.logg(3, f'No {OtherConfig.lang_main} subtitles file found ({media.src_filename_extension})')
                    elif msg["lang"] == 'additional':
                        logger.logg(3, f'No {OtherConfig.lang_additional} subtitles file found ({media.src_filename_extension})')


@socketio.on('media_start_stop')
def media_start_stop(msg):
    print(f'### media_start_stop msg: {msg}')
    for item in msg["selected_files"]:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                media.extract_audio_state = 'not_extracted'
                media.subtitle_main_state = 'not_extracted'
                media.subtitle_additional_state = 'not_extracted'
                media.extract_hdrplus_state = 'not_extracted'
                media.download_voiceover_state = 'not_downloaded'
                media.create_voiceover_state = 'not_created'
                media.convert_video_state = 'not_converted'
                media.convert_audio_state = 'not_converted'
                media.convert_audio_voiceover_state = 'not_converted'
                media.mux_state = 'not_muxed'
                utils.set_start_stop(media, start_at = msg["start"], stop_at = msg["stop"])


@socketio.on('download_voiceover')
def download_voiceover(msg):
    print(f'### download_voiceover msg: {msg}')
    for item in msg["selected_files"]:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                if msg["button"] == 'start':
                    media.create_voiceover_state = 'not_created'
                    media.convert_audio_voiceover_state = 'not_converted'
                    media.mux_state = 'not_muxed'
                    obj_job_list.instant_do(media, 'download_voiceover')
                elif msg["button"] == 'stop':
                    obj_job_list.stop_job(media, 'download_voiceover')


@socketio.on('create_voiceover')
def create_voiceover(msg):
    print(f'### create_voiceover msg: {msg}')
    for item in msg["selected_files"]:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                can_do = True
                if media.extract_audio_state != 'extracted':
                    can_do = False
                    logg(6, f'Audio not extracted ({media.src_filename_extension})')
                if media.subtitle_main_state != 'extracted' and media.subtitle_main_state != 'downloaded' and media.subtitle_main_state != 'exist':
                    can_do = False
                    logg(6, f'Subtitles not exist ({media.src_filename_extension})')
                if media.download_voiceover_state != 'downloaded':
                    can_do = False
                    logg(6, f'Voiceover not downloaded ({media.src_filename_extension})')

                if can_do == True:
                    if msg["button"] == 'start':
                        media.convert_audio_voiceover_state = 'not_converted'
                        media.mux_state = 'not_muxed'
                        obj_job_list.instant_do(media, 'create_voiceover')
                    elif msg["button"] == 'stop':
                        obj_job_list.stop_job(media, 'create_voiceover')
                else:
                    logg(6, f'Create voiceover not possible ({media.src_filename_extension})')


@socketio.on('mux')
def mux(msg):
    print(f'### mux msg: {msg}')
    for item in msg["selected_files"]:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                can_do = True
                if media.media_dst == 'archive':
                    if media.convert_video_state != 'converted':
                        can_do = False
                        logg(6, f'Video not converted ({media.src_filename_extension})')
                    if media.convert_audio_state != 'converted':
                        can_do = False
                        logg(6, f'Audio not converted ({media.src_filename_extension})')
                if media.convert_audio_voiceover_state != 'converted':
                    can_do = False
                    logg(6, f'Voiceover audio not converted ({media.src_filename_extension})')

                if can_do == True:
                    if msg["button"] == 'start':
                        obj_job_list.instant_do(media, 'mux')
                else:
                    logg(6, f'Mux not possible ({media.src_filename_extension})')

@socketio.on('move_files')
def move_files(msg):
    print(f'### move_files msg: {msg}')
    for item in msg["selected_files"]:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                can_do = True
                if media.mux_state != 'muxed':
                    can_do = False
                    logg(6, f'Media not muxed ({media.src_filename_extension})')

                if can_do == True:
                    if msg["button"] == 'start':
                        obj_job_list.instant_do(media, 'move_files')
                else:
                    logg(6, f'Moving files not possible ({media.src_filename_extension})')


###############################################################################
###############################################################################
###############################################################################


@socketio.on('show_media_info')
def show_media_info(msg):
    for item in msg:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                logg(1, f'Media info:\n{media}')


@socketio.on('test_conversion')
def test_conversion(msg):
    for item in msg:
        for media in utils.obj_media_list.return_list():
            if item == media.src_filename_extension:
                print(f'\ntest_conversion ==============================================================================')
                last_frame.test_convert_video(media)


@socketio.on('recreate_database')
def recreate_database():
    print(f'### recreate_database')
    dbing.recreate_database()


@socketio.on('test_a')
def test_a():
    print(f'### test_a')
    path = utils.exec_path('ffmpeg')
    print(f'############ path: {path}')


