import json, pathlib
base = pathlib.Path(r"<local-path>")
src = (base / "s1_blender_review.html").read_text(encoding="utf-8")
block = (base / "jsonld_block.json").read_text(encoding="utf-8")
json.loads(block)  # syntax check
script = '<script type="application/ld+json">\n' + block.strip() + '\n</script>\n'
out = src.replace("</head>", script + "</head>", 1)
(base / "s1_blender_review_with_jsonld.html").write_text(out, encoding="utf-8")
print("written")
