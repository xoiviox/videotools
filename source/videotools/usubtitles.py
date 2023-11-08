from videotools.config import DirConfig, OtherConfig
from videotools.logger import logg
from videotools.dbing import add_to_db
from flask_socketio import emit

import subprocess
import os
import shutil
import re
import datetime


def subtitle_process(media, lang, time_drift = 0):
    if lang == 'main':
        filename = media.src_filename + '.srt'
        dst_filename = f'{media.dst_filename}.srt'
        tts_list_filename = f'{media.dst_filename}.tts.txt'
    elif lang == 'additional':
        filename = media.src_filename + '.' + OtherConfig.lang_additional + '.srt'
        dst_filename = f'{media.dst_filename}.{OtherConfig.lang_additional}.srt'

    if os.path.isfile(media.directory + filename):
        if check_subtitles_read(media.directory, filename) == 1:
            subtitles_list = fix_subtitles_format(media, lang)
            new_body_main_dir, new_body_temp_dir, tts_body_temp_dir = recreate_subtitles(media, subtitles_list, time_drift)

            with open(media.directory + filename, 'w') as text_file:
                text_file.write(new_body_main_dir)
            with open(media.directory_temp + dst_filename, 'w') as text_file:
                text_file.write(new_body_temp_dir)
            
            if lang == 'main':
                tts_list = make_tts(media, tts_body_temp_dir)
                with open(media.directory_temp + tts_list_filename, 'w') as text_file:
                    text_file.write(tts_list)


def check_subtitles_read(directory, filename):
    file_path = directory + '/' + filename
    try:
        with open(file_path, 'r') as test_file:
            test_file.read() + '\n\n'
            return 1
    except:
        try:
            cmd_conv_s = f'iconv -f windows-1250 -t utf-8 "{file_path}" -o "{file_path}.tmp" '
            cmd_conv_s = cmd_conv_s + f'&& \\\nrm "{file_path}" '
            cmd_conv_s = cmd_conv_s + f'&& \\\nmv "{file_path}.tmp" "{file_path}"'
            subprocess.run(cmd_conv_s, shell=True, check=True, stderr=subprocess.DEVNULL)
            logg(3, f'File read error, converted successfully ({filename})')
            return 1
        except:
            logg(3, f'File read error, convert error ({filename})')
            cmd_final = f'rm "{file_path}.tmp"'
            try:
                subprocess.run(cmd_final, shell=True, check=True, stderr=subprocess.DEVNULL)
            except:
                logg(3, f'File remove error ({filename})')
            return 0


def download_subtitles(media, lang):
    add_to_db(media)
    emit('media_update',  media.as_dict())
    if lang == 'main':
        cmd_qnapi = f'qnapi -c -d -l {OtherConfig.lang_main} -f SRT -q "{media.src_file_path}"'
        try:
            logg(2, f'Finding {OtherConfig.lang_main} subtitles with qnapi ({media.src_filename_extension})')
            subprocess.run(cmd_qnapi, shell=True, check=True, stderr=subprocess.DEVNULL)  ### wersja bez outputu
            logg(2, f'{OtherConfig.lang_main.title()} subtitles found with qnapi ({media.src_filename_extension})')
            subtitle_process(media, lang)
            media.subtitle_main_state = 'downloaded'
            media.download_voiceover_state = 'not_downloaded'
            media.create_voiceover_state = 'not_created'
            media.convert_audio_voiceover_state = 'not_converted'
            media.mux_state = 'not_muxed'
        except:
            logg(2, f'No {OtherConfig.lang_main} subtitles found with qnapi ({media.src_filename_extension})')
            media.subtitle_main_state = 'not_downloaded'
        add_to_db(media)
        emit('media_update',  media.as_dict())
    elif lang == 'additional':
        cmd_qnapi = f'qnapi -c -d -l {OtherConfig.lang_additional} -f SRT -q "{media.src_file_path}"'
        if os.path.isfile(media.directory + media.src_filename + '.srt'):
            shutil.move(media.directory + media.src_filename + '.srt',  media.directory + media.src_filename + '.srt.tmp')
        try:
            logg(2, f'Finding {OtherConfig.lang_additional} subtitles with qnapi ({media.src_filename_extension})')
            subprocess.run(cmd_qnapi, shell=True, check=True, stderr=subprocess.DEVNULL)  ### wersja bez outputu
            logg(2, f'{OtherConfig.lang_additional.title()} subtitles found with qnapi ({media.src_filename_extension})')
            shutil.move(media.directory + media.src_filename + '.srt',  media.directory + media.src_filename + '.eng.srt')
            subtitle_process(media, lang)
            media.subtitle_additional_state = 'downloaded'
            media.mux_state = 'not_muxed'
        except:
            logg(2, f'No {OtherConfig.lang_additional} subtitles found with qnapi ({media.src_filename_extension})')
            media.subtitle_additional_state = 'not_downloaded'
        add_to_db(media)
        emit('media_update',  media.as_dict())
        if os.path.isfile(media.directory + media.src_filename + '.srt.tmp'):
            shutil.move(media.directory + media.src_filename + '.srt.tmp',  media.directory + media.src_filename + '.srt')


