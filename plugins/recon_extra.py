"""Extended recon."""
NAME="Extended Recon";VERSION="1.0";DESCRIPTION="Extra recon"
def run(app=None):
    import subprocess
    r={}
    try:r["dns"]=subprocess.run(["resolvectl","status"],capture_output=True,text=True,timeout=5).stdout[:200]
    except:pass
    return r