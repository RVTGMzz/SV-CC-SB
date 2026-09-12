#!/usr/bin/env python3
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'src/Cardcha/assets/airship_props/set01_redux/window_runtime'
SEASONS=['default','spring','summer','fall','winter']
TIMES=['morning','noon','evening','night']
WEATHERS=['rain','storm','snow']

for season in SEASONS:
    for tod in TIMES:
        clear_path=DIR/f'window_scene_{season}_{tod}_clear.png'
        clear=Image.open(clear_path).convert('RGBA')

        # The source sky crop is fully opaque. The generator may add stars with translucent
        # pixels at night; those are visual tint pixels, not transparency windows. Normalize
        # the clear reference surface first so the room's black void can never leak through.
        clear.putalpha(255)
        assert clear.getchannel('A').getextrema()==(255,255), clear_path
        clear.save(clear_path)

        for weather in WEATHERS:
            path=DIR/f'window_scene_{season}_{tod}_{weather}.png'
            weather_scene=Image.open(path).convert('RGBA')

            # The weather scene already contains the weather-tinted sky. Most pixels are
            # opaque; only authored translucent additions (rain header, snow veil, stars)
            # need to blend over the fully opaque clear scene.
            fixed=Image.alpha_composite(clear, weather_scene)
            if weather=='snow':
                # Add a very light cold veil while retaining the visible landscape/clouds.
                veil=Image.new('RGBA',fixed.size,(215,232,248,24))
                fixed=Image.alpha_composite(fixed,veil)

            assert fixed.getchannel('A').getextrema()==(255,255), path
            fixed.save(path)

print('0696C scene compositing fixed: all 80 environment scenes are fully opaque.')