def fix_subtitles_format(media, lang):
    subtitles_list = []
    if lang == 'main':
        filename = media.src_filename + '.srt'
    elif lang == 'additional':
        filename = media.src_filename + '.' + OtherConfig.lang_additional + '.srt'

    with open(media.directory + filename, 'r') as subtitle_file:
        subtitle_file_content = subtitle_file.read() + '\n\n'
        regex = re.compile(r'\d+\n(............).-->.(............)\n(.+\n.+\n.+|.+\n.+|.+|\n.+\n.+\n.+|\n.+\n.+|\n.+)*\n', re.M | re.I)
        matches = [item.groups() for item in regex.finditer(subtitle_file_content)]
        subtitle_format = 'srt'
        if len(matches) == 0:
            regex = re.compile(r'\[(\d+)\]\[(\d+)\](.+)$', re.M | re.I)
            matches = [item.groups() for item in regex.finditer(subtitle_file_content)]
            subtitle_format = 'mpl'
            if len(matches) == 0:
                regex = re.compile(r'\{(\d+)\}\{(\d+)\}(.+)$', re.M | re.I)
                matches = [item.groups() for item in regex.finditer(subtitle_file_content)]
                subtitle_format = 'sub'
                if len(matches) == 0:
                    subtitle_format = 'NONE'

        frame_rate = int(media.video_frame_rate.split('/')[0]) / int(media.video_frame_rate.split('/')[1])
        for idx, item in enumerate(matches):
            if item[2] != None:
                if '\n' in item[2][:2]:
                    as_list = list(item)
                    as_list[2] = as_list[2][1:]
                    item = tuple(as_list)
                if item[2] == None:
                    logg(1, f'Empty line detected ({filename})  idx = {idx}, item = {item}')
                elif (item[0] == '0' and item[1] == '0') or (item[0] == '1' and item[1] == '1'):
                    frame_rate = float(item[2])
                    if frame_rate > 23 and frame_rate < 26:
                        logg(3, f'Subtitles have information about framerate: {item[2]} ({filename})')
                else:
                    single_subtitle = item[2]
                    time_start = ''
                    time_stop = ''
                    if subtitle_format == 'srt':
                        time_start = item[0]
                        time_stop = item[1]
                    elif subtitle_format == 'mpl':
                        s, ss = divmod(int(item[0]), 10)
                        m, s = divmod(s, 60)
                        h, m = divmod(m, 60)
                        time_start = '{:02d}:{:02d}:{:02d},{:03d}'.format(h, m, s, ss * 100)
                        s, ss = divmod(int(item[1]), 10)
                        m, s = divmod(s, 60)
                        h, m = divmod(m, 60)
                        time_stop = '{:02d}:{:02d}:{:02d},{:03d}'.format(h, m, s, ss * 100)
                    elif subtitle_format == 'sub':
                        second_start = int(item[0]) / frame_rate
                        second_stop = int(item[1]) / frame_rate
                        time_split_start = str(second_start).split('.')
                        time_split_stop = str(second_stop).split('.')
                        m, s = divmod(int(time_split_start[0]), 60)
                        h, m = divmod(m, 60)
                        time_start = '{:02d}:{:02d}:{:02d},{:03d}'.format(h, m, s, int(float('0.' + time_split_start[1]) * 1000))
                        m, s = divmod(int(time_split_stop[0]), 60)
                        h, m = divmod(m, 60)
                        time_stop = '{:02d}:{:02d}:{:02d},{:03d}'.format(h, m, s, int(float('0.' + time_split_stop[1]) * 1000))

                    single_line = [time_start, time_stop, single_subtitle]
                    subtitles_list.append(single_line)
        subtitles_list = fix_subtitles_body(media, subtitles_list, filename)
        logg(3, f'Subtitle format (oryginally "{subtitle_format}") and body fixed ({filename})')
    return subtitles_list


