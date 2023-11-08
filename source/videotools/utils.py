from videotools.config import DirConfig, OtherConfig
from videotools.models import MediaObj
from videotools.logger import logg
from videotools.probe import probe_file, check_lenght
from videotools.dbing import add_to_db, check_db
from videotools import resdet
from videotools import socketio, emit

from videotools import usubtitles

from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler

from datetime import datetime
import time
import json
import os
import shutil
import re


########################################################################################

class ObjMediaList():
    media_list = []

    arch_tts_list = []

    def add_media(self, src_file_path):
        tmp_fp = src_file_path.split('/')
        directory = '/'.join(tmp_fp[:len(tmp_fp) - 1]) + '/'
        src_filename_extension = tmp_fp[len(tmp_fp) - 1]
        src_filename = src_filename_extension.split('.')
        src_filename = '.'.join(src_filename[:len(src_filename) - 1])
        src_extension = src_filename_extension.split('.')
        src_extension = src_extension[len(src_extension) - 1]
        src_size = os.path.getsize(src_file_path)
        
        if src_filename_extension not in obj_media_list.return_src_filename_extension():
            logg(6, f'New file: {src_file_path}')
            media = check_db(src_filename_extension, src_size)

            if media != None:
                socketio.emit('media_add', media.as_dict())
                if not os.path.isfile(f'{media.directory_temp}{media.dst_filename}.info.video.json') or not os.path.isfile(f'{media.directory_temp}{media.dst_filename}.info.audio.json') or not os.path.isfile(f'{media.directory_temp}{media.dst_filename}.info.subtitles.json') or not os.path.isfile(f'{media.directory_temp}{media.dst_filename}.info.madiainfo.json'):
                    if media.media_dst == 'archive':
                        info_video, info_audio, info_subtitles, info_mediainfo =  probe_file(media)
                        self.write_meta(media, info_video, info_audio, info_subtitles, info_mediainfo)
                delays_calc(media)
                
                h265_file = f'{media.directory_temp + media.dst_filename}.h265'
                if os.path.isfile(h265_file):
                    if os.path.getsize(h265_file) > 1000000:
                        if media.convert_video_state != 'converted':
                            media.convert_video_state = 'converted'
                            add_to_db(media)

                
            elif media == None:
                media = MediaObj(src_filename_extension=src_filename_extension, src_size=src_size, src_file_path=src_file_path, src_filename=src_filename, src_extension=src_extension, directory=directory)
                socketio.emit('media_add', media.as_dict())

                set_filename(media)
                info_video, info_audio, info_subtitles, info_mediainfo =  probe_file(media)
                set_directories(media)
                delays_calc(media)
                setup_media_dst(media, 'initial')
                logg(6, f'File scanned ({media.src_filename_extension})')

                add_to_db(media)
                if media.media_dst == 'archive':
                    self.write_meta(media, info_video, info_audio, info_subtitles, info_mediainfo)

                if media.media_dst == 'rearchive':
                    if not os.path.isfile(f'{media.directory}{media.src_filename}.srt'):
                        shutil.copy(f'{media.directory_archive}{media.dst_filename}.srt', f'{media.directory}{media.src_filename}.srt')
                    if not os.path.isfile(f'{media.directory}{media.src_filename}.{OtherConfig.lang_additional}.srt'):
                        shutil.copy(f'{media.directory_archive}{media.dst_filename}.{OtherConfig.lang_additional}.srt', f'{media.directory}{media.src_filename}.{OtherConfig.lang_additional}.srt')

                socketio.emit('media_update', media.as_dict())

            file_check(media)
            self.media_list.append(media)

        else:
            print(f'######################## media already in obj_media_list, db not checked: {src_file_path}')

    def remove_media(self, src_file_path):
        for media in self.media_list:
            if media.src_file_path == src_file_path:
                logg(6, f'File removed: {src_file_path}')
                self.media_list.remove(media)
                socketio.emit('media_rem', media.as_dict())

    def print_media_list(self):
        print(f'### media_list = {self.media_list}')

    def return_list(self):
        return self.media_list
    
    def return_src_filename_extension(self):
        tmp = []
        for item in self.media_list:
            tmp.append(item.src_filename_extension)
        return tmp
    
    def write_meta(self, media, info_video, info_audio, info_subtitles, info_mediainfo):
        with open(f'{media.directory_temp}{media.dst_filename}.info.video.json', 'w', encoding='utf-8') as f:
            json.dump(info_video, f, ensure_ascii=False, indent=4)
        with open(f'{media.directory_temp}{media.dst_filename}.info.audio.json', 'w', encoding='utf-8') as f:
            json.dump(info_audio, f, ensure_ascii=False, indent=4)
        with open(f'{media.directory_temp}{media.dst_filename}.info.subtitles.json', 'w', encoding='utf-8') as f:
            json.dump(info_subtitles, f, ensure_ascii=False, indent=4)
        with open(f'{media.directory_temp}{media.dst_filename}.info.madiainfo.json', 'w', encoding='utf-8') as f:
            json.dump(info_mediainfo, f, ensure_ascii=False, indent=4)


