import re
import os
from datetime import datetime
import soundfile as sf
import numpy as np
import librosa
import argparse
import noisereduce as nr


def is_time_stamp(l):
    if l[:2].isnumeric() and l[2] == ':':
        return True
    return False


def has_letters(line):
    if re.search('[a-zA-Z]', line):
        return True
    return False


def has_no_text(line):
    l = line.strip()
    if not len(l):
        return True
    if l.isnumeric():
        return True
    if is_time_stamp(l):
        return True
    if l[0] == '(' and l[-1] == ')':
        return True
    if not has_letters(line):
        return True
    return False


def is_lowercase_letter_or_comma(letter):
    if letter.isalpha() and letter.lower() == letter:
        return True
    if letter == ',':
        return True
    return False


def num2text(line):
    convert_dict = {'1': 'một',
                    '2': 'hai',
                    '3': 'ba',
                    '4': 'bốn',
                    '5': 'năm',
                    '6': 'sáu',
                    '7': 'bảy',
                    '8': 'tám',
                    '9': 'chín'}

    line = line.split(" ")
    newline = []

    for word in line:
        if word in convert_dict.keys():
            word = convert_dict[word]
        newline.append(word)

    return ' '.join(newline)


def clean_up(lines):
    """
    Get rid of all non-text lines and
    try to combine text broken into multiple lines
    """

    new_lines = []
    for line in lines[1:]:
        if has_no_text(line) or is_time_stamp(line):
            continue
        else:
            # append line
            line = line[:-1]
            line = num2text(line)
            new_lines.append(line.lower())
    return new_lines


def process_time_stamp(line):
    line = line.split(" ")
    start_time = line[0]
    end_time = line[2][:-1]
    start_time = datetime.strptime(start_time, '%H:%M:%S,%f')
    start_time = start_time.second + start_time.minute * 60 + start_time.hour * 3600 + start_time.microsecond / 1e6
    end_time = datetime.strptime(end_time, '%H:%M:%S,%f')
    end_time = end_time.second + end_time.minute * 60 + end_time.hour * 3600 + end_time.microsecond / 1e6

    return start_time, end_time


def get_all_timestamps(file, file_encoding='utf-8'):
    all_time_stamps = []
    with open(file, encoding=file_encoding, errors='replace') as f:
        lines = f.readlines()
        for line in lines:
            if is_time_stamp(line):
                s, e = process_time_stamp(line)
                all_time_stamps.append([s, e])
    return all_time_stamps


def merge(all_time_stamps, all_texts, num_merge_segments=3):
    for i, text in enumerate(all_texts):
        # remove sound, music segments
        if all_texts[i].startswith('['):
            all_texts.remove(text)
            all_time_stamps.remove(all_time_stamps[i])

        else:
            for j in range(1, num_merge_segments):
                try:

                    if all_texts[i + 1] == '[âm nhạc]':
                        all_texts.remove(all_texts[i + 1])
                        all_time_stamps.remove(all_time_stamps[i + 1])
                        break
                    else:
                        # merge timestamps
                        all_time_stamps[i][1] = all_time_stamps[i + 1][1]
                        all_time_stamps.remove(all_time_stamps[i + 1])

                        # merge texts
                        all_texts[i] = all_texts[i] + ' ' + all_texts[i + 1]
                        all_texts.remove(all_texts[i + 1])
                except IndexError:
                    pass


def get_timestamp_and_text(srt_file, encoding='utf-8'):
    with open(srt_file, encoding=encoding, errors='replace') as f:
        texts = f.readlines()
        all_texts = clean_up(texts)

    f.close()
    all_timestamps = get_all_timestamps(file=srt_file)
    merge(all_time_stamps=all_timestamps, all_texts=all_texts)

    return all_timestamps, all_texts


def remove_background_sound(save_dir):
    all_wav_files = [file for file in os.listdir(save_dir) if file.endswith('.wav')]
    for idx,filename in enumerate(all_wav_files):
        print(f'Cleaning file {idx + 1}/ {len(all_wav_files)}')
        filename = os.path.join(save_dir, filename)
        audio, sr = librosa.load(filename, sr=48000)
        audio = librosa.resample(audio, orig_sr=sr, target_sr=22050)
        reduced_noise = nr.reduce_noise(y=audio, sr=22050, prop_decrease=0.95,use_tqdm=True)
        sf.write(filename, reduced_noise, samplerate=22050)


def segment_audio(segment_dir):
    all_files = sorted(os.listdir(segment_dir))

    try:
        os.makedirs(os.path.join(os.path.dirname(segment_dir), 'wavs'))
        print('Creating save directory...')
    except FileExistsError:
        print('Directory has been created. Continue segmenting...')

    with open('metadata.txt', 'w') as f:
        for idx,file in enumerate(all_files):
            if file.endswith('.srt'):

                all_timestamps, all_texts = get_timestamp_and_text(os.path.join(segment_dir, file))
                name = os.path.splitext(file)[0]
                audio, sr = librosa.load(os.path.join(segment_dir, name + ".wav"))
                for i, [start, end] in enumerate(all_timestamps):
                    # segment audio
                    start *= sr
                    end *= sr
                    seg = audio[round(start):round(end)]
                    out_filename = os.path.join(os.path.dirname(segment_dir), 'wavs', f'{name}-seg-{i}.wav')
                    sf.write(out_filename, seg, samplerate=22050)

                    # write text subtitle for each audio segment
                    text = all_texts[i]
                    text = f'{name}-seg-{i}|' + text
                    f.write(text)
                    f.write("\n")
    f.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--segment_dir", default='/home/artorias/PycharmProjects/CrawlData/downloads',
                        type=str,
                        help="path to the download data directory")
    args = parser.parse_args()
    remove_background_sound(save_dir=args.segment_dir)
    segment_audio(segment_dir=args.segment_dir)
