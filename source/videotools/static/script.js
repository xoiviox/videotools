function flag_state(state) {
    if (state == null || state == 'not_converted' || state == 'not_extracted' || state == 'not_created') {
        return String.fromCodePoint(0x1F311);
    } else if (state == 'converting' || state == 'extracting' || state == 'creating') {
        return String.fromCodePoint(0x1F7E1);
    } else if (state == 'converted' || state == 'extracted' || state == 'exist' || state == 'created') {
        return String.fromCodePoint(0x1F7E2);
    } else if (state == 'error' || state == 'error') {
        return String.fromCodePoint(0x1F534);
    }
}


function selectbox_media_add(media) {
    console.log('media_add:', media.src_filename_extension);
    // long_dot_string = flag_state(media.convert_video_state) + ' ' + flag_state(media.convert_audio_state) + ' ' + flag_state(media.convert_audio_voiceover_state) + ' ' + flag_state(media.extract_audio_state) + ' ' + flag_state(media.extract_subtitle_1_state) + ' ' + flag_state(media.extract_subtitle_2_state);
    long_dot_string = flag_state(media.convert_video_state) + ' ' + flag_state(media.convert_audio_state) + ' ' + flag_state(media.convert_audio_voiceover_state) + ' ' + flag_state(media.extract_audio_state) + ' ' + flag_state(media.create_voiceover_state);
    op_all_string = long_dot_string + '\xa0\xa0' + media.src_filename_extension;

    const newOption = document.createElement('option');
    const optionText = document.createTextNode(op_all_string);
    newOption.appendChild(optionText);
    newOption.setAttribute('value', media.src_filename_extension);
    newOption.setAttribute('class', 'list_object');

    document.getElementById('filelist').appendChild(newOption);
    selectbox_sort();
};


function flag_update(media) {
    var selectobject = document.getElementById("filelist");
    for (let i = 0; i < selectobject.length; i++) {
        if (selectobject[i].value == media.src_filename_extension) {
            // long_dot_string = flag_state(media.convert_video_state) + ' ' + flag_state(media.convert_audio_state) + ' ' + flag_state(media.convert_audio_voiceover_state) + ' ' + flag_state(media.extract_audio_state) + ' ' + flag_state(media.extract_subtitle_1_state) + ' ' + flag_state(media.extract_subtitle_2_state);
            long_dot_string = flag_state(media.convert_video_state) + ' ' + flag_state(media.convert_audio_state) + ' ' + flag_state(media.convert_audio_voiceover_state) + ' ' + flag_state(media.extract_audio_state) + ' ' + flag_state(media.create_voiceover_state);
            op_all_string = long_dot_string + '\xa0\xa0' + media.src_filename_extension;
            selectobject[i].text = op_all_string;
        }
    }
}


function selectbox_media_rem(media) {
    console.log('media_rem:', media.src_filename_extension);
    var selectobject = document.getElementById("filelist");
    for (var i=0; i<selectobject.length; i++) {
        if (selectobject.options[i].value == media.src_filename_extension)
            selectobject.remove(i);
    }
};


function selectbox_sort() {
    $("#filelist").html($("#filelist option").sort(function (a, b) {
        return a.value == b.value ? 0 : a.value.toLowerCase() < b.value.toLowerCase() ? -1 : 1
    }))
}