########################################################################################

class NewEvent(LoggingEventHandler):
    def on_created(self, event):
        super(LoggingEventHandler, self).on_created(event)
        if event.src_path[-3:] in OtherConfig.video_extensions:
            obj_media_list.add_media(event.src_path)

    def on_deleted(self, event):
        super(LoggingEventHandler, self).on_deleted(event)
        if event.src_path[-3:] in OtherConfig.video_extensions:
            obj_media_list.remove_media(event.src_path)
        elif event.src_path[-3:] == 'srt':
            self.update_media(event.src_path, 'delete')

    def on_moved(self, event):
        super(LoggingEventHandler, self).on_moved(event)
        self.update_media(event.dest_path, 'add')

    def update_media(self, dest_path, update_type):
        new_filename = dest_path.split('/')[-1][:-4]
        new_filename_extension = dest_path.split('/')[-1][-3:]
        lang_main = False
        lang_additional = False

        if new_filename_extension == 'srt':
            if new_filename[-3:] == OtherConfig.lang_additional:
                lang_additional = True
                new_filename = new_filename[:-4]
            else:
                lang_main = True

            for media in obj_media_list.return_list():
                if media.src_filename == new_filename:
                    if update_type == 'add':
                        if lang_main == True:
                            usubtitles.subtitle_process(media, 'main')
                            media.subtitle_main_state = 'exist'
                        if lang_additional == True:
                            usubtitles.subtitle_process(media, 'additional')
                            media.subtitle_additional_state = 'exist'
                    elif update_type == 'delete':
                        if lang_main == True: media.subtitle_main_state = None
                        if lang_additional == True: media.subtitle_additional_state = None
                    add_to_db(media)


def monitor_changes():
    print(f'### monitor_changes & initial_directory_scan')
    initial_directory_scan(DirConfig.d_make_n)
    event_handler = NewEvent()
    new_observer = Observer()
    new_observer.schedule(event_handler, DirConfig.d_make_n, recursive=True)
    new_observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        new_observer.stop()
    new_observer.join()


def initial_directory_scan(dir):
    for file_name in sorted(os.listdir(dir), key=str.casefold):
        if file_name[-3:] in OtherConfig.video_extensions:
            obj_media_list.add_media(dir + file_name)


########################################################################################

obj_media_list = ObjMediaList()

########################################################################################


def set_filename(media):
    min_year = 1950
    staff_pos = 0
    staff = ''

    media.src_filename_extension = media.src_file_path.split('/')[-1]
    media.src_filename = '.'.join(media.src_file_path.split('/')[-1].split('.')[:-1])
    media.src_extension = media.src_file_path.split('.')[-1]

    tmp = media.src_filename.replace(' ',  '.').replace('..',  '.').replace('-', '.').replace('(', '').replace(')', '').replace('[', '').replace(']', '')
    words = tmp.split('.')

    for item in words:
        if len(item) == 0:
            words.remove(item)

    for s_idx, s_item in enumerate(reversed(words)):
        try:
            if (s_item[0] == 'S' or s_item[0] == 's') and (s_item[3] == 'E' or s_item[3] == 'e') and (s_item[1:3].isdigit() == True) and (s_item[4:6].isdigit() == True):
                s_item = 'S' + s_item[1:3] + 'E' + s_item[4:6]
                staff_pos = s_idx
                staff = s_item
                media.video_type = 'serie'
                break
            elif int(s_item) >= min_year and int(s_item) <= int(datetime.now().year):
                staff_pos = s_idx
                staff = s_item
                media.video_type = 'movie'
                break
        except:
            pass

    base_filename = words[:-staff_pos - 1]
    for b_idx, b_item in enumerate(base_filename):
        b_item = b_item[0].upper() + b_item[1:]
        base_filename[b_idx] = b_item

    base_filename.append(staff)
    media.base_filename = '.'.join(base_filename)

    if media.video_type == 'movie':
        media.dst_directory = media.base_filename
        media.base_directory = media.base_filename
    elif media.video_type == 'serie':
        media.dst_directory = media.base_filename[:-7]
        media.base_directory = media.base_filename[:-7]

    if 'imax' in media.src_filename.lower():
        media.imax = True
    else:
        media.imax = False


