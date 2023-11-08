import errno
import os
import pty
import select
import subprocess, shlex
import re
import threading
import time
import datetime
import shutil
import sys

from videotools import socketio
from videotools import utils, usubtitles, utts
from videotools.config import DirConfig, OtherConfig
from videotools.logger import logg
from videotools.dbing import add_to_db, delete_from_db

from pydub import AudioSegment, effects
from google.cloud import texttospeech
from io import BytesIO

########################################################################################

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = OtherConfig.google_credentials_file
priority_io_move_files = 1
priority_io_detect_resolution = 2
priority_io_extract_subtitles = 3
priority_io_extract_hdrplus = 4
priority_io_extract_audio = 5
priority_io_mux = 6

download_time_table = []

########################################################################################


class ObjJobList():
    jobs = []
    instant_threads = []
    queued_video_convert_threads = []
    queued_audio_convert_threads = []
    queued_audio_voiceover_convert_threads = []
    queued_io_threads = []
    queued_download_threads = []
    queued_create_voiceover_threads = []
    converting_audio = 0
    converting_video = 0

    def create_job(self, media, operation_type, command):
        #print(f'### create_job')
        for job in self.jobs:
            if job.name == media.src_filename_extension and job.operation_type == operation_type:
                #print(f'### create_job ### job exists')
                return job
        if operation_type == 'download_voiceover':
            job = JobDownload(media, operation_type, '')
        elif operation_type == 'extract_hdrplus':
            job = JobExtractHDRPlus(media, operation_type, command)
        elif operation_type == 'extract_subtitles':
            job = JobExtractSubtitles(media, operation_type, command)
        elif operation_type == 'create_voiceover':
            job = JobCreateVoiceover(media, operation_type, '')
        elif operation_type == 'move_files':
            job = JobMoveFiles(media, operation_type, '')
        elif operation_type == 'mux':
            job = JobMux(media, operation_type, command)
        else:
            job = Job(media, operation_type, command)
        self.jobs.append(job)
        return job

    def create_thread(self, media, operation_type, job):
        #print(f'### create_thread')
        if operation_type == 'detect_resolution':
            thread = threading.Thread(target=utils.detect_resolution, args=(media, ), name=media.src_filename_extension, daemon=True)
        else:
            thread = threading.Thread(target=job.run, args=(), name=media.src_filename_extension, daemon=True)
        return thread

    def instant_do(self, media, operation_type):
        if operation_type == 'detect_resolution':
            #print(f'### start_job ### detect_resolution')
            job = self.create_job(media, operation_type, '')
        else:
            #print(f'### start_job ### else')
            command = make_command(media, operation_type)
            job = self.create_job(media, operation_type, command)
        thread = self.create_thread(media, operation_type, job)

        self.instant_threads.append(thread)
        #print(f'### start_job ### pre started')
        thread.start()
        #print(f'### start_job ### started')
        self.job_state_update(thread.name, operation_type)
        thread.join()
        self.job_state_update(thread.name, operation_type)

        self.instant_threads.remove(thread)
        self.jobs.remove(job)

    def stop_job(self, media, operation_type):
        #print(f'### stop_job')
        for job in self.jobs:
            if job.name == media.src_filename_extension and job.operation_type == operation_type:
                job.terminate()

    def remove_job(self, name, operation_type):
        #print(f'### remove_job')
        for job in self.jobs:
            if job.name == name and job.operation_type == operation_type:
                self.jobs.remove(job)

    def job_state_update(self, name, operation_type):
        #print(f'### job_state_update ### name = {name}, operation_type = {operation_type}')
        for job in self.jobs:
            if job.name == name and job.operation_type == operation_type:

                if operation_type == 'convert_video':
                    if job.started == True and job.operation_finished == False:
                        job.media.convert_video_state = 'converting'
                        logg(3, f'Converting video ({job.media.src_filename_extension})')
                    if job.interrupted == False:
                        job.media.convert_video_state = 'converted'
                        logg(3, f'Converting video done ({job.media.src_filename_extension})')
                    if job.interrupted == True:
                        job.media.convert_video_state = 'error'
                        logg(3, f'ERROR converting video ({job.media.src_filename_extension})')

                if operation_type == 'convert_audio':
                    if job.started == True and job.operation_finished == False:
                        job.media.convert_audio_state = 'converting'
                        logg(3, f'Converting audio ({job.media.src_filename_extension})')
                    if job.interrupted == False:
                        job.media.convert_audio_state = 'converted'
                        logg(3, f'Converting audio done ({job.media.src_filename_extension})')
                    if job.interrupted == True:
                        job.media.convert_audio_state = 'error'
                        logg(3, f'ERROR converting audio ({job.media.src_filename_extension})')
                
                if operation_type == 'convert_voiceover_audio':
                    if job.started == True and job.operation_finished == False:
                        job.media.convert_audio_voiceover_state = 'converting'
                        logg(3, f'Converting voiceover audio ({job.media.src_filename_extension})')
                    if job.interrupted == False:
                        job.media.convert_audio_voiceover_state = 'converted'
                        logg(3, f'Converting voiceover audio done ({job.media.src_filename_extension})')
                    if job.interrupted == True:
                        job.media.convert_audio_voiceover_state = 'error'
                        logg(3, f'ERROR converting voiceover audio ({job.media.src_filename_extension})')
                
                if operation_type == 'extract_hdrplus':
                    if job.started == True and job.operation_finished == False:
                        job.media.extract_hdrplus_state = 'extracting'
                        logg(3, f'Extracting HDR+ data ({job.media.src_filename_extension})')
                    if job.interrupted == False:
                        job.media.extract_hdrplus_state = 'extracted'
                        logg(3, f'Extracting HDR+ data done ({job.media.src_filename_extension})')
                    if job.interrupted == True:
                        job.media.extract_hdrplus_state = 'error'
                        logg(3, f'ERROR extracting HDR+ data done ({job.media.src_filename_extension})')
                
                if operation_type == 'extract_audio':
                    if job.started == True and job.operation_finished == False:
                        job.media.extract_audio_state = 'extracting'
                        logg(3, f'Extracting audio ({job.media.src_filename_extension})')
                    if job.interrupted == False:
                        job.media.extract_audio_state = 'extracted'
                        logg(3, f'Extracting audio done ({job.media.src_filename_extension})')
                    if job.interrupted == True:
                        job.media.extract_audio_state = 'error'
                        logg(3, f'ERROR extracting audio ({job.media.src_filename_extension})')
                
                if operation_type == 'extract_subtitles':
                    if job.started == True and job.operation_finished == False:
                        if job.media.subtitle_stream_main != None: job.media.subtitle_main_state = 'extracting'
                        if job.media.subtitle_stream_additional != None: job.media.subtitle_additional_state = 'extracting'
                        logg(3, f'Extracting subtitles ({job.media.src_filename_extension})')
                    if job.interrupted == False:
                        if job.media.subtitle_stream_main != None: job.media.subtitle_main_state = 'extracted'
                        if job.media.subtitle_stream_additional != None: job.media.subtitle_additional_state = 'extracted'
                        logg(3, f'Extracting subtitles done ({job.media.src_filename_extension})')
                    if job.interrupted == True:
                        if job.media.subtitle_stream_main != None: job.media.subtitle_main_state = 'error'
                        if job.media.subtitle_stream_additional != None: job.media.subtitle_additional_state = 'error'
                        logg(3, f'ERROR extracting subtitles ({job.media.src_filename_extension})')
                
                if operation_type == 'download_voiceover':
                    if job.started == True and job.operation_finished == False:
                        job.media.download_voiceover_state = 'downloading'
                        logg(3, f'Downloading voiceover ({job.media.src_filename_extension})')
                    if job.interrupted == False:
                        job.media.download_voiceover_state = 'downloaded'
                        logg(3, f'Downloading voiceover done ({job.media.src_filename_extension})')
                    if job.interrupted == True:
                        job.media.download_voiceover_state = 'error'
                        logg(3, f'ERROR downloading voiceover ({job.media.src_filename_extension})')
                
                if operation_type == 'create_voiceover':
                    if job.started == True and job.operation_finished == False:
                        job.media.create_voiceover_state = 'creating'
                        logg(3, f'Creating voiceover ({job.media.src_filename_extension})')
                    if job.interrupted == False:
                        job.media.create_voiceover_state = 'created'
                        logg(3, f'Creating voiceover done ({job.media.src_filename_extension})')
                    if job.interrupted == True:
                        job.media.create_voiceover_state = 'error'
                        logg(3, f'ERROR creating voiceover ({job.media.src_filename_extension})')
                
                if operation_type == 'mux':
                    if job.started == True and job.operation_finished == False:
                        job.media.mux_state = 'muxing'
                        logg(3, f'Muxing ({job.media.src_filename_extension})')
                    if job.interrupted == False:
                        job.media.mux_state = 'muxed'
                        logg(3, f'Muxing done ({job.media.src_filename_extension})')
                    if job.interrupted == True:
                        job.media.mux_state = 'error'
                        logg(3, f'ERROR muxing ({job.media.src_filename_extension})')
                
                if operation_type == 'move_files':
                    if job.started == True and job.operation_finished == False:
                        job.media.move_files_state = 'moving'
                        logg(3, f'Moving files ({job.media.src_filename_extension})')
                    if job.interrupted == False:
                        job.media.move_files_state = 'moved'
                        logg(3, f'Moving files done ({job.media.src_filename_extension})')
                    if job.interrupted == True:
                        job.media.move_files_state = 'error'
                        logg(3, f'ERROR moving files ({job.media.src_filename_extension})')


                add_to_db(job.media)
                socketio.emit('media_update', job.media.as_dict(), broadcast=True)