def fix_subtitles_body(media, subtitles_list, filename):
    with open(DirConfig.d_conf + 'fix_list_subtitle.txt', 'r') as f_subtitle_clean:
        subtitle_clean_content = f_subtitle_clean.read()

    subtitle_clean_list = subtitle_clean_content.split('\n')
    subtitle_to_remove = []
    for item in subtitle_clean_list:
        if item != '':
            subtitle_to_remove.append(item)
    new_subtitle_list = []
    for idx_slist, item_slist in enumerate(subtitles_list):
        sub = item_slist[2].replace('…', '...').replace('. . .', '...').replace('\xa0', ' ').replace('|', '\n').replace(';', ',').replace('–', '-')

        sub = re.sub('{.*an[0-9]}', '', sub)
        sub = re.sub('<.*font.*>', '', sub)

        sub = sub.replace('{y:i}', '<i>').replace('{Y:i}', '<i>').replace('{Y:I}', '<i>').replace('{y:I}', '<i>').replace('{y:b}', '').replace('{Y:b}', '').replace('{Y:B}', '').replace('{y:B}', '')
        sub = sub.replace('<b>', '').replace('</b>', '').replace('<I>', '<i>').replace('</I>', '</i>').replace('<i><i>', '<i>').replace('</i></i>', '</i>')
        sub = sub.replace(',,', '"')
        sub = sub.replace('...?', '...')
        sub = sub.replace('...!', '...')
        sub = sub.replace('\'\'', '"')

        for pos in re.finditer('^/', sub): # do poprawki # zmiana slasha na wiecej niz jeden znak psuje 2 linie stringa
            if sub[pos.end():pos.end() + 2] != 'i>':
                sub = sub[:pos.start()] + '\\' + sub[pos.end():]
        sub = sub.replace('\\', '<i>')
        for pos in re.finditer('\n/', sub):
            sub = sub[:pos.start()] + '\\' + sub[pos.end():]
        sub = sub.replace('\\', '\n<i>')
        for pos in re.finditer(' /', sub):
            sub = sub[:pos.start()] + '\\' + sub[pos.end():]
        sub = sub.replace('\\', '\n<i>')

        found_ita = sub.find('<i>')
        if found_ita != -1:
            sub_to_fix = sub.split('\n')
            for italic_idx, ita_item in enumerate(sub_to_fix):
                pos_of_ita = ita_item.find('<i>')

                if pos_of_ita == 0:
                    if ita_item[-4:] == '</i>':
                        sub_to_fix[italic_idx] = sub_to_fix[italic_idx]
                    elif ita_item[-4:] != '</i>':
                        sub_to_fix[italic_idx] = sub_to_fix[italic_idx] + '</i>'

                found_ita_close = ita_item.find('</i>')
                if found_ita_close == len(ita_item) - 4 and ita_item[:3] != '<i>':
                    sub_to_fix[italic_idx] = '<i>' + sub_to_fix[italic_idx]

                sub = '\n'.join(sub_to_fix)
            
        for idx_sunwanted, item_sunwanted in enumerate(subtitle_to_remove):
            find_unwanted = re.compile(item_sunwanted, re.M)
            matches = find_unwanted.search(sub)
            if matches:
                logg(0, f'Removed line with word: {item_sunwanted} ({filename})')
                break
            if not matches and idx_sunwanted == len(subtitle_to_remove) - 1:
                single_line = [item_slist[0], item_slist[1], sub]
                new_subtitle_list.append(single_line)

    
    endfix_sub_list = []
    for idx_line,  line in enumerate(new_subtitle_list):
        text_item = line[2].split('\n')
        fixed_line = ''
        for idx_sentence,  sentence in enumerate(text_item):
            regex_noi = re.compile(r' \"$')
            regex_wi = re.compile(r' \"</i>$')
            matches_noi = regex_noi.search(sentence)
            matches_wi = regex_wi.search(sentence)
            if matches_noi:
                sentence = sentence[:-2] + '"'
            elif matches_wi:
                sentence = sentence[:-6] + '"</i>'
    
            regex_2space = re.compile(r'  $')
            regex_1space = re.compile(r' $')
            regex_2spacei = re.compile(r'  </i>$')
            regex_1spacei = re.compile(r' </i>$')
            matches_2space = regex_2space.search(sentence)
            matches_1space = regex_1space.search(sentence)
            matches_2spacei = regex_2spacei.search(sentence)
            matches_1spacei = regex_1spacei.search(sentence)
            if matches_2space:
                sentence = sentence[:-2]
            elif matches_1space:
                sentence = sentence[:-1]
            elif matches_2spacei:
                sentence = sentence[:-6] + '</i>'
            elif matches_1spacei:
                sentence = sentence[:-5] + '</i>'
            
            regex_dots1 = re.compile(r'^- \.\.\. ')
            regex_dots2 = re.compile(r'^\.\.\. ')
            regex_dots3 = re.compile(r'^<i>- \.\.\. ')
            regex_dots4 = re.compile(r'^<i>\.\.\. ')
            matches_dots1 = regex_dots1.search(sentence)
            matches_dots2 = regex_dots2.search(sentence)
            matches_dots3 = regex_dots3.search(sentence)
            matches_dots4 = regex_dots4.search(sentence)
            if matches_dots1:
                sentence = '- ...' + sentence[6:]
            elif matches_dots2:
                sentence = '...' + sentence[4:]
            elif matches_dots3:
                sentence = '<i>- ...' + sentence[9:]
            elif matches_dots4:
                sentence = '<i>...' + sentence[7:]

            regex_test = re.compile((r'^-[a-zA-Z]'))
            matches_test = regex_test.search(sentence)
            if matches_test:
                sentence = '- ' +  sentence[1:]

            if idx_sentence == 0:
                fixed_line = sentence
            else:
                fixed_line = fixed_line + '\n' + sentence
        
        endfix_sub_list.append([line[0], line[1], fixed_line])

    return endfix_sub_list


