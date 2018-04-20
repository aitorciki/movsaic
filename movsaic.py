#!/usr/bin/env python

import argparse
import math
import os
import shlex
import subprocess


def build_filter(width, height, num_inputs):
    prev = 'base'
    size = math.ceil(math.sqrt(num_inputs))
    c_width = width // size
    c_height = height // size

    base = [f'color=color=black:size={width}x{height} [{prev}]']
    defs = []
    overlays = []

    for i in range(num_inputs):
        current = f'tmp{i + 1}'
        y = i // size
        x = i % size
        offset_y = y * c_height
        offset_x = x * c_width

        d = f'[{i}:v] setpts=PTS-STARTPTS, scale={c_width}x{c_height} [{y+1}x{x+1}]'
        o = f'[{prev}][{y+1}x{x+1}] overlay=shortest=1:y={offset_y}:x={offset_x}'
        if i < num_inputs - 1:
            o += f' [{current}]'

        defs.append(d)
        overlays.append(o)

        prev = current

    return '; '.join(base + defs + overlays)


def build_ffmpeg(inputs, width, height, output, codec, extra_params=''):
    command = ['ffmpeg']

    for input in inputs:
        command.extend(['-i', input])

    command.extend(['-filter_complex', build_filter(width, height, len(inputs))])
    command.extend(['-c:v', codec])
    command.extend(shlex.split(extra_params))

    command.append(output)

    return command

def safe_output(output):
    if not os.path.exists(output):
        return output

    name, ext = os.path.splitext(output)
    suffix = 1

    while True:
        output = f'{name}.{suffix}{ext}'
        suffix = suffix + 1

        if not os.path.exists(output):
            break

    return output

def mosaicify(inputs, width, height, output, codec, ffmpeg_params):
    output = safe_output(output)
    command = build_ffmpeg(inputs, width, height, output, codec, ffmpeg_params)

    try:
        subprocess.run(command, check=True)

        print(f'\nVideo ready at {os.path.abspath(output)}')
    except Exception:
        # ffmpeg outputs its errors to stderr
        pass


if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description='Make a collage of videos.',
        conflict_handler='resolve'
    )
    p.add_argument('inputs', metavar='input', nargs='+', help='videos to combine in a mosaic')
    p.add_argument('-w', '--width', type=int, default=1920, help='output video width')
    p.add_argument('-h', '--height', type=int, default=1080, help='output video height')
    p.add_argument('-o', '--output', default='./movsaic.mp4', help='output file')
    p.add_argument('-c', '--codec', default='libx264', help='output file video codec')
    p.add_argument('--ffmpeg-params', default='', help='extra params to pass to ffmpeg')

    mosaicify(**vars(p.parse_args()))