class Job():
    def __init__(self, media, operation_type, command):
        self.kill = threading.Event()
        self.media = media
        self.operation_type = operation_type
        self.command = command
        self.name = media.src_filename_extension
        self.interrupted = None
        self.started = False
        self.operation_finished = False

    def terminate(self):
        print(f'### terminating: {self.operation_type}')
        self.kill.set()
        
    def return_src_file_name_extension(self):
        return self.media.src_filename_extension

    def run(self):
        self.started = True
        out_r, out_w = pty.openpty()
        err_r, err_w = pty.openpty()
        proc = subprocess.Popen(shlex.split(self.command), stdout=out_w, stderr=err_w)
        os.close(out_w)
        os.close(err_w)

        log_file_path = f'{self.media.directory_temp}{self.media.dst_filename}.ffmpeg_{self.operation_type}.log'
        open(log_file_path, 'w').close

        log_file = open(log_file_path, 'a')
        fds = {OutStream(out_r), OutStream(err_r)}
        while not self.kill.is_set():
            if fds:
                time_to_sleep = 0
                rlist, _, _ = select.select(fds, [], [])
                for f in rlist:
                    lines, readable = f.read_lines()

                    for single_line in lines:
                        if single_line[:4] == 'size' or single_line[:5] == 'frame':
                            log_file.write(f'\n{single_line}')
                        else:
                            log_file.write(single_line)

                    if len(lines) != 0:
                        analyze_result = output_analyze(self.media, self.operation_type, lines[-1], self.media.proper_video_time)
                        if analyze_result is not None:
                            time_to_sleep = 1
                        if analyze_result == 'error':
                            print(f'### ERROR when:\n\n{self.command}\n')
                            fds.remove(f)
                            self.terminate()
                            self.operation_finished = False
                    if not readable:

                        fds.remove(f)
                        self.terminate()
                        self.operation_finished = True
        log_file.close()
        proc.kill()

        if self.kill.is_set() and self.operation_finished == False:
            self.interrupted = True
        else:
            self.interrupted = False
            self.after_job_done()
    
    def after_job_done(self):
        pass


class JobExtractHDRPlus(Job):
    def run(self):
        self.started = True

        subprocess.run(self.command, shell=True, check=True, stderr=subprocess.DEVNULL)

        self.terminate()
        self.operation_finished = True

        if self.kill.is_set() and self.operation_finished == False:
            self.interrupted = True
        else:
            self.interrupted = False


class JobExtractSubtitles(Job):
    def after_job_done(self):
        usubtitles.subtitle_process(self.media, 'main')
        usubtitles.subtitle_process(self.media, 'additional')


class JobDownload(Job):
    def run(self):
        self.started = True

        this_month_bytes, this_month_chars = update_download_bytes('get')
        tts_sentences_gathered = 0
        tts_sentences_sum = 0
        tts_bytes_sum = 0
        tts_chars_sum = 0
        tts_bytes_gathered = 0
        tts_chars_gathered = 0
        tts_bytes_downloaded = 0
        tts_chars_downloaded = 0

        for item in self.media.tts_list:
            tts_bytes_sum += len(item[4].encode('utf-8'))
            tts_chars_sum += len(item[4])
            tts_sentences_sum += 1

        # print(f'\n### tts_sentences_sum: {tts_sentences_sum}')
        # print(f'### tts_bytes_sum: {tts_bytes_sum}')
        # print(f'### tts_chars_sum: {tts_chars_sum}')
        # print(f'### this_month_bytes: {this_month_bytes}')
        # print(f'### this_month_chars: {this_month_chars}\n')

        google_tts_used_curr = ( 100 * (this_month_bytes) ) / OtherConfig.bytes_download_limit
        logg(2, f'Google cloud TTS used: {google_tts_used_curr:.2f} %')

        if tts_bytes_sum == 0:
            self.terminate()
            self.operation_finished = True
            logg(2, f'Empty TTS? ({self.media.title})')

        if not os.path.isdir(self.media.directory_tts):
            os.makedirs(self.media.directory_tts)

        logg(2, f'Listing all voiceovers from archives ({self.media.title})')
        media_with_tts_list = utts.get_all_tts(self.media, arch_movies = True, arch_series = True, arch_temporary = True, temp_directory = True)
        copied_from_arch = []
        copied_from_arch_bytes = 0
        copied_from_arch_chars = 0
        copied_from_arch_sentences = 0
        download_start_time = time.time()
        download_start_time_copy = time.time()
        logg(2, f'Copying available voiceovers from archives ({self.media.title})')
        for index, current_tts in enumerate(self.media.tts_list):
            sentence_found = False
            for arch_media in media_with_tts_list:
                if sentence_found == True:
                    break
                for arch_tts in arch_media['tts_list']:
                    if current_tts[4] == arch_tts[4]:
                    #if current_tts[4].lower() == arch_tts[4].lower():
                        full_filename_arch = f'{arch_media["vo_directory_path"]}{arch_tts[0]}_{arch_tts[2]}.mp3'
                        full_filename_current = f'{self.media.directory_tts}{current_tts[0]}_{current_tts[2]}.mp3'
                        if not os.path.isfile(full_filename_current):
                            shutil.copy(full_filename_arch, full_filename_current)
                        copied_from_arch.append(current_tts)
                        copied_from_arch_bytes = copied_from_arch_bytes + len(current_tts[4].encode("utf-8"))
                        copied_from_arch_chars = copied_from_arch_chars + len(current_tts[4])
                        copied_from_arch_sentences += 1
                        sentence_found = True

                        download_current_time = time.time()
                        tts_bytes_gathered += len(current_tts[4].encode('utf-8'))
                        tts_chars_gathered += len(current_tts[4])
                        percentage = (100 * tts_bytes_gathered) / tts_bytes_sum
                        download_run_time = download_current_time - download_start_time
                        eta = ((download_run_time * 100) / percentage) - download_run_time
                        print(f'### {self.operation_type} ### {self.media.src_filename_extension} ### percentage {format(percentage, ".2f") if percentage < 100 else str(format(percentage, ".0f"))}, eta {time.strftime("%H:%M:%S", time.gmtime(float(eta)))}')
                        socketio.emit('process_update', [self.operation_type,
                                            self.media.src_filename_extension, format(percentage, '.2f') if percentage < 100 else str(format(percentage, ".0f")),
                                            time.strftime("%H:%M:%S", time.gmtime(float(eta)))])
                        break

            if tts_bytes_gathered + tts_bytes_downloaded == tts_bytes_sum and self.operation_finished == False:
                self.terminate()
                self.operation_finished = True

        savings_from_arch_bytes = ( 100 * copied_from_arch_bytes ) / tts_bytes_sum
        savings_from_arch_chars = ( 100 * copied_from_arch_chars ) / tts_chars_sum
        savings_from_arch_sentences = ( 100 * copied_from_arch_sentences ) / tts_sentences_sum

        to_download_tts_list = []
        for current_tts in self.media.tts_list:
            if current_tts not in copied_from_arch:
                to_download_tts_list.append(current_tts)

        ######################################################################################################

        copied_from_current_bytes = 0
        copied_from_current_chars = 0
        copied_from_current_sentences = 0
        process_tts_list = []
        for index, to_download_tts in enumerate(to_download_tts_list):
            sentence_found = False
            for process_tts in process_tts_list:
                if process_tts[4].lower() == to_download_tts[4].lower():
                    copied_from_current_bytes = copied_from_current_bytes + len(process_tts[4].encode("utf-8"))
                    copied_from_current_chars = copied_from_current_chars + len(process_tts[4])
                    copied_from_current_sentences += 1
                    sentence_found = True
                    break
            process_tts_list.append(to_download_tts)

        savings_from_current_bytes = ( 100 * copied_from_current_bytes ) / tts_bytes_sum
        savings_from_current_chars = ( 100 * copied_from_current_chars ) / tts_chars_sum
        savings_from_current_sentences = ( 100 * copied_from_current_sentences ) / tts_sentences_sum

        ###################################################################################################### download

        logg(2, f'Download new voiceovers ({self.media.title})')
        process_tts_list = []
        while not self.kill.is_set():
            for index, to_download_tts in enumerate(to_download_tts_list):
                sentence_found = False
                for process_tts in process_tts_list:
                    if process_tts[4].lower() == to_download_tts[4].lower():
                        full_filename_src = f'{self.media.directory_tts}{process_tts[0]}_{process_tts[2]}.mp3'
                        full_filename_dst = f'{self.media.directory_tts}{to_download_tts[0]}_{to_download_tts[2]}.mp3'
                        if not os.path.isfile(full_filename_dst):
                            shutil.copy(full_filename_src, full_filename_dst)
                        sentence_found = True
                        tts_bytes_gathered += len(process_tts[4].encode('utf-8'))
                        tts_chars_gathered += len(process_tts[4])
                        break
                if sentence_found == False:
                    if not os.path.isfile(self.media.directory_tts + f'{to_download_tts[0]}_{to_download_tts[2]}.mp3'):
                        if this_month_bytes + tts_bytes_downloaded + len(to_download_tts[4].encode('utf-8')) < OtherConfig.bytes_download_limit:
                            download_result = download_voiceover(self.media.directory_tts, f'{to_download_tts[0]}_{to_download_tts[2]}.mp3', to_download_tts[4])
                            update_download_bytes('add', len(to_download_tts[4].encode("utf-8")), len(to_download_tts[4]))
                            tts_bytes_gathered += len(to_download_tts[4].encode('utf-8'))
                            tts_bytes_downloaded += len(to_download_tts[4].encode('utf-8'))
                            tts_chars_gathered += len(to_download_tts[4])
                            tts_chars_downloaded += len(to_download_tts[4])
                        else:
                            logg(2, f'Monthly limit of free google tts reached ({this_month_bytes + tts_bytes_downloaded} of {OtherConfig.bytes_download_limit} bytes)')
                            self.terminate()
                            self.operation_finished = True
                            break
                    else:
                        tts_bytes_gathered += len(to_download_tts[4].encode('utf-8'))
                        tts_chars_gathered += len(to_download_tts[4])

                download_current_time = time.time()
                percentage = (100 * tts_bytes_gathered) / tts_bytes_sum
                download_run_time = download_current_time - download_start_time
                eta = ((download_run_time * 100) / percentage) - download_run_time
                print(f'### {self.operation_type} ### {self.media.src_filename_extension} ### percentage {format(percentage, ".2f") if percentage < 100 else str(format(percentage, ".0f"))}, eta {time.strftime("%H:%M:%S", time.gmtime(float(eta)))}')
                socketio.emit('process_update', [self.operation_type,
                                    self.media.src_filename_extension, format(percentage, '.2f') if percentage < 100 else str(format(percentage, ".0f")),
                                    time.strftime("%H:%M:%S", time.gmtime(float(eta)))])

                process_tts_list.append(to_download_tts)

                if index + 1 == len(to_download_tts_list):
                        self.terminate()
                        self.operation_finished = True

        logg(2, f'Downloaded voiceovers: {tts_bytes_downloaded} bytes, copied voiceovers: {copied_from_arch_bytes + copied_from_current_bytes} of {tts_bytes_sum} bytes ({savings_from_arch_bytes + savings_from_current_bytes:.2f} %) ({self.media.title})')

        google_tts_used_curr = ( 100 * (this_month_bytes + tts_bytes_downloaded) ) / OtherConfig.bytes_download_limit
        logg(2, f'Google cloud TTS used: {google_tts_used_curr:.2f} %')

        ######################################################################################################

        if self.kill.is_set() and self.operation_finished == False:
            self.interrupted = True
        else:
            self.interrupted = False


