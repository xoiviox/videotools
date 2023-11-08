from videotools.config import DirConfig, OtherConfig
from videotools.models import MediaObj
from videotools.logger import logg

from videotools import usubtitles

import re, os


def compare_test(media):
    print(f'\n### compare_test: {media.title}')

    old_srt_path_main = media.directory_archive + media.dst_filename + '.srt'
    old_srt_path_additional = media.directory_archive + media.dst_filename + '.' + OtherConfig.lang_additional + '.srt'

    new_srt_path_main = media.directory_temp + media.dst_filename + '.srt'
    new_srt_path_additional = media.directory_temp + media.dst_filename + '.' + OtherConfig.lang_additional + '.srt'

    old_tts_path = media.directory_archive + media.dst_filename + '.tts.txt'
    new_tts_path = media.directory_temp + media.dst_filename + '.tts.txt'
    
    print(f'### old_srt_path_main: {old_srt_path_main}')
    print(f'### old_srt_path_additional: {old_srt_path_additional}')
    print(f'### new_srt_path_main: {new_srt_path_main}')
    print(f'### new_srt_path_additional: {new_srt_path_additional}')
    print(f'### old_tts_path: {old_tts_path}')
    print(f'### new_tts_path: {new_tts_path}')
    print(f'')
    
    print(f'\n### old_srt_main vs new_srt_main')
    with open(old_srt_path_main, 'r') as old_srt_file_main:
        old_srt_string_main = old_srt_file_main.read()
    with open(new_srt_path_main, 'r') as new_srt_file_main:
        new_srt_string_main = new_srt_file_main.read()
    compare_srt(srt_to_list(old_srt_string_main), srt_to_list(new_srt_string_main))

    print(f'\n### old_srt_additional vs new_srt_additional')
    with open(old_srt_path_additional, 'r') as old_srt_file_additional:
        old_srt_string_additional = old_srt_file_additional.read()
    with open(new_srt_path_additional, 'r') as new_srt_file_additional:
        new_srt_string_additional = new_srt_file_additional.read()
    compare_srt(srt_to_list(old_srt_string_additional), srt_to_list(new_srt_string_additional))

    print(f'\n### old_tts vs new_tts')
    with open(old_tts_path, 'r') as old_tts_file:
        old_tts_string = old_tts_file.read()
    with open(new_tts_path, 'r') as new_tts_file:
        new_tts_string = new_tts_file.read()
    compare_tts(tts_to_list(old_tts_string), tts_to_list(new_tts_string))
    compare_tts_options(old_tts_string)


def compare_srt(srt_old, srt_new):
    changes_in_srt = False
    if len(srt_old) != len(srt_new):
            changes_in_srt = True
    else:
        for index in range(len(srt_old)):
            if srt_old[index] != srt_new[index]:
                changes_in_srt = True
                break
    print(f'### changes_in_srt: {changes_in_srt}')


def compare_tts(tts_old, tts_new):
    tts_to_delete = []
    for index, item in enumerate(tts_old):
        if item not in tts_new:
            tts_to_delete.append(item)
    print(f'\n### tts_to_delete: {tts_to_delete}')

    tts_to_download = []
    for index, item in enumerate(tts_new):
        if item not in tts_old:
            tts_to_download.append(item)
    print(f'\n### tts_to_download: {tts_to_download}')


def compare_tts_options(tts_string_old):
    changes_in_google_vo = False
    changes_in_vo = False

    regex_google_vo = re.compile(r'^(google_vo_.+)=(.+)$', re.M | re.I)
    regex_vo = re.compile(r'^(vo_.+)=(.+)$', re.M | re.I)

    matches_google_vo_tts_old = [item.groups() for item in regex_google_vo.finditer(tts_string_old)]
    matches_vo_tts_old = [item.groups() for item in regex_vo.finditer(tts_string_old)]

    for item in matches_google_vo_tts_old:
        if (item[0] == 'google_vo_language_code' and item[1] != OtherConfig.google_vo_language_code) or \
            (item[0] == 'google_vo_voice_name' and item[1] != OtherConfig.google_vo_voice_name) or \
            (item[0] == 'google_vo_speaking_rate' and item[1] != str(OtherConfig.google_vo_speaking_rate)) or \
            (item[0] == 'google_vo_pitch' and item[1] != str(OtherConfig.google_vo_pitch)):
            changes_in_google_vo = True

    for item in matches_vo_tts_old:
        if (item[0] == 'vo_max_sentence_gap_long' and item[1] != str(OtherConfig.vo_max_sentence_gap_long)) or \
            (item[0] == 'vo_max_sentence_gap_short' and item[1] != str(OtherConfig.vo_max_sentence_gap_short)) or \
            (item[0] == 'vo_step_down_sentences_gap' and item[1] != str(OtherConfig.vo_step_down_sentences_gap)) or \
            (item[0] == 'vo_min_sentence_gap_long' and item[1] != str(OtherConfig.vo_min_sentence_gap_long)) or \
            (item[0] == 'vo_max_playback_speed' and item[1] != str(OtherConfig.vo_max_playback_speed)) or \
            (item[0] == 'vo_audio_volume_param1' and item[1] != str(OtherConfig.vo_audio_volume_param1)) or \
            (item[0] == 'vo_audio_volume_param2' and item[1] != str(OtherConfig.vo_audio_volume_param2)) or \
            (item[0] == 'vo_audio_volume_min' and item[1] != str(OtherConfig.vo_audio_volume_min)):
            changes_in_vo = True

    return changes_in_google_vo, changes_in_vo