def set_directories(media):
    title_base = ' '.join(media.base_filename.split(
        '.')[:len(media.base_filename.split('.')) - 1])
    title_suffix = str(media.base_filename.split('.')[-1:][0])
    media.title = title_base + ' (' + title_suffix + ')'

    current_dir = media.src_file_path.split('/')
    del current_dir[len(current_dir) - 1]
    media.directory = '/'.join(current_dir) + '/'

    media.directory_temp = DirConfig.d_temp
    media.directory_tts = DirConfig.d_temp + media.dst_filename + '.VO/'

    media.directory_done = DirConfig.d_done_n

    if media.video_type == 'movie':
        if media.src_width == 3840 or media.src_height == 2160:
            if media.dhdr == True and media.hdr == True:
                media.directory_final = DirConfig.fin_movies_uhd_dhdr
            elif media.dhdr == False and media.hdr == True:
                media.directory_final = DirConfig.fin_movies_uhd_hdr
            elif media.dhdr == False and media.hdr == False:
                media.directory_final = DirConfig.fin_movies_uhd

        if (media.src_width <= 1920 and media.src_width >= 1916) or media.src_height == 1080:
            if media.dhdr == True and media.hdr == True:
                media.directory_final = DirConfig.fin_movies_fhd_dhdr
            elif media.dhdr == False and media.hdr == True:
                media.directory_final = DirConfig.fin_movies_fhd_hdr
            elif media.dhdr == False and media.hdr == False: 
                media.directory_final = DirConfig.fin_movies_fhd
        
        media.directory_final_meta = DirConfig.fin_meta_movies
        media.directory_archive = DirConfig.d_arch_movies + media.dst_directory + '/'

    elif media.video_type == 'serie':
        if media.src_width == 3840 or media.src_height == 2160:
            if media.dhdr == True and media.hdr == True:
                media.directory_final = DirConfig.fin_series_uhd_dhdr + media.base_directory + '/'
            elif media.dhdr == False and media.hdr == True:
                media.directory_final = DirConfig.fin_series_uhd_hdr + media.base_directory + '/'
            elif media.dhdr == False and media.hdr == False:
                media.directory_final = DirConfig.fin_series_uhd + media.base_directory + '/'

        if (media.src_width <= 1920 and media.src_width >= 1916) or media.src_height == 1080:
            if media.dhdr == True and media.hdr == True:
                media.directory_final = DirConfig.fin_series_fhd_dhdr + media.base_directory + '/'
            elif media.dhdr == False and media.hdr == True:
                media.directory_final = DirConfig.fin_series_fhd_hdr + media.base_directory + '/'
            elif media.dhdr == False and media.hdr == False:
                media.directory_final = DirConfig.fin_series_fhd + media.base_directory + '/'

        media.directory_final_meta = DirConfig.fin_meta_series + media.base_directory  + '/'
        media.directory_archive = DirConfig.d_arch_series + media.base_directory + '/'