class JobCreateVoiceover(Job):
    def run(self):
        self.started = True

        create_start_time = time.time()

        sentences_sum = len(self.media.tts_list)
        sentences_processed = 0

        logg(3, f'Reading wav files ({self.media.src_filename_extension})')
        with open(self.media.directory_temp + self.media.dst_filename + '.FL.wav', 'rb') as file_org_audio_FL:
            org_audio_FL = AudioSegment.from_wav(file_org_audio_FL)
        with open(self.media.directory_temp + self.media.dst_filename + '.FR.wav', 'rb') as file_org_audio_FR:
            org_audio_FR = AudioSegment.from_wav(file_org_audio_FR)
        if self.media.dst_audio_channels == 6:
            with open(self.media.directory_temp + self.media.dst_filename + '.FC.wav', 'rb') as file_org_audio_FC:
                org_audio_FC = AudioSegment.from_wav(file_org_audio_FC)

        tts_list_current = self.media.tts_list
        current_time_position = 0
        max_sentence_gap_long = OtherConfig.vo_max_sentence_gap_long
        max_sentence_gap_short = int(OtherConfig.vo_max_sentence_gap_long * OtherConfig.vo_max_sentence_gap_short)
        final_track_FLFR = AudioSegment.silent(duration=0, frame_rate=24000)
        final_track_FC = AudioSegment.silent(duration=0, frame_rate=24000)

        logg(3, f'Adding voiceover audio ({self.media.src_filename_extension})')
        while not self.kill.is_set():
            if len(tts_list_current) > 0:
                current_pos = tts_list_current.pop(0)
                proper_list = [current_pos[0], [current_pos[3]]]
                while True:
                    if len(tts_list_current) > 0:
                        if tts_list_current[0][0] == current_pos[0]:
                            proper_list[1].append(tts_list_current[0][3])
                            tts_list_current.remove(tts_list_current[0])
                            sentences_processed += 1
                        else:
                            break
                    else:
                        break

                time_start = datetime.datetime.strptime(current_pos[0], '%H.%M.%S.%f') - datetime.datetime.strptime('00.00.00.000', '%H.%M.%S.%f')
                max_time = 0
                if len(tts_list_current) > 0:
                    next_pos = tts_list_current[0]
                    time_stop = datetime.datetime.strptime(next_pos[0], '%H.%M.%S.%f') - datetime.datetime.strptime('00.00.00.000', '%H.%M.%S.%f')
                    max_time_for_sentence = time_stop - time_start
                    max_time_for_sentence = (int(max_time_for_sentence.total_seconds() * 1000))

                from_previous_to_current = (int(time_start.total_seconds() * 1000)) - current_time_position
                if from_previous_to_current < 0:
                    max_time_for_sentence = max_time_for_sentence + from_previous_to_current

                empty_segment = AudioSegment.silent(duration=from_previous_to_current, frame_rate=24000)
                sentence_audio = AudioSegment.silent(duration=0, frame_rate=24000)
                sentences_gap_long = AudioSegment.silent(duration=max_sentence_gap_long, frame_rate=24000)
                sentences_gap_short = AudioSegment.silent(duration=max_sentence_gap_short, frame_rate=24000)


                sentence_lenght_adjusted = False
                while sentence_lenght_adjusted == False:
                    while True:
                        for index, gap_type in enumerate(proper_list[1]):
                            sentence_filename = self.media.directory_tts + proper_list[0] + '_' + str(index) + '.mp3'

                            if os.path.isfile(sentence_filename):
                                with open(sentence_filename, 'rb') as file_sentence_filename:
                                    if index == 0:
                                        try:
                                            if gap_type == 'short':
                                                sentence_audio = AudioSegment.from_mp3(sentence_filename) + sentences_gap_short
                                            else:
                                                sentence_audio = AudioSegment.from_mp3(sentence_filename) + sentences_gap_long
                                        except:
                                            print(f'######### ERROR READING AUDIO: {sentence_filename}')
                                            self.terminate()
                                            self.operation_finished = False
                                    if index != 0:
                                        try:
                                            if gap_type == 'short':
                                                sentence_audio = sentence_audio + AudioSegment.from_mp3(sentence_filename) + sentences_gap_short
                                            else:
                                                sentence_audio = sentence_audio + AudioSegment.from_mp3(sentence_filename) + sentences_gap_long
                                        except:
                                            print(f'######### ERROR READING AUDIO: {sentence_filename}')
                                            self.terminate()
                                            self.operation_finished = False
                            else:
                                print(f'######### file does not exists: {sentence_filename}')
                                self.terminate()
                                self.operation_finished = False

                        if len(sentence_audio) <= max_time_for_sentence or len(tts_list_current) == 0:
                            sentence_lenght_adjusted = True
                            break
                        elif OtherConfig.vo_max_sentence_gap_long * OtherConfig.vo_min_sentence_gap_long > len(sentences_gap_long[:-(OtherConfig.vo_max_sentence_gap_long * OtherConfig.vo_step_down_sentences_gap)]):
                            break
                        elif len(sentences_gap_long) > OtherConfig.vo_max_sentence_gap_long * OtherConfig.vo_min_sentence_gap_long:
                            sentences_gap_long = sentences_gap_long[:-(OtherConfig.vo_max_sentence_gap_long * OtherConfig.vo_step_down_sentences_gap)]
                            sentences_gap_short = sentences_gap_short[:-(OtherConfig.vo_max_sentence_gap_long * OtherConfig.vo_max_sentence_gap_short * OtherConfig.vo_step_down_sentences_gap)]
                        else:
                            break

                    if len(sentence_audio) > max_time_for_sentence and len(tts_list_current) != 0:
                        tmp_sentence_audio = sentence_audio
                        index = 1
                        while(True):
                            num = index / 100 + 1
                            tmp_sentence_audio = effects.speedup(sentence_audio, playback_speed = num)
                            if len(tmp_sentence_audio) <= max_time_for_sentence or num >= OtherConfig.vo_max_playback_speed:
                                sentence_audio = effects.speedup(sentence_audio, playback_speed = num)
                                break
                            index += 1

                        sentence_lenght_adjusted = True
                    else:
                        sentence_lenght_adjusted = True

                time_add_vol_check = 300
                time_start_sec = int(time_start.total_seconds() * 1000) - time_add_vol_check
                if time_start_sec < 0:
                    time_start_sec = 0
                time_stop_sec = time_start_sec + len(sentence_audio) + (time_add_vol_check * 2)
                
                sentence_FL = org_audio_FL[time_start_sec:time_stop_sec]
                sentence_FR = org_audio_FR[time_start_sec:time_stop_sec]
                if self.media.dst_audio_channels == 6:
                    sentence_FC = org_audio_FC[time_start_sec:time_stop_sec]

                dBFS_sentence_FL = sentence_FL.dBFS
                dBFS_sentence_FR = sentence_FR.dBFS
                dBFS_sentence_FLFR = (dBFS_sentence_FL + dBFS_sentence_FR) / 2
                if self.media.dst_audio_channels == 6:
                    dBFS_sentence_FC = sentence_FC.dBFS
                dBFS_sentence_audio = sentence_audio.dBFS

                if dBFS_sentence_FLFR == -float('Inf'): dBFS_sentence_FLFR = -90.30899869919435
                if self.media.dst_audio_channels == 6:
                    if dBFS_sentence_FC == -float('Inf'): dBFS_sentence_FC = -90.30899869919435

                channels_2_up = 0.7
                dBFS_calc_FLFR = dBFS_sentence_FLFR - (dBFS_sentence_FLFR / OtherConfig.vo_audio_volume_param1) - dBFS_sentence_audio
                if self.media.dst_audio_channels == 6:
                    sentence_audio_gain_FLFR = dBFS_calc_FLFR + OtherConfig.vo_audio_volume_param2 
                elif self.media.dst_audio_channels == 2:
                    sentence_audio_gain_FLFR = dBFS_calc_FLFR + (OtherConfig.vo_audio_volume_param2 * channels_2_up)

                if self.media.dst_audio_channels == 6:
                    dBFS_calc_FC = dBFS_sentence_FC - (dBFS_sentence_FC / OtherConfig.vo_audio_volume_param1) - dBFS_sentence_audio
                    sentence_audio_gain_FC = dBFS_calc_FC + OtherConfig.vo_audio_volume_param2 

                if self.media.dst_audio_channels == 6:
                    while (dBFS_sentence_audio + sentence_audio_gain_FLFR) < OtherConfig.vo_audio_volume_min:
                        sentence_audio_gain_FLFR = sentence_audio_gain_FLFR + 0.01
                elif self.media.dst_audio_channels == 2:
                    while (dBFS_sentence_audio + sentence_audio_gain_FLFR) < (OtherConfig.vo_audio_volume_min * channels_2_up):
                        sentence_audio_gain_FLFR = sentence_audio_gain_FLFR + 0.01

                if self.media.dst_audio_channels == 6:
                    while (dBFS_sentence_audio + sentence_audio_gain_FC) < OtherConfig.vo_audio_volume_min:
                        sentence_audio_gain_FC = sentence_audio_gain_FC + 0.01

                sentence_audio_FLFR = sentence_audio.apply_gain(sentence_audio_gain_FLFR)
                if self.media.dst_audio_channels == 6:
                    sentence_audio_FC = sentence_audio.apply_gain(sentence_audio_gain_FC)

                # if self.media.dst_audio_channels == 6:
                #     print(f'### volumes levels ### {current_pos[0]} ### FLFR: {format(dBFS_sentence_FLFR, ".1f")}  VO FLFR: {format(sentence_audio_FLFR.dBFS, ".1f")} ### FC: {format(dBFS_sentence_FC, ".1f")}  VO FC: {format(sentence_audio_FC.dBFS, ".1f")}')
                # else:
                #     print(f'### volumes levels - FLFR: {dBFS_sentence_FLFR}, VO FLFR: {sentence_audio_FLFR.dBFS}')

                final_track_FLFR = final_track_FLFR + empty_segment + (sentence_audio_FLFR)
                if self.media.dst_audio_channels == 6:
                    final_track_FC = final_track_FC + empty_segment + (sentence_audio_FC)

                current_time_position = len(final_track_FLFR)
                if len(tts_list_current) == 0:
                    last_empty_segm_len = len(org_audio_FL) - current_time_position
                    last_empty_segm = AudioSegment.silent(duration=last_empty_segm_len, frame_rate=24000)
                    final_track_FLFR = final_track_FLFR + last_empty_segm
                    if self.media.dst_audio_channels == 6:
                        final_track_FC = final_track_FC + last_empty_segm

                sentences_processed += 1

                create_current_time = time.time()
                percentage = (100 * sentences_processed) / sentences_sum
                create_run_time = create_current_time - create_start_time
                eta = ((create_run_time * 100) / percentage) - create_run_time
                print(f'### {self.operation_type} ### {self.media.src_filename_extension} ### percentage {format(percentage, ".2f") if percentage < 100 else str(format(percentage, ".0f"))}, eta {time.strftime("%H:%M:%S", time.gmtime(float(eta)))}')
                socketio.emit('process_update', [self.operation_type,
                                    self.media.src_filename_extension, format(percentage, '.2f') if percentage < 100 else str(format(percentage, ".0f")),
                                    time.strftime("%H:%M:%S", time.gmtime(float(eta)))])

            else:
                break

        logg(3, f'Writing voiceover files ({self.media.src_filename_extension})')
        final_track_FLFR = final_track_FLFR.set_frame_rate(48000)
        with open(self.media.directory_temp + self.media.dst_filename + '.VO.FLFR.wav', 'wb') as file_final_track_FLFR:
            final_track_FLFR.export(file_final_track_FLFR, format="wav")
        if self.media.dst_audio_channels == 6:
            final_track_FC = final_track_FC.set_frame_rate(48000)
            with open(self.media.directory_temp + self.media.dst_filename + '.VO.FC.wav', 'wb') as file_final_track_FC:
                final_track_FC.export(file_final_track_FC, format="wav")

        logg(3, f'Merging voiceover files ({self.media.src_filename_extension})')
        merge_vo_channels = f'{utils.exec_path("ffmpeg")} -y -i "{self.media.directory_temp}{self.media.dst_filename}.FL.wav" -i "{self.media.directory_temp}{self.media.dst_filename}.VO.FLFR.wav" -filter_complex "[0:a][1:a]amerge=inputs=2,pan=mono|c0=1*c0+1*c1[a]" -map "[a]" "{self.media.directory_temp}{self.media.dst_filename}.FL.VO.wav"'
        merge_vo_channels = merge_vo_channels + f' && \\\n{utils.exec_path("ffmpeg")} -y -i "{self.media.directory_temp}{self.media.dst_filename}.FR.wav" -i "{self.media.directory_temp}{self.media.dst_filename}.VO.FLFR.wav" -filter_complex "[0:a][1:a]amerge=inputs=2,pan=mono|c0=1*c0+1*c1[a]" -map "[a]" "{self.media.directory_temp}{self.media.dst_filename}.FR.VO.wav"'
        if self.media.dst_audio_channels == 6:
            merge_vo_channels = merge_vo_channels + f' && \\\n{utils.exec_path("ffmpeg")} -y -i "{self.media.directory_temp}{self.media.dst_filename}.FC.wav" -i "{self.media.directory_temp}{self.media.dst_filename}.VO.FC.wav" -filter_complex "[0:a][1:a]amerge=inputs=2,pan=mono|c0=1*c0+1*c1[a]" -map "[a]" "{self.media.directory_temp}{self.media.dst_filename}.FC.VO.wav"'

        subprocess.run(merge_vo_channels, shell=True, check=True, stderr=subprocess.DEVNULL)

        self.terminate()
        self.operation_finished = True
        if self.kill.is_set() and self.operation_finished == False:
            self.interrupted = True
        else:
            self.interrupted = False


