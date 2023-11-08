import json
import subprocess
import re

from videotools.logger import logg
from videotools.config import OtherConfig

from videotools import utils


########################################################################################


def get_video_info(json_info_ffprobe, json_info_mediainfo, media):
    list_video = []
    for idx in range(len(json_info_ffprobe['streams'])):
        this_stream = json_info_ffprobe['streams'][idx]
        codec_name = this_stream['codec_name']
        if codec_name == 'hevc' or codec_name == 'h264':
            index = this_stream['index']
            default = this_stream['disposition']['default']
            forced = this_stream['disposition']['forced']
            start_time = format(float(this_stream['start_time']), '.3f')
            hdr = None
            dhdr = None
            if 'color_primaries' in this_stream and this_stream['color_primaries'] == 'bt2020':
                hdr = True
            else:
                hdr = False
                dhdr = False
            src_width = this_stream['width']
            src_height = this_stream['height']
            frame_rate = this_stream['r_frame_rate']

            bit_rate = ''
            language = ''
            title = ''
            if 'bit_rate' in this_stream:
                bit_rate = this_stream['bit_rate']

            if bit_rate == '':
                if 'tags' in this_stream:
                    if 'BPS-eng' in this_stream['tags']:
                        bit_rate = this_stream['tags']['BPS-eng']
                    if 'language' in this_stream['tags']:
                        language = this_stream['tags']['language']
                    if 'title' in this_stream['tags']:
                        if this_stream['tags']['title'] != media.src_filename:
                            title = this_stream['tags']['title']

            max_cll = None
            master_display = None
            if hdr == True:
                cmd_md = f'{utils.exec_path("ffprobe")} "{media.src_file_path}" -show_streams -select_streams v:0 -read_intervals "%+#1" -show_frames -show_entries side_data -v quiet -pretty -print_format json -of json'
                proc_cmd_md = subprocess.Popen(cmd_md, shell=True, stdout=subprocess.PIPE)
                result_cmd_md = proc_cmd_md.stdout.read().decode('utf-8')[:-1]
                json_info_ffprobe_cmd_md = json.loads(result_cmd_md)

                master_display_raw = None
                for frame in json_info_ffprobe_cmd_md["packets_and_frames"]:
                    if frame["type"] != "frame" or "side_data_list" not in frame:
                        continue
                    for item in frame["side_data_list"]:
                        if not master_display_raw and item["side_data_type"] == "Mastering display metadata":
                            master_display_raw = item
                        if item["side_data_type"] == "Content light level metadata":
                            max_cll = f'{item["max_content"]},{item["max_average"]}'
                            if max_cll == '0,0':
                                max_cll = None

                if not master_display_raw:
                    master_display_raw = {'side_data_type': 'Mastering display metadata', 'red_x': '34000/50000', 'red_y': '16000/50000', 'green_x': '13250/50000', 'green_y': '34500/50000',
                                        'blue_x': '7500/50000', 'blue_y': '3000/50000', 'white_point_x': '15635/50000', 'white_point_y': '16450/50000',
                                        'min_luminance': '50/10000', 'max_luminance': '40000000/10000'}
                    logg(7, 'warning: ',  'guessing mastering display metadata')

                cmd_dhdr = f'{utils.exec_path("ffmpeg")} -loglevel panic -i "{media.src_file_path}" -map 0:{index} -c copy -vbsf hevc_mp4toannexb -f hevc - | {utils.exec_path("hdr10plus_tool")} --verify extract -'
                proc_dhdr = subprocess.Popen(cmd_dhdr, shell=True, stdout=subprocess.PIPE)
                result_dhdr = proc_dhdr.stdout.read().decode('utf-8')[:-1]
                if result_dhdr.find('Dynamic HDR10+ metadata detected.') != -1:
                    dhdr = True
                else:
                    dhdr = False

                for key in master_display_raw.keys():
                    master_display_raw[key] = master_display_raw[key].split("/")[0]

                master_display = 'G(%s,%s)B(%s,%s)R(%s,%s)WP(%s,%s)L(%s,%s)' % (master_display_raw['green_x'], master_display_raw['green_y'], master_display_raw['blue_x'], master_display_raw['blue_y'],
                                master_display_raw['red_x'],  master_display_raw['red_y'], master_display_raw['white_point_x'], master_display_raw['white_point_y'], master_display_raw['max_luminance'],
                                master_display_raw['min_luminance'])

            stream_size = ''
            duration = ''
            for item in json_info_mediainfo['media']['track']:
                if item['@type'] == 'Video' and item['StreamOrder'] == str(index):
                    if dhdr == True and item['HDR_Format'] and item['HDR_Format'] == 'SMPTE ST 2094 App 4':
                        if 'HDR_Format_Compatibility' not in item:
                            dhdr = False
                    if 'Duration' in item:
                        duration = format(float(item["Duration"]), '.3f')
                    if 'StreamSize' in item:
                        stream_size = item["StreamSize"]
                        stream_size = format(int(stream_size) / 1024 ** 3, '.3f')
                    if bit_rate == '':
                        if 'BitRate' in item:
                            bit_rate = item["BitRate"]

            if bit_rate != '':
                bit_rate = format(int(bit_rate) / 1000000, '.3f')

            list_video.append({'index': index, 'codec_name': codec_name, 'language': language, 'stream_size': stream_size, 'bit_rate': bit_rate, 'duration': duration, 'start_time': start_time,
                            'default': default, 'forced': forced, 'hdr': hdr, 'dhdr': dhdr, 'src_width': src_width, 'src_height': src_height, 'frame_rate': frame_rate, 'master_display': master_display,
                            'max_cll': max_cll, 'title': title})
    
    media.list_video = json.dumps(list_video)
    if media.video_stream != None: utils.setup_video(media, media.video_stream)
    else: utils.setup_video(media, 'initial')