def delays_calc(media):
    # print(f'media.video_delay: {media.video_delay}')
    # print(f'media.audio_delay: {media.audio_delay}')
    # print(f'media.video_duration: {media.video_duration}')
    # print(f'media.audio_duration: {media.audio_duration}')
    # print(f'media.start_at: {media.start_at}')
    # print(f'media.stop_at: {media.stop_at}')
    # print(f'=======')

    # media.video_delay = 10
    # media.audio_delay = 10
    # media.video_duration = 1000
    # media.audio_duration = 1000
    # media.start_at = 0
    # media.stop_at = 1000
    # print(f'media.video_delay: {media.video_delay}')
    # print(f'media.audio_delay: {media.audio_delay}')
    # print(f'media.video_duration: {media.video_duration}')
    # print(f'media.audio_duration: {media.audio_duration}')
    # print(f'media.start_at: {media.start_at}')
    # print(f'media.stop_at: {media.stop_at}')

    proper_audio_delay = 0
    proper_video_delay = 0
    proper_video_start_at = 0
    proper_video_time = 0
    proper_audio_start_at = 0
    proper_audio_time = 0


    if media.video_delay == 0 and media.audio_delay == 0:
        #logg(2, f'No delays in video or audio ({media.src_filename}.{media.src_extension})')

        if media.video_duration == media.audio_duration:
            #logg(2, f'Duration of video ({media.video_duration}) and audio ({media.audio_duration}) equal ({media.src_filename}.{media.src_extension})')
            if media.start_at < media.video_duration:
                proper_video_start_at = media.start_at
                proper_audio_start_at = media.start_at
            if media.stop_at == 0:
                proper_video_time = media.video_duration - proper_video_start_at
                proper_audio_time = media.audio_duration - proper_audio_start_at
            elif media.stop_at > media.video_duration:
                proper_video_time = media.video_duration - proper_video_start_at
                proper_audio_time = media.audio_duration - proper_audio_start_at
            elif media.stop_at <= media.video_duration:
                proper_video_time = media.stop_at - proper_video_start_at
                proper_audio_time = media.stop_at - proper_audio_start_at

        elif media.video_duration > media.audio_duration:
            #logg(2, f'Duration of video ({media.video_duration}) longer than audio ({media.audio_duration}) ({media.src_filename}.{media.src_extension})')
            if media.start_at < media.audio_duration:
                proper_video_start_at = media.start_at
                proper_audio_start_at = media.start_at
            if media.stop_at == 0:
                proper_video_time = media.audio_duration - proper_audio_start_at
                proper_audio_time = media.audio_duration - proper_audio_start_at
            elif media.stop_at > media.audio_duration:
                proper_video_time = media.audio_duration - proper_audio_start_at
                proper_audio_time = media.audio_duration - proper_audio_start_at
            elif media.stop_at <= media.audio_duration:
                proper_video_time = media.stop_at - proper_audio_start_at
                proper_audio_time = media.stop_at - proper_audio_start_at

        elif media.video_duration < media.audio_duration:
            #logg(2, f'Duration of audio ({media.audio_duration}) longer than video ({media.video_duration}) ({media.src_filename}.{media.src_extension})')
            if media.start_at < media.video_duration:
                proper_video_start_at = media.start_at
                proper_audio_start_at = media.start_at
            if media.stop_at == 0:
                proper_video_time = media.video_duration - proper_video_start_at
                proper_audio_time = media.video_duration - proper_video_start_at
            elif media.stop_at > media.video_duration:
                proper_video_time = media.video_duration - proper_video_start_at
                proper_audio_time = media.video_duration - proper_video_start_at
            elif media.stop_at <= media.video_duration:
                proper_video_time = media.stop_at - proper_video_start_at
                proper_audio_time = media.stop_at - proper_video_start_at

    elif media.video_delay != 0 and media.audio_delay != 0:
        #logg(2, f'Delays in video ({media.video_delay}) and audio ({media.audio_delay}) ({media.src_filename}.{media.src_extension})')
        # bigger_delay = media.video_delay if media.video_delay >= media.audio_delay else media.audio_delay
        # print(f'bigger_delay: {bigger_delay}')

        if media.video_duration == media.audio_duration:
            #logg(2, f'Duration of video ({media.video_duration}) and audio ({media.audio_duration}) equal ({media.src_filename}.{media.src_extension})')
            #if media.start_at < media.video_duration and media.start_at < media.audio_duration:
                
            if media.audio_delay == media.video_delay:
                if media.start_at < media.video_duration and media.start_at < media.audio_duration:
                    if media.start_at == 0:
                        proper_video_start_at = media.video_delay
                        proper_audio_start_at = media.audio_delay
                    elif media.start_at > media.video_delay:
                        proper_video_start_at = media.start_at - media.video_delay
                        proper_audio_start_at = media.start_at - media.audio_delay
                    elif media.start_at <= media.video_delay:
                        proper_video_start_at = media.video_delay
                        proper_audio_start_at = media.video_delay

                if media.stop_at == 0:
                    proper_video_time = media.video_duration - proper_audio_start_at
                    proper_audio_time = media.video_duration - proper_audio_start_at
                elif media.stop_at > media.video_duration:
                    proper_video_time = media.video_duration - proper_audio_start_at
                    proper_audio_time = media.video_duration - proper_audio_start_at
                elif media.stop_at <= media.video_duration:
                    proper_video_time = media.stop_at - proper_audio_start_at
                    proper_audio_time = media.stop_at - proper_audio_start_at

            elif media.audio_delay > media.video_delay:
                proper_audio_delay = media.audio_delay - media.video_delay
                if media.start_at == 0:
                    proper_video_start_at = 0
                    proper_audio_start_at = 0
                elif media.start_at > media.video_delay:
                    proper_video_start_at = media.start_at - media.video_delay
                    proper_audio_start_at = media.start_at - media.video_delay
                elif media.start_at <= media.video_delay:
                    proper_video_start_at = media.video_delay
                    proper_audio_start_at = media.video_delay

            elif media.audio_delay < media.video_delay:
                if media.start_at == 0:
                    proper_video_start_at = 0
                    proper_audio_start_at = media.video_delay - media.audio_delay
                elif media.start_at > media.video_delay:
                    proper_video_start_at = media.start_at - media.video_delay
                    proper_audio_start_at = media.start_at - media.audio_delay
                elif media.start_at <= media.video_delay:
                    proper_video_start_at = 0
                    proper_audio_start_at = media.video_delay - media.audio_delay



                # elif media.start_at >= media.video_duration:
                #     proper_audio_start_at = media.video_delay

                # if media.stop_at == 0:
                #     proper_video_time = media.video_duration - proper_audio_start_at
                #     proper_audio_time = media.video_duration - proper_audio_start_at
                # elif media.stop_at > media.video_duration:
                #     proper_video_time = media.video_duration - proper_audio_start_at
                #     proper_audio_time = media.video_duration - proper_audio_start_at
                # elif media.stop_at <= media.video_duration:
                #     proper_video_time = media.stop_at - proper_audio_start_at
                #     proper_audio_time = media.stop_at - proper_audio_start_at

    elif media.video_delay != 0 and media.audio_delay == 0:
        #logg(2, f'Delay in video ({media.video_delay}) ({media.src_filename}.{media.src_extension})')

        if media.video_duration == media.audio_duration:
            #logg(2, f'Duration of video ({media.video_duration}) and audio ({media.audio_duration}) equal ({media.src_filename}.{media.src_extension})')
            if media.start_at < media.video_duration:
                if media.start_at == 0:
                    proper_audio_start_at = media.video_delay
                elif media.start_at > media.video_delay:
                    proper_video_start_at = media.start_at - media.video_delay
                    proper_audio_start_at = media.start_at
                elif media.start_at <= media.video_delay:
                    proper_video_start_at = media.video_delay
                    proper_audio_start_at = media.video_delay
            elif media.start_at >= media.video_duration:
                proper_audio_start_at = media.video_delay
            if media.stop_at == 0:
                proper_video_time = media.video_duration - proper_audio_start_at
                proper_audio_time = media.video_duration - proper_audio_start_at
            elif media.stop_at > media.video_duration:
                proper_video_time = media.video_duration - proper_audio_start_at
                proper_audio_time = media.video_duration - proper_audio_start_at
            elif media.stop_at <= media.video_duration:
                proper_video_time = media.stop_at - proper_audio_start_at
                proper_audio_time = media.stop_at - proper_audio_start_at

        elif media.video_duration > media.audio_duration:
            #logg(2, f'Duration of video ({media.video_duration}) longer than audio ({media.audio_duration}) ({media.src_filename}.{media.src_extension})')
            if media.start_at < media.audio_duration:
                if media.start_at == 0:
                    proper_audio_start_at = media.video_delay
                elif media.start_at > media.video_delay:
                    proper_video_start_at = media.start_at - media.video_delay
                    proper_audio_start_at = media.start_at
                elif media.start_at <= media.video_delay:
                    proper_video_start_at = media.video_delay
                    proper_audio_start_at = media.video_delay
            elif media.start_at >= media.audio_duration:
                proper_audio_start_at = media.video_delay
            if media.stop_at == 0:
                proper_video_time = media.audio_duration - proper_audio_start_at
                proper_audio_time = media.audio_duration - proper_audio_start_at
            elif media.stop_at > media.audio_duration:
                proper_video_time = media.audio_duration - proper_audio_start_at
                proper_audio_time = media.audio_duration - proper_audio_start_at
            elif media.stop_at <= media.audio_duration:
                proper_video_time = media.stop_at - proper_audio_start_at
                proper_audio_time = media.stop_at - proper_audio_start_at

        elif media.video_duration < media.audio_duration:
            #logg(2, f'Duration of audio ({media.audio_duration}) longer than video ({media.video_duration}) ({media.src_filename}.{media.src_extension})')
            if media.start_at < media.video_duration:
                if media.start_at == 0:
                    proper_audio_start_at = media.video_delay
                elif media.start_at > media.video_delay:
                    proper_video_start_at = media.start_at - media.video_delay
                    proper_audio_start_at = media.start_at
                elif media.start_at <= media.video_delay:
                    proper_video_start_at = media.video_delay
                    proper_audio_start_at = media.video_delay
            elif media.start_at >= media.video_duration:
                proper_audio_start_at = media.video_delay
            if media.stop_at == 0:
                proper_video_time = media.video_duration - proper_audio_start_at
                proper_audio_time = media.video_duration - proper_audio_start_at
            elif media.stop_at > media.video_duration:
                proper_video_time = media.video_duration - proper_audio_start_at
                proper_audio_time = media.video_duration - proper_audio_start_at
            elif media.stop_at <= media.video_duration:
                proper_video_time = media.stop_at - proper_audio_start_at
                proper_audio_time = media.stop_at - proper_audio_start_at

    elif media.video_delay == 0 and media.audio_delay != 0:
        #logg(2, f'Delay in audio ({media.audio_delay}) ({media.src_filename}.{media.src_extension})')
        proper_audio_delay = media.audio_delay

        if media.video_duration == media.audio_duration:
            #logg(2, f'Duration of video ({media.video_duration}) and audio ({media.audio_duration}) equal ({media.src_filename}.{media.src_extension})')
            if media.start_at < media.video_duration:
                proper_video_start_at = media.start_at
                proper_audio_start_at = media.start_at
            if media.stop_at == 0:
                proper_video_time = media.video_duration - proper_video_start_at
                proper_audio_time = media.audio_duration - proper_audio_start_at
            elif media.stop_at > media.video_duration:
                proper_video_time = media.video_duration - proper_video_start_at
                proper_audio_time = media.audio_duration - proper_audio_start_at
            elif media.stop_at <= media.video_duration:
                proper_video_time = media.stop_at - proper_video_start_at
                proper_audio_time = media.stop_at - proper_audio_start_at

        elif media.video_duration > media.audio_duration:
            #logg(2, f'Duration of video ({media.video_duration}) longer than audio ({media.audio_duration}) ({media.src_filename}.{media.src_extension})')
            if media.start_at < media.audio_duration:
                proper_video_start_at = media.start_at
                proper_audio_start_at = media.start_at
            if media.stop_at == 0:
                proper_video_time = media.audio_duration - proper_audio_start_at
                proper_audio_time = media.audio_duration - proper_audio_start_at
            elif media.stop_at > media.audio_duration:
                proper_video_time = media.audio_duration - proper_audio_start_at
                proper_audio_time = media.audio_duration - proper_audio_start_at
            elif media.stop_at <= media.audio_duration:
                proper_video_time = media.stop_at - proper_audio_start_at
                proper_audio_time = media.stop_at - proper_audio_start_at

        elif media.video_duration < media.audio_duration:
            #logg(2, f'Duration of audio ({media.audio_duration}) longer than video ({media.video_duration}) ({media.src_filename}.{media.src_extension})')
            if media.start_at < media.video_duration:
                proper_video_start_at = media.start_at
                proper_audio_start_at = media.start_at
            if media.stop_at == 0:
                proper_video_time = media.video_duration - proper_video_start_at
                proper_audio_time = media.video_duration - proper_video_start_at
            elif media.stop_at > media.video_duration:
                proper_video_time = media.video_duration - proper_video_start_at
                proper_audio_time = media.video_duration - proper_video_start_at
            elif media.stop_at <= media.video_duration:
                proper_video_time = media.stop_at - proper_video_start_at
                proper_audio_time = media.stop_at - proper_video_start_at



    media.proper_video_delay = proper_video_delay
    media.proper_audio_delay = proper_audio_delay
    media.proper_video_start_at = proper_video_start_at
    media.proper_video_time = proper_video_time
    media.proper_audio_start_at = proper_audio_start_at
    media.proper_audio_time = proper_audio_time

    # print(f'')
    # print(f'################## after delays_calc')
    # print(f'media.video_duration: {media.video_duration}')
    # print(f'media.audio_duration: {media.audio_duration}')
    # print(f'proper_video_delay: {proper_video_delay}')
    # print(f'proper_audio_delay: {proper_audio_delay}')
    # print(f'proper_video_start_at: {proper_video_start_at}')
    # print(f'proper_video_time: {proper_video_time}')
    # print(f'proper_audio_start_at: {proper_audio_start_at}')
    # print(f'proper_audio_time: {proper_audio_time}')