class JobMux(Job):
    def run(self):
        self.started = True

        subprocess.run(self.command, shell=True, check=True, stderr=subprocess.DEVNULL)

        self.terminate()
        self.operation_finished = True

        if self.kill.is_set() and self.operation_finished == False:
            self.interrupted = True
        else:
            self.interrupted = False


class JobMoveFiles(Job):
    def run(self):
        self.started = True
        
        old_res_type = ''
        old_base_meta = ''

        if self.media.media_dst == 'archive':# or self.media.media_dst == 'rearchive':
            if os.path.isfile(self.media.directory_final_meta + self.media.base_filename + '.FHD.mkv'):
                old_res_type = '.FHD'
                old_res_type_extension = old_res_type + '.mkv'
                old_base_meta = self.media.directory_final_meta + self.media.base_filename + old_res_type
                os.unlink(old_base_meta + '.mkv')
                if self.media.video_type == 'movie':
                    if os.path.isfile(DirConfig.fin_movies_fhd + self.media.base_filename + old_res_type_extension):
                        os.remove(DirConfig.fin_movies_fhd + self.media.base_filename + old_res_type_extension)
                    else: os.remove(DirConfig.old_fin_movies_fhd + self.media.base_filename + old_res_type_extension)
                elif self.media.video_type == 'serie':
                    if os.path.isfile(DirConfig.fin_series_fhd + self.media.base_directory + '/' + self.media.base_filename + old_res_type_extension):
                        os.remove(DirConfig.fin_series_fhd + self.media.base_directory + '/' + self.media.base_filename + old_res_type_extension)
                    else: os.remove(DirConfig.old_fin_series_fhd + self.media.base_directory + '/' + self.media.base_filename + old_res_type_extension)
                    if os.path.isdir(DirConfig.old_fin_series_fhd + self.media.base_directory + '/'):
                        if not os.listdir(DirConfig.old_fin_series_fhd + self.media.base_directory + '/'):
                            print(f'### direcotory is empty: {DirConfig.old_fin_series_fhd + self.media.base_directory + "/"}')
                        else: print(f'### direcotory is not empty: {DirConfig.old_fin_series_fhd + self.media.base_directory + "/"}')

            if os.path.isfile(self.media.directory_final_meta + self.media.base_filename + '.FHD.HDR.mkv'):
                old_res_type = '.FHD.HDR'
                old_res_type_extension = old_res_type + '.mkv'
                old_base_meta = self.media.directory_final_meta + self.media.base_filename + old_res_type
                os.unlink(old_base_meta + '.mkv')
                if self.media.video_type == 'movie':
                    if os.path.isfile(DirConfig.fin_movies_fhd_hdr + self.media.base_filename + old_res_type_extension):
                        os.remove(DirConfig.fin_movies_fhd_hdr + self.media.base_filename + old_res_type_extension)
                    else: os.remove(DirConfig.old_fin_movies_fhd_hdr + self.media.base_filename + old_res_type_extension)
                elif self.media.video_type == 'serie':
                    if os.path.isfile(DirConfig.fin_series_fhd_hdr + self.media.base_directory + '/' + self.media.base_filename + old_res_type_extension):
                        os.remove(DirConfig.fin_series_fhd_hdr + self.media.base_directory + '/' + self.media.base_filename + old_res_type_extension)
                    else: os.remove(DirConfig.old_fin_series_fhd_hdr + self.media.base_directory + '/' + self.media.base_filename + old_res_type_extension)
                
            if os.path.isfile(self.media.directory_final_meta + self.media.base_filename + '.FHD.DHDR.mkv'):
                old_res_type = '.FHD.DHDR'
                old_res_type_extension = old_res_type + '.mkv'
                old_base_meta = self.media.directory_final_meta + self.media.base_filename + old_res_type
                os.unlink(old_base_meta + '.mkv')
                if self.media.video_type == 'movie':
                    if os.path.isfile(DirConfig.fin_movies_fhd_dhdr + self.media.base_filename + old_res_type_extension):
                        os.remove(DirConfig.fin_movies_fhd_dhdr + self.media.base_filename + old_res_type_extension)
                    else: os.remove(DirConfig.old_fin_movies_fhd_dhdr + self.media.base_filename + old_res_type_extension)
                elif self.media.video_type == 'serie':
                    if os.path.isfile(DirConfig.fin_series_fhd_dhdr + self.media.base_directory + '/' + self.media.base_filename + old_res_type_extension):
                        os.remove(DirConfig.fin_series_fhd_dhdr + self.media.base_directory + '/' + self.media.base_filename + old_res_type_extension)
                    else: os.remove(DirConfig.old_fin_series_fhd_dhdr + self.media.base_directory + '/' + self.media.base_filename + old_res_type_extension)

            if os.path.isfile(self.media.directory_final_meta + self.media.base_filename + '.UHD.mkv'):
                old_res_type = '.UHD'
                old_res_type_extension = old_res_type + '.mkv'
                old_base_meta = self.media.directory_final_meta + self.media.base_filename + old_res_type
                os.unlink(old_base_meta + '.mkv')
                if self.media.video_type == 'movie':
                    if os.path.isfile(DirConfig.fin_movies_uhd + self.media.base_filename + old_res_type_extension):
                        os.remove(DirConfig.fin_movies_uhd + self.media.base_filename + old_res_type_extension)
                    else: os.remove(DirConfig.old_fin_movies_uhd + self.media.base_filename + old_res_type_extension)
                elif self.media.video_type == 'serie':
                    if os.path.isfile(DirConfig.fin_series_uhd + self.media.base_directory + '/' + self.media.base_filename + old_res_type_extension):
                        os.remove(DirConfig.fin_series_uhd + self.media.base_directory + '/' + self.media.base_filename + old_res_type_extension)
                    else: os.remove(DirConfig.old_fin_series_uhd + self.media.base_directory + '/' + self.media.base_filename + old_res_type_extension)

            if os.path.isfile(self.media.directory_final_meta + self.media.base_filename + '.UHD.HDR.mkv'):
                old_res_type = '.UHD.HDR'
                old_res_type_extension = old_res_type + '.mkv'
                old_base_meta = self.media.directory_final_meta + self.media.base_filename + old_res_type
                os.unlink(old_base_meta + '.mkv')
                if self.media.video_type == 'movie':
                    if os.path.isfile(DirConfig.fin_movies_uhd_hdr + self.media.base_filename + old_res_type_extension):
                        os.remove(DirConfig.fin_movies_uhd_hdr + self.media.base_filename + old_res_type_extension)
                    else: os.remove(DirConfig.old_fin_movies_uhd_hdr + self.media.base_filename + old_res_type_extension)
                elif self.media.video_type == 'serie':
                    if os.path.isfile(DirConfig.fin_series_uhd_hdr + self.media.base_directory + '/' + self.media.base_filename + old_res_type_extension):
                        os.remove(DirConfig.fin_series_uhd_hdr + self.media.base_directory + '/' + self.media.base_filename + old_res_type_extension)
                    else: os.remove(DirConfig.old_fin_series_uhd_hdr + self.media.base_directory + '/' + self.media.base_filename + old_res_type_extension)
                
            if os.path.isfile(self.media.directory_final_meta + self.media.base_filename + '.UHD.DHDR.mkv'):
                old_res_type = '.UHD.DHDR'
                old_res_type_extension = old_res_type + '.mkv'
                old_base_meta = self.media.directory_final_meta + self.media.base_filename + old_res_type
                os.unlink(old_base_meta + '.mkv')
                if self.media.video_type == 'movie':
                    if os.path.isfile(DirConfig.fin_movies_uhd_dhdr + self.media.base_filename + old_res_type_extension):
                        os.remove(DirConfig.fin_movies_uhd_dhdr + self.media.base_filename + old_res_type_extension)
                    else: os.remove(DirConfig.old_fin_movies_uhd_dhdr + self.media.base_filename + old_res_type_extension)
                elif self.media.video_type == 'serie':
                    if os.path.isfile(DirConfig.fin_series_uhd_dhdr + self.media.base_directory + '/' + self.media.base_filename + old_res_type_extension):
                        os.remove(DirConfig.fin_series_uhd_dhdr + self.media.base_directory + '/' + self.media.base_filename + old_res_type_extension)
                    else: os.remove(DirConfig.old_fin_series_uhd_dhdr + self.media.base_directory + '/' + self.media.base_filename + old_res_type_extension)


        if self.media.media_dst == 'archive':
            if old_res_type != '':
                if self.media.video_type == 'movie':
                    old_archive = DirConfig.d_arch_movies + self.media.base_filename + old_res_type + '/'
                    print(f'=== remove old archive if exists: {old_archive}')
                    if os.path.isdir(old_archive):
                        cmd_rm = f'yes | rm -R "{old_archive}"'
                        subprocess.run(cmd_rm, shell=True, check=True, stderr=subprocess.DEVNULL)
                elif self.media.video_type == 'serie':
                    old_archive = DirConfig.d_arch_series + self.media.base_directory + '/' + self.media.base_filename + old_res_type
                    if os.path.isfile(old_archive + '.srt'):
                        cmd_rm = f'yes | rm -R "{old_archive}"*'
                        print(f'=== remove old archive if exists: {old_archive}')
                        subprocess.run(cmd_rm, shell=True, check=True, stderr=subprocess.DEVNULL)

            if self.media.video_type == 'movie':
                if not os.path.isdir(self.media.directory_archive):
                    os.mkdir(self.media.directory_archive)
            elif self.media.video_type == 'serie':
                if not os.path.isdir(self.media.directory_final):
                    os.makedirs(self.media.directory_final)
                    subprocess.call(['chmod', '-R', '777', self.media.directory_final])
                if not os.path.isdir(self.media.directory_final_meta):
                    os.makedirs(self.media.directory_final_meta)
                    subprocess.call(['chmod', '-R', '777', self.media.directory_final_meta])
                if not os.path.isdir(self.media.directory_archive):
                    os.makedirs(self.media.directory_archive)


        if self.media.media_dst == 'temporary' and self.media.video_type == 'serie':
            if not os.path.isdir(self.media.directory_final):
                os.makedirs(self.media.directory_final)

        shutil.move(self.media.directory_done + self.media.dst_filename + '.mkv', self.media.directory_final + self.media.dst_filename + '.mkv')

        if self.media.media_dst == 'temporary':
            shutil.move(self.media.directory_tts, self.media.directory_archive + self.media.dst_directory + '.VO')
            shutil.move(self.media.directory_temp + self.media.dst_filename + '.srt', self.media.directory_archive + self.media.dst_filename + '.srt')
            shutil.move(self.media.directory_temp + self.media.dst_filename + '.eng.srt', self.media.directory_archive + self.media.dst_filename + '.eng.srt')
            shutil.move(self.media.directory_temp + self.media.dst_filename + '.tts.txt', self.media.directory_archive + self.media.dst_filename + '.tts.txt')
            

        if self.media.media_dst == 'archive':
            if self.media.video_type == 'movie':
                
                # if old_res_type != '' and (self.media.base_filename + old_res_type != self.media.dst_filename):
                #print(f'#ooo# 1: ' + old_base_meta + '.nfo')
                if os.path.isfile(old_base_meta + '.nfo'):
                    shutil.move(old_base_meta + '.nfo',  self.media.directory_final_meta + self.media.dst_filename + '.nfo')
                #print(f'#ooo# 2: ' + old_base_meta + '-fanart.jpg')
                if os.path.isfile(old_base_meta + '-fanart.jpg'):
                    shutil.move(old_base_meta + '-fanart.jpg',  self.media.directory_final_meta + self.media.dst_filename + '-fanart.jpg')
                #if self.media.voiceover != True:
                #print(f'#ooo# 3: ' + old_base_meta + '-poster-copy.jpg')
                if os.path.isfile(old_base_meta + '-poster-copy.jpg'): ################################################################################################ TMP
                    os.remove(old_base_meta + '-poster.jpg')
                    shutil.move(old_base_meta + '-poster-copy.jpg',  old_base_meta + '-poster.jpg')
                    os.remove(old_base_meta + '-poster-flag.jpg')
                #print(f'#ooo# 4: ' + old_base_meta + '-poster.jpg')
                if os.path.isfile(old_base_meta + '-poster.jpg'):
                    shutil.move(old_base_meta + '-poster.jpg',  self.media.directory_final_meta + self.media.dst_filename + '-poster.jpg')

            elif self.media.video_type == 'serie': 
                # if old_res_type != '' and (self.media.base_filename + old_res_type != self.media.dst_filename):
                if os.path.isfile(old_base_meta + '.nfo'):
                    shutil.move(old_base_meta + '.nfo', self.media.directory_final_meta + self.media.dst_filename + '.nfo')
                if os.path.isfile(old_base_meta + '-thumb.jpg'):
                    shutil.move(old_base_meta + '-thumb.jpg',  self.media.directory_final_meta + self.media.dst_filename + '-thumb.jpg')
                # #if media.voiceover != True:
                if os.path.isfile(self.media.directory_final_meta + 'poster-copy.jpg'): ################################################################################################ TMP
                    os.remove(self.media.directory_final_meta + 'poster.jpg')
                    shutil.move(self.media.directory_final_meta + 'poster-copy.jpg',  self.media.directory_final_meta + 'poster.jpg')
                    os.remove(self.media.directory_final_meta + 'poster-flag.jpg')


        if self.media.media_dst == 'archive':
            shutil.move(self.media.directory_temp + self.media.dst_filename + '.info.audio.json', self.media.directory_archive + self.media.dst_filename + '.info.audio.json')
            shutil.move(self.media.directory_temp + self.media.dst_filename + '.info.madiainfo.json', self.media.directory_archive + self.media.dst_filename + '.info.madiainfo.json')
            shutil.move(self.media.directory_temp + self.media.dst_filename + '.info.subtitles.json', self.media.directory_archive + self.media.dst_filename + '.info.subtitles.json')
            shutil.move(self.media.directory_temp + self.media.dst_filename + '.info.video.json', self.media.directory_archive + self.media.dst_filename + '.info.video.json')


        if self.media.media_dst == 'archive' or self.media.media_dst == 'rearchive':
            if os.path.isdir(self.media.directory_tts):
                if os.path.isdir(self.media.directory_archive + self.media.dst_filename + '.VO'):
                    shutil.rmtree(self.media.directory_archive + self.media.dst_filename + '.VO')
                shutil.move(self.media.directory_tts, self.media.directory_archive + self.media.dst_filename + '.VO')

            if os.path.isfile(self.media.directory_temp + self.media.dst_filename + '.srt'):
                shutil.move(self.media.directory_temp + self.media.dst_filename + '.srt', self.media.directory_archive + self.media.dst_filename + '.srt')
            shutil.move(self.media.directory_temp + self.media.dst_filename + '.eng.srt', self.media.directory_archive + self.media.dst_filename + '.eng.srt')
            if os.path.isfile(self.media.directory_temp + self.media.dst_filename + '.tts.txt'):
                shutil.move(self.media.directory_temp + self.media.dst_filename + '.tts.txt', self.media.directory_archive + self.media.dst_filename + '.tts.txt')


        if self.media.media_dst == 'archive':# or self.media.media_dst == 'rearchive':
            cmd_sm = f'yes | ln -f -s {self.media.directory_final}{self.media.dst_filename}.mkv {self.media.directory_final_meta}{self.media.dst_filename}.mkv'
            subprocess.run(cmd_sm, shell=True, check=True, stderr=subprocess.DEVNULL)


        logg(3, f'Removing unnecessery files ({self.media.src_filename_extension})')
        cmd_rm1 = f'yes | rm -R "{self.media.directory_temp}{self.media.dst_filename}"*'
        cmd_rm2 = f'yes | rm -R "{self.media.directory}{self.media.src_filename}"*'
        subprocess.run(cmd_rm1, shell=True, check=True, stderr=subprocess.DEVNULL)
        subprocess.run(cmd_rm2, shell=True, check=True, stderr=subprocess.DEVNULL)
        logg(3, f'Removing unnecessery files done ({self.media.src_filename_extension})')


        if self.media.media_dst == 'temporary' or self.media.media_dst == 'rearchive':
            delete_from_db(self.media)

        self.terminate()
        self.operation_finished = True

        if self.kill.is_set() and self.operation_finished == False:
            self.interrupted = True
        else:
            self.interrupted = False


