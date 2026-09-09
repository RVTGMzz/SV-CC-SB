from pathlib import Path
import base64, hashlib, io, runpy, zipfile

parts = [Path(f"tools/0671_assets_chunk{i}.b64").read_text(encoding="utf-8").strip() for i in range(1, 5)]
bundle = "".join(parts)
assert len(bundle) == 14160, f"0671 bundle b64 length mismatch: {len(bundle)}"
raw = base64.b64decode(bundle, validate=True)
assert len(raw) == 10619, f"0671 bundle byte length mismatch: {len(raw)}"
digest = hashlib.sha256(raw).hexdigest()
assert digest == "20cc8fefd365bf500046ad39b8c6f2c25e8517d3d77a666f9b9069c3d26403ab", digest
with zipfile.ZipFile(io.BytesIO(raw)) as z:
    names = z.namelist()
    assert len(names) == 10, names
    assert set(names) == {
        "chacha_mirror_rabbit.png",
        "chacha_resonance_rabbit.png",
        "chacha_trinity_rabbit.png",
        "hollow_curator.png",
        "hollow_curator_arena_tiles.png",
        "mimi_arena_tiles.png",
        "mimi_resonance_master.png",
        "tricolor_arena_tiles.png",
        "tricolor_guardians.png",
        "tricolor_unified.png",
    }
Path("tools/0671_assets.zip.b64").write_text(bundle, encoding="utf-8")
print(f"0671 clean asset bundle PASS sha256={digest} files={len(names)}")
runpy.run_path("tools/alpha28_0671_authored_boss_visuals_arenas.py", run_name="__main__")