function selected_update(media_sum) {
    console.log(media_sum)

    $(".line_data#src_filename_extension").html(media_sum.src_filename_extension);
    $(".line_data#src_size").html(media_sum.src_size);
    $(".line_data#src_file_path").html(media_sum.src_file_path);
    $(".line_data#src_filename").html(media_sum.src_filename);
    $(".line_data#src_extension").html(media_sum.src_extension);
    $(".line_data#dst_directory").html(media_sum.dst_directory);
    $(".line_data#dst_filename").html(media_sum.dst_filename);
    $(".line_data#base_directory").html(media_sum.base_directory);
    $(".line_data#base_filename").html(media_sum.base_filename);
    $(".line_data#media_dst").html(media_sum.media_dst);
    $(".line_data#video_type").html(media_sum.video_type);
    $(".line_data#directory").html(media_sum.directory);
    $(".line_data#directory_temp").html(media_sum.directory_temp);
    $(".line_data#directory_tts").html(media_sum.directory_tts);
    $(".line_data#directory_done").html(media_sum.directory_done);
    $(".line_data#directory_archive").html(media_sum.directory_archive);
    $(".line_data#directory_final").html(media_sum.directory_final);
    $(".line_data#directory_final_meta").html(media_sum.directory_final_meta);
    $(".line_data#title").html(media_sum.title);
    $(".line_data#video_stream").html(media_sum.video_stream);
    $(".line_data#audio_stream").html(media_sum.audio_stream);
    $(".line_data#video_frame_rate").html(media_sum.video_frame_rate);
    $(".line_data#subtitle_stream_main").html(media_sum.subtitle_stream_main);
    $(".line_data#subtitle_stream_additional").html(media_sum.subtitle_stream_additional);
    $(".line_data#video_duration").html(media_sum.video_duration);
    $(".line_data#audio_duration").html(media_sum.audio_duration);
    $(".line_data#video_delay").html(media_sum.video_delay);
    $(".line_data#audio_delay").html(media_sum.audio_delay);
    $(".line_data#audio_language").html(media_sum.audio_language);
    $(".line_data#audio_channels").html(media_sum.audio_channels);
    $(".line_data#dst_audio_channels").html(media_sum.dst_audio_channels);
    $(".line_data#hdr").html(media_sum.hdr);
    $(".line_data#dhdr").html(media_sum.dhdr);
    $(".line_data#imax").html(media_sum.imax);
    $(".line_data#max_cll").html(media_sum.max_cll);
    $(".line_data#master_display").html(media_sum.master_display);
    $(".line_data#src_width").html(media_sum.src_width);
    $(".line_data#src_height").html(media_sum.src_height);
    $(".line_data#real_width").html(media_sum.real_width);
    $(".line_data#real_height").html(media_sum.real_height);
    $(".line_data#dst_width").html(media_sum.dst_width);
    $(".line_data#dst_height").html(media_sum.dst_height);
    $(".line_data#dst_bitrate").html(media_sum.dst_bitrate);
    $(".line_data#start_at").html(media_sum.start_at);
    $(".line_data#stop_at").html(media_sum.stop_at);
    $(".line_data#cut_str").html(media_sum.cut_str);

    if (media_sum.convert_video_state == 'converted') { string_convert_video_state = String.fromCodePoint(0x1F7E2) + ' converted' }
    else if (media_sum.convert_video_state == 'converting') { string_convert_video_state = String.fromCodePoint(0x1F7E1) + ' converting' }
    else if (media_sum.convert_video_state == 'error') { string_convert_video_state = String.fromCodePoint(0x1F534) + ' error' }
    else if (media_sum.convert_video_state == 'not_converted' || media_sum.convert_video_state == null) { string_convert_video_state = String.fromCodePoint(0x1F311) + '  not converted' }
    $(".line_data#convert_video_state").html(string_convert_video_state);

    if (media_sum.convert_audio_state == 'converted') { string_convert_audio_state = String.fromCodePoint(0x1F7E2) + ' converted' }
    else if (media_sum.convert_audio_state == 'converting') { string_convert_audio_state = String.fromCodePoint(0x1F7E1) + ' converting' }
    else if (media_sum.convert_audio_state == 'error') { string_convert_audio_state = String.fromCodePoint(0x1F534) + ' error' }
    else if (media_sum.convert_audio_state == 'not_converted' || media_sum.convert_audio_state == null) { string_convert_audio_state = String.fromCodePoint(0x1F311) + '  not converted' }
    $(".line_data#convert_audio_state").html(string_convert_audio_state);

    if (media_sum.convert_audio_voiceover_state == 'converted') { string_convert_audio_voiceover_state = String.fromCodePoint(0x1F7E2) + ' converted' }
    else if (media_sum.convert_audio_voiceover_state == 'converting') { string_convert_audio_voiceover_state = String.fromCodePoint(0x1F7E1) + ' converting' }
    else if (media_sum.convert_audio_voiceover_state == 'error') { string_convert_audio_voiceover_state = String.fromCodePoint(0x1F534) + ' error' }
    else if (media_sum.convert_audio_voiceover_state == 'not_converted' || media_sum.convert_audio_voiceover_state == null) { string_convert_audio_voiceover_state = String.fromCodePoint(0x1F311) + '  not converted' }
    $(".line_data#convert_audio_voiceover_state").html(string_convert_audio_voiceover_state);

    if (media_sum.extract_audio_state == 'extracted') { string_extract_audio_state = String.fromCodePoint(0x1F7E2) + ' extracted' }
    else if (media_sum.extract_audio_state == 'extracting') { string_extract_audio_state = String.fromCodePoint(0x1F7E1) + ' extracting' }
    else if (media_sum.extract_audio_state == 'error') { string_extract_audio_state = String.fromCodePoint(0x1F534) + ' error' }
    else if (media_sum.extract_audio_state == 'not_extracted' || media_sum.extract_audio_state == null) { string_extract_audio_state = String.fromCodePoint(0x1F311) + '  not extracted' }
    $(".line_data#extract_audio_state").html(string_extract_audio_state);

    string_subtitle_main_state = '';
    if (media_sum.subtitle_main_state == 'extracted') { string_subtitle_main_state = String.fromCodePoint(0x1F7E2) + ' extracted' }
    else if (media_sum.subtitle_main_state == 'extracting') { string_subtitle_main_state = String.fromCodePoint(0x1F7E1) + ' extracting' }
    else if (media_sum.subtitle_main_state == 'error') { string_subtitle_main_state = String.fromCodePoint(0x1F534) + ' error' }
    else if (media_sum.subtitle_main_state == 'not_extracted' || media_sum.subtitle_main_state == null) { string_subtitle_main_state = String.fromCodePoint(0x1F311) + '  not extracted' }
    else if (media_sum.subtitle_main_state == 'exist') { string_subtitle_main_state = String.fromCodePoint(0x1F7E2) + '  exist' }
    else if (media_sum.subtitle_main_state == 'downloaded') { string_subtitle_main_state = String.fromCodePoint(0x1F7E2) + '  downloaded' }
    else if (media_sum.subtitle_main_state == 'downloading') { string_subtitle_main_state = String.fromCodePoint(0x1F7E1) + '  downloading' }
    else if (media_sum.subtitle_main_state == 'not_downloaded') { string_subtitle_main_state = String.fromCodePoint(0x1F311) + '  not downloaded' }
    $(".line_data#subtitle_main_state").html(string_subtitle_main_state);

    string_subtitle_additional_state = '';
    if (media_sum.subtitle_additional_state == 'extracted') { string_subtitle_additional_state = String.fromCodePoint(0x1F7E2) + ' extracted' }
    else if (media_sum.subtitle_additional_state == 'extracting') { string_subtitle_additional_state = String.fromCodePoint(0x1F7E1) + ' extracting' }
    else if (media_sum.subtitle_additional_state == 'error') { string_subtitle_additional_state = String.fromCodePoint(0x1F534) + ' error' }
    else if (media_sum.subtitle_additional_state == 'not_extracted' || media_sum.subtitle_additional_state == null) { string_subtitle_additional_state = String.fromCodePoint(0x1F311) + '  not extracted' }
    else if (media_sum.subtitle_additional_state == 'exist') { string_subtitle_additional_state = String.fromCodePoint(0x1F7E2) + '  exist' }
    else if (media_sum.subtitle_additional_state == 'downloaded') { string_subtitle_additional_state = String.fromCodePoint(0x1F7E2) + '  downloaded' }
    else if (media_sum.subtitle_additional_state == 'downloading') { string_subtitle_additional_state = String.fromCodePoint(0x1F7E1) + '  downloading' }
    else if (media_sum.subtitle_additional_state == 'not_downloaded') { string_subtitle_additional_state = String.fromCodePoint(0x1F311) + '  not downloaded' }
    $(".line_data#subtitle_additional_state").html(string_subtitle_additional_state);

    string_extract_hdrplus_state = '';
    if (media_sum.dhdr == true) {
        if (media_sum.extract_hdrplus_state == 'extracted') { string_extract_hdrplus_state = String.fromCodePoint(0x1F7E2) + ' extracted' }
        else if (media_sum.extract_hdrplus_state == 'extracting') { string_extract_hdrplus_state = String.fromCodePoint(0x1F7E1) + ' extracting' }
        else if (media_sum.extract_hdrplus_state == 'error') { string_extract_hdrplus_state = String.fromCodePoint(0x1F534) + ' error' }
        else if (media_sum.extract_hdrplus_state == 'not_extracted' || media_sum.extract_hdrplus_state == null) { string_extract_hdrplus_state = String.fromCodePoint(0x1F311) + '  not extracted' }
    }
    else {
        string_extract_hdrplus_state = String.fromCodePoint(0x1F311) + ' no dhdr'
    }
    $(".line_data#extract_hdrplus_state").html(string_extract_hdrplus_state);

    string_download_voiceover_state = '';
    if (media_sum.download_voiceover_state == 'downloaded') { string_download_voiceover_state = String.fromCodePoint(0x1F7E2) + ' downloaded' }
    else if (media_sum.download_voiceover_state == 'downloading') { string_download_voiceover_state = String.fromCodePoint(0x1F7E1) + ' downloading' }
    else if (media_sum.download_voiceover_state == 'error') { string_download_voiceover_state = String.fromCodePoint(0x1F534) + ' error' }
    else if (media_sum.download_voiceover_state == 'not_downloaded' || media_sum.download_voiceover_state == null) { string_download_voiceover_state = String.fromCodePoint(0x1F311) + '  not downloaded' }
    $(".line_data#download_voiceover_state").html(string_download_voiceover_state);

    string_create_voiceover_state = '';
    if (media_sum.create_voiceover_state == 'created') { string_create_voiceover_state = String.fromCodePoint(0x1F7E2) + ' created' }
    else if (media_sum.create_voiceover_state == 'creating') { string_create_voiceover_state = String.fromCodePoint(0x1F7E1) + ' creating' }
    else if (media_sum.create_voiceover_state == 'error') { string_create_voiceover_state = String.fromCodePoint(0x1F534) + ' error' }
    else if (media_sum.create_voiceover_state == 'not_created' || media_sum.create_voiceover_state == null) { string_create_voiceover_state = String.fromCodePoint(0x1F311) + '  not created' }
    $(".line_data#create_voiceover_state").html(string_create_voiceover_state);

    string_mux_state = '';
    if (media_sum.mux_state == 'muxed') { string_mux_state = String.fromCodePoint(0x1F7E2) + ' muxed' }
    else if (media_sum.mux_state == 'muxing') { string_mux_state = String.fromCodePoint(0x1F7E1) + ' muxing' }
    else if (media_sum.mux_state == 'error') { string_mux_state = String.fromCodePoint(0x1F534) + ' error' }
    else if (media_sum.mux_state == 'not_muxed' || media_sum.mux_state == null) { string_mux_state = String.fromCodePoint(0x1F311) + '  not muxed' }
    $(".line_data#mux_state").html(string_mux_state);

    string_move_files_state = '';
    if (media_sum.move_files_state == 'moved') { string_move_files_state = String.fromCodePoint(0x1F7E2) + ' moved' }
    else if (media_sum.move_files_state == 'moving') { string_move_files_state = String.fromCodePoint(0x1F7E1) + ' moving' }
    else if (media_sum.move_files_state == 'error') { string_move_files_state = String.fromCodePoint(0x1F534) + ' error' }
    else if (media_sum.move_files_state == 'not_moved' || media_sum.move_files_state == null) { string_move_files_state = String.fromCodePoint(0x1F311) + '  not moved' }
    $(".line_data#move_files_state").html(string_move_files_state);


    document.getElementById('dropdown_media_dst').innerHTML = '';
    dsts_list = ['default', 'archive', 'rearchive', 'temporary']
    for (var i = 0; i < dsts_list.length; i++) {
        newOption = document.createElement('option');
        optionText = document.createTextNode(dsts_list[i]);
        newOption.appendChild(optionText);
        newOption.setAttribute('class', 'list_object');
        newOption.setAttribute('value', dsts_list[i]);
        
        if (media_sum.media_dst ==  dsts_list[i]) {
            newOption.setAttribute('selected', 'selected');
        }
        document.getElementById('dropdown_media_dst').appendChild(newOption);
    }

    var json_list_video = JSON.parse(media_sum.list_video)
    var json_list_audio = JSON.parse(media_sum.list_audio)
    var json_list_subtitle_main = JSON.parse(media_sum.list_subtitle_main)
    var json_list_subtitle_additional = JSON.parse(media_sum.list_subtitle_additional)

    fill_video_list_option(json_list_video, media_sum.video_stream)
    fill_audio_list_option(json_list_audio, media_sum.audio_stream)
    fill_sub_list_option(json_list_subtitle_main, media_sum.subtitle_stream_main, 'main')
    fill_sub_list_option(json_list_subtitle_additional, media_sum.subtitle_stream_additional, 'additional')


    document.getElementById('media_start_number').value = new Date(media_sum.start_at * 1000).toISOString().slice(11, 21);
    document.getElementById('media_stop_number').value = new Date(media_sum.stop_at * 1000).toISOString().slice(11, 21);
}