########################################################################################

class OutStream:
    def __init__(self, fileno):
        self._fileno = fileno
        self._buffer = b''

    def read_lines(self):
        try:
            output = os.read(self._fileno, 1000)
        except OSError as e:
            if e.errno != errno.EIO: raise
            output = b''
        lines = output.split(b'\r')
        lines[0] = self._buffer + lines[0]
        if output:
            self._buffer = lines[-1]
            finished_lines = lines[:-1]
            readable = True
        else:
            self._buffer = b''
            if len(lines) == 1 and not lines[0]:
                lines = []
            finished_lines = lines
            readable = False
        finished_lines = [line.rstrip(b'\r').decode() for line in finished_lines]
        return finished_lines, readable

    def fileno(self):
        return self._fileno


def output_analyze(media, operation_type, output_line, duration):
    output_line = output_line.strip()

    bad_words = ['corrupt', 'error', 'failed']
    for word in bad_words:
        find_word = re.search(f'.*{word}.*', output_line)
        if find_word:
            print(f'### found bad word: {word}')
            return 'error'

    current_seconds = None
    remaining_seconds = None
    percentage = None
    speed = None
    eta = None
    bitrate = None

    if re.search('.*size.*time.*', output_line):
        current_time = re.sub(r'.*size.*time=(...........).*bitrate=(.*) speed=(.*)', r'\1', output_line)
        time_split = re.split(r"[:.]", current_time)
        current_seconds = int(time_split[0])*3600 + int(time_split[1])*60 + int(time_split[2]) + int(time_split[3])/100
        if current_seconds != 0.0:
            remaining_seconds =  duration - current_seconds
            percentage = 100 * current_seconds / duration
            speed_string = re.sub(r'.*size.*time=(...........).*bitrate=(.*) speed=(.*)x', r'\3', output_line).replace(' ', '')
            try:
                speed = float(speed_string)
                eta = remaining_seconds / speed
            except:
                speed = 0
                eta = 0
            bitrate = float(re.sub(r'.*size.*time=(...........).*bitrate=(.*) speed=(.*)', r'\2', output_line)[:-7].replace(' ', ''))
            if operation_type == 'extract_audio':
                bitrate = bitrate * media.dst_audio_channels

    if re.search('.*video:(.*)kB.*audio:(.*)kB.*subtitle:(.*)kB.*', output_line):
        size = 0
        if operation_type == 'convert_audio' or operation_type == 'convert_audio_voiceover' or operation_type == 'extract_audio':
            size = re.sub(r'.*video:(.*)kB.*audio:(.*)kB.*subtitle:(.*)kB other.*', r'\2', output_line)
        elif operation_type == 'convert_video':
            size = re.sub(r'.*video:(.*)kB.*audio:(.*)kB.*subtitle:(.*)kB other.*', r'\1', output_line)
        elif operation_type == 'extract_subtitles':
            size = re.sub(r'.*video:(.*)kB.*audio:(.*)kB.*subtitle:(.*)kB other.*', r'\3', output_line)
            
        print(f'size : {size}')
        current_seconds = duration
        remaining_seconds = 0
        percentage = 100
        eta = 0
        bitrate = float(size) * 8 * 1024 / 1000 / duration

    if bitrate != None:
        print(f'### {media.src_filename_extension} ### percentage {format(percentage, ".2f") if percentage < 100 else str(percentage)}, eta {time.strftime("%H:%M:%S", time.gmtime(float(eta)))}, bitrate {format(bitrate, ".1f")}')
        
        if operation_type != 'extract_subtitles':
            socketio.emit('process_update', [operation_type,
                                            media.src_filename_extension,
                                            format(percentage, '.2f') if percentage < 100 else str(percentage),
                                            time.strftime("%H:%M:%S", time.gmtime(float(eta))),
                                            format(bitrate, '.1f')])
        else:
            sub_addon = ''
            if media.subtitle_stream_main != None and media.subtitle_stream_additional != None:
                sub_addon = 'both'
            elif media.subtitle_stream_main != None:
                sub_addon = 'main'
            elif media.subtitle_stream_additional != None:
                sub_addon = 'additional'
            socketio.emit('process_update', [operation_type,
                                            media.src_filename_extension,
                                            format(percentage, '.2f') if percentage < 100 else str(percentage),
                                            time.strftime("%H:%M:%S", time.gmtime(float(eta))),
                                            format(bitrate, '.0f'),
                                            sub_addon])
        return [duration, current_seconds, remaining_seconds, percentage, speed, eta, bitrate]


