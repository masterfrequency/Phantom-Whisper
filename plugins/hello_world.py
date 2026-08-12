"""Sample plugin."""
NAME="Hello World";VERSION="1.0";DESCRIPTION="Demo"
def run(app=None):
    import platform
    return {"plugin":NAME,"system":platform.system(),"node":platform.node(),"message":"Plugin system ALIVE!"}