function fill_video_list_option(json_list_video, video_stream) {
    document.getElementById('dropdown_video_stream').innerHTML = '';
    
    newOption = document.createElement('option');
    optionText = document.createTextNode('default');
    newOption.appendChild(optionText);
    newOption.setAttribute('value', 'default');
    newOption.setAttribute('class', 'list_object');
    if ($('#filelist').val().length > 1 || json_list_video.length > 1) {
        document.getElementById('dropdown_video_stream').appendChild(newOption);
    }

    for (var i = 0; i < json_list_video.length; i++) {
        desc = json_list_video[i];
        txt = desc.index

        if (desc.codec_name) {
            txt = txt + ', ' + desc.codec_name + ', ' + desc.bit_rate + ' Mb/s, ' + desc.duration + ' s'
            if (desc.language != null && desc.language != '') { txt = txt + ', ' + desc.language }
            txt = txt + ', ' + desc.stream_size + ' GiB, delay ' + desc.start_time + ' s'
            if (desc.src_width != null && desc.src_width != '' && desc.src_height != null && desc.src_height != '') { txt = txt + ', ' + desc.src_width + 'x' + desc.src_height}
            if (desc.hdr == 1) { txt = txt + ', hdr' }
            if (desc.dhdr == 1) { txt = txt + ', dhdr' }
            if (desc.default == 1) { txt = txt + ', default' }
            if (desc.forced == 1) { txt = txt + ', forced' }
            if (desc.title != null && desc.title != '') { txt = txt + ',\xa0\xa0TITLE: ' + desc.title }
        }

        newOption = document.createElement('option');
        optionText = document.createTextNode(txt);
        newOption.appendChild(optionText);
        newOption.setAttribute('value', desc.index);
        newOption.setAttribute('class', 'list_object');

        if (video_stream == desc.index) {
            newOption.setAttribute('selected', 'selected');
        }

        document.getElementById('dropdown_video_stream').appendChild(newOption);
    }

}

