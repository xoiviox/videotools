import subprocess
import os
import cv2
import numpy as np
from decimal import Decimal

from videotools import utils
from videotools.config import OtherConfig
from videotools.logger import logg


def take_screenshots(media):
    shorter_duration = None
    if media.video_duration < media.audio_duration:
        shorter_duration = float(media.video_duration)
    else:
        shorter_duration = float(media.audio_duration)

    movie_start_time = int(shorter_duration * OtherConfig.percentage_video_start / 100)
    movie_stop_time = int(shorter_duration * OtherConfig.percentage_video_stop / 100)
    movie_cutted_time = int(shorter_duration - movie_start_time - movie_stop_time)
    movie_screens_interval = int(movie_cutted_time / (OtherConfig.screens_num - 1))

    actual_position = movie_start_time
    for i in range(OtherConfig.screens_num):
        screenshot_cmd = f'{utils.exec_path("ffmpeg")} -hide_banner -y -ss {str(actual_position)} -i "{media.src_file_path}" -vframes 1 "{media.directory_temp}{media.dst_filename}_screenshot_{str(i)}.png"'
        actual_position = actual_position + movie_screens_interval
        proc_screenshot = subprocess.Popen(screenshot_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = proc_screenshot.communicate()


def adder(screenshot_table):
    new_table = []
    for i in range(0, len(screenshot_table), 2):
        if i + 1 < len(screenshot_table):
            img_a = cv2.imread(screenshot_table[i], 1)
            img_b = cv2.imread(screenshot_table[i + 1], 1)
            result_img = cv2.addWeighted(img_a, 0.5, img_b, 0.5, 0)
            cv2.imwrite(screenshot_table[i], result_img)
            os.remove(screenshot_table[i + 1])
            new_table.append(screenshot_table[i])
        else:
            os.remove(screenshot_table[i])
    return new_table


def add_screenshots(media):
    screenshot_table = []
    for i in range(OtherConfig.screens_num):
        screenshot_table.append(f'{media.directory_temp}{media.dst_filename}_screenshot_{str(i)}.png')
    while len(screenshot_table) >= 2:
        screenshot_table = adder(screenshot_table)
        if len(screenshot_table) == 1:
            os.rename(screenshot_table[0], f'{media.directory_temp}{media.dst_filename}_screenshot_combined.png')


def resolution_determiner(media):
    if media.real_width != 0 and media.real_height != 0:
        media.dst_width = media.real_width
        media.dst_height = media.real_height
    elif media.real_width != 0:
        media.dst_width = media.real_width
        media.dst_height = media.src_height
        media.real_height = media.src_height
    elif media.real_height != 0:
        media.dst_width = media.src_width
        media.dst_height = media.real_height
        media.real_width = media.src_width
    else:
        if not os.path.isfile(media.directory_temp + media.dst_filename + '_screenshot_combined.png'):
            logg(6, 'Taking screenshots ...')
            take_screenshots(media)
            logg(6, 'Mixing screenshots ...')
            add_screenshots(media)
        bar_finder(media)
    cutter(media)
    current_pixels = media.dst_width * media.dst_height
    media.dst_bitrate = int(round(OtherConfig.max_bitrate_fhd + (current_pixels - OtherConfig.pixels_fhd) * ((OtherConfig.max_bitrate_uhd - OtherConfig.max_bitrate_fhd) / (OtherConfig.pixels_uhd - OtherConfig.pixels_fhd))))


#def calc_bitrate(width, height)



def bar_finder(media):
    c_top = bar_finder_top(media)
    c_buttom = bar_finder_buttom(media)
    c_left = bar_finder_left(media)
    c_right = bar_finder_right(media)

    from_top = c_top
    from_button = media.src_height - c_buttom
    from_left = c_left
    from_right = media.src_width - c_right

    if from_top > from_button:
        from_button = from_top
    if from_top < from_button:
        from_top = from_button
    if from_left > from_right:
        from_right = from_left
    if from_left < from_right:
        from_left = from_right

    result_v = media.src_height - (from_top + from_button)
    result_h = media.src_width - (from_left + from_right)

    media.real_width = result_h
    media.real_height = result_v


def bar_finder_top(media):
    image = cv2.imread(f'{media.directory_temp}{media.dst_filename}_screenshot_combined.png', 1)
    for i in range(media.src_height):

        arr_width_0 = np.zeros(3)
        arr_width_1 = np.zeros(3)
        arr_width_2 = np.zeros(3)

        if i <= media.src_height:
            for j in range(media.src_width):
                arr_width_0 = arr_width_0 + image[i, j]

            avg_line_rgb_0 = arr_width_0 / media.src_width
            avg_line_0 = (avg_line_rgb_0[0] + avg_line_rgb_0[1] + avg_line_rgb_0[2]) / 3

        if i + 1 <= media.src_height:
            for j in range(media.src_width):
                arr_width_1 = arr_width_1 + image[i + 1, j]

            avg_line_rgb_1 = arr_width_1 / media.src_width
            avg_line_1 = (avg_line_rgb_1[0] + avg_line_rgb_1[1] + avg_line_rgb_1[2]) / 3

        if i + 2 <= media.src_height:
            for j in range(media.src_width):
                arr_width_2 = arr_width_2 + image[i + 2, j]

            avg_line_rgb_2 = arr_width_2 / media.src_width
            avg_line_2 = (avg_line_rgb_2[0] + avg_line_rgb_2[1] + avg_line_rgb_2[2]) / 3

        if avg_line_0 != 0 and avg_line_1 != 0 and avg_line_0 != 1:
            avg = (avg_line_0 + avg_line_1 + avg_line_2) / 3
            avg_min = avg - (avg / OtherConfig.line_diff_accept)
            avg_max = avg + (avg / OtherConfig.line_diff_accept)
            if avg_min < avg_line_0 < avg_max and avg_min < avg_line_0 < avg_max and avg_min < avg_line_0 < avg_max and avg_line_0 > OtherConfig.color_tresh:
                return i

        if i > media.src_height / 4:
            break


def bar_finder_buttom(media):
    image = cv2.imread(f'{media.directory_temp}{media.dst_filename}_screenshot_combined.png', 1)
    for i in reversed(range(media.src_height)):

        arr_width_0 = np.zeros(3)
        arr_width_1 = np.zeros(3)
        arr_width_2 = np.zeros(3)

        if i <= media.src_height:
            for j in range(media.src_width):
                arr_width_0 = arr_width_0 + image[i, j]

            avg_line_rgb_0 = arr_width_0 / media.src_width
            avg_line_0 = (avg_line_rgb_0[0] + avg_line_rgb_0[1] + avg_line_rgb_0[2]) / 3

        if i - 1 <= media.src_height:
            for j in range(media.src_width):
                arr_width_1 = arr_width_1 + image[i - 1, j]

            avg_line_rgb_1 = arr_width_1 / media.src_width
            avg_line_1 = (avg_line_rgb_1[0] + avg_line_rgb_1[1] + avg_line_rgb_1[2]) / 3

        if i - 2 <= media.src_height:
            for j in range(media.src_width):
                arr_width_2 = arr_width_2 + image[i - 2, j]

            avg_line_rgb_2 = arr_width_2 / media.src_width
            avg_line_2 = (avg_line_rgb_2[0] + avg_line_rgb_2[1] + avg_line_rgb_2[2]) / 3

        if avg_line_0 != 0 and avg_line_1 != 0 and avg_line_0 != 1:
            avg = (avg_line_0 + avg_line_1 + avg_line_2) / 3
            avg_min = avg - (avg / OtherConfig.line_diff_accept)
            avg_max = avg + (avg / OtherConfig.line_diff_accept)
            if avg_min < avg_line_0 < avg_max and avg_min < avg_line_0 < avg_max and avg_min < avg_line_0 < avg_max and avg_line_0 > OtherConfig.color_tresh:
                return i + 1

        if i < media.src_width / 4:
            break


def bar_finder_left(media):
    image = cv2.imread(f'{media.directory_temp}{media.dst_filename}_screenshot_combined.png', 1)
    for j in range(media.src_width):

        arr_height_0 = np.zeros(3)
        arr_height_1 = np.zeros(3)
        arr_height_2 = np.zeros(3)

        if j <= media.src_width:
            for i in range(media.src_height):
                arr_height_0 = arr_height_0 + image[i, j]

            avg_line_rgb_0 = arr_height_0 / media.src_height
            avg_line_0 = (avg_line_rgb_0[0] + avg_line_rgb_0[1] + avg_line_rgb_0[2]) / 3

        if j + 1 <= media.src_width:
            for i in range(media.src_height):
                arr_height_1 = arr_height_1 + image[i, j + 1]

            avg_line_rgb_1 = arr_height_1 / media.src_height
            avg_line_1 = (avg_line_rgb_1[0] + avg_line_rgb_1[1] + avg_line_rgb_1[2]) / 3

        if j + 2 <= media.src_width:
            for i in range(media.src_height):
                arr_height_2 = arr_height_2 + image[i, j + 2]

            avg_line_rgb_2 = arr_height_2 / media.src_height
            avg_line_2 = (avg_line_rgb_2[0] + avg_line_rgb_2[1] + avg_line_rgb_2[2]) / 3

        if avg_line_0 != 0 and avg_line_1 != 0 and avg_line_0 != 1:
            avg = (avg_line_0 + avg_line_1 + avg_line_2)/ 3
            avg_min = avg - (avg / OtherConfig.line_diff_accept)
            avg_max = avg + (avg / OtherConfig.line_diff_accept)
            if avg_min < avg_line_0 < avg_max and avg_min < avg_line_0 < avg_max and avg_min < avg_line_0 < avg_max and avg_line_0 > OtherConfig.color_tresh:
                return j

        if j > media.src_width / 4:
            break


def bar_finder_right(media):
    image = cv2.imread(f'{media.directory_temp}{media.dst_filename}_screenshot_combined.png', 1)
    for j in reversed(range(media.src_width)):
        arr_height_0 = np.zeros(3)
        arr_height_1 = np.zeros(3)
        arr_height_2 = np.zeros(3)

        if j <= media.src_width:
            for i in range(media.src_height):
                arr_height_0 = arr_height_0 + image[i, j]

            avg_line_rgb_0 = arr_height_0 / media.src_height
            avg_line_0 = (avg_line_rgb_0[0] + avg_line_rgb_0[1] + avg_line_rgb_0[2]) / 3

        if j - 1 <= media.src_width:
            for i in range(media.src_height):
                arr_height_1 = arr_height_1 + image[i, j - 1]

            avg_line_rgb_1 = arr_height_1 / media.src_height
            avg_line_1 = (avg_line_rgb_1[0] + avg_line_rgb_1[1] + avg_line_rgb_1[2]) / 3

        if j - 2 <= media.src_width:
            for i in range(media.src_height):
                arr_height_2 = arr_height_2 + image[i, j - 2]

            avg_line_rgb_2 = arr_height_2 / media.src_height
            avg_line_2 = (avg_line_rgb_2[0] + avg_line_rgb_2[1] + avg_line_rgb_2[2]) / 3

        if avg_line_0 != 0 and avg_line_1 != 0 and avg_line_0 != 1:
            avg = (avg_line_0 + avg_line_1 + avg_line_2)/ 3
            avg_min = avg - (avg / OtherConfig.line_diff_accept)
            avg_max = avg + (avg / OtherConfig.line_diff_accept)
            if avg_min < avg_line_0 < avg_max and avg_min < avg_line_0 < avg_max and avg_min < avg_line_0 < avg_max and avg_line_0 > OtherConfig.color_tresh:
                return j + 1

        if j < media.src_width / 4:
            break


def rounder(n):
    answer = round(n)
    if not answer%2:
        return answer
    if abs(answer+1-n) < abs(answer-1-n):
        return answer + 1
    else:
        return answer - 1


def cutter(media):
    croop = ''
    scale = ''

    cut_h = 'in_h'
    cut_w = 'in_w'

    if media.src_height > media.real_height:
        cut_h = f'{cut_h}-2*{int((media.src_height - media.real_height) / 2)}'
    if media.src_width > media.real_width:
        cut_w = f'{cut_w}-2*{int((media.src_width - media.real_width) / 2)}'
    if cut_h != 'in_h' or cut_w != 'in_w':
        croop = f'crop={cut_w}:{cut_h}'

    if 3840 >= media.real_width > 1920 and 2160 >= media.real_height > 1080:  ### process for 2160p
        if media.real_width / media.real_height == 1.7777777777777777:  ### this is 16:9
            media.dst_width = 3840
            media.dst_height = 2160
        elif media.real_width / media.real_height < 1.7777777777777777:  ### height is primary
            new_w = (2160 * media.real_width) / media.real_height
            new_w = rounder(new_w)
            media.dst_width = new_w
            media.dst_height = 2160
        elif media.real_width / media.real_height > 1.7777777777777777:  ### width is primary
            new_h = (3840 * media.real_height) / media.real_width
            new_h = rounder(new_h)
            media.dst_width = 3840
            media.dst_height = new_h

    if 1920 >= media.real_width and 1080 >= media.real_height:  ### process for 1080p
        if media.real_width / media.real_height == 1.7777777777777777:  ### this is 16:9
            media.dst_width = 1920
            media.dst_height = 1080
        elif media.real_width / media.real_height < 1.7777777777777777:  ### height is primary
            new_w = (1080 * media.real_width) / media.real_height
            new_w = rounder(new_w)
            media.dst_width = new_w
            media.dst_height = 1080
        elif media.real_width / media.real_height > 1.7777777777777777:  ### width is primary
            new_h = (1920 * media.real_height) / media.real_width
            new_h = rounder(new_h)
            media.dst_width = 1920
            media.dst_height = new_h

    if media.real_width != media.dst_width or media.real_height != media.dst_height:  ### scaling needed
        scale = f'scale={media.dst_width}:{media.dst_height}'

    if croop != '' and scale != '':
        media.cut_str = f'-vf "{croop}, {scale}"'
    elif croop != '' or scale != '':
        media.cut_str = f'-vf "{croop}{scale}"'