########################################################################################


def detect_resolution(media):
    logg(6, f'Detecting resolution (input: {media.src_width}x{media.src_height}): {media.src_filename_extension} ...')
    resdet.take_screenshots(media)
    resdet.add_screenshots(media)
    resdet.bar_finder(media)
    resdet.resolution_determiner(media)
    #resdet.cutter(media)
    logg(6, f'Detecting resolution done (real {media.real_width}x{media.real_height}, dst: {media.dst_width}x{media.dst_height}): {media.src_filename_extension}')
    add_to_db(media)
    socketio.emit('media_update', media.as_dict(), broadcast=True)


########################################################################################


def setup_media_dst(media, input):
    current_media_dst = media.media_dst
    initial = False
    if input == 'initial':
        initial = True
        input = 'default'

    if input == 'default':
        if os.path.islink(media.directory_final_meta + media.src_filename + '.mkv'):
            media.media_dst = 'rearchive'
        else:
            media.media_dst = 'archive'
    else:
        media.media_dst = input

    if media.media_dst == 'temporary':
        media.directory_archive = DirConfig.d_arch_temporary
        media.directory_final_meta = None
        if media.video_type == 'movie':
            media.directory_final = DirConfig.fin_temp_movies
        elif media.video_type == 'serie':
            media.directory_final = DirConfig.fin_temp_series + media.base_filename[:-3] + '/'
    elif media.media_dst == 'archive':
        set_directories(media)

    add_to_db(media)
    socketio.emit('media_update', media.as_dict(), broadcast=True)