function fill_audio_list_option(json_list_audio, audio_stream) {
    document.getElementById('dropdown_audio_stream').innerHTML = '';
    
    newOption = document.createElement('option');
    optionText = document.createTextNode('default');
    newOption.appendChild(optionText);
    newOption.setAttribute('value', 'default');
    newOption.setAttribute('class', 'list_object');
    if ($('#filelist').val().length > 1 || json_list_audio.length > 1) {
        document.getElementById('dropdown_audio_stream').appendChild(newOption);
    }

    for (var i = 0; i < json_list_audio.length; i++) {
        desc = json_list_audio[i];
        txt = desc.index
        
        if (desc.codec_name) {
            txt = txt + ', ' + desc.codec_name + ', ' + desc.bit_rate + ' Mb/s, ' + desc.duration + ' s, ' + desc.language + ', ' + desc.channels + ' ch, ' + desc.stream_size + ' GiB, delay ' + desc.start_time + ' s'
            if (desc.atmos == 1) { txt = txt + ', atmos' }
            if (desc.default == 1) { txt = txt + ', default' }
            if (desc.forced == 1) { txt = txt + ', forced' }
            if (desc.title != null && desc.title != '') { txt = txt + ',\xa0\xa0TITLE: ' + desc.title }
        }

        newOption = document.createElement('option');
        optionText = document.createTextNode(txt);
        newOption.appendChild(optionText);
        newOption.setAttribute('value', desc.index);
        newOption.setAttribute('class', 'list_object');

        if (audio_stream == desc.index) {
            newOption.setAttribute('selected', 'selected');
        }

        document.getElementById('dropdown_audio_stream').appendChild(newOption);
    }

}