def recreate_subtitles(media, subtitles_list, time_drift):
    tts_body_temp_dir = []

    new_body_main_dir = ''
    new_body_temp_dir = ''

    sub_num_main_dir = 1
    sub_num_temp_dir = 1
    for item in subtitles_list:
        tmp_time = (datetime.datetime.strptime(item[0], '%H:%M:%S,%f') - datetime.datetime.strptime('00:00:00,000', '%H:%M:%S,%f')).total_seconds()

        tmp_sub_time_start = (datetime.datetime.strptime(item[0], '%H:%M:%S,%f') - datetime.datetime.strptime('00:00:00,000', '%H:%M:%S,%f'))
        tmp_sub_time_stop = (datetime.datetime.strptime(item[1], '%H:%M:%S,%f') - datetime.datetime.strptime('00:00:00,000', '%H:%M:%S,%f'))

        if time_drift < 0 and tmp_time + time_drift < 0:
            sub_time_start = datetime.datetime.strptime('00:00:00,000', '%H:%M:%S,%f') - datetime.datetime.strptime('00:00:00,000', '%H:%M:%S,%f')
            sub_time_stop = tmp_sub_time_stop - tmp_sub_time_start
        else:
            sub_time_start = tmp_sub_time_start + datetime.timedelta(seconds = time_drift)
            sub_time_stop = tmp_sub_time_stop + datetime.timedelta(seconds = time_drift)

        new_sub_time_start = '0' + str(sub_time_start - datetime.timedelta(seconds=float(media.start_at))).replace('.',  ',')
        new_sub_time_stop = '0' + str(sub_time_stop - datetime.timedelta(seconds=float(media.start_at))).replace('.',  ',')

        new_sub_time_start = fix_timestamp(new_sub_time_start)
        new_sub_time_stop = fix_timestamp(new_sub_time_stop)

        main_time_start = '0' + str(sub_time_start).replace('.',  ',')
        main_time_stop = '0' + str(sub_time_stop).replace('.',  ',')

        main_time_start = fix_timestamp(main_time_start)
        main_time_stop = fix_timestamp(main_time_stop)

        new_body_main_dir = new_body_main_dir + str(sub_num_main_dir) + '\n'
        new_body_main_dir = new_body_main_dir + main_time_start + ' --> ' + main_time_stop + '\n'
        new_body_main_dir = new_body_main_dir + item[2] + '\n\n'
        sub_num_main_dir += 1

        temp_time_start = new_sub_time_start
        temp_time_stop = new_sub_time_stop

        if tmp_time > float(media.start_at):
            if media.stop_at == 0:
                new_body_temp_dir = new_body_temp_dir + str(sub_num_temp_dir) + '\n'
                new_body_temp_dir = new_body_temp_dir + temp_time_start + ' --> ' + temp_time_stop + '\n'
                new_body_temp_dir = new_body_temp_dir + item[2] + '\n\n'
                sub_num_temp_dir += 1
                tts_body_temp_dir.append([temp_time_start, temp_time_stop, item[2]])
                
            elif tmp_time < float(media.stop_at):
                new_body_temp_dir = new_body_temp_dir + str(sub_num_temp_dir) + '\n'
                new_body_temp_dir = new_body_temp_dir + temp_time_start + ' --> ' + temp_time_stop + '\n'
                new_body_temp_dir = new_body_temp_dir + item[2] + '\n\n'
                sub_num_temp_dir += 1
                tts_body_temp_dir.append([temp_time_start, temp_time_stop, item[2]])

    return new_body_main_dir, new_body_temp_dir, tts_body_temp_dir


