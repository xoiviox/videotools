class DirConfig:
    d_ffmpeg = '../../exec/ffmpeg' # leave empty if using system os exec
    d_ffprobe = '../../exec/ffprobe' # leave empty if using system os exec
    d_mediainfo = '../../exec/mediainfo' # leave empty if using system os exec
    d_mkvmerge = '../../exec/mkvmerge' # leave empty if using system os exec
    d_hdr10plus_tool = '../../exec/hdr10plus_tool' # leave empty if using system os exec
    
    d_main = '/big/test/'
    d_conv = d_main + 'new_file/'
    d_conf = d_main + 'conf/'
    d_done_n = d_main + 'done/'
    d_make_n = d_main + 'make/'
    d_temp = d_main + 'temp/'

    d_arch_movies = d_main + 'archive/movies/'
    d_arch_series = d_main + 'archive/series/'
    d_arch_temporary = d_main + 'archive/temporary/'

    fin_main = '/big/video_files_new/'

    fin_movies_uhd = fin_main + 'movies_uhd/'
    fin_movies_uhd_hdr = fin_main + 'movies_uhd_hdr/'
    fin_movies_uhd_dhdr = fin_main + 'movies_uhd_dhdr/'
    fin_movies_fhd = fin_main + 'movies_fhd/'
    fin_movies_fhd_hdr = fin_main + 'movies_fhd_hdr/'
    fin_movies_fhd_dhdr = fin_main + 'movies_fhd_dhdr/'

    fin_series_uhd = fin_main + 'series_uhd/'
    fin_series_uhd_hdr = fin_main + 'series_uhd_hdr/'
    fin_series_uhd_dhdr = fin_main + 'series_uhd_dhdr/'
    fin_series_fhd = fin_main + 'series_fhd/'
    fin_series_fhd_hdr = fin_main + 'series_fhd_hdr/'
    fin_series_fhd_dhdr = fin_main + 'series_fhd_dhdr/'

    old_fin_main = '/big/video_files/'

    old_fin_movies_uhd = old_fin_main + 'movies_uhd/'
    old_fin_movies_uhd_hdr = old_fin_main + 'movies_uhd_hdr/'
    old_fin_movies_uhd_dhdr = old_fin_main + 'movies_uhd_dhdr/'
    old_fin_movies_fhd = old_fin_main + 'movies_fhd/'
    old_fin_movies_fhd_hdr = old_fin_main + 'movies_fhd_hdr/'
    old_fin_movies_fhd_dhdr = old_fin_main + 'movies_fhd_dhdr/'

    old_fin_series_uhd = old_fin_main + 'series_uhd/'
    old_fin_series_uhd_hdr = old_fin_main + 'series_uhd_hdr/'
    old_fin_series_uhd_dhdr = old_fin_main + 'series_uhd_dhdr/'
    old_fin_series_fhd = old_fin_main + 'series_fhd/'
    old_fin_series_fhd_hdr = old_fin_main + 'series_fhd_hdr/'
    old_fin_series_fhd_dhdr = old_fin_main + 'series_fhd_dhdr/'

    fin_meta = '/small/video_meta/'
    fin_meta_movies = fin_meta + 'meta_movies/'
    fin_meta_series = fin_meta + 'meta_series/'

    fin_temp = '/big/video_to_delete/'
    fin_temp_movies = fin_temp + 'VO.movies/'
    fin_temp_series = fin_temp + 'VO.series/'


class OtherConfig:
    video_extensions = ['mkv', 'mp4', 'avi']

    lang_main = 'pol'
    lang_additional = 'eng'
    
    audio_quaility_original = 4
    audio_quaility_voiceover = 3

    max_bitrate_fhd = 1999
    max_bitrate_uhd = 4499
    pixels_fhd = 1920 * 1080
    pixels_uhd = 3840 * 2160

    screens_num = 32                        ### liczba screenów do wykonania i dodania (najefektywniej = potęga 2)
    percentage_video_start = 2              ### pominięcie początku video w min
    percentage_video_stop = 5               ### pominięcie końca video w min
    color_tresh = 1                         ### minimalna "ilość koloru"
    line_diff_accept = 3.1                  ### minimalna różnica w kolorze linii (w %) aby uznać za obraz ### było 5% początkowo ale 3.1% jest lepsze    

    #file_length_tolerance = 1               ### seconds

    log_web_level = 6                       ### 7 = debug, 6 = informational, 5 = significant, 4 = warning, 3 = error, 2 = critical
    log_print_level = 6
    log_write_level = 7
    log_gap = 96

    google_vo_language_code = 'pl-PL'
    google_vo_voice_name = 'pl-PL-Wavenet-B'
    google_vo_speaking_rate = 1.3
    google_vo_pitch = -4.0

    vo_max_sentence_gap_long = 400
    vo_max_sentence_gap_short = 0.25        ### of long gap
    vo_step_down_sentences_gap = 0.1        ### of long gap
    vo_min_sentence_gap_long = 0.1          ### of long gap
    vo_max_playback_speed = 1.15
    vo_audio_volume_param1 = 7
    vo_audio_volume_param2 = 1              ### głośność względem orginału (-2.33 ciszej, -2.83 głośniej)
    vo_audio_volume_min = -30               ### głośność minimalna 28

    google_credentials_file = '/small/apps/google-cloud-auth-ene-acc.json'
    #google_credentials_file = '/small/apps/central-hold-374616-60fd8189da1a.json'
    chars_download_limit = 1000000
    bytes_download_limit = 1000000
    requests_per_minute = 1000
    


class AppConfig:
    SESSION_TYPE = 'sqlalchemy'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DirConfig.d_conf}database.sqlite'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CHECK_SAME_THREAD = False
    #SQLALCHEMY_ENGINE_OPTIONS = {"check_same_thread": False}
    #SQLALCHEMY_ECHO = True
