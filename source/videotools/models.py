from videotools import db


class MediaObj(db.Model):
    __tablename__ = 'media'
    
    src_filename_extension = db.Column(db.Text, primary_key=True, unique=True)
    src_size = db.Column(db.Integer)
    src_file_path = db.Column(db.Text)
    src_filename = db.Column(db.Text)
    src_extension = db.Column(db.Text)

    list_video = db.Column(db.Text)
    list_audio = db.Column(db.Text)
    list_subtitle_main = db.Column(db.Text)
    list_subtitle_additional = db.Column(db.Text)

    dst_directory = db.Column(db.Text)
    dst_filename = db.Column(db.Text)
    base_directory = db.Column(db.Text)
    base_filename = db.Column(db.Text)
    media_dst = db.Column(db.Text)
    video_type = db.Column(db.Text)
    directory = db.Column(db.Text)
    directory_temp = db.Column(db.Text)
    directory_tts = db.Column(db.Text)
    directory_done = db.Column(db.Text)
    directory_archive = db.Column(db.Text)
    directory_final = db.Column(db.Text)
    directory_final_meta = db.Column(db.Text)
    title = db.Column(db.Text)

    video_stream = db.Column(db.Integer)
    audio_stream = db.Column(db.Integer)
    subtitle_stream_main = db.Column(db.Integer)
    subtitle_stream_additional = db.Column(db.Integer)

    video_duration = db.Column(db.Float)
    video_delay = db.Column(db.Float)
    video_frame_rate = db.Column(db.Text)
    hdr = db.Column(db.Boolean)
    dhdr = db.Column(db.Boolean)
    imax = db.Column(db.Boolean)
    max_cll = db.Column(db.Text)
    master_display = db.Column(db.Text)
    src_width = db.Column(db.Integer)
    src_height = db.Column(db.Integer)
    real_width = db.Column(db.Integer)
    real_height = db.Column(db.Integer)
    dst_width = db.Column(db.Integer)
    dst_height = db.Column(db.Integer)
    dst_bitrate = db.Column(db.Integer)
    cut_str = db.Column(db.Text)
    
    audio_duration = db.Column(db.Float)
    audio_delay = db.Column(db.Float)
    audio_language = db.Column(db.Text)
    audio_channels = db.Column(db.Integer)
    dst_audio_channels = db.Column(db.Integer)
    
    start_at = db.Column(db.Float)
    stop_at = db.Column(db.Float)

    create_voiceover_state = db.Column(db.Text)
    download_voiceover_state = db.Column(db.Text)
    convert_video_state = db.Column(db.Text)
    convert_audio_state = db.Column(db.Text)
    convert_audio_voiceover_state = db.Column(db.Text)
    extract_audio_state = db.Column(db.Text)
    subtitle_main_state = db.Column(db.Text)
    subtitle_additional_state = db.Column(db.Text)

    extract_hdrplus_state = db.Column(db.Text)
    mux_state = db.Column(db.Text)
    move_files_state = db.Column(db.Text)

    tts_list = []

    def __str__(self):
        result =    f'src_filename_extension: {self.src_filename_extension}\nsrc_size: {self.src_size}\nsrc_file_path: {self.src_file_path}\nsrc_filename: {self.src_filename}\nsrc_extension: {self.src_extension}\ndst_directory: {self.dst_directory}\ndst_filename: {self.dst_filename}\nbase_directory: {self.base_directory}\nbase_filename: {self.base_filename}\n' \
                    f'media_dst: {self.media_dst}\nvideo_type: {self.video_type}\ndirectory: {self.directory}\ndirectory_temp: {self.directory_temp}\ndirectory_tts: {self.directory_tts}\ndirectory_done: {self.directory_done}\ndirectory_archive: {self.directory_archive}\n' \
                    f'directory_final: {self.directory_final}\ndirectory_final_meta: {self.directory_final_meta}\ntitle: {self.title}\nvideo_stream: {self.video_stream}\naudio_stream: {self.audio_stream}\nvideo_frame_rate: {self.video_frame_rate}\nsubtitle_stream_main: {self.subtitle_stream_main}\nsubtitle_stream_additional: {self.subtitle_stream_additional}\n' \
                    f'video_duration: {self.video_duration}\naudio_duration: {self.audio_duration}\nvideo_delay: {self.video_delay}\naudio_delay: {self.audio_delay}\naudio_language: {self.audio_language}\naudio_channels: {self.audio_channels}\ndst_audio_channels: {self.dst_audio_channels}\n' \
                    f'hdr: {self.hdr}\ndhdr: {self.dhdr}\nimax: {self.imax}\nmax_cll: {self.max_cll}\nmaster_display: {self.master_display}\nsrc_width: {self.src_width}\nsrc_height: {self.src_height}\nreal_width: {self.real_width}\n' \
                    f'real_height: {self.real_height}\ndst_width: {self.dst_width}\ndst_height: {self.dst_height}\ndst_bitrate: {self.dst_bitrate}\nstart_at: {self.start_at}\nstop_at: {self.stop_at}\ncut_str: {self.cut_str}\n' \
                    f'convert_video_state: {self.convert_video_state}\nconvert_audio_state: {self.convert_audio_state}\nconvert_audio_voiceover_state: {self.convert_audio_voiceover_state}\nextract_audio_state: {self.extract_audio_state}\nsubtitle_main_state: {self.subtitle_main_state}\nsubtitle_additional_state: {self.subtitle_additional_state}\n' \
                    f'extract_hdrplus_state: {self.extract_hdrplus_state}\ndownload_voiceover_state: {self.download_voiceover_state}\ncreate_voiceover_state: {self.create_voiceover_state}\nmux_state: {self.mux_state}\nmove_files_state: {self.move_files_state}'
        return result

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __iter__(self):
        return iter(self)

