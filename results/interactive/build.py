"""build.py - assemble the self-contained interactive landscape page.

Inlines three.js and the exported grid into a single HTML file with no
external requests, so it works offline and inside a strict CSP.

    python landscape.py            # regenerate data/landscape.npz
    python results/interactive/export.py
    python results/interactive/build.py
"""
import pathlib

HERE = pathlib.Path(__file__).parent
body = (HERE / "_template.html").read_text()
three = (HERE / "three.min.js").read_text()
data = (HERE / "landscape.json").read_text()

i = body.rindex("<script>")
out = (body[:i]
       + "<script>\n" + three + "\n</script>\n"
       + "<script>window.__LANDSCAPE__=" + data + ";</script>\n"
       + body[i:])
(HERE / "landscape_3d.html").write_bytes(out.encode("utf-8"))
print(f"wrote landscape_3d.html ({len(out)/1024:.1f} KB)")
