import subprocess
import shlex
import os
import cv2
import numpy as np
import json
from decimal import Decimal
import time
from PIL import Image
from pydub import AudioSegment, effects

from videotools.dbing import add_to_db
from videotools.config import OtherConfig
from videotools.logger import logg
from videotools import utils


def detect_last_real_frame(media):
    frame_count = 0
    cmd_probe_mediainfo = f'{utils.exec_path("mediainfo")} --Output=JSON "{media.src_file_path}"'
    probe_mediainfo = subprocess.Popen(cmd_probe_mediainfo, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    mediainfo_stdout, mediainfo_stderr = probe_mediainfo.communicate()
    json_info_mediainfo = json.loads(mediainfo_stdout.decode('utf-8')[:-1])
    for item in json_info_mediainfo['media']['track']:
        if item['@type'] == 'Video' and item['StreamOrder'] == str(media.video_stream):
            if 'FrameCount' in item:
                frame_count = int(item["FrameCount"])
            else:
                print(f'############################################# no FrameCount')

    current_frame = frame_count - 1
    frames_per_second = int(media.video_frame_rate.split('/')[0]) / int(media.video_frame_rate.split('/')[1])
    step_big_sec = 0.3
    step_small_sec = 1

    actual_position = current_frame / frames_per_second
    image_path = f'{media.directory_temp}{media.dst_filename}_frame.png'
    if os.path.isfile(image_path):
        os.remove(image_path)
    while True:
        cmd = f'{utils.exec_path("ffmpeg")} -hide_banner -y -ss {actual_position} -i "{media.src_file_path}" -vframes 1 "{image_path}"'
        print(f'### actual_position: {actual_position}')
        proc_screenshot = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = proc_screenshot.communicate()

        if not os.path.isfile(image_path):  # no frame to extract
            actual_position = actual_position - step_big_sec
            current_frame = current_frame - (step_big_sec * frames_per_second)
        elif not Image.open(image_path).getbbox(): # this is black
            actual_position = actual_position - step_big_sec
            current_frame = current_frame - (step_big_sec * frames_per_second)
        else: # this is NOT black
            break

    final_time = actual_position
    print(f'\n### final_time: {final_time}')
    print(f'### to cut: {media.video_duration - final_time}')

    return media.video_duration - final_time


def detect_last_real_audio(media):
    files = []
    times = []
    if media.dst_audio_channels == 2:
        pass
    elif media.dst_audio_channels == 6:
        files.append(f'{media.directory_temp}{media.dst_filename}.FL.wav')
        files.append(f'{media.directory_temp}{media.dst_filename}.FR.wav')
        files.append(f'{media.directory_temp}{media.dst_filename}.FC.wav')
        files.append(f'{media.directory_temp}{media.dst_filename}.SL.wav')
        files.append(f'{media.directory_temp}{media.dst_filename}.SR.wav')
        files.append(f'{media.directory_temp}{media.dst_filename}.LFE.wav')
        
        for item in files:
            audio = AudioSegment.from_file(item)
            end_audio = detect_silence(audio.reverse())
            times.append(end_audio / 1000)

    times.sort()
    return times[0]


def detect_silence(sound, silence_threshold=-60.0, chunk_size=5):
    trim_ms = 0
    assert chunk_size > 0 # to avoid infinite loop
    while sound[trim_ms:trim_ms+chunk_size].dBFS < silence_threshold and trim_ms < len(sound):
        trim_ms += chunk_size
    return trim_ms


def detect_media_end(media):
    video_cut = detect_last_real_frame(media)

    if media.audio_delay == 0 and media.video_delay == 0:
        print(f'### a media.proper_video_time: {media.proper_video_time}')
        print(f'### a media.proper_audio_time: {media.proper_audio_time}')
        media.proper_video_time = media.proper_video_time - video_cut
        media.proper_audio_time = media.proper_audio_time - video_cut

        media.proper_video_time = media.proper_video_time
        media.proper_audio_time = media.proper_video_time

        media.stop_at = format(media.proper_video_time,'.3f')
        media.proper_video_time = round(media.proper_video_time,3)
        media.proper_audio_time = round(media.proper_video_time,3)

        print(f'### b media.proper_video_time: {media.proper_video_time}')
        print(f'### b media.proper_audio_time: {media.proper_audio_time}')
    else:
        print(f'#################################################### video and audio delay not zero')

    add_to_db(media)


def test_convert_video(media):
    logg(6, f'Running test conversion ({media.src_filename_extension})')

    test_time = 3

    test_time_pre = media.start_at - test_time
    if test_time_pre < 0:
        test_time_pre = 0.0

    duration_time_start_pre = test_time
    if duration_time_start_pre > media.start_at:
        duration_time_start_pre = media.start_at

    sproper_video_start_at_pre = f'-ss {test_time_pre} '
    sproper_video_start_at_post = f'-ss {media.start_at} '
    sproper_video_time_pre = f'-t {duration_time_start_pre} '
    sproper_video_time_post = f'-t {test_time} '

    cmd_start_pre = f'{utils.exec_path("ffmpeg")} -hide_banner -y {sproper_video_start_at_pre}{sproper_video_time_pre}-threads 4 -i "{media.src_file_path}" -s hd720 -c:v libx265 -pix_fmt yuv420p10le -x265-params "crf=24:vbv-maxrate=1000:vbv-bufsize=2000:aq-mode=3:colorprim=bt709:colormatrix=bt709:transfer=bt709" -map 0:{media.video_stream} -c:a libfdk_aac -vbr 2 -ac 2 -map 0:{media.audio_stream} "{media.directory_temp}{media.dst_filename}_start_pre.mkv"'
    cmd_start_post = f'{utils.exec_path("ffmpeg")} -hide_banner -y {sproper_video_start_at_post}{sproper_video_time_post}-threads 4 -i "{media.src_file_path}" -s hd720 -c:v libx265 -pix_fmt yuv420p10le -x265-params "crf=24:vbv-maxrate=1000:vbv-bufsize=2000:aq-mode=3:colorprim=bt709:colormatrix=bt709:transfer=bt709" -map 0:{media.video_stream} -c:a libfdk_aac -vbr 2 -ac 2 -map 0:{media.audio_stream} "{media.directory_temp}{media.dst_filename}_start_post.mkv"'

    print(f'### running start test pre')
    proc_cmd_start_pre = subprocess.Popen(cmd_start_pre, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result_cmd_start_pre = proc_cmd_start_pre.stdout.read().decode('utf-8')[:-1]
    print(f'### running start test post')
    proc_cmd_start_post = subprocess.Popen(cmd_start_post, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result_cmd_start_post = proc_cmd_start_post.stdout.read().decode('utf-8')[:-1]

    sproper_video_stop_at_pre = f'-ss {media.stop_at - test_time} '
    sproper_video_stop_at_post = f'-ss {media.stop_at} '
    sproper_video_time = f'-t {test_time} '

    cmd_stop_pre = f'{utils.exec_path("ffmpeg")} -hide_banner -y {sproper_video_stop_at_pre}{sproper_video_time}-threads 4 -i "{media.src_file_path}" -s hd720 -c:v libx265 -pix_fmt yuv420p10le -x265-params "crf=24:vbv-maxrate=1000:vbv-bufsize=2000:aq-mode=3:colorprim=bt709:colormatrix=bt709:transfer=bt709" -map 0:{media.video_stream} -c:a libfdk_aac -vbr 2 -ac 2 -map 0:{media.audio_stream} "{media.directory_temp}{media.dst_filename}_stop_pre.mkv"'
    cmd_stop_post = f'{utils.exec_path("ffmpeg")} -hide_banner -y {sproper_video_stop_at_post}{sproper_video_time}-threads 4 -i "{media.src_file_path}" -s hd720 -c:v libx265 -pix_fmt yuv420p10le -x265-params "crf=24:vbv-maxrate=1000:vbv-bufsize=2000:aq-mode=3:colorprim=bt709:colormatrix=bt709:transfer=bt709" -map 0:{media.video_stream} -c:a libfdk_aac -vbr 2 -ac 2 -map 0:{media.audio_stream} "{media.directory_temp}{media.dst_filename}_stop_post.mkv"'

    print(f'### running stop test pre')
    proc_cmd_stop_pre = subprocess.Popen(cmd_stop_pre, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result_cmd_stop_pre = proc_cmd_stop_pre.stdout.read().decode('utf-8')[:-1]
    print(f'### running stop test post')
    proc_cmd_stop_post = subprocess.Popen(cmd_stop_post, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result_cmd_stop_post = proc_cmd_stop_post.stdout.read().decode('utf-8')[:-1]

    logg(6, f'Test conversion done ({media.src_filename_extension})')