def setup_video(media, input_stream):
    list_video = json.loads(media.list_video)

    initial = False
    if input_stream == 'initial':
        initial = True
        input_stream = 'default'

    media_changed = None
    good_stream = None
    if input_stream == 'default':
        for item in list_video:
            if item['default'] == 1:
                good_stream = item['index']
        if good_stream == None:
            good_stream = list_video[0]['index']

    if good_stream != None:
        input_stream = good_stream
    
    if media.audio_stream != input_stream:
        media_changed = True

    for item in list_video:
        if item['index'] == int(input_stream):
            media.video_stream = int(input_stream)
            media.video_duration = float(item['duration'])
            media.video_delay = float(item['start_time'])
            media.hdr = item['hdr']
            media.dhdr = item['dhdr']
            media.src_width = int(item['src_width'])
            media.src_height = int(item['src_height'])
            media.video_frame_rate = item['frame_rate']
            media.master_display = item['master_display']
            media.max_cll = item['max_cll']


    if media_changed and media.video_stream != None and initial == False:
        add_to_db(media)
        socketio.emit('media_update', media.as_dict(), broadcast=True)


def setup_audio(media, input_stream):
    list_audio = json.loads(media.list_audio)

    initial = False
    if input_stream == 'initial':
        initial = True
        input_stream = 'default'

    media_changed = None
    good_stream = None
    if input_stream == 'default':
        for item in list_audio:
            if item['default'] == 1:
                good_stream = item['index']
        if good_stream == None:
            good_stream = list_audio[0]['index']

    if good_stream != None:
        input_stream = good_stream
    
    if media.audio_stream != input_stream:
        media_changed = True

    for item in list_audio:
        if item['index'] == int(input_stream):
            media.audio_stream = int(input_stream)
            media.audio_duration = float(item['duration'])
            media.audio_delay = float(item['start_time'])
            media.audio_language = item['language']
            media.audio_channels = item['channels']

            if media.audio_channels == 8:
                media.dst_audio_channels = 6
            if media.audio_channels == 7:
                media.dst_audio_channels = 6
            if media.audio_channels == 6:
                media.dst_audio_channels = 6
            if media.audio_channels == 3:
                media.dst_audio_channels = 2
            if media.audio_channels == 2:
                media.dst_audio_channels = 2
            if media.audio_channels == 1:
                media.dst_audio_channels = 2

    if media_changed and media.audio_stream != None and initial == False:
        add_to_db(media)
        socketio.emit('media_update', media.as_dict(), broadcast=True)