function fill_sub_list_option(json_list_sub_lang, subtitle_stream, lang) {
    if (lang == 'main') { dropdown = 'dropdown_subtitle_stream_main' }
    else if (lang == 'additional') { dropdown = 'dropdown_subtitle_stream_additional' }
    document.getElementById(dropdown).innerHTML = '';

    newOption = document.createElement('option');
    optionText = document.createTextNode('default');
    newOption.appendChild(optionText);
    newOption.setAttribute('value', 'default');
    newOption.setAttribute('class', 'list_object');
    if ($('#filelist').val().length > 1 || json_list_sub_lang.length > 1) {
        document.getElementById(dropdown).appendChild(newOption);
    }

    for (var i = 0; i < json_list_sub_lang.length; i++) {
        desc = json_list_sub_lang[i];
        txt = desc.index

        if (Object.keys(desc).length > 1) {
            if (desc.language != null && desc.language != '') { txt = txt + ', ' + desc.language }
            if (desc.bps != null && desc.bps != '') { txt = txt + ', ' + desc.bps + ' bps' }
            if (desc.frames != null && desc.frames != '') { txt = txt + ', ' + desc.frames + ' frames' }
            if (desc.default == 1) { txt = txt + ', default' }
            if (desc.forced == 1) { txt = txt + ', forced' }
            if (desc.title != null && desc.title != '') { txt = txt + ',\xa0\xa0TITLE: ' + desc.title }
        }

        newOption = document.createElement('option');
        optionText = document.createTextNode(txt);
        newOption.appendChild(optionText);
        newOption.setAttribute('value', desc.index);
        newOption.setAttribute('class', 'list_object');

        if (subtitle_stream == desc.index) {
            newOption.setAttribute('selected', 'selected');
        }

        document.getElementById(dropdown).appendChild(newOption);
    }
}

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