def update_download_bytes(operation, text_bytes = 0, text_chars = 0):
    if not os.path.isfile(DirConfig.d_conf + 'tts_bytes.txt'):
        open(DirConfig.d_conf + 'tts_bytes.txt', 'a').close()
    
    with open(DirConfig.d_conf + 'tts_bytes.txt', 'r') as tts_bytes_file:
        tts_bytes = tts_bytes_file.read()
    
    acc_text_bytes = 0
    acc_text_chars = 0
    
    current_date = datetime.date.today().strftime('%Y-%m')
    match_text_bytes = re.findall(current_date + ' bytes: (\d+)\n' + current_date + ' chars: (\d+)', tts_bytes)
    
    if match_text_bytes:
        acc_text_bytes = int(match_text_bytes[0][0])
        acc_text_chars = int(match_text_bytes[0][1])
    else:
        tts_bytes = tts_bytes + current_date + ' bytes: 0\n' + current_date + ' chars: 0\n\n'
        with open(DirConfig.d_conf + 'tts_bytes.txt', 'w') as tts_bytes_file:
            tts_bytes_file.write(tts_bytes)
    
    if operation == 'get':
        return acc_text_bytes, acc_text_chars
    elif operation == 'add':
        updated_acc_text_bytes = acc_text_bytes + text_bytes
        updated_acc_text_chars = acc_text_chars + text_chars
        
        tts_bytes = tts_bytes.replace(current_date + ' bytes: ' + str(acc_text_bytes), current_date + ' bytes: ' + str(updated_acc_text_bytes))
        tts_bytes = tts_bytes.replace(current_date + ' chars: ' + str(acc_text_chars), current_date + ' chars: ' + str(updated_acc_text_chars))
    
        with open(DirConfig.d_conf + 'tts_bytes.txt', 'w') as tts_bytes_file:
            tts_bytes_file.write(tts_bytes)