def srt_to_list(srt_string):
    list_str = []
    regex = re.compile(r'(\d.+)+\n(............).-->.(............)\n(.+\n.+\n.+|.+\n.+|.+)*\n', re.M | re.I)
    matches = [item.groups() for item in regex.finditer(srt_string)]
    for item in matches:
        list_str.append(item)
    return list_str


def tts_to_list(tts_string):
    list_tts = []
    regex = re.compile(r'(............) (............) (.) (long|short) (.+)$', re.M | re.I)
    matches = [item.groups() for item in regex.finditer(tts_string)]
    for item in matches:
        list_tts.append(item)
    return list_tts


########################################################################################


def get_all_tts(media, arch_movies = True, arch_series = True, arch_temporary = True, temp_directory = True):
    tmp_list = []
    media_with_tts_list = []

    if arch_movies == True:
        for filename in sorted(os.listdir(DirConfig.fin_meta_movies), key=str.casefold):
            if filename[-3:] in OtherConfig.video_extensions:
                filename = filename[:-4]
                filename_splitted = filename.split('.')
                tts_file_path = DirConfig.d_arch_movies + filename + '/' + filename + '.tts.txt'
                vo_directory_path = DirConfig.d_arch_movies + filename + '/' + filename + '.VO/'
                if os.path.isfile(tts_file_path):
                    tmp_list.append({'tts_file_path' : f'{tts_file_path}', 'vo_directory_path' : f'{vo_directory_path}', 'tts_list' : []})
    
    if arch_series == True:
        for dir_name in sorted(os.listdir(DirConfig.fin_meta_series), key=str.casefold):
            for filename in sorted(os.listdir(DirConfig.fin_meta_series + dir_name), key=str.casefold):
                if filename[-3:] in OtherConfig.video_extensions:
                    filename = filename[:-4]
                    filename_splitted = filename.split('.')
                    if filename_splitted[-1] == 'FHD' or filename_splitted[-1] == 'UHD':
                        tts_file_path = DirConfig.d_arch_series + '.'.join(filename_splitted[:-2]) + '/' + filename + '.tts.txt'
                        vo_directory_path = DirConfig.d_arch_series + '.'.join(filename_splitted[:-2]) + '/' + filename + '.VO/'
                    elif filename_splitted[-1] == 'HDR' or filename_splitted[-1] == 'DHDR':
                        if filename_splitted[-2] == 'FHD' or filename_splitted[-2] == 'UHD':
                            tts_file_path = DirConfig.d_arch_series + '.'.join(filename_splitted[:-3]) + '/' + filename + '.tts.txt'
                            vo_directory_path = DirConfig.d_arch_series + '.'.join(filename_splitted[:-3]) + '/' + filename + '.VO/'
                    if os.path.isfile(tts_file_path):
                        tmp_list.append({'tts_file_path' : f'{tts_file_path}', 'vo_directory_path' : f'{vo_directory_path}', 'tts_list' : []})

    if arch_temporary == True:
        for filename in sorted(os.listdir(DirConfig.d_arch_temporary), key=str.casefold):
            if filename[-7:] == 'tts.txt':
                tts_file_path = DirConfig.d_arch_temporary + filename
                vo_directory_path = DirConfig.d_arch_temporary + filename[:-8] + '.VO/'
                tmp_list.append({'tts_file_path' : f'{tts_file_path}', 'vo_directory_path' : f'{vo_directory_path}', 'tts_list' : []})

    if temp_directory == True:
        for filename in sorted(os.listdir(DirConfig.d_temp), key=str.casefold):
            if filename[-7:] == 'tts.txt' and media.dst_filename != filename.split('/')[-1][:-8]:
                tts_file_path = DirConfig.d_temp + filename
                vo_directory_path = DirConfig.d_temp + filename[:-8] + '.VO/'
                if os.path.isdir(vo_directory_path):
                    tmp_list.append({'tts_file_path' : f'{tts_file_path}', 'vo_directory_path' : f'{vo_directory_path}', 'tts_list' : []})

    for item in tmp_list:
        with open(item['tts_file_path'], 'r') as tts_file:
            tts_string = tts_file.read()
        changes_in_google_vo, changes_in_vo = compare_tts_options(tts_string)
        if changes_in_google_vo == False:
            media_with_tts_list.append({'tts_file_path' : f'{item["tts_file_path"]}', 'vo_directory_path' : f'{item["vo_directory_path"]}', 'tts_list' : tts_to_list(tts_string)})

    return media_with_tts_list