$(document).ready(function() {
    var socket = io.connect('http://192.168.7.3:5000');


    socket.on('connected', function(msg) {
        pre_selected_files = $('#filelist').val()
        console.log('pre_selected_files:', pre_selected_files);

        
        for (var i=document.getElementById('filelist').options.length; i-->0;)
            document.getElementById('filelist').options[i] = null;
        
        for (let i = 0; i < msg.length; i++) {
            selectbox_media_add(msg[i])
        }
        var selected_files = $('#filelist').val();
        socket.emit('selected_files', selected_files);
        selectbox_sort()
    });

    socket.on('disconnected', function(msg) {
        for (var i=document.getElementById('filelist').options.length; i-->0;)
            document.getElementById('filelist').options[i] = null;
    });


///////////////////////////////////////////////////////////////////////////////


    //selectbox_sort()

    socket.on('logger_update', function(msg) {
        console.log('logger_update: ', msg);
        if ($('#logger_area').val() == '') {
            $('#logger_area').val( $('#logger_area').val() + msg);
        } else {
            $('#logger_area').val( $('#logger_area').val() + '\n' + msg);
        }
        $('#logger_area').scrollTop($('#logger_area')[0].scrollHeight);
    });

    socket.on('media_add', function(msg) {
        selectbox_media_add(msg)
    });

    socket.on('media_rem', function(msg) {
        selectbox_media_rem(msg)
        socket.emit('selected_files', $('#filelist').val());
    });

    socket.on('media_update', function(msg) {
        console.log('############################### media update')
        var selectobject_val = $('#filelist').val();
        if (selectobject_val.length == 1) {
            if (selectobject_val[0] == msg.src_filename_extension) {
                selected_update(msg)
            }
        }
        if (selectobject_val.length > 1) {
            var selected_files = [];
            for (let i = 0; i < selectobject_val.length; i++) {
                selected_files.push(selectobject_val[i]); 
            }
            socket.emit('selected_files', selected_files);
        }

        flag_update(msg);
    });

    socket.on('selected_update', function(msg) {
        if (msg == null) {
            document.getElementById('dropdown_media_dst').innerHTML = '';
            document.getElementById('dropdown_video_stream').innerHTML = '';
            document.getElementById('dropdown_audio_stream').innerHTML = '';
            document.getElementById('dropdown_subtitle_stream_main').innerHTML = '';
            document.getElementById('dropdown_subtitle_stream_additional').innerHTML = '';
            document.getElementById('media_start_number').value = 0;
            document.getElementById('media_stop_number').value = 0;
            $(".line_data").html('');
            document.activeElement.blur();
        } else {
            selected_update(msg);
        }
    });  

///////////////////////////////////////////////////////////////////////////////

    socket.on('process_update', function(msg) {
        var selectobject_val = $('#filelist').val();
        if (selectobject_val.length == 1) {
            if (selectobject_val[0] == msg[1]) {
                if (msg[0] == 'extract_subtitles') {
                    element = 'extract_subtitles_state'
                    progress_string = '<progress class="progress_bar" value="' + parseFloat(msg[2]) + '" max="100"></progress>\xa0\xa0\xa0\xa0' + msg[2] + '% (eta: ' + msg[3] + ')'
                    if (msg[5] == 'main' || msg[5] == 'both') {
                        document.getElementById('subtitle_main_state').innerHTML = progress_string;
                    }
                    if (msg[5] == 'additional' || msg[5] == 'both') {
                        document.getElementById('subtitle_additional_state').innerHTML = progress_string;
                    }
                }

                else {
                    if (msg[0] == 'convert_audio') {element = 'convert_audio_state'}
                    if (msg[0] == 'convert_voiceover_audio') {element = 'convert_audio_voiceover_state'}
                    if (msg[0] == 'convert_video') {element = 'convert_video_state'}
                    if (msg[0] == 'extract_audio') {element = 'extract_audio_state'}
                    if (msg[0] == 'download_voiceover') {element = 'download_voiceover_state'}
                    if (msg[0] == 'create_voiceover') {element = 'create_voiceover_state'}
                    
                    if (msg[0] == 'create_voiceover' || msg[0] == 'download_voiceover') {
                        progress_string = '<progress class="progress_bar" value="' + parseFloat(msg[2]) + '" max="100"></progress>\xa0\xa0\xa0\xa0' + msg[2] + '% (eta: ' + msg[3] + ')'
                    }
                    else {
                        progress_string = '<progress class="progress_bar" value="' + parseFloat(msg[2]) + '" max="100"></progress>\xa0\xa0\xa0\xa0' + msg[2] + '% (eta: ' + msg[3] + ', bitrate: ' + msg[4] + ' kb/s)'
                    }

                    document.getElementById(element).innerHTML = progress_string;
                }
            }
        }
    });

///////////////////////////////////////////////////////////////////////////////


    $('select#filelist').change(function(event) {
        socket.emit('selected_files', $('#filelist').val());
        console.log('selected files:', $('#filelist').val())
        return false;
    });


///////////////////////////////////////////////////////////////////////////////


    $('button#set_media_dst').click(function(event) {
        socket.emit('set_media_dst', [$('#filelist').val(), $('#dropdown_media_dst').val()]);
        console.log('set_media_dst', [$('#filelist').val(), $('#dropdown_media_dst').val()]);
        return false;
    });
    $('button#set_video_stream').click(function(event) {
        socket.emit('set_video_stream', [$('#filelist').val(), $('#dropdown_video_stream').val()]);
        console.log('set_video_stream', [$('#filelist').val(), $('#dropdown_video_stream').val()]);
        return false;
    });
    $('button#set_audio_stream').click(function(event) {
        socket.emit('set_audio_stream', [$('#filelist').val(), $('#dropdown_audio_stream').val()]);
        console.log('set_audio_stream', [$('#filelist').val(), $('#dropdown_audio_stream').val()]);
        return false;
    });
    $('button#set_subtitle_stream_main').click(function(event) {
        socket.emit('set_subtitle_stream_main', [$('#filelist').val(), $('#dropdown_subtitle_stream_main').val()]);
        console.log('set_subtitle_stream_main', [$('#filelist').val(), $('#dropdown_subtitle_stream_main').val()]);
        return false;
    });
    $('button#set_subtitle_stream_additional').click(function(event) {
        socket.emit('set_subtitle_stream_additional', [$('#filelist').val(), $('#dropdown_subtitle_stream_additional').val()]);
        console.log('set_subtitle_stream_additional', [$('#filelist').val(), $('#dropdown_subtitle_stream_additional').val()]);
        return false;
    });



///////////////////////////////////////////////////////////////////////////////


    $('button.btn_detect_resolution').click(function(event) {
        socket.emit('detect_resolution', {button: this.value, selected_files: $('#filelist').val()});
        console.log('detect_resolution', {button: this.value, selected_files: $('#filelist').val()});
        return false;
    });

    $('button.btn_extract_hdrplus').click(function(event) {
        socket.emit('extract_hdrplus', {button: this.value, selected_files: $('#filelist').val()});
        console.log('extract_hdrplus', {button: this.value, selected_files: $('#filelist').val()});
        return false;
    });

    $('button.btn_extract_audio').click(function(event) {
        socket.emit('extract_audio', {button: this.value, selected_files: $('#filelist').val()});
        console.log('extract_audio', {button: this.value, selected_files: $('#filelist').val()});
        return false;
    });

    $('button.btn_convert_video').click(function(event) {
        socket.emit('convert_video', {button: this.value, selected_files: $('#filelist').val()});
        console.log('convert_video', {button: this.value, selected_files: $('#filelist').val()});
        return false;
    });

    $('button.btn_convert_audio').click(function(event) {
        socket.emit('convert_audio', {button: this.value, selected_files: $('#filelist').val()});
        console.log('convert_audio', {button: this.value, selected_files: $('#filelist').val()});
        return false;
    });

    $('button.btn_convert_voiceover_audio').click(function(event) {
        socket.emit('convert_voiceover_audio', {button: this.value, selected_files: $('#filelist').val()});
        console.log('convert_voiceover_audio', {button: this.value, selected_files: $('#filelist').val()});
        return false;
    });

    $('button.btn_download_subtitles_main').click(function(event) {
        socket.emit('download_subtitles_main', {button: this.value, selected_files: $('#filelist').val()});
        console.log('download_subtitles_main', {button: this.value, selected_files: $('#filelist').val()});
        return false;
    });

    $('button.btn_download_subtitles_additional').click(function(event) {
        socket.emit('download_subtitles_additional', {button: this.value, selected_files: $('#filelist').val()});
        console.log('download_subtitles_additional', {button: this.value, selected_files: $('#filelist').val()});
        return false;
    });

    $('button.btn_extract_subtitles').click(function(event) {
        socket.emit('extract_subtitles', {button: this.value, selected_files: $('#filelist').val()});
        console.log('extract_subtitles', {button: this.value, selected_files: $('#filelist').val()});
        return false;
    });

    $('button.btn_download_voiceover').click(function(event) {
        socket.emit('download_voiceover', {button: this.value, selected_files: $('#filelist').val()});
        console.log('download_voiceover', {button: this.value, selected_files: $('#filelist').val()});
        return false;
    });

    $('button.btn_create_voiceover').click(function(event) {
        socket.emit('create_voiceover', {button: this.value, selected_files: $('#filelist').val()});
        console.log('create_voiceover', {button: this.value, selected_files: $('#filelist').val()});
        return false;
    });

    $('button.btn_mux').click(function(event) {
        socket.emit('mux', {button: this.value, selected_files: $('#filelist').val()});
        console.log('mux', {button: this.value, selected_files: $('#filelist').val()});
        return false;
    });

    $('button.btn_move_files').click(function(event) {
        socket.emit('move_files', {button: this.value, selected_files: $('#filelist').val()});
        console.log('move_files', {button: this.value, selected_files: $('#filelist').val()});
        return false;
    });

    $('button#media_start_stop_btn').click(function(event) {
        socket.emit('media_start_stop', {selected_files: $('#filelist').val(), start: $('#media_start_number').val(), stop: $('#media_stop_number').val()});
        console.log('media_start_stop', {selected_files: $('#filelist').val(), start: $('#media_start_number').val(), stop: $('#media_stop_number').val()});
        return false;
    });

    $('button#sub_time_drift_btn').click(function(event) {
        socket.emit('sub_time_drift', {selected_files: $('#filelist').val(), button: this.name, lang: $('#sub_time_drift_dropdown').val(), time_drift: $('#sub_time_drift_number').val()});
        console.log('sub_time_drift', {selected_files: $('#filelist').val(), button: this.name, lang: $('#sub_time_drift_dropdown').val(), time_drift: $('#sub_time_drift_number').val()});
        return false;
    });


    $('button#recreate_database').click(function(event) {
        socket.emit('recreate_database');
        console.log('recreate_database');
        return false;
    });

    $('button#show_media_info').click(function(event) {
        socket.emit('show_media_info', $('#filelist').val());
        console.log('show_media_info', $('#filelist').val());
        return false;
    });

    $('button#test_conversion').click(function(event) {
        socket.emit('test_conversion', $('#filelist').val());
        console.log('test_conversion', $('#filelist').val());
        return false;
    });

    $('button#test_a').click(function(event) {
        socket.emit('test_a');
        console.log('test_a');
        return false;
    });



    $('#clear_logger').click(function(event) {
        // console.log('clear_logger');
        // console.log(event);
        $('#logger_area').val('')
    });

});