def get_audio_info(json_info_ffprobe, json_info_mediainfo, media):
    list_audio = []
    for idx in range(len(json_info_ffprobe['streams'])):
        this_stream = json_info_ffprobe['streams'][idx]
        index = this_stream['index']
        codec_name = this_stream['codec_name']
        channels = this_stream['channels']
        start_time = format(float(this_stream['start_time']), '.3f')
        default = this_stream['disposition']['default']
        forced = this_stream['disposition']['forced']
        
        bit_rate = ''
        if 'bit_rate' in this_stream:
            bit_rate = this_stream['bit_rate']
        if bit_rate == '':
            if 'tags' in this_stream:
                if 'BPS-eng' in this_stream['tags']:
                    bit_rate = this_stream['tags']['BPS-eng']
        language = ''
        if 'tags' in this_stream:
            if 'language' in this_stream['tags']:
                language = this_stream['tags']['language']
        title = ''
        if 'tags' in this_stream:
            if 'title' in this_stream['tags']:
                if this_stream['tags']['title'] != media.src_filename:
                    title = this_stream['tags']['title']

        format_commercial = ''
        duration = ''
        bitrate_mode = ''
        stream_size = ''
        atmos = 0
        for item in json_info_mediainfo['media']['track']:
            if 'StreamOrder' in item:
                if int(item['StreamOrder']) == index:
                    if 'Format_Commercial_IfAny' in item:
                        format_commercial = item["Format_Commercial_IfAny"]
                        if 'Atmos' in format_commercial:
                            atmos = 1
                    if 'Duration' in item:
                        duration = format(float(item["Duration"]), '.3f')
                    if 'BitRate_Mode' in item:
                        bitrate_mode = item["BitRate_Mode"]
                    if 'StreamSize' in item:
                        stream_size = item["StreamSize"]
                        stream_size = format(int(stream_size) / 1024 ** 3, '.3f')
                    if bit_rate == '':
                        if 'BitRate' in item:
                            bit_rate = item["BitRate"]
        if bit_rate != '':
            bit_rate = format(int(bit_rate) / 1000000, '.3f')

        list_audio.append({'index': index, 'codec_name': codec_name, 'language': language, 'channels': channels, 'stream_size': stream_size, 'bitrate_mode': bitrate_mode,
                                'bit_rate': bit_rate, 'duration': duration, 'start_time': start_time, 'atmos': atmos, 'default': default, 'forced': forced, 'title': title})
    
    media.list_audio = json.dumps(list_audio)
    if media.audio_stream != None: utils.setup_audio(media, media.audio_stream)
    else: utils.setup_audio(media, 'initial')


def get_subtitle_info(json_info_ffprobe, json_info_mediainfo, media):
    list_subtitle_main = []
    list_subtitle_additional = []
    for idx in range(len(json_info_ffprobe['streams'])):
        this_stream = json_info_ffprobe['streams'][idx]
        if this_stream['codec_name'] == 'subrip':
            index = this_stream['index']
            default = this_stream['disposition']['default']
            forced = this_stream['disposition']['forced']

            language = ''
            if 'tags' in this_stream:
                if 'language' in this_stream['tags']:
                    language = this_stream['tags']['language']
                title = ''
                if 'title' in this_stream['tags']:
                    title = this_stream['tags']['title']
                bps = ''
                if 'BPS-eng' in this_stream['tags']:
                    bps = this_stream['tags']['BPS-eng']
                frames = ''
                if 'NUMBER_OF_FRAMES-eng' in this_stream['tags']:
                    frames = this_stream['tags']['NUMBER_OF_FRAMES-eng']

                list_lang = {'index': index, 'language': language, 'default': default, 'forced': forced, 'bps': bps, 'frames': frames, 'title': title}
                if language == OtherConfig.lang_main: list_subtitle_main.append(list_lang)
                elif language == OtherConfig.lang_additional: list_subtitle_additional.append(list_lang)

    media.list_subtitle_main = json.dumps(list_subtitle_main)
    if media.subtitle_stream_main != None:
        utils.setup_sub_lang(media, media.subtitle_stream_main, 'main')
    else:
        utils.setup_sub_lang(media, 'initial', 'main')

    media.list_subtitle_additional = json.dumps(list_subtitle_additional)
    if media.subtitle_stream_additional != None:
        utils.setup_sub_lang(media, media.subtitle_stream_additional, 'additional')
    else:
        utils.setup_sub_lang(media, 'initial', 'additional')


