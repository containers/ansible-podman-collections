import os


def verify_inventory_file(self, path: str) -> bool:

    unused, ext = os.path.splitext(path)
    if ext not in (".yml", ".yaml"):
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            header = f.read(2048)
        return (
            (f"plugin: {self.NAME}\n" in header)
            or (f"plugin: '{self.NAME}'" in header)
            or (f'plugin: "{self.NAME}"' in header)
        )
    except Exception:
        return False