def setup_sub_lang(media, input_stream, lang):
    initial = False
    if input_stream == 'initial':
        initial = True
        input_stream = 'default'

    if lang == 'main':
        list_sub_lang = json.loads(media.list_subtitle_main)
        media_subtitle_stream = media.subtitle_stream_main
    if lang == 'additional':
        list_sub_lang = json.loads(media.list_subtitle_additional)
        media_subtitle_stream = media.subtitle_stream_additional
    
    media_changed = None

    if input_stream == 'default':
        if len(list_sub_lang) > 0:
            good_stream = None
            for idx in reversed(range(len(list_sub_lang))):
                if not 'SDH' in list_sub_lang[idx]['title'] and list_sub_lang[idx]['forced'] != 1:
                    good_stream = list_sub_lang[idx]['index']
                if good_stream == None and idx == 0:
                    good_stream = list_sub_lang[0]['index']

            if good_stream != None:
                input_stream = good_stream

    if media_subtitle_stream != input_stream:
        media_changed = True

    if input_stream != 'default':
        media_subtitle_stream = input_stream
        if lang == 'main':
            media.subtitle_stream_main = media_subtitle_stream
        if lang == 'additional':
            media.subtitle_stream_additional = media_subtitle_stream

    if media_changed and media_subtitle_stream != None and initial == False:
        add_to_db(media)
        socketio.emit('media_update', media.as_dict(), broadcast=True)


########################################################################################