########################################################################################


def set_filename_suff(media):
    if (media.src_width <= 1920 and media.src_width >= 1916) or media.src_height == 1080:
        if media.dhdr == True and media.hdr == True:
            media.dst_filename = media.base_filename + '.FHD.DHDR'
            media.dst_directory = media.dst_directory + '.FHD.DHDR'
        elif media.dhdr == False and media.hdr == True:
            media.dst_filename = media.base_filename + '.FHD.HDR'
            media.dst_directory = media.dst_directory + '.FHD.HDR'
        elif media.dhdr == False and media.hdr == False:
            media.dst_filename = media.base_filename + '.FHD'
            media.dst_directory = media.dst_directory + '.FHD'

    if media.src_width == 3840 or media.src_height == 2160:
        if media.dhdr == True and media.hdr == True:
            media.dst_filename = media.base_filename + '.UHD.DHDR'
            media.dst_directory = media.dst_directory + '.UHD.DHDR'
        elif media.dhdr == False and media.hdr == True:
            media.dst_filename = media.base_filename + '.UHD.HDR'
            media.dst_directory = media.dst_directory + '.UHD.HDR'
        elif media.dhdr == False and media.hdr == False:
            media.dst_filename = media.base_filename + '.UHD'
            media.dst_directory = media.dst_directory + '.UHD'
    
    if media.src_width == 1280 or media.src_height == 720:
        media.dst_filename = media.base_filename + '.HD'
        media.dst_directory = media.dst_directory + '.HD'
        media.media_dst = 'temporary'


def probe_file(media):
    cmd_probe_ffprobe_video = f'{utils.exec_path("ffprobe")} -v quiet -of json -show_format -show_streams -select_streams v -i "{media.src_file_path}"'
    proc_probe_ffprobe_video = subprocess.Popen(cmd_probe_ffprobe_video, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result_probe_ffprobe_video = proc_probe_ffprobe_video.stdout.read().decode('utf-8')[:-1]
    json_info_ffprobe_video = json.loads(result_probe_ffprobe_video)

    cmd_probe_ffprobe_audio = f'{utils.exec_path("ffprobe")} -v quiet -of json -show_format -show_streams -select_streams a -i "{media.src_file_path}"'
    proc_probe_ffprobe_audio = subprocess.Popen(cmd_probe_ffprobe_audio, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result_probe_ffprobe_audio = proc_probe_ffprobe_audio.stdout.read().decode('utf-8')[:-1]
    json_info_ffprobe_audio = json.loads(result_probe_ffprobe_audio)

    cmd_probe_ffprobe_subtitle = f'{utils.exec_path("ffprobe")} -v quiet -of json -show_format -show_streams -select_streams s -i "{media.src_file_path}"'
    proc_probe_ffprobe_subtitle = subprocess.Popen(cmd_probe_ffprobe_subtitle, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result_probe_ffprobe_subtitle = proc_probe_ffprobe_subtitle.stdout.read().decode('utf-8')[:-1]
    json_info_ffprobe_subtitle = json.loads(result_probe_ffprobe_subtitle)

    cmd_probe_mediainfo = f'{utils.exec_path("mediainfo")} --Output=JSON "{media.src_file_path}"'
    probe_mediainfo = subprocess.Popen(cmd_probe_mediainfo, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    mediainfo_stdout, mediainfo_stderr = probe_mediainfo.communicate()
    json_info_mediainfo = json.loads(mediainfo_stdout.decode('utf-8')[:-1])

    get_video_info(json_info_ffprobe_video, json_info_mediainfo, media)
    get_audio_info(json_info_ffprobe_audio, json_info_mediainfo, media)
    get_subtitle_info(json_info_ffprobe_subtitle, json_info_mediainfo, media)

    set_filename_suff(media)

    media.start_at = 0
    media.stop_at = 0

    return json_info_ffprobe_video, json_info_ffprobe_audio, json_info_ffprobe_subtitle, json_info_mediainfo
    

########################################################################################


def check_lenght(file_path):
    cmd = f'{utils.exec_path("ffprobe")} -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
    proc_cmd = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    result_cmd = proc_cmd.stdout.read().decode('utf-8')[:-1]
    print(f'000 cmd = {cmd}')
    return float(result_cmd)