def download_voiceover(directory, file_name, tts_line):
    target_dBFS = -13.5

    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text = tts_line)
    voice = texttospeech.VoiceSelectionParams(language_code = OtherConfig.google_vo_language_code, name = OtherConfig.google_vo_voice_name)
    audio_config = texttospeech.AudioConfig(audio_encoding = texttospeech.AudioEncoding.LINEAR16, speaking_rate = OtherConfig.google_vo_speaking_rate, pitch = OtherConfig.google_vo_pitch, volume_gain_db = 14)
    response = client.synthesize_speech(input = input_text, voice = voice, audio_config = audio_config)
    data = BytesIO(response.audio_content)
    audio = AudioSegment.from_file(data)
    
    change_in_dBFS = target_dBFS - audio.dBFS
    audio = audio.apply_gain(change_in_dBFS)

    start_trim = detect_silence(audio)
    end_trim = detect_silence(audio.reverse())

    duration = len(audio)
    trimmed_sound = audio[start_trim:duration - end_trim]
    trimmed_sound.export(directory + file_name, bitrate='48k', format="mp3")


def detect_silence(sound, silence_threshold=-60.0, chunk_size=5):
    trim_ms = 0
    assert chunk_size > 0
    while sound[trim_ms:trim_ms+chunk_size].dBFS < silence_threshold and trim_ms < len(sound):
        trim_ms += chunk_size
    return trim_ms


########################################################################################

def make_command(media, operation_type):
    cmd = ''
    if operation_type == 'detect_resolution':
        cmd = ''
    if operation_type == 'convert_video':
        cmd = cmd_convert_video(media)
    if operation_type == 'convert_audio':
        cmd = cmd_convert_audio(media)
    if operation_type == 'convert_voiceover_audio':
        cmd = cmd_convert_voiceover_audio(media)
    if operation_type == 'extract_hdrplus':
        cmd = cmd_extract_hdrplus(media)
    if operation_type == 'extract_audio':
        cmd = cmd_extract_audio(media)
    if operation_type == 'extract_subtitles':
        cmd = cmd_extract_subtitles(media)
    if operation_type == 'mux':
        cmd = cmd_mux(media)
    
    print(f'\n============================================================================== printing cmd:\n{cmd}\n')
    
    return cmd

def cmd_convert_video(media):
    cmd = ''
    
    sproper_video_start_at = ''
    sproper_video_time = ''

    if media.proper_video_start_at != 0:
        sproper_video_start_at = f'-ss {media.proper_video_start_at} '
    if media.proper_video_time != 0:
        sproper_video_time = f'-t {media.proper_video_time} '

    if media.audio_duration - media.video_duration > 1 and media.audio_duration - media.video_duration > -1:
        if media.proper_video_start_at != 0:
            sproper_video_start_at = f'-ss {media.proper_video_start_at} '
        if media.proper_video_time != 0:
            sproper_video_time = f'-t {media.proper_video_time} '

    cut_str = ''
    if media.cut_str != None:
        cut_str = media.cut_str + ' '
    master_display = ''
    if media.master_display != None:
        master_display = ':master-display=' + media.master_display
    max_cll = ''
    if media.max_cll != None:
        max_cll = ':max-cll=' + media.max_cll
    dhdr = ''
    if media.dhdr == 1:
        dhdr = f':dhdr10_opt=1:dhdr10-info="{media.directory_temp}{media.dst_filename}.dhdr.metadata.json"'

    if media.hdr == 1:
        cmd = f'{utils.exec_path("ffmpeg")} -hide_banner -y -threads 4 -i "{media.src_file_path}" {sproper_video_start_at}{sproper_video_time}{cut_str}-c:v libx265 -pix_fmt yuv420p10le -x265-params "crf=24:vbv-maxrate={media.dst_bitrate}:vbv-bufsize={media.dst_bitrate*2}:aq-mode=3:colorprim=bt2020:colormatrix=bt2020nc:transfer=smpte2084:repeat-headers=1:hdr10=1:hdr10_opt=1{max_cll}{master_display}{dhdr}" -map 0:{media.video_stream} "{media.directory_temp}{media.dst_filename}.h265"'
    else:
        cmd = f'{utils.exec_path("ffmpeg")} -hide_banner -y -threads 4 -i "{media.src_file_path}" {sproper_video_start_at}{sproper_video_time}{cut_str}-c:v libx265 -pix_fmt yuv420p10le -x265-params "crf=24:vbv-maxrate={media.dst_bitrate}:vbv-bufsize={media.dst_bitrate*2}:aq-mode=3:colorprim=bt709:colormatrix=bt709:transfer=bt709" -map 0:{media.video_stream} "{media.directory_temp}{media.dst_filename}.h265"'

    return cmd

def cmd_convert_audio(media):
    cmd = ''
    if media.dst_audio_channels == 2:
        cmd = f'{utils.exec_path("ffmpeg")} -y -threads 4 -i "{media.directory_temp}{media.dst_filename}.FL.wav" -i "{media.directory_temp}{media.dst_filename}.FR.wav" -filter_complex "[0:a][1:a]join=inputs=2:channel_layout=stereo:map=0.0-FL|1.0-FR[a]" -map "[a]" -c:a libfdk_aac -vbr {OtherConfig.audio_quaility_original} -ac 2 "{media.directory_temp}{media.dst_filename}.aac"'
    elif media.dst_audio_channels == 6:
        cmd = f'{utils.exec_path("ffmpeg")} -y -threads 4 -i "{media.directory_temp}{media.dst_filename}.FL.wav" -i "{media.directory_temp}{media.dst_filename}.FR.wav" -i "{media.directory_temp}{media.dst_filename}.FC.wav" -i "{media.directory_temp}{media.dst_filename}.LFE.wav" -i "{media.directory_temp}{media.dst_filename}.SL.wav" -i "{media.directory_temp}{media.dst_filename}.SR.wav" -filter_complex "[0:a][1:a][2:a][3:a][4:a][5:a]join=inputs=6:channel_layout=5.1(side):map=0.0-FL|1.0-FR|2.0-FC|3.0-LFE|4.0-SL|5.0-SR[a]" -map "[a]" -c:a libfdk_aac -vbr {OtherConfig.audio_quaility_original} -ac 6 "{media.directory_temp}{media.dst_filename}.aac"'
    elif media.dst_audio_channels == 8:
        cmd = f'{utils.exec_path("ffmpeg")} -y -threads 4 -i "{media.directory_temp}{media.dst_filename}.FL.wav" -i "{media.directory_temp}{media.dst_filename}.FR.wav" -i "{media.directory_temp}{media.dst_filename}.FC.wav" -i "{media.directory_temp}{media.dst_filename}.LFE.wav" -i "{media.directory_temp}{media.dst_filename}.BL.wav" -i "{media.directory_temp}{media.dst_filename}.BR.wav" -i "{media.directory_temp}{media.dst_filename}.SL.wav" -i "{media.directory_temp}{media.dst_filename}.SR.wav" -filter_complex "[0:a][1:a][2:a][3:a][4:a][5:a][6:a][7:a]join=inputs=8:channel_layout=7.1:map=0.0-FL|1.0-FR|2.0-FC|3.0-LFE|4.0-BL|5.0-BR|6.0-SL|7.0-SR[a]" -map "[a]" -c:a libfdk_aac -vbr {OtherConfig.audio_quaility_original} -ac 8 "{media.directory_temp}{media.dst_filename}.aac"'
    return cmd