def file_check(media):
    there_is_change = False

    subtitle_main_file = media.directory + media.src_filename + '.srt'
    if os.path.isfile(subtitle_main_file):
        if media.subtitle_main_state == None or media.subtitle_main_state == 'not_downloaded' or media.subtitle_main_state == 'not_extracted':
            media.subtitle_main_state = 'exist'
            there_is_change = True
            usubtitles.subtitle_process(media, 'main')
        elif media.subtitle_main_state == 'extracting' or media.subtitle_main_state == 'downloading':
            media.subtitle_main_state = None
            there_is_change = True
            os.remove(subtitle_main_file)
        elif media.subtitle_main_state == 'extracted' or media.subtitle_main_state == 'downloaded' or media.subtitle_main_state == 'exist':
            usubtitles.subtitle_process(media, 'main')
    else:
        media.subtitle_main_state = None
        there_is_change = True

    subtitle_additional_file = media.directory + media.src_filename + '.' + OtherConfig.lang_additional + '.srt'
    if os.path.isfile(subtitle_additional_file):
        if media.subtitle_additional_state == None or media.subtitle_additional_state == 'not_downloaded' or media.subtitle_additional_state == 'not_extracted':
            media.subtitle_additional_state = 'exist'
            there_is_change = True
            usubtitles.subtitle_process(media, 'additional')
        elif media.subtitle_additional_state == 'extracting' or media.subtitle_additional_state == 'downloading':
            media.subtitle_additional_state = None
            there_is_change = True
            os.remove(subtitle_additional_file)
        elif media.subtitle_additional_state == 'extracted' or media.subtitle_additional_state == 'downloaded' or media.subtitle_additional_state == 'exist':
            usubtitles.subtitle_process(media, 'additional')
    else:
        media.subtitle_additional_state = None
        there_is_change = True

    if media.extract_audio_state != 'extracted':
        media.extract_audio_state = 'not_extracted'
        there_is_change = True

    convert_video_file = media.directory_temp + media.dst_filename + '.h265'
    if os.path.isfile(convert_video_file):
        if not media.convert_video_state == 'converted':
            media.convert_video_state = 'not_converted'
            there_is_change = True
    else:
        media.convert_video_state = None
        there_is_change = True

    if media.convert_audio_state != 'converted':
        media.convert_audio_state = 'not_converted'
        there_is_change = True

    if media.convert_audio_voiceover_state != 'converted':
        media.convert_audio_voiceover_state = 'not_converted'
        there_is_change = True
    
    if media.create_voiceover_state != 'created':
        media.create_voiceover_state = 'not_created'
        there_is_change = True
    
    if media.extract_hdrplus_state != 'extracted':
        media.extract_hdrplus_state = 'not_extracted'
        there_is_change = True

    if there_is_change == True:
        add_to_db(media)
        socketio.emit('media_update', media.as_dict())


########################################################################################


def set_start_stop(media, start_at, stop_at):
    list_start_at = start_at.split(':')
    for index, i in enumerate(list_start_at):
        list_start_at[index] = float(list_start_at[index] )

    start_at_seconds = list_start_at[-1]
    if len(list_start_at) > 1:
        start_at_seconds = start_at_seconds + (list_start_at[-2] * 60)
    if len(list_start_at) > 2:
        start_at_seconds = start_at_seconds + (list_start_at[-3] * 3600)

    list_stop_at = stop_at.split(':')
    for index, i in enumerate(list_stop_at):
        list_stop_at[index] = float(list_stop_at[index] )

    stop_at_seconds = list_stop_at[-1]
    if len(list_stop_at) > 1:
        stop_at_seconds = stop_at_seconds + (list_stop_at[-2] * 60)
    if len(list_stop_at) > 2:
        stop_at_seconds = stop_at_seconds + (list_stop_at[-3] * 3600)

    media.start_at = start_at_seconds
    media.stop_at = stop_at_seconds
    delays_calc(media)
    usubtitles.subtitle_process(media, 'main')
    usubtitles.subtitle_process(media, 'additional')
    add_to_db(media)
    socketio.emit('media_update', media.as_dict(), broadcast=True)


def exec_path(exec_type):
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    
    if exec_type == 'ffmpeg':
        if DirConfig.d_ffmpeg == '':
            return 'ffmpeg'
        else:
            return DirConfig.d_ffmpeg

    if exec_type == 'ffprobe':
        if DirConfig.d_ffprobe == '':
            return 'ffprobe'
        else:
            return DirConfig.d_ffprobe
    
    if exec_type == 'mediainfo':
        if DirConfig.d_mediainfo == '':
            return 'mediainfo'
        else:
            return DirConfig.d_mediainfo

    if exec_type == 'mkvmerge':
        if DirConfig.d_mkvmerge == '':
            return 'mkvmerge'
        else:
            return DirConfig.d_mkvmerge

    if exec_type == 'hdr10plus_tool':
        if DirConfig.d_hdr10plus_tool == '':
            return 'hdr10plus_tool'
        else:
            return DirConfig.d_hdr10plus_tool

