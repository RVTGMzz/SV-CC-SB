#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, io, json, zipfile
from PIL import Image

VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.69"
SHIP_SHA = "58caeabc94744ad04ae1f006c91e09bf9a55d5a211d53b426b12ca9d0dc1c9ce"
EXPECTED = {
    "morning": "9a8996ef0068057e774419d9d4597f44753951b3ec1ec519cd6771efaad7b5d0",
    "noon": "fa0f00051febb62d107e4a1dc14a079dbfc8183659a73b9ed2ecfe5c4efb3aff",
    "evening": "b94d30d18bacecc2c3f09971aec2d5951956490be8c7cad2243b4689c865a638",
    "night": "f9d15f66485f514f4be8589ee29d45beabda87e357b1c1d3ffa7965855ed1990",
}
ROOT = "Cardcha/assets/airship_props/set01_redux/window_runtime/"

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    with zipfile.ZipFile(args.package) as z:
        manifest = json.loads(z.read("Cardcha/manifest.json"))
        assert manifest["Version"] == VERSION, manifest["Version"]
        dll = z.read("Cardcha/Cardcha.dll")
        assert dll[:2] == b"MZ" and len(dll) > 50000
        for state, wanted in EXPECTED.items():
            raw = z.read(ROOT + f"window_scene_default_{state}_clear.png")
            assert hashlib.sha256(raw).hexdigest() == wanted, state
            with Image.open(io.BytesIO(raw)) as image:
                image.load()
                assert image.format == "PNG", (state, image.format)
                assert image.size == (160, 80), (state, image.size)
                assert image.mode == "RGBA", (state, image.mode)
        ship = z.read(ROOT + "observation_window_airship.png")
        assert hashlib.sha256(ship).hexdigest() == SHIP_SHA
        ambient = json.loads(z.read("Cardcha/assets/airship_props/set01_redux/airship_ambient_manifest.json"))
        window = ambient["observationWindow"]
        assert window["productionStatus"] == "D2_CLEAR_TIME_MATRIX_MATERIALIZED_PENDING_RON_VISUAL"
        assert window["d2ClearMatrix"]["legacyEnvironmentOverlayReuse"] is False
        assert window["d2ClearMatrix"]["airshipLayer"] == "independent-.68-runtime-sprite"
    print(json.dumps({"package": str(args.package), "version": VERSION, "audit": "PASS", "visualAcceptance": "PENDING-RON-VISUAL"}, indent=2))

if __name__ == "__main__":
    main()