def fix_timestamp(timestamp):
    if len(timestamp) == 15:
        timestamp = timestamp[:-3]
        return(timestamp)
    elif len(timestamp) == 8:
        timestamp = timestamp + ',000'
        return(timestamp)
    elif len(timestamp) == 12:
        return(timestamp)


def make_tts(media, subtitles_list):
    separators = '\.|\,|\:|\!|\?|Tak,|Nie,|Ok,|OK,'

    tts_list = []
    tts_string_to_write = ''

    tts_string_to_write = tts_string_to_write + f'google_vo_language_code={OtherConfig.google_vo_language_code}\n'
    tts_string_to_write = tts_string_to_write + f'google_vo_voice_name={OtherConfig.google_vo_voice_name}\n'
    tts_string_to_write = tts_string_to_write + f'google_vo_speaking_rate={OtherConfig.google_vo_speaking_rate}\n'
    tts_string_to_write = tts_string_to_write + f'google_vo_pitch={OtherConfig.google_vo_pitch}\n'

    tts_string_to_write = tts_string_to_write + f'vo_max_sentence_gap_long={OtherConfig.vo_max_sentence_gap_long}\n'
    tts_string_to_write = tts_string_to_write + f'vo_max_sentence_gap_short={OtherConfig.vo_max_sentence_gap_short}\n'
    tts_string_to_write = tts_string_to_write + f'vo_step_down_sentences_gap={OtherConfig.vo_step_down_sentences_gap}\n'
    tts_string_to_write = tts_string_to_write + f'vo_min_sentence_gap_long={OtherConfig.vo_min_sentence_gap_long}\n'
    tts_string_to_write = tts_string_to_write + f'vo_max_playback_speed={OtherConfig.vo_max_playback_speed}\n'
    tts_string_to_write = tts_string_to_write + f'vo_audio_volume_param1={OtherConfig.vo_audio_volume_param1}\n'
    tts_string_to_write = tts_string_to_write + f'vo_audio_volume_param2={OtherConfig.vo_audio_volume_param2}\n'
    tts_string_to_write = tts_string_to_write + f'vo_audio_volume_min={OtherConfig.vo_audio_volume_min}\n'

    fix_list = []
    with open(DirConfig.d_conf + 'fix_list_tts.txt', 'r') as f_fix_list_tts:
        tmp = f_fix_list_tts.read()
        tmp = tmp.split('\n')
        for item in tmp:
            if item != '':
                item = item.split(':')
                item_left = item[0].split(';')
                item_right = item[1].split(';')
                fix_list.append(item_left + item_right)

    for subtitle_number, s_item in enumerate(subtitles_list):
        time_start = s_item[0].replace(':', '.').replace(',', '.')
        time_stop = s_item[1].replace(':', '.').replace(',', '.')
        body = s_item[2]

        body = body.replace('<i>', '').replace('</i>', '').replace('–', '-').replace('- ', '').replace('- ', '').replace('\n', ' ').replace('"', '').replace('<<', '').replace('*', '')
        body = body.replace('>>', '').replace('...', '.').replace('!!!', '!').replace('???', '?').replace(';', '').replace('„', '').replace('”', '')
        body = body.replace('[', '').replace(']', '').replace('(', '').replace(')', '')
        body = body.replace('. ...', '. ').replace('! ...', '! ').replace('? ...', '? ')
        body = body.replace('?!', '?').replace('!?', '?')
        body = body.replace('♩', '').replace('♪', '').replace('♬', '').replace('♫', '')

        upper_test = body.replace('.', '').replace(',', '').replace('!', '').replace('?', '').replace(':', '').replace(';', '').replace('-', '').split()
        upper_result = []
        counter = 0
        for item in upper_test:
            if item.isupper():
                counter += 1
            if not item.isdigit():
                upper_result.append(item)
        if len(upper_result) == counter:
            body = body[0].upper() + body[1:].lower()

        for fix_item in fix_list:
            if fix_item[0] == 'all':
                body = body.replace(fix_item[2], fix_item[3])
            if fix_item[0] == 'serie' and media.video_type == 'serie':
                if fix_item[1] == 'all' or fix_item[1] == media.base_directory:
                    body = body.replace(fix_item[2], fix_item[3])
            if fix_item[0] == 'movie' and media.video_type == 'movie':
                if fix_item[1] == 'all' or fix_item[1] == media.base_directory:
                    body = body.replace(fix_item[2], fix_item[3])

        if body[:1] == '.':
            body = body[1:]
        
        separator_list = []
        find_separator = re.finditer(separators, body)
        for index, item in enumerate(find_separator):
            separator_list.append([item.start(), item.end()])    

        for index, item in enumerate(separator_list):
            if index + 1 == len(separator_list) and len(body) == item[1]:
                separator_list.remove(item)
                if body[-1] != '?':
                    body = body[:-1]

        corrected_separator_list = []
        for index, item in enumerate(separator_list):
            if (item[1] - item[0] == 1) and (body[item[0]] == '.' or body[item[0]] == ',' or body[item[0]] == ':'):
                num_pre = False
                num_post = False
                big_char_pre = False
                big_char_post = False

                if body[item[0] - 1].isdigit():
                    num_pre = True
                if item[1] < len(body):
                    if body[item[1]].isdigit():
                        num_post = True
                
                if body[item[0] - 1].isupper():
                    big_char_pre = True
                if item[1] < len(body):
                    if body[item[1]].isupper():
                        big_char_post = True

                if (num_pre == False and num_post == False) or (num_pre == True and num_post == False) or (num_pre == False and num_post == True):
                    if body[item[0]] == ',' or body[item[0]] == ':':
                        corrected_separator_list.append(item)
                    if big_char_pre == True and big_char_post == True:
                        corrected_separator_list.append(item)

        new_sentence = ''
        for index, item in enumerate(corrected_separator_list):
            if index == 0:
                new_sentence = body[:item[0]]
            else:
                new_sentence = new_sentence + body[corrected_separator_list[index - 1][1]:item[0]]
            if index + 1 == len(corrected_separator_list):
                new_sentence = new_sentence + body[corrected_separator_list[index][1]:]

        if new_sentence != '':
            body = new_sentence

        new_list = []
        final_separator_list = []
        final_find_separator = re.finditer(separators, body)
        for index, item in enumerate(final_find_separator):
            final_separator_list.append([item.start(), item.end()])

        final_corrected_separator_list = []
        for index, item in enumerate(final_separator_list):
            num_pre = False
            num_post = False
            if body[item[0] - 1].isdigit():
                num_pre = True
            if item[1] < len(body):
                if body[item[1]].isdigit():
                    num_post = True
            if num_pre == True and num_post == True:
                pass
            else:
                final_corrected_separator_list.append(item)

        for index, item in enumerate(final_corrected_separator_list):
            if item[1] - item[0] == 4 or item[1] - item[0] == 3:
                if index == 0:
                    new_list.append(['short', body[:item[1] - 1]])
                else:
                    new_list.append(['short', body[final_corrected_separator_list[index -1][1] + 1:item[1] - 1]])

            elif item[1] - item[0] == 1 and body[item[0]:item[1]] == '?' or body[item[0]:item[1]] == '!' or body[item[0]:item[1]] == '.':
                if index == 0:
                    if body[item[1] - 1:item[1]] == '?':
                        new_list.append(['long', body[:item[1]]])
                    else:
                        new_list.append(['long', body[:item[1] - 1]])
                else:
                    if body[item[1] - 1:item[1]] == '?':
                        new_list.append(['long', body[final_corrected_separator_list[index -1][1] + 1:item[1]]])
                    else:
                        new_list.append(['long', body[final_corrected_separator_list[index -1][1] + 1:item[0]]])

            if index + 1 == len(final_corrected_separator_list):
                if item[1] < len(body):
                    new_list.append(['long', body[item[1] + 1:len(body)]])

        if len(final_corrected_separator_list) == 0:
            body = [['long', body]]

        if new_list != []:
            body = new_list

        for index, item in enumerate(body):
            tts_string_to_write = f'{tts_string_to_write}{time_start} {time_stop} {index} {item[0]} {item[1]}\n'
            tts_list.append([time_start, time_stop, str(index), item[0], item[1]])

    media.tts_list = tts_list
    
    return tts_string_to_write