def cmd_convert_voiceover_audio(media):
    cmd = ''
    if media.dst_audio_channels == 2:
        cmd = f'{utils.exec_path("ffmpeg")} -y -threads 4 -i "{media.directory_temp}{media.dst_filename}.FL.VO.wav" -i "{media.directory_temp}{media.dst_filename}.FR.VO.wav" -filter_complex "[0:a][1:a]join=inputs=2:channel_layout=stereo:map=0.0-FL|1.0-FR[a]" -map "[a]" -c:a libfdk_aac -vbr {OtherConfig.audio_quaility_voiceover} -ac 2 "{media.directory_temp}{media.dst_filename}.VO.aac"'
    elif media.dst_audio_channels == 6:
        cmd = f'{utils.exec_path("ffmpeg")} -y -threads 4 -i "{media.directory_temp}{media.dst_filename}.FL.VO.wav" -i "{media.directory_temp}{media.dst_filename}.FR.VO.wav" -i "{media.directory_temp}{media.dst_filename}.FC.VO.wav" -i "{media.directory_temp}{media.dst_filename}.LFE.wav" -i "{media.directory_temp}{media.dst_filename}.SL.wav" -i "{media.directory_temp}{media.dst_filename}.SR.wav" -filter_complex "[0:a][1:a][2:a][3:a][4:a][5:a]join=inputs=6:channel_layout=5.1(side):map=0.0-FL|1.0-FR|2.0-FC|3.0-LFE|4.0-SL|5.0-SR[a]" -map "[a]" -c:a libfdk_aac -vbr {OtherConfig.audio_quaility_voiceover} -ac 6 "{media.directory_temp}{media.dst_filename}.VO.aac"'
    elif media.dst_audio_channels == 8:
        cmd = f'{utils.exec_path("ffmpeg")} -y -threads 4 -i "{media.directory_temp}{media.dst_filename}.FL.VO.wav" -i "{media.directory_temp}{media.dst_filename}.FR.VO.wav" -i "{media.directory_temp}{media.dst_filename}.FC.VO.wav" -i "{media.directory_temp}{media.dst_filename}.LFE.wav" -i "{media.directory_temp}{media.dst_filename}.BL.wav" -i "{media.directory_temp}{media.dst_filename}.BR.wav" -i "{media.directory_temp}{media.dst_filename}.SL.wav" -i "{media.directory_temp}{media.dst_filename}.SR.wav" -filter_complex "[0:a][1:a][2:a][3:a][4:a][5:a][6:a][7:a]join=inputs=8:channel_layout=7.1:map=0.0-FL|1.0-FR|2.0-FC|3.0-LFE|4.0-BL|5.0-BR|6.0-SL|7.0-SR[a]" -map "[a]" -c:a libfdk_aac -vbr {OtherConfig.audio_quaility_voiceover} -ac 8 "{media.directory_temp}{media.dst_filename}.VO.aac"'
    return cmd

def cmd_extract_hdrplus(media):
    cmd = f'{utils.exec_path("ffmpeg")} -i "{media.src_file_path}" -map 0:{media.video_stream} -c copy -vbsf hevc_mp4toannexb -f hevc - | {utils.exec_path("hdr10plus_tool")} extract -o "{media.directory_temp}{media.dst_filename}.dhdr.metadata.json" -'
    return cmd

def cmd_extract_audio(media):
    cmd = ''

    sproper_audio_start_at = ''
    sproper_audio_time = ''
    
    if media.proper_audio_start_at != 0:
        sproper_audio_start_at = f'-ss {media.proper_audio_start_at} '
    if media.proper_audio_time != 0:
        sproper_audio_time = f'-t {media.proper_audio_time} '

    if media.audio_duration - media.video_duration > 1 and media.audio_duration - media.video_duration > -1:
        if media.proper_audio_start_at != 0:
            sproper_audio_start_at = f'-ss {media.proper_audio_start_at} '
        if media.proper_audio_time != 0:
            sproper_audio_time = f'-t {media.proper_audio_time} '

    proper_audio_delay = media.proper_audio_delay * 1000
    filter_adelay = ''

    if media.audio_channels == 1 or media.dst_audio_channels == 2:
        if proper_audio_delay > 0:
            filter_adelay = f';[FL]adelay={proper_audio_delay}[FL];[FR]adelay={proper_audio_delay}[FR]'
        cmd = f'{utils.exec_path("ffmpeg")} -y -threads 4 -i "{media.src_file_path}" -filter_complex "[0:{media.audio_stream}]channelsplit=channel_layout=stereo[FL][FR]{filter_adelay}" -ar 48000 {sproper_audio_start_at}{sproper_audio_time}-map "[FL]" "{media.directory_temp}{media.dst_filename}.FL.wav" -ar 48000 {sproper_audio_start_at}{sproper_audio_time}-map "[FR]" "{media.directory_temp}{media.dst_filename}.FR.wav"'

    if media.dst_audio_channels == 6:
        if proper_audio_delay > 0:
            filter_adelay = f';[FL]adelay={proper_audio_delay}[FL];[FR]adelay={proper_audio_delay}[FR];[FC]adelay={proper_audio_delay}[FC];[LFE]adelay={proper_audio_delay}[LFE];[SL]adelay={proper_audio_delay}[SL];[SR]adelay={proper_audio_delay}[SR]'
        cmd = f'{utils.exec_path("ffmpeg")} -y -threads 4 -i "{media.src_file_path}" -filter_complex "[0:{media.audio_stream}]channelsplit=channel_layout=5.1[FL][FR][FC][LFE][SL][SR]{filter_adelay}" -ar 48000 {sproper_audio_start_at}{sproper_audio_time}-map "[FL]" "{media.directory_temp}{media.dst_filename}.FL.wav" -ar 48000 {sproper_audio_start_at}{sproper_audio_time}-map "[FR]" "{media.directory_temp}{media.dst_filename}.FR.wav" -ar 48000 {sproper_audio_start_at}{sproper_audio_time}-map "[FC]" "{media.directory_temp}{media.dst_filename}.FC.wav" -ar 48000 {sproper_audio_start_at}{sproper_audio_time}-map "[LFE]" "{media.directory_temp}{media.dst_filename}.LFE.wav" -ar 48000 {sproper_audio_start_at}{sproper_audio_time}-map "[SL]" "{media.directory_temp}{media.dst_filename}.SL.wav" -ar 48000 {sproper_audio_start_at}{sproper_audio_time}-map "[SR]" "{media.directory_temp}{media.dst_filename}.SR.wav"'

    return cmd

def cmd_extract_subtitles(media):
    cmd = f'{utils.exec_path("ffmpeg")} -y -i "{media.src_file_path}"'
    if media.subtitle_stream_main != None:
        cmd = cmd + f' -map 0:{media.subtitle_stream_main} "{media.directory + media.src_filename}.srt"'
    if media.subtitle_stream_additional != None:
        cmd = cmd + f' -map 0:{media.subtitle_stream_additional} "{media.directory + media.src_filename}.{OtherConfig.lang_additional}.srt"'
    return cmd

def cmd_mux(media):
    cmd = ''

    if media.audio_language == '':
        media.audio_language = 'und'

    add_lang_main_sub = ''
    add_lang_main_sub_map = ''
    if media.audio_language != OtherConfig.lang_main:
        add_lang_main_sub = f'--language 0:{OtherConfig.lang_main} --default-track 0:no "(" {media.directory_temp}{media.dst_filename}.srt ")" '
        if media.media_dst == 'temporary' or media.media_dst == 'rearchive':
            add_lang_main_sub_map = ',2:0'
        else:
            add_lang_main_sub_map = ',3:0'
    
    add_lang_additional_sub = ''
    add_lang_additional_sub_map = ''
    if os.path.isfile(f'{media.directory_temp}{media.dst_filename}.{OtherConfig.lang_additional}.srt'):
        add_lang_additional_sub = f'--language 0:eng --default-track 0:no "(" {media.directory_temp}{media.dst_filename}.{OtherConfig.lang_additional}.srt ")" '
        if media.media_dst == 'temporary' or media.media_dst == 'rearchive':
            if media.audio_language == OtherConfig.lang_main: add_lang_additional_sub_map = ',2:0'
            else: add_lang_additional_sub_map = ',3:0'
        else:
            if media.audio_language == OtherConfig.lang_main: add_lang_additional_sub_map = ',3:0'
            else: add_lang_additional_sub_map = ',4:0'

    cmd_vo = f'--language 0:{OtherConfig.lang_main} --default-track 0:no "(" {media.directory_temp}{media.dst_filename}.VO.aac ")" '

    if media.media_dst == 'archive':
        cmd = f'{utils.exec_path("mkvmerge")} --ui-language en_US -q -o "{media.directory_done}{media.dst_filename}.mkv" --no-subtitles --no-track-tags --no-global-tags --no-chapters --language 0:und --default-track 0:yes "(" {media.directory_temp}{media.dst_filename}.h265 ")" --language 0:{media.audio_language} --default-track 0:yes "(" {media.directory_temp}{media.dst_filename}.aac ")" {cmd_vo}{add_lang_main_sub}{add_lang_additional_sub}--title "{media.title}" --track-order 0:0,1:0,2:0{add_lang_main_sub_map}{add_lang_additional_sub_map}'
    elif media.media_dst == 'temporary' or media.media_dst == 'rearchive':
        cmd = f'{utils.exec_path("mkvmerge")} --ui-language en_US -q -o "{media.directory_done}{media.dst_filename}.mkv" --no-subtitles --no-track-tags --no-global-tags --no-chapters --language 0:und --default-track 0:yes --language 1:{media.audio_language} "(" "{media.src_file_path}" ")" {cmd_vo}{add_lang_main_sub}{add_lang_additional_sub}--title "{media.title}" --track-order 0:0,0:1,1:0{add_lang_main_sub_map}{add_lang_additional_sub_map}'

    return cmd